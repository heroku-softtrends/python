#!/usr/bin/env python3
"""
Environment switching script for Invoice Reader
Usage:
    python switch_env.py development  # Switch to SQLite
    python switch_env.py production   # Switch to PostgreSQL
"""

import sys
import shutil
import os

def switch_environment(env):
    """Switch to specified environment"""
    
    if env not in ['development', 'production']:
        print("❌ Error: Environment must be 'development' or 'production'")
        sys.exit(1)
    
    env_file_source = f".env.{env}"
    env_file_target = ".env"
    
    if not os.path.exists(env_file_source):
        print(f"❌ Error: {env_file_source} not found")
        sys.exit(1)
    
    # Backup current .env
    if os.path.exists(env_file_target):
        shutil.copy(env_file_target, f"{env_file_target}.backup")
        print(f"💾 Backed up current .env to .env.backup")
    
    # Copy environment-specific file
    shutil.copy(env_file_source, env_file_target)
    
    if env == "development":
        print("🔧 Switched to DEVELOPMENT environment (SQLite)")
        print("   Database: SQLite (invoicereader.db)")
        print("   Frontend URL: http://localhost:3000")
    else:
        print("🚀 Switched to PRODUCTION environment (PostgreSQL)")
        print("   Database: PostgreSQL (AWS RDS)")
        print("   Frontend URL: https://your-production-domain.com")
    
    print(f"\n✅ Environment configuration updated!")
    print("⚠️  Restart your server for changes to take effect")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python switch_env.py [development|production]")
        print("\nExamples:")
        print("  python switch_env.py development  # Use SQLite")
        print("  python switch_env.py production   # Use PostgreSQL")
        sys.exit(1)
    
    environment = sys.argv[1].lower()
    switch_environment(environment)