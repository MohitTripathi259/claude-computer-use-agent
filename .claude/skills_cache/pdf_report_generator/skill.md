---
name: pdf_report_generator
description: Generates professional PDF reports, presentations, and documents from data. Works generically with any data source or can be customized via config.json. Includes built-in templates for common report types.
allowed-tools: [anthropic-api, mcp-client]
version: "1.0.0"
---

# PDF/Report Generator

## Overview
Generate professional reports, executive summaries, presentations, and documents from any data source. Works immediately without configuration using intelligent defaults, or customize via config.json for your specific needs.

## Core Capabilities
- **Smart Data Extraction**: Automatically detects data structure and content type
- **Multiple Formats**: PDF, PowerPoint, Word, HTML, Markdown
- **Built-in Templates**: Executive summary, financial report, project status, analysis report
- **AI-Enhanced**: Uses Claude to generate insights and narrative from raw data
- **Brand Customization**: Apply company branding (when configured)
- **Chart Generation**: Automatic visualization of numerical data

## Default Behavior (No Config Required)

When run without config.json, the skill:
1. Accepts data from function call or stdin
2. Auto-detects data structure (JSON, CSV, table, text)
3. Selects appropriate template based on content
4. Generates professional PDF with intelligent formatting
5. Returns PDF as base64 or saves to default location

### Example Usage (No Config)
```python
from pdf_report_generator import ReportGenerator

# Works immediately with any data
generator = ReportGenerator()
pdf = generator.generate({
    "title": "Q4 Sales Report",
    "data": {...},
    "charts": [...]
})
```

## With Configuration (Advanced)

Create `config.json` to customize:

### Required Fields (if using config)
```json
{
  "input": {
    "from": "mcp://database/reports_data"
  },
  "output": {
    "to": "mcp://file-server/reports"
  }
}
```

### Optional Fields
```json
{
  "template": "executive_summary",
  "format": "pdf",
  "branding": {
    "logo": "mcp://assets/company-logo.png",
    "colors": {
      "primary": "#1E3A8A",
      "secondary": "#3B82F6"
    },
    "font": "Arial"
  },
  "include_ai_insights": true,
  "auto_charts": true,
  "page_size": "A4",
  "orientation": "portrait"
}
```

## Built-in Templates

### 1. Executive Summary
- One-page overview
- Key metrics highlighted
- Visual KPI cards
- Action items section

### 2. Financial Report
- Income statement format
- Chart visualizations
- Variance analysis
- Period comparisons

### 3. Project Status
- Timeline visualization
- Milestone tracking
- Resource utilization
- Risk assessment

### 4. Data Analysis
- Multi-section layout
- Statistical summaries
- Multiple chart types
- Insight callouts

### 5. Generic Report
- Flexible sections
- Auto-formatted tables
- Mixed content support

## AI Enhancement

When `include_ai_insights: true`:
- Automatically generates executive summary from data
- Identifies trends and anomalies
- Creates narrative explanations
- Suggests recommendations
- Highlights key findings

## Execution Modes

### Mode 1: Direct Data (No Config)
```python
generator = ReportGenerator()
pdf = generator.generate(data={...}, title="My Report")
```

### Mode 2: MCP Input (With Config)
```python
# Reads from config.json automatically
generator = ReportGenerator()
pdf = generator.execute()  # Uses MCP sources from config
```

### Mode 3: Scheduled Generation
```python
# If config has schedule
generator = ReportGenerator()
generator.run_scheduled()  # Generates reports on schedule
```

## Output Examples

### Default Output (No Config)
- Saves to `./output/report_{timestamp}.pdf`
- Returns base64 encoded PDF
- Includes generation metadata

### Configured Output
- Saves to MCP server location
- Can trigger notifications
- Supports multiple format generation
- Archives previous versions

## Error Handling
- **Missing data**: Creates placeholder report with warning
- **Invalid template**: Falls back to generic template
- **Format error**: Attempts alternate format
- **MCP unavailable**: Saves locally with retry queue

## Performance
- Generates 10-page report in ~5 seconds
- Handles datasets up to 100MB
- Supports batch generation
- Parallel processing for multiple reports

## Data Source Compatibility
- JSON objects and arrays
- CSV files
- Database query results
- API responses
- Excel spreadsheets
- Plain text with structure

## Chart Types Supported
- Line charts (trends)
- Bar charts (comparisons)
- Pie charts (proportions)
- Scatter plots (correlations)
- Heat maps (matrices)
- Gauges (KPIs)

## Customization Without Config

Even without config.json, you can customize per-execution:
```python
generator.generate(
    data={...},
    template="executive_summary",
    format="pdf",
    title="Custom Title",
    include_charts=True,
    ai_insights=True
)
```

## When to Use Config vs Direct Parameters

**Use config.json when:**
- Regular scheduled reports
- Consistent branding required
- Multiple data sources
- Team-wide standardization
- Automated workflows

**Use direct parameters when:**
- One-off reports
- Testing different templates
- Dynamic data sources
- API integrations
- Custom applications

## Integration Examples

### With Agent
```python
# Agent automatically calls when user requests report
user: "Generate Q4 sales report from the database"
agent: *invokes pdf_report_generator with extracted parameters*
```

### With Workflow
```python
# Part of automated pipeline
1. Data extraction skill -> outputs data
2. PDF generator skill -> creates report
3. Email skill -> sends to stakeholders
```

### With API
```python
@app.post("/generate-report")
async def create_report(data: dict):
    generator = ReportGenerator()
    pdf = generator.generate(data)
    return {"pdf": pdf, "url": upload_to_storage(pdf)}
```

## Configuration Priority

When config.json exists:
1. Function parameters (highest priority)
2. config.json settings
3. Built-in defaults (lowest priority)

## Examples

### Example 1: Simple Report (No Config)
```python
from scripts.generator import ReportGenerator

generator = ReportGenerator()
pdf = generator.generate({
    "title": "Monthly Sales",
    "summary": "Sales increased 15%",
    "data": {
        "revenue": 150000,
        "growth": "15%",
        "top_products": [...]
    }
})
```

### Example 2: With Config
```json
{
  "input": {
    "from": "mcp://salesforce/monthly-data"
  },
  "output": {
    "to": "mcp://sharepoint/reports",
    "format": "pdf"
  },
  "template": "executive_summary",
  "branding": {
    "logo": "mcp://assets/logo.png",
    "colors": {"primary": "#1E3A8A"}
  },
  "schedule": "monthly",
  "notify": "mcp://email/executives@company.com"
}
```

### Example 3: Batch Generation
```python
generator = ReportGenerator()
reports = generator.generate_batch([
    {"title": "North Region", "data": north_data},
    {"title": "South Region", "data": south_data},
    {"title": "East Region", "data": east_data}
])
```
