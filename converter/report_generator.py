"""
HTML report generation for ZIM conversion validation.
"""

import logging
from datetime import datetime
from pathlib import Path


def generate_link_validation_report(lst_missing_index, lst_unknown, lst_errors, output_path):
    """
    Generate an HTML report of link validation issues.

    Args:
        lst_missing_index: List of missing index page warnings
        lst_unknown: List of unknown file extensions
        lst_errors: List of processing errors
        output_path: Directory to save the report

    Returns:
        Path: Path to generated report or None if failed
    """
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZIM Conversion Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-box { background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #4CAF50; }
        .stat-box.warning { border-left-color: #ff9800; }
        .stat-box.error { border-left-color: #f44336; }
        .stat-number { font-size: 32px; font-weight: bold; color: #333; }
        .stat-label { color: #666; font-size: 14px; }
        .issue-list { background: #fafafa; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .issue-item { padding: 8px; margin: 5px 0; background: white; border-left: 3px solid #ff9800; }
        .error-item { border-left-color: #f44336; }
        code { background: #e0e0e0; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
        .timestamp { color: #999; font-size: 12px; text-align: right; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ZIM Conversion Report</h1>

        <div class="summary">
            <div class="stat-box warning">
                <div class="stat-number">{missing_links_count}</div>
                <div class="stat-label">Missing Index Pages</div>
            </div>
            <div class="stat-box warning">
                <div class="stat-number">{unknown_mime_count}</div>
                <div class="stat-label">Unknown MIME Types</div>
            </div>
            <div class="stat-box error">
                <div class="stat-number">{errors_count}</div>
                <div class="stat-label">Processing Errors</div>
            </div>
        </div>

        {missing_section}
        {mime_section}
        {error_section}

        <div class="timestamp">Generated: {timestamp}</div>
    </div>
</body>
</html>"""

    missing_section = ""
    if lst_missing_index:
        items = "\n".join([f'<div class="issue-item">{item}</div>' for item in lst_missing_index])
        missing_section = f"""
        <h2>Missing Index Pages ({len(lst_missing_index)})</h2>
        <p>Links ending with <code>/</code> but no <code>index.html</code> file found:</p>
        <div class="issue-list">{items}</div>
        """

    mime_section = ""
    if lst_unknown:
        unique_unknown = sorted(set(lst_unknown))
        items = "\n".join([f'<div class="issue-item"><code>.{ext}</code></div>' for ext in unique_unknown])
        mime_section = f"""
        <h2>Unknown MIME Types ({len(unique_unknown)})</h2>
        <p>File extensions without registered MIME types (treated as HTML):</p>
        <div class="issue-list">{items}</div>
        """

    error_section = ""
    if lst_errors:
        items = "\n".join([f'<div class="issue-item error-item">{item}</div>' for item in lst_errors])
        error_section = f"""
        <h2>Processing Errors ({len(lst_errors)})</h2>
        <p>Files that failed to process:</p>
        <div class="issue-list">{items}</div>
        """

    html_content = html_content.format(
        missing_links_count=len(lst_missing_index),
        unknown_mime_count=len(set(lst_unknown)),
        errors_count=len(lst_errors),
        missing_section=missing_section,
        mime_section=mime_section,
        error_section=error_section,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    report_path = Path(output_path) / "conversion_report.html"
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return report_path
    except Exception as e:
        logging.error(f"Failed to generate report: {e}")
        return None
