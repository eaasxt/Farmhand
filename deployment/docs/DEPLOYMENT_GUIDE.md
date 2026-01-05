# Gas Town MCP Integration Layer - Production Deployment Guide

**Complete deployment procedures for the Gas Town MCP Integration Layer**

This guide covers deployment of the production-ready enhancement system that bridges Steve Yegge's Gas Town with the MCP Agent Mail ecosystem.

## 🎯 **Deployment Overview**

### **What We're Deploying**

The Gas Town MCP Integration Layer consists of:
- **Bridge System**: Detection and integration with Steve's Gas Town v0.1.1+
- **Enhanced Dashboard**: Real-time monitoring beyond basic status
- **tmux Integration**: Enhanced UX with Gas Town-themed configuration
- **MCP Connectivity**: Bridge to Agent Mail ecosystem

### **Architecture**

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│  Steve's Gas Town   │    │  Gas Town MCP Bridge │    │   MCP Agent Mail    │
│     (Go System)     │◄──►│   (Python Layer)     │◄──►│    (Ecosystem)      │
├─────────────────────┤    ├──────────────────────┤    ├─────────────────────┤
│ ✅ Existing System  │    │ 🔄 Our Integration    │    │ ✅ Existing System  │
│ ✅ No Changes       │    │ 📊 Enhanced Features  │    │ ✅ No Changes       │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
```

## 🚀 **Quick Deployment**

### **Prerequisites Validation**

```bash
# 1. Verify Steve's Gas Town is installed
which gt || echo "ERROR: Install Steve's Gas Town first"
gt --version  # Should show: gt version 0.1.1+

# 2. Verify MCP Agent Mail is running
curl -s http://127.0.0.1:8765/health || echo "WARNING: MCP Agent Mail not running"

# 3. Check Python environment
python3 --version  # Should be Python 3.8+
```

### **Installation**

```bash
# Deploy the Gas Town MCP Integration Layer
python3 /tmp/migrate_to_mcp_bridge.py --migrate

# Update PATH for new tools
echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
gt-mcp detect
gt-mcp status
```

### **Enhanced Features Setup**

```bash
# Configure tmux integration
gt-mcp tmux setup
echo 'source-file ~/.tmux.conf.gastown-mcp' >> ~/.tmux.conf
tmux source-file ~/.tmux.conf

# Test enhanced dashboard
gt-mcp dashboard --detect
```

## 📋 **Deployment Verification**

### **Integration Verification**

```bash
# 1. Detection Test
gt-mcp detect --json
# Expected: Shows Steve's Gas Town found and integrated

# 2. Status Integration Test
gt-mcp status
# Expected: Shows combined Gas Town + MCP status

# 3. Command Passthrough Test
gt-mcp --version
# Expected: Shows Steve's gt version (passthrough working)

# 4. Dashboard Test
timeout 10 gt-mcp dashboard --detect
# Expected: Launches without errors

# 5. tmux Integration Test
gt-mcp tmux status
# Expected: Shows tmux session information
```

### **Performance Validation**

```bash
# Timing benchmarks (should be sub-second)
time gt-mcp detect       # < 0.2s expected
time gt-mcp status       # < 0.5s expected (Steve's gt call dominates)
time gt-mcp dashboard --detect  # < 0.3s expected
```

### **MCP Integration Test**

```bash
# Test MCP Agent Mail connectivity
curl -s http://127.0.0.1:8765/health
# Expected: {"status": "healthy"}

# Test bridge services
gt-mcp detect --json | jq '.integration.mcp_available'
# Expected: true
```

## 🏗️ **Component Architecture**

### **Installed Components**

```
~/.local/bin/
├── gt-mcp -> gt_mcp_wrapper.py         # Main CLI entry point
├── gt_mcp_wrapper.py                   # CLI wrapper (passes through to Steve's gt)
├── gastown_mcp_bridge.py               # Detection and bridge system
└── enhanced_gastown_dashboard.py       # Real-time monitoring dashboard
```

### **Configuration Files**

```
~/.tmux.conf.gastown-mcp               # Enhanced tmux configuration
~/.config/gt-mcp/                      # Future configuration directory
```

## 🔄 **Deployment Workflows**

### **Standard Workflow**

```bash
# 1. Validate Environment
gt --version && echo "✅ Steve's Gas Town ready"
curl -s http://127.0.0.1:8765/health && echo "✅ MCP Agent Mail ready"

