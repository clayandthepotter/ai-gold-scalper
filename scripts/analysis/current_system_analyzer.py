#!/usr/bin/env python3
"""
AI Gold Scalper - Current System Analyzer
Phase 1: System Analysis & Baseline

This script analyzes the current system capabilities and establishes baseline performance metrics.
It examines the consolidated AI server configuration, model loading, and current trading logic.

Version: 1.0.0
Created: 2025-01-22
"""

import os
import sys
import json
import logging
import importlib.util
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scripts/analysis/system_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemAnalyzer:
    """Comprehensive system analysis for the AI Gold Scalper"""
    
    def __init__(self):
        self.analysis_results = {}
        self.recommendations = []
        self.baseline_metrics = {}
        
    def analyze_current_system(self) -> Dict:
        """Main analysis function"""
        logger.info("Starting comprehensive system analysis...")
        
        # 1. Analyze server code
        self.analyze_server_code()
        
        # 2. Analyze configuration
        self.analyze_configuration()
        
        # 3. Analyze directory structure
        self.analyze_directory_structure()
        
        # 4. Check model dependencies
        self.check_model_dependencies()
        
        # 5. Assess trading logic
        self.assess_trading_logic()
        
        # 6. Generate recommendations
        self.generate_recommendations()
        
        # 7. Create baseline metrics
        self.establish_baseline_metrics()
        
        return self.create_analysis_report()
    
    def analyze_server_code(self):
        """Analyze the consolidated AI server code"""
        logger.info("Analyzing server code structure...")
        
        server_path = "enhanced_ai_server_consolidated.py"
        if not os.path.exists(server_path):
            self.analysis_results['server_code'] = {
                'status': 'ERROR',
                'error': 'Server file not found'
            }
            return
        
        try:
            with open(server_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Code analysis metrics
            analysis = {
                'file_size_kb': len(code) / 1024,
                'total_lines': len(code.split('\n')),
                'classes_identified': [],
                'key_features': [],
                'performance_monitoring': False,
                'signal_fusion': False,
                'ml_integration': False,
                'gpt4_integration': False
            }
            
            # Identify key components
            if 'class PerformanceMonitor' in code:
                analysis['classes_identified'].append('PerformanceMonitor')
                analysis['performance_monitoring'] = True
                analysis['key_features'].append('Performance monitoring with P95/P99 metrics')
            
            if 'class SignalFusionEngine' in code:
                analysis['classes_identified'].append('SignalFusionEngine')
                analysis['signal_fusion'] = True
                analysis['key_features'].append('Multi-signal fusion engine')
            
            if 'class ModelInferenceEngine' in code:
                analysis['classes_identified'].append('ModelInferenceEngine')
                analysis['ml_integration'] = True
                analysis['key_features'].append('ML model inference engine')
            
            if 'openai.ChatCompletion.create' in code:
                analysis['gpt4_integration'] = True
                analysis['key_features'].append('GPT-4 market analysis')
            
            if 'class TechnicalAnalysisEngine' in code:
                analysis['classes_identified'].append('TechnicalAnalysisEngine')
                analysis['key_features'].append('Advanced technical analysis')
            
            if 'class DevTunnelClient' in code:
                analysis['classes_identified'].append('DevTunnelClient')
                analysis['key_features'].append('Dev tunnel for model updates')
            
            # Check for logging capabilities
            logging_features = []
            if 'log_request' in code:
                logging_features.append('Request logging')
            if 'log_signal_accuracy' in code:
                logging_features.append('Signal accuracy tracking')
            if 'log_model_update' in code:
                logging_features.append('Model update logging')
            
            analysis['current_logging'] = logging_features
            analysis['status'] = 'SUCCESS'
            
            self.analysis_results['server_code'] = analysis
            
        except Exception as e:
            self.analysis_results['server_code'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def analyze_configuration(self):
        """Analyze configuration files and settings"""
        logger.info("Analyzing configuration...")
        
        config_analysis = {
            'config_files_found': [],
            'config_status': {},
            'missing_configs': []
        }
        
        # Check for config files
        config_paths = [
            'config.json',
            'shared/config/settings.json',
            'vps_components/config/settings.json'
        ]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                config_analysis['config_files_found'].append(config_path)
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    config_analysis['config_status'][config_path] = {
                        'status': 'VALID',
                        'keys': list(config_data.keys()) if isinstance(config_data, dict) else 'Not a dict',
                        'size_kb': os.path.getsize(config_path) / 1024
                    }
                    
                    # Check for key configuration items
                    if isinstance(config_data, dict):
                        if 'openai_api_key' not in config_data:
                            config_analysis['missing_configs'].append('OpenAI API Key')
                        if 'trading_parameters' not in config_data:
                            config_analysis['missing_configs'].append('Trading Parameters')
                        if 'risk_management' not in config_data:
                            config_analysis['missing_configs'].append('Risk Management Settings')
                    
                except Exception as e:
                    config_analysis['config_status'][config_path] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
        
        self.analysis_results['configuration'] = config_analysis
    
    def analyze_directory_structure(self):
        """Analyze the project directory structure"""
        logger.info("Analyzing directory structure...")
        
        structure_analysis = {
            'root_files': [],
            'directories': {},
            'total_files': 0,
            'organization_score': 0
        }
        
        # Get root level files
        for item in os.listdir('.'):
            if os.path.isfile(item):
                structure_analysis['root_files'].append(item)
                structure_analysis['total_files'] += 1
            elif os.path.isdir(item) and not item.startswith('.'):
                # Analyze directory contents
                try:
                    dir_files = []
                    for root, dirs, files in os.walk(item):
                        dir_files.extend(files)
                        structure_analysis['total_files'] += len(files)
                    
                    structure_analysis['directories'][item] = {
                        'file_count': len(dir_files),
                        'subdirectories': [d for d in os.listdir(item) if os.path.isdir(os.path.join(item, d))]
                    }
                except Exception as e:
                    structure_analysis['directories'][item] = {'error': str(e)}
        
        # Calculate organization score (higher is better)
        org_score = 0
        if 'vps_components' in structure_analysis['directories']:
            org_score += 25
        if 'shared' in structure_analysis['directories']:
            org_score += 25
        if 'scripts' in structure_analysis['directories']:
            org_score += 25
        if len(structure_analysis['root_files']) < 20:  # Clean root directory
            org_score += 25
        
        structure_analysis['organization_score'] = org_score
        self.analysis_results['directory_structure'] = structure_analysis
    
    def check_model_dependencies(self):
        """Check ML model files and dependencies"""
        logger.info("Checking model dependencies...")
        
        model_analysis = {
            'model_directories': [],
            'model_files': [],
            'required_packages': [],
            'missing_dependencies': []
        }
        
        # Check for model directories
        model_dirs = ['models', 'shared/models', 'vps_components/models']
        for model_dir in model_dirs:
            if os.path.exists(model_dir):
                model_analysis['model_directories'].append(model_dir)
                
                # List model files
                for root, dirs, files in os.walk(model_dir):
                    for file in files:
                        if file.endswith(('.pkl', '.joblib', '.h5', '.pt', '.pth')):
                            model_analysis['model_files'].append(os.path.join(root, file))
        
        # Check required packages (basic ML stack)
        required_packages = [
            'numpy', 'pandas', 'scikit-learn', 'joblib', 
            'torch', 'flask', 'openai', 'aiohttp'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                model_analysis['required_packages'].append(f"{package}: AVAILABLE")
            except ImportError:
                model_analysis['missing_dependencies'].append(package)
                model_analysis['required_packages'].append(f"{package}: MISSING")
        
        self.analysis_results['model_dependencies'] = model_analysis
    
    def assess_trading_logic(self):
        """Assess current trading logic and signal generation"""
        logger.info("Assessing trading logic...")
        
        trading_assessment = {
            'signal_sources': [],
            'risk_management': {},
            'signal_fusion_capability': False,
            'performance_tracking': False,
            'current_limitations': []
        }
        
        # Check server code for trading logic components
        server_path = "enhanced_ai_server_consolidated.py"
        if os.path.exists(server_path):
            with open(server_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Identify signal sources
            if 'calculate_technical_signal' in code:
                trading_assessment['signal_sources'].append('Technical Analysis')
            if 'calculate_ml_signal' in code:
                trading_assessment['signal_sources'].append('ML Models')
            if 'calculate_gpt4_signal' in code:
                trading_assessment['signal_sources'].append('GPT-4 Analysis')
            
            # Check signal fusion
            if 'SignalFusionEngine' in code and 'fuse_signals' in code:
                trading_assessment['signal_fusion_capability'] = True
            
            # Check performance tracking
            if 'PerformanceMonitor' in code and 'log_signal_accuracy' in code:
                trading_assessment['performance_tracking'] = True
            
            # Check risk management features
            risk_features = []
            if '_calculate_lot_size' in code:
                risk_features.append('Dynamic lot sizing')
            if '_calculate_risk_parameters' in code:
                risk_features.append('Dynamic SL/TP calculation')
            if 'confidence_threshold' in code:
                risk_features.append('Confidence-based filtering')
            
            trading_assessment['risk_management'] = {
                'features': risk_features,
                'confidence_threshold_exists': 'confidence_threshold' in code
            }
            
            # Identify limitations
            limitations = []
            if not trading_assessment['signal_fusion_capability']:
                limitations.append('No signal fusion capability')
            if not trading_assessment['performance_tracking']:
                limitations.append('Limited performance tracking')
            if len(trading_assessment['signal_sources']) < 2:
                limitations.append('Single signal source dependency')
            
            trading_assessment['current_limitations'] = limitations
        
        self.analysis_results['trading_logic'] = trading_assessment
    
    def generate_recommendations(self):
        """Generate actionable recommendations based on analysis"""
        logger.info("Generating recommendations...")
        
        recommendations = []
        
        # Server code recommendations
        server_analysis = self.analysis_results.get('server_code', {})
        if server_analysis.get('status') == 'SUCCESS':
            if not server_analysis.get('performance_monitoring'):
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Performance',
                    'action': 'Implement comprehensive performance monitoring',
                    'description': 'Add detailed trade logging and performance metrics tracking'
                })
            
            current_logging = server_analysis.get('current_logging', [])
            if 'Signal accuracy tracking' not in current_logging:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Logging',
                    'action': 'Enhance signal accuracy tracking',
                    'description': 'Implement detailed signal prediction vs actual outcome logging'
                })
        
        # Configuration recommendations
        config_analysis = self.analysis_results.get('configuration', {})
        missing_configs = config_analysis.get('missing_configs', [])
        if missing_configs:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Configuration',
                'action': 'Complete configuration setup',
                'description': f'Add missing configurations: {", ".join(missing_configs)}'
            })
        
        # Model dependencies recommendations
        model_analysis = self.analysis_results.get('model_dependencies', {})
        if model_analysis.get('missing_dependencies'):
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Dependencies',
                'action': 'Install missing ML dependencies',
                'description': f'Missing packages: {", ".join(model_analysis["missing_dependencies"])}'
            })
        
        # Trading logic recommendations
        trading_analysis = self.analysis_results.get('trading_logic', {})
        limitations = trading_analysis.get('current_limitations', [])
        for limitation in limitations:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Trading Logic',
                'action': f'Address: {limitation}',
                'description': 'Enhance trading system capabilities'
            })
        
        self.recommendations = recommendations
    
    def establish_baseline_metrics(self):
        """Establish baseline performance metrics"""
        logger.info("Establishing baseline metrics...")
        
        baseline = {
            'analysis_date': datetime.now().isoformat(),
            'system_version': '5.0.0-consolidated',
            'code_complexity': {
                'total_lines': self.analysis_results.get('server_code', {}).get('total_lines', 0),
                'classes_count': len(self.analysis_results.get('server_code', {}).get('classes_identified', [])),
                'file_size_kb': self.analysis_results.get('server_code', {}).get('file_size_kb', 0)
            },
            'feature_coverage': {
                'signal_sources': len(self.analysis_results.get('trading_logic', {}).get('signal_sources', [])),
                'has_signal_fusion': self.analysis_results.get('trading_logic', {}).get('signal_fusion_capability', False),
                'has_performance_tracking': self.analysis_results.get('trading_logic', {}).get('performance_tracking', False)
            },
            'organization_score': self.analysis_results.get('directory_structure', {}).get('organization_score', 0),
            'total_files': self.analysis_results.get('directory_structure', {}).get('total_files', 0),
            'recommendations_count': len(self.recommendations)
        }
        
        self.baseline_metrics = baseline
    
    def create_analysis_report(self) -> Dict:
        """Create comprehensive analysis report"""
        logger.info("Creating analysis report...")
        
        return {
            'analysis_metadata': {
                'timestamp': datetime.now().isoformat(),
                'analyzer_version': '1.0.0',
                'analysis_type': 'baseline_system_assessment'
            },
            'system_analysis': self.analysis_results,
            'recommendations': self.recommendations,
            'baseline_metrics': self.baseline_metrics,
            'summary': {
                'overall_health': self._calculate_overall_health(),
                'critical_issues': self._identify_critical_issues(),
                'next_steps': self._suggest_next_steps()
            }
        }
    
    def _calculate_overall_health(self) -> str:
        """Calculate overall system health score"""
        health_score = 0
        max_score = 100
        
        # Server code health (25 points)
        if self.analysis_results.get('server_code', {}).get('status') == 'SUCCESS':
            health_score += 15
            if self.analysis_results['server_code'].get('performance_monitoring'):
                health_score += 5
            if len(self.analysis_results['server_code'].get('classes_identified', [])) >= 5:
                health_score += 5
        
        # Configuration health (25 points)
        config_analysis = self.analysis_results.get('configuration', {})
        if config_analysis.get('config_files_found'):
            health_score += 15
            if not config_analysis.get('missing_configs'):
                health_score += 10
        
        # Dependencies health (25 points)
        model_analysis = self.analysis_results.get('model_dependencies', {})
        if not model_analysis.get('missing_dependencies'):
            health_score += 20
        if model_analysis.get('model_files'):
            health_score += 5
        
        # Organization health (25 points)
        org_score = self.analysis_results.get('directory_structure', {}).get('organization_score', 0)
        health_score += min(25, org_score)
        
        if health_score >= 80:
            return f"EXCELLENT ({health_score}/100)"
        elif health_score >= 60:
            return f"GOOD ({health_score}/100)"
        elif health_score >= 40:
            return f"FAIR ({health_score}/100)"
        else:
            return f"NEEDS_IMPROVEMENT ({health_score}/100)"
    
    def _identify_critical_issues(self) -> List[str]:
        """Identify critical issues that need immediate attention"""
        critical_issues = []
        
        # Check for high-priority recommendations
        for rec in self.recommendations:
            if rec['priority'] == 'HIGH':
                critical_issues.append(rec['action'])
        
        return critical_issues
    
    def _suggest_next_steps(self) -> List[str]:
        """Suggest immediate next steps"""
        next_steps = [
            "Review the analysis report and prioritize recommendations",
            "Address critical issues first (HIGH priority items)",
            "Implement enhanced logging system for better performance tracking",
            "Set up baseline performance monitoring",
            "Create testing framework for signal accuracy validation"
        ]
        
        return next_steps

