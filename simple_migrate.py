import os
import sys
import subprocess

def run_command(command):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd='.')
        print(f"Command: {command}")
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception running command: {e}")
        return False

def main():
    print("Simple Migration Script")
    print("=" * 30)
    
    # Commands to run
    commands = [
        "python manage.py makemigrations doctors",
        "python manage.py makemigrations prescriptions", 
        "python manage.py makemigrations chat",
        "python manage.py migrate"
    ]
    
    for cmd in commands:
        print(f"\nRunning: {cmd}")
        success = run_command(cmd)
        if not success:
            print(f"❌ Command failed: {cmd}")
            break
        else:
            print(f"✅ Command succeeded: {cmd}")
    
    print("\nMigration script completed!")

if __name__ == '__main__':
    main()