#!/bin/bash

# Google Cloud Run Deployment Script
# FloorPlanGen Generator Service

echo "🚀 Deploying FloorPlanGen Generator to Google Cloud Run"
echo "========================================================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK not installed"
    echo ""
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    echo ""
    echo "After installation, run:"
    echo "  gcloud auth login"
    echo "  gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "✅ Google Cloud SDK installed"
echo ""

# Navigate to generator service
cd /home/user/webapp/generator-service

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
echo "📦 Current project: $PROJECT_ID"
echo ""

# Deploy
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy floorplangen-generator \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8001 \
  --platform managed \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "Your service URL will be displayed above"
echo "It should look like: https://floorplangen-generator-xxx-uc.a.run.app"
echo ""
echo "Next steps:"
echo "1. Copy the service URL"
echo "2. Set GENERATOR_URL in Cloudflare"
echo "3. Deploy your backend"
