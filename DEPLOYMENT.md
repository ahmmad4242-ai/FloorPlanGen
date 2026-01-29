# FloorPlanGen Generator Service - Deployment Guide

## 🚀 Deploy to Railway.app (Recommended)

### Prerequisites
- GitHub account
- Railway.app account (free tier available)

### Deployment Steps

1. **Push to GitHub**
   ```bash
   cd /home/user/webapp
   git add generator-service/
   git commit -m "feat: Prepare Generator Service for deployment"
   git push origin main
   ```

2. **Deploy on Railway**
   - Go to https://railway.app
   - Sign in with GitHub
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `FloorPlanGen` repository
   - Select `generator-service` as root directory
   - Railway will auto-detect Dockerfile and deploy

3. **Get Service URL**
   - After deployment, Railway will provide a URL like:
   - `https://floorplangen-generator.up.railway.app`

4. **Update Backend**
   - Copy the Railway URL
   - Update `GENERATOR_URL` in Backend code
   - Deploy Backend to Cloudflare Pages

---

## 🐳 Deploy to Google Cloud Run

### Deployment Steps

1. **Install Google Cloud SDK**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Deploy**
   ```bash
   cd /home/user/webapp/generator-service
   gcloud run deploy floorplangen-generator \
     --source . \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8001
   ```

3. **Get Service URL**
   ```
   Service URL: https://floorplangen-generator-xxx-uc.a.run.app
   ```

---

## 🎯 Deploy to Render.com

### Deployment Steps

1. **Connect GitHub**
   - Go to https://render.com
   - Sign in with GitHub
   - Click "New +"
   - Select "Web Service"
   - Connect your repository

2. **Configure Service**
   - Name: `floorplangen-generator`
   - Environment: `Docker`
   - Region: `Oregon (US West)`
   - Branch: `main`
   - Root Directory: `generator-service`

3. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)

4. **Get Service URL**
   ```
   https://floorplangen-generator.onrender.com
   ```

---

## 🧪 Test Deployment

After deployment, test with:

```bash
# Health check
curl https://YOUR_SERVICE_URL/health

# Test generation
curl -X POST https://YOUR_SERVICE_URL/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test-001",
    "variant_count": 1,
    "boundary_layer": "BOUNDARY",
    "constraints": {
      "units": [
        {"type": "1BR", "count": 2, "net_area_m2": {"min": 60, "max": 75}}
      ],
      "circulation": {
        "corridor_width_m": {"min": 2.0, "target": 2.3}
      }
    }
  }'
```

---

## 📊 Cost Comparison

| Platform | Free Tier | Paid Plan | Best For |
|----------|-----------|-----------|----------|
| Railway | 500 hours/month | $5/month | Quick deploy |
| Google Cloud Run | 2M requests/month | Pay per use | Production |
| Render | 750 hours/month | $7/month | Simple setup |

**Recommendation: Railway.app** (easiest + free tier)

---

## 🔗 Next Steps After Deployment

1. Copy your deployment URL
2. Update Backend `GENERATOR_URL`
3. Test integration
4. Deploy to production
5. Celebrate! 🎉

