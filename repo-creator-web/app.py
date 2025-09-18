from flask import Flask, render_template, request, redirect, url_for, flash
import os
from github import Github

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in production

# Set your GitHub token securely here (env var or secret manager)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def create_github_repo(org_name, repo_name, team_slugs, labels, add_cloudbuild, category, region, codeowners):
    CLOUDBUILD_WEBHOOK_URL = "https://cloudbuild.googleapis.com/github/webhook"
    DEFAULT_BRANCH = "main"
    g = Github(GITHUB_TOKEN)
    org = g.get_organization(org_name)
    repo = org.create_repo(repo_name, private=True, auto_init=True)
    for label in labels:
        repo.create_label(name=label['name'], color=label['color'])
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
    if category in ["sox", "banking"]:
        for owner in codeowners:
            user = g.get_user(owner.strip())
            repo.add_to_collaborators(user, permission="admin")
    else:
        for team_slug in team_slugs:
            team = org.get_team_by_slug(team_slug.strip())
            team.add_to_repos(repo)
            team.set_repo_permission(repo, "push")
    branch = repo.get_branch(DEFAULT_BRANCH)
    branch.edit_protection(
        required_approving_review_count=1,
        enforce_admins=True,
        dismiss_stale_reviews=True,
        require_code_owner_reviews=True,
        restrictions=None
    )
    return True

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        org_name = request.form['org_name']
        repo_name = request.form['repo_name']
        team_slugs = request.form['team_slugs'].split(',')
        labels = []
        for label in request.form['labels'].split(','):
            if ':' in label:
                name, color = label.split(':')
                labels.append({'name': name.strip(), 'color': color.strip()})
        add_cloudbuild = 'add_cloudbuild' in request.form
        category = request.form['category']
        region = request.form['region']
        codeowners = request.form['codeowners'].split(',') if request.form['codeowners'] else []
        try:
            create_github_repo(org_name, repo_name, team_slugs, labels, add_cloudbuild, category, region, codeowners)
            flash(f"Repository '{repo_name}' created and configured!", 'success')
        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')
        return redirect(url_for('index'))
    return render_template('form.html')

if __name__ == '__main__':
    app.run(debug=True)
