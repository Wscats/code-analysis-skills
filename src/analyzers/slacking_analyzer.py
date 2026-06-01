"""
Engagement Signal Analyzer.

⚠️  IMPORTANT — INTENDED USE & LIMITATIONS

This analyzer extracts *aggregate* commit-pattern signals (sparsity, gap size,
trivial-change ratio, etc.) from a Git repository.

It is intended ONLY for:
  - Self-reflection by the developer being analyzed (with their consent)
  - Aggregate, anonymized team-health diagnostics
  - Open-source contribution-pattern research with public data

It is NOT a productivity meter, a "slacking detector", or an employee-performance
metric, despite the legacy name `SlackingAnalyzer` kept here for backward
compatibility. Git activity is a narrow, biased proxy that misses code review,
mentoring, design, ops work, on-call, refactor planning, pair-programming, and
many other forms of contribution. Low signal values do NOT mean low engagement
or low value, and high signal values do NOT mean someone is "slacking".

DO NOT use the output of this analyzer to:
  - Make hiring, firing, promotion, compensation, or PIP decisions
  - Rank, grade, or publicly compare individual developers
  - Surveil employees or monitor non-consenting contributors
  - Generate "leaderboards" of individual workers

By using this module you accept responsibility for ensuring informed consent
from every developer whose data is analyzed and for compliance with applicable
privacy and labor regulations (e.g., GDPR, local works-council rules).
"""

import logging
from collections import defaultdict, Counter
from typing import Dict

from src.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

# Thresholds (tuning knobs only — do not infer "performance" from these)
TRIVIAL_COMMIT_LINE_THRESHOLD = 5  # commits with <= 5 lines changed
LARGE_GAP_HOURS = 72  # 3 days without commits
HIGH_ADD_DELETE_RATIO = 10  # added/deleted ratio above this is unusually high


