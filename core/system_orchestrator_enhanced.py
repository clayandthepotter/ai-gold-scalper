#!/usr/bin/env python3
"""
AI Gold Scalper Enhanced System Orchestrator
Manages complete infrastructure including all Phase 4 components and backtesting system.

Features:
- Full Phase 4 AI system integration
- Comprehensive backtesting framework management
- Advanced component health monitoring
- Automated dependency resolution
- Intelligent startup and shutdown sequences
- Performance monitoring and alerts
- Model training and deployment automation
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
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor
import requests
import argparse

class EnhancedSystemOrchestrator:
    def __init__(self, interactive_setup=False):
        self.config = {}
        self.processes = {}
        self.deployment_type = None
        self.installation_path = None
        self.running = True
        self.dev_tunnels = {}
        self.security_tokens = {}
        self.network_checks = {}
        self.health_history = {}
        
        # Initialize base path and config file
        self.base_path = Path(r"G:\My Drive\AI_Gold_Scalper")
        self.config_file = self.base_path / "config.json"
        self.log_file = self.base_path / "logs" / "orchestrator_enhanced.log"
        
        # Setup logging
        self.setup_logging()
        
        if interactive_setup:
            self.interactive_setup()
        else:
            self.load_configuration()
        
        # Enhanced component configurations with full Phase 4 integration
        self.components = {
            # Core AI Infrastructure
            'ai_server': {
                'script': 'enhanced_ai_server_consolidated.py',
                'port': 5000,
                'health_endpoint': '/health',
                'dependencies': ['model_registry'],
                'type': 'service',
                'critical': True,
                'restart_policy': 'always',
                'startup_delay': 0
            },
            'performance_dashboard': {
                'script': 'scripts/monitoring/performance_dashboard.py',
                'port': 8080,
                'health_endpoint': '/api/system-status',
                'dependencies': ['ai_server'],
                'type': 'service',
                'critical': True,
                'restart_policy': 'always',
                'startup_delay': 5
            },
            
            # Phase 4 AI System Components
            'model_registry': {
                'script': 'scripts/ai/model_registry.py',
                'type': 'persistent_service',
                'dependencies': [],
                'critical': True,
                'restart_policy': 'always',
                'startup_delay': 0,
                'health_check': 'database_connection'
            },
            'ensemble_system': {
                'script': 'scripts/ai/ensemble_models.py',
                'type': 'on_demand_service',
                'dependencies': ['model_registry'],
                'critical': False,
                'restart_policy': 'on_failure',
                'startup_delay': 10,
                'health_check': 'model_availability'
            },
            'regime_detector': {
                'script': 'scripts/ai/market_regime_detector.py',
                'type': 'continuous_service',
                'dependencies': [],
                'critical': False,
                'restart_policy': 'always',
                'startup_delay': 3,
                'health_check': 'detection_active'
            },
            'phase4_controller': {
                'script': 'scripts/integration/phase4_integration.py',
                'type': 'continuous_service',
                'dependencies': ['ensemble_system', 'regime_detector', 'model_registry'],
                'critical': True,
                'restart_policy': 'always',
                'startup_delay': 15,
                'health_check': 'controller_status'
            },
            'adaptive_learning': {
                'script': 'scripts/ai/adaptive_learning.py',
                'type': 'periodic_service',
                'schedule': 'hourly',
                'dependencies': ['model_registry'],
                'critical': False,
                'restart_policy': 'on_failure',
                'startup_delay': 20,
                'health_check': 'learning_active'
            },
            
            # Analysis & Optimization
            'risk_optimizer': {
                'script': 'scripts/analysis/risk_parameter_optimizer.py',
                'type': 'scheduled_service',
                'schedule': 'daily',
                'dependencies': ['ai_server'],
                'critical': False,
                'restart_policy': 'on_failure',
                'startup_delay': 30,
                'health_check': 'optimization_ready'
            },
            'postmortem_analyzer': {
                'script': 'scripts/monitoring/trade_postmortem_analyzer.py',
                'type': 'event_driven_service',
                'dependencies': ['ai_server'],
                'critical': False,
                'restart_policy': 'on_failure',
                'startup_delay': 25,
                'health_check': 'analyzer_ready'
            },
            'enhanced_trade_logger': {
                'script': 'scripts/monitoring/enhanced_trade_logger.py',
                'type': 'continuous_service',
                'dependencies': ['ai_server'],
                'critical': True,
                'restart_policy': 'always',
                'startup_delay': 8,
                'health_check': 'logging_active'
            },
            
            # Backtesting & Validation
            'backtesting_system': {
                'script': 'scripts/backtesting/comprehensive_backtester.py',
                'type': 'on_demand_service',
                'dependencies': ['phase4_controller'],
                'critical': False,
                'restart_policy': 'manual',
                'startup_delay': 0,
                'health_check': 'backtester_ready'
            },
            'backtesting_integration': {
                'script': 'scripts/integration/backtesting_integration.py',
                'type': 'scheduled_service',
                'schedule': 'weekly',
                'dependencies': ['backtesting_system', 'phase4_controller'],
                'critical': False,
                'restart_policy': 'on_failure',
                'startup_delay': 0,
                'health_check': 'integration_ready'
            },
            
            # Data & Model Management (To be created)
            'data_processor': {
                'script': 'scripts/data/market_data_processor.py',
                'type': 'scheduled_service',
                'schedule': 'hourly',
                'dependencies': [],
                'critical': False,
                'restart_policy': 'on_failure',
                'startup_delay': 0,
                'health_check': 'data_pipeline_active',
                'optional': True  # Component doesn't exist yet
            },
            'model_trainer': {
                'script': 'scripts/training/automated_model_trainer.py',
                'type': 'event_driven_service',
                'dependencies': ['data_processor', 'model_registry'],
                'critical': False,
                'restart_policy': 'manual',
                'startup_delay': 0,
                'health_check': 'trainer_ready',
                'optional': True  # Component doesn't exist yet
            }
        }
        
        self.setup_signal_handlers()
        if not interactive_setup:
            self.log_info("Enhanced System Orchestrator initialized")
            print("Enhanced System Orchestrator initialized with Phase 4 integration")
    
    def setup_logging(self):
        """Setup comprehensive logging system"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(str(self.log_file)),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('EnhancedOrchestrator')
    
    def log_info(self, message: str):
        if hasattr(self, 'logger'):
            self.logger.info(message)
    
    def log_error(self, message: str):
        if hasattr(self, 'logger'):
            self.logger.error(message)
    
    def log_warning(self, message: str):
        if hasattr(self, 'logger'):
            self.logger.warning(message)
    
    def load_configuration(self):
        """Load system configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                self.deployment_type = self.config.get('deployment_type', 'development')
                self.installation_path = self.config.get('installation_path', str(self.base_path))
            except Exception as e:
                self.log_error(f"Error loading configuration: {e}")
                self.config = {}
    
    def save_configuration(self):
        """Save current configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.log_error(f"Error saving configuration: {e}")
    
    def check_component_dependencies(self, component_name: str) -> bool:
        """Check if all dependencies for a component are running"""
        component = self.components.get(component_name, {})
        dependencies = component.get('dependencies', [])
        
        for dep in dependencies:
            if dep not in self.processes:
                self.log_warning(f"Dependency {dep} not running for {component_name}")
                return False
                
            process_info = self.processes[dep]
            if process_info['process'].poll() is not None:
                self.log_warning(f"Dependency {dep} has stopped for {component_name}")
                return False
        
        return True
    
    def get_startup_order(self) -> List[str]:
        """Get components in dependency order for startup"""
        ordered = []
        remaining = set(self.components.keys())
        
        # Remove optional components that don't exist
        for comp_name in list(remaining):
            component = self.components[comp_name]
            if component.get('optional', False):
                script_path = self.base_path / component['script']
                if not script_path.exists():
                    self.log_info(f"Optional component {comp_name} not found, skipping")
                    remaining.remove(comp_name)
        
        while remaining:
            # Find components with no unmet dependencies
            ready = []
            for comp_name in remaining:
                deps = self.components[comp_name].get('dependencies', [])
                if all(dep in ordered or dep not in remaining for dep in deps):
                    ready.append(comp_name)
            
            if not ready:
                # Circular dependency or missing dependency
                self.log_error(f"Circular or missing dependencies detected: {remaining}")
                break
            
            # Sort by startup delay
            ready.sort(key=lambda x: self.components[x].get('startup_delay', 0))
            
            for comp_name in ready:
                ordered.append(comp_name)
                remaining.remove(comp_name)
        
        return ordered
    
    def start_component(self, component_name: str) -> bool:
        """Start a specific component"""
        if component_name in self.processes:
            self.log_warning(f"Component {component_name} is already running")
            return True
        
        component = self.components.get(component_name)
        if not component:
            self.log_error(f"Unknown component: {component_name}")
            return False
        
        script_path = self.base_path / component['script']
        if not script_path.exists():
            if component.get('optional', False):
                self.log_info(f"Optional component {component_name} not found, skipping")
                return True
            else:
                self.log_error(f"Component script not found: {script_path}")
                return False
        
        # Check dependencies
        if not self.check_component_dependencies(component_name):
            self.log_error(f"Dependencies not met for {component_name}")
            return False
        
        self.log_info(f"Starting component: {component_name}")
        
        try:
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(self.base_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[component_name] = {
                'process': process,
                'start_time': datetime.now(),
                'restart_count': 0,
                'component_info': component
            }
            
            # Wait for startup delay
            startup_delay = component.get('startup_delay', 0)
            if startup_delay > 0:
                self.log_info(f"Waiting {startup_delay}s for {component_name} to initialize")
                time.sleep(startup_delay)
            
            # Verify the process started successfully
            if process.poll() is None:
                self.log_info(f"✅ {component_name} started successfully (PID: {process.pid})")
                return True
            else:
                self.log_error(f"❌ {component_name} failed to start")
                del self.processes[component_name]
                return False
                
        except Exception as e:
            self.log_error(f"Error starting {component_name}: {e}")
            return False
    
    def stop_component(self, component_name: str) -> bool:
        """Stop a specific component"""
        if component_name not in self.processes:
            self.log_warning(f"Component {component_name} is not running")
            return True
        
        process_info = self.processes[component_name]
        process = process_info['process']
        
        self.log_info(f"Stopping component: {component_name}")
        
        try:
            # Try graceful shutdown first
            process.terminate()
            
            # Wait up to 10 seconds for graceful shutdown
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if still running
                self.log_warning(f"Force killing {component_name}")
                process.kill()
                process.wait()
            
            del self.processes[component_name]
            self.log_info(f"✅ {component_name} stopped")
            return True
            
        except Exception as e:
            self.log_error(f"Error stopping {component_name}: {e}")
            return False
    
    def check_component_health(self, component_name: str) -> bool:
        """Enhanced health check for components"""
        if component_name not in self.processes:
            return False
        
        process_info = self.processes[component_name]
        process = process_info['process']
        component = process_info['component_info']
        
        # Check if process is still running
        if process.poll() is not None:
            return False
        
        # Check port availability for services
        if 'port' in component:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('localhost', component['port']))
                sock.close()
                if result != 0:
                    return False
            except Exception:
                return False
        
        # Check health endpoint if available
        if 'health_endpoint' in component and 'port' in component:
            try:
                url = f"http://localhost:{component['port']}{component['health_endpoint']}"
                response = requests.get(url, timeout=5)
                if response.status_code != 200:
                    return False
            except Exception:
                return False
        
        return True
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'deployment_type': self.deployment_type,
            'components': {},
            'summary': {
                'total_components': len(self.components),
                'running_components': 0,
                'healthy_components': 0,
                'critical_components_running': 0,
                'total_critical_components': 0
            }
        }
        
        for component_name, component_config in self.components.items():
            # Skip optional components that don't exist
            if component_config.get('optional', False):
                script_path = self.base_path / component_config['script']
                if not script_path.exists():
                    continue
            
            component_status = {
                'type': component_config.get('type', 'unknown'),
                'critical': component_config.get('critical', False),
                'dependencies': component_config.get('dependencies', [])
            }
            
            if component_config.get('critical', False):
                status['summary']['total_critical_components'] += 1
            
            if component_name in self.processes:
                process_info = self.processes[component_name]
                process = process_info['process']
                
                if process.poll() is None:
                    # Process is running
                    status['summary']['running_components'] += 1
                    if component_config.get('critical', False):
                        status['summary']['critical_components_running'] += 1
                    
                    health = self.check_component_health(component_name)
                    if health:
                        status['summary']['healthy_components'] += 1
                    
                    component_status.update({
                        'status': 'healthy' if health else 'unhealthy',
                        'pid': process.pid,
                        'uptime': str(datetime.now() - process_info['start_time']),
                        'restart_count': process_info.get('restart_count', 0),
                        'health_check': health
                    })
                else:
                    # Process has died
                    component_status.update({
                        'status': 'stopped',
                        'exit_code': process.returncode,
                        'restart_count': process_info.get('restart_count', 0)
                    })
            else:
                component_status['status'] = 'not_running'
            
            status['components'][component_name] = component_status
        
        return status
    
    def print_system_status(self):
        """Print formatted system status"""
        status = self.get_system_status()
        
        print("\n" + "="*70)
        print("🚀 AI GOLD SCALPER - ENHANCED SYSTEM STATUS")
        print("="*70)
        
        summary = status['summary']
        
        print(f"📊 System Summary:")
        print(f"   • Deployment: {status['deployment_type']}")
        print(f"   • Running: {summary['running_components']}/{summary['total_components']} components")
        print(f"   • Healthy: {summary['healthy_components']}/{summary['running_components']} running components")
        print(f"   • Critical: {summary['critical_components_running']}/{summary['total_critical_components']} critical components")
        
        print(f"\n🎯 Component Status:")
        
        # Group components by type
        service_components = []
        ai_components = []
        analysis_components = []
        backtesting_components = []
        
        for comp_name, comp_info in status['components'].items():
            comp_type = comp_info.get('type', 'unknown')
            if 'service' in comp_type and comp_name in ['ai_server', 'performance_dashboard']:
                service_components.append((comp_name, comp_info))
            elif comp_name in ['model_registry', 'ensemble_system', 'regime_detector', 'phase4_controller', 'adaptive_learning']:
                ai_components.append((comp_name, comp_info))
            elif comp_name in ['risk_optimizer', 'postmortem_analyzer', 'enhanced_trade_logger']:
                analysis_components.append((comp_name, comp_info))
            elif 'backtesting' in comp_name:
                backtesting_components.append((comp_name, comp_info))
        
        # Display components by category
        categories = [
            ("🔧 Core Services", service_components),
            ("🤖 AI Intelligence", ai_components),
            ("📊 Analysis & Monitoring", analysis_components),
            ("🧪 Backtesting & Validation", backtesting_components)
        ]
        
        for category_name, components in categories:
            if components:
                print(f"\n{category_name}:")
                for comp_name, comp_info in components:
                    status_emoji = {
                        'healthy': '✅',
                        'unhealthy': '⚠️ ',
                        'stopped': '❌',
                        'not_running': '⭕'
                    }.get(comp_info['status'], '❓')
                    
                    critical_indicator = " [CRITICAL]" if comp_info.get('critical', False) else ""
                    print(f"   {status_emoji} {comp_name.upper()}: {comp_info['status']}{critical_indicator}")
                    
                    if 'pid' in comp_info:
                        print(f"      PID: {comp_info['pid']} | Uptime: {comp_info['uptime']} | Restarts: {comp_info.get('restart_count', 0)}")
        
        print("="*70)
    
    def start_all(self) -> bool:
        """Start all components in dependency order"""
        print("\n🚀 Starting AI Gold Scalper Enhanced System...")
        print("   Phase 4 AI Integration + Comprehensive Backtesting")
        
        startup_order = self.get_startup_order()
        
        self.log_info(f"Startup order: {startup_order}")
        print(f"\n📋 Startup sequence: {len(startup_order)} components")
        
        failed_components = []
        
        for i, component_name in enumerate(startup_order, 1):
            component = self.components[component_name]
            
            print(f"\n[{i}/{len(startup_order)}] Starting {component_name}...")
            
            if self.start_component(component_name):
                startup_delay = component.get('startup_delay', 0)
                if startup_delay > 0:
                    print(f"   ⏱️  Waiting {startup_delay}s for initialization...")
                    time.sleep(startup_delay)
            else:
                failed_components.append(component_name)
                if component.get('critical', False):
                    print(f"   ❌ Critical component {component_name} failed to start!")
                    print("   🛑 Aborting startup due to critical component failure")
                    return False
        
        if failed_components:
            print(f"\n⚠️  Failed to start: {', '.join(failed_components)}")
        
        print("\n🎉 System startup completed!")
        self.print_system_status()
        
        # Display access information
        if 'ai_server' in self.processes and 'performance_dashboard' in self.processes:
            print(f"\n🌐 Access Information:")
            print(f"   • AI Server: http://localhost:5000")
            print(f"   • Performance Dashboard: http://localhost:8080")
            print(f"   • System Status: http://localhost:8080/api/system-status")
        
        return len(failed_components) == 0
    
    def stop_all(self):
        """Stop all components in reverse order"""
        print("\n🛑 Stopping all components...")
        
        # Stop in reverse dependency order
        components = list(self.processes.keys())
        components.reverse()
        
        for component_name in components:
            self.stop_component(component_name)
        
        print("✅ All components stopped")
    
    def restart_component(self, component_name: str):
        """Restart a specific component"""
        print(f"🔄 Restarting {component_name}...")
        
        if component_name in self.processes:
            # Increment restart count
            self.processes[component_name]['restart_count'] = self.processes[component_name].get('restart_count', 0) + 1
        
        self.stop_component(component_name)
        time.sleep(2)
        self.start_component(component_name)
    
    def restart_all(self):
        """Restart all components"""
        print("🔄 Restarting all components...")
        self.stop_all()
        time.sleep(5)
        self.start_all()
    
    def monitor_loop(self):
        """Enhanced monitoring loop with intelligent restart policies"""
        print("👁️  Starting enhanced monitoring loop...")
        
        while self.running:
            try:
                failed_components = []
                
                # Check component health
                for component_name in list(self.processes.keys()):
                    if not self.check_component_health(component_name):
                        component = self.processes[component_name]['component_info']
                        restart_policy = component.get('restart_policy', 'manual')
                        
                        self.log_warning(f"Component {component_name} health check failed")
                        
                        if restart_policy == 'always':
                            self.log_info(f"Auto-restarting {component_name} (policy: always)")
                            self.restart_component(component_name)
                        elif restart_policy == 'on_failure':
                            restart_count = self.processes.get(component_name, {}).get('restart_count', 0)
                            if restart_count < 3:  # Max 3 restart attempts
                                self.log_info(f"Auto-restarting {component_name} (policy: on_failure, attempt {restart_count + 1})")
                                self.restart_component(component_name)
                            else:
                                self.log_error(f"Component {component_name} exceeded restart limit")
                                failed_components.append(component_name)
                        else:
                            failed_components.append(component_name)
                
                # Alert on critical component failures
                if failed_components:
                    critical_failed = [c for c in failed_components if self.components[c].get('critical', False)]
                    if critical_failed:
                        self.log_error(f"CRITICAL ALERT: Critical components failed: {critical_failed}")
                        print(f"🚨 CRITICAL ALERT: {critical_failed} components failed!")
                
                # Sleep for monitoring interval
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoring interrupted by user")
                break
            except Exception as e:
                self.log_error(f"Error in monitoring loop: {e}")
                time.sleep(30)
    
    def run_backtesting(self, symbol: str = "XAUUSD", strategy: str = "ai_model"):
        """Run backtesting system"""
        print(f"🧪 Running backtesting for {symbol} with {strategy} strategy...")
        
        try:
            from scripts.integration.backtesting_integration import BacktestingIntegration
            
            integration = BacktestingIntegration()
            results = integration.run_comprehensive_backtest(symbol=symbol)
            
            if 'error' in results:
                print(f"❌ Backtesting failed: {results['error']}")
                return False
            
            print("✅ Backtesting completed successfully!")
            
            # Display results
            backtest_info = results.get('backtest_info', {})
            summary = results.get('summary', {})
            
            print(f"\n📊 Backtest Results:")
            print(f"   • Total Return: {backtest_info.get('total_return_pct', 0):.2f}%")
            print(f"   • Win Rate: {summary.get('win_rate', 0):.1f}%")
            print(f"   • Profit Factor: {summary.get('profit_factor', 0):.2f}")
            print(f"   • Sharpe Ratio: {summary.get('sharpe_ratio', 0):.2f}")
            print(f"   • Total Trades: {summary.get('total_trades', 0)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error running backtesting: {e}")
            return False
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def shutdown(self):
        """Graceful shutdown"""
        self.running = False
        self.stop_all()
        print("🏁 System shutdown complete")

