"""
Developer Reflection Report Generator (formerly DeveloperEvaluator).

⚠️  IMPORTANT — INTENDED USE & LIMITATIONS

This module produces *self-reflection* feedback for an individual developer
based purely on their Git history. The output:

  - Is a NARROW, BIASED proxy. Git history misses code review, design,
    mentoring, on-call, ops, security work, pair programming, refactor
    planning, and many other forms of contribution.
  - MUST NOT be used to evaluate, rank, discipline, promote, demote, fire,
    or compensate any employee or contributor.
  - MUST NOT be used to compare individual developers against each other for
    workplace decisions.
  - MUST be used only with informed consent of the analyzed developer, and
    in a non-punitive context (e.g., a developer running it on their own
    repository, or an opt-in team retrospective).

The composite "score" / "grade" / "verdict" labels are kept for backward
compatibility with the report templates, but they are reframed throughout as
DESCRIPTIVE INDICATORS, not authoritative judgements.

Tone: neutral, supportive, evidence-based. No stigmatizing language, no
pseudoscientific claims, no "wake-up call" framing.
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


# Scoring weights for each dimension (total = 100). These are descriptive
# weights for the composite indicator — NOT a measure of human worth.
DIMENSION_WEIGHTS = {
    "commit_discipline": 15,    # Commit habits, message quality, conventions
    "work_consistency": 15,     # Cadence regularity (Git timestamps only)
    "efficiency": 20,           # Churn, rework, change volume
    "code_quality": 25,         # Bug-fix ratio, revert, complexity, tests
    "code_style": 10,           # Conventional commits, issue refs
    "engagement": 15,           # Inverse of cadence-sparsity signals
}


# Always-attached interpretive guard. Every per-developer result carries this
# field so downstream renderers cannot accidentally drop the disclaimer.
_INTERPRETATION_NOTICE = (
    "This report is a DESCRIPTIVE summary of Git-history signals only. It is "
    "not a performance review, not a measure of an individual's value, and not "
    "a basis for HR, compensation, ranking, or disciplinary decisions. Many "
    "important contributions (design, code review, mentoring, on-call, "
    "operations, pair programming) are invisible to Git history. Read the "
    "findings as discussion prompts, not verdicts."
)


class DeveloperEvaluator:
    """
    Generates a *self-reflection* report for each developer from analyzer
    metrics. Output is intentionally framed as observations + suggestions,
    not verdicts.

    Each developer report contains:
      - A composite descriptive indicator (0-100) and an indicator band
      - Lists of supportive observations and points to consider, each
        backed by concrete data
      - Suggestions phrased as discussion prompts, not directives
      - A neutral one-line summary
      - An always-attached ``interpretation_notice`` disclaimer
    """

    def evaluate(self, repo_metrics: Dict) -> Dict:
        """
        Build the per-developer reflection report.

        Args:
            repo_metrics: Dict with keys like 'commit_patterns', 'work_habits',
                          'efficiency', 'code_style', 'code_quality', 'slacking'.

        Returns:
            Dict keyed by author with reflection-report results.
        """
        # Collect all authors
        all_authors = set()
        for analyzer_data in repo_metrics.values():
            if isinstance(analyzer_data, dict):
                all_authors.update(analyzer_data.keys())

        results = {}
        for author in sorted(all_authors):
            commit = repo_metrics.get("commit_patterns", {}).get(author, {})
            habit = repo_metrics.get("work_habits", {}).get(author, {})
            eff = repo_metrics.get("efficiency", {}).get(author, {})
            style = repo_metrics.get("code_style", {}).get(author, {})
            quality = repo_metrics.get("code_quality", {}).get(author, {})
            slacking = repo_metrics.get("slacking", {}).get(author, {})

            if not commit:
                continue

            # Calculate dimension scores (each 0-100, then weighted)
            dim_scores = {}
            dim_scores["commit_discipline"] = self._score_commit_discipline(commit, style)
            dim_scores["work_consistency"] = self._score_work_consistency(habit)
            dim_scores["efficiency"] = self._score_efficiency(eff)
            dim_scores["code_quality"] = self._score_code_quality(quality)
            dim_scores["code_style"] = self._score_code_style(style)
            dim_scores["engagement"] = self._score_engagement(slacking)

            # Weighted composite descriptive indicator
            total_score = 0
            for dim, score in dim_scores.items():
                weight = DIMENSION_WEIGHTS.get(dim, 0)
                total_score += score * (weight / 100.0)
            total_score = round(total_score, 1)

            grade = self._letter_grade(total_score)

            observations = self._identify_strengths(
                commit, habit, eff, style, quality, slacking, dim_scores
            )
            considerations = self._identify_weaknesses(
                commit, habit, eff, style, quality, slacking, dim_scores
            )
            suggestions = self._generate_suggestions(
                commit, habit, eff, style, quality, slacking, dim_scores
            )
            verdict = self._generate_verdict(total_score, dim_scores, slacking)

            results[author] = {
                "overall_score": total_score,
                "grade": grade,
                "dimension_scores": dim_scores,
                # Backward-compatible field names; templates render these.
                "strengths": observations,
                "weaknesses": considerations,
                "suggestions": suggestions,
                "verdict": verdict,
                "interpretation_notice": _INTERPRETATION_NOTICE,
            }

        return results

    # ─── Dimension Scorers ────────────────────────────────────────────────

    def _score_commit_discipline(self, commit: Dict, style: Dict) -> float:
        """Score commit discipline (0-100)."""
        score = 50.0  # baseline

        # Commit frequency
        avg_per_day = commit.get("avg_commits_per_active_day", 0)
        if 2 <= avg_per_day <= 8:
            score += 15
        elif avg_per_day > 8:
            score += 5  # very granular commits
        elif avg_per_day > 0:
            score += 8

        # Message quality
        avg_msg_len = commit.get("avg_message_length", 0)
        if 30 <= avg_msg_len <= 100:
            score += 15
        elif avg_msg_len > 100:
            score += 10
        elif avg_msg_len > 15:
            score += 5

        # Merge ratio (high values may reflect a merge-only role rather than
        # a quality issue — kept as a soft signal only).
        merge_ratio = commit.get("merge_ratio", 0)
        if merge_ratio < 0.3:
            score += 10
        elif merge_ratio < 0.5:
            score += 5

        # Conventional commits
        conv_ratio = style.get("conventional_commit_ratio", 0)
        if conv_ratio > 0.8:
            score += 10
        elif conv_ratio > 0.5:
            score += 5

        return min(100, max(0, score))

    def _score_work_consistency(self, habit: Dict) -> float:
        """Score cadence consistency (0-100). Descriptive only."""
        score = 50.0

        weekend_ratio = habit.get("weekend_ratio", 0)
        if weekend_ratio < 0.1:
            score += 15
        elif weekend_ratio < 0.2:
            score += 10
        else:
            score -= 5

        late_night = habit.get("late_night_ratio", 0)
        if late_night < 0.1:
            score += 15
        elif late_night < 0.2:
            score += 5
        else:
            score -= 10

        streak = habit.get("longest_streak_days", 0)
        if streak >= 10:
            score += 15
        elif streak >= 5:
            score += 10
        elif streak >= 3:
            score += 5

        gap = habit.get("avg_gap_between_commits_hours", 999)
        if gap < 24:
            score += 5
        elif gap < 48:
            score += 2

        return min(100, max(0, score))

    def _score_efficiency(self, eff: Dict) -> float:
        """Score change-pattern indicator (0-100). Descriptive only."""
        score = 50.0

        churn = eff.get("churn_rate", 0)
        if churn < 0.3:
            score += 20
        elif churn < 0.5:
            score += 10
        elif churn < 0.8:
            score += 0
        else:
            score -= 10

        rework = eff.get("rework_ratio", 0)
        if rework < 0.15:
            score += 15
        elif rework < 0.3:
            score += 5
        else:
            score -= 10

        lpc = eff.get("lines_per_commit", 0)
        if 20 <= lpc <= 300:
            score += 15
        elif lpc > 300:
            score += 5
        elif lpc > 0:
            score += 3

        return min(100, max(0, score))

    def _score_code_quality(self, quality: Dict) -> float:
        """Score code-quality indicator (0-100). Based on Git artefacts only."""
        score = 50.0

        bug_fix = quality.get("bug_fix_ratio", 0)
        if bug_fix < 0.15:
            score += 15
        elif bug_fix < 0.3:
            score += 5
        elif bug_fix > 0.5:
            score -= 10

        revert = quality.get("revert_ratio", 0)
        if revert < 0.02:
            score += 10
        elif revert < 0.05:
            score += 5
        else:
            score -= 10

        large = quality.get("large_commit_ratio", 0)
        if large < 0.1:
            score += 10
        elif large < 0.2:
            score += 5
        else:
            score -= 5

        test_ratio = quality.get("test_modification_ratio", 0)
        if test_ratio > 0.2:
            score += 15
        elif test_ratio > 0.1:
            score += 10
        elif test_ratio > 0.05:
            score += 5

        complexity = quality.get("avg_python_complexity", 0)
        if 0 < complexity <= 5:
            score += 10
        elif complexity <= 10:
            score += 5
        elif complexity > 15:
            score -= 10

        return min(100, max(0, score))

    def _score_code_style(self, style: Dict) -> float:
        """Score code style adherence (0-100)."""
        score = 50.0

        conv = style.get("conventional_commit_ratio", 0)
        if conv > 0.8:
            score += 25
        elif conv > 0.5:
            score += 15
        elif conv > 0.2:
            score += 5

        issue_ref = style.get("issue_reference_ratio", 0)
        if issue_ref > 0.5:
            score += 20
        elif issue_ref > 0.3:
            score += 10
        elif issue_ref > 0.1:
            score += 5

        return min(100, max(0, score))

    def _score_engagement(self, slacking: Dict) -> float:
        """Score cadence-density indicator (inverse of sparsity signal)."""
        idx = slacking.get("slacking_index", 50)
        return max(0, min(100, 100 - idx))

    # ─── Observation / Consideration / Suggestion Generators ─────────────

    def _identify_strengths(
        self, commit, habit, eff, style, quality, slacking, dim_scores
    ) -> List[str]:
        """Identify supportive, evidence-based observations."""
        observations = []

        if commit.get("avg_commits_per_active_day", 0) >= 3:
            observations.append("Steady commit cadence on the days they are active.")

        if commit.get("avg_message_length", 0) >= 40:
            observations.append("Commit messages tend to be descriptive — helpful for traceability.")

        if habit.get("weekend_ratio", 1) < 0.05:
            observations.append("Most commits land on weekdays, suggesting commits stay inside regular hours.")

        if habit.get("longest_streak_days", 0) >= 7:
            observations.append(
                f"At one point sustained a {habit['longest_streak_days']}-day commit streak."
            )

        if eff.get("churn_rate", 1) < 0.3:
            observations.append("Low code churn — added lines tend to stay in the codebase.")

        if eff.get("rework_ratio", 1) < 0.15:
            observations.append("Low rework ratio — files tend not to be re-edited within a week.")

        if quality.get("test_modification_ratio", 0) > 0.2:
            observations.append("Test files are touched alongside code changes regularly.")

        if quality.get("bug_fix_ratio", 1) < 0.15:
            observations.append("Few commits are tagged as bug-fixes (in this Git history sample).")

        if quality.get("revert_ratio", 1) < 0.02:
            observations.append("Reverts are rare in this history.")

        if style.get("conventional_commit_ratio", 0) > 0.7:
            observations.append("Conventional Commits format is followed consistently.")

        if style.get("issue_reference_ratio", 0) > 0.5:
            observations.append("Commits frequently reference issue / ticket numbers.")

        if slacking.get("slacking_index", 100) <= 20:
            observations.append("Cadence appears dense across the active span.")

        if eff.get("ownership_ratio", 0) > 0.5:
            observations.append("Holds majority authorship on a notable share of touched files.")

        return observations[:8]

    def _identify_weaknesses(
        self, commit, habit, eff, style, quality, slacking, dim_scores
    ) -> List[str]:
        """Surface points worth a conversation — neutral, specific, non-stigmatizing."""
        considerations = []

        if commit.get("avg_message_length", 999) < 20:
            considerations.append(
                "Commit messages average under 20 chars — longer messages would help "
                "future readers (and the author) understand the *why* behind a change."
            )

        if commit.get("merge_ratio", 0) > 0.5:
            considerations.append(
                f"Merge commits make up {commit['merge_ratio']:.0%} of activity. "
                "This may simply reflect a merge-only role; worth confirming with the author."
            )

        if habit.get("late_night_ratio", 0) > 0.2:
            considerations.append(
                f"{habit['late_night_ratio']:.0%} of commits land in late-night hours. "
                "This may reflect time-zone settings, batched pushes, on-call work, or a "
                "preferred schedule — context from the author is needed before drawing conclusions."
            )

        if habit.get("weekend_ratio", 0) > 0.25:
            considerations.append(
                f"Weekend commits are {habit['weekend_ratio']:.0%} of the total. "
                "Consider whether this matches the author's intended work pattern, or "
                "whether workload / time-zone settings are the cause."
            )

        if eff.get("churn_rate", 0) > 0.6:
            considerations.append(
                f"Churn rate is {eff['churn_rate']:.0%} — a large share of added lines "
                "are later removed. Common causes include exploratory prototyping, "
                "scope changes, or refactoring sweeps; not necessarily a problem."
            )

        if eff.get("rework_ratio", 0) > 0.3:
            considerations.append(
                f"Rework ratio is {eff['rework_ratio']:.0%} — files are revisited "
                "within a week. May reflect iterative review feedback, evolving "
                "requirements, or shared-ownership work."
            )

        if quality.get("bug_fix_ratio", 0) > 0.4:
            considerations.append(
                f"{quality['bug_fix_ratio']:.0%} of commits are tagged as fixes. "
                "Could indicate fix-heavy work assignment, or an opportunity for more "
                "tests / earlier review."
            )

        if quality.get("revert_ratio", 0) > 0.05:
            considerations.append(
                f"Reverts are {quality['revert_ratio']:.0%} of commits — slightly elevated. "
                "Worth checking whether CI / pre-merge checks could catch issues earlier."
            )

        if quality.get("large_commit_ratio", 0) > 0.2:
            considerations.append(
                f"{quality['large_commit_ratio']:.0%} of commits are large (>500 lines). "
                "Smaller commits are usually easier to review."
            )

        if quality.get("test_modification_ratio", 0) < 0.05:
            considerations.append(
                "Test files are rarely touched alongside code changes. This might be fine "
                "(e.g., docs / infra work), or may suggest a gap in test coverage."
            )

        if style.get("conventional_commit_ratio", 0) < 0.2:
            considerations.append(
                "Conventional Commits format is rarely used. Adopting it makes "
                "automated changelogs and release tooling easier."
            )

        if slacking.get("slacking_index", 0) > 60:
            considerations.append(
                f"Cadence-sparsity indicator is {slacking['slacking_index']}/100. "
                "This is a *descriptive* signal — many legitimate situations produce sparse "
                "Git activity (architecture work, code review, on-call, paternity / sick "
                "leave, time-off). The right next step is a supportive conversation, never "
                "a punitive one."
            )

        if eff.get("lines_per_commit", 0) < 10 and commit.get("total_commits", 0) > 20:
            considerations.append(
                "Commits average under 10 lines each. Very granular commits can be useful, "
                "but consider whether some of them could be squashed for clearer history."
            )

        return considerations[:8]

    def _generate_suggestions(
        self, commit, habit, eff, style, quality, slacking, dim_scores
    ) -> List[str]:
        """Generate neutral, practical suggestions phrased as discussion prompts."""
        suggestions = []

        if dim_scores.get("commit_discipline", 0) < 60:
            suggestions.append(
                "📝 Consider adopting Conventional Commits (feat/fix/docs…) and writing "
                "messages that explain the *why* of a change."
            )

        if dim_scores.get("work_consistency", 0) < 60:
            suggestions.append(
                "⏰ A more even commit cadence (smaller batches more often) tends to "
                "make review and rollback easier."
            )

        if dim_scores.get("efficiency", 0) < 60:
            suggestions.append(
                "🚀 If churn or rework feels high, a brief design sketch or a quick "
                "review-before-implementation pass can sometimes reduce iteration cost."
            )

        if dim_scores.get("code_quality", 0) < 60:
            suggestions.append(
                "🔍 Pairing each behavioural change with a test (where it fits the "
                "codebase culture) tends to reduce the bug-fix follow-up rate."
            )

        if quality.get("large_commit_ratio", 0) > 0.15:
            suggestions.append(
                "✂️ Where it doesn't break the change's logical unit, smaller commits "
                "(roughly under ~200 lines) are easier to review."
            )

        if habit.get("late_night_ratio", 0) > 0.15:
            suggestions.append(
                "🌙 If late-night commits don't match the author's preferred schedule, "
                "it may be worth a check-in about workload — but Git timestamps alone "
                "are not enough to draw conclusions."
            )

        if slacking.get("slacking_index", 0) > 50:
            suggestions.append(
                "💬 The cadence-sparsity indicator is elevated. Treat this as a prompt "
                "for a supportive 1:1 (workload, blockers, time-off, role mix) — never as "
                "evidence of low effort."
            )

        if style.get("issue_reference_ratio", 0) < 0.3:
            suggestions.append(
                "🔗 Linking commits to issue / ticket numbers improves traceability and "
                "audit trails for the whole team."
            )

        if eff.get("ownership_ratio", 0) > 0.8:
            suggestions.append(
                "🤝 Authorship is highly concentrated in this developer. Pair-programming "
                "or rotating ownership reduces bus-factor risk for the team."
            )

        return suggestions[:6]

    def _generate_verdict(self, score, dim_scores, slacking) -> str:
        """Generate a one-line, neutral summary."""
        idx = slacking.get("slacking_index", 50)

        if score >= 85:
            return "📈 Strong descriptive indicators across most Git-history dimensions."
        elif score >= 75:
            return "📊 Solid descriptive indicators, with a few areas worth a follow-up chat."
        elif score >= 65:
            return "🔎 Mixed picture — several dimensions look healthy, others may be worth discussing."
        elif score >= 50:
            if idx > 60:
                return (
                    "🗒️ Mid-range indicators with sparse cadence. Read with full context "
                    "(role mix, time-off, on-call, design work) before drawing conclusions."
                )
            return "🗒️ Mid-range indicators. Specific dimensions may benefit from a 1:1 conversation."
        elif score >= 35:
            return (
                "🧭 Several Git-history indicators are below typical ranges. Treat as a "
                "prompt for a supportive conversation, not a verdict."
            )
        else:
            return (
                "🧭 Indicators are markedly low across many dimensions. This often points "
                "to factors invisible to Git history (role focus, time-off, blockers, "
                "tooling). A supportive 1:1 is the right next step."
            )

    @staticmethod
    def _letter_grade(score: float) -> str:
        """Convert numeric score to a descriptive band label."""
        if score >= 90:
            return "S"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        elif score >= 35:
            return "E"
        else:
            return "F"