# 2. Deploy Integration Layer
python3 /tmp/migrate_to_mcp_bridge.py --migrate

# 3. Configure Environment
export PATH="$PATH:$HOME/.local/bin"

# 4. Verify Integration
gt-mcp detect && echo "✅ Integration successful"

# 5. Setup Enhanced Features
gt-mcp tmux setup && echo "✅ tmux integration ready"

# 6. Test Complete System
gt-mcp status && echo "✅ System operational"
```

### **Multi-Agent Setup Workflow**

```bash
# 1. Base deployment (as above)
python3 /tmp/migrate_to_mcp_bridge.py --migrate

# 2. Start MCP Agent Mail if needed
sudo systemctl start mcp-agent-mail

# 3. Verify multi-agent readiness
gt-mcp detect --json | jq '.integration.bridge_status'
# Expected: "active"

# 4. Test agent registration capability
# (Actual registration done by individual agents)
curl -s http://127.0.0.1:8765/mail
# Expected: Web interface accessible
```

## 🔧 **Configuration Management**

### **Bridge Configuration**

The integration layer automatically detects and adapts:

```python
# Detection paths for Steve's Gas Town
DETECTION_PATHS = [
    "/home/ubuntu/go/bin/gt",
    "/usr/local/bin/gt",
    "~/go/bin/gt"
]

# Performance settings
DETECTION_TIMEOUT = 10  # seconds
DETECTION_CACHE = 60    # seconds

# Dashboard settings
REFRESH_RATE = 5        # seconds
DATA_GATHERING_TIMEOUT = 30  # seconds
```

### **tmux Configuration**

Enhanced key bindings added to `~/.tmux.conf.gastown-mcp`:

```bash
# Gas Town MCP Integration Key Bindings
bind-key g display-popup -E -d "#{pane_current_path}" "gt-mcp status"
bind-key G display-popup -E -d "#{pane_current_path}" -h 90% "gt-mcp dashboard"
bind-key m display-popup -E -d "#{pane_current_path}" "gt-mcp detect"
bind-key b display-popup -E -d "#{pane_current_path}" "gt-mcp detect --json"
```

### **Environment Variables**

```bash
# Optional configuration
export GT_MCP_CACHE_TIMEOUT=60        # Detection cache duration
export GT_MCP_HEALTH_TIMEOUT=30       # Health check timeout
export GT_MCP_DASHBOARD_REFRESH=5     # Dashboard refresh rate
export GT_MCP_DEBUG=0                 # Debug logging (0 or 1)
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Steve's Gas Town Not Found**

```bash
# Symptom: gt-mcp detect shows "found": false

# Solution 1: Check installation
which gt
go install github.com/steveyegge/gastown/cmd/gt@latest

# Solution 2: Add to PATH
export PATH="$PATH:$HOME/go/bin"
echo 'export PATH="$PATH:$HOME/go/bin"' >> ~/.bashrc
```

#### **MCP Agent Mail Not Available**

```bash
# Symptom: gt-mcp status shows MCP unavailable

# Check service status
sudo systemctl status mcp-agent-mail

# Start if needed
sudo systemctl start mcp-agent-mail

# Verify endpoint
curl -s http://127.0.0.1:8765/health
```

#### **Bridge Commands Not Working**

```bash
# Symptom: gt-mcp command not found

# Check installation
ls -la ~/.local/bin/gt-mcp

# Reinstall if needed
python3 /tmp/migrate_to_mcp_bridge.py --migrate

# Verify PATH
echo $PATH | grep -o ~/.local/bin || echo "Add ~/.local/bin to PATH"
```

#### **Dashboard Issues**

```bash
# Symptom: Dashboard fails to launch

# Check Rich library availability
python3 -c "import rich; print('Rich available')" || pip3 install rich

# Test in fallback mode
gt-mcp dashboard --detect 2>&1 | head -20
```

#### **Permission Issues**

```bash
# Fix script permissions
chmod +x ~/.local/bin/gt-mcp
chmod +x ~/.local/bin/gt_mcp_wrapper.py
chmod +x ~/.local/bin/gastown_mcp_bridge.py
chmod +x ~/.local/bin/enhanced_gastown_dashboard.py
```

