# Installation Guide - AI Gold Scalper

## 📋 Overview

This comprehensive installation guide will walk you through setting up the AI Gold Scalper system on your local machine or VPS. Whether you're a beginner or experienced user, this guide provides step-by-step instructions for a successful installation.

## 🎯 System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, Linux (Ubuntu 18.04+), macOS 10.15+
- **Python**: 3.8 or higher (3.9+ recommended)
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 5GB free space (10GB recommended)
- **Internet**: Stable broadband connection

### Recommended Requirements
- **Operating System**: Windows 11 or Ubuntu 20.04 LTS
- **Python**: 3.11 (latest stable)
- **RAM**: 16GB for full development suite
- **Storage**: 20GB+ for historical data and models
- **CPU**: Multi-core processor (4+ cores recommended)
- **Internet**: High-speed connection for real-time data

### Additional Software
- **MetaTrader 5**: For live trading (free download from MetaQuotes)
- **Git** (optional): For version control and updates
- **Text Editor/IDE**: VS Code, PyCharm, or similar (optional)

## 🚀 Installation Methods

Choose the installation method that best fits your needs:

### Method 1: Quick Installation (Recommended for Beginners)
**Time Required**: 15-30 minutes  
**Best For**: Users who want to get started quickly

### Method 2: Development Installation  
**Time Required**: 45-60 minutes  
**Best For**: Developers and advanced users

### Method 3: VPS Production Installation
**Time Required**: 30-45 minutes  
**Best For**: Production trading environments

---

## 📦 Method 1: Quick Installation

### Step 1: Download and Extract

1. **Download the AI Gold Scalper system**
   ```bash
   # If using Git
   git clone https://github.com/your-repo/AI_Gold_Scalper.git
   cd AI_Gold_Scalper
   
   # Or extract from ZIP file to desired location
   ```

2. **Navigate to the installation directory**
   ```bash
   cd "G:\My Drive\AI_Gold_Scalper"
   ```

### Step 2: Python Environment Setup

#### Option A: Using System Python (Simplest)
```bash
# Check Python version
python --version

# Should show Python 3.8+ 
# If not installed, download from: https://www.python.org/downloads/
```

#### Option B: Using Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv ai_gold_scalper_env

# Activate virtual environment
# Windows:
ai_gold_scalper_env\Scripts\activate
# Linux/macOS:
source ai_gold_scalper_env/bin/activate

# Verify activation (should show virtual env path)
which python
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install core requirements
pip install -r requirements.txt

# This will install approximately 30+ packages including:
# - flask (web framework)
# - pandas (data analysis)
# - numpy (numerical computing)
# - scikit-learn (machine learning)
# - plotly (visualization)
# - requests (HTTP client)
# - And many more...
```

### Step 4: Initial Configuration

```bash
# Run the interactive setup wizard
python core/system_orchestrator_enhanced.py interactive-setup
```

The setup wizard will guide you through:
- Deployment type selection
- OpenAI API key configuration (optional)
- AI signal weight settings
- Component selection
- Server configuration

### Step 5: Verification

```bash
# Test the installation
python core/system_orchestrator_enhanced.py status

# Should show system components and their status
```

### Step 6: First Launch

```bash
# Start the system
python core/system_orchestrator_enhanced.py start

# Open browser and verify:
# - AI Server: http://localhost:5000/health
# - Dashboard: http://localhost:8080
```

**🎉 Congratulations! Quick installation complete.**

---

## 🔧 Method 2: Development Installation

This method provides additional tools and configurations for development and customization.

### Step 1: Enhanced Environment Setup

#### Create Development Environment
```bash
# Create and activate virtual environment
python -m venv ai_gold_scalper_dev
# Windows:
ai_gold_scalper_dev\Scripts\activate
# Linux/macOS:
source ai_gold_scalper_dev/bin/activate
```

#### Install Development Dependencies
```bash
# Install core requirements
pip install -r requirements.txt

# Install development tools (optional)
pip install jupyter notebook ipython black flake8 pytest

# Install additional ML libraries for research
pip install tensorflow torch optuna hyperopt
```

### Step 2: Development Configuration

#### Configure Development Settings
```bash
# Copy development configuration template
cp config/development_template.json config.json

# Edit configuration file
notepad config.json  # Windows
nano config.json     # Linux
```

#### Sample Development Configuration
```json
{
  "deployment_type": "development",
  "debug_mode": true,
  "logging_level": "DEBUG",
  "ai": {
    "api_key": "your_openai_api_key_here",
    "signal_fusion": {
      "ml_weight": 0.4,
      "technical_weight": 0.4,
      "gpt4_weight": 0.2
    }
  },
  "server": {
    "host": "localhost",
    "port": 5000,
    "debug": true
  },
  "development": {
    "enable_all_components": true,
    "verbose_logging": true,
    "performance_profiling": true
  }
}
```

### Step 3: Database Initialization

```bash
# Initialize system databases
python utils/initialize_databases.py

