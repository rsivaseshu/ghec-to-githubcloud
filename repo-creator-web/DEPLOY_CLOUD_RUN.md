# Deploying the Flask GitHub Repo Creator to Google Cloud Run

## 1. Prerequisites
- Google Cloud account and project
- gcloud CLI installed and authenticated
- Enable Cloud Run and Artifact Registry APIs

## 2. Prepare your app
- Your Flask app should be in a folder (e.g., `repo-creator-web`)
- Make sure you have a `requirements.txt` file with:
  ```
  Flask
  PyGithub
  gunicorn
  ```
- Add a `Dockerfile` (see below)

## 3. Example Dockerfile
```
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["gunicorn", "-b", ":8080", "app:app"]
```

## 4. Deploy to Cloud Run
From the `repo-creator-web` directory, run:

```
gcloud builds submit --tag gcr.io/$(gcloud config get-value project)/repo-creator-web

gcloud run deploy repo-creator-web \
  --image gcr.io/$(gcloud config get-value project)/repo-creator-web \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

- Replace `us-central1` with your preferred region.
- After deployment, Cloud Run will give you a public URL for your app.

## 5. Security
- Consider using Google Secret Manager for your GitHub token or require users to input their own.

---

You now have a web-based GitHub repo creation tool running in Google Cloud!
