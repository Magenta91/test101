# PDF Extraction Service - Production Branch

🚀 **Production-ready Flask application for intelligent PDF data extraction**

## ✨ Features

- **Dual PDF Processing**: AWS Textract + Tesseract OCR fallback
- **AI-Powered Extraction**: OpenAI GPT-4o-mini for intelligent data processing
- **Unified Output**: 55+ numerical fields + 1 comprehensive commentary
- **Excel Export**: Clean, structured data export
- **Cost Tracking**: Real-time processing cost monitoring
- **Production Ready**: Optimized for Railway deployment

## 🚀 Quick Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/github/Magenta91/test101?branch=prod)

### Manual Deployment:
1. Fork this repository
2. Connect to Railway
3. Set environment variables
4. Deploy!

## ⚙️ Environment Variables

Set these in Railway dashboard:

```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
OPENAI_API_KEY=your_openai_api_key
S3_BUCKET_NAME=your_s3_bucket_name
AWS_REGION=us-east-1
FLASK_ENV=production
```

## 🏗️ Architecture

- **Frontend**: HTML5 + CSS3 + JavaScript
- **Backend**: Flask (Python 3.10)
- **PDF Processing**: AWS Textract → Tesseract OCR (fallback)
- **AI Processing**: OpenAI GPT-4o-mini
- **Data Export**: Pandas + OpenPyXL
- **Deployment**: Railway (Docker)

## 📊 Processing Flow

1. **PDF Upload** → Validate and process
2. **Text Extraction** → AWS Textract (primary) or Tesseract (fallback)
3. **AI Analysis** → OpenAI GPT-4o-mini extracts structured data
4. **Data Processing** → Unified extraction with single commentary
5. **Export** → Clean Excel file with numerical data + commentary

## 🔧 Health Monitoring

- **Health Check**: `/health` - Basic service status
- **Detailed Status**: `/status` - Module and dependency verification
- **Real-time Logs**: Available in Railway dashboard

## 💰 Cost Efficiency

- **Single API Call**: ~$0.004-0.005 per document
- **Optimized Processing**: GPT-4o-mini for cost-effectiveness
- **Smart Fallbacks**: Reduce cloud costs with local OCR

## 🛠️ Local Development

```bash
# Clone repository
git clone https://github.com/Magenta91/test101.git
cd test101
git checkout prod

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.production .env
# Edit .env with your API keys

# Run application
python app.py
```

## 📋 API Endpoints

- `GET /` - Main application interface
- `POST /extract` - PDF upload and processing
- `POST /process_stream` - Streaming data processing
- `GET /health` - Health check
- `GET /status` - Detailed system status

## 🔒 Security

- Environment variable configuration
- Input validation and sanitization
- File type and size restrictions
- Error handling and logging

## 📈 Performance

- **Processing Time**: 5-15 seconds per document
- **File Size Limit**: 16MB per PDF
- **Concurrent Processing**: Optimized for Railway's infrastructure
- **Memory Usage**: Efficient with garbage collection

## 🎯 Production Features

- ✅ **Docker containerization**
- ✅ **Gunicorn WSGI server**
- ✅ **Health monitoring**
- ✅ **Error handling**
- ✅ **Logging and debugging**
- ✅ **Environment-based configuration**

## 📞 Support

For issues or questions:
- Check Railway logs for deployment issues
- Verify environment variables are set correctly
- Ensure API keys have proper permissions

---

**Built for production. Optimized for Railway. Ready to scale.** 🚀