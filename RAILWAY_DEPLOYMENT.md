# Railway Deployment - Final Steps

## ✅ Code Successfully Pushed to GitHub!

Your security fixes are now in GitHub and Railway will auto-deploy.

---

## 🚀 STEP 1: Configure Railway Environment Variables

**IMPORTANT:** Railway needs these environment variables to run securely.

### Go to Railway Dashboard

1. Open: https://railway.app
2. Sign in
3. Click on your **ModelScout backend** project
4. Click on your service (the backend app)

### Add Environment Variables

Click **"Variables"** tab, then add these **one by one**:

```bash
MINO_API_KEY=sk-mino-jBi3ccgxYhMoOMupjX0YFPdbSrvPADS3
FLASK_ENV=production
ALLOWED_ORIGINS=https://modelscout-de997072.vercel.app
PORT=5000
```

**How to add:**
1. Click "+ New Variable"
2. Enter variable name (e.g., `MINO_API_KEY`)
3. Enter value
4. Click "Add"
5. Repeat for all 4 variables

### Save and Deploy

- Railway will automatically redeploy when you add variables
- Wait for deployment to complete (2-3 minutes)

---

## 🔍 STEP 2: Monitor Deployment

### Check Build Logs

1. In Railway dashboard, click **"Deployments"** tab
2. Click on the latest deployment
3. Watch the build logs

**Look for:**
```
✓ Installing dependencies from requirements.txt
✓ flask-limiter installed
✓ flask-talisman installed
✓ Starting application...
```

### Check Runtime Logs

Click **"View Logs"** and look for:

```
[OK] ModelScout Analyst module loaded successfully
[OK] Mino AI Analyst loaded successfully
[OK] Multimodal Analyst loaded successfully
ℹ️  Running in production mode (debug disabled)
[*] Model Scout Orchestrator starting on port 5000
```

**If you see errors:**
- ❌ "MINO_API_KEY is required" → Check env var is set correctly
- ❌ "ModuleNotFoundError" → Railway is installing dependencies
- ❌ "Port already in use" → Ignore, Railway handles this

---

## ✅ STEP 3: Test Your Deployment

### Test 1: Health Check

Open in browser or use curl:
```
https://modelscout-de997072-production.up.railway.app/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "model-scout-orchestrator",
  "version": "1.0.0-phase1",
  "timestamp": "2026-01-23T..."
}
```

### Test 2: API Sources

```
https://modelscout-de997072-production.up.railway.app/api/sources
```

**Expected:** JSON with benchmark sources

### Test 3: Frontend Integration

1. Open your Vercel app: https://modelscout-de997072.vercel.app
2. Try to get a recommendation
3. Should work without CORS errors

---

## 🔒 STEP 4: Verify Security

### Check CORS Protection

Open browser console (F12) on your Vercel app:
- ✅ No CORS errors
- ✅ API calls work normally

Try from unauthorized domain (should fail):
```bash
curl -H "Origin: https://evil.com" \
  https://modelscout-de997072-production.up.railway.app/api/sources
```

**Expected:** No `Access-Control-Allow-Origin` header (blocked)

### Check API Key Validation

Railway logs should show:
```
✓ MINO_API_KEY validated
```

### Check Debug Mode

Railway logs should show:
```
ℹ️  Running in production mode (debug disabled)
```

---

## 📊 Deployment Status Checklist

- [ ] Railway environment variables configured
- [ ] Railway deployment successful (green status)
- [ ] Health endpoint returns 200 OK
- [ ] API sources endpoint works
- [ ] Frontend can connect to backend
- [ ] No CORS errors in browser console
- [ ] CORS blocks unauthorized origins
- [ ] API key validated in logs
- [ ] Debug mode disabled in logs

---

## 🎯 Your Railway URL

**Backend API:** https://modelscout-de997072-production.up.railway.app

**Endpoints:**
- Health: `/health`
- Sources: `/api/sources`
- Search: `/api/search` (POST)
- Recommend: `/api/v2/analyst/recommend/ai` (POST)
- Multimodal: `/api/v2/analyst/recommend/multimodal` (POST)

---

## 🔧 Troubleshooting

### Problem: Deployment fails

**Check:**
1. Railway logs for error message
2. Ensure all 4 env vars are set
3. Check `requirements.txt` is in repo

**Solution:**
- Fix the error shown in logs
- Redeploy by clicking "Redeploy" in Railway

### Problem: "MINO_API_KEY is required"

**Solution:**
1. Go to Railway → Variables
2. Add `MINO_API_KEY` with your actual key
3. Railway will auto-redeploy

### Problem: CORS errors in browser

**Solution:**
1. Check `ALLOWED_ORIGINS` in Railway variables
2. Should be: `https://modelscout-de997072.vercel.app`
3. No trailing slash!
4. Redeploy if changed

### Problem: 502 Bad Gateway

**Solution:**
1. Check Railway logs for Python errors
2. Ensure `PORT=5000` is set
3. Check app is actually starting (look for "Running on port 5000")

---

## ✨ Success Indicators

When everything is working:

1. **Railway Dashboard:**
   - Status: Active (green)
   - Latest deployment: Successful
   - Logs show: "Running on port 5000"

2. **Health Endpoint:**
   - Returns 200 OK
   - JSON response with "healthy" status

3. **Frontend:**
   - No CORS errors
   - Recommendations work
   - No console errors

4. **Security:**
   - CORS blocks unauthorized origins
   - API key validated
   - Debug mode disabled

---

## 📈 Next Steps (After Deployment)

1. **Monitor for 24 hours**
   - Check Railway logs for errors
   - Monitor API usage
   - Watch for CORS issues

2. **Update Frontend ENV** (if needed)
   - Vercel → Settings → Environment Variables
   - Ensure `VITE_API_URL` points to Railway

3. **Test All Features**
   - Text LLM recommendations
   - Multimodal recommendations
   - Model comparisons

---

## 🎉 You're Done!

Once Railway shows "Active" and health check works, your security fixes are deployed!

**Deployment Time:** ~5 minutes  
**Status:** Ready for production ✅

---

**Railway URL:** https://modelscout-de997072-production.up.railway.app  
**Vercel URL:** https://modelscout-de997072.vercel.app

**Last Updated:** 2026-01-23
