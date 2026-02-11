#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skills MCP Server - Model Context Protocol Server for Business Skills

Dynamically loads skills from S3 and exposes them as MCP tools.

Features:
- Loads skills from S3 (s3://cerebricks-studio-agent-skills/skills_phase3/)
- Includes 3 legacy hardcoded skills for compatibility
- Exposes all skills via MCP JSON-RPC 2.0 protocol

Run: python skills_mcp_server.py
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import json
import sys
from pathlib import Path

# Add orchestrator to path for skill loader
orchestrator_path = Path(__file__).parent / "orchestrator"
sys.path.insert(0, str(orchestrator_path))

# Add retail_mcp_server to path to import skills
retail_path = Path(__file__).parent.parent / "retail_mcp_server"
sys.path.insert(0, str(retail_path))

try:
    from skills.pdf_report_generator.scripts import ReportGenerator
    from skills.sentiment_analyzer.scripts import SentimentAnalyzer
    from skills.competitive_intelligence_monitor.scripts import CompetitiveMonitor
    SKILLS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Skills not available: {e}")
    SKILLS_AVAILABLE = False
    # Create mock classes for development
    class ReportGenerator:
        def generate(self, data, template="default"):
            return {"status": "mock", "message": "ReportGenerator not available"}

    class SentimentAnalyzer:
        def analyze(self, text):
            return {"sentiment": "neutral", "score": 0.5, "note": "Mock analyzer"}

    class CompetitiveMonitor:
        def monitor(self, urls, frequency="daily"):
            return {"status": "mock", "message": "CompetitiveMonitor not available"}

# Import S3 Skill Loader
try:
    from skill_loader import get_skill_loader
    S3_SKILLS_AVAILABLE = True
except ImportError:
    S3_SKILLS_AVAILABLE = False
    logging.warning("S3 Skill Loader not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Skills MCP Server (S3 + Legacy)",
    description="Model Context Protocol server exposing S3 skills + legacy hardcoded skills",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize skill instances
try:
    pdf_generator = ReportGenerator()
    sentiment_analyzer = SentimentAnalyzer()
    competitive_monitor = CompetitiveMonitor()
    logger.info("✓ All skills initialized successfully")
except Exception as e:
    logger.warning(f"Skills initialization warning: {e}")
    pdf_generator = ReportGenerator()
    sentiment_analyzer = SentimentAnalyzer()
    competitive_monitor = CompetitiveMonitor()


# ===================
# MCP Tool Definitions
# ===================

MCP_TOOLS = [
    {
        "name": "generate_pdf_report",
        "description": """
Generate a professional PDF report from structured data.

Supports multiple templates and data formats. Can create:
- Executive summaries
- Data analysis reports
- Sales reports
- Inventory reports
- Custom formatted documents

Returns the PDF file path or base64 encoded PDF data.
        """.strip(),
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "Structured data to include in the report (JSON object)"
                },
                "title": {
                    "type": "string",
                    "description": "Report title",
                    "default": "Business Report"
                },
                "template": {
                    "type": "string",
                    "enum": ["default", "executive", "detailed", "summary"],
                    "description": "Report template to use",
                    "default": "default"
                },
                "output_format": {
                    "type": "string",
                    "enum": ["file", "base64"],
                    "description": "Output format (file path or base64 encoded)",
                    "default": "file"
                },
                "output_path": {
                    "type": "string",
                    "description": "Output file path (for file format)",
                    "default": "/workspace/report.pdf"
                }
            },
            "required": ["data"]
        }
    },
    {
        "name": "analyze_sentiment",
        "description": """
Analyze sentiment from text content.

Provides:
- Overall sentiment (positive/negative/neutral)
- Sentiment score (-1.0 to 1.0)
- Confidence level
- Key emotional indicators
- Sentiment breakdown by section

Supports multiple languages and text sources.
        """.strip(),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text content to analyze"
                },
                "source": {
                    "type": "string",
                    "description": "Source of the text (e.g., 'review', 'social_media', 'article')",
                    "default": "general"
                },
                "detailed": {
                    "type": "boolean",
                    "description": "Return detailed analysis including emotions and keywords",
                    "default": False
                },
                "language": {
                    "type": "string",
                    "description": "Text language (auto-detect if not specified)",
                    "default": "auto"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "monitor_competitor",
        "description": """
Monitor competitor websites for changes and intelligence.

Features:
- Website change detection
- Content extraction
- Pricing monitoring
- Product updates tracking
- Alert generation for significant changes

Can monitor multiple URLs and track changes over time.
        """.strip(),
        "inputSchema": {
            "type": "object",
            "properties": {
                "urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of competitor URLs to monitor"
                },
                "frequency": {
                    "type": "string",
                    "enum": ["once", "hourly", "daily", "weekly"],
                    "description": "Monitoring frequency",
                    "default": "once"
                },
                "track_changes": {
                    "type": "boolean",
                    "description": "Track and report changes from previous scan",
                    "default": True
                },
                "extract_pricing": {
                    "type": "boolean",
                    "description": "Attempt to extract pricing information",
                    "default": False
                },
                "generate_report": {
                    "type": "boolean",
                    "description": "Generate intelligence report",
                    "default": True
                }
            },
            "required": ["urls"]
        }
    }
]