# Load sample data (optional)
python utils/load_sample_data.py
```

### Step 4: Development Tools Setup

#### Jupyter Notebook Setup (Optional)
```bash
# Install Jupyter kernel for the virtual environment
python -m ipykernel install --user --name ai_gold_scalper_dev

# Start Jupyter Notebook
jupyter notebook

# Access notebooks in the browser at http://localhost:8888
```

#### IDE Configuration (VS Code Example)
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./ai_gold_scalper_dev/Scripts/python.exe",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true
}
```

### Step 5: Run Development Tests

```bash
# Run system tests
python -m pytest utils/test_*.py

# Run component tests
python utils/test_backtesting_system.py

# Verify system integration
python utils/verify_wsgi_deployment.py
```

---

## 🌐 Method 3: VPS Production Installation

This method is optimized for production VPS environments with minimal resource usage.

### Step 1: VPS Preparation

#### System Updates (Ubuntu/Debian)
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Install Python 3.9+ if not available
sudo apt install -y python3.9 python3.9-venv python3.9-dev
```

#### System Updates (CentOS/RHEL)
```bash
# Update system packages
sudo yum update -y

# Install EPEL repository
sudo yum install -y epel-release

# Install required packages
sudo yum install -y python3 python3-pip git
```

### Step 2: User and Directory Setup

```bash
# Create dedicated user (recommended)
sudo useradd -m -s /bin/bash goldtrader
sudo usermod -aG sudo goldtrader

# Switch to trading user
sudo su - goldtrader

# Create application directory
mkdir -p ~/ai_gold_scalper
cd ~/ai_gold_scalper
```

### Step 3: Application Installation

```bash
# Download and extract application
wget https://github.com/your-repo/AI_Gold_Scalper/archive/main.zip
unzip main.zip
mv AI_Gold_Scalper-main/* .
rm -rf AI_Gold_Scalper-main main.zip

# Create production virtual environment
python3 -m venv venv
source venv/bin/activate

# Install production dependencies only
pip install --no-cache-dir -r requirements.txt
```

### Step 4: Production Configuration

#### Create Production Config
```bash
# Create production configuration
cat > config.json << 'EOF'
{
  "deployment_type": "production",
  "logging_level": "INFO",
  "ai": {
    "api_key": "YOUR_OPENAI_API_KEY",
    "signal_fusion": {
      "ml_weight": 0.5,
      "technical_weight": 0.4,
      "gpt4_weight": 0.1
    }
  },
  "server": {
    "host": "0.0.0.0",
    "port": 5000
  },
  "selected_components": [
    "ai_server",
    "model_registry", 
    "enhanced_trade_logger",
    "regime_detector",
    "data_processor"
  ],
  "performance": {
    "cache_timeout": 300,
    "max_workers": 4,
    "connection_pool_limit": 50
  }
}
EOF
```

#### Set Proper Permissions
```bash
# Set file permissions
chmod 600 config.json
chmod +x core/*.py
chmod +x scripts/*/*.py

# Create log directories
mkdir -p logs/backtesting
chmod 755 logs
```

### Step 5: System Service Setup (Linux)

#### Create Systemd Service
```bash
# Create service file
sudo tee /etc/systemd/system/ai-gold-scalper.service > /dev/null << 'EOF'
[Unit]
Description=AI Gold Scalper Trading System
After=network.target

[Service]
Type=simple
User=goldtrader
WorkingDirectory=/home/goldtrader/ai_gold_scalper
Environment=PATH=/home/goldtrader/ai_gold_scalper/venv/bin
ExecStart=/home/goldtrader/ai_gold_scalper/venv/bin/python core/system_orchestrator_enhanced.py start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ai-gold-scalper
sudo systemctl start ai-gold-scalper

# Check service status
sudo systemctl status ai-gold-scalper
```

### Step 6: Firewall and Security

```bash
# Configure firewall (Ubuntu)
sudo ufw allow 5000/tcp  # AI Server
sudo ufw allow 8080/tcp  # Dashboard (if enabled)
sudo ufw enable

# Secure SSH (recommended)
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

---

## 🔧 Advanced Installation Options

### GPU Support (Optional)

For enhanced machine learning performance:

