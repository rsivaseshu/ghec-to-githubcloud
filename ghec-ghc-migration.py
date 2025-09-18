"""
Interactive script to automate GitHub repo creation and setup for developers.
Prompts for repo name, team names, labels, Cloud Build integration, repo category, region, code owners, description, topics, and default branch.
Optionally creates a default cloudbuild.yaml, CODEOWNERS, LICENSE, and README.md in the new repo.
"""

from github import Github
import os
import tempfile

# --- USER INPUT ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or input("Enter your GitHub token: ")
ORG_NAME = input("Enter your GitHub organization name: ")
REPO_NAME = input("Enter the new repository name: ")
DESCRIPTION = input("Enter repository description: ")
TOPICS = input("Enter topics/tags (comma-separated): ").split(",")
DEFAULT_BRANCH = input("Enter default branch name (default: main): ") or "main"
TEAM_SLUGS = input("Enter team slugs (comma-separated): ").split(",")
LABELS = []
while True:
    label = input("Add a label (format: name:color, or leave blank to finish): ")
    if not label:
        break
    try:
        name, color = label.split(":")
        LABELS.append({"name": name.strip(), "color": color.strip()})
    except ValueError:
        print("Invalid format. Please use name:color (e.g., bug:d73a4a)")
add_cloudbuild = input("Add Google Cloud Build integration? (y/n): ").lower() == "y"
add_cloudbuild_yaml = input("Create default cloudbuild.yaml in the new repo? (y/n): ").lower() == "y"
category = input("Select repo category (sox/banking/normal): ").strip().lower()
region = input("Select region (china/north-america): ").strip().lower()
codeowners = input("Enter code owners (comma-separated GitHub usernames): ").split(",")
add_codeowners_file = input("Create CODEOWNERS file in the new repo? (y/n): ").lower() == "y"
add_license = input("Add LICENSE file? (y/n): ").lower() == "y"
add_readme = input("Add README.md file? (y/n): ").lower() == "y"
CLOUDBUILD_WEBHOOK_URL = "https://cloudbuild.googleapis.com/github/webhook"

# --- AUTHENTICATION ---
g = Github(GITHUB_TOKEN)
org = g.get_organization(ORG_NAME)

# --- CREATE REPOSITORY ---
repo = org.create_repo(
    REPO_NAME,
    private=True,
    auto_init=True,
    description=DESCRIPTION,
    default_branch=DEFAULT_BRANCH
)
print(f"Repository '{REPO_NAME}' created.")

# --- SET TOPICS ---
if TOPICS and any(t.strip() for t in TOPICS):
    repo.replace_topics([t.strip() for t in TOPICS if t.strip()])
    print("Topics set.")

# --- ADD LABELS ---
for label in LABELS:
    repo.create_label(name=label["name"], color=label["color"])
print("Standard labels added.")

# --- ADD GOOGLE CLOUDBUILD WEBHOOK ---
if add_cloudbuild:
    repo.create_hook(
        name="web",
        config={
            "url": CLOUDBUILD_WEBHOOK_URL,
            "content_type": "json"
        },
        events=["push", "pull_request"],
        active=True
    )
    print("Google Cloud Build webhook added.")

# --- ADD TEAMS/COLLABORATORS BASED ON CATEGORY ---
if category in ["sox", "banking"]:
    # Only code owners as collaborators
    for owner in codeowners:
        user = g.get_user(owner.strip())
        repo.add_to_collaborators(user, permission="admin")
    print("Code owners added as collaborators (admin access).")
else:
    # Normal: add org teams as collaborators
    for team_slug in TEAM_SLUGS:
        team = org.get_team_by_slug(team_slug.strip())
        team.add_to_repos(repo)
        team.set_repo_permission(repo, "push")
    print("Teams added as collaborators.")
    # Optionally, add org as reader (if you have a team for all org users)
    # Example: org.get_team_by_slug('all-users').add_to_repos(repo)

# --- SET BRANCH PROTECTION RULES ---
branch = repo.get_branch(DEFAULT_BRANCH)
branch.edit_protection(
    required_approving_review_count=1,
    enforce_admins=True,
    dismiss_stale_reviews=True,
    require_code_owner_reviews=True,
    restrictions=None
)
print("Branch protection rules set.")

