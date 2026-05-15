# Render Deployment Guide

## ✅ Prerequisites

1. **Render Account** - Sign up at [render.com](https://render.com)
2. **GitHub Repository** - Already done! ✓
3. **Database** - Render provides PostgreSQL
4. **AWS S3 Account** - For file storage (optional, can use local storage)
5. **OAuth Credentials** - From Google, Facebook, GitHub

---

## 🚀 Step-by-Step Deployment

### Step 1: Connect GitHub to Render

1. Go to [render.com](https://render.com) and login
2. Click **"New +"** → **"Blueprint"**
3. Select **"Public Git Repository"**
4. Paste: `https://github.com/whyyashhhh/Cloud-Stoage-project`
5. Click **"Connect"**
6. Authorize Render to access your GitHub account

---

### Step 2: Configure Services

Render will read `render.yaml` and show services to deploy:

#### **Backend (API)**
- Service: `cloud-storage-backend`
- Runtime: Python 3.11
- Region: Choose closest to your users
- Plan: Free tier (limited) or Paid for production

#### **Frontend**
- Service: `cloud-storage-frontend`
- Type: Static Site
- Automatically deploys from `/frontend` folder

#### **Database**
- PostgreSQL 15
- Auto-managed backups
- 90-day free trial

---

### Step 3: Set Environment Variables

Click the backend service and go to **Environment** tab. Add these:

```env
DATABASE_URL=postgresql://clouduser:PASSWORD@postgres-host:5432/cloud_storage
SECRET_KEY=your-super-secret-key-min-32-chars
REDIS_URL=redis://localhost:6379/0
MAX_UPLOAD_SIZE_MB=400

# AWS S3 (for file storage)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
S3_BUCKET_NAME=your-s3-bucket-name
AWS_REGION=us-east-1

# OAuth - Get these from provider dashboards
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://your-app.onrender.com/api/v1/auth/callback/google

FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret
FACEBOOK_REDIRECT_URI=https://your-app.onrender.com/api/v1/auth/callback/facebook

GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=https://your-app.onrender.com/api/v1/auth/callback/github

FRONTEND_URL=https://your-frontend.onrender.com
```

---

### Step 4: Create PostgreSQL Database

1. In Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Name: `cloud-storage-db`
3. Region: Same as backend
4. Copy the `Internal Database URL` (for services in same region)
5. Set as `DATABASE_URL` in backend environment

---

### Step 5: Configure OAuth Redirect URIs

Update each OAuth provider with your Render URLs:

#### **Google**
- Admin console → Credentials → OAuth 2.0 Client ID
- Add: `https://your-app.onrender.com/api/v1/auth/callback/google`

#### **Facebook**
- App Settings → Facebook Login → Valid OAuth Redirect URIs
- Add: `https://your-app.onrender.com/api/v1/auth/callback/facebook`

#### **GitHub**
- Settings → Developer settings → OAuth Apps
- Edit app → Authorization callback URL
- Set to: `https://your-app.onrender.com/api/v1/auth/callback/github`

---

### Step 6: Deploy

1. Click **"Deploy Blueprint"**
2. Render will:
   - Build backend service
   - Deploy frontend
   - Create/configure database
   - Run migrations
3. Wait for all services to show **"Live"** (green)

---

## 📊 After Deployment

### Access Your App
- **Frontend**: `https://cloud-storage-frontend.onrender.com`
- **Backend API**: `https://cloud-storage-backend.onrender.com`
- **API Docs**: `https://cloud-storage-backend.onrender.com/docs`

### Test Features
1. Sign up with Google/Facebook/GitHub
2. Login
3. Upload file < 400MB
4. Try uploading file > 400MB (should fail)
5. Download, restore, delete files

---

## 💰 Pricing

### Free Tier (Good for Testing)
- ❌ Services spin down after 15 min inactivity
- ✅ PostgreSQL free for 90 days
- ✅ 750 build minutes/month
- ✅ 100GB bandwidth/month

### Paid Tier (Production)
- ✅ Always running services
- ✅ PostgreSQL: ~$15/month
- ✅ Backend: ~$7/month
- ✅ Frontend: ~$7/month
- **Total**: ~$30/month for small production

---

## 🔧 Troubleshooting

### Service Won't Start
1. Check logs: Click service → **Logs** tab
2. Look for error messages
3. Verify environment variables are set
4. Check `startCommand` in render.yaml

### Database Connection Failed
- Verify `DATABASE_URL` is correct internal URL
- Database must be running
- Check credentials in URL match

### OAuth Login Fails
- Verify redirect URI matches exactly in provider dashboard
- Check `GOOGLE/FACEBOOK/GITHUB_CLIENT_ID` and `SECRET` are set
- Ensure frontend can reach backend (CORS configured)

### File Upload Fails
- Verify AWS S3 credentials are correct
- Check S3 bucket exists and is accessible
- Ensure `MAX_UPLOAD_SIZE_MB` is set to 400

---

## 📈 Scaling Beyond Free Tier

When ready for production:

1. **Upgrade Backend Service**
   - Click service → **Settings** → Change plan from "Free" to paid
   - Choose plan based on expected load

2. **Upgrade PostgreSQL**
   - Click database → **Settings** → Upgrade plan
   - Choose appropriate compute/storage

3. **Use Redis for Caching** (Optional)
   - Add Redis service in Render
   - Update `REDIS_URL` environment variable
   - Improves performance with rate limiting

4. **Enable Automatic Deploys**
   - Already enabled: pushes to main trigger deploys
   - Check **Auto-Deploy** toggle is on

---

## 🔐 Production Security Checklist

- [ ] Secret key is 32+ random characters
- [ ] OAuth secrets stored in environment (not in code)
- [ ] S3 bucket has proper access policies
- [ ] Database backup enabled
- [ ] HTTPS enforced (Render does this by default)
- [ ] CORS properly configured for frontend URL
- [ ] Rate limiting enabled (Redis needed)

---

## 📝 Monitoring

### Check Service Health
1. Dashboard shows green = all systems running
2. Click service → **Logs** to see activity
3. Check **Metrics** for CPU/memory usage

### Set Up Alerts (Paid)
1. Service → **Settings** → **Alerts**
2. Notify when service is down
3. Get email notifications

---

## 🚀 Next Steps

1. **Get OAuth Credentials** from providers (if not done)
2. **Set Environment Variables** in Render
3. **Deploy Blueprint** 
4. **Test All Features**
5. **Monitor Logs** for errors
6. **Upgrade to Paid** when ready for production

---

## 🆘 Support

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **GitHub**: Push new commits to main = automatic redeploy
- **View Logs**: Service → Logs tab for debugging

---

## 📞 Contact

For deployment issues, check:
1. Render logs in dashboard
2. Backend logs at `/api/v1/health`
3. Frontend console (F12) for client errors
