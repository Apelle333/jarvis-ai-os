#!/usr/bin/env python3
"""
JARVIS AI Operating System - Setup Validation
Validates that all components are properly installed and configured
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(path, description):
    """Check if a file exists"""
    if os.path.exists(path):
        print(f"[+] {description}: {path}")
        return True
    else:
        print(f"[-] {description}: {path} (NOT FOUND)")
        return False

def check_directory_exists(path, description):
    """Check if a directory exists"""
    if os.path.isdir(path):
        print(f"[+] {description}: {path}")
        return True
    else:
        print(f"[-] {description}: {path} (NOT FOUND)")
        return False

def check_python_module(module_name):
    """Check if a Python module can be imported"""
    try:
        __import__(module_name)
        print(f"[+] Python module: {module_name}")
        return True
    except ImportError as e:
        print(f"[-] Python module: {module_name} ({e})")
        return False

def main():
    print("JARVIS AI Operating System - Setup Validation")
    print("=" * 50)

    all_good = True

    # Check root directory structure
    print("\n1. Checking directory structure:")
    all_good &= check_directory_exists("backend", "Backend directory")
    all_good &= check_directory_exists("frontend", "Frontend directory")
    all_good &= check_directory_exists("database", "Database directory")
    all_good &= check_directory_exists("logs", "Logs directory")
    all_good &= check_directory_exists("models", "Models directory")

    # Check backend structure
    print("\n2. Checking backend structure:")
    all_good &= check_directory_exists("backend/agents", "Agents directory")
    all_good &= check_directory_exists("backend/api", "API directory")
    all_good &= check_directory_exists("backend/core", "Core directory")
    all_good &= check_directory_exists("backend/memory", "Memory directory")
    all_good &= check_directory_exists("backend/tools", "Tools directory")
    all_good &= check_directory_exists("backend/voice", "Voice directory")

    all_good &= check_file_exists("backend/main.py", "Main entry point")
    all_good &= check_file_exists("backend/requirements.txt", "Python requirements")
    all_good &= check_file_exists("backend/.env.example", "Environment example")

    # Check frontend structure
    print("\n3. Checking frontend structure:")
    all_good &= check_directory_exists("frontend/app", "App directory")
    all_good &= check_directory_exists("frontend/components", "Components directory")
    all_good &= check_directory_exists("frontend/context", "Context directory")
    all_good &= check_directory_exists("frontend/pages", "Pages directory")

    all_good &= check_file_exists("frontend/package.json", "Node.js package file")
    all_good &= check_file_exists("frontend/app/page.tsx", "Main page component")
    all_good &= check_file_exists("frontend/app/layout.tsx", "Root layout")
    all_good &= check_file_exists("frontend/app/globals.css", "Global styles")

    # Check key components
    print("\n4. Checking key components:")
    all_good &= check_file_exists("frontend/components/JarvisOrb.tsx", "JarvisOrb component")
    all_good &= check_file_exists("frontend/components/Chat.tsx", "Chat component")
    all_good &= check_file_exists("frontend/components/SystemPanel.tsx", "SystemPanel component")
    all_good &= check_file_exists("frontend/components/Avatar3D.tsx", "Avatar3D component")
    all_good &= check_file_exists("frontend/components/VoiceVisualizer.tsx", "VoiceVisualizer component")

    # Check API routes
    print("\n5. Checking API routes:")
    all_good &= check_file_exists("frontend/pages/api/chat.ts", "Chat API route")
    all_good &= check_file_exists("frontend/pages/api/health.ts", "Health API route")

    # Check Python dependencies (basic)
    print("\n6. Checking Python environment:")
    python_reqs = [
        "fastapi",
        "uvicorn",
        "ollama",
        "chromadb",
        "sentence_transformers",
        "whisper",
        "psutil",
        "pyautogui"
    ]

    for req in python_reqs:
        # Special case for voice packages
        if req == "whisper":
            all_good &= check_python_module("whisper")
        elif req == "sentence_transformers":
            all_good &= check_python_module("sentence_transformers")
        else:
            all_good &= check_python_module(req)

    # Check Node.js
    print("\n7. Checking Node.js environment:")
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[+] Node.js version: {result.stdout.strip()}")
        else:
            print("[-] Node.js not found or not working")
            all_good = False
    except FileNotFoundError:
        print("[-] Node.js not installed")
        all_good = False

    # Summary
    print("\n" + "=" * 50)
    if all_good:
        print("[+] All checks passed! Your JARVIS setup looks good.")
        print("\nNext steps:")
        print("1. Install Python dependencies: pip install -r backend/requirements.txt")
        print("2. Install Node.js dependencies: cd frontend && npm install")
        print("3. Pull required Ollama models: ollama pull llama2 mistral codellama")
        print("4. Copy .env.example to .env and configure as needed")
        print("5. Run: python setup.py or use start.bat/start.sh")
    else:
        print("[-] Some checks failed. Please review the output above.")
        print("You may need to install missing dependencies or fix configuration issues.")

    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())