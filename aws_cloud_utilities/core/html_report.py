"""HTML Report Generator for AWS Cloud Utilities.

This module provides a reusable HTML report generation system that can be used
across different AWS commands to create formatted, responsive HTML reports.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ReportSection:
    """Represents a section in the HTML report."""

    title: str
    content: str
    section_type: str = "default"  # default, summary, table, warning, success, error
    collapsible: bool = False
    expanded: bool = True


@dataclass
class ReportMetadata:
    """Metadata for the HTML report."""

    title: str
    generated_at: datetime = field(default_factory=datetime.now)
    aws_profile: Optional[str] = None
    aws_region: Optional[str] = None
    description: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)


class HTMLReportGenerator:
    """Generates HTML reports with a modern, responsive design."""

    # CSS styles for the report
    CSS_TEMPLATE = """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }

        .header h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }

        .header .subtitle {
            font-size: 14px;
            opacity: 0.9;
        }

        .metadata {
            background: #f8f9fa;
            padding: 20px 30px;
            border-bottom: 1px solid #e0e0e0;
        }

        .metadata-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }

        .metadata-item {
            display: flex;
            flex-direction: column;
        }

        .metadata-label {
            font-size: 11px;
            text-transform: uppercase;
            color: #666;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }

        .metadata-value {
            font-size: 14px;
            color: #333;
            font-weight: 500;
        }

        .content {
            padding: 30px;
        }

        .section {
            margin-bottom: 30px;
        }

        .section:last-child {
            margin-bottom: 0;
        }

        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
            cursor: pointer;
            user-select: none;
        }

        .section-title {
            font-size: 20px;
            font-weight: 600;
            color: #333;
        }

        .toggle-icon {
            font-size: 20px;
            color: #666;
            transition: transform 0.3s ease;
        }

        .toggle-icon.collapsed {
            transform: rotate(-90deg);
        }

        .section-content {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }

        .section-content.hidden {
            display: none;
        }

        .section-summary {
            background: #e8f4f8;
            border-left-color: #0091ea;
        }

        .section-warning {
            background: #fff3e0;
            border-left-color: #ff9800;
        }

        .section-error {
            background: #ffebee;
            border-left-color: #f44336;
        }

        .section-success {
            background: #e8f5e9;
            border-left-color: #4caf50;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 6px;
            overflow: hidden;
        }

        th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        td {
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
            font-size: 14px;
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover {
            background: #f8f9fa;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .badge-primary {
            background: #e3f2fd;
            color: #1976d2;
        }

        .badge-success {
            background: #e8f5e9;
            color: #388e3c;
        }

        .badge-warning {
            background: #fff3e0;
            color: #f57c00;
        }

        .badge-error {
            background: #ffebee;
            color: #d32f2f;
        }

        .badge-info {
            background: #e0f7fa;
            color: #0097a7;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .stat-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: #333;
            margin-top: 8px;
        }

        .footer {
            background: #f8f9fa;
            padding: 20px 30px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            color: #666;
            font-size: 13px;
        }

        pre {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            line-height: 1.5;
        }

        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
        }

        @media (max-width: 768px) {
            body {
                padding: 10px;
            }

            .header {
                padding: 20px;
            }

            .header h1 {
                font-size: 22px;
            }

            .content {
                padding: 20px;
            }

            .metadata-grid {
                grid-template-columns: 1fr;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    """

    # JavaScript for interactive features
    JS_TEMPLATE = """
    <script>
        function toggleSection(sectionId) {
            const content = document.getElementById(sectionId);
            const icon = document.getElementById(sectionId + '-icon');

            if (content.classList.contains('hidden')) {
                content.classList.remove('hidden');
                icon.classList.remove('collapsed');
            } else {
                content.classList.add('hidden');
                icon.classList.add('collapsed');
            }
        }

        // Auto-expand all sections on load (optional)
        document.addEventListener('DOMContentLoaded', function() {
            console.log('AWS Cloud Utilities Report loaded');
        });
    </script>
    """

    def __init__(self, metadata: ReportMetadata):
        """Initialize the HTML report generator.

        Args:
            metadata: Report metadata including title, timestamps, and custom fields
        """
        self.metadata = metadata
        self.sections: List[ReportSection] = []

    def add_section(
        self,
        title: str,
        content: str,
        section_type: str = "default",
        collapsible: bool = False,
        expanded: bool = True,
    ) -> None:
        """Add a section to the report.

        Args:
            title: Section title
            content: HTML content for the section
            section_type: Type of section (default, summary, table, warning, success, error)
            collapsible: Whether the section can be collapsed
            expanded: Whether the section is expanded by default (only if collapsible=True)
        """
        section = ReportSection(
            title=title,
            content=content,
            section_type=section_type,
            collapsible=collapsible,
            expanded=expanded,
        )
        self.sections.append(section)

    def _generate_header(self) -> str:
        """Generate the report header HTML."""
        html = f"""
        <div class="header">
            <h1>{self.metadata.title}</h1>
            <div class="subtitle">AWS Cloud Utilities Report</div>
        </div>
        """
        return html

    def _generate_metadata(self) -> str:
        """Generate the metadata section HTML."""
        metadata_items = []

        # Generated timestamp
        metadata_items.append(
            f"""
            <div class="metadata-item">
                <div class="metadata-label">Generated At</div>
                <div class="metadata-value">{self.metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
            </div>
            """
        )

        # AWS Profile
        if self.metadata.aws_profile:
            metadata_items.append(
                f"""
                <div class="metadata-item">
                    <div class="metadata-label">AWS Profile</div>
                    <div class="metadata-value">{self.metadata.aws_profile}</div>
                </div>
                """
            )

        # AWS Region
        if self.metadata.aws_region:
            metadata_items.append(
                f"""
                <div class="metadata-item">
                    <div class="metadata-label">AWS Region</div>
                    <div class="metadata-value">{self.metadata.aws_region}</div>
                </div>
                """
            )

        # Custom fields
        for key, value in self.metadata.custom_fields.items():
            metadata_items.append(
                f"""
                <div class="metadata-item">
                    <div class="metadata-label">{key}</div>
                    <div class="metadata-value">{value}</div>
                </div>
                """
            )

        html = f"""
        <div class="metadata">
            <div class="metadata-grid">
                {''.join(metadata_items)}
            </div>
        </div>
        """
        return html

    def _generate_section(self, section: ReportSection, index: int) -> str:
        """Generate HTML for a single section.

        Args:
            section: The section to generate
            index: Section index for unique IDs

        Returns:
            HTML string for the section
        """
        section_id = f"section-{index}"
        section_class = f"section-content section-{section.section_type}"

        if section.collapsible and not section.expanded:
            section_class += " hidden"

        if section.collapsible:
            header = f"""
            <div class="section-header" onclick="toggleSection('{section_id}')">
                <div class="section-title">{section.title}</div>
                <div class="toggle-icon {'collapsed' if not section.expanded else ''}" id="{section_id}-icon">▼</div>
            </div>
            """
        else:
            header = f"""
            <div class="section-header">
                <div class="section-title">{section.title}</div>
            </div>
            """

        html = f"""
        <div class="section">
            {header}
            <div class="{section_class}" id="{section_id}">
                {section.content}
            </div>
        </div>
        """
        return html

    def _generate_content(self) -> str:
        """Generate the main content HTML."""
        sections_html = []
        for i, section in enumerate(self.sections):
            sections_html.append(self._generate_section(section, i))

        html = f"""
        <div class="content">
            {''.join(sections_html)}
        </div>
        """
        return html

    def _generate_footer(self) -> str:
        """Generate the report footer HTML."""
        html = """
        <div class="footer">
            Generated by AWS Cloud Utilities -
            <a href="https://github.com/jon-the-dev/aws-cloud-tools" style="color: #667eea; text-decoration: none;">
                View on GitHub
            </a>
        </div>
        """
        return html

    def generate(self) -> str:
        """Generate the complete HTML report.

        Returns:
            Complete HTML document as a string
        """
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.metadata.title}</title>
    {self.CSS_TEMPLATE}
</head>
<body>
    <div class="container">
        {self._generate_header()}
        {self._generate_metadata()}
        {self._generate_content()}
        {self._generate_footer()}
    </div>
    {self.JS_TEMPLATE}
</body>
</html>
"""
        return html

    def save(self, filepath: Union[str, Path]) -> None:
        """Save the report to an HTML file.

        Args:
            filepath: Path to save the HTML file
        """
        filepath = Path(filepath)

        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Generate and save HTML
        html_content = self.generate()
        filepath.write_text(html_content, encoding="utf-8")

        logger.info(f"HTML report saved to {filepath}")


# Utility functions for creating common report components


def create_table_html(
    headers: List[str], rows: List[List[Any]], table_id: Optional[str] = None
) -> str:
    """Create an HTML table from headers and rows.

    Args:
        headers: List of column headers
        rows: List of rows, where each row is a list of cell values
        table_id: Optional ID for the table element

    Returns:
        HTML string for the table
    """
    table_attrs = f'id="{table_id}"' if table_id else ""

    header_html = "".join([f"<th>{header}</th>" for header in headers])
    rows_html = []

    for row in rows:
        cells_html = "".join([f"<td>{cell}</td>" for cell in row])
        rows_html.append(f"<tr>{cells_html}</tr>")

    html = f"""
    <table {table_attrs}>
        <thead>
            <tr>{header_html}</tr>
        </thead>
        <tbody>
            {''.join(rows_html)}
        </tbody>
    </table>
    """
    return html


def create_stats_grid_html(stats: Dict[str, Union[str, int, float]]) -> str:
    """Create a statistics grid display.

    Args:
        stats: Dictionary of stat label to value

    Returns:
        HTML string for the stats grid
    """
    stat_cards = []
    for label, value in stats.items():
        stat_cards.append(
            f"""
            <div class="stat-card">
                <div class="stat-label">{label}</div>
                <div class="stat-value">{value}</div>
            </div>
            """
        )

    html = f"""
    <div class="stats-grid">
        {''.join(stat_cards)}
    </div>
    """
    return html


def create_badge(text: str, badge_type: str = "primary") -> str:
    """Create a badge HTML element.

    Args:
        text: Badge text
        badge_type: Badge type (primary, success, warning, error, info)

    Returns:
        HTML string for the badge
    """
    return f'<span class="badge badge-{badge_type}">{text}</span>'


def create_list_html(items: List[str], ordered: bool = False) -> str:
    """Create an HTML list from items.

    Args:
        items: List of items to display
        ordered: Whether to create an ordered list (ol) or unordered list (ul)

    Returns:
        HTML string for the list
    """
    list_tag = "ol" if ordered else "ul"
    items_html = "".join([f"<li>{item}</li>" for item in items])
    return f"<{list_tag}>{items_html}</{list_tag}>"
