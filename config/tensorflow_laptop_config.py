#!/usr/bin/env python3
"""
AI Gold Scalper - TensorFlow GPU Configuration for RTX 4050 Laptop
Optimizes TensorFlow for 6GB VRAM and 16GB RAM constraints
"""

import tensorflow as tf
import logging
import os
import psutil


class LaptopGPUConfig:
    """TensorFlow GPU configuration optimized for RTX 4050 laptop"""
    
    def __init__(self):
        self.gpu_memory_limit = 5120  # 5GB (leaving 1GB buffer)
        self.enable_mixed_precision = True
        self.enable_xla = True
        
    def configure_gpu_for_laptop(self):
        """Optimize TensorFlow for RTX 4050 laptop"""
        
        try:
            # Get available GPUs
            gpus = tf.config.experimental.list_physical_devices('GPU')
            
            if not gpus:
                logging.warning("No GPU detected. Running on CPU only.")
                return False
                
            logging.info(f"Found {len(gpus)} GPU(s): {[gpu.name for gpu in gpus]}")
            
            # Configure first GPU (RTX 4050)
            gpu = gpus[0]
            
            # Enable memory growth to prevent VRAM allocation issues
            tf.config.experimental.set_memory_growth(gpu, True)
            
            # Set memory limit to 5GB (leaving 1GB buffer for system)
            tf.config.set_logical_device_configuration(
                gpu,
                [tf.config.LogicalDeviceConfiguration(memory_limit=self.gpu_memory_limit)]
            )
            
            # Enable mixed precision for better performance and memory usage
            if self.enable_mixed_precision:
                tf.keras.mixed_precision.set_global_policy('mixed_float16')
                logging.info("✅ Mixed precision enabled (float16)")
            
            # Enable XLA compilation for faster execution
            if self.enable_xla:
                tf.config.optimizer.set_jit(True)
                logging.info("✅ XLA acceleration enabled")
            
            # Configure threading for AMD Ryzen 5 8654HS (6 cores, 12 threads)
            tf.config.threading.set_inter_op_parallelism_threads(6)
            tf.config.threading.set_intra_op_parallelism_threads(12)
            
            logging.info("✅ GPU configured for laptop optimization")
            logging.info(f"   - Memory limit: {self.gpu_memory_limit}MB")
            logging.info(f"   - Mixed precision: {self.enable_mixed_precision}")
            logging.info(f"   - XLA acceleration: {self.enable_xla}")
            
            return True
            
        except RuntimeError as e:
            logging.error(f"❌ GPU configuration failed: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ Unexpected error during GPU configuration: {e}")
            return False
    
    def get_gpu_info(self):
        """Get GPU information and current usage"""
        try:
            # TensorFlow GPU info
            gpus = tf.config.experimental.list_physical_devices('GPU')
            
            if not gpus:
                return {"error": "No GPU detected"}
            
            gpu_info = {
                "gpu_count": len(gpus),
                "gpu_names": [gpu.name for gpu in gpus],
                "memory_limit_mb": self.gpu_memory_limit,
                "mixed_precision": self.enable_mixed_precision,
                "xla_enabled": self.enable_xla
            }
            
            # Try to get detailed GPU info using nvidia-ml-py if available
            try:
                import pynvml
                pynvml.nvmlInit()
                
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                gpu_info.update({
                    "gpu_name": gpu_name,
                    "total_memory_mb": memory_info.total // 1024 // 1024,
                    "used_memory_mb": memory_info.used // 1024 // 1024,
                    "free_memory_mb": memory_info.free // 1024 // 1024,
                    "memory_utilization": (memory_info.used / memory_info.total) * 100
                })
                
            except ImportError:
                logging.info("pynvml not available. Install with: pip install pynvml")
            except Exception as e:
                logging.warning(f"Could not get detailed GPU info: {e}")
            
            return gpu_info
            
        except Exception as e:
            return {"error": str(e)}
    
    def monitor_gpu_memory(self):
        """Monitor GPU memory usage and provide warnings"""
        try:
            import pynvml
            pynvml.nvmlInit()
            
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            
            used_percentage = (memory_info.used / memory_info.total) * 100
            
            if used_percentage > 90:
                logging.warning(f"⚠️  GPU memory usage high: {used_percentage:.1f}%")
                return "high"
            elif used_percentage > 75:
                logging.info(f"GPU memory usage: {used_percentage:.1f}%")
                return "medium"
            else:
                return "low"
                
        except ImportError:
            return "unknown"
        except Exception:
            return "error"
    
    def optimize_for_model_size(self, model_size="medium"):
        """Adjust configuration based on model size"""
        
        if model_size == "small":
            # For small models, allow more concurrent operations
            self.gpu_memory_limit = 3072  # 3GB
            tf.config.threading.set_inter_op_parallelism_threads(8)
            
        elif model_size == "medium":
            # Default configuration for medium models
            self.gpu_memory_limit = 5120  # 5GB
            tf.config.threading.set_inter_op_parallelism_threads(6)
            
        elif model_size == "large":
            # For large models, use maximum memory
            self.gpu_memory_limit = 5632  # 5.5GB (aggressive)
            tf.config.threading.set_inter_op_parallelism_threads(4)
            
        logging.info(f"GPU configuration optimized for {model_size} models")
        logging.info(f"Memory limit set to: {self.gpu_memory_limit}MB")


