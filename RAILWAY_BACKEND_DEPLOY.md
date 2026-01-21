# 🚂 Railway Backend Deployment - Step by Step

## ❌ What Went Wrong:

Railway tried to deploy the **frontend** (Node/Vite) instead of the **backend** (Python/Flask).

---

## ✅ CORRECT Steps to Deploy Backend:

### **Step 1: Create New Service**

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose **`Shubham-275/modelscout-de997072`**

### **Step 2: Configure Root Directory** ⚠️ CRITICAL!

**IMMEDIATELY after the service is created:**

1. Click on the service card
2. Go to **Settings** tab (gear icon)
3. Scroll to **"Root Directory"**
4. Enter: `backend`
5. Click **"Update"**

**This tells Railway to deploy the Python backend, not the Node frontend!**

### **Step 3: Add Environment Variables**

1. Click **"Variables"** tab
2. Click **"+ New Variable"**
3. Add these one by one:

```
MINO_API_KEY=sk-mino-jBi3ccgxYhMoOMupjX0YFPdbSrvPADS3
MINO_API_URL=https://mino.ai/v1/automation/run-sse
DATABASE_PATH=/app/modelscout.db
FLASK_ENV=production
PORT=5000
```

### **Step 4: Trigger Redeploy**

1. Go to **"Deployments"** tab
2. Click **"Deploy"** or wait for auto-deploy
3. Watch the logs - should see:
   ```
   ✓ Detected Python
   ✓ Installing requirements.txt
   ✓ Starting gunicorn
   ```

### **Step 5: Get Your Railway URL**

1. Go to **"Settings"** tab
2. Scroll to **"Networking"**
3. Click **"Generate Domain"**
4. Copy the URL (e.g., `https://modelscout-production.up.railway.app`)

---

## 🎯 Expected Deployment Logs:

```
↳ Detected Python
↳ Using pip package manager
↳ Installing from requirements.txt
↳ Starting with gunicorn

Packages
──────────
python  │  3.11.x  │  nixpacks default
pip     │  latest  │  nixpacks default

Steps
──────────
▸ install
$ pip install -r requirements.txt

▸ start
$ gunicorn --bind 0.0.0.0:$PORT app:app

Deploy
──────────
✓ Successfully deployed!
```

---

## 🐛 If It Still Fails:

### **Check These:**

1. **Root Directory is set to `backend`** ✅
   - Settings → Root Directory → `backend`

2. **railway.json exists in backend folder** ✅
   - Already created and pushed

3. **requirements.txt has gunicorn** ✅
   - Already included

### **Common Errors:**

**Error: "No such file or directory: requirements.txt"**
- **Fix**: Root directory not set to `backend`

**Error: "Module 'app' not found"**
- **Fix**: Root directory not set to `backend`

**Error: "Port already in use"**
- **Fix**: Use `$PORT` environment variable (already configured)

---

## 📋 Quick Checklist:

- [ ] Railway project created
- [ ] Root directory set to `backend`
- [ ] Environment variables added (5 total)
- [ ] Deployment successful
- [ ] Railway URL generated
- [ ] URL copied for Vercel

---

## 🔄 After Backend Deploys:

### **Update Vercel with Backend URL:**

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click your `modelscout-de997072` project
3. **Settings** → **Environment Variables**
4. Add/Update:
   ```
   VITE_API_URL=https://your-railway-url.up.railway.app
   ```
5. Go to **Deployments** → Click **"..."** → **"Redeploy"**

---

## ✅ Test Your Backend:

Once deployed, test it:

```bash
curl https://your-railway-url.up.railway.app/health
```

Should return:
```json
{"status": "ok"}
```

---

**The key is setting Root Directory to `backend` BEFORE the first deploy!** 🎯
