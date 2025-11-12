# Railway Deployment Guide

## 🚀 Quick Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/github/Magenta91/test101?branch=prod2)

## 📋 Prerequisites

- Railway account (sign up at [railway.app](https://railway.app))
- OpenAI API key (required)
- AWS credentials (optional - for Textract)

## 🔧 Deployment Steps

### 1. Deploy from GitHub

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose **`Magenta91/test101`**
5. Select **`prod2` branch**
6. Railway will automatically detect the Dockerfile and deploy

### 2. Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

#### Required:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

#### Optional (for AWS Textract):
```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
S3_BUCKET_NAME=your_s3_bucket_name
AWS_REGION=us-east-1
```

#### Optional Configuration:
```env
FLASK_ENV=production
```

### 3. Deploy!

Railway will automatically:
- Build the Docker image
- Install all dependencies
- Start the application
- Provide a public URL

## 🌐 Access Your App

After deployment, your app will be available at:
```
https://your-app-name.up.railway.app
```

## 🔍 Health Check

Verify deployment:
```
https://your-app-name.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "PDF Extraction Service is running"
}
```

## ✨ Features

- **Unified Extraction**: 55+ numerical fields + 1 comprehensive commentary
- **Dual Processing**: AWS Textract (primary) + Tesseract OCR (fallback)
- **Cost Effective**: ~$0.004-0.005 per document
- **Clean Output**: Excel export without document summaries
- **Production Ready**: Gunicorn WSGI server with proper configuration

## 📊 Processing Options

### With AWS Credentials:
- Uses AWS Textract for high-quality extraction
- Falls back to Tesseract if Textract fails

### Without AWS Credentials:
- Uses Tesseract OCR only
- Still provides full functionality

## 🛠️ Troubleshooting

### Build Fails
- Check Railway logs for specific errors
- Verify Dockerfile syntax
- Ensure all dependencies are in requirements.txt

### App Doesn't Start
- Check environment variables are set
- Verify OPENAI_API_KEY is valid
- Check Railway logs for startup errors

### 500 Errors
- Verify OpenAI API key is valid and has credits
- Check Railway logs for detailed error messages
- Ensure PDF files are valid and not corrupted

## 📈 Performance

- **Build Time**: 3-5 minutes
- **Startup Time**: 10-30 seconds
- **Processing Time**: 5-15 seconds per PDF
- **Memory Usage**: ~500MB-1GB

## 💰 Cost Considerations

### Railway:
- Free tier: 500 hours/month execution time
- Paid plans: Starting at $5/month

### OpenAI API:
- GPT-4o-mini: ~$0.004-0.005 per document
- Depends on document size and complexity

### AWS Textract (Optional):
- Pay per document processed
- ~$0.015 per page

## 🔒 Security

- Environment variables stored securely in Railway
- HTTPS enabled by default
- No API keys in code or repository

## 📝 Files Included

- `Dockerfile` - Docker configuration
- `requirements.txt` - Python dependencies
- `railway.json` - Railway configuration
- `Procfile` - Process definition
- `.railwayignore` - Files to exclude from deployment
- `.env.example` - Environment variables template

## 🎯 Success Indicators

Your deployment is successful when:
- ✅ Build completes without errors
- ✅ Health endpoint returns 200
- ✅ Main page loads
- ✅ PDF upload and processing works
- ✅ Excel download functions

---

**Your PDF extraction service is now live on Railway!** 🎉