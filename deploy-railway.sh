#!/bin/bash

# Railway CLI Deployment Script for FloorPlanGen Generator

echo "🚀 FloorPlanGen Generator - Railway Deployment"
echo "=============================================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

echo "✅ Railway CLI installed"
echo ""

# Navigate to generator service
cd /home/user/webapp/generator-service

echo "🔐 Step 1: Login to Railway"
echo "Run: railway login"
echo "This will open a browser window for authentication"
echo ""
read -p "Press Enter after completing login..."

echo ""
echo "🎯 Step 2: Initialize Railway Project"
railway init

echo ""
echo "🚀 Step 3: Deploy to Railway"
railway up

echo ""
echo "🌐 Step 4: Get Service URL"
echo "Your service URL is:"
railway domain

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "Next steps:"
echo "1. Copy the URL above"
echo "2. Set it as GENERATOR_URL in Cloudflare"
echo "3. Deploy your backend"
echo ""
