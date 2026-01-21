# 🎯 Deployment Checklist

## Pre-Deployment
- [ ] All features tested locally
- [ ] Production build works (`npm run build`)
- [ ] Backend runs with gunicorn (`gunicorn app:app`)
- [ ] Environment variables documented
- [ ] Code committed to GitHub

## Railway (Backend)
- [ ] Account created at railway.app
- [ ] New project created from GitHub repo
- [ ] Root directory set to `backend`
- [ ] Environment variables added:
  - [ ] `MINO_API_KEY`
  - [ ] `MINO_API_URL`
  - [ ] `DATABASE_PATH`
- [ ] First deployment successful
- [ ] Railway URL copied

## Vercel (Frontend)
- [ ] Account created at vercel.com
- [ ] Project imported from GitHub
- [ ] Environment variable added:
  - [ ] `VITE_API_URL` (Railway URL)
- [ ] First deployment successful
- [ ] Vercel URL copied

## Post-Deployment
- [ ] Frontend loads correctly
- [ ] Backend API responds
- [ ] "Find a Model" feature works
- [ ] "Benchmarks" page works
- [ ] Mino API integration working
- [ ] No CORS errors
- [ ] All routes accessible

## Optional Enhancements
- [ ] Custom domain added (Vercel)
- [ ] Custom domain added (Railway)
- [ ] Analytics enabled (Vercel)
- [ ] Monitoring set up (UptimeRobot)
- [ ] Error tracking (Sentry)

## Maintenance
- [ ] Auto-deploy enabled (default)
- [ ] Deployment notifications set up
- [ ] Backup strategy planned
- [ ] Update schedule defined

---

## 🚀 Ready to Deploy?

Follow: [DEPLOY_QUICK.md](./DEPLOY_QUICK.md)

## 📚 Need Details?

See: [DEPLOY_VERCEL_RAILWAY.md](./DEPLOY_VERCEL_RAILWAY.md)
