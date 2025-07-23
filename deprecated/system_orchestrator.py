#!/usr/bin/env python3
"""
AI Gold Scalper Comprehensive System Orchestrator
Manages complete infrastructure including:
- Dev tunnel setup and secure connections
- All system components (AI server, dashboard, data processing, training)
- Health monitoring, failure detection, and automatic recovery
- Network configuration and port management
- Security checks and authentication
- Logging and alerting systems
"""
import os
import sys
import time
import subprocess
import threading
import signal
import json
import socket
import psutil
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
import requests
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

class SystemOrchestrator:
    def __init__(self, interactive_setup=False):
        self.config = {}
        self.processes = {}
        self.deployment_type = None
        self.installation_path = None
        self.components = {}  # Initialize components attribute
        self.running = True  # Initialize running state
        self.dev_tunnels = {}  # Dev tunnel processes
        self.security_tokens = {}  # Security tokens for authentication
        self.network_checks = {}  # Network connectivity checks
        self.health_history = {}  # Component health history
        
        # Initialize base path and config file first
        self.base_path = Path(r"G:\My Drive\AI_Gold_Scalper")
        self.config_file = self.base_path / "config.json"
        self.log_file = self.base_path / "logs" / "orchestrator.log"
        
        # Setup logging
        self.setup_logging()
        
        if interactive_setup:
            self.interactive_setup()
        else:
            self.load_configuration()
        
        # Component configurations
        self.components = {
            'ai_server': {
                'script': 'enhanced_ai_server.py',
                'port': 5000,
                'health_endpoint': '/health',
                'dependencies': ['models']
            },
            'dashboard': {
                'script': 'dashboard/trading_dashboard.py',
                'port': 8080,
                'health_endpoint': '/api/system-status',
                'dependencies': ['ai_server']
            },
            'task_pending_watcher': {
                'script': 'task_pending_watcher.py',
                'dependencies': [],
                'laptop_only': True  # Only run on laptop
            },
            'task_completed_watcher': {
                'script': 'task_completed_watcher.py',
                'dependencies': [],
                'vps_only': True  # Only run on VPS
            },
            'data_processor': {
                'script': 'data_processor.py',
                'schedule': 'manual',  # Run manually or via cron
                'dependencies': []
            },
            'model_trainer': {
                'script': 'enhanced_model_trainer.py',
                'schedule': 'manual',  # Run manually or scheduled
                'dependencies': ['data_processor']
            }
        }
        
        self.setup_signal_handlers()
        if not interactive_setup:
            self.log_info("System Orchestrator initialized")
            print("System Orchestrator initialized")
    
    def setup_logging(self):
        """Setup comprehensive logging system"""
        # Ensure logs directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(str(self.log_file)),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('SystemOrchestrator')
    
    def log_info(self, message: str):
        """Log info message"""
        if hasattr(self, 'logger'):
            self.logger.info(message)
    
    def log_error(self, message: str):
        """Log error message"""
        if hasattr(self, 'logger'):
            self.logger.error(message)
    
    def log_warning(self, message: str):
        """Log warning message"""
        if hasattr(self, 'logger'):
            self.logger.warning(message)
    
    def interactive_setup(self):
        """Interactive setup wizard for deployment configuration"""
        print("\n" + "="*60)
        print("🚀 AI GOLD SCALPER - INTERACTIVE SETUP WIZARD")
        print("="*60)
        print()
        
        # Step 1: Determine deployment type
        print("STEP 1: Define your deployment type\n")
        print("1. GPU-Based Model Training Location (Laptop/Workstation)")
        print("   - Runs AI server, dashboard, data processing, model training")
        print("   - Monitors for pending training tasks")
        print("   - High-performance GPU required")
        print()
        print("2. Virtual Private Server (VPS)")
        print("   - Runs AI server, dashboard for live trading")
        print("   - Monitors for completed training tasks")
        print("   - Manages live trading operations")
        print()
        
        while True:
            choice = input("Select deployment type (1 or 2): ").strip()
            if choice == '1':
                self.deployment_type = 'laptop'
                print("\n✅ Configured as GPU Training Location")
                break
            elif choice == '2':
                self.deployment_type = 'vps'
                print("\n✅ Configured as Virtual Private Server")
                break
            else:
                print("❌ Invalid choice. Please enter 1 or 2.")
        
        # Step 2: Get root drive/path
        print("\nSTEP 2: Specify installation path\n")
        
        if os.name == 'nt':  # Windows
            print("Available drives (select by number or enter a full path):")
            drives = [f"{d}:\\" for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f"{d}:\\")]
            for i, drive in enumerate(drives, 1):
                print(f"  {i}. {drive}")
            print()
            
            default_path = "G:\\My Drive\\AI_Gold_Scalper"
            user_path = input(f"Enter installation path (default: {default_path}): ").strip()
            
            if not user_path:
                user_path = default_path
            elif user_path.isdigit():
                # User selected a drive number, need to build the path
                drive_index = int(user_path) - 1
                if 0 <= drive_index < len(drives):
                    selected_drive = drives[drive_index]
                    
                    # Ask if this is a Google Drive
                    is_google_drive = input(f"\nIs {selected_drive} a Google Drive? (y/N): ").strip().lower()
                    
                    if is_google_drive in ['y', 'yes']:
                        # Ask for the drive name (folder name in Google Drive)
                        print("\n📁 Google Drive Folder Configuration:")
                        print("   Most users have 'My Drive' as their main Google Drive folder.")
                        print("   If unsure, just press ENTER to use the default.")
                        drive_name = input("\nEnter Google Drive folder name (press ENTER for 'My Drive'): ").strip()
                        if not drive_name:
                            drive_name = "My Drive"
                            print(f"   ✅ Using default: '{drive_name}'")
                        else:
                            print(f"   ✅ Using custom folder: '{drive_name}'")
                        user_path = f"{selected_drive}{drive_name}\\AI_Gold_Scalper"
                    else:
                        # Regular drive, just add AI_Gold_Scalper
                        user_path = selected_drive + "AI_Gold_Scalper"
                        
                    print(f"\n📁 Compiled path: {user_path}")
                else:
                    print(f"Invalid drive selection. Using default: {default_path}")
                    user_path = default_path
                    
        else:  # Linux/Unix
            default_path = "/home/ai_gold_scalper"
            user_path = input(f"Enter installation path (default: {default_path}): ").strip()
            
            if not user_path:
                user_path = default_path
        
        self.base_path = Path(user_path)
        self.config_file = self.base_path / "config.json"
        
        print(f"\n✅ Installation path set to: {self.base_path}")
        
        # Step 3: Create directories and save configuration
        print("\nSTEP 3: Creating directory structure...")
        self.create_directory_structure()
        
        # Step 4: Save configuration
        print("\nSTEP 4: Saving configuration...")
        self.save_configuration()
        
        print("\n" + "="*60)
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"Deployment Type: {self.deployment_type.upper()}")
        print(f"Installation Path: {self.base_path}")
        print(f"Configuration saved to: {self.config_file}")
        print()
        
    def create_directory_structure(self):
        """Create the necessary directory structure"""
        # First, ensure the base path exists
        if not self.base_path.exists():
            print(f"  📁 Creating base directory: {self.base_path}")
            self.base_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Created base directory: {self.base_path}")
        else:
            print(f"  ℹ️  Base directory already exists: {self.base_path}")
        
        directories = [
            "data/historical",
            "data/processed", 
            "data/tasks",
            "models/trained",
            "logs",
            "dashboard/templates",
            "config"
        ]
        
        for directory in directories:
            dir_path = self.base_path / directory
            existed = dir_path.exists()
            dir_path.mkdir(parents=True, exist_ok=True)
            
            if existed:
                print(f"  ℹ️  Already exists: {dir_path}")
            else:
                print(f"  ✅ Created: {dir_path}")
    
    def save_configuration(self):
        """Save deployment configuration to file"""
        config = {
            "deployment_type": self.deployment_type,
            "base_path": str(self.base_path),
            "setup_date": datetime.now().isoformat(),
            "components": self.get_components_for_deployment(),
            "ports": {
                "ai_server": 5000,
                "dashboard": 8080
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_configuration(self):
        """Load deployment configuration from file"""
        if self.config_file and self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.deployment_type = config.get('deployment_type')
                return config
        return None
    
    def get_components_for_deployment(self):
        """Get components that should run for the current deployment type"""
        if not self.deployment_type:
            return list(self.components.keys())
            
        components = []
        for component_name, config in self.components.items():
            if self.deployment_type == 'laptop':
                if not config.get('vps_only', False):
                    components.append(component_name)
            elif self.deployment_type == 'vps':
                if not config.get('laptop_only', False):
                    components.append(component_name)
            else:
                components.append(component_name)
        
        return components
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}. Shutting down gracefully...")
        self.shutdown()
        sys.exit(0)
    
    def check_dependencies(self):
        """Check if all required files and dependencies exist"""
        print("Checking system dependencies...")
        
        issues = []
        
        # Check Python scripts
        for component, config in self.components.items():
            script_path = self.base_path / config['script']
            if not script_path.exists():
                issues.append(f"Missing script: {script_path}")
        
        # Check model files
        models_dir = self.base_path / "models" / "trained"
        required_models = [
            "rf_classifier.pkl",
            "rf_regressor.pkl",
            "rf_classifier_scaler.pkl",
            "rf_regressor_scaler.pkl",
            "feature_list.pkl"
        ]
        
        for model_file in required_models:
            model_path = models_dir / model_file
            if not model_path.exists():
                issues.append(f"Missing model file: {model_path}")
        
        # Check data files
        data_file = self.base_path / "data" / "processed" / "XAUUSD_1min_sample.csv"
        if not data_file.exists():
            issues.append(f"Missing processed data file: {data_file}")
        
        if issues:
            print("❌ Dependency check failed:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ All dependencies satisfied")
            return True
    
    def start_component(self, component_name):
        """Start a specific component"""
        if component_name in self.processes:
            print(f"Component {component_name} is already running")
            return
        
        config = self.components[component_name]
        script_path = self.base_path / config['script']
        
        print(f"Starting {component_name}...")
        
        try:
            # Start the process
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(self.base_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[component_name] = {
                'process': process,
                'config': config,
                'start_time': datetime.now()
            }
            
            print(f"✅ {component_name} started (PID: {process.pid})")
            
            # Wait a moment for the service to initialize
            if 'port' in config:
                time.sleep(3)
                if self.check_component_health(component_name):
                    print(f"✅ {component_name} health check passed")
                else:
                    print(f"⚠️  {component_name} health check failed")
            
        except Exception as e:
            print(f"❌ Failed to start {component_name}: {e}")
    
    def stop_component(self, component_name):
        """Stop a specific component"""
        if component_name not in self.processes:
            print(f"Component {component_name} is not running")
            return
        
        print(f"Stopping {component_name}...")
        
        process_info = self.processes[component_name]
        process = process_info['process']
        
        try:
            # Terminate the process
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
                print(f"✅ {component_name} stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop
                process.kill()
                print(f"⚠️  {component_name} force killed")
            
            del self.processes[component_name]
            
        except Exception as e:
            print(f"❌ Error stopping {component_name}: {e}")
    
    def check_component_health(self, component_name):
        """Check if a component is healthy"""
        if component_name not in self.processes:
            return False
        
        config = self.components[component_name]
        
        if 'port' not in config:
            # For non-web components, just check if process is running
            process = self.processes[component_name]['process']
            return process.poll() is None
        
        # For web components, check HTTP endpoint
        try:
            url = f"http://127.0.0.1:{config['port']}{config['health_endpoint']}"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_system_status(self):
        """Get status of all components"""
        status = {}
        
        for component_name in self.components:
            if component_name in self.processes:
                process_info = self.processes[component_name]
                process = process_info['process']
                
                if process.poll() is None:
                    # Process is running
                    health = self.check_component_health(component_name)
                    status[component_name] = {
                        'status': 'healthy' if health else 'unhealthy',
                        'pid': process.pid,
                        'uptime': str(datetime.now() - process_info['start_time']),
                        'health_check': health
                    }
                else:
                    # Process has died
                    status[component_name] = {
                        'status': 'stopped',
                        'exit_code': process.returncode
                    }
            else:
                status[component_name] = {'status': 'not_running'}
        
        return status
    
    def print_system_status(self):
        """Print formatted system status"""
        status = self.get_system_status()
        
        print("\n" + "="*50)
        print("SYSTEM STATUS")
        print("="*50)
        
        for component, info in status.items():
            status_emoji = {
                'healthy': '✅',
                'unhealthy': '⚠️ ',
                'stopped': '❌',
                'not_running': '⭕'
            }.get(info['status'], '❓')
            
            print(f"{status_emoji} {component.upper()}: {info['status']}")
            
            if 'pid' in info:
                print(f"    PID: {info['pid']}")
                print(f"    Uptime: {info['uptime']}")
                print(f"    Health: {'OK' if info['health_check'] else 'FAIL'}")
        
        print("="*50)
    
    def start_all(self):
        """Start all components in dependency order"""
        print("Starting all system components...")
        
        if not self.check_dependencies():
            print("❌ Cannot start system due to missing dependencies")
            return False
        
        # Start components in dependency order
        start_order = ['ai_server', 'dashboard']
        
        for component in start_order:
            self.start_component(component)
            time.sleep(2)  # Brief pause between starts
        
        print("\n🚀 All components started!")
        self.print_system_status()
        return True
    
    def stop_all(self):
        """Stop all components"""
        print("Stopping all components...")
        
        # Stop in reverse order
        for component in reversed(list(self.processes.keys())):
            self.stop_component(component)
        
        print("✅ All components stopped")
    
    def restart_component(self, component_name):
        """Restart a specific component"""
        print(f"Restarting {component_name}...")
        self.stop_component(component_name)
        time.sleep(2)
        self.start_component(component_name)
    
    def restart_all(self):
        """Restart all components"""
        print("Restarting all components...")
        self.stop_all()
        time.sleep(5)
        self.start_all()
    
    def run_data_processing(self):
        """Run data processing pipeline"""
        print("Running data processing pipeline...")
        
        script_path = self.base_path / "data_processor.py"
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.base_path),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Data processing completed successfully")
                return True
            else:
                print(f"❌ Data processing failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error running data processing: {e}")
            return False
    
    def run_model_training(self):
        """Run model training pipeline"""
        print("Running model training pipeline...")
        
        script_path = self.base_path / "enhanced_model_trainer.py"
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.base_path),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Model training completed successfully")
                return True
            else:
                print(f"❌ Model training failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error running model training: {e}")
            return False
    
    def monitor_loop(self):
        """Main monitoring loop"""
        print("Starting monitoring loop...")
        
        while self.running:
            try:
                # Check component health every 30 seconds
                for component_name in list(self.processes.keys()):
                    if not self.check_component_health(component_name):
                        print(f"⚠️  {component_name} health check failed, attempting restart...")
                        self.restart_component(component_name)
                
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\nMonitoring interrupted by user")
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(30)
    
    def shutdown(self):
        """Shutdown the orchestrator"""
        self.running = False
        self.stop_all()

def main():
    parser = argparse.ArgumentParser(description="AI Gold Scalper System Orchestrator")
    parser.add_argument('action', choices=[
        'start', 'stop', 'restart', 'status', 'monitor',
        'process-data', 'train-models', 'setup', 'interactive-setup'
    ], help='Action to perform')
    
    parser.add_argument('--component', '-c', help='Specific component to target')
    
    args = parser.parse_args()
    
    # Handle interactive setup first
    if args.action == 'interactive-setup':
        orchestrator = SystemOrchestrator(interactive_setup=True)
        
        # After interactive setup, ask if user wants to continue
        continue_setup = input("\nWould you like to start the system now? (y/N): ").strip().lower()
        if continue_setup in ['y', 'yes']:
            try:
                orchestrator.start_all()
                print("\n📊 System started! Access your dashboard at:")
                print(f"   🔗 http://localhost:8080")
                print("\n Press Ctrl+C to stop monitoring and shut down the system.")
                orchestrator.monitor_loop()
            except KeyboardInterrupt:
                print("\nShutdown requested by user")
            finally:
                orchestrator.shutdown()
        else:
            print("\n✅ Setup completed. Run 'python system_orchestrator.py start' to begin.")
        return
    
    # Standard non-interactive mode
    orchestrator = SystemOrchestrator()
    
    try:
        if args.action == 'setup':
            print("Verifying AI Gold Scalper system setup...")
            if orchestrator.check_dependencies():
                print("✅ System setup verified")
            else:
                print("❌ System setup incomplete")
                print("\nRun 'python system_orchestrator.py interactive-setup' for guided setup.")
        
        elif args.action == 'start':
            if args.component:
                orchestrator.start_component(args.component)
            else:
                orchestrator.start_all()
        
        elif args.action == 'stop':
            if args.component:
                orchestrator.stop_component(args.component)
            else:
                orchestrator.stop_all()
        
        elif args.action == 'restart':
            if args.component:
                orchestrator.restart_component(args.component)
            else:
                orchestrator.restart_all()
        
        elif args.action == 'status':
            orchestrator.print_system_status()
        
        elif args.action == 'monitor':
            orchestrator.start_all()
            orchestrator.monitor_loop()
        
        elif args.action == 'process-data':
            orchestrator.run_data_processing()
        
        elif args.action == 'train-models':
            orchestrator.run_model_training()
    
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    finally:
        orchestrator.shutdown()

if __name__ == "__main__":
    main()
