#!/usr/bin/env python3
"""
JARVIS AI Operating System - Setup Script
Handles initial setup and installation of dependencies
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, cwd=None, check=True):
    """Run a shell command and return the result"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 12):
        print(f"Error: Python 3.12+ required. You have Python {version.major}.{version.minor}")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} is compatible")

def check_node_version():
    """Check if Node.js version is compatible"""
    try:
        result = run_command("node --version", check=False)
        if result.returncode != 0:
            print("Warning: Node.js not found. Frontend development will not be available.")
            return False

        version_str = result.stdout.strip().lstrip('v')
        major = int(version_str.split('.')[0])
        if major < 18:
            print(f"Warning: Node.js 18+ recommended. You have version {version_str}")
        else:
            print(f"✓ Node.js {version_str} is compatible")
        return True
    except Exception as e:
        print(f"Warning: Could not check Node.js version: {e}")
        return False

def setup_backend():
    """Setup backend dependencies"""
    print("\n=== Setting up Backend ===")
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("Error: Backend directory not found")
        return False

    # Create virtual environment
    venv_path = backend_dir / "venv"
    if not venv_path.exists():
        print("Creating Python virtual environment...")
        run_command(f"{sys.executable} -m venv {venv_path}", cwd=backend_dir)

    # Determine pip path
    if platform.system() == "Windows":
        pip_path = venv_path / "Scripts" / "pip"
        python_path = venv_path / "Scripts" / "python"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"

    # Upgrade pip
    print("Upgrading pip...")
    run_command(f"{pip_path} install --upgrade pip", cwd=backend_dir)

    # Install requirements
    requirements_file = backend_dir / "requirements.txt"
    if requirements_file.exists():
        print("Installing backend requirements...")
        run_command(f"{pip_path} install -r {requirements_file}", cwd=backend_dir)
    else:
        print("Warning: requirements.txt not found")

    # Create necessary directories
    dirs_to_create = [
        backend_dir / "database",
        backend_dir / "logs",
        backend_dir / "models"
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(exist_ok=True)
        print(f"Created directory: {dir_path}")

    print("✓ Backend setup completed")
    return True

def setup_frontend():
    """Setup frontend dependencies"""
    print("\n=== Setting up Frontend ===")
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("Error: Frontend directory not found")
        return False

    # Check if npm/yarn is available
    npm_check = run_command("npm --version", check=False)
    if npm_check.returncode != 0:
        print("Error: npm not found. Please install Node.js to setup frontend.")
        return False

    # Install dependencies
    print("Installing frontend dependencies...")
    result = run_command("npm install", cwd=frontend_dir, check=False)
    if result.returncode != 0:
        print("Error: Failed to install frontend dependencies")
        print(result.stdout)
        print(result.stderr)
        return False

    print("✓ Frontend setup completed")
    return True

def create_directories():
    """Create necessary directories"""
    print("\n=== Creating Directories ===")

    directories = [
        "backend/database",
        "backend/logs",
        "backend/models",
        "frontend"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def main():
    """Main setup function"""
    print("=" * 50)
    print("JARVIS AI Operating System - Setup")
    print("=" * 50)

    # Check system requirements
    print("\n=== Checking System Requirements ===")
    check_python_version()
    check_node_version()

    # Create directories
    create_directories()

    # Setup components
    backend_success = setup_backend()
    frontend_success = setup_frontend()

    print("\n" + "=" * 50)
    if backend_success and frontend_success:
        print("Setup completed successfully! 🎉")
        print("\nNext steps:")
        print("1. Backend: cd backend && venv/Scripts/activate (Windows) or source venv/bin/activate (Linux/Mac)")
        print("2. Start backend: python main.py")
        print("3. In another terminal: cd frontend && npm run dev")
        print("4. Visit http://localhost:3000 to access JARVIS is a markdown table
    print("Setup completed with some issues. Please check the output above.")
        print("\nTroubleshooting:")
        print("- Ensure you have Python 3.12+ installed")
        print("- Ensure you have Node.js 18+ installed (for frontend)")
        print("- Check your internet connection for downloading dependencies")
        print("- Make sure you have sufficient disk space")
    print("=" * 50)

if __name__ == "__main__":
    main()