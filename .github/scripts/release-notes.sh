#!/usr/bin/env bash
# Prints Markdown release notes for the commits between two refs.
#
# Usage: release-notes.sh <previous tag or empty> <new tag> <target sha>
#
# One line per commit on the first-parent history, so it works for direct
# commits to main as well as merged PRs:
#   - direct and squash-merged commits use the commit subject
#   - merge commits use the PR title (first line of the merge commit body)
# Commits with "[skip changelog]" anywhere in the message are left out.
set -euo pipefail

last="$1"
tag="$2"
target="$3"
range="${last:+$last..}$target"

echo "## What's Changed"
echo

git log --first-parent --invert-grep --grep='\[skip changelog\]' --format=%H "$range" | while read -r sha; do
  short=$(git rev-parse --short "$sha")
  if git rev-parse -q --verify "$sha^2" >/dev/null; then
    title=$(git log -1 --format=%b "$sha" | sed -n '/[^[:space:]]/{p;q;}')
    pr=$(git log -1 --format=%s "$sha" | grep -o '#[0-9]\+' | head -n1 || true)
    echo "- ${title:-$(git log -1 --format=%s "$sha")} (${pr:-$short})"
  else
    subject=$(git log -1 --format=%s "$sha")
    # Squash merges already end with the PR number, e.g. "Add feature (#26)"
    if [[ "$subject" =~ \(#[0-9]+\)$ ]]; then
      echo "- $subject"
    else
      echo "- $subject ($short)"
    fi
  fi
done

if [ -n "$last" ]; then
  echo
  echo "**Full Changelog**: https://github.com/${GITHUB_REPOSITORY:-OwlCaribou/swurApp}/compare/$last...$tag"
fi
