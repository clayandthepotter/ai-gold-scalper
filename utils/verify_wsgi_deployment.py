#!/usr/bin/env python3
"""
WSGI Deployment Verification Script
Verifies that the AI Gold Scalper system is properly configured with Waitress WSGI server
"""

import sys
import os
import time
import requests
import subprocess
import threading
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_header():
    """Print verification header"""
    print("=" * 70)
    print("🚀 AI GOLD SCALPER - WSGI DEPLOYMENT VERIFICATION")
    print("=" * 70)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_dependencies():
    """Check if required dependencies are installed"""
    print("📦 CHECKING DEPENDENCIES...")
    dependencies = {
        'waitress': 'Production WSGI server',
        'flask': 'Web framework',
        'requests': 'HTTP client for testing'
    }
    
    missing = []
    for dep, desc in dependencies.items():
        try:
            __import__(dep)
            print(f"  ✅ {dep:15} - {desc}")
        except ImportError:
            print(f"  ❌ {dep:15} - {desc} (MISSING)")
            missing.append(dep)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("   Install with: pip install " + " ".join(missing))
        return False
    
    print("  🎯 All dependencies satisfied!")
    return True

def check_server_config():
    """Check if server is properly configured for WSGI"""
    print("\n🔧 CHECKING SERVER CONFIGURATION...")
    
    try:
        from core.enhanced_ai_server_consolidated import app, CONFIG
        print("  ✅ AI server module imported successfully")
        print(f"  ✅ Server version: {CONFIG.get('server_version', 'Unknown')}")
        
        # Check if waitress is properly integrated
        server_file = 'core/enhanced_ai_server_consolidated.py'
        if os.path.exists(server_file):
            with open(server_file, 'r') as f:
                content = f.read()
                if 'from waitress import serve' in content:
                    print("  ✅ Waitress WSGI integration detected")
                    if 'serve(app,' in content:
                        print("  ✅ Waitress serve configuration found")
                    else:
                        print("  ⚠️  Waitress import found but serve() call missing")
                else:
                    print("  ❌ Waitress WSGI integration not found")
                    return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Server configuration check failed: {e}")
        return False

def start_server_test():
    """Start the server for testing"""
    print("\n🌐 STARTING SERVER FOR TESTING...")
    
    try:
        # Start server in background
        server_process = subprocess.Popen(
            [sys.executable, 'core/enhanced_ai_server_consolidated.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        print("  ⏳ Waiting for server startup...")
        time.sleep(5)
        
        # Check if process is still running
        if server_process.poll() is not None:
            stdout, stderr = server_process.communicate()
            print(f"  ❌ Server failed to start")
            print(f"     Error: {stderr[:200]}")
            return None
        
        print("  ✅ Server started successfully")
        return server_process
        
    except Exception as e:
        print(f"  ❌ Failed to start server: {e}")
        return None

def test_server_endpoints(port=5000):
    """Test server endpoints"""
    print(f"\n🧪 TESTING SERVER ENDPOINTS (Port {port})...")
    
    base_url = f"http://localhost:{port}"
    test_endpoints = [
        ('/health', 'Health check endpoint'),
        ('/models/status', 'Model status endpoint'),
        ('/performance', 'Performance metrics endpoint')
    ]
    
    results = []
    for endpoint, description in test_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"  ✅ {endpoint:20} - {description}")
                results.append(True)
                
                # Parse response for additional info
                try:
                    data = response.json()
                    if endpoint == '/health' and 'server_version' in data:
                        print(f"     📊 Server Version: {data['server_version']}")
                    if endpoint == '/performance' and 'avg_response_time_ms' in data:
                        print(f"     ⚡ Avg Response: {data['avg_response_time_ms']}ms")
                except:
                    pass
            else:
                print(f"  ⚠️  {endpoint:20} - {description} (HTTP {response.status_code})")
                results.append(False)
                
        except requests.exceptions.ConnectionError:
            print(f"  ❌ {endpoint:20} - {description} (Connection failed)")
            results.append(False)
        except Exception as e:
            print(f"  ❌ {endpoint:20} - {description} (Error: {str(e)[:50]})")
            results.append(False)
    
    return results

def test_ai_signal_endpoint():
    """Test the main AI signal endpoint"""
    print("\n🤖 TESTING AI SIGNAL ENDPOINT...")
    
    try:
        test_data = {
            "test": True,
            "symbol": "XAUUSD",
            "bid": 2000.50
        }
        
        response = requests.post(
            "http://localhost:5000/ai_signal",
            json=test_data,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print("  ✅ AI signal endpoint responding")
            print(f"     📊 Signal: {data.get('signal', 'N/A')}")
            print(f"     📊 Confidence: {data.get('confidence', 'N/A')}%")
            print(f"     📊 Test Mode: {data.get('test_mode', 'N/A')}")
            return True
        else:
            print(f"  ❌ AI signal endpoint failed (HTTP {response.status_code})")
            return False
            
    except Exception as e:
        print(f"  ❌ AI signal test failed: {e}")
        return False

def performance_test():
    """Basic performance test"""
    print("\n⚡ PERFORMANCE TEST...")
    
    try:
        # Test response times
        times = []
        for i in range(5):
            start = time.time()
            response = requests.get("http://localhost:5000/health", timeout=5)
            duration = time.time() - start
            times.append(duration * 1000)  # Convert to ms
            
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"  📊 Average Response Time: {avg_time:.2f}ms")
        print(f"  📊 Min Response Time: {min_time:.2f}ms")
        print(f"  📊 Max Response Time: {max_time:.2f}ms")
        
        if avg_time < 100:
            print("  ✅ Excellent response times!")
        elif avg_time < 500:
            print("  ✅ Good response times")
        else:
            print("  ⚠️  Response times could be improved")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Performance test failed: {e}")
        return False

def print_summary(results):
    """Print verification summary"""
    print("\n" + "=" * 70)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(results)
    
    print(f"📊 Tests Passed: {passed_tests}/{total_tests}")
    print(f"✅ Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! WSGI deployment is ready for production!")
        print("🚀 Your AI Gold Scalper system is properly configured with Waitress WSGI.")
    elif passed_tests >= total_tests * 0.8:
        print("\n✅ MOSTLY SUCCESSFUL! Minor issues detected but system is functional.")
        print("🔧 Review any warnings above for optimization opportunities.")
    else:
        print("\n⚠️  ISSUES DETECTED! Please review the failed tests above.")
        print("🛠️  Some components may need attention before production deployment.")
    
    print(f"\n⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

def main():
    """Main verification function"""
    print_header()
    
    results = []
    server_process = None
    
    try:
        # Check dependencies
        results.append(check_dependencies())
        
        # Check server configuration
        results.append(check_server_config())
        
        # Start server for testing
        server_process = start_server_test()
        if server_process:
            results.append(True)
            
            # Test endpoints
            endpoint_results = test_server_endpoints()
            results.extend(endpoint_results)
            
            # Test AI signal endpoint
            results.append(test_ai_signal_endpoint())
            
            # Performance test
            results.append(performance_test())
        else:
            results.append(False)
        
    except KeyboardInterrupt:
        print("\n⏹️  Verification interrupted by user")
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        results.append(False)
    finally:
        # Clean up server process
        if server_process and server_process.poll() is None:
            print("\n🛑 Stopping test server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
    
    # Print summary
    print_summary(results)
    
    # Exit with appropriate code
    if all(results):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
