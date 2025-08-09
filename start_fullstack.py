#!/usr/bin/env python3
"""
ProfAI Full Stack Launcher - Starts both backend and frontend
"""
import subprocess
import sys
import time
import os
from pathlib import Path

def check_node_installed():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Node.js not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js not installed")
        return False

def install_frontend_dependencies():
    """Install frontend dependencies"""
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    print("📦 Installing frontend dependencies...")
    try:
        result = subprocess.run(['npm', 'install'], cwd=frontend_dir, shell=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting FastAPI backend on port 8000...")
    
    # Set environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = 'src'
    
    try:
        # Start uvicorn server
        cmd = [sys.executable, '-m', 'uvicorn', 'profai.server:app', '--reload', '--host', '0.0.0.0', '--port', '8000']
        process = subprocess.Popen(cmd, env=env)
        return process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the React frontend"""
    print("⚛️  Starting React frontend on port 3000...")
    
    frontend_dir = Path("frontend")
    try:
        # Start React dev server
        process = subprocess.Popen(['npm', 'start'], cwd=frontend_dir, shell=True)
        return process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def main():
    print("🎓 ProfAI Full Stack Launcher")
    print("=" * 40)
    
    # Check if Node.js is installed
    if not check_node_installed():
        print("\n💡 Please install Node.js from https://nodejs.org/")
        print("   Then run this script again.")
        return
    
    # Install frontend dependencies if needed
    if not Path("frontend/node_modules").exists():
        if not install_frontend_dependencies():
            print("❌ Failed to install frontend dependencies")
            return
    
    print("\n🚀 Starting servers...")
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print("❌ Failed to start backend")
        return
    
    print("⏳ Waiting for backend to start...")
    time.sleep(3)  # Give backend time to start
    
    # Start frontend  
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ Failed to start frontend")
        backend_process.terminate()
        return
    
    print("\n🎉 Both servers started successfully!")
    print("📊 Backend API: http://localhost:8000")
    print("⚛️  Frontend UI: http://localhost:3000")
    print("\n💡 Your browser should automatically open to the frontend.")
    print("📝 API documentation available at: http://localhost:8000/docs")
    print("\n⚠️  Press Ctrl+C to stop both servers")
    
    try:
        # Wait for user to stop
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Servers stopped")

if __name__ == "__main__":
    main()