def main():
    parser = argparse.ArgumentParser(description="AI Gold Scalper Enhanced System Orchestrator")
    parser.add_argument('action', choices=[
        'start', 'stop', 'restart', 'status', 'monitor',
        'backtest', 'setup', 'interactive-setup'
    ], help='Action to perform')
    
    parser.add_argument('--component', '-c', help='Specific component to target')
    parser.add_argument('--symbol', '-s', default='XAUUSD', help='Symbol for backtesting')
    parser.add_argument('--strategy', '-st', default='ai_model', help='Strategy for backtesting')
    
    args = parser.parse_args()
    
    # Handle interactive setup
    if args.action == 'interactive-setup':
        orchestrator = EnhancedSystemOrchestrator(interactive_setup=True)
        
        continue_setup = input("\nWould you like to start the system now? (y/N): ").strip().lower()
        if continue_setup in ['y', 'yes']:
            try:
                orchestrator.start_all()
                print("\n🌐 System Access:")
                print("   • AI Server: http://localhost:5000")
                print("   • Dashboard: http://localhost:8080")
                print("\n👁️  Press Ctrl+C to stop monitoring and shut down.")
                orchestrator.monitor_loop()
            except KeyboardInterrupt:
                print("\n🛑 Shutdown requested by user")
            finally:
                orchestrator.shutdown()
    else:
        orchestrator = EnhancedSystemOrchestrator()
        
        if args.action == 'start':
            if args.component:
                orchestrator.start_component(args.component)
            else:
                success = orchestrator.start_all()
                if success:
                    print("\n👁️  Starting monitoring. Press Ctrl+C to stop.")
                    try:
                        orchestrator.monitor_loop()
                    except KeyboardInterrupt:
                        print("\n🛑 Monitoring stopped")
                    finally:
                        orchestrator.shutdown()
        
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
            try:
                orchestrator.monitor_loop()
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped")
        
        elif args.action == 'backtest':
            orchestrator.run_backtesting(args.symbol, args.strategy)

if __name__ == "__main__":
    main()
