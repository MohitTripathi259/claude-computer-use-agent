"""
Template Manager
Provides built-in report templates
"""

from typing import Dict, Any, Optional


class TemplateManager:
    """Manages report templates"""

    def __init__(self):
        self.templates = {
            'executive_summary': self._executive_summary_template,
            'financial_report': self._financial_report_template,
            'project_status': self._project_status_template,
            'data_analysis': self._data_analysis_template,
            'generic': self._generic_template
        }

    def apply_template(
        self,
        template_name: str,
        data: Dict,
        branding: Optional[Dict] = None,
        ai_insights: bool = True
    ) -> Dict:
        """Apply template to data"""
        template_func = self.templates.get(template_name, self._generic_template)
        return template_func(data, branding, ai_insights)

    def _executive_summary_template(
        self,
        data: Dict,
        branding: Optional[Dict],
        ai_insights: bool
    ) -> Dict:
        """Executive summary template - one page overview"""
        return {
            'template': 'executive_summary',
            'layout': 'single_page',
            'sections': [
                {
                    'type': 'header',
                    'content': {
                        'title': data.get('title'),
                        'logo': branding.get('logo') if branding else None
                    }
                },
                {
                    'type': 'kpi_cards',
                    'content': data.get('metrics', [])[:4]
                },
                {
                    'type': 'summary_text',
                    'content': data.get('ai_insights', {}).get('summary', '')
                },
                {
                    'type': 'bullet_points',
                    'title': 'Key Findings',
                    'content': data.get('ai_insights', {}).get('key_findings', [])
                }
            ]
        }

    def _financial_report_template(self, data: Dict, branding: Optional[Dict], ai_insights: bool) -> Dict:
        """Financial report template"""
        return {
            'template': 'financial_report',
            'layout': 'multi_page',
            'sections': [
                {'type': 'cover_page', 'content': {'title': data.get('title')}},
                {'type': 'financial_summary', 'content': data.get('metrics', [])},
                {'type': 'charts', 'content': data.get('charts', [])},
                {'type': 'detailed_tables', 'content': data.get('tables', [])}
            ]
        }

    def _project_status_template(self, data: Dict, branding: Optional[Dict], ai_insights: bool) -> Dict:
        """Project status template"""
        return {
            'template': 'project_status',
            'sections': [
                {'type': 'header', 'content': {'title': data.get('title')}},
                {'type': 'status_indicators', 'content': data.get('metrics')},
                {'type': 'timeline', 'content': data.get('milestones', [])},
                {'type': 'risks', 'content': data.get('risks', [])}
            ]
        }

    def _data_analysis_template(self, data: Dict, branding: Optional[Dict], ai_insights: bool) -> Dict:
        """
        Data analysis / inventory analysis template.

        NOTE: This version is aligned with PDFFormatter, which expects
        sections to use 'name' and optional 'title' fields such as:
        - header
        - kpi_dashboard
        - data_tables
        - key_findings
        - recommendations
        """
        ai = data.get('ai_insights', {}) if ai_insights else {}

        sections = [
            {
                'template': 'data_analysis',
                'name': 'header',
                'title': data.get('title'),
                'content': {
                    'title': data.get('title')
                }
            }
        ]

        # KPI section (top metrics)
        if data.get('metrics'):
            sections.append({
                'name': 'kpi_dashboard',
                'title': 'Key Metrics',
                'content': {
                    'metrics': data.get('metrics', [])
                }
            })

        # Data tables / numeric breakdowns
        # Pass full processed data so PDFFormatter can render totals,
        # breakdowns, products/low-stock tables, etc.
        sections.append({
            'name': 'data_tables',
            'title': 'Data Overview',
            'content': {
                'data': {
                    # Use common keys that PDFFormatter._build_data_section understands
                    'totals': data.get('totals'),
                    'global_stats': data.get('global_stats'),
                    'breakdown': data.get('breakdown'),
                    'top_products': data.get('top_products') or data.get('products'),
                    'tables': data.get('tables', [])
                } or data,
                # Also expose tables at the same level for formatter convenience
                'tables': data.get('tables', [])
            }
        })

        # AI-generated insights
        if ai:
            # Key findings
            if ai.get('key_findings'):
                sections.append({
                    'name': 'key_findings',
                    'title': 'Key Findings',
                    'content': {
                        'findings': ai.get('key_findings', [])
                    }
                })

            # Recommendations
            if ai.get('recommendations'):
                sections.append({
                    'name': 'recommendations',
                    'title': 'Recommendations',
                    'content': {
                        'items': ai.get('recommendations', [])
                    }
                })

        return {
            'template': 'data_analysis',
            'sections': sections
        }

    def _generic_template(self, data: Dict, branding: Optional[Dict], ai_insights: bool) -> Dict:
        """Generic flexible template"""
        sections = [
            {'type': 'header', 'content': {'title': data.get('title')}}
        ]

        if data.get('metrics'):
            sections.append({'type': 'metrics', 'content': data['metrics']})

        if data.get('charts'):
            sections.append({'type': 'charts', 'content': data['charts']})

        if data.get('tables'):
            sections.append({'type': 'tables', 'content': data['tables']})

        if ai_insights and data.get('ai_insights'):
            sections.append({'type': 'insights', 'content': data['ai_insights']})

        return {
            'template': 'generic',
            'sections': sections
        }
