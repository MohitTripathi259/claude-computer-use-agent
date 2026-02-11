#!/usr/bin/env python3
"""
PDF/Report Generator - Main Logic
Works with or without config.json - intelligent defaults
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import base64

from .templates import TemplateManager
from .formatters import PDFFormatter, PPTXFormatter, DOCXFormatter

# Optional: Anthropic Claude SDK for richer AI insights
try:
    import anthropic  # type: ignore
except ImportError:
    anthropic = None


class ReportGenerator:
    """
    Generates professional reports in multiple formats.
    Works immediately without config, customizable with config.json
    """

    def __init__(self, config_path: str = './config.json'):
        """Initialize generator with optional config"""
        self.config = self._load_config_if_exists(config_path)
        self.template_manager = TemplateManager()
        self.has_config = self.config is not None

        # Initialize formatters
        self.formatters = {
            'pdf': PDFFormatter(),
            'pptx': PPTXFormatter(),
            'docx': DOCXFormatter()
        }

        print(f"PDF/Report Generator initialized")
        if self.has_config:
            print(f"Using configuration from {config_path}")
        else:
            print(f"Running with intelligent defaults (no config file)")

    def _load_config_if_exists(self, config_path: str) -> Optional[Dict]:
        """Load config only if it exists - no error if missing"""
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return None

    def generate(
        self,
        data: Optional[Dict] = None,
        title: Optional[str] = None,
        template: Optional[str] = None,
        format: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate report with flexible parameters.
        Priority: function params > config.json > defaults

        Args:
            data: Report data (if None, reads from config input source)
            title: Report title
            template: Template name (overrides config)
            format: Output format (overrides config)
            **kwargs: Additional parameters

        Returns:
            Dict with 'content' (base64), 'path', 'metadata'
        """
        print("\nStarting report generation...")

        # Step 1: Get data (from param or config source)
        if data is None:
            if self.has_config and 'input' in self.config:
                print("Fetching data from configured source...")
                data = self._fetch_data_from_source()
            else:
                raise ValueError(
                    "No data provided and no input source in config. "
                    "Either pass data parameter or configure input source."
                )

        # Step 2: Determine settings (param > config > default)
        settings = self._resolve_settings(title, template, format, kwargs)

        print(f"Template: {settings['template']}")
        print(f"Format: {settings['format']}")
        print(f"Branding: {'Yes' if settings.get('branding') else 'Default'}")

        # Step 3: Process data and enhance with AI if enabled
        processed_data = self._process_data(data, settings)

        # Step 4: Apply template
        print("Applying template...")
        report_structure = self.template_manager.apply_template(
            template_name=settings['template'],
            data=processed_data,
            branding=settings.get('branding'),
            ai_insights=settings.get('include_ai_insights', True)
        )

        # Step 5: Generate output in requested format
        print(f"Generating {settings['format'].upper()}...")
        formatter = self.formatters[settings['format']]
        output = formatter.format(report_structure, settings)

        # Step 6: Save to destination
        save_path = self._save_output(output, settings)

        # Step 7: Notify if configured
        if self.has_config and self.config.get('notify'):
            self._send_notification(save_path, settings)

        print(f"Report generated successfully!")
        print(f"Saved to: {save_path}")

        return {
            'success': True,
            'path': save_path,
            'content_base64': base64.b64encode(output).decode('utf-8'),
            'format': settings['format'],
            'title': settings['title'],
            'generated_at': datetime.now().isoformat(),
            'size_bytes': len(output)
        }

    def execute(self) -> Dict[str, Any]:
        """
        Execute with config.json settings.
        This is the main entry point for scheduled/automated execution.
        """
        if not self.has_config:
            raise ValueError(
                "execute() requires config.json. "
                "Use generate(data=...) for direct invocation."
            )

        return self.generate()

    def generate_batch(self, data_list: List[Dict]) -> List[Dict]:
        """Generate multiple reports from a list of data"""
        print(f"\nBatch generation: {len(data_list)} reports")
        results = []

        for idx, data_item in enumerate(data_list, 1):
            print(f"\n[{idx}/{len(data_list)}]")
            try:
                result = self.generate(
                    data=data_item.get('data'),
                    title=data_item.get('title'),
                    template=data_item.get('template')
                )
                results.append(result)
            except Exception as e:
                print(f"Failed: {str(e)}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'title': data_item.get('title', 'Unknown')
                })

        successful = sum(1 for r in results if r.get('success'))
        print(f"\nBatch complete: {successful}/{len(data_list)} successful")

        return results

    def _resolve_settings(
        self,
        title: Optional[str],
        template: Optional[str],
        format: Optional[str],
        kwargs: Dict
    ) -> Dict:
        """Resolve settings from params > config > defaults"""
        settings = {
            'title': title or (self.config or {}).get('title') or 'Generated Report',
            'template': template or (self.config or {}).get('template') or 'generic',
            'format': format or (self.config or {}).get('output', {}).get('format') or 'pdf',
            'page_size': kwargs.get('page_size') or (self.config or {}).get('page_size') or 'A4',
            'orientation': kwargs.get('orientation') or (self.config or {}).get('orientation') or 'portrait',
            'include_ai_insights': kwargs.get('ai_insights', (self.config or {}).get('include_ai_insights', True)),
            'auto_charts': kwargs.get('auto_charts', (self.config or {}).get('auto_charts', True)),
            'language': kwargs.get('language') or (self.config or {}).get('language') or 'en',
            'branding': (self.config or {}).get('branding'),
            # Optional: which retail data type this report is about
            'data_type': kwargs.get('data_type') or (self.config or {}).get('data_type') or 'generic',
        }

        return settings

    def _fetch_data_from_source(self) -> Dict:
        """Fetch data from configured MCP source"""
        print("  Connecting to data source...")
        return {
            "status": "demo_mode",
            "message": "In production, would fetch from: " + self.config['input']['from']
        }

    def _process_data(self, data: Dict, settings: Dict) -> Dict:
        """Process and enhance data"""
        processed = {
            'raw_data': data,
            'title': settings['title'],
            'generated_at': datetime.now().isoformat(),
            'data_type': settings.get('data_type', 'generic'),
        }

        # Auto-detect data structure
        if isinstance(data, dict):
            # Extract metrics for KPIs
            processed['metrics'] = self._extract_metrics(data)

            # Identify tables
            processed['tables'] = self._extract_tables(data)

            # Identify chart data
            if settings['auto_charts']:
                processed['charts'] = self._generate_chart_specs(data)

            # Inventory-specific enrichment: better KPIs and tables
            if settings.get('data_type') == 'inventory':
                processed = self._enrich_inventory_data(data, processed)

        # AI enhancement
        if settings['include_ai_insights']:
            print("  Generating AI insights...")
            processed['ai_insights'] = self._generate_ai_insights(data, settings)

        return processed

    def _enrich_inventory_data(self, data: Dict, processed: Dict) -> Dict:
        """
        Add richer, inventory-specific structure so the PDF looks like
        a proper inventory report instead of generic JSON.
        """
        # Inventory stats from Lambda: date, total_items, global_stats, breakdown, etc.
        global_stats = data.get('global_stats', {})

        # Build KPI-style metrics
        metrics = []

        def add_metric(label: str, value):
            if isinstance(value, (int, float)):
                metrics.append({
                    'label': label,
                    'value': value,
                    'format': 'number'
                })

        add_metric('Total Stock Units', global_stats.get('total_stock'))
        add_metric('Low Stock Items', global_stats.get('low_stock_count'))
        add_metric('Total Stock Value (Rs)', global_stats.get('total_stock_value'))
        add_metric('Distinct SKUs', data.get('total_items'))

        if metrics:
            # Replace or extend any generic metrics
            processed['metrics'] = metrics

        # Tables: low stock items as a dedicated table if present
        low_stock_items = data.get('low_stock_items', [])
        if isinstance(low_stock_items, list) and low_stock_items:
            tables = processed.get('tables', [])
            tables.append({
                'title': 'Low Stock Items',
                'data': low_stock_items
            })
            processed['tables'] = tables

        return processed

    def _extract_metrics(self, data: Dict) -> List[Dict]:
        """Extract key metrics for KPI display"""
        metrics = []

        for key, value in data.items():
            if isinstance(value, (int, float)):
                metrics.append({
                    'label': key.replace('_', ' ').title(),
                    'value': value,
                    'format': 'number'
                })

        return metrics[:6]  # Top 6 metrics

    def _extract_tables(self, data: Dict) -> List[Dict]:
        """Extract tabular data"""
        tables = []

        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                tables.append({
                    'title': key.replace('_', ' ').title(),
                    'data': value
                })

        return tables

    def _generate_chart_specs(self, data: Dict) -> List[Dict]:
        """Generate chart specifications from data"""
        charts = []

        # Look for time series data
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 2:
                if all(isinstance(item, dict) for item in value):
                    charts.append({
                        'type': 'line',
                        'title': key.replace('_', ' ').title(),
                        'data': value
                    })

        return charts[:3]  # Limit to 3 charts

    def _generate_ai_insights(self, data: Dict, settings: Dict) -> Dict:
        """
        Generate AI insights.

        Preferred: use Anthropic Claude via official SDK if available and
        ANTHROPIC_API_KEY is set. Fallback: simple fixed placeholders.
        """
        # Fallback used if SDK or API key not configured, or on error
        fallback = {
            'summary': f"AI-generated summary of {settings['title']}",
            'key_findings': [
                "Finding 1 based on data analysis",
                "Finding 2 showing trend",
                "Finding 3 highlighting anomaly"
            ],
            'recommendations': [
                "Recommendation 1",
                "Recommendation 2"
            ]
        }

        # If Anthropic SDK is not installed, use fallback
        if anthropic is None:
            return fallback

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return fallback

        try:
            client = anthropic.Anthropic(api_key=api_key)

            # Keep payload reasonable in size
            data_json = json.dumps(data, default=str)
            if len(data_json) > 4000:
                data_json = data_json[:4000] + "... (truncated)"

            prompt = (
                "You are a retail analytics assistant. Based on the JSON data "
                f"below, generate clear insights for a report titled "
                f"\"{settings['title']}\".\n\n"
                "Return ONLY a JSON object with exactly these keys:\n"
                "  - summary: string (2-3 sentences)\n"
                "  - key_findings: array of 3-6 short bullet strings\n"
                "  - recommendations: array of 2-5 short action-oriented strings\n\n"
                "Do not include any other keys, text, or explanation.\n\n"
                "Report data (may be truncated):\n"
                f"{data_json}\n"
            )

            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=512,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}],
            )

            # Concatenate text blocks from response
            text_parts = []
            for block in response.content:
                # Newer SDKs use .type attribute; be defensive
                if getattr(block, "type", None) == "text":
                    text_parts.append(block.text)
            text = "".join(text_parts).strip()

            parsed = json.loads(text)

            return {
                'summary': parsed.get('summary') or fallback['summary'],
                'key_findings': parsed.get('key_findings') or fallback['key_findings'],
                'recommendations': parsed.get('recommendations') or fallback['recommendations'],
            }
        except Exception:
            # Any error (network, JSON parse, etc.) → safe fallback
            return fallback

    def _save_output(self, output: bytes, settings: Dict) -> str:
        """Save output to configured destination or default location"""
        # Determine save location
        if self.has_config and 'output' in self.config:
            destination = self.config['output'].get('to', './output/')
            filename_pattern = self.config['output'].get('filename_pattern', 'report_{date}_{time}')
        else:
            destination = './output/'
            filename_pattern = 'report_{date}_{time}'

        # Create output directory if local
        if destination.startswith('./') or not destination.startswith('mcp://'):
            Path(destination).mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = filename_pattern.format(
            date=datetime.now().strftime('%Y%m%d'),
            time=datetime.now().strftime('%H%M%S'),
            title=settings['title'].replace(' ', '_').lower()
        )
        filename += f".{settings['format']}"

        # Save locally (in production would handle MCP)
        if destination.startswith('./'):
            save_path = os.path.join(destination, filename)
            with open(save_path, 'wb') as f:
                f.write(output)
        else:
            save_path = f"{destination}/{filename}"
            print(f"  Would upload to: {save_path}")

        return save_path

    def _send_notification(self, report_path: str, settings: Dict):
        """Send notification that report is ready"""
        print(f"  Sending notification to: {self.config['notify']}")


def main():
    """CLI entry point"""
    import sys

    if len(sys.argv) > 1:
        # Load data from file
        data_file = sys.argv[1]
        with open(data_file, 'r') as f:
            data = json.load(f)
    else:
        # Demo data
        data = {
            "title": "Q4 2025 Sales Report",
            "revenue": 1500000,
            "growth": 15.5,
            "top_products": [
                {"name": "Product A", "sales": 500000},
                {"name": "Product B", "sales": 400000}
            ]
        }

    generator = ReportGenerator()
    result = generator.generate(data)

    print(f"\nReport Details:")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
