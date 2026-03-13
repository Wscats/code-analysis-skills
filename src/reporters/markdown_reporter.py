"""
Markdown Reporter - Generates analysis reports in Markdown format.
"""

from typing import Dict

from src.reporters.base_reporter import BaseReporter


class MarkdownReporter(BaseReporter):
    """Generates beautiful Markdown reports from analysis metrics."""

    def generate(self, metrics: Dict) -> str:
        """Generate a Markdown report."""
        lines = []
        lines.append("# 📊 Code Analysis Report\n")

        for repo_name, repo_metrics in metrics.items():
            lines.append(f"## 📁 Repository: {repo_name}\n")

            # Collect all authors across analyzers
            all_authors = set()
            for analyzer_data in repo_metrics.values():
                all_authors.update(analyzer_data.keys())

            if not all_authors:
                lines.append("_No data available for this repository._\n")
                continue

            for author in sorted(all_authors):
                lines.append(f"### 👤 {author}\n")

                # Commit Patterns
                commit_data = repo_metrics.get("commit_patterns", {}).get(author, {})
                if commit_data:
                    lines.append("#### 📝 Commit Patterns\n")
                    lines.append("| Metric | Value |")
                    lines.append("|--------|-------|")
                    lines.append(f"| Total Commits | {commit_data.get('total_commits', 0)} |")
                    lines.append(f"| Non-merge Commits | {commit_data.get('non_merge_commits', 0)} |")
                    lines.append(f"| Merge Ratio | {commit_data.get('merge_ratio', 0):.1%} |")
                    lines.append(f"| Active Span (days) | {commit_data.get('active_span_days', 0)} |")
                    lines.append(f"| Unique Active Days | {commit_data.get('unique_active_days', 0)} |")
                    lines.append(f"| Avg Commits/Active Day | {commit_data.get('avg_commits_per_active_day', 0)} |")
                    lines.append(f"| Avg Message Length | {commit_data.get('avg_message_length', 0)} |")
                    lines.append(f"| Avg Lines Added | {commit_data.get('avg_lines_added', 0)} |")
                    lines.append(f"| Avg Lines Deleted | {commit_data.get('avg_lines_deleted', 0)} |")
                    lines.append(f"| Avg Files Changed | {commit_data.get('avg_files_changed', 0)} |")
                    lines.append(f"| Total Lines Added | {commit_data.get('total_lines_added', 0):,} |")
                    lines.append(f"| Total Lines Deleted | {commit_data.get('total_lines_deleted', 0):,} |")
                    lines.append("")

                # Work Habits
                habit_data = repo_metrics.get("work_habits", {}).get(author, {})
                if habit_data:
                    lines.append("#### ⏰ Work Habits\n")
                    lines.append("| Metric | Value |")
                    lines.append("|--------|-------|")
                    lines.append(f"| Peak Hour | {habit_data.get('peak_hour', 'N/A')}:00 |")
                    lines.append(f"| Weekday Commits | {habit_data.get('weekday_commits', 0)} |")
                    lines.append(f"| Weekend Commits | {habit_data.get('weekend_commits', 0)} |")
                    lines.append(f"| Weekend Ratio | {habit_data.get('weekend_ratio', 0):.1%} |")
                    lines.append(f"| Late Night Ratio | {habit_data.get('late_night_ratio', 0):.1%} |")
                    lines.append(f"| Longest Streak (days) | {habit_data.get('longest_streak_days', 0)} |")
                    lines.append(f"| Avg Gap Between Commits (hrs) | {habit_data.get('avg_gap_between_commits_hours', 0)} |")
                    lines.append("")

                    # Time slot distribution
                    slots = habit_data.get("time_slot_distribution", {})
                    if slots:
                        lines.append("**Time Slot Distribution:**\n")
                        lines.append("| Time Slot | Commits |")
                        lines.append("|-----------|---------|")
                        for slot, count in sorted(slots.items()):
                            lines.append(f"| {slot.replace('_', ' ').title()} | {count} |")
                        lines.append("")

                    # Day of week distribution
                    dow = habit_data.get("day_of_week_distribution", {})
                    if dow:
                        lines.append("**Day of Week Distribution:**\n")
                        lines.append("| Day | Commits |")
                        lines.append("|-----|---------|")
                        for day, count in dow.items():
                            lines.append(f"| {day} | {count} |")
                        lines.append("")

                # Efficiency
                eff_data = repo_metrics.get("efficiency", {}).get(author, {})
                if eff_data:
                    lines.append("#### 🚀 Development Efficiency\n")
                    lines.append("| Metric | Value |")
                    lines.append("|--------|-------|")
                    lines.append(f"| Churn Rate | {eff_data.get('churn_rate', 0):.1%} |")
                    lines.append(f"| Rework Ratio | {eff_data.get('rework_ratio', 0):.1%} |")
                    lines.append(f"| Lines per Commit | {eff_data.get('lines_per_commit', 0)} |")
                    lines.append(f"| Unique Files Touched | {eff_data.get('unique_files_touched', 0)} |")
                    lines.append(f"| Owned Files | {eff_data.get('owned_files_count', 0)} |")
                    lines.append(f"| Ownership Ratio | {eff_data.get('ownership_ratio', 0):.1%} |")
                    lines.append(f"| Repo Avg Bus Factor | {eff_data.get('repo_avg_bus_factor', 0)} |")
                    lines.append("")

                # Code Style
                style_data = repo_metrics.get("code_style", {}).get(author, {})
                if style_data:
                    lines.append("#### 🎨 Code Style\n")
                    lines.append("| Metric | Value |")
                    lines.append("|--------|-------|")
                    lines.append(f"| Conventional Commit Ratio | {style_data.get('conventional_commit_ratio', 0):.1%} |")
                    lines.append(f"| Issue Reference Ratio | {style_data.get('issue_reference_ratio', 0):.1%} |")
                    lines.append(f"| Avg Change Size (lines) | {style_data.get('avg_change_size_lines', 0)} |")
                    lines.append("")

                    lang_dist = style_data.get("language_distribution", {})
                    if lang_dist:
                        lines.append("**Language Distribution:**\n")
                        lines.append("| Extension | Modifications |")
                        lines.append("|-----------|---------------|")
                        for ext, count in sorted(lang_dist.items(), key=lambda x: -x[1]):
                            lines.append(f"| {ext} | {count} |")
                        lines.append("")

                    cat_dist = style_data.get("file_category_distribution", {})
                    if cat_dist:
                        lines.append("**File Category Distribution:**\n")
                        lines.append("| Category | Count |")
                        lines.append("|----------|-------|")
                        for cat, count in sorted(cat_dist.items(), key=lambda x: -x[1]):
                            lines.append(f"| {cat} | {count} |")
                        lines.append("")

                # Code Quality
                quality_data = repo_metrics.get("code_quality", {}).get(author, {})
                if quality_data:
                    lines.append("#### 🔍 Code Quality\n")
                    lines.append("| Metric | Value |")
                    lines.append("|--------|-------|")
                    lines.append(f"| Bug Fix Ratio | {quality_data.get('bug_fix_ratio', 0):.1%} |")
                    lines.append(f"| Revert Ratio | {quality_data.get('revert_ratio', 0):.1%} |")
                    lines.append(f"| Large Commit Ratio | {quality_data.get('large_commit_ratio', 0):.1%} |")
                    lines.append(f"| Test Modification Ratio | {quality_data.get('test_modification_ratio', 0):.1%} |")
                    lines.append(f"| Doc Modification Ratio | {quality_data.get('doc_modification_ratio', 0):.1%} |")
                    lines.append(f"| Avg Commit Size | {quality_data.get('avg_commit_size', 0)} |")
                    lines.append(f"| Median Commit Size | {quality_data.get('median_commit_size', 0)} |")
                    if quality_data.get("avg_python_complexity", 0) > 0:
                        lines.append(f"| Avg Python Complexity | {quality_data.get('avg_python_complexity', 0)} |")
                    lines.append("")

                lines.append("---\n")

        # Comparison summary if multiple authors
        lines.append(self._generate_comparison_summary(metrics))

        return "\n".join(lines)

    def _generate_comparison_summary(self, metrics: Dict) -> str:
        """Generate a comparison summary table across all authors."""
        # Aggregate across repos
        author_summary = {}
        for repo_name, repo_metrics in metrics.items():
            commit_data = repo_metrics.get("commit_patterns", {})
            habit_data = repo_metrics.get("work_habits", {})
            eff_data = repo_metrics.get("efficiency", {})
            quality_data = repo_metrics.get("code_quality", {})

            for author in commit_data:
                if author not in author_summary:
                    author_summary[author] = {
                        "total_commits": 0,
                        "total_lines": 0,
                        "avg_commits_day": 0,
                        "weekend_ratio": 0,
                        "late_night_ratio": 0,
                        "bug_fix_ratio": 0,
                        "churn_rate": 0,
                    }

                cd = commit_data.get(author, {})
                hd = habit_data.get(author, {})
                ed = eff_data.get(author, {})
                qd = quality_data.get(author, {})

                author_summary[author]["total_commits"] += cd.get("total_commits", 0)
                author_summary[author]["total_lines"] += cd.get("total_lines_added", 0) + cd.get("total_lines_deleted", 0)
                author_summary[author]["avg_commits_day"] = cd.get("avg_commits_per_active_day", 0)
                author_summary[author]["weekend_ratio"] = hd.get("weekend_ratio", 0)
                author_summary[author]["late_night_ratio"] = hd.get("late_night_ratio", 0)
                author_summary[author]["bug_fix_ratio"] = qd.get("bug_fix_ratio", 0)
                author_summary[author]["churn_rate"] = ed.get("churn_rate", 0)

        if len(author_summary) < 2:
            return ""

        lines = []
        lines.append("## 📋 Author Comparison Summary\n")
        lines.append("| Author | Commits | Lines Changed | Commits/Day | Weekend % | Late Night % | Bug Fix % | Churn Rate |")
        lines.append("|--------|---------|---------------|-------------|-----------|-------------|-----------|------------|")

        for author, data in sorted(author_summary.items(), key=lambda x: -x[1]["total_commits"]):
            lines.append(
                f"| {author} "
                f"| {data['total_commits']} "
                f"| {data['total_lines']:,} "
                f"| {data['avg_commits_day']} "
                f"| {data['weekend_ratio']:.1%} "
                f"| {data['late_night_ratio']:.1%} "
                f"| {data['bug_fix_ratio']:.1%} "
                f"| {data['churn_rate']:.1%} |"
            )

        lines.append("")
        return "\n".join(lines)
