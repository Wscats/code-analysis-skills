"""
Code Analysis Skills - Main Entry Point

A Git-history reflection tool: scans Git repositories and produces descriptive
statistics about commit cadence, file-change patterns, code-style markers, and
code-quality artefacts (bug-fix commits, reverts, complexity).

⚠️  IMPORTANT — INTENDED USE & LIMITATIONS

This tool produces DESCRIPTIVE STATISTICS only. The output:
  - Is a NARROW, BIASED proxy. Code review, design, mentoring, on-call,
    operations, and many other contributions are invisible to Git history.
  - MUST NOT be used for performance reviews, ranking, compensation, promotion,
    discipline, or any other HR decision.
  - MUST be run only with the INFORMED CONSENT of every developer whose Git
    history is analyzed.
  - MUST be interpreted in context (role, time-zone, on-call, time-off, etc.).

Outputs: Markdown, JSON, HTML, PDF — each carrying an explicit usage notice.
"""

import json
import logging
import os
import sys
from typing import Optional

import click
import yaml

from src.scanner import RepoScanner
from src.analyzers.commit_analyzer import CommitAnalyzer
from src.analyzers.work_habit_analyzer import WorkHabitAnalyzer
from src.analyzers.efficiency_analyzer import EfficiencyAnalyzer
from src.analyzers.code_style_analyzer import CodeStyleAnalyzer
from src.analyzers.code_quality_analyzer import CodeQualityAnalyzer
from src.analyzers.slacking_analyzer import SlackingAnalyzer
from src.evaluator.developer_evaluator import DeveloperEvaluator
from src.reporters.markdown_reporter import MarkdownReporter
from src.reporters.json_reporter import JsonReporter
from src.reporters.html_reporter import HtmlReporter
from src.reporters.pdf_reporter import PdfReporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


USAGE_NOTICE_TEXT = (
    "\n⚠️  Usage notice — please read before continuing.\n"
    "\n"
    "  This tool produces a DESCRIPTIVE summary of Git history only.\n"
    "  It does NOT measure productivity, engagement, or the value of any\n"
    "  individual’s contribution. Code review, design, mentoring, on-call,\n"
    "  ops, and many other contributions are invisible to Git history.\n"
    "\n"
    "  DO NOT use the output of this tool for:\n"
    "    • performance reviews, ranking, or comparison of individual workers\n"
    "    • compensation, promotion, discipline, or PIP decisions\n"
    "    • employee surveillance or monitoring of non-consenting contributors\n"
    "\n"
    "  Run this tool only with the INFORMED CONSENT of every developer whose\n"
    "  Git history is analyzed, and ensure compliance with applicable privacy\n"
    "  and labor regulations (e.g., GDPR, local works-council rules).\n"
)


CONSENT_ENV_VAR = "CODE_ANALYSIS_ACK_USAGE_POLICY"


