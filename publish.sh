#!/usr/bin/env bash
# Publish this skill to ClawHub.
#
# Slug:    wscats/code-analysis-skills
# Version: v1.0.7
#
# Usage:
#   ./publish.sh                # publish using defaults below
#   VERSION=v1.0.8 ./publish.sh # override version
#
# Prerequisites:
#   - `clawhub` CLI installed and logged in (`clawhub login`).
#   - Run from the repository root (the directory containing skill.yaml).

set -euo pipefail

# ─── Config (override via environment variables if needed) ──────────────────
# NOTE: clawhub slugs must be a single segment (lowercase letters, digits, and
# single hyphens only). The owner handle (e.g. `wscats/`) is taken from your
# logged-in account, not the slug.
SLUG="${SLUG:-code-analysis-skills}"
OWNER="${OWNER:-wscats}"
VERSION="${VERSION:-v1.0.9}"
NAME="${NAME:-Code Analysis Skills}"
TAGS="${TAGS:-latest,git,code-analysis,reflection}"
CHANGELOG="${CHANGELOG:-Doc/code alignment + dead-code purge: removed -a/--author from all docs (CLI never had it after v1.0.7); documented --multi-author-team-retro and --consented-author in every README/SKILL table; updated project tree to point at cadence_signal_analyzer.py and narrator/reflection_narrator.py; deleted unused *_score intermediates (sparsity_score / trivial_score / non_code_score / late_week_skew_score / add_delete_imbalance_score / disappearance_score / low_output_score) from cadence analyzer; removed legacy 'formerly DeveloperEvaluator' callout from narrator header.}"

# ─── Resolve script directory (the skill folder) ────────────────────────────
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_PATH="${SKILL_PATH:-${SCRIPT_DIR}}"

# ─── Sanity checks ──────────────────────────────────────────────────────────
if ! command -v clawhub >/dev/null 2>&1; then
  echo "❌ 'clawhub' CLI not found in PATH. Install it first:" >&2
  echo "   npm install -g @clawhub/cli   (or follow the official docs)" >&2
  exit 1
fi

if [[ ! -f "${SKILL_PATH}/skill.yaml" ]]; then
  echo "❌ skill.yaml not found at: ${SKILL_PATH}" >&2
  echo "   Run this script from the repository root, or set SKILL_PATH=..." >&2
  exit 1
fi

# ─── Show plan and confirm session ──────────────────────────────────────────
echo "──────────────────────────────────────────────────────────────"
echo " ClawHub publish"
echo "──────────────────────────────────────────────────────────────"
echo "  Owner     : ${OWNER}"
echo "  Slug      : ${SLUG}"
echo "  Version   : ${VERSION}"
echo "  Name      : ${NAME}"
echo "  Tags      : ${TAGS}"
echo "  Path      : ${SKILL_PATH}"
echo "  Changelog : ${CHANGELOG}"
echo "──────────────────────────────────────────────────────────────"

# Verify the user is logged in (non-fatal: clawhub publish will also check).
if ! clawhub whoami >/dev/null 2>&1; then
  echo "⚠️  You don't appear to be logged in. Running 'clawhub login' first..."
  clawhub login
fi

# ─── Publish ────────────────────────────────────────────────────────────────
clawhub publish "${SKILL_PATH}" \
  --slug "${SLUG}" \
  --name "${NAME}" \
  --version "${VERSION}" \
  --tags "${TAGS}" \
  --changelog "${CHANGELOG}"

echo "✅ Published ${SLUG}@${VERSION}"
echo "   View: https://clawhub.ai/${OWNER}/${SLUG}"
