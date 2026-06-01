#!/usr/bin/env bash
# Enable branch protection on main after secret-scan.yml has run at least once.
# Requires: gh auth login with repo admin access.
set -euo pipefail

repo="${1:-amber-siru-lin/ai-sql-poc}"
branch="${2:-main}"

echo "Setting branch protection on ${repo}@${branch}..."
echo "Requires status checks: gitleaks, block-sensitive-paths"
echo

gh api \
  --method PUT \
  "repos/${repo}/branches/${branch}/protection" \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      {"context": "gitleaks", "app_id": null},
      {"context": "block-sensitive-paths", "app_id": null}
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF

echo
echo "Done. Verify in GitHub: Settings → Branches → ${branch}"