### **Diagnostic Commands**

```bash
# Complete system check
echo "=== Steve's Gas Town ==="
which gt && gt --version

echo "=== MCP Agent Mail ==="
curl -s http://127.0.0.1:8765/health

echo "=== Integration Bridge ==="
gt-mcp detect --json

echo "=== Performance Test ==="
time gt-mcp detect

echo "=== tmux Integration ==="
gt-mcp tmux status
```

## 📊 **Monitoring & Validation**

### **Health Monitoring**

```bash
# Continuous health monitoring
watch -n 30 'gt-mcp status | head -20'

# Performance monitoring
time gt-mcp detect && echo "Detection performance OK"

# Resource monitoring
ps aux | grep -E "(gt-mcp|enhanced_gastown)" | grep -v grep
```

### **Integration Metrics**

| Component | Expected Performance | Validation |
|-----------|---------------------|------------|
| **Detection** | < 0.2s | `time gt-mcp detect` |
| **Status** | < 0.5s | `time gt-mcp status` |
| **Dashboard** | < 0.3s | `time gt-mcp dashboard --detect` |
| **Memory** | < 20MB | `ps aux` for gt-mcp processes |

### **Validation Reports**

```bash
# Generate deployment report
{
  echo "=== Gas Town MCP Integration Deployment Report ==="
  echo "Date: $(date)"
  echo "User: $(whoami)"
  echo "Host: $(hostname)"
  echo ""
  echo "=== Steve's Gas Town ==="
  which gt && gt --version || echo "NOT FOUND"
  echo ""
  echo "=== MCP Agent Mail ==="
  curl -s http://127.0.0.1:8765/health || echo "NOT RUNNING"
  echo ""
  echo "=== Integration Status ==="
  gt-mcp detect --json 2>/dev/null || echo "INTEGRATION FAILED"
  echo ""
  echo "=== Performance ==="
  echo -n "Detection time: "
  (time gt-mcp detect >/dev/null) 2>&1 | grep real
} > /tmp/gt-mcp-deployment-report.txt

cat /tmp/gt-mcp-deployment-report.txt
```

## 🔐 **Security Considerations**

### **Security Features**

- ✅ **No Privilege Escalation**: Integration layer runs with user permissions
- ✅ **Command Passthrough**: All gt commands pass through to Steve's binary
- ✅ **Local Operations**: No external network dependencies beyond MCP
- ✅ **File Permissions**: Secure file permissions on installation
- ✅ **No System Changes**: Preserves existing Gas Town configuration

### **Security Validation**

```bash
# Check file permissions
ls -la ~/.local/bin/gt-mcp*
# Expected: -rwxr-xr-x (755 permissions)

# Verify no sudo required
gt-mcp status  # Should work without sudo

# Check for secure operation
gt-mcp detect --json | jq '.security // "No security violations detected"'
```

## 📈 **Performance Optimization**

### **Optimization Settings**

```bash
# Cache optimization for frequent calls
export GT_MCP_CACHE_TIMEOUT=120  # 2-minute cache

# Dashboard optimization for slower systems
export GT_MCP_DASHBOARD_REFRESH=10  # 10-second refresh

# Health check optimization
export GT_MCP_HEALTH_TIMEOUT=60  # 1-minute timeout
```

### **Performance Tuning**

```bash
# For high-frequency usage
echo 'alias gts="gt-mcp status"' >> ~/.bashrc
echo 'alias gtd="gt-mcp detect"' >> ~/.bashrc

# For development environments
echo 'export GT_MCP_DEBUG=1' >> ~/.bashrc  # Enable debug logging

# For production environments
echo 'export GT_MCP_CACHE_TIMEOUT=300' >> ~/.bashrc  # 5-minute cache
```

## 🔄 **Upgrade Procedures**

### **Upgrading Steve's Gas Town**

```bash
# Update Steve's system (our layer automatically adapts)
go install github.com/steveyegge/gastown/cmd/gt@latest

# Verify integration still works
gt-mcp detect
gt-mcp status
```

### **Upgrading Integration Layer**

```bash
# Backup current installation
cp ~/.local/bin/gt_mcp_wrapper.py ~/.local/bin/gt_mcp_wrapper.py.bak

# Deploy new version
python3 /tmp/migrate_to_mcp_bridge.py --migrate

# Verify upgrade
gt-mcp detect --json | jq '.version // "No version info"'
```

