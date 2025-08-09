#!/usr/bin/env python3
"""
Simple Backend Starter - Installs packages and starts server
"""
import subprocess
import sys
import os
from pathlib import Path

def install_packages():
    """Install required packages"""
    packages = [
        "fastapi==0.112.2",
        "uvicorn[standard]==0.30.6", 
        "python-multipart",
        "python-dotenv==1.0.1",
        "openai==1.40.3",
        "google-generativeai==0.8.3",
        "elevenlabs==1.9.0"
    ]
    
    print("📦 Installing required packages...")
    for package in packages:
        print(f"   Installing {package}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to install {package}: {result.stderr}")
            return False
        
    print("✅ All packages installed successfully")
    return True

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI server...")
    
    # Set environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = 'src'
    
    # Start server
    cmd = [sys.executable, "-m", "uvicorn", "profai.server:app", "--reload", "--host", "127.0.0.1", "--port", "8000"]
    
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

def main():
    print("🎓 ProfAI Backend Starter")
    print("=" * 30)
    
    # Install packages
    if not install_packages():
        print("❌ Failed to install packages")
        return
    
    # Start server
    print("🌐 Server will be available at: http://127.0.0.1:8000")
    print("📖 API docs will be available at: http://127.0.0.1:8000/docs")
    print("\n⚠️  Press Ctrl+C to stop the server")
    
    start_server()

if __name__ == "__main__":
    main()
