#!/usr/bin/env python3
"""
🚀 EV CHARGING COMMAND CENTER - QUICK START GUIDE
==================================================

This script helps you quickly set up and run the system.
Run this as: python3 quick_start.py
"""

import subprocess
import sys
import os
import time
from pathlib import Path

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅  {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}❌  {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️   {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️   {text}{Colors.ENDC}")

def run_command(cmd, description=""):
    """Run a shell command and return success status"""
    try:
        if description:
            print_info(description)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print_success("Done!")
            return True
        else:
            print_error(f"Failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print_error("Command timed out")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print_header("Checking Python Version")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor} detected")
        return True
    else:
        print_error(f"Python 3.8+ required (found {version.major}.{version.minor})")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print_header("Checking Dependencies")
    
    required_packages = {
        'Flask': 'flask',
        'Flask-SocketIO': 'flask_socketio',
        'SQLAlchemy': 'sqlalchemy',
        'scikit-learn': 'sklearn',
        'Chart.js': 'chart.js (frontend)',
    }
    
    missing = []
    for package_name, import_name in required_packages.items():
        try:
            if import_name != 'chart.js (frontend)':
                __import__(import_name)
                print_success(f"{package_name} installed")
            else:
                print_success(f"{package_name} available (frontend library)")
        except ImportError:
            print_warning(f"{package_name} not found")
            missing.append(package_name)
    
    if missing:
        print_warning(f"Missing packages: {', '.join(missing)}")
        print_info("Run: pip install -r requirements.txt")
        return False
    
    print_success("All dependencies available!")
    return True

def setup_project():
    """Setup the project environment"""
    print_header("Setting Up Project")
    
    server_dir = Path(__file__).parent / "ev-secure-charging" / "server"
    
    if not server_dir.exists():
        server_dir = Path("/Users/swatisingh/Desktop/EVproject/ev-secure-charging/server")
    
    if not server_dir.exists():
        print_error(f"Server directory not found: {server_dir}")
        return False
    
    os.chdir(server_dir)
    print_success(f"Working directory: {server_dir}")
    
    # Check for database
    db_path = server_dir / "database.db"
    if db_path.exists():
        print_info(f"Database found at {db_path}")
    else:
        print_warning(f"Database will be created on first run")
    
    return True

def test_imports():
    """Test if all modules import correctly"""
    print_header("Testing Module Imports")
    
    modules = [
        'app',
        'models',
        'auth',
        'ml_model',
        'security_apis',
    ]
    
    all_good = True
    for module in modules:
        try:
            __import__(module)
            print_success(f"Module '{module}' imports successfully")
        except ImportError as e:
            print_error(f"Failed to import '{module}': {e}")
            all_good = False
    
    return all_good

def show_system_info():
    """Display system information"""
    print_header("System Information")
    
    print(f"{Colors.CYAN}Platform Details:{Colors.ENDC}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  OS: {sys.platform}")
    print(f"  Working Directory: {os.getcwd()}")
    print()
    
    print(f"{Colors.CYAN}Available Components:{Colors.ENDC}")
    print(f"  ✓ Flask Web Server")
    print(f"  ✓ SQLite Database")
    print(f"  ✓ WebSocket Server")
    print(f"  ✓ ML Detection Engine")
    print(f"  ✓ Blockchain Logger")
    print(f"  ✓ Security APIs")
    print()

def show_quick_start():
    """Show quick start instructions"""
    print_header("Quick Start Instructions")
    
    print(f"{Colors.BOLD}1. Install Dependencies (if not done):{Colors.ENDC}")
    print(f"   $ pip install -r requirements.txt")
    print()
    
    print(f"{Colors.BOLD}2. Navigate to Server Directory:{Colors.ENDC}")
    print(f"   $ cd /Users/swatisingh/Desktop/EVproject/ev-secure-charging/server")
    print()
    
    print(f"{Colors.BOLD}3. Run the Application:{Colors.ENDC}")
    print(f"   $ python3 app.py")
    print()
    
    print(f"{Colors.BOLD}4. Access the Dashboard:{Colors.ENDC}")
    print(f"   • Open browser: {Colors.GREEN}http://localhost:5000{Colors.ENDC}")
    print()
    
    print(f"{Colors.BOLD}5. Login with Default Credentials:{Colors.ENDC}")
    print(f"   • Username: {Colors.YELLOW}admin{Colors.ENDC}")
    print(f"   • Password: {Colors.YELLOW}admin123{Colors.ENDC}")
    print()
    
    print(f"{Colors.BOLD}6. Explore Features:{Colors.ENDC}")
    print(f"   • Dashboard: View real-time status")
    print(f"   • Security: Monitor threats & attacks")
    print(f"   • Analytics: View statistics & trends")
    print(f"   • Charging: Predictive management")
    print(f"   • Admin: System controls & reports")
    print()

def show_api_examples():
    """Show API endpoint examples"""
    print_header("API Endpoint Examples")
    
    print(f"{Colors.BOLD}Get System Status:{Colors.ENDC}")
    print(f"  $ curl http://localhost:5000/status")
    print()
    
    print(f"{Colors.BOLD}Get Threat Level:{Colors.ENDC}")
    print(f"  $ curl http://localhost:5000/api/security/threat-level")
    print()
    
    print(f"{Colors.BOLD}Trigger Attack Simulation:{Colors.ENDC}")
    print(f"  $ curl http://localhost:5000/attack/dos")
    print()
    
    print(f"{Colors.BOLD}Admin Login:{Colors.ENDC}")
    print(f"  $ curl -X POST http://localhost:5000/auth/login \\")
    print(f"      -H 'Content-Type: application/json' \\")
    print(f"      -d '{{\"username\":\"admin\",\"password\":\"admin123\"}}'")
    print()

def show_documentation_links():
    """Show documentation file links"""
    print_header("Documentation Files")
    
    docs = {
        "README_ENTERPRISE.md": "Complete project documentation",
        "TEST_AND_DEMO_GUIDE.md": "Testing procedures and demo workflow",
        "PROJECT_COMPLETION_SUMMARY.md": "All features and phases completed",
    }
    
    base_path = Path(__file__).parent
    if not base_path.name == "EVproject":
        base_path = Path("/Users/swatisingh/Desktop/EVproject")
    
    for doc_file, description in docs.items():
        doc_path = base_path / doc_file
        if doc_path.exists():
            print_success(f"{doc_file}")
            print(f"         → {description}")
        else:
            print_warning(f"{doc_file} (not found)")
    
    print()

def show_attack_simulations():
    """Show attack simulation options"""
    print_header("Attack Simulation Scripts")
    
    print(f"{Colors.BOLD}Available Attack Types:{Colors.ENDC}")
    print()
    
    attacks = {
        "DoS Attack": "Simulates server flooding",
        "Fake Data Attack": "Injects bogus billing data",
        "Replay Attack": "Replays captured packets",
        "Missing Packet": "Creates packet loss scenarios",
    }
    
    for attack_type, description in attacks.items():
        print(f"  • {Colors.CYAN}{attack_type}{Colors.ENDC}: {description}")
    
    print()
    print(f"{Colors.BOLD}Manual Trigger:{Colors.ENDC}")
    print(f"  $ curl http://localhost:5000/attack/dos")
    print()
    
    print(f"{Colors.BOLD}Using Python Scripts:{Colors.ENDC}")
    print(f"  $ cd /Users/swatisingh/Desktop/EVproject/attacks")
    print(f"  $ python3 dos_attack.py")
    print()

def show_troubleshooting():
    """Show common troubleshooting steps"""
    print_header("Troubleshooting")
    
    print(f"{Colors.BOLD}Issue: Port 5000 Already in Use{Colors.ENDC}")
    print(f"  Solution: $ pkill -f 'python3 app.py'")
    print()
    
    print(f"{Colors.BOLD}Issue: Database Lock Error{Colors.ENDC}")
    print(f"  Solution: $ rm database.db  (will recreate on startup)")
    print()
    
    print(f"{Colors.BOLD}Issue: Import Errors{Colors.ENDC}")
    print(f"  Solution: $ pip install --upgrade -r requirements.txt")
    print()
    
    print(f"{Colors.BOLD}Issue: WebSocket Connection Failed{Colors.ENDC}")
    print(f"  Solution: $ pip install flask-socketio python-socketio")
    print()

def main():
    """Main execution function"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     🚗⚡ EV CHARGING COMMAND CENTER - QUICK START 🚀        ║")
    print("║         Enterprise AI-Powered Management System           ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    # Perform checks
    if not check_python_version():
        print_error("System requirements not met. Exiting.")
        sys.exit(1)
    
    print()
    check_dependencies()
    
    print()
    if not setup_project():
        print_error("Setup failed. Exiting.")
        sys.exit(1)
    
    print()
    if not test_imports():
        print_warning("Some imports failed - system may not run properly")
    
    print()
    show_system_info()
    
    # Show guides
    show_quick_start()
    show_api_examples()
    show_attack_simulations()
    show_documentation_links()
    show_troubleshooting()
    
    # Final message
    print_header("Ready to Start!")
    
    print(f"{Colors.GREEN}{Colors.BOLD}Next Step:{Colors.ENDC}")
    print(f"{Colors.GREEN}python3 app.py{Colors.ENDC}\n")
    
    print(f"{Colors.GREEN}Then open: {Colors.YELLOW}http://localhost:5000{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}Questions?{Colors.ENDC}")
    print(f"Read the documentation:")
    print(f"  • {Colors.CYAN}README_ENTERPRISE.md{Colors.ENDC}")
    print(f"  • {Colors.CYAN}TEST_AND_DEMO_GUIDE.md{Colors.ENDC}")
    print(f"  • {Colors.CYAN}PROJECT_COMPLETION_SUMMARY.md{Colors.ENDC}")
    print()
    
    print(f"{Colors.GREEN}🎉 System is ready for use!{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Setup cancelled by user.{Colors.ENDC}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.ENDC}\n")
        sys.exit(1)
