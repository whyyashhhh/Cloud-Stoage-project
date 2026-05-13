# 🚀 How to Run Your Cloud Storage App

## Option 1: Docker Compose (Recommended) ✅

### Step 1: Navigate to project directory
```bash
cd "C:\Users\tsuya\OneDrive\Desktop\cloud project"
```

### Step 2: Start all services
```bash
docker-compose up -d
```

This starts:
- ✅ Frontend (nginx) on http://localhost:3000
- ✅ Backend (FastAPI) on http://localhost:8000
- ✅ PostgreSQL database on localhost:5432

### Step 3: Access the application
```
Login:     http://localhost:3000/modern-login.html
Sign Up:   http://localhost:3000/modern-signup.html
Dashboard: http://localhost:3000/modern-dashboard.html
API Docs:  http://localhost:8000/docs
```

### Step 4: Stop when done
```bash
docker-compose down
```

---

## Option 2: Windows Batch Script

Simply run:
```bash
setup.bat
```

This will start everything automatically!

---

## Option 3: Manual Setup (Advanced)

### Terminal 1 - Backend (FastAPI)
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 - Frontend (Nginx/Python)
```bash
cd frontend
python -m http.server 3000
```

---

## ✅ Verify Everything Works

### Check Backend Health
```
http://localhost:8000/api/v1/health
```

### Check Frontend
```
http://localhost:3000/modern-login.html
```

### Check API Documentation
```
http://localhost:8000/docs
```

---

## 🎯 Test the Application

1. **Create Account**
   - Go to: http://localhost:3000/modern-signup.html
   - Fill in username, email, password
   - Click "Sign up"

2. **Login**
   - Go to: http://localhost:3000/modern-login.html
   - Enter credentials
   - Click "Sign in"

3. **Upload File**
   - Drag & drop file or click upload area
   - Watch progress bar
   - File appears in list

4. **Download File**
   - Click "Download" button
   - File downloads automatically

5. **Delete File**
   - Click "Delete" button
   - Confirm deletion
   - File removed

6. **Restore Version**
   - Upload same file again (creates v2)
   - Click "Restore"
   - Select version to restore

---

## 📊 What You'll See

### Modern Design ✨
- Blue glass morphism theme
- Smooth animations
- Responsive layout
- Professional UI

### Organized Files ✅
- Clean HTML (no inline CSS)
- Single unified CSS file
- Fast loading
- Consistent design

---

## 🔧 Troubleshooting

### Port Already In Use
```bash
# Kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Database Connection Error
- Make sure PostgreSQL is running
- Check credentials in .env file
- Verify database exists

### Frontend Not Loading
- Check if nginx/Python server is running
- Clear browser cache
- Try incognito mode

---

## 📝 Environment Setup

Create `.env` file in backend with:
```env
DB_USER=clouduser
DB_PASSWORD=your_password
DB_NAME=cloud_storage
SECRET_KEY=your-secret-key
GCS_PROJECT_ID=your-project-id
GCS_BUCKET_NAME=your-bucket-name
```

---

## 🎉 You're Ready!

Your app is production-ready with:
- ✅ Organized frontend
- ✅ Optimized CSS (95% smaller)
- ✅ Professional design
- ✅ Full functionality
- ✅ Complete documentation

**Choose option 1 or 2 above and run!** 🚀