# --- CREATE DEFAULT cloudbuild.yaml IF REQUESTED ---
if add_cloudbuild_yaml:
    cloudbuild_content = '''steps:\n  - name: 'gcr.io/cloud-builders/git'\n    args: ['clone', 'https://github.com/$REPO_NAME']\n  - name: 'gcr.io/cloud-builders/docker'\n    args: ['build', '-t', 'gcr.io/$PROJECT_ID/$REPO_NAME:$COMMIT_SHA', '.']\n  - name: 'gcr.io/cloud-builders/docker'\n    args: ['push', 'gcr.io/$PROJECT_ID/$REPO_NAME:$COMMIT_SHA']\n\nimages:\n  - 'gcr.io/$PROJECT_ID/$REPO_NAME:$COMMIT_SHA'\n'''
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(cloudbuild_content)
        tmp_path = tmp.name
    with open(tmp_path, "rb") as f:
        repo.create_file(
            path="cloudbuild.yaml",
            message="Add default cloudbuild.yaml",
            content=f.read(),
            branch=DEFAULT_BRANCH
        )
    print("Default cloudbuild.yaml added to the new repository.")

# --- CREATE CODEOWNERS FILE IF REQUESTED ---
if add_codeowners_file and codeowners:
    codeowners_content = "* " + " ".join([f"@{owner.strip()}" for owner in codeowners if owner.strip()])
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(codeowners_content)
        tmp_path = tmp.name
    with open(tmp_path, "rb") as f:
        repo.create_file(
            path=".github/CODEOWNERS",
            message="Add CODEOWNERS file",
            content=f.read(),
            branch=DEFAULT_BRANCH
        )
    print("CODEOWNERS file added to the new repository.")

# --- CREATE LICENSE FILE IF REQUESTED ---
if add_license:
    license_content = "MIT License\n\nCopyright (c) 2025 <Your Company>\n\nPermission is hereby granted, free of charge, to any person obtaining a copy..."
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(license_content)
        tmp_path = tmp.name
    with open(tmp_path, "rb") as f:
        repo.create_file(
            path="LICENSE",
            message="Add LICENSE file",
            content=f.read(),
            branch=DEFAULT_BRANCH
        )
    print("LICENSE file added to the new repository.")

# --- CREATE README.md FILE IF REQUESTED ---
if add_readme:
    readme_content = f"# {REPO_NAME}\n\n{DESCRIPTION}\n\n## Region\n{region}\n\n## Category\n{category}\n"
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(readme_content)
        tmp_path = tmp.name
    with open(tmp_path, "rb") as f:
        repo.create_file(
            path="README.md",
            message="Add README.md file",
            content=f.read(),
            branch=DEFAULT_BRANCH
        )
    print("README.md file added to the new repository.")

# --- CREATE ISSUE TEMPLATE IF REQUESTED ---
add_issue_template = input("Add default ISSUE_TEMPLATE? (y/n): ").lower() == "y"
if add_issue_template:
    issue_template_content = (
        "---\n"
        "name: Bug report\n"
        "about: Create a report to help us improve\n"
        "title: ''\n"
        "labels: bug\n"
        "assignees: ''\n\n"
        "---\n\n"
        "**Describe the bug**\nA clear and concise description of what the bug is.\n\n"
        "**To Reproduce**\nSteps to reproduce the behavior:\n1. Go to '...'")
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(issue_template_content)
        tmp_path = tmp.name
    with open(tmp_path, "rb") as f:
        repo.create_file(
            path=".github/ISSUE_TEMPLATE/bug_report.md",
            message="Add default bug report issue template",
            content=f.read(),
            branch=DEFAULT_BRANCH
        )
    print("Default ISSUE_TEMPLATE added to the new repository.")

# --- CREATE PULL REQUEST TEMPLATE IF REQUESTED ---
add_pr_template = input("Add default PULL_REQUEST_TEMPLATE? (y/n): ").lower() == "y"
if add_pr_template:
    pr_template_content = (
        "# Pull Request\n\n"
        "## Description\nPlease include a summary of the change and which issue is fixed.\n\n"
        "## Type of change\n- [ ] Bug fix\n- [ ] New feature\n- [ ] Breaking change\n- [ ] Documentation update\n\n"
        "## Checklist\n- [ ] My code follows the style guidelines\n- [ ] I have performed a self-review\n- [ ] I have commented my code\n- [ ] I have made corresponding changes to the documentation\n- [ ] My changes generate no new warnings\n")
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(pr_template_content)
        tmp_path = tmp.name
    with open(tmp_path, "rb") as f:
        repo.create_file(
            path=".github/PULL_REQUEST_TEMPLATE.md",
            message="Add default pull request template",
            content=f.read(),
            branch=DEFAULT_BRANCH
        )
    print("Default PULL_REQUEST_TEMPLATE added to the new repository.")

print(f"Repository '{REPO_NAME}' fully configured.")
