#!/bin/bash

# Delete OAuth brand
gcloud alpha iap oauth-brands delete

# Delete API keys
gcloud alpha services api-keys list --format="value(name)" | while read -r key; do
    gcloud alpha services api-keys delete "$key"
done

# Remove IAM policy binding
gcloud projects remove-iam-policy-binding spry-ether-453902-b0 \
    --member="serviceAccount:gemini-service@spry-ether-453902-b0.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Delete service account
gcloud iam service-accounts delete gemini-service@spry-ether-453902-b0.iam.gserviceaccount.com \
    --quiet

# Disable services
gcloud services disable drive.googleapis.com --force
gcloud services disable aiplatform.googleapis.com --force

echo "Cleanup completed"