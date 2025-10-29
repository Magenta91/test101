# Railway Deployment Guide 🚂

Railway is perfect for Flask apps - much easier than PythonAnywhere!

## 🚀 **Quick Deployment Steps**

### 1. **Prepare Your Repository**
```bash
# Make sure you're on the v5 branch
git checkout v5

# Copy Railway requirements
cp requirements-railway.txt requirements.txt

# Commit the Railway files
git add railway.json Procfile nixpacks.toml requirements.txt
git commit -m "Add Railway deployment configuration"
git push origin v5
```

### 2. **Deploy to Railway**

#### **Option A: GitHub Integration (Recommended)**
1. Go to [railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Choose **`Magenta91/test101`**
6. Select **`v5` branch**
7. Railway will auto-detect and deploy!

#### **Option B: Railway CLI**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

### 3. **Configure Environment Variables**
In Railway dashboard, go to **Variables** tab and add:

```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
OPENAI_API_KEY=your_openai_api_key
S3_BUCKET_NAME=your_s3_bucket_name
AWS_REGION=us-east-1
FLASK_ENV=production
```

### 4. **Custom Domain (Optional)**
- Go to **Settings** → **Domains**
- Add your custom domain or use Railway's generated URL

## ✅ **Why Railway is Better**

### **Advantages over PythonAnywhere:**
- ✅ **Automatic deployments** from GitHub
- ✅ **No file size limits** for uploads
- ✅ **Better performance** and scaling
- ✅ **Built-in SSL/HTTPS**
- ✅ **Environment variable management**
- ✅ **Real-time logs and monitoring**
- ✅ **No manual WSGI configuration**
- ✅ **Supports all Python packages**

### **Railway Features:**
- 🔄 **Auto-deploys** on git push
- 📊 **Built-in monitoring**
- 🔒 **Automatic HTTPS**
- 🌍 **Global CDN**
- 💾 **Persistent storage**
- 🔧 **Easy scaling**

## 📋 **Files Created for Railway**

1. **`railway.json`** - Railway configuration
2. **`Procfile`** - Process definition
3. **`nixpacks.toml`** - Build configuration
4. **`requirements-railway.txt`** - Python dependencies
5. **Updated `app.py`** - Added PORT configuration

## 🔧 **Configuration Details**

### **Web Server:**
- **Gunicorn** WSGI server
- **Port:** Dynamic (Railway assigns)
- **Workers:** 1 (optimized for Railway)
- **Timeout:** 120 seconds (for PDF processing)

### **Build Process:**
- **Python 3.10**
- **Tesseract OCR** included
- **All dependencies** auto-installed

## 🌐 **Access Your App**

After deployment, your app will be available at:
```
https://your-app-name.up.railway.app
```

## 📊 **Expected Performance**

### **Railway Free Tier:**
- ✅ **500 hours/month** execution time
- ✅ **1GB RAM**
- ✅ **1GB storage**
- ✅ **Unlimited bandwidth**

### **Perfect for:**
- ✅ PDF processing (up to 16MB files)
- ✅ OpenAI API calls
- ✅ AWS Textract integration
- ✅ Excel export downloads

## 🔍 **Monitoring & Logs**

Railway provides:
- **Real-time logs** in dashboard
- **Metrics** and performance monitoring
- **Deployment history**
- **Environment management**

## 🎯 **Success Checklist**

After deployment, verify:
- [ ] App loads at Railway URL
- [ ] PDF upload works
- [ ] AWS Textract processes files
- [ ] OpenAI extraction works
- [ ] Excel download functions
- [ ] No errors in Railway logs

## 💡 **Pro Tips**

1. **Use Railway's GitHub integration** for automatic deployments
2. **Monitor logs** during first deployment
3. **Test with small PDFs first**
4. **Set up custom domain** for production use
5. **Enable notifications** for deployment status

Railway deployment is much smoother than PythonAnywhere! 🎉

Your PDF extraction app will be live in minutes, not hours! 🚀