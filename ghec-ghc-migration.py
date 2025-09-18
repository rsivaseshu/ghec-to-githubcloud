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

# --- CREATE SECURITY.md IF REQUESTED ---
add_security_md = input("Add SECURITY.md? (y/n): ").lower() == "y"
if add_security_md:
    security_content = (
        "# Security Policy\n\n"
        "## Reporting a Vulnerability\n"
        "Please report security issues to security@example.com.\n"
    )
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(security_content)
        tmp_path = tmp.name
    with open(tmp_path, "rb") as f:
        repo.create_file(
            path=".github/SECURITY.md",
            message="Add SECURITY.md file",
            content=f.read(),
            branch=DEFAULT_BRANCH
        )
    print("SECURITY.md file added to the new repository.")

# --- CREATE CONTRIBUTING.md IF REQUESTED ---
add_contributing_md = input("Add CONTRIBUTING.md? (y/n): ").lower() == "y"
if add_contributing_md:
    contributing_content = (
        "# Contributing\n\n"
        "Thank you for considering contributing!\n\n"
        "## How to contribute\n- Fork the repo\n- Create a feature branch\n- Submit a pull request\n"
    )
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(contributing_content)
        tmp_path = tmp.name
    with open(tmp_path, "rb") as f:
        repo.create_file(
            path=".github/CONTRIBUTING.md",
            message="Add CONTRIBUTING.md file",
            content=f.read(),
            branch=DEFAULT_BRANCH
        )
    print("CONTRIBUTING.md file added to the new repository.")

# --- SLACK/TEAMS NOTIFICATION (optional, via webhook env var) ---
import requests
slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
if slack_webhook:
    requests.post(slack_webhook, json={"text": f"Repo {REPO_NAME} created in {ORG_NAME}."})

# --- AUDIT LOGGING ---
from datetime import datetime
with open("repo_audit.log", "a") as log:
    log.write(f"{datetime.now()} | {REPO_NAME} | {ORG_NAME} | {category} | {region} | {codeowners}\n")

# --- ADVANCED BRANCH PROTECTION (status checks, push restrictions) ---
branch.edit_protection(
    required_approving_review_count=2,
    enforce_admins=True,
    dismiss_stale_reviews=True,
    require_code_owner_reviews=True,
    required_status_checks={"strict": True, "contexts": ["ci/test", "lint"]},
    restrictions=None
)
print("Advanced branch protection rules set.")

# --- TEKTON PIPELINE YAML IF REQUESTED ---
add_tekton = input("Add tekton.yaml for Tekton CI/CD? (y/n): ").lower() == "y"
if add_tekton:
    tekton_content = (
        "apiVersion: tekton.dev/v1beta1\n"
        "kind: Pipeline\n"
        "metadata:\n  name: sample-pipeline\n"
        "spec:\n  tasks:\n    - name: echo\n      taskSpec:\n        steps:\n          - name: echo\n            image: ubuntu\n            script: |\n              echo Hello Tekton!\n"
    )
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(tekton_content)
        tmp_path = tmp.name
    with open(tmp_path, "rb") as f:
        repo.create_file(
            path="tekton.yaml",
            message="Add Tekton pipeline template",
            content=f.read(),
            branch=DEFAULT_BRANCH
        )
    print("tekton.yaml file added to the new repository.")

# --- GCP SECRET MANAGER INTEGRATION (example) ---
add_gcp_secret = input("Create a GCP Secret? (y/n): ").lower() == "y"
if add_gcp_secret:
    try:
        from google.cloud import secretmanager
        gcp_project = input("Enter GCP project ID for secret: ")
        secret_id = input("Enter secret name: ")
        secret_value = input("Enter secret value: ")
        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{gcp_project}"
        secret = client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )
        client.add_secret_version(
            request={
                "parent": secret.name,
                "payload": {"data": secret_value.encode()},
            }
        )
        print(f"Secret {secret_id} created in GCP Secret Manager.")
    except Exception as e:
        print(f"GCP Secret Manager error: {e}")

# --- VAULT INTEGRATION (example) ---
add_vault_secret = input("Create a Vault secret? (y/n): ").lower() == "y"
if add_vault_secret:
    try:
        import hvac
        vault_url = input("Enter Vault URL: ")
        vault_token = input("Enter Vault token: ")
        secret_path = input("Enter Vault secret path: ")
        secret_key = input("Enter secret key: ")
        secret_value = input("Enter secret value: ")
        client = hvac.Client(url=vault_url, token=vault_token)
        client.secrets.kv.v2.create_or_update_secret(
            path=secret_path,
            secret={secret_key: secret_value},
        )
        print(f"Secret {secret_key} created at {secret_path} in Vault.")
    except Exception as e:
        print(f"Vault error: {e}")

print(f"Repository '{REPO_NAME}' fully configured.")