def configure_gpu_for_laptop():
    """Main function to configure GPU for laptop"""
    config = LaptopGPUConfig()
    return config.configure_gpu_for_laptop()


def get_gpu_status():
    """Get current GPU status"""
    config = LaptopGPUConfig()
    return config.get_gpu_info()


def test_gpu_configuration():
    """Test GPU configuration with a simple computation"""
    try:
        # Configure GPU
        if not configure_gpu_for_laptop():
            return False
        
        # Test tensor operations
        print("🧪 Testing GPU configuration...")
        
        # Create test tensors
        with tf.device('/GPU:0'):
            a = tf.random.normal([1000, 1000])
            b = tf.random.normal([1000, 1000])
            
            # Matrix multiplication
            start_time = tf.timestamp()
            c = tf.matmul(a, b)
            end_time = tf.timestamp()
            
            computation_time = end_time - start_time
            
        print(f"✅ GPU test completed successfully!")
        print(f"   Matrix multiplication (1000x1000): {computation_time:.3f}s")
        
        # Test mixed precision if enabled
        config = LaptopGPUConfig()
        if config.enable_mixed_precision:
            with tf.device('/GPU:0'):
                a_fp16 = tf.cast(a, tf.float16)
                b_fp16 = tf.cast(b, tf.float16)
                
                start_time = tf.timestamp()
                c_fp16 = tf.matmul(a_fp16, b_fp16)
                end_time = tf.timestamp()
                
                fp16_time = end_time - start_time
                
            print(f"   Mixed precision test: {fp16_time:.3f}s")
            print(f"   Performance improvement: {((computation_time - fp16_time) / computation_time * 100):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ GPU test failed: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🚀 AI Gold Scalper - RTX 4050 GPU Configuration")
    print("=" * 50)
    
    # Configure GPU
    success = configure_gpu_for_laptop()
    
    if success:
        # Get GPU info
        gpu_info = get_gpu_status()
        print(f"\n📊 GPU Information:")
        for key, value in gpu_info.items():
            print(f"   {key}: {value}")
        
        # Test configuration
        print(f"\n🧪 Running GPU tests...")
        test_result = test_gpu_configuration()
        
        if test_result:
            print(f"\n🎉 RTX 4050 configuration completed successfully!")
        else:
            print(f"\n⚠️  Configuration completed but tests failed")
    else:
        print(f"\n❌ GPU configuration failed. Check your CUDA installation.")
