#!/usr/bin/env python3
"""
AI Image Finder - Simple Test Script
Quick test to verify everything works
"""

import os
import sys
import subprocess

def test_system():
    """Quick test of the AI Image Finder system"""
    print("🧪 AI Image Finder - Quick Test")
    print("=" * 40)
    
    # Test 1: Python version
    print(f"🐍 Python: {sys.version_info.major}.{sys.version_info.minor} ", end="")
    if sys.version_info >= (3, 8):
        print("✅")
    else:
        print("❌ (Need 3.8+)")
        return False
    
    # Test 2: Check if main file exists
    main_file = "ai_image_finder.py"
    print(f"📄 Main file: ", end="")
    if os.path.exists(main_file):
        print("✅")
    else:
        print("❌ Missing ai_image_finder.py")
        return False
    
    # Test 3: Try importing key components
    print("📦 Checking packages...")
    packages = [
        ("PyQt5", "PyQt5"),
        ("sentence_transformers", "sentence-transformers"),
        ("faiss", "faiss-cpu"),
        ("PIL", "Pillow"),
        ("numpy", "numpy"),
        ("torch", "torch")
    ]
    
    missing = []
    for import_name, pip_name in packages:
        try:
            if import_name == "faiss":
                import faiss
            elif import_name == "PIL":
                from PIL import Image
            else:
                __import__(import_name)
            print(f"   ✅ {import_name}")
        except ImportError:
            print(f"   ❌ {import_name}")
            missing.append(pip_name)
    
    if missing:
        print(f"\n⚠️ Missing packages will be auto-installed: {', '.join(missing)}")
    
    # Test 4: Check for existing index
    print("\n💾 Index files:")
    if os.path.exists("data/faiss_index.bin"):
        index_size = os.path.getsize("data/faiss_index.bin") / 1024 / 1024
        print(f"   ✅ Search index exists ({index_size:.1f} MB)")
    else:
        print("   ℹ️  No index (will need to create one)")
    
    print("\n" + "=" * 40)
    print("🎯 System Check Complete!")
    print("🚀 Ready to launch AI Image Finder")
    
    return True

def launch_application():
    """Launch the main application"""
    try:
        print("\n🚀 Starting AI Image Finder...")
        subprocess.run([sys.executable, "ai_image_finder.py"])
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Launch failed: {e}")

if __name__ == "__main__":
    if test_system():
        choice = input("\n🚀 Launch AI Image Finder? (y/n): ").strip().lower()
        if choice == 'y':
            launch_application()
    else:
        print("❌ System check failed!")
        sys.exit(1)