def run_analysis(
    repo_path: str,
    scan_all_repos: bool = False,
    authors: Optional[list] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    branch: Optional[str] = None,
    output_format: str = "markdown",
    output_path: Optional[str] = None,
    acknowledge_usage_policy: bool = False,
) -> dict:
    """
    Main analysis orchestrator.

    Args:
        repo_path: Path to a Git repo or parent directory.
        scan_all_repos: Whether to recursively scan for all .git repos.
        authors: List of author names/emails to filter. None means all.
        since: Start date in ISO format.
        until: End date in ISO format.
        branch: Branch name to analyze.
        output_format: 'json', 'markdown', 'html', or 'pdf'.
        output_path: Output file path (used for PDF generation).
        acknowledge_usage_policy: Caller must explicitly set this to True (or
            set the ``CODE_ANALYSIS_ACK_USAGE_POLICY=1`` environment variable)
            to confirm they have read the usage notice and have consent from
            every developer whose Git history will be analyzed. The tool
            refuses to run otherwise.

    Returns:
        A dict with 'report' (formatted string) and 'metrics' (raw data).
    """
    # Refuse to run analysis without explicit acknowledgement of the usage
    # notice. This is intentionally a hard gate: the analyzers below extract
    # personal Git-activity data and the project must not become a
    # frictionless surveillance tool.
    env_ack = os.environ.get(CONSENT_ENV_VAR, "").strip().lower() in (
        "1", "true", "yes", "y",
    )
    if not (acknowledge_usage_policy or env_ack):
        logger.warning(USAGE_NOTICE_TEXT)
        logger.warning(
            "Refusing to run: pass acknowledge_usage_policy=True (or set %s=1 "
            "in the environment) to confirm you have informed consent from "
            "every analyzed developer and will not use the output for HR "
            "decisions, ranking, or surveillance.",
            CONSENT_ENV_VAR,
        )
        return {
            "report": USAGE_NOTICE_TEXT + (
                "\nAnalysis refused: usage policy was not acknowledged. "
                f"Set acknowledge_usage_policy=True or {CONSENT_ENV_VAR}=1 "
                "to proceed.\n"
            ),
            "metrics": {},
            "reports": {},
        }
    # Step 1: Discover repositories
    scanner = RepoScanner()
    if scan_all_repos:
        repos = scanner.scan_directory(repo_path)
    else:
        repos = scanner.scan_single(repo_path)

    if not repos:
        logger.warning("No Git repositories found at: %s", repo_path)
        return {"report": "No Git repositories found.", "metrics": {}}

    logger.info("Found %d repository(ies) to analyze.", len(repos))

    # Step 2: Run all analyzers on each repository
    all_metrics = {}

    for repo_info in repos:
        repo_name = repo_info["name"]
        logger.info("Analyzing repository: %s", repo_name)

        common_kwargs = dict(
            authors=authors, since=since, until=until, branch=branch
        )

        commit_analyzer = CommitAnalyzer(repo_info["path"], **common_kwargs)
        work_habit_analyzer = WorkHabitAnalyzer(repo_info["path"], **common_kwargs)
        efficiency_analyzer = EfficiencyAnalyzer(repo_info["path"], **common_kwargs)
        code_style_analyzer = CodeStyleAnalyzer(repo_info["path"], **common_kwargs)
        code_quality_analyzer = CodeQualityAnalyzer(repo_info["path"], **common_kwargs)
        slacking_analyzer = SlackingAnalyzer(repo_info["path"], **common_kwargs)

        repo_metrics = {
            "commit_patterns": commit_analyzer.analyze(),
            "work_habits": work_habit_analyzer.analyze(),
            "efficiency": efficiency_analyzer.analyze(),
            "code_style": code_style_analyzer.analyze(),
            "code_quality": code_quality_analyzer.analyze(),
            "slacking": slacking_analyzer.analyze(),
        }

        # Step 2.5: Run developer evaluations
        evaluator = DeveloperEvaluator()
        repo_metrics["evaluations"] = evaluator.evaluate(repo_metrics)

        all_metrics[repo_name] = repo_metrics

    # Step 3: Generate report(s)
    # Support generating multiple formats at once
    formats_to_generate = _parse_formats(output_format)
    reports = {}

    for fmt in formats_to_generate:
        reporter = _get_reporter(fmt)

        if fmt == "pdf":
            # PDF needs a file path
            pdf_path = output_path or "report.pdf"
            if not pdf_path.endswith(".pdf"):
                pdf_path = pdf_path.rsplit(".", 1)[0] + ".pdf"
            reporter.generate_to_file(all_metrics, pdf_path)
            reports[fmt] = f"PDF saved to: {pdf_path}"
            logger.info("PDF report generated: %s", pdf_path)
        else:
            reports[fmt] = reporter.generate(all_metrics)

    # Return the primary format's report
    primary_report = reports.get(formats_to_generate[0], "")

    return {"report": primary_report, "metrics": all_metrics, "reports": reports}


def _parse_formats(output_format: str) -> list:
    """Parse output format string, supporting comma-separated multiple formats."""
    formats = [f.strip().lower() for f in output_format.split(",")]
    valid = {"markdown", "json", "html", "pdf"}
    result = []
    for f in formats:
        if f in valid:
            result.append(f)
        else:
            logger.warning("Unknown format '%s', ignoring.", f)
    return result if result else ["markdown"]


def _get_reporter(output_format: str):
    """Factory method to get the appropriate reporter."""
    reporters = {
        "markdown": MarkdownReporter,
        "json": JsonReporter,
        "html": HtmlReporter,
        "pdf": PdfReporter,
    }
    reporter_cls = reporters.get(output_format.lower())
    if not reporter_cls:
        raise ValueError(
            f"Unsupported output format: {output_format}. "
            f"Choose from: {list(reporters.keys())}"
        )
    return reporter_cls()


# ─── CLI Interface ────────────────────────────────────────────────────────────


