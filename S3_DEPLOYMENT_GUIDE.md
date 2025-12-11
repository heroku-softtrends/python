# 🚀 AWS S3 Integration & Heroku Deployment Guide

## ✅ **What's Been Configured**

### **1. Environment-Based Configuration**
- **Development**: Uses SQLite + Local file storage
- **Production**: Uses PostgreSQL + AWS S3 storage

### **2. AWS S3 Integration**
- ✅ S3 credentials configured in `.env`
- ✅ Bucket `sftinvoicereader` connected and tested
- ✅ File upload/download working
- ✅ Automatic storage mode switching based on environment

### **3. Database Configuration**
- ✅ SQLite for development (`ENVIRONMENT=development`)
- ✅ PostgreSQL for production (`ENVIRONMENT=production`)
- ✅ Connection pooling and timeout handling

---

## 🔧 **Environment Configuration**

### **Current `.env` Settings:**
```properties
# Change this for deployment
ENVIRONMENT=development  # development | production

# Database URLs
SQLITE_URL=sqlite:///./invoicereader.db
POSTGRES_URL=postgresql://u5hihvko57gqfc:p5ea23a8e2d8fa635303f78804905693f10fd3afd70e7ea20ceba27019e82fdf1@c57oa7dm3pc281.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d22ec8obdr7dh

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=AKIARACWDMKE4QS4644M
AWS_SECRET_ACCESS_KEY=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
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=sftinvoicereader

# File Storage Mode
FILE_STORAGE_MODE=s3  # local | s3
```

---

## 📋 **How It Works**

### **Development Mode** (`ENVIRONMENT=development`)
- **Database**: SQLite (`invoicereader.db`)
- **File Storage**: Local `uploads/` folder
- **Use Case**: Local development and testing

### **Production Mode** (`ENVIRONMENT=production`)
- **Database**: PostgreSQL (AWS RDS)
- **File Storage**: AWS S3 bucket
- **Use Case**: Heroku deployment

### **File Storage Logic:**
```python
# Files uploaded via POST /api/upload
if production:
    save_to_s3("s3://sftinvoicereader/filename.pdf")
else:
    save_to_local("uploads/filename.pdf")
```

---

## 🚀 **Heroku Deployment Steps**

### **1. Prepare for Deployment**
Update `.env` for production:
```properties
ENVIRONMENT=production
```

### **2. Create Heroku App**
```bash
heroku create your-invoice-reader-app
```

### **3. Set Environment Variables on Heroku**
```bash
# Database & Environment
heroku config:set ENVIRONMENT=production
heroku config:set DATABASE_URL="postgresql://u5hihvko57gqfc:p5ea23a8e2d8fa635303f78804905693f10fd3afd70e7ea20ceba27019e82fdf1@c57oa7dm3pc281.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d22ec8obdr7dh"

# AWS S3 Configuration
heroku config:set AWS_ACCESS_KEY_ID=AKIARACWDMKE4QS4644M
heroku config:set AWS_SECRET_ACCESS_KEY=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
heroku config:set AWS_REGION=us-east-1
heroku config:set AWS_S3_BUCKET_NAME=sftinvoicereader
heroku config:set FILE_STORAGE_MODE=s3

# Security
heroku config:set SECRET_KEY="your-production-secret-key-here"
```

### **4. Create Procfile**
```
web: uvicorn app.main:app --host=0.0.0.0 --port=${PORT:-5000}
```

### **5. Deploy**
```bash
git add .
git commit -m "Add S3 integration for Heroku deployment"
git push heroku main
```

---

## 🔍 **Testing the Configuration**

### **Test Local Development:**
```bash
# Set environment to development
ENVIRONMENT=development

# Start server
python -m uvicorn app.main:app --reload --port 8000

# Upload test file - should save to local uploads/ folder
```

### **Test Production Mode:**
```bash
# Set environment to production  
ENVIRONMENT=production

# Start server
python -m uvicorn app.main:app --reload --port 8000

# Upload test file - should save to S3 bucket
```

---

## 📊 **Current Status**

### **✅ Working Features:**
- ✅ Environment-based configuration
- ✅ AWS S3 file upload/download
- ✅ PostgreSQL database connection
- ✅ AI-powered field extraction
- ✅ File storage abstraction layer

### **📁 File Storage Locations:**
- **Development**: `uploads/filename.pdf` (local)
- **Production**: `s3://sftinvoicereader/filename.pdf` (S3)

### **🗄️ Database Storage:**
- **Development**: `invoicereader.db` (SQLite)
- **Production**: AWS RDS PostgreSQL

---

## ⚡ **Benefits for Heroku Deployment**

### **1. Persistent File Storage**
- ❌ **Before**: Files deleted every 24 hours on Heroku
- ✅ **Now**: Files stored permanently in AWS S3

### **2. Scalable Database**
- ❌ **Before**: SQLite not suitable for production
- ✅ **Now**: PostgreSQL supports multiple connections

### **3. Environment Flexibility**
- ✅ Easy switching between dev/production
- ✅ No code changes needed for deployment
- ✅ Secure credential management

---

## 🛠️ **Troubleshooting**

### **Issue: S3 Upload Fails**
```bash
# Check S3 credentials
aws s3 ls s3://sftinvoicereader --profile default

# Verify bucket permissions
```

### **Issue: Database Connection Fails**
```bash
# Test PostgreSQL connection
psql "postgresql://u5hihvko57gqfc:p5ea23a8e2d8fa635303f78804905693f10fd3afd70e7ea20ceba27019e82fdf1@c57oa7dm3pc281.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d22ec8obdr7dh"
```

### **Issue: Environment Variables Not Loading**
```bash
# Check .env file exists and has correct values
cat .env

# Verify environment loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('ENVIRONMENT'))"
```

---

## 🎯 **Next Steps for Deployment**

1. **Set `ENVIRONMENT=production`** in your Heroku config
2. **Deploy to Heroku** using the steps above
3. **Test file upload** to ensure S3 integration works
4. **Deploy your React frontend** with updated API endpoints

Your invoice reader is now ready for production deployment with persistent file storage! 🚀