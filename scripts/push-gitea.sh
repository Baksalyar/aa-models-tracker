#!/usr/bin/env bash
# Push private files (AGENTS.md, todo.md, data/) to Gitea only.
# Usage: ./scripts/push-gitea.sh
set -e

git add -f AGENTS.md todo.md data/models.json data/feed.xml
git commit --amend --no-edit
git push origin main --force
git rm --cached AGENTS.md todo.md data/models.json data/feed.xml 2>/dev/null
