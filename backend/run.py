# ── RUN SCRIPT ───────────────────────────────
"""SP3CT3R Backend Launcher"""
import uvicorn
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
    

# python run.py
# Visit http://localhost:8000/health
# uvicorn app.main:app --reload
