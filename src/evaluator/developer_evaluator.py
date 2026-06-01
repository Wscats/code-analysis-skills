"""
Per-Developer Reflection Narrative Generator (formerly DeveloperEvaluator).

⚠️  IMPORTANT — INTENDED USE & STRUCTURAL SAFEGUARDS

This module produces *self-reflection narrative text* for an individual
developer based purely on their Git history. The output:

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

Structural safeguards in this rewrite:
  * No composite 0-100 score is produced. Per-dimension component values
    survive (so the developer can self-introspect each axis), but they are
    deliberately never combined into a single number.
  * No S/A/B/C/D/E/F letter band is produced. Letter grades framed Git
    statistics as a personal report card, which they are not.
  * No "verdict" sentence. The output is supportive observations + points to
    consider with context + discussion prompts. Nothing more.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


# Per-dimension component weights — kept only so each dimension's narrative
# can mention which axes a developer might want to reflect on first. They are
# deliberately NOT combined into a single composite score.
DIMENSION_LABELS = {
    "commit_discipline": "Commit discipline (frequency, message length, conventions)",
    "work_consistency":  "Cadence consistency (timestamp distribution)",
    "efficiency":        "Change patterns (churn, rework, change volume)",
    "code_quality":      "Code-quality artefacts (bug-fix ratio, reverts, tests, complexity)",
    "code_style":        "Style markers (Conventional Commits, issue references)",
    "engagement":        "Cadence density (inverse of long-gap signals)",
}


# Always-attached interpretive guard. Every per-developer result carries this
# field so downstream renderers cannot accidentally drop the disclaimer.
_INTERPRETATION_NOTICE = (
    "This narrative is a DESCRIPTIVE summary of Git-history signals only. It "
    "is not a performance review, not a measure of an individual's value, and "
    "not a basis for HR, compensation, ranking, or disciplinary decisions. "
    "Many important contributions (design, code review, mentoring, on-call, "
    "operations, pair programming) are invisible to Git history. Read the "
    "findings as personal reflection prompts, not verdicts."
)


class DeveloperEvaluator:
    """
    Generates a *self-reflection* narrative for each developer from analyzer
    metrics. Output is intentionally framed as observations + suggestions,
    never as a score, grade, or verdict.

    Each developer narrative contains:
      - Supportive observations, each backed by concrete component values
      - Points to consider with context (no judgement language)
      - Suggestions phrased as personal reflection prompts
      - An always-attached ``interpretation_notice`` disclaimer

    The legacy field names ``overall_score``, ``grade``, ``dimension_scores``
    and ``verdict`` are intentionally NOT emitted by this class anymore.
    Downstream consumers that relied on them must migrate to the narrative
    fields above.
    """

    def evaluate(self, repo_metrics: Dict) -> Dict:
        """
        Build the per-developer reflection narrative.

        Args:
            repo_metrics: Dict with keys like 'commit_patterns', 'work_habits',
                          'efficiency', 'code_style', 'code_quality', 'slacking'.

        Returns:
            Dict keyed by author with reflection-narrative results.
        """
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

            observations = self._identify_strengths(
                commit, habit, eff, style, quality, slacking
            )
            considerations = self._identify_weaknesses(
                commit, habit, eff, style, quality, slacking
            )
            suggestions = self._generate_suggestions(
                commit, habit, eff, style, quality, slacking
            )

            results[author] = {
                # Narrative-only outputs. NO composite score, NO grade band,
                # NO verdict. Field names that templates already render are
                # preserved (strengths / weaknesses / suggestions); no others.
                "strengths": observations,
                "weaknesses": considerations,
                "suggestions": suggestions,
                "interpretation_notice": _INTERPRETATION_NOTICE,
            }

        return results

    # ─── Observation / Consideration / Suggestion Generators ─────────────

    def _identify_strengths(
        self, commit, habit, eff, style, quality, slacking
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

        if eff.get("ownership_ratio", 0) > 0.5:
            observations.append("Holds majority authorship on a notable share of touched files.")

        return observations[:8]

    def _identify_weaknesses(
        self, commit, habit, eff, style, quality, slacking
    ) -> List[str]:
        """Surface points worth a personal reflection — neutral, specific."""
        considerations = []

        if commit.get("avg_message_length", 999) < 20:
            considerations.append(
                "Commit messages average under 20 chars — longer messages would "
                "help future readers (and the author) understand the *why* "
                "behind a change."
            )

        if commit.get("merge_ratio", 0) > 0.5:
            considerations.append(
                f"Merge commits make up {commit['merge_ratio']:.0%} of activity. "
                "This may simply reflect a merge-only role; worth confirming "
                "with the author."
            )

        if habit.get("late_night_ratio", 0) > 0.2:
            considerations.append(
                f"{habit['late_night_ratio']:.0%} of commits land in late-night "
                "hours. This may reflect time-zone settings, batched pushes, "
                "on-call work, or a preferred schedule — context from the "
                "author is needed before drawing conclusions."
            )

        if habit.get("weekend_ratio", 0) > 0.25:
            considerations.append(
                f"Weekend commits are {habit['weekend_ratio']:.0%} of the total. "
                "Consider whether this matches the author's intended work "
                "pattern, or whether workload / time-zone settings are the "
                "cause."
            )

        if eff.get("churn_rate", 0) > 0.6:
            considerations.append(
                f"Churn rate is {eff['churn_rate']:.0%} — a large share of "
                "added lines are later removed. Common causes include "
                "exploratory prototyping, scope changes, or refactoring "
                "sweeps; not necessarily a problem."
            )

        if eff.get("rework_ratio", 0) > 0.3:
            considerations.append(
                f"Rework ratio is {eff['rework_ratio']:.0%} — files are "
                "revisited within a week. May reflect iterative review "
                "feedback, evolving requirements, or shared-ownership work."
            )

        if quality.get("bug_fix_ratio", 0) > 0.4:
            considerations.append(
                f"{quality['bug_fix_ratio']:.0%} of commits are tagged as fixes. "
                "Could indicate fix-heavy work assignment, or an opportunity "
                "for more tests / earlier review."
            )

        if quality.get("revert_ratio", 0) > 0.05:
            considerations.append(
                f"Reverts are {quality['revert_ratio']:.0%} of commits — "
                "slightly elevated. Worth checking whether CI / pre-merge "
                "checks could catch issues earlier."
            )

        if quality.get("large_commit_ratio", 0) > 0.2:
            considerations.append(
                f"{quality['large_commit_ratio']:.0%} of commits are large "
                "(>500 lines). Smaller commits are usually easier to review."
            )

        if quality.get("test_modification_ratio", 0) < 0.05:
            considerations.append(
                "Test files are rarely touched alongside code changes. This "
                "might be fine (e.g., docs / infra work), or may suggest a "
                "gap in test coverage."
            )

        if style.get("conventional_commit_ratio", 0) < 0.2:
            considerations.append(
                "Conventional Commits format is rarely used. Adopting it "
                "makes automated changelogs and release tooling easier."
            )

        if eff.get("lines_per_commit", 0) < 10 and commit.get("total_commits", 0) > 20:
            considerations.append(
                "Commits average under 10 lines each. Very granular commits "
                "can be useful, but consider whether some of them could be "
                "squashed for clearer history."
            )

        return considerations[:8]

    def _generate_suggestions(
        self, commit, habit, eff, style, quality, slacking
    ) -> List[str]:
        """Generate neutral, practical reflection prompts."""
        suggestions = []

        if style.get("conventional_commit_ratio", 0) < 0.5:
            suggestions.append(
                "📝 Consider adopting Conventional Commits (feat/fix/docs…) "
                "and writing messages that explain the *why* of a change."
            )

        if habit.get("avg_gap_between_commits_hours", 0) > 72:
            suggestions.append(
                "⏰ Smaller, more frequent commits tend to make review and "
                "rollback easier than infrequent large batches."
            )

        if eff.get("churn_rate", 0) > 0.5 or eff.get("rework_ratio", 0) > 0.3:
            suggestions.append(
                "🚀 If churn or rework feels high, a brief design sketch or "
                "a quick review-before-implementation pass can sometimes "
                "reduce iteration cost."
            )

        if quality.get("test_modification_ratio", 0) < 0.1:
            suggestions.append(
                "🔍 Pairing each behavioural change with a test (where it "
                "fits the codebase culture) tends to reduce the bug-fix "
                "follow-up rate."
            )

        if quality.get("large_commit_ratio", 0) > 0.15:
            suggestions.append(
                "✂️ Where it doesn't break the change's logical unit, smaller "
                "commits (roughly under ~200 lines) are easier to review."
            )

        if habit.get("late_night_ratio", 0) > 0.15:
            suggestions.append(
                "🌙 If late-night commits don't match your preferred schedule, "
                "this is a useful self-reflection prompt — but Git timestamps "
                "alone are not enough to draw firm conclusions."
            )

        if style.get("issue_reference_ratio", 0) < 0.3:
            suggestions.append(
                "🔗 Linking commits to issue / ticket numbers improves "
                "traceability and audit trails."
            )

        if eff.get("ownership_ratio", 0) > 0.8:
            suggestions.append(
                "🤝 Authorship is highly concentrated. Pair-programming or "
                "rotating ownership reduces bus-factor risk for the team."
            )

        return suggestions[:6]