```bash
# Install CUDA (NVIDIA GPUs only)
# Follow NVIDIA CUDA installation guide for your OS

# Install GPU-enabled packages
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install tensorflow-gpu
```

### Docker Installation (Alternative)

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 5000 8080

CMD ["python", "core/system_orchestrator_enhanced.py", "start"]
EOF

# Build and run container
docker build -t ai-gold-scalper .
docker run -d -p 5000:5000 -p 8080:8080 ai-gold-scalper
```

---

## ✅ Installation Verification

### Verification Checklist

Run these commands to verify your installation:

```bash
# 1. Check Python and packages
python --version
pip list | grep -E "(flask|pandas|numpy|scikit-learn)"

# 2. Verify system components
python core/system_orchestrator_enhanced.py status

# 3. Test AI server
curl http://localhost:5000/health

# 4. Check dashboard (if enabled)
curl http://localhost:8080/api/system-status

# 5. Verify model registry
python -c "from scripts.ai.model_registry import ModelRegistry; print('Model Registry: OK')"

# 6. Test trade logger
python -c "from scripts.monitoring.enhanced_trade_logger import *; print('Trade Logger: OK')"
```

### Expected Results

✅ **Successful Installation Indicators:**
- Python version 3.8+
- All required packages installed
- System status shows components running
- Health endpoint returns `{"status": "healthy"}`
- No import errors in verification tests

❌ **Common Issues and Solutions:**
- **Python version too old**: Install Python 3.8+
- **Package installation fails**: Check internet connection, upgrade pip
- **Permission denied**: Run as administrator or use sudo
- **Port already in use**: Change ports in configuration
- **Import errors**: Verify virtual environment activation

---

## 🔧 Post-Installation Configuration

### 1. OpenAI API Key Setup

```bash
# Method 1: Interactive setup
python core/system_orchestrator_enhanced.py interactive-setup

# Method 2: Direct configuration
# Edit config.json and add your API key:
# "api_key": "sk-your-openai-api-key-here"
```

### 2. MetaTrader 5 Integration

1. **Download and install MT5** from MetaQuotes
2. **Create demo account** for testing
3. **Install Expert Advisor** (EA) for AI Gold Scalper
4. **Configure EA settings** to connect to AI server
5. **Enable automated trading** in MT5

### 3. Component Selection

```bash
# Run interactive setup to choose components
python core/system_orchestrator_enhanced.py interactive-setup

# Or edit config.json directly:
"selected_components": [
  "ai_server",
  "model_registry", 
  "enhanced_trade_logger",
  "performance_dashboard"
]
```

---

## 🆘 Troubleshooting

### Common Installation Issues

#### Python Installation Issues
```bash
# Windows: Download from python.org
# Linux: sudo apt install python3.9
# macOS: brew install python@3.9

# Verify installation
python --version
pip --version
```

#### Package Installation Issues
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install packages one by one if bulk install fails
pip install flask pandas numpy scikit-learn

# Use --no-cache-dir for clean installation
pip install --no-cache-dir -r requirements.txt
```

#### Permission Issues (Linux)
```bash
# Use virtual environment to avoid permission issues
python3 -m venv venv
source venv/bin/activate

# Or install with --user flag
pip install --user -r requirements.txt
```

#### Port Conflicts
```bash
# Check what's using port 5000
netstat -tulnp | grep :5000

# Kill process using port
sudo kill -9 <process_id>

# Or change port in config.json
"server": {"port": 5001}
```

### Getting Help

1. **Check logs**: Look in `/logs/` directory for error messages
2. **Verify configuration**: Ensure config.json is properly formatted
3. **Test components individually**: Run each component separately
4. **Check system requirements**: Ensure all requirements are met
5. **Review documentation**: See [Troubleshooting Guide](25_Troubleshooting.md)

---

## 🔄 Next Steps

After successful installation:

1. **[Quick Start Guide](01_Quick_Start_Guide.md)** - Get trading in 15 minutes
2. **[Configuration Guide](21_Configuration_Guide.md)** - Customize your setup
3. **[System Overview](02_System_Overview.md)** - Understand what you installed
4. **[Performance Dashboard](14_Performance_Dashboard.md)** - Monitor your system

---

## 📋 Installation Summary

| Installation Type | Time Required | Best For | Components |
|-------------------|---------------|----------|------------|
| **Quick** | 15-30 min | Beginners | Core components |
| **Development** | 45-60 min | Developers | All components + tools |
| **VPS Production** | 30-45 min | Live trading | Production components |

**🎉 Your AI Gold Scalper installation is now complete and ready for trading!**

*Next: [Quick Start Guide](01_Quick_Start_Guide.md) to begin using your system.*
