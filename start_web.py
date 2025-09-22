#!/usr/bin/env python
"""
start_web.py

Simple script to start the web interface for the MCP chatbot.
Run this script to launch the web application.
"""

import os
import sys
import subprocess

def main():
    print("🚀 Starting MCP Chatbot Web Interface...")
    print("📋 Open your browser and go to: http://localhost:8000")
    print("⏹️  Press Ctrl+C to stop the server")
    print()
    
    try:
        # Run the web application
        subprocess.run([
            sys.executable, 
            "web_app.py"
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
    except KeyboardInterrupt:
        print("\n👋 Shutting down web interface...")
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")

if __name__ == "__main__":
    main()