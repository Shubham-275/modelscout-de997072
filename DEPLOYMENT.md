# ModelScout Deployment Guide

## 🚀 Quick Deploy Options

### Option 1: Vercel (Frontend) + Render (Backend) - RECOMMENDED
**Best for**: Easy setup, free tier available

### Option 2: Railway (Full Stack)
**Best for**: Single platform deployment

### Option 3: Docker + Any Cloud Provider
**Best for**: Maximum control

---

## 📋 Pre-Deployment Checklist

- [ ] Mino API Key configured
- [ ] Environment variables documented
- [ ] Database initialized (if using persistent storage)
- [ ] CORS configured for production domain
- [ ] API endpoints tested

---

## 🎯 Option 1: Vercel + Render (Recommended)

### Frontend (Vercel)

1. **Install Vercel CLI** (optional):
   ```bash
   npm i -g vercel
   ```

2. **Deploy via Vercel Dashboard**:
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Framework: **Vite**
   - Root Directory: `./`
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **Environment Variables** (in Vercel Dashboard):
   ```
   VITE_API_URL=https://your-backend.onrender.com
   ```

### Backend (Render)

1. **Go to [render.com](https://render.com)**

2. **Create New Web Service**:
   - Connect your GitHub repository
   - Root Directory: `backend`
   - Runtime: **Python 3**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

3. **Environment Variables** (in Render Dashboard):
   ```
   MINO_API_KEY=your_mino_api_key_here
   MINO_API_URL=https://mino.ai/v1/automation/run-sse
   DATABASE_PATH=./modelscout.db
   FLASK_ENV=production
   ```

4. **Add to requirements.txt**:
   ```
   gunicorn==21.2.0
   ```

---

## 🎯 Option 2: Railway (Full Stack)

1. **Go to [railway.app](https://railway.app)**

2. **Deploy Backend**:
   - New Project → Deploy from GitHub
   - Root Directory: `backend`
   - Add environment variables (same as Render)

3. **Deploy Frontend**:
   - New Service → Deploy from GitHub  
   - Root Directory: `./`
   - Add `VITE_API_URL` pointing to backend URL

---

## 🎯 Option 3: Docker Deployment

### Backend Dockerfile
See `backend/Dockerfile`

### Frontend Dockerfile  
See `Dockerfile`

### Docker Compose
See `docker-compose.yml`

**Deploy to**:
- AWS ECS
- Google Cloud Run
- DigitalOcean App Platform
- Any VPS with Docker

---

## 🔒 Security Checklist

- [ ] Remove `.env` from git (already in `.gitignore`)
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS (automatic on Vercel/Render)
- [ ] Set CORS to specific domains (not `*`)
- [ ] Rate limit API endpoints
- [ ] Validate all user inputs

---

## 🌐 Custom Domain Setup

### Vercel (Frontend)
1. Go to Project Settings → Domains
2. Add your domain
3. Update DNS records as instructed

### Render (Backend)
1. Go to Settings → Custom Domains
2. Add `api.yourdomain.com`
3. Update DNS records

---

## 📊 Monitoring & Logs

### Vercel
- Automatic deployment logs
- Analytics dashboard
- Error tracking

### Render
- Real-time logs in dashboard
- Metrics & health checks
- Auto-deploy on git push

---

## 🔄 CI/CD

Both Vercel and Render auto-deploy on git push to main branch.

**To disable auto-deploy**:
- Vercel: Project Settings → Git
- Render: Service Settings → Auto-Deploy

---

## 💰 Cost Estimates

### Free Tier (Hobby Projects)
- **Vercel**: Free (100GB bandwidth/month)
- **Render**: Free (750 hours/month, sleeps after 15min inactivity)
- **Railway**: $5 credit/month

### Production (Paid)
- **Vercel Pro**: $20/month
- **Render Starter**: $7/month
- **Railway**: Pay-as-you-go (~$10-20/month)

---

## 🚨 Common Issues

### Issue: Backend sleeps on free tier
**Solution**: Upgrade to paid tier or use a cron job to ping every 10 minutes

### Issue: CORS errors
**Solution**: Update `app.py` CORS settings with production domain

### Issue: Environment variables not loading
**Solution**: Restart service after adding env vars

---

## 📞 Support

- Vercel Docs: https://vercel.com/docs
- Render Docs: https://render.com/docs
- Railway Docs: https://docs.railway.app

---

## ✅ Post-Deployment

1. Test all features on production URL
2. Monitor error logs for 24 hours
3. Set up uptime monitoring (UptimeRobot, Pingdom)
4. Share with users! 🎉
