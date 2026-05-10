#!/usr/bin/env bash
set -euo pipefail

# Effectue un cycle complet git add + commit + push.
# Usage:
#   scripts/push_git.sh "Mon message de commit"
#   scripts/push_git.sh "Mon message" origin main
#
# Parametres:
#   1: message de commit (obligatoire)
#   2: remote git (optionnel, defaut: origin)
#   3: branche cible (optionnel, defaut: branche courante)

if ! command -v git >/dev/null 2>&1; then
  echo "git est introuvable sur cette machine." >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Ce dossier n'est pas un depot git." >&2
  exit 1
fi

COMMIT_MESSAGE="${1:-}"
REMOTE_NAME="${2:-origin}"
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
TARGET_BRANCH="${3:-$CURRENT_BRANCH}"

if [[ -z "$COMMIT_MESSAGE" ]]; then
  echo "Message de commit manquant." >&2
  echo "Usage: scripts/push_git.sh \"Mon message\" [remote] [branche]" >&2
  exit 1
fi

if [[ "$CURRENT_BRANCH" == "HEAD" ]] && [[ -z "${3:-}" ]]; then
  echo "HEAD detache: precise la branche cible en 3e argument." >&2
  echo "Exemple: scripts/push_git.sh \"Mon message\" origin main" >&2
  exit 1
fi

if ! git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  echo "Remote introuvable: $REMOTE_NAME" >&2
  exit 1
fi

# Ajoute toutes les modifications suivies et non suivies.
git add -A

# Evite un commit vide.
if git diff --cached --quiet; then
  echo "Aucune modification a commit." >&2
  exit 1
fi

git commit -m "$COMMIT_MESSAGE"

# Configure l'upstream automatiquement au premier push de la branche.
if git rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1; then
  git push "$REMOTE_NAME" "$TARGET_BRANCH"
else
  git push -u "$REMOTE_NAME" "$TARGET_BRANCH"
fi

echo "Push termine: $REMOTE_NAME/$TARGET_BRANCH"
