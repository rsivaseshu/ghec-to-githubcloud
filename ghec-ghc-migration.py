"""
Interactive script to automate GitHub repo creation and setup for developers.
Prompts for repo name, team names, labels, and Cloud Build integration.
"""

from github import Github
import os

# --- USER INPUT ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or input("Enter your GitHub token: ")
ORG_NAME = input("Enter your GitHub organization name: ")
REPO_NAME = input("Enter the new repository name: ")
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
CLOUDBUILD_WEBHOOK_URL = "https://cloudbuild.googleapis.com/github/webhook"
DEFAULT_BRANCH = "main"

# --- AUTHENTICATION ---
g = Github(GITHUB_TOKEN)
org = g.get_organization(ORG_NAME)

# --- CREATE REPOSITORY ---
repo = org.create_repo(REPO_NAME, private=True, auto_init=True)
print(f"Repository '{REPO_NAME}' created.")

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

# --- ADD TEAMS AS COLLABORATORS ---
for team_slug in TEAM_SLUGS:
    team = org.get_team_by_slug(team_slug.strip())
    team.add_to_repos(repo)
    team.set_repo_permission(repo, "push")
print("Teams added as collaborators.")

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

print(f"Repository '{REPO_NAME}' fully configured.")
