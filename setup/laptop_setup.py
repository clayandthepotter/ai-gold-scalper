#!/usr/bin/env python3
"""
AI Gold Scalper - Complete Laptop Setup Script
Optimized for RTX 4050 + AMD Ryzen 5 8654HS + 16GB RAM

This script configures your laptop for optimal AI trading performance.
"""

import subprocess
import sys
import os
import json
import logging
import time
from pathlib import Path
import psutil
import platform

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/laptop_setup.log'),
        logging.StreamHandler()
    ]
)

class LaptopSetup:
    """Complete laptop setup for AI Gold Scalper system"""
    
    def __init__(self):
        self.setup_log = []
        self.errors = []
        
        # System specs
        self.cpu_cores = psutil.cpu_count(logical=False)
        self.cpu_threads = psutil.cpu_count(logical=True)
        self.total_ram_gb = round(psutil.virtual_memory().total / (1024**3))
        
        print("🚀 AI Gold Scalper - Laptop Setup")
        print("=" * 50)
        print(f"💻 System Detected:")
        print(f"   CPU Cores: {self.cpu_cores}")
        print(f"   CPU Threads: {self.cpu_threads}")
        print(f"   Total RAM: {self.total_ram_gb}GB")
        print(f"   OS: {platform.system()} {platform.release()}")
        print()
    
    def log_step(self, message, status="info"):
        """Log setup step with timestamp"""
        if status == "success":
            print(f"✅ {message}")
            logging.info(f"SUCCESS: {message}")
        elif status == "error":
            print(f"❌ {message}")
            logging.error(f"ERROR: {message}")
            self.errors.append(message)
        elif status == "warning":
            print(f"⚠️ {message}")
            logging.warning(f"WARNING: {message}")
        else:
            print(f"ℹ️ {message}")
            logging.info(f"INFO: {message}")
        
        self.setup_log.append({
            "timestamp": time.time(),
            "message": message,
            "status": status
        })
    
    def check_prerequisites(self):
        """Check system prerequisites"""
        self.log_step("Checking system prerequisites...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 8:
            self.log_step(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} - OK", "success")
        else:
            self.log_step(f"Python version {python_version.major}.{python_version.minor} not supported. Need Python 3.8+", "error")
            return False
        
        # Check available disk space
        disk_usage = psutil.disk_usage('.')
        free_gb = disk_usage.free / (1024**3)
        if free_gb > 10:
            self.log_step(f"Available disk space: {free_gb:.1f}GB - OK", "success")
        else:
            self.log_step(f"Low disk space: {free_gb:.1f}GB. Need at least 10GB", "warning")
        
        # Check RAM
        if self.total_ram_gb >= 16:
            self.log_step(f"RAM: {self.total_ram_gb}GB - Perfect for AI trading", "success")
        elif self.total_ram_gb >= 8:
            self.log_step(f"RAM: {self.total_ram_gb}GB - Will work but may need optimization", "warning")
        else:
            self.log_step(f"RAM: {self.total_ram_gb}GB - May not be sufficient", "error")
        
        return True
    
    def create_directories(self):
        """Create necessary directories"""
        self.log_step("Creating directory structure...")
        
        directories = [
            "data", "logs", "models", "config/laptop",
            "backups", "temp", "cache"
        ]
        
        for directory in directories:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
                self.log_step(f"Created directory: {directory}", "success")
            except Exception as e:
                self.log_step(f"Failed to create directory {directory}: {e}", "error")
    
    def check_cuda_installation(self):
        """Check CUDA installation"""
        self.log_step("Checking CUDA installation...")
        
        try:
            # Check nvidia-smi
            result = subprocess.run(['nvidia-smi'], 
                                   capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log_step("NVIDIA drivers detected", "success")
                
                # Extract CUDA version from nvidia-smi output
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if 'CUDA Version:' in line:
                        cuda_version = line.split('CUDA Version:')[1].strip().split()[0]
                        self.log_step(f"CUDA Version: {cuda_version}", "success")
                        break
                
                return True
            else:
                self.log_step("nvidia-smi failed. NVIDIA drivers may not be installed", "error")
                return False
                
        except FileNotFoundError:
            self.log_step("nvidia-smi not found. Install NVIDIA drivers first", "error")
            return False
        except subprocess.TimeoutExpired:
            self.log_step("nvidia-smi timeout. GPU may be unavailable", "error")
            return False
        except Exception as e:
            self.log_step(f"Error checking CUDA: {e}", "error")
            return False
    
    def install_python_packages(self):
        """Install required Python packages"""
        self.log_step("Installing Python packages...")
        
        # Core packages
        packages = [
            "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118",
            "tensorflow[and-cuda]==2.13.0",
            "pynvml",  # For GPU monitoring
            "psutil",  # For system monitoring
        ]
        
        for package in packages:
            try:
                self.log_step(f"Installing: {package}")
                result = subprocess.run([sys.executable, '-m', 'pip', 'install'] + package.split(), 
                                       capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    self.log_step(f"Installed: {package}", "success")
                else:
                    self.log_step(f"Failed to install {package}: {result.stderr}", "error")
                    
            except subprocess.TimeoutExpired:
                self.log_step(f"Timeout installing {package}", "error")
            except Exception as e:
                self.log_step(f"Error installing {package}: {e}", "error")
        
        # Install from requirements.txt
        try:
            if Path("requirements.txt").exists():
                self.log_step("Installing packages from requirements.txt...")
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                                       capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    self.log_step("Requirements.txt packages installed", "success")
                else:
                    self.log_step(f"Some packages failed to install: {result.stderr}", "warning")
            else:
                self.log_step("requirements.txt not found", "warning")
                
        except Exception as e:
            self.log_step(f"Error installing requirements: {e}", "error")
    
    def configure_tensorflow_gpu(self):
        """Configure TensorFlow for RTX 4050"""
        self.log_step("Configuring TensorFlow GPU...")
        
        try:
            # Import and configure TensorFlow
            sys.path.append('config')
            from tensorflow_laptop_config import configure_gpu_for_laptop, test_gpu_configuration
            
            # Configure GPU
            if configure_gpu_for_laptop():
                self.log_step("TensorFlow GPU configuration successful", "success")
                
                # Test GPU
                if test_gpu_configuration():
                    self.log_step("GPU performance test passed", "success")
                else:
                    self.log_step("GPU test failed but configuration succeeded", "warning")
                    
                return True
            else:
                self.log_step("TensorFlow GPU configuration failed", "error")
                return False
                
        except ImportError as e:
            self.log_step(f"Could not import TensorFlow config: {e}", "error")
            return False
        except Exception as e:
            self.log_step(f"Error configuring TensorFlow: {e}", "error")
            return False
    
    def initialize_databases(self):
        """Initialize system databases"""
        self.log_step("Initializing databases...")
        
        try:
            # Import database schema module
            sys.path.append('core')
            from database_schemas import initialize_system_databases
            
            if initialize_system_databases():
                self.log_step("Database initialization successful", "success")
                return True
            else:
                self.log_step("Database initialization failed", "error")
                return False
                
        except ImportError as e:
            self.log_step(f"Could not import database module: {e}", "error")
            return False
        except Exception as e:
            self.log_step(f"Error initializing databases: {e}", "error")
            return False
    
    def optimize_windows_settings(self):
        """Optimize Windows settings for AI trading"""
        self.log_step("Optimizing Windows settings...")
        
        try:
            # Set high performance power plan
            power_cmd = [
                'powercfg', '-setactive', 
                '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'  # High Performance GUID
            ]
            
            result = subprocess.run(power_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                self.log_step("Set high performance power plan", "success")
            else:
                self.log_step("Could not set power plan (may need admin rights)", "warning")
            
            # Try to set GPU to performance mode
            try:
                gpu_cmd = ['nvidia-smi', '-pm', '1']
                result = subprocess.run(gpu_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_step("GPU persistence mode enabled", "success")
            except:
                self.log_step("Could not enable GPU persistence mode", "warning")
            
        except Exception as e:
            self.log_step(f"Error optimizing Windows settings: {e}", "warning")
    
    def create_laptop_config(self):
        """Create laptop-specific configuration"""
        self.log_step("Creating laptop configuration...")
        
        laptop_config = {
            "hardware": {
                "gpu": "RTX 4050",
                "gpu_memory_gb": 6,
                "cpu": "AMD Ryzen 5 8654HS",
                "cpu_cores": self.cpu_cores,
                "cpu_threads": self.cpu_threads,
                "ram_gb": self.total_ram_gb
            },
            "tensorflow": {
                "gpu_memory_limit_mb": 5120,
                "mixed_precision": True,
                "xla_acceleration": True,
                "inter_op_threads": 6,
                "intra_op_threads": 12
            },
            "trading": {
                "max_concurrent_models": 3,
                "max_concurrent_requests": 2,
                "ai_request_timeout_ms": 10000,
                "memory_conservation": True
            },
            "schedule": {
                "model_training": "22:00",  # 10 PM
                "system_backup": "02:00",   # 2 AM
                "system_cleanup": "03:00"   # 3 AM
            }
        }
        
        try:
            config_path = Path("config/laptop/laptop_config.json")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(laptop_config, f, indent=2)
            
            self.log_step(f"Laptop configuration saved to {config_path}", "success")
            return True
            
        except Exception as e:
            self.log_step(f"Error creating laptop config: {e}", "error")
            return False
    
    def test_system_integration(self):
        """Test complete system integration"""
        self.log_step("Testing system integration...")
        
        tests = {
            "tensorflow_gpu": self._test_tensorflow,
            "database_connection": self._test_database,
            "memory_usage": self._test_memory,
            "system_performance": self._test_performance
        }
        
        results = {}
        for test_name, test_func in tests.items():
            try:
                results[test_name] = test_func()
                status = "success" if results[test_name] else "error"
                self.log_step(f"Test {test_name}: {'PASSED' if results[test_name] else 'FAILED'}", status)
            except Exception as e:
                results[test_name] = False
                self.log_step(f"Test {test_name} crashed: {e}", "error")
        
        # Overall result
        passed_tests = sum(results.values())
        total_tests = len(results)
        
        if passed_tests == total_tests:
            self.log_step(f"All {total_tests} integration tests passed!", "success")
            return True
        elif passed_tests > total_tests / 2:
            self.log_step(f"{passed_tests}/{total_tests} tests passed. System mostly functional", "warning")
            return True
        else:
            self.log_step(f"Only {passed_tests}/{total_tests} tests passed. System may have issues", "error")
            return False
    
    def _test_tensorflow(self):
        """Test TensorFlow GPU functionality"""
        try:
            import tensorflow as tf
            
            # Check GPU availability
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if not gpus:
                return False
            
            # Test computation
            with tf.device('/GPU:0'):
                a = tf.random.normal([100, 100])
                b = tf.random.normal([100, 100])
                c = tf.matmul(a, b)
                
            return True
        except:
            return False
    
    def _test_database(self):
        """Test database connectivity"""
        try:
            import sqlite3
            
            # Test connection to trades database
            db_path = Path("data/trades.db")
            if not db_path.exists():
                return False
                
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
            return len(tables) > 0
        except:
            return False
    
    def _test_memory(self):
        """Test memory usage"""
        try:
            memory = psutil.virtual_memory()
            # System should have at least 4GB free
            return memory.available > 4 * 1024**3
        except:
            return False
    
    def _test_performance(self):
        """Test system performance"""
        try:
            import time
            
            # CPU test
            start_time = time.time()
            result = sum(i**2 for i in range(100000))
            cpu_time = time.time() - start_time
            
            # Memory test
            test_data = [i for i in range(1000000)]
            memory_test = len(test_data) == 1000000
            
            return cpu_time < 1.0 and memory_test
        except:
            return False
    
    def generate_setup_report(self):
        """Generate setup completion report"""
        self.log_step("Generating setup report...")
        
        report = {
            "setup_timestamp": time.time(),
            "system_info": {
                "cpu_cores": self.cpu_cores,
                "cpu_threads": self.cpu_threads,
                "ram_gb": self.total_ram_gb,
                "os": f"{platform.system()} {platform.release()}"
            },
            "setup_log": self.setup_log,
            "errors": self.errors,
            "success": len(self.errors) == 0
        }
        
        try:
            report_path = Path("logs/laptop_setup_report.json")
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.log_step(f"Setup report saved to {report_path}", "success")
            
            # Print summary
            print("\n" + "="*50)
            print("🎉 SETUP SUMMARY")
            print("="*50)
            print(f"✅ Steps completed: {len(self.setup_log)}")
            print(f"❌ Errors encountered: {len(self.errors)}")
            
            if len(self.errors) == 0:
                print("🏆 Setup completed successfully!")
                print("🚀 Your RTX 4050 laptop is ready for AI trading!")
            else:
                print("⚠️  Setup completed with some issues:")
                for error in self.errors[-3:]:  # Show last 3 errors
                    print(f"   • {error}")
            
            return report
            
        except Exception as e:
            self.log_step(f"Error generating report: {e}", "error")
            return None
    
    def run_complete_setup(self):
        """Run the complete laptop setup process"""
        print("🚀 Starting complete laptop setup for AI Gold Scalper...")
        print("This may take several minutes...\n")
        
        setup_steps = [
            ("Prerequisites Check", self.check_prerequisites),
            ("Directory Creation", self.create_directories),
            ("CUDA Installation Check", self.check_cuda_installation),
            ("Python Packages Installation", self.install_python_packages),
            ("TensorFlow GPU Configuration", self.configure_tensorflow_gpu),
            ("Database Initialization", self.initialize_databases),
            ("Windows Optimization", self.optimize_windows_settings),
            ("Laptop Configuration", self.create_laptop_config),
            ("System Integration Test", self.test_system_integration)
        ]
        
        for step_name, step_func in setup_steps:
            print(f"\n📋 {step_name}")
            print("-" * 40)
            
            try:
                success = step_func()
                if not success and step_name in ["Prerequisites Check", "Database Initialization"]:
                    self.log_step(f"Critical step failed: {step_name}", "error")
                    print(f"\n❌ Setup aborted due to critical failure in: {step_name}")
                    return False
            except Exception as e:
                self.log_step(f"Step crashed: {step_name} - {e}", "error")
                if step_name in ["Prerequisites Check", "Database Initialization"]:
                    print(f"\n❌ Setup aborted due to critical crash in: {step_name}")
                    return False
        
        # Generate final report
        report = self.generate_setup_report()
        return report is not None and len(self.errors) < 3  # Allow up to 2 minor errors


def main():
    """Main setup function"""
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Create and run setup
    setup = LaptopSetup()
    success = setup.run_complete_setup()
    
    if success:
        print("\n🎉 Laptop setup completed successfully!")
        print("📋 Next steps:")
        print("   1. Test the system with: python utils/test_enhanced_market_data.py") 
        print("   2. Start the AI server: python core/enhanced_ai_server_consolidated.py")
        print("   3. Launch MetaTrader 5 and load the EA")
        print("   4. Monitor system performance in the dashboard")
        return 0
    else:
        print("\n❌ Setup completed with significant issues.")
        print("📋 Check the logs for details and resolve issues before proceeding.")
        return 1


if __name__ == "__main__":
    exit(main())