### **Rolling Back Integration**

```bash
# Remove integration layer
rm ~/.local/bin/gt-mcp*

# Restore direct access to Steve's Gas Town
# (Steve's system continues working unchanged)
gt --version  # Direct access to Steve's binary

# Re-install integration if needed
python3 /tmp/migrate_to_mcp_bridge.py --migrate
```

## 📚 **Reference Documentation**

### **Command Reference**

| Command | Purpose | Example |
|---------|---------|---------|
| `gt-mcp detect` | Show integration status | `gt-mcp detect --json` |
| `gt-mcp status` | Combined system status | `gt-mcp status` |
| `gt-mcp dashboard` | Launch monitoring | `gt-mcp dashboard` |
| `gt-mcp tmux setup` | Configure tmux | `gt-mcp tmux setup` |
| `gt-mcp <any-command>` | Pass through to Steve's gt | `gt-mcp convoy list` |

### **Integration Points**

- **Steve's Gas Town**: `/home/ubuntu/go/bin/gt` (no changes)
- **MCP Agent Mail**: `http://127.0.0.1:8765/` (no changes)
- **Integration Bridge**: `~/.local/bin/gt-mcp` (our addition)
- **Enhanced tmux**: `~/.tmux.conf.gastown-mcp` (our addition)

### **Related Documentation**

- **[Integration Guide](/home/ubuntu/projects/deere/INTEGRATION_GUIDE.md)**: Complete integration process
- **[AI Orchestration Guide](/home/ubuntu/projects/deere/AI_ORCHESTRATION_GUIDE.md)**: Multi-agent coordination
- **[Validation Report](/home/ubuntu/projects/deere/gas_town/docs/VALIDATION_REPORT.md)**: Testing results
- **[Gas Town Archive](/home/ubuntu/projects/deere/gas_town/archive/ARCHIVE_README.md)**: Historical reference

## 🎯 **Production Checklist**

### **Pre-Deployment**

- [ ] Steve's Gas Town v0.1.1+ installed and working
- [ ] MCP Agent Mail running on port 8765
- [ ] Python 3.8+ available
- [ ] User has ~/.local/bin in PATH

### **Deployment**

- [ ] Run migration script: `python3 /tmp/migrate_to_mcp_bridge.py --migrate`
- [ ] Update PATH: `export PATH="$PATH:$HOME/.local/bin"`
- [ ] Verify detection: `gt-mcp detect`
- [ ] Test status: `gt-mcp status`

### **Post-Deployment**

- [ ] Configure tmux: `gt-mcp tmux setup`
- [ ] Test dashboard: `gt-mcp dashboard --detect`
- [ ] Validate performance: `time gt-mcp detect` (< 0.2s)
- [ ] Test command passthrough: `gt-mcp --version`
- [ ] Verify MCP connectivity: `gt-mcp detect --json | jq '.integration'`

### **Production Validation**

- [ ] All commands work as expected
- [ ] Performance meets benchmarks (< 0.5s response times)
- [ ] Steve's Gas Town functionality unchanged
- [ ] MCP integration functional
- [ ] Enhanced features operational
- [ ] No security issues detected

## 🏆 **Success Metrics**

### **Integration Success Criteria**

✅ **Steve's Gas Town Integration**: All `gt` commands work through `gt-mcp`
✅ **Enhanced Status**: Combined system visibility
✅ **Real-Time Dashboard**: Monitoring beyond basic status
✅ **tmux Integration**: Enhanced UX with Gas Town theming
✅ **MCP Connectivity**: Bridge to Agent Mail ecosystem
✅ **Performance**: Sub-second response times
✅ **Non-Competing**: No conflicts with existing systems

### **Deployment Complete**

🎉 **Gas Town MCP Integration Layer Successfully Deployed**

The system is now ready for production use with:
- Enhanced monitoring and dashboard capabilities
- Superior tmux integration for multi-agent coordination
- MCP ecosystem connectivity through Agent Mail bridge
- Full compatibility with Steve's sophisticated Gas Town system

---

*For technical support, troubleshooting, or advanced configuration, refer to the Integration Guide and related documentation.*
