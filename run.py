import uvicorn
import webbrowser
import threading
import time
import os
import sys

def open_browser(url):
    time.sleep(1.2)
    print(f"\n🚀 Opening StudyPulse in your browser at {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"
    
    print("=" * 65)
    print("⚡ StudyPulse - Smart Course Tracker & AI Doubt Solver Platform")
    print("=" * 65)
    print(f"Starting server on {url} ...")
    
    # Open browser in a separate daemon thread
    threading.Thread(target=open_browser, args=(url,), daemon=True).start()
    
    # Start Uvicorn ASGI Server
    uvicorn.run("main:app", host=host, port=port, reload=False)