@click.command()
@click.option(
    "--repo-path", "-r", required=True, help="Path to Git repo or parent directory."
)
@click.option(
    "--scan-all", is_flag=True, default=False, help="Scan all .git repos recursively."
)
@click.option(
    "--author", "-a", multiple=True, help="Author name/email to analyze (repeatable)."
)
@click.option("--since", "-s", default=None, help="Start date (ISO format).")
@click.option("--until", "-u", default=None, help="End date (ISO format).")
@click.option("--branch", "-b", default=None, help="Branch to analyze.")
@click.option(
    "--format",
    "-f",
    "output_format",
    default="markdown",
    help="Output format(s): markdown, json, html, pdf (comma-separated for multiple).",
)
@click.option("--output", "-o", default=None, help="Output file path (prints to stdout if omitted).")
@click.option(
    "--i-have-consent",
    "acknowledge_usage_policy",
    is_flag=True,
    default=False,
    help=(
        "Required. By passing this flag you confirm that (1) you have read the "
        "usage notice, (2) you have informed consent from every developer whose "
        "Git history will be analyzed, and (3) you will NOT use the output for "
        "performance reviews, ranking, compensation, discipline, surveillance, "
        "or any HR decision. Without this flag the tool refuses to run."
    ),
)
def cli(repo_path, scan_all, author, since, until, branch, output_format, output, acknowledge_usage_policy):
    """Code Analysis Skills - Generate a Git-history reflection report.

    \b
    Usage notice:
      This tool produces a DESCRIPTIVE summary of Git history only and
      MUST NOT be used for performance reviews, ranking, compensation,
      discipline, or any HR decision. Run only with the informed consent
      of every analyzed developer.

      You must pass --i-have-consent to confirm.
    """
    # Always print the usage notice to stderr, even when --i-have-consent
    # is set, so it travels with the command output.
    click.echo(USAGE_NOTICE_TEXT, err=True)

    authors_list = list(author) if author else None

    result = run_analysis(
        repo_path=repo_path,
        scan_all_repos=scan_all,
        authors=authors_list,
        since=since,
        until=until,
        branch=branch,
        output_format=output_format,
        output_path=output,
        acknowledge_usage_policy=acknowledge_usage_policy,
    )

    if not result.get("metrics"):
        # Refused or empty: just print the report (which contains the
        # refusal explanation) and exit non-zero so scripts notice.
        click.echo(result["report"])
        sys.exit(2 if not acknowledge_usage_policy else 1)

    # Handle multiple output formats
    formats = _parse_formats(output_format)

    if len(formats) == 1 and formats[0] != "pdf":
        report_text = result["report"]
        if output:
            ext_map = {"markdown": ".md", "json": ".json", "html": ".html"}
            out_path = output
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            click.echo(f"Report saved to: {out_path}")
        else:
            click.echo(report_text)
    else:
        # Multiple formats: save each to a file
        base = output or "report"
        if "." in base:
            base = base.rsplit(".", 1)[0]

        ext_map = {"markdown": ".md", "json": ".json", "html": ".html", "pdf": ".pdf"}
        for fmt in formats:
            if fmt == "pdf":
                # Already saved by run_analysis
                click.echo(f"PDF saved to: {base}.pdf")
                continue
            ext = ext_map.get(fmt, f".{fmt}")
            out_path = f"{base}{ext}"
            report_text = result["reports"].get(fmt, "")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            click.echo(f"{fmt.upper()} report saved to: {out_path}")


# ─── Skill Entry Point (for ClawHub) ─────────────────────────────────────────


def main(params: dict) -> dict:
    """
    ClawHub skill entry point.

    Args:
        params: Dict of parameters from skill.yaml. Must include
            ``acknowledge_usage_policy: true`` (or the
            ``CODE_ANALYSIS_ACK_USAGE_POLICY=1`` environment variable) to
            confirm informed consent and acceptable use. The tool refuses to
            run otherwise.

    Returns:
        Dict with 'report' and 'metrics' outputs.
    """
    return run_analysis(
        repo_path=params.get("repo_path", "."),
        scan_all_repos=params.get("scan_all_repos", False),
        authors=params.get("authors") or None,
        since=params.get("since") or None,
        until=params.get("until") or None,
        branch=params.get("branch") or None,
        output_format=params.get("output_format", "markdown"),
        output_path=params.get("output_path") or None,
        acknowledge_usage_policy=bool(params.get("acknowledge_usage_policy", False)),
    )


if __name__ == "__main__":
    cli()
