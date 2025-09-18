# New Repository Setup Guide

## 1. Create a New Repository

- Update the configuration section in `ghec-ghc-migration.py` with your repo name, org, and teams.
- Run the script:
  ```
  python ghec-ghc-migration.py
  ```

## Automated Repository Creation

Run the provided Python script. You will be prompted for:
- GitHub token
- Organization name
- Repository name
- Team slugs (comma-separated)
- Labels (name:color, e.g., bug:d73a4a)
- Whether to add Google Cloud Build integration

The script will create and configure your repository based on your inputs.

## 2. Add Cloud Build Pipeline

- Copy the provided `cloudbuild.yaml` template into the root of your new repository.
- Customize the build steps as needed for your project.

## 3. Enable Google Cloud Build Integration

- The script automatically adds the Cloud Build webhook.
- Ensure your Google Cloud project is configured to accept GitHub triggers.

## 4. Push Your Code

- Commit and push your code and `cloudbuild.yaml` to the new repository.
