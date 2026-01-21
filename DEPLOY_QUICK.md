# 🚀 Deploy ModelScout in 5 Minutes

## ⚡ Recommended: Vercel + Railway

**Why this combo?**
- ✅ Fastest deployment
- ✅ Best developer experience  
- ✅ Free tier available
- ✅ Auto-deploy on git push
- ✅ Built-in monitoring

---

## 📦 Quick Deploy Steps

### 1️⃣ Push to GitHub (if not already)
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/modelscout.git
git push -u origin main
```

### 2️⃣ Deploy Backend to Railway (2 min)

1. Go to **[railway.app](https://railway.app)** → Sign in with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your `modelscout` repository
4. **Settings** → **Root Directory** → Set to `backend`
5. **Variables** → Add:
   ```
   MINO_API_KEY=your_key_here
   MINO_API_URL=https://mino.ai/v1/automation/run-sse
   ```
6. Click **"Deploy"** → Copy your Railway URL

### 3️⃣ Deploy Frontend to Vercel (2 min)

1. Go to **[vercel.com](https://vercel.com)** → Sign in with GitHub
2. Click **"Add New..."** → **"Project"**
3. Select your `modelscout` repository
4. **Environment Variables** → Add:
   ```
   VITE_API_URL=https://your-railway-url.up.railway.app
   ```
5. Click **"Deploy"**

### 4️⃣ Done! 🎉

Your app is live at:
- **Frontend**: `https://your-project.vercel.app`
- **Backend**: `https://your-project.up.railway.app`

---

## 🔄 Auto-Deploy Enabled

Every time you push to GitHub:
```bash
git add .
git commit -m "New feature"
git push
```
Both Vercel and Railway automatically rebuild and deploy! ✨

---

## 📖 Detailed Guides

- **Vercel + Railway**: See [DEPLOY_VERCEL_RAILWAY.md](./DEPLOY_VERCEL_RAILWAY.md)
- **All Options**: See [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Docker**: See [docker-compose.yml](./docker-compose.yml)

---

## 💰 Cost

**Free Tier:**
- Vercel: 100GB bandwidth/month
- Railway: $5 credit/month (~500 hours)
- **Total: FREE** for most projects! 🎉

---

## 🆘 Troubleshooting

### Backend not starting?
Check Railway logs → Common fix: Ensure `gunicorn` is in `requirements.txt`

### CORS errors?
Update `backend/app.py` with your Vercel domain in CORS settings

### Build failing?
Run `npm run build` locally first to catch errors

---

## ✅ Checklist

- [ ] Code pushed to GitHub
- [ ] Railway backend deployed
- [ ] Vercel frontend deployed  
- [ ] Environment variables set
- [ ] Test production URL
- [ ] Share with the world! 🌍

---

**Need help?** Check the detailed guides or open an issue!
