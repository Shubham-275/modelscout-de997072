# 🚀 Vercel + Railway Deployment Guide

## Why This Combo?
- **Vercel**: Best-in-class frontend hosting, instant deploys, global CDN
- **Railway**: Modern backend hosting, better than Render, $5 free credit/month
- **Total Setup Time**: 5 minutes ⚡

---

## 🎯 Step-by-Step Deployment

### Part 1: Deploy Backend to Railway (2 minutes)

1. **Go to [railway.app](https://railway.app)**
   - Sign in with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `modelscout` repository

3. **Configure Service**
   - Railway will auto-detect it's a Python app ✅
   - Click "Add variables" and add:
     ```
     MINO_API_KEY=your_mino_api_key_here
     MINO_API_URL=https://mino.ai/v1/automation/run-sse
     DATABASE_PATH=/app/modelscout.db
     FLASK_ENV=production
     ```

4. **Set Root Directory**
   - Go to Settings → Root Directory
   - Set to: `backend`

5. **Configure Build & Start**
   - Railway auto-detects from `requirements.txt` ✅
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 app:app`

6. **Deploy!**
   - Click "Deploy"
   - Wait ~2 minutes for first deploy
   - Copy your Railway URL (e.g., `https://modelscout-production.up.railway.app`)

---

### Part 2: Deploy Frontend to Vercel (2 minutes)

1. **Go to [vercel.com](https://vercel.com)**
   - Sign in with GitHub

2. **Import Project**
   - Click "Add New..." → "Project"
   - Select your `modelscout` repository
   - Vercel auto-detects Vite ✅

3. **Configure Environment Variables**
   - Add this variable:
     ```
     VITE_API_URL=https://your-railway-url.up.railway.app
     ```
   - Replace with your actual Railway URL from Part 1

4. **Deploy!**
   - Click "Deploy"
   - Wait ~1 minute
   - Your app is live! 🎉

---

## 🔧 Railway Configuration Files

### Option 1: Using railway.json (Recommended)

Create `railway.json` in your `backend` folder:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 app:app",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Option 2: Using nixpacks.toml

Create `nixpacks.toml` in your `backend` folder:

```toml
[phases.setup]
nixPkgs = ["python310"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 app:app"
```

---

## 🌐 Custom Domain Setup

### Vercel (Frontend)
1. Go to Project Settings → Domains
2. Add your domain (e.g., `modelscout.com`)
3. Update DNS:
   ```
   Type: CNAME
   Name: @
   Value: cname.vercel-dns.com
   ```

### Railway (Backend)
1. Go to Settings → Networking
2. Click "Generate Domain" for free `.railway.app` subdomain
3. Or add custom domain (e.g., `api.modelscout.com`):
   ```
   Type: CNAME
   Name: api
   Value: your-service.railway.app
   ```

---

## 💰 Pricing

### Free Tier
- **Vercel**: 100GB bandwidth/month, unlimited projects
- **Railway**: $5 free credit/month (~500 hours)
- **Total**: FREE for hobby projects! 🎉

### Paid Tier (If you need more)
- **Vercel Pro**: $20/month (unlimited bandwidth)
- **Railway**: Pay-as-you-go (~$5-10/month for small apps)

---

## 🔄 Auto-Deploy Setup

Both platforms auto-deploy on git push to `main` branch!

**To deploy:**
```bash
git add .
git commit -m "Update feature"
git push origin main
```

Both services will automatically rebuild and deploy ✅

---

## 📊 Monitoring & Logs

### Railway
- Real-time logs: Click on service → "Logs" tab
- Metrics: CPU, Memory, Network usage
- Deployments: See all deployment history

### Vercel
- Analytics: Built-in web analytics
- Logs: Deployment logs and runtime logs
- Performance: Core Web Vitals tracking

---

## 🐛 Troubleshooting

### Issue: Railway app crashes on startup
**Solution**: Check logs for errors. Common fixes:
```bash
# Make sure gunicorn is in requirements.txt
pip freeze | grep gunicorn

# Test locally first
gunicorn --bind 0.0.0.0:5000 app:app
```

### Issue: CORS errors on production
**Solution**: Update `app.py` CORS settings:
```python
from flask_cors import CORS

# Update this line
CORS(app, origins=["https://your-vercel-domain.vercel.app"])
```

### Issue: Environment variables not loading
**Solution**: 
1. Restart Railway service after adding variables
2. Check variable names match exactly (case-sensitive)

### Issue: Vercel build fails
**Solution**: Check build logs. Common fixes:
```bash
# Update dependencies
npm install

# Test build locally
npm run build
```

---

## 🚀 Advanced: GitHub Actions CI/CD

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run tests
        run: |
          npm install
          npm run test
      
      # Vercel and Railway auto-deploy on push
      # This workflow just runs tests before deploy
```

---

## ✅ Post-Deployment Checklist

- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured
- [ ] Custom domain added (optional)
- [ ] CORS configured for production domain
- [ ] Test all features on production URL
- [ ] Set up monitoring/alerts
- [ ] Share with users! 🎉

---

## 🆘 Need Help?

- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs
- **Railway Discord**: https://discord.gg/railway
- **Vercel Discord**: https://vercel.com/discord

---

## 🎯 Quick Commands Reference

```bash
# Test backend locally
cd backend
gunicorn --bind 0.0.0.0:5000 app:app

# Test frontend build
npm run build
npm run preview

# Deploy (auto-deploy on push)
git push origin main

# View Railway logs
railway logs

# View Vercel logs
vercel logs
```

---

## 🌟 Pro Tips

1. **Use Railway's free $5 credit wisely**: It's enough for ~500 hours/month
2. **Enable Vercel Analytics**: Free and gives great insights
3. **Set up uptime monitoring**: Use UptimeRobot (free) to monitor your app
4. **Use Railway's database add-ons**: If you need PostgreSQL/Redis
5. **Vercel Edge Functions**: For serverless API routes if needed

---

**You're all set! 🚀**

Deploy and share your amazing AI model comparison tool with the world!
