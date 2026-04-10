#!/usr/bin/env bash
# Deploy the dashboard to yulinl2.github.io (GitHub Pages).
#
# Prerequisites:
#   - git configured with push access to yulinl2/yulinl2.github.io
#   - dashboard/index.html built (run: python dashboard/build_dashboard.py)
#
# Usage:
#   bash dashboard/deploy.sh
#
# This copies dashboard/index.html to the pages repo under
# open-idea-sourcing/index.html, commits, and pushes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DASHBOARD_HTML="$SCRIPT_DIR/index.html"
PAGES_REPO_DIR="${PAGES_REPO_DIR:-$HOME/yulinl2.github.io}"
DEPLOY_PATH="open-idea-sourcing"

if [ ! -f "$DASHBOARD_HTML" ]; then
  echo "ERROR: Dashboard not built. Run: python dashboard/build_dashboard.py"
  exit 1
fi

echo "Deploying dashboard to $PAGES_REPO_DIR/$DEPLOY_PATH/"

# Clone if not present
if [ ! -d "$PAGES_REPO_DIR/.git" ]; then
  echo "Cloning yulinl2.github.io..."
  git clone "https://github.com/yulinl2/yulinl2.github.io.git" "$PAGES_REPO_DIR"
fi

# Copy dashboard
mkdir -p "$PAGES_REPO_DIR/$DEPLOY_PATH"
cp "$DASHBOARD_HTML" "$PAGES_REPO_DIR/$DEPLOY_PATH/index.html"

# Commit and push
cd "$PAGES_REPO_DIR"
git add "$DEPLOY_PATH/index.html"
if git diff --cached --quiet; then
  echo "No changes to deploy."
else
  git commit -m "Update Open Idea Sourcing dashboard

Auto-deployed from Open-Idea-Sourcing pipeline."
  git push
  echo "Deployed! Visit: https://yulinl2.github.io/$DEPLOY_PATH/"
fi
