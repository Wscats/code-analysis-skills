"""
HTML Reporter - Generates analysis reports in HTML format.

Uses Jinja2 templates for rich, styled HTML output.
"""

from typing import Dict

from jinja2 import Template

from src.reporters.base_reporter import BaseReporter

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Analysis Report</title>
    <style>
        :root {
            --primary: #4f46e5;
            --primary-light: #818cf8;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 {
            font-size: 2rem;
            color: var(--primary);
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid var(--primary);
        }
        h2 {
            font-size: 1.5rem;
            color: var(--text);
            margin: 2rem 0 1rem;
            padding: 0.5rem 1rem;
            background: var(--primary);
            color: white;
            border-radius: 8px;
        }
        h3 {
            font-size: 1.2rem;
            color: var(--primary);
            margin: 1.5rem 0 0.5rem;
        }
        h4 {
            font-size: 1rem;
            color: var(--text-muted);
            margin: 1rem 0 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 0.5rem 0 1rem;
        }
        th, td {
            padding: 0.6rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }
        th {
            background: var(--bg);
            font-weight: 600;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
        }
        tr:hover { background: #f1f5f9; }
        .metric-value { font-weight: 600; color: var(--primary); }
        .comparison-table th { background: var(--primary); color: white; }
        .comparison-table tr:nth-child(even) { background: #f8fafc; }
        .badge {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-good { background: #dcfce7; color: #166534; }
        .badge-warn { background: #fef3c7; color: #92400e; }
        .badge-bad { background: #fee2e2; color: #991b1b; }
        footer {
            text-align: center;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.875rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Code Analysis Report</h1>

        {% for repo_name, repo_metrics in metrics.items() %}
        <h2>📁 {{ repo_name }}</h2>

        {% set all_authors = [] %}
        {% for analyzer_data in repo_metrics.values() %}
            {% for author in analyzer_data.keys() %}
                {% if author not in all_authors %}
                    {% if all_authors.append(author) %}{% endif %}
                {% endif %}
            {% endfor %}
        {% endfor %}

        {% for author in all_authors | sort %}
        <div class="card">
            <h3>👤 {{ author }}</h3>

            {% set cd = repo_metrics.get('commit_patterns', {}).get(author, {}) %}
            {% if cd %}
            <h4>📝 Commit Patterns</h4>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Total Commits</td><td class="metric-value">{{ cd.total_commits }}</td></tr>
                <tr><td>Merge Ratio</td><td>{{ "%.1f%%" | format(cd.merge_ratio * 100) }}</td></tr>
                <tr><td>Active Span</td><td>{{ cd.active_span_days }} days</td></tr>
                <tr><td>Avg Commits/Day</td><td class="metric-value">{{ cd.avg_commits_per_active_day }}</td></tr>
                <tr><td>Avg Lines Added</td><td>{{ cd.avg_lines_added }}</td></tr>
                <tr><td>Avg Lines Deleted</td><td>{{ cd.avg_lines_deleted }}</td></tr>
                <tr><td>Total Lines Added</td><td>{{ "{:,}".format(cd.total_lines_added) }}</td></tr>
                <tr><td>Total Lines Deleted</td><td>{{ "{:,}".format(cd.total_lines_deleted) }}</td></tr>
            </table>
            {% endif %}

            {% set hd = repo_metrics.get('work_habits', {}).get(author, {}) %}
            {% if hd %}
            <h4>⏰ Work Habits</h4>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Peak Hour</td><td class="metric-value">{{ hd.peak_hour }}:00</td></tr>
                <tr><td>Weekend Ratio</td><td>{{ "%.1f%%" | format(hd.weekend_ratio * 100) }}</td></tr>
                <tr><td>Late Night Ratio</td><td>
                    {{ "%.1f%%" | format(hd.late_night_ratio * 100) }}
                    {% if hd.late_night_ratio > 0.3 %}
                        <span class="badge badge-warn">High</span>
                    {% endif %}
                </td></tr>
                <tr><td>Longest Streak</td><td>{{ hd.longest_streak_days }} days</td></tr>
                <tr><td>Avg Gap</td><td>{{ hd.avg_gap_between_commits_hours }} hrs</td></tr>
            </table>
            {% endif %}

            {% set ed = repo_metrics.get('efficiency', {}).get(author, {}) %}
            {% if ed %}
            <h4>🚀 Efficiency</h4>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Churn Rate</td><td>{{ "%.1f%%" | format(ed.churn_rate * 100) }}</td></tr>
                <tr><td>Rework Ratio</td><td>
                    {{ "%.1f%%" | format(ed.rework_ratio * 100) }}
                    {% if ed.rework_ratio > 0.3 %}
                        <span class="badge badge-warn">High Rework</span>
                    {% endif %}
                </td></tr>
                <tr><td>Lines/Commit</td><td>{{ ed.lines_per_commit }}</td></tr>
                <tr><td>Files Touched</td><td>{{ ed.unique_files_touched }}</td></tr>
                <tr><td>Ownership Ratio</td><td>{{ "%.1f%%" | format(ed.ownership_ratio * 100) }}</td></tr>
                <tr><td>Bus Factor</td><td>{{ ed.repo_avg_bus_factor }}</td></tr>
            </table>
            {% endif %}

            {% set qd = repo_metrics.get('code_quality', {}).get(author, {}) %}
            {% if qd %}
            <h4>🔍 Code Quality</h4>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Bug Fix Ratio</td><td>
                    {{ "%.1f%%" | format(qd.bug_fix_ratio * 100) }}
                    {% if qd.bug_fix_ratio > 0.5 %}
                        <span class="badge badge-bad">High</span>
                    {% elif qd.bug_fix_ratio > 0.3 %}
                        <span class="badge badge-warn">Moderate</span>
                    {% else %}
                        <span class="badge badge-good">Low</span>
                    {% endif %}
                </td></tr>
                <tr><td>Revert Ratio</td><td>{{ "%.1f%%" | format(qd.revert_ratio * 100) }}</td></tr>
                <tr><td>Large Commit Ratio</td><td>{{ "%.1f%%" | format(qd.large_commit_ratio * 100) }}</td></tr>
                <tr><td>Test Modification Ratio</td><td>{{ "%.1f%%" | format(qd.test_modification_ratio * 100) }}</td></tr>
                <tr><td>Avg Commit Size</td><td>{{ qd.avg_commit_size }} lines</td></tr>
                {% if qd.avg_python_complexity > 0 %}
                <tr><td>Avg Python Complexity</td><td>{{ qd.avg_python_complexity }}</td></tr>
                {% endif %}
            </table>
            {% endif %}
        </div>
        {% endfor %}
        {% endfor %}

        <footer>
            Generated by <strong>Code Analysis Skills</strong> | Powered by ClawHub
        </footer>
    </div>
</body>
</html>
"""


class HtmlReporter(BaseReporter):
    """Generates styled HTML reports from analysis metrics."""

    def generate(self, metrics: Dict) -> str:
        """Generate an HTML report using Jinja2 template."""
        template = Template(HTML_TEMPLATE)
        return template.render(metrics=metrics)
