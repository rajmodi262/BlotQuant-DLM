import subprocess
import sys
import time
import webbrowser
import os
from pathlib import Path

# Config
BACKEND_PORT = int(os.environ.get("BLOTQUANT_PORT", 8001))
ROOT_DIR = Path(__file__).parent

def print_banner():
    print("\n" + "="*50)
    print("  🧬 BlotQuant DLM - Deep Learning Platform")
    print("="*50 + "\n")

def check_requirements():
    print("[1/3] Checking requirements...")
    
    # Check if Python is adequate
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8+ is required.")
        sys.exit(1)
        
    # Install Python requirements quietly
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt", "--quiet"],
            cwd=ROOT_DIR, check=True
        )
        print("  ✓ Python dependencies satisfied")
    except subprocess.CalledProcessError:
        print("❌ Error: Failed to install Python dependencies.")
        sys.exit(1)

    # Check if Node is installed
    try:
        subprocess.run(["node", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("  ✓ Node.js found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: Node.js is not installed or not in PATH.")
        sys.exit(1)

def start_servers():
    print(f"\n[2/3] Starting backend server (Port {BACKEND_PORT})...")
    
    # Init SQLite DB early
    db_dir = ROOT_DIR / "data" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Start Backend
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", str(BACKEND_PORT)],
        cwd=ROOT_DIR
    )
    
    time.sleep(2) # Give backend a moment to start
    
    print(f"\n[3/3] Starting frontend server (Vite)...")
    
    # NPM install if node_modules doesn't exist
    if not (ROOT_DIR / "frontend" / "node_modules").exists():
        print("  Installing frontend dependencies (first run)...")
        subprocess.run(["npm", "install", "--silent"], cwd=ROOT_DIR / "frontend", shell=(os.name == 'nt'))
        
    # Start Frontend
    frontend = subprocess.Popen(
        ["npx", "vite", "--host", "--port", "5173"],
        cwd=ROOT_DIR / "frontend",
        shell=(os.name == 'nt')  # Windows needs shell=True for npx
    )
    
    return backend, frontend

def main():
    print_banner()
    check_requirements()
    backend, frontend = start_servers()
    
    print("\n" + "="*50)
    print("  🚀 READY! Opening browser...")
    print(f"  Backend:  http://localhost:{BACKEND_PORT}")
    print(f"  Frontend: http://localhost:5173")
    print("  Press Ctrl+C to stop all servers.")
    print("="*50 + "\n")
    
    time.sleep(3)
    webbrowser.open("http://localhost:5173")
    
    try:
        backend.wait()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        backend.terminate()
        frontend.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