def main():
    """Run the system analysis"""
    print("="*60)
    print("AI GOLD SCALPER - SYSTEM ANALYSIS (Phase 1)")
    print("="*60)
    print()
    
    analyzer = SystemAnalyzer()
    report = analyzer.analyze_current_system()
    
    # Save detailed report
    report_path = 'scripts/analysis/system_analysis_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"📄 Detailed report saved to: {report_path}")
    print()
    
    # Print summary
    print("📊 ANALYSIS SUMMARY")
    print("-" * 40)
    print(f"Overall Health: {report['summary']['overall_health']}")
    print(f"Total Recommendations: {len(report['recommendations'])}")
    print()
    
    # Print critical issues
    critical_issues = report['summary']['critical_issues']
    if critical_issues:
        print("🚨 CRITICAL ISSUES (Immediate Attention Required):")
        for i, issue in enumerate(critical_issues, 1):
            print(f"  {i}. {issue}")
        print()
    
    # Print high-priority recommendations
    high_priority_recs = [r for r in report['recommendations'] if r['priority'] == 'HIGH']
    if high_priority_recs:
        print("⚡ HIGH PRIORITY RECOMMENDATIONS:")
        for i, rec in enumerate(high_priority_recs, 1):
            print(f"  {i}. [{rec['category']}] {rec['action']}")
            print(f"     → {rec['description']}")
        print()
    
    # Print next steps
    print("🎯 NEXT STEPS:")
    for i, step in enumerate(report['summary']['next_steps'], 1):
        print(f"  {i}. {step}")
    
    print()
    print("="*60)
    print("Analysis complete! Ready to move to implementation phase.")
    print("="*60)

if __name__ == "__main__":
    main()