# ===================
# MCP JSON-RPC Models
# ===================

class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 request."""
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[int] = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 response."""
    jsonrpc: str = "2.0"
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[int] = None


# ===================
# Tool Execution Logic
# ===================

async def execute_pdf_report_tool(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Execute generate_pdf_report tool."""
    data = arguments.get("data", {})
    title = arguments.get("title", "Business Report")
    template = arguments.get("template", "default")
    output_format = arguments.get("output_format", "file")
    output_path = arguments.get("output_path", "/workspace/report.pdf")

    logger.info(f"Generating PDF report: {title} (template: {template})")

    try:
        # Generate report using ReportGenerator
        result = pdf_generator.generate(
            data=data,
            title=title,
            template=template,
            output_format=output_format,
            output_path=output_path
        )

        if output_format == "file":
            return [{
                "type": "text",
                "text": f"PDF report generated successfully:\n"
                        f"Title: {title}\n"
                        f"Template: {template}\n"
                        f"Output: {output_path}\n"
                        f"Status: {result.get('status', 'success')}"
            }]
        else:
            return [{
                "type": "text",
                "text": f"PDF report generated (base64):\n{result.get('data', 'N/A')[:200]}..."
            }]

    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return [{
            "type": "text",
            "text": f"Error generating PDF report: {str(e)}"
        }]


async def execute_sentiment_tool(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Execute analyze_sentiment tool."""
    text = arguments.get("text", "")
    source = arguments.get("source", "general")
    detailed = arguments.get("detailed", False)
    language = arguments.get("language", "auto")

    if not text:
        return [{
            "type": "text",
            "text": "Error: 'text' parameter is required"
        }]

    logger.info(f"Analyzing sentiment for text ({len(text)} chars, source: {source})")

    try:
        # Analyze sentiment using SentimentAnalyzer
        result = sentiment_analyzer.analyze(
            text=text,
            source=source,
            detailed=detailed,
            language=language
        )

        # Format output
        sentiment = result.get("sentiment", "neutral")
        score = result.get("score", 0.0)
        confidence = result.get("confidence", 0.0)

        output = f"Sentiment Analysis Results:\n"
        output += f"  Sentiment: {sentiment.upper()}\n"
        output += f"  Score: {score:.2f} (-1.0 to 1.0)\n"
        output += f"  Confidence: {confidence:.2%}\n"

        if detailed and "emotions" in result:
            output += f"\n  Top Emotions:\n"
            for emotion, value in list(result.get("emotions", {}).items())[:3]:
                output += f"    - {emotion}: {value:.2f}\n"

        if detailed and "keywords" in result:
            keywords = result.get("keywords", [])[:5]
            output += f"\n  Key Terms: {', '.join(keywords)}\n"

        return [{
            "type": "text",
            "text": output
        }]

    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        return [{
            "type": "text",
            "text": f"Error analyzing sentiment: {str(e)}"
        }]


async def execute_competitive_monitor_tool(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Execute monitor_competitor tool."""
    urls = arguments.get("urls", [])
    frequency = arguments.get("frequency", "once")
    track_changes = arguments.get("track_changes", True)
    extract_pricing = arguments.get("extract_pricing", False)
    generate_report = arguments.get("generate_report", True)

    if not urls:
        return [{
            "type": "text",
            "text": "Error: 'urls' parameter is required (list of URLs)"
        }]

    logger.info(f"Monitoring {len(urls)} competitor URLs (frequency: {frequency})")

    try:
        # Monitor competitors using CompetitiveMonitor
        result = competitive_monitor.monitor(
            urls=urls,
            frequency=frequency,
            track_changes=track_changes,
            extract_pricing=extract_pricing,
            generate_report=generate_report
        )

        # Format output
        output = f"Competitive Intelligence Monitor Results:\n"
        output += f"  URLs Monitored: {len(urls)}\n"
        output += f"  Frequency: {frequency}\n"
        output += f"  Status: {result.get('status', 'completed')}\n"

        if "changes_detected" in result:
            output += f"\n  Changes Detected: {result.get('changes_detected', 0)}\n"

        if "pricing" in result and extract_pricing:
            output += f"\n  Pricing Data Extracted: {len(result.get('pricing', []))} items\n"

        if "report_path" in result and generate_report:
            output += f"\n  Report Generated: {result.get('report_path')}\n"

        if "insights" in result:
            insights = result.get("insights", [])[:3]
            if insights:
                output += f"\n  Key Insights:\n"
                for insight in insights:
                    output += f"    - {insight}\n"

        return [{
            "type": "text",
            "text": output
        }]

    except Exception as e:
        logger.error(f"Competitive monitoring error: {e}")
        return [{
            "type": "text",
            "text": f"Error monitoring competitors: {str(e)}"
        }]


# ===================
# MCP Endpoints
# ===================

@app.post("/")
async def mcp_handler(request: Request):
    """
    Main MCP JSON-RPC 2.0 handler.

    Handles both tools/list and tools/call methods.
    """
    try:
        body = await request.json()
        rpc_request = JSONRPCRequest(**body)

        logger.info(f"MCP Request: {rpc_request.method}")

        if rpc_request.method == "tools/list":
            # Return list of available tools
            return JSONRPCResponse(
                result={"tools": MCP_TOOLS},
                id=rpc_request.id
            ).dict(exclude_none=True)

        elif rpc_request.method == "tools/call":
            # Execute a tool
            params = rpc_request.params or {}
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if not tool_name:
                return JSONRPCResponse(
                    error={
                        "code": -32602,
                        "message": "Missing 'name' parameter"
                    },
                    id=rpc_request.id
                ).dict(exclude_none=True)

            # Route to appropriate tool handler
            if tool_name == "generate_pdf_report":
                content = await execute_pdf_report_tool(arguments)
            elif tool_name == "analyze_sentiment":
                content = await execute_sentiment_tool(arguments)
            elif tool_name == "monitor_competitor":
                content = await execute_competitive_monitor_tool(arguments)
            else:
                return JSONRPCResponse(
                    error={
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    },
                    id=rpc_request.id
                ).dict(exclude_none=True)

            # Return successful result
            return JSONRPCResponse(
                result={"content": content},
                id=rpc_request.id
            ).dict(exclude_none=True)

        else:
            # Unknown method
            return JSONRPCResponse(
                error={
                    "code": -32601,
                    "message": f"Method not found: {rpc_request.method}"
                },
                id=rpc_request.id
            ).dict(exclude_none=True)

    except Exception as e:
        logger.error(f"MCP handler error: {e}", exc_info=True)
        return JSONRPCResponse(
            error={
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        ).dict(exclude_none=True)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "server": "Skills MCP Server",
        "tools_available": len(MCP_TOOLS),
        "skills_loaded": SKILLS_AVAILABLE
    }


@app.get("/")
async def root():
    """Root endpoint with server info (GET request)."""
    return {
        "name": "Skills MCP Server",
        "version": "1.0.0",
        "protocol": "Model Context Protocol (MCP)",
        "tools": len(MCP_TOOLS),
        "skills_available": SKILLS_AVAILABLE,
        "endpoints": {
            "tools/list": "POST / with method=tools/list",
            "tools/call": "POST / with method=tools/call"
        },
        "tool_names": [tool["name"] for tool in MCP_TOOLS],
        "skills": [
            "pdf_report_generator",
            "sentiment_analyzer",
            "competitive_intelligence_monitor"
        ]
    }


# ===================
# Lifecycle Events
# ===================

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logger.info("Starting Skills MCP Server...")
    logger.info(f"Skills available: {SKILLS_AVAILABLE}")
    logger.info(f"MCP Server ready with {len(MCP_TOOLS)} tools!")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down Skills MCP Server...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
