#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick API Key Setup Script
Run this to add your Groq API key to the .env file
"""

import os
from pathlib import Path

def setup_groq_api_key():
    """Setup Groq API key in .env file"""
    
    print("=" * 50)
    print("  GROQ API KEY SETUP")
    print("=" * 50)
    print()
    
    # Get the project root directory
    project_root = Path(__file__).parent
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    # Check if .env already exists
    if env_file.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to update it? (y/n): ").lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    # Copy from .env.example if it doesn't exist
    if not env_file.exists() and env_example.exists():
        print("📋 Creating .env file from .env.example...")
        with open(env_example, 'r') as f:
            content = f.read()
        with open(env_file, 'w') as f:
            f.write(content)
        print("✅ .env file created")
    
    # Get API key from user
    print()
    print("Get your free Groq API key from: https://console.groq.com/keys")
    print()
    print("Your API key should start with: gsk_")
    print()
    
    api_key = input("Paste your Groq API key here: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Setup cancelled.")
        return
    
    if not api_key.startswith("gsk_"):
        print("⚠️  Warning: API key doesn't start with 'gsk_'")
        response = input("Continue anyway? (y/n): ").lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    # Update .env file
    print()
    print("💾 Saving API key to .env file...")
    
    try:
        # Read current .env content
        if env_file.exists():
            with open(env_file, 'r') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Update or add GROQ_API_KEY
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('GROQ_API_KEY='):
                lines[i] = f'GROQ_API_KEY={api_key}\n'
                updated = True
                break
        
        if not updated:
            lines.append(f'\nGROQ_API_KEY={api_key}\n')
        
        # Write back to .env
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        print("✅ API key saved successfully!")
        print()
        print("=" * 50)
        print("  SETUP COMPLETE!")
        print("=" * 50)
        print()
        print("Next steps:")
        print("1. Make sure 'groq' package is installed: pip install groq")
        print("2. Run the application: python main.py")
        print("3. Go to the AI Expert tab in the right panel")
        print("4. Click 'Analyze Current Design' to test the AI")
        print()
        print("The AI Expert is now ready to help you optimize your irrigation system!")
        print()
        
    except Exception as e:
        print(f"❌ Error saving API key: {e}")
        return

if __name__ == "__main__":
    setup_groq_api_key()
