# ── STARTUP SCRIPT ───────────────────────
"""SP3CT3R — Start everything (backend + frontend)"""
import subprocess, sys, os, time, webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_backend():
    print("🚀 Starting SP3CT3R backend...")
    return subprocess.Popen([sys.executable, "backend/run.py"], cwd=ROOT)

def run_frontend():
    print("🎨 Starting SP3CT3R frontend...")
    return subprocess.Popen(["npm", "run", "dev"], cwd=os.path.join(ROOT, "frontend"))

if __name__ == "__main__":
    backend = run_backend()
    time.sleep(2)
    frontend = run_frontend()
    time.sleep(3)
    webbrowser.open("http://localhost:5173")
    print("\n✅ SP3CT3R is running!")
    print("   Backend:  http://localhost:8000")
    print("   Frontend: http://localhost:5173")
    print("   API Docs: http://localhost:8000/api/docs")
    print("\nPress Ctrl+C to stop.\n")
    try:
        backend.wait()
    except KeyboardInterrupt:
        backend.terminate()
        frontend.terminate()
        print("\n🛑 SP3CT3R stopped.")

