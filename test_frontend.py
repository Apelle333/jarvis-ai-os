#!/usr/bin/env python3
"""
JARVIS AI Operating System - Frontend Validation
Validates that frontend components are properly installed
"""

import os
import sys
import json
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

def check_file_contains(path, substring, description):
    """Check if a file contains a specific substring"""
    if not os.path.exists(path):
        print(f"[-] {description}: {path} (FILE NOT FOUND)")
        return False

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            if substring in content:
                print(f"[+] {description}: {path} contains '{substring}'")
                return True
            else:
                print(f"[-] {description}: {path} does not contain '{substring}'")
                return False
    except Exception as e:
        print(f"[-] Error reading {path}: {e}")
        return False

def main():
    print("JARVIS AI Operating System - Frontend Validation")
    print("=" * 50)

    all_good = True

    # Change to the script's directory to make paths relative
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Check root directory structure
    print("\n1. Checking directory structure:")
    all_good &= check_directory_exists("frontend", "Frontend directory")
    all_good &= check_directory_exists("frontend/app", "App directory")
    all_good &= check_directory_exists("frontend/components", "Components directory")
    all_good &= check_directory_exists("frontend/context", "Context directory")
    # Next.js App Router uses `frontend/app` instead of `frontend/pages`.
    # Accept either layout: prefer App Router but allow Pages router when present.
    pages_present = check_directory_exists("frontend/pages", "Pages directory")
    app_present = check_directory_exists("frontend/app", "App directory (Next.js App Router)")
    all_good &= (pages_present or app_present)

    # Check key files
    print("\n2. Checking key files:")
    all_good &= check_file_exists("frontend/package.json", "Package.json")
    all_good &= check_file_exists("frontend/tsconfig.json", "TSConfig.json")
    all_good &= check_file_exists("frontend/postcss.config.js", "PostCSS config")
    all_good &= check_file_exists("frontend/tailwind.config.js", "Tailwind config")

    # Check key components
    print("\n3. Checking key React components:")
    all_good &= check_file_exists("frontend/components/JarvisOrb.tsx", "JarvisOrb component")
    all_good &= check_file_exists("frontend/components/Chat.tsx", "Chat component")
    all_good &= check_file_exists("frontend/components/SystemPanel.tsx", "SystemPanel component")
    all_good &= check_file_exists("frontend/components/Avatar3D.tsx", "Avatar3D component")
    all_good &= check_file_exists("frontend/components/VoiceVisualizer.tsx", "VoiceVisualizer component")

    # Check for key content in components
    print("\n4. Checking component content:")
    # JarvisOrb may use the shared `useJarvis` context hook instead of local useState
    jarvisorb_ok = check_file_contains("frontend/components/JarvisOrb.tsx", "useState", "JarvisOrb uses useState")
    if not jarvisorb_ok:
        jarvisorb_ok = check_file_contains("frontend/components/JarvisOrb.tsx", "useJarvis", "JarvisOrb uses useJarvis context hook")
    all_good &= jarvisorb_ok
    all_good &= check_file_contains("frontend/components/Chat.tsx", "sendMessage", "Chat has sendMessage function")
    all_good &= check_file_contains("frontend/components/SystemPanel.tsx", "systemInfo", "SystemPanel uses systemInfo state")
    all_good &= check_file_contains("frontend/components/Avatar3D.tsx", "@react-three/fiber", "Avatar3D uses react-three-fiber")
    all_good &= check_file_contains("frontend/components/VoiceVisualizer.tsx", "useEffect", "VoiceVisualizer uses useEffect")

    # Check pages
    print("\n5. Checking pages:")
    all_good &= check_file_exists("frontend/app/page.tsx", "Main page")
    all_good &= check_file_exists("frontend/app/layout.tsx", "Root layout")
    all_good &= check_file_exists("frontend/app/globals.css", "Global styles")

    # Check API routes
    print("\n6. Checking API routes:")
    # If legacy pages/api exists, validate those routes. Otherwise, ensure components
    # reference backend endpoints (App Router commonly proxies to backend).
    if os.path.isdir("frontend/pages/api"):
        all_good &= check_file_exists("frontend/pages/api/chat.ts", "Chat API endpoint")
        all_good &= check_file_exists("frontend/pages/api/health.ts", "Health API endpoint")
    else:
        # Scan components for expected backend fetch usage as an indicator
        # that API routes are provided by the backend.
        found_chat = False
        for root, dirs, files in os.walk("frontend/components"):
            for f in files:
                if f.endswith('.tsx') or f.endswith('.ts'):
                    p = os.path.join(root, f)
                    try:
                        with open(p, 'r', encoding='utf-8') as fh:
                            c = fh.read()
                            if '/api/chat' in c or '/api/chat/message' in c or '/api/chat/status' in c:
                                found_chat = True
                                break
                    except Exception:
                        continue
            if found_chat:
                break
        if found_chat:
            print(f"[+] Frontend components reference chat API endpoints (backend provided)")
        else:
            print(f"[-] No frontend API routes found and components don't reference chat endpoints")
            all_good = False

    # Check context
    print("\n7. Checking context:")
    all_good &= check_file_exists("frontend/context/JarvisContext.tsx", "Jarvis context")

    # Check package.json content
    print("\n8. Checking package.json:")
    if check_file_exists("frontend/package.json", "Package.json"):
        try:
            with open("frontend/package.json", 'r') as f:
                package_data = json.load(f)
                deps = package_data.get('dependencies', {})
                dev_deps = package_data.get('devDependencies', {})

                required_deps = ['react', 'react-dom', 'next']
                for dep in required_deps:
                    if dep in deps:
                        print(f"[+] Package dependency: {dep} {deps[dep]}")
                    else:
                        print(f"[-] Missing package dependency: {dep}")
                        all_good = False

                required_dev_deps = ['typescript', '@types/react', '@types/node']
                for dep in required_dev_deps:
                    if dep in dev_deps:
                        print(f"[+] Dev dependency: {dep} {dev_deps[dep]}")
                    else:
                        print(f"[-] Missing dev dependency: {dep}")
                        all_good = False
        except Exception as e:
            print(f"[-] Error parsing package.json: {e}")
            all_good = False

    # Summary
    print("\n" + "=" * 50)
    if all_good:
        print("[+] All frontend checks passed!")
        print("\nNext steps for frontend development:")
        print("1. Install Node.js dependencies: cd frontend && npm install")
        print("2. Start development server: npm run dev")
        print("3. Visit http://localhost:3000 to see the application")
        return 0
    else:
        print("[-] Some frontend checks failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())