class SlackingAnalyzer(BaseAnalyzer):
    """
    Computes neutral, aggregate engagement-signal metrics for each author.

    The composite ``engagement_signal_score`` ranges from 0 to 100 and reflects
    *how sparse / bursty / low-volume* the Git activity looks relative to the
    active span. It is a descriptive statistic, NOT a judgement of the person.

    The legacy class name ``SlackingAnalyzer`` and the legacy field name
    ``slacking_index`` are retained for backward compatibility only — readers
    should treat them as ``EngagementSignalAnalyzer`` and
    ``engagement_signal_score`` respectively.
    """

    # Neutral, descriptive labels — no person-judgement language.
    LEVEL_DESCRIPTIONS = [
        (20, "Dense activity",      "活跃密集",   "Frequent commits over the active span."),
        (40, "Regular activity",    "规律活跃",   "Typical commit cadence."),
        (60, "Mixed cadence",       "节奏不均",   "Mixed cadence with some quiet stretches."),
        (80, "Sparse cadence",      "节奏稀疏",   "Many quiet stretches; signal is partial — context required."),
        (100, "Very sparse cadence","节奏非常稀疏","Activity is concentrated in short bursts. Read with full context."),
    ]

    def analyze(self) -> Dict:
        """
        Analyze engagement signals for each author.

        Returns:
            Dict keyed by author name with neutral, aggregate signal metrics.
        """
        author_data = defaultdict(lambda: {
            "commit_times": [],
            "commit_dates": [],
            "lines_added": [],
            "lines_deleted": [],
            "files_changed": [],
            "commit_messages": [],
            "file_paths": [],
            "weekdays": [],
        })

        for commit in self._get_commits():
            author = commit.author.name
            data = author_data[author]
            data["commit_times"].append(commit.committer_date)
            data["commit_dates"].append(commit.committer_date.date())
            data["commit_messages"].append(commit.msg)
            data["weekdays"].append(commit.committer_date.weekday())

            total_added = 0
            total_deleted = 0
            files = 0
            paths = []
            for mod in commit.modified_files:
                total_added += mod.added_lines
                total_deleted += mod.deleted_lines
                files += 1
                if mod.new_path:
                    paths.append(mod.new_path)

            data["lines_added"].append(total_added)
            data["lines_deleted"].append(total_deleted)
            data["files_changed"].append(files)
            data["file_paths"].append(paths)

        result = {}
        for author, data in author_data.items():
            total = len(data["commit_times"])
            if total == 0:
                continue

            signals = {}

            # Signal 1: Cadence sparsity — unique active days / span days.
            dates = sorted(data["commit_dates"])
            if len(dates) >= 2:
                span_days = (dates[-1] - dates[0]).days or 1
            else:
                span_days = 1
            unique_days = len(set(dates))
            activity_ratio = unique_days / span_days if span_days > 0 else 1.0
            signals["sparsity_score"] = max(0, min(25, round((1 - activity_ratio) * 30)))

            # Signal 2: Trivial-change ratio (commits with very few lines changed).
            trivial_count = sum(
                1 for a, d in zip(data["lines_added"], data["lines_deleted"])
                if (a + d) <= TRIVIAL_COMMIT_LINE_THRESHOLD
            )
            trivial_ratio = trivial_count / total
            signals["trivial_commit_ratio"] = round(trivial_ratio, 3)
            signals["trivial_score"] = round(trivial_ratio * 20, 1)

            # Signal 3: Long-gap ratio — proportion of inter-commit gaps over 72h.
            sorted_times = sorted(data["commit_times"])
            gap_hours = []
            large_gap_count = 0
            for i in range(1, len(sorted_times)):
                gap = (sorted_times[i] - sorted_times[i - 1]).total_seconds() / 3600
                gap_hours.append(gap)
                if gap > LARGE_GAP_HOURS:
                    large_gap_count += 1
            avg_gap = sum(gap_hours) / len(gap_hours) if gap_hours else 0
            large_gap_ratio = large_gap_count / len(gap_hours) if gap_hours else 0
            signals["large_gap_ratio"] = round(large_gap_ratio, 3)
            signals["disappearance_score"] = round(large_gap_ratio * 20, 1)

            # Signal 4: Average lines per active day (volume proxy only;
            # NOT a productivity score — small refactors and reviews don't show up here).
            total_lines = sum(data["lines_added"]) + sum(data["lines_deleted"])
            lines_per_day = total_lines / unique_days if unique_days > 0 else 0
            if lines_per_day < 20:
                signals["low_output_score"] = 15
            elif lines_per_day < 50:
                signals["low_output_score"] = 8
            elif lines_per_day < 100:
                signals["low_output_score"] = 3
            else:
                signals["low_output_score"] = 0

            # Signal 5: Non-code-only commit ratio (config / docs only commits).
            non_code_commits = 0
            for paths_list in data["file_paths"]:
                if paths_list and all(self._is_non_code(p) for p in paths_list):
                    non_code_commits += 1
            non_code_ratio = non_code_commits / total
            signals["non_code_ratio"] = round(non_code_ratio, 3)
            signals["non_code_score"] = round(non_code_ratio * 10, 1)

            # Signal 6: Weekday-skew — descriptive only (e.g., commits clustered late in the week).
            dow_counts = Counter(data["weekdays"])
            friday_count = dow_counts.get(4, 0)
            monday_count = dow_counts.get(0, 0)
            weekday_total = sum(1 for d in data["weekdays"] if d < 5) or 1
            friday_ratio = friday_count / weekday_total
            monday_ratio = monday_count / weekday_total
            late_week_skew = max(0, friday_ratio - monday_ratio)
            signals["late_week_skew_score"] = round(late_week_skew * 10, 1)

            # Signal 7: Add/delete imbalance — descriptive only (often appears for
            # initial commits, vendored code, generated files, etc.).
            total_added = sum(data["lines_added"])
            total_deleted = sum(data["lines_deleted"])
            if total_deleted > 0:
                add_delete_ratio = total_added / total_deleted
            else:
                add_delete_ratio = total_added if total_added > 0 else 1
            high_add_signal = 1 if add_delete_ratio > HIGH_ADD_DELETE_RATIO else 0
            signals["add_delete_imbalance_score"] = high_add_signal * 5

            # Composite engagement signal score (0-100). Descriptive, not evaluative.
            engagement_signal_score = min(100, round(
                signals["sparsity_score"]
                + signals["trivial_score"]
                + signals["disappearance_score"]
                + signals["low_output_score"]
                + signals["non_code_score"]
                + signals["late_week_skew_score"]
                + signals["add_delete_imbalance_score"]
            ))

            level, level_cn, level_description = self._level_for(engagement_signal_score)

            result[author] = {
                # New, neutral field names
                "engagement_signal_score": engagement_signal_score,
                "cadence_label": level,
                "cadence_label_cn": level_cn,
                "cadence_description": level_description,

                # Legacy field names retained for backward compatibility
                # (consumers should treat them as descriptive cadence stats only).
                "slacking_index": engagement_signal_score,
                "slacking_level": level,
                "slacking_level_cn": level_cn,

                # Always-attached interpretive guard so downstream renderers
                # cannot accidentally drop the disclaimer.
                "interpretation_notice": (
                    "Descriptive Git-cadence statistic only. Does NOT measure "
                    "productivity, engagement, or work quality. Must not be used "
                    "for performance evaluation, ranking, or HR decisions."
                ),

                "total_commits": total,
                "active_span_days": span_days,
                "unique_active_days": unique_days,
                "activity_ratio": round(activity_ratio, 3),
                "trivial_commit_ratio": signals["trivial_commit_ratio"],
                "large_gap_ratio": signals["large_gap_ratio"],
                "avg_gap_hours": round(avg_gap, 1),
                "lines_per_active_day": round(lines_per_day, 1),
                "non_code_commit_ratio": signals["non_code_ratio"],
                "friday_ratio": round(friday_ratio, 3),
                "monday_ratio": round(monday_ratio, 3),
                "signal_breakdown": {
                    "sparsity": signals["sparsity_score"],
                    "trivial_commits": signals["trivial_score"],
                    "long_gaps": signals["disappearance_score"],
                    "low_volume": signals["low_output_score"],
                    "non_code_only": signals["non_code_score"],
                    "late_week_skew": signals["late_week_skew_score"],
                    "add_delete_imbalance": signals["add_delete_imbalance_score"],
                },
            }

        return result

    @classmethod
    def _level_for(cls, score: int):
        """Return (en_label, cn_label, description) for an engagement signal score."""
        for ceiling, en, cn, desc in cls.LEVEL_DESCRIPTIONS:
            if score <= ceiling:
                return en, cn, desc
        en, cn, desc = cls.LEVEL_DESCRIPTIONS[-1][1:]
        return en, cn, desc

    @staticmethod
    def _is_non_code(filepath: str) -> bool:
        """Check if a file is a non-code file (config, docs, etc.)."""
        path_lower = filepath.lower()
        non_code_exts = [
            ".md", ".rst", ".txt", ".adoc", ".yml", ".yaml", ".json",
            ".toml", ".ini", ".cfg", ".env", ".lock", ".gitignore",
            ".editorconfig", ".prettierrc",
        ]
        non_code_names = [
            "readme", "changelog", "license", "contributing",
            "dockerfile", "makefile", ".github/",
        ]
        return (
            any(path_lower.endswith(ext) for ext in non_code_exts)
            or any(name in path_lower for name in non_code_names)
        )
