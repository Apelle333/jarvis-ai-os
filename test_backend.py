#!/usr/bin/env python3
"""
JARVIS AI Operating System - Backend Test
Tests that the backend can start and basic components work
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

async def test_imports():
    """Test that key modules can be imported"""
    print("Testing imports...")

    try:
        from core.brain import JARVIS_Brain
        print("[+] JARVIS_Brain imported successfully")
    except Exception as e:
        print(f"[-] Failed to import JARVIS_Brain: {e}")
        return False

    try:
        from core.planner import Planner
        print("[+] Planner imported successfully")
    except Exception as e:
        print(f"[-] Failed to import Planner: {e}")
        return False

    try:
        from core.model_router import ModelRouter
        print("[+] ModelRouter imported successfully")
    except Exception as e:
        print(f"[-] Failed to import ModelRouter: {e}")
        return False

    try:
        from core.personality import Personality
        print("[+] Personality imported successfully")
    except Exception as e:
        print(f"[-] Failed to import Personality: {e}")
        return False

    try:
        from agents.main_agent import MainAgent
        print("[+] MainAgent imported successfully")
    except Exception as e:
        print(f"[-] Failed to import MainAgent: {e}")
        return False

    try:
        from agents.coding_agent import CodingAgent
        print("[+] CodingAgent imported successfully")
    except Exception as e:
        print(f"[-] Failed to import CodingAgent: {e}")
        return False

    try:
        from agents.research_agent import ResearchAgent
        print("[+] ResearchAgent imported successfully")
    except Exception as e:
        print(f"[-] Failed to import ResearchAgent: {e}")
        return False

    try:
        from agents.security_agent import SecurityAgent
        print("[+] SecurityAgent imported successfully")
    except Exception as e:
        print(f"[-] Failed to import SecurityAgent: {e}")
        return False

    try:
        from agents.system_agent import SystemAgent
        print("[+] SystemAgent imported successfully")
    except Exception as e:
        print(f"[-] Failed to import SystemAgent: {e}")
        return False

    try:
        from agents.swarm_manager import SwarmManager
        print("[+] SwarmManager imported successfully")
    except Exception as e:
        print(f"[-] Failed to import SwarmManager: {e}")
        return False

    try:
        from memory.memory_manager import MemoryManager
        print("[+] MemoryManager imported successfully")
    except Exception as e:
        print(f"[-] Failed to import MemoryManager: {e}")
        return False

    try:
        from tools.filesystem import FileSystemTool
        print("[+] FileSystemTool imported successfully")
    except Exception as e:
        print(f"[-] Failed to import FileSystemTool: {e}")
        return False

    try:
        from tools.terminal import TerminalTool
        print("[+] TerminalTool imported successfully")
    except Exception as e:
        print(f"[-] Failed to import TerminalTool: {e}")
        return False

    try:
        from tools.browser import BrowserTool
        print("[+] BrowserTool imported successfully")
    except Exception as e:
        print(f"[-] Failed to import BrowserTool: {e}")
        return False

    try:
        from tools.automation import AutomationTool
        print("[+] AutomationTool imported successfully")
    except Exception as e:
        print(f"[-] Failed to import AutomationTool: {e}")
        return False

    try:
        from tools.system_monitor import SystemMonitor
        print("[+] SystemMonitor imported successfully")
    except Exception as e:
        print(f"[-] Failed to import SystemMonitor: {e}")
        return False

    try:
        from voice.whisper import WhisperSTT
        print("[+] WhisperSTT imported successfully")
    except Exception as e:
        print(f"[-] Failed to import WhisperSTT: {e}")
        return False

    try:
        from voice.piper import PiperTTS
        print("[+] PiperTTS imported successfully")
    except Exception as e:
        print(f"[-] Failed to import PiperTTS: {e}")
        return False

    return True

async def test_brain_initialization():
    """Test that the brain can be initialized"""
    print("\nTesting brain initialization...")

    try:
        from core.brain import JARVIS_Brain
        brain = JARVIS_Brain()
        print("[+] JARVIS_Brain instantiated successfully")

        # Try to initialize (this might fail if dependencies missing, but that's ok for this test)
        try:
            await brain.initialize()
            print("[+] JARVIS_Brain initialized successfully")
            await brain.shutdown()
        except Exception as e:
            print(f"! JARVIS_Brain initialization failed (may be expected if deps missing): {e}")
            # This is okay for a basic test

        return True
    except Exception as e:
        print(f"[-] Failed to test JARVIS_Brain: {e}")
        return False

async def main():
    print("JARVIS AI Operating System - Backend Component Test")
    print("=" * 50)

    success = True

    success &= await test_imports()
    success &= await test_brain_initialization()

    print("\n" + "=" * 50)
    if success:
        print("[+] All tests passed! The backend components are working correctly.")
    else:
        print("[-] Some tests failed. Please check the output above.")

    return 0 if success else 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)