# 🏠 Local Dashboard Setup Guide

This guide helps you set up the AI Gold Scalper dashboard on your **local computer** for development and monitoring.

## 📋 Quick Start

1. **Copy Project to Local Machine**
   - Download/copy the entire `AI_Gold_Scalper` folder to your local computer
   - Ensure all files are present, especially:
     - `scripts/monitoring/performance_dashboard.py`
     - `scripts/monitoring/enhanced_trade_logger.py`
     - `start_dashboard.ps1`
     - `setup_local_dashboard.ps1`

2. **Run Setup Script**
   ```powershell
   # Open PowerShell in the AI_Gold_Scalper directory
   .\setup_local_dashboard.ps1
   ```

3. **Start Dashboard**
   ```powershell
   .\start_dashboard.ps1
   ```

4. **Access Dashboard**
   - Open browser to: `http://localhost:5555`

## 🏗️ Architecture Options

### Option 1: Pure Local Setup (Recommended for Development)
```
LOCAL MACHINE:
├── Dashboard (localhost:5555)
├── Analysis Tools
├── Model Training
└── Local Database Copy

VPS:
├── AI Server (Live Trading)
└── Production Database
```

**Pros:**
- ✅ No network dependencies
- ✅ Fast development cycle
- ✅ Full control over environment
- ✅ Uses local machine resources

**Cons:**
- ❌ Need to copy data from VPS periodically
- ❌ Not real-time unless synced

### Option 2: Hybrid Setup (Best of Both Worlds)
```
LOCAL MACHINE:
├── Dashboard (localhost:5555)
├── Analysis Tools
└── Model Training

VPS:
├── AI Server (Live Trading)
├── Production Database
└── API Endpoint for Dashboard
```

**Pros:**
- ✅ Real-time data access
- ✅ Local development flexibility
- ✅ Always-on production trading

**Cons:**
- ❌ Requires network connection
- ❌ Need to secure VPS API access

### Option 3: Full VPS Setup
```
VPS:
├── AI Server (Live Trading)
├── Production Database
└── Dashboard (VPS:5555)
```

**Pros:**
- ✅ Always available
- ✅ Remote access from anywhere

**Cons:**
- ❌ Uses VPS resources
- ❌ Need to configure firewall
- ❌ Slower development cycle

## 🔧 Data Connection Methods

### Method 1: Local Database Copy
1. Copy `trade_logs.db` from VPS to local `scripts/monitoring/`
2. Dashboard reads local database file
3. Update periodically by copying new database

**Setup:**
```powershell
# Copy from VPS (example with scp)
scp user@your-vps:/path/to/trade_logs.db scripts/monitoring/
```

### Method 2: SSH Tunnel to VPS Database
1. Create SSH tunnel to VPS
2. Dashboard connects through tunnel
3. Real-time data access

**Setup:**
```powershell
# Create SSH tunnel (port 5432 for database)
ssh -L 5432:localhost:5432 user@your-vps

# Dashboard connects to localhost:5432 (tunneled to VPS)
```

### Method 3: VPS API Access
1. Set up REST API on VPS
2. Dashboard calls API for data
3. Most flexible but requires API development

## 🚀 Getting Started

### Step 1: Choose Your Setup
Run the setup script and choose your preferred connection method:

```powershell
.\setup_local_dashboard.ps1
```

### Step 2: Configure Data Access
Based on your choice:

- **Local Data:** Copy `trade_logs.db` from VPS
- **VPS Data:** Set up SSH tunnel or API access
- **Demo Mode:** Use sample data for testing

### Step 3: Start Dashboard
```powershell
.\start_dashboard.ps1
```

### Step 4: Access Features
- **Dashboard:** `http://localhost:5555`
- **Health Monitor:** Check system status
- **Trade Analytics:** Review performance
- **Risk Assessment:** Monitor risk metrics

## 🔄 Development Workflow

### Daily Development:
1. Start local dashboard
2. Develop and test changes
3. Copy new database from VPS (if needed)
4. Deploy changes to VPS when ready

### Production Monitoring:
1. Keep dashboard running locally
2. Sync data periodically
3. Use for analysis and optimization
4. Push model updates to VPS

## 🛠️ Troubleshooting

### Dashboard Won't Start
- Check Python installation: `python --version`
- Install missing packages: `pip install flask pandas plotly`
- Verify project structure is correct

### No Data Showing
- Check database file exists: `scripts/monitoring/trade_logs.db`
- Verify database has data
- Check connection settings

### Connection Issues (VPS Data)
- Test SSH connection to VPS
- Verify tunnel is active
- Check firewall settings

### Performance Issues
- Close unnecessary browser tabs
- Restart dashboard
- Check system resources

## 📊 Dashboard Features

### Real-time Monitoring:
- Live trade performance
- System health indicators
- Risk metrics tracking
- Auto-refresh every 30 seconds

### Interactive Analytics:
- Profit/Loss charts
- Win rate analysis
- Drawdown tracking
- Signal accuracy metrics

### System Health:
- AI server status
- Model performance
- Resource utilization
- Error tracking

## 🔒 Security Notes

### For Local Setup:
- Dashboard only accessible from your computer
- No external network exposure
- Safe for development and testing

### For VPS Access:
- Use SSH keys, not passwords
- Consider VPN for additional security
- Limit API access to your IP
- Use strong authentication

## 📞 Need Help?

If you encounter issues:
1. Check this guide first
2. Run the setup script again
3. Verify all prerequisites are met
4. Check the troubleshooting section

The setup script will guide you through each step and help identify any issues.
