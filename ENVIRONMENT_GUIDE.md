# Environment Configuration Guide

## 🔧 Development vs Production Setup

This application supports **environment-based database configuration**:

- **Development**: Uses SQLite (local file database)
- **Production**: Uses PostgreSQL (AWS RDS)

## 📁 Environment Files

- `.env` - Current active environment (auto-generated)
- `.env.development` - SQLite configuration for local development
- `.env.production` - PostgreSQL configuration for production
- `.env.backup` - Backup of previous .env (auto-created)

## 🚀 Quick Environment Switching

### Method 1: Using the Switch Script (Recommended)
```bash
# Switch to development (SQLite)
python switch_env.py development

# Switch to production (PostgreSQL)  
python switch_env.py production
```

### Method 2: Manual Environment Variable
```bash
# For development
set ENVIRONMENT=development

# For production  
set ENVIRONMENT=production
```

### Method 3: Direct .env Edit
Edit `.env` file and change:
```env
ENVIRONMENT=development  # or 'production'
```

## 🗃️ Database Information

### Development (SQLite)
- **Database**: `invoicereader.db` (local file)
- **Location**: BackEnd folder
- **Pros**: Fast, no network, easy setup
- **Use for**: Local development, testing

### Production (PostgreSQL)
- **Database**: AWS RDS PostgreSQL
- **Connection**: Encrypted, pooled connections
- **Pros**: Scalable, production-ready
- **Use for**: Live deployment, staging

## 🛠️ Server Commands

```bash
# Start development server (auto-detects environment)
python -m uvicorn app.main:app --reload --port 8000

# Force development environment
set ENVIRONMENT=development && python -m uvicorn app.main:app --reload

# Force production environment  
set ENVIRONMENT=production && python -m uvicorn app.main:app --reload
```

## 📋 Migration Commands

```bash
# Create tables (works with both databases)
python -c "from app.models import Base; from app.database import engine; Base.metadata.create_all(bind=engine)"

# Check current database
python -c "from app.database import DATABASE_URL; print(f'Using: {DATABASE_URL[:50]}...')"
```

## 🔍 Environment Status Check

The server will print the database type on startup:
- `🔧 Using SQLite for DEVELOPMENT environment`
- `🚀 Using PostgreSQL for PRODUCTION environment`

## 💡 Tips

1. **Always use development** for local coding
2. **Test with production** before deploying
3. **Keep .env.production secure** (don't commit with real credentials)
4. **Backup data** before switching environments
5. **Restart server** after environment changes