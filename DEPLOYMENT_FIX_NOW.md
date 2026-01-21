# 🚨 DEPLOYMENT FIX GUIDE

## Current Issues:

1. ❌ **Vercel still using Docker/nginx** (should use Vite)
2. ❌ **Backend not deployed** (API calls failing)
3. ❌ **Frontend can't connect to backend**

---

## 🔧 IMMEDIATE FIXES:

### Fix 1: Force Vercel to Rebuild (Clear Cache)

**Option A: Via Vercel Dashboard**
1. Go to https://vercel.com/dashboard
2. Click on your `modelscout-de997072` project
3. Go to **Settings** → **General**
4. Scroll down and click **"Delete Project"**
5. Re-import from GitHub (fresh start)

**Option B: Redeploy with Environment Variable**
1. Go to Vercel Dashboard → Your Project
2. **Settings** → **Environment Variables**
3. Add a dummy variable: `FORCE_REBUILD=true`
4. Go to **Deployments** → Click **"..."** on latest → **"Redeploy"**
5. Check **"Use existing Build Cache"** is **UNCHECKED**

---

### Fix 2: Deploy Backend to Railway (CRITICAL!)

**Your frontend is trying to call the backend API, but it doesn't exist yet!**

#### Step-by-Step Railway Deployment:

1. **Go to [railway.app](https://railway.app)**
   - Sign in with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `Shubham-275/modelscout-de997072`

3. **Configure Root Directory**
   - After project creates, click on the service
   - Go to **Settings** → **Root Directory**
   - Set to: `backend`
   - Click "Save"

4. **Add Environment Variables**
   - Go to **Variables** tab
   - Click "+ New Variable"
   - Add these:
     ```
     MINO_API_KEY=sk-mino-jBi3ccgxYhMoOMupjX0YFPdbSrvPADS3
     MINO_API_URL=https://mino.ai/v1/automation/run-sse
     DATABASE_PATH=/app/modelscout.db
     FLASK_ENV=production
     PORT=5000
     ```

5. **Deploy!**
   - Railway will auto-deploy
   - Wait ~2-3 minutes
   - Copy your Railway URL (e.g., `https://modelscout-production.up.railway.app`)

6. **Update Vercel with Backend URL**
   - Go to Vercel Dashboard
   - Your project → **Settings** → **Environment Variables**
   - Add/Update:
     ```
     VITE_API_URL=https://your-railway-url.up.railway.app
     ```
   - Redeploy Vercel

---

## 🎯 Expected Result After Fixes:

### Vercel (Frontend):
- ✅ Uses Vite build (not Docker)
- ✅ Serves static React app
- ✅ No nginx logs
- ✅ Fast loading

### Railway (Backend):
- ✅ Python Flask app running
- ✅ Mino API connected
- ✅ Database initialized
- ✅ API endpoints working

### Integration:
- ✅ Frontend calls backend API
- ✅ "Get Recommendation" works
- ✅ "Find a Model" works
- ✅ "Benchmarks" page works

---

## 🐛 Debugging Steps:

### If Vercel Still Shows nginx Logs:

1. **Delete the Dockerfile**:
   ```bash
   git rm Dockerfile nginx.conf docker-compose.yml
   git commit -m "Remove Docker files for Vercel"
   git push
   ```

2. **Force Vercel to use Vite**:
   - Update `vercel.json`:
     ```json
     {
       "buildCommand": "npm run build",
       "outputDirectory": "dist",
       "framework": "vite"
     }
     ```

### If Backend Fails on Railway:

1. **Check Logs**:
   - Railway Dashboard → Your Service → "Logs" tab
   - Look for errors

2. **Common Issues**:
   - Missing `gunicorn` in `requirements.txt` (already added ✅)
   - Wrong root directory (should be `backend`)
   - Missing environment variables

### If Frontend Can't Connect to Backend:

1. **Check CORS**:
   - Backend `app.py` should have:
     ```python
     from flask_cors import CORS
     CORS(app)  # Allow all origins for now
     ```

2. **Check Environment Variable**:
   - Vercel → Settings → Environment Variables
   - `VITE_API_URL` should match Railway URL exactly

---

## ✅ Quick Verification:

### Test Backend (Railway):
```bash
curl https://your-railway-url.up.railway.app/health
# Should return: {"status": "ok"}
```

### Test Frontend (Vercel):
1. Open: https://modelscout-de997072.vercel.app
2. Click "Find a Model"
3. Type "travel assistant"
4. Click "GET RECOMMENDATION"
5. Should work! ✅

---

## 📋 Deployment Checklist:

- [ ] Railway backend deployed
- [ ] Railway environment variables set
- [ ] Railway URL copied
- [ ] Vercel environment variable updated with Railway URL
- [ ] Vercel redeployed (with cache cleared)
- [ ] Frontend loads without nginx logs
- [ ] API calls work
- [ ] All features functional

---

## 🆘 Still Not Working?

**Option: Start Fresh**

1. Delete Vercel project
2. Delete Railway project
3. Follow `DEPLOY_QUICK.md` from scratch
4. Should take 5 minutes total

---

**Priority: Deploy the backend to Railway FIRST, then fix Vercel!** 🚀
