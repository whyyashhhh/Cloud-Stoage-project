# OAuth Social Login & Upload Limit Setup Guide

## ✅ Features Implemented

### 1. **400MB Upload Limit**
- Enforced on both frontend and backend
- Users get clear error message if file exceeds 400MB
- Configurable via `MAX_UPLOAD_SIZE_MB` environment variable

### 2. **Social Login (OAuth 2.0)**
Added three social login options:
- ✅ **Google** - Most popular for personal users
- ✅ **Facebook** - Wide reach and user base
- ✅ **GitHub** - Developer-friendly alternative

---

## 🚀 How to Set Up Social Login

### Option 1: Google OAuth

**Step 1: Create Google OAuth Credentials**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Navigate to "APIs & Services" → "Credentials"
4. Click "Create Credentials" → "OAuth 2.0 Client ID"
5. Select "Web Application"
6. Add Authorized redirect URIs:
   - `http://localhost:8000/api/v1/auth/callback/google` (development)
   - Your production URL when deploying

**Step 2: Add to .env**
```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback/google
```

---

### Option 2: Facebook OAuth

**Step 1: Create Facebook OAuth Credentials**
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app → "Consumer"
3. Select "Facebook Login" product
4. Go to Settings → Basic, copy App ID and Secret
5. Under Products → Facebook Login → Settings:
   - Add Valid OAuth Redirect URIs:
     - `http://localhost:8000/api/v1/auth/callback/facebook` (development)
     - Your production URL when deploying

**Step 2: Add to .env**
```env
FACEBOOK_CLIENT_ID=your-app-id
FACEBOOK_CLIENT_SECRET=your-app-secret
FACEBOOK_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback/facebook
```

---

### Option 3: GitHub OAuth

**Step 1: Create GitHub OAuth App**
1. Go to GitHub → Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Fill in:
   - Application name: "Cloud Storage"
   - Homepage URL: `http://localhost:3000`
   - Authorization callback URL: `http://localhost:8000/api/v1/auth/callback/github`
4. Copy Client ID and generate Client Secret

**Step 2: Add to .env**
```env
GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback/github
```

---

## 🔧 Configuration

### Complete .env Example
```env
# Database
DB_USER=clouduser
DB_PASSWORD=cloudpassword
DB_NAME=cloud_storage

# JWT Secret
SECRET_KEY=your-super-secret-key

# Upload Limit (400MB)
MAX_UPLOAD_SIZE_MB=400

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback/google

# Facebook OAuth
FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-secret
FACEBOOK_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback/facebook

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-secret
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback/github

# Frontend
FRONTEND_URL=http://localhost:3000
```

---

## 📱 How Users Experience It

### Login Flow with Social Login
1. User visits login page
2. Sees three social login buttons: **Google**, **Facebook**, **GitHub**
3. Clicks button → redirected to provider
4. Logs in with their account
5. Approves permissions → auto-redirected to dashboard
6. Account created automatically (if first time)

### File Upload with Size Validation
1. User selects file > 400MB
2. Frontend shows: "File size exceeds 400MB limit (XXX)"
3. User can only upload files ≤ 400MB

---

## 🧪 Testing

### Test Without OAuth Setup
- Social buttons work but show configuration message
- Users can still use traditional username/password login

### Test With OAuth Setup
1. Start backend: `python -m uvicorn app:app --reload`
2. Start frontend: `python -m http.server 3000`
3. Navigate to `http://localhost:3000/modern-login.html`
4. Click Google/Facebook/GitHub button
5. Complete OAuth flow
6. Should be logged in and redirected to dashboard

### Test Upload Limit
1. Try uploading file > 400MB
2. Should see error: "File size exceeds 400MB limit"
3. Upload file < 400MB should work normally

---

## 📚 Backend Changes

### New Endpoints
```
GET  /api/v1/auth/oauth/google     → Returns Google auth URL
GET  /api/v1/auth/oauth/facebook   → Returns Facebook auth URL
GET  /api/v1/auth/oauth/github     → Returns GitHub auth URL

GET  /api/v1/auth/callback/google  → Handles Google callback (code → token)
GET  /api/v1/auth/callback/facebook → Handles Facebook callback (code → token)
GET  /api/v1/auth/callback/github   → Handles GitHub callback (code → token)
```

### Updated Endpoints
```
POST /api/v1/files/multipart/init  → Now validates file size (400MB limit)
```

### New Dependencies
- `authlib` - OAuth library
- `httpx` - Async HTTP client for OAuth calls

---

## 🎨 Frontend Changes

### Updated Pages
- `modern-login.html` - Social login buttons with handlers
- `modern-signup.html` - Social signup buttons
- `cloudvault_script.js` - File size validation (400MB)

### New Error Messages
- "File size exceeds 400MB limit"
- "OAuth configuration missing" (if provider not configured)

---

## 🔒 Security Notes

1. **Never commit credentials** - Keep .env in .gitignore
2. **Use production URLs** - Update redirect URIs for production
3. **Secure tokens** - Tokens stored in localStorage (consider secure cookies in production)
4. **HTTPS Required** - OAuth requires HTTPS in production

---

## 🚢 Deployment

When deploying to production:

1. Update all `REDIRECT_URI` values to production domain
2. Update `FRONTEND_URL` to production domain
3. Keep OAuth secrets secure in environment
4. Consider using secrets manager (AWS Secrets Manager, Azure Key Vault, etc.)

---

## ❓ Troubleshooting

### "OAuth is not configured"
- Check `.env` file has `PROVIDER_CLIENT_ID` set
- Restart backend after changing .env

### "Invalid redirect URI"
- Ensure redirect URI matches exactly in OAuth provider dashboard
- Include protocol: `http://` or `https://`
- Check for trailing slashes

### OAuth callback shows blank page
- Check browser console for errors
- Verify code parameter is in URL
- Restart backend

### File upload says "exceeds 400MB"
- This is intentional - upload limit is 400MB
- Can be changed via `MAX_UPLOAD_SIZE_MB` in .env

---

## 📞 Support

For OAuth issues, check:
- [Google OAuth Docs](https://developers.google.com/identity/protocols/oauth2)
- [Facebook Login Docs](https://developers.facebook.com/docs/facebook-login)
- [GitHub OAuth Docs](https://docs.github.com/en/developers/apps/building-oauth-apps)
