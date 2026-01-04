# Gas Town MEOW Stack - Production Deployment Guide

**Complete deployment automation and rollback procedures for 100% production readiness**

## Overview

This guide covers the comprehensive deployment automation system for the Gas Town MEOW stack, including:

- **Automated Deployment Pipeline** - Full automation for all MEOW components
- **Zero-Downtime Deployment** - Blue-green deployment strategies  
- **Comprehensive Rollback** - Complete rollback procedures and automation
- **CI/CD Integration** - Git hooks and GitHub Actions integration
- **Production Safety** - Validation, monitoring, and emergency procedures

---

## 🏗️ Architecture Overview

```
Gas Town MEOW Stack - Deployment Architecture

deployment/
├── scripts/                          # Automation Scripts
│   ├── deploy/                      # Deployment automation
│   │   └── deploy_meow_stack.sh     # Main deployment script
│   ├── rollback/                    # Rollback procedures  
│   │   └── rollback_meow_stack.sh   # Comprehensive rollback
│   ├── zero-downtime/               # Blue-green deployment
│   │   └── blue_green_deploy.sh     # Zero-downtime deployment
│   └── validation/                  # Pre/post deployment validation
│       └── deployment_validator.sh  # Validation suite
├── ci-cd/                           # CI/CD Integration
│   ├── hooks/                       # Git hooks
│   │   ├── pre-receive             # Pre-deployment validation
│   │   └── post-receive            # Automated deployment trigger
│   └── pipelines/                   # CI/CD pipelines
│       └── github_actions.yml      # GitHub Actions workflow
├── configs/                         # Deployment configurations
├── logs/                           # Deployment logs and reports
└── backup/                         # System backups
```

---

## 🚀 Quick Start

### 1. Validate Environment

```bash
# Run pre-deployment validation
./deployment/scripts/validation/deployment_validator.sh -t pre

# Check deployment readiness
./deployment/scripts/deploy/deploy_meow_stack.sh --validate-only
```

### 2. Standard Deployment

```bash
# Deploy all components
./deployment/scripts/deploy/deploy_meow_stack.sh

# Deploy specific component
./deployment/scripts/deploy/deploy_meow_stack.sh -c marketplace
./deployment/scripts/deploy/deploy_meow_stack.sh -c monitoring
./deployment/scripts/deploy/deploy_meow_stack.sh -c orchestration
```

### 3. Zero-Downtime Deployment

```bash
# Blue-green deployment (production recommended)
./deployment/scripts/zero-downtime/blue_green_deploy.sh

# With custom ports
./deployment/scripts/zero-downtime/blue_green_deploy.sh --blue-port 9000 --green-port 9001
```

### 4. Emergency Rollback

```bash
# List available backups
./deployment/scripts/rollback/rollback_meow_stack.sh -l

# Rollback to latest backup
./deployment/scripts/rollback/rollback_meow_stack.sh

# Rollback to specific backup
./deployment/scripts/rollback/rollback_meow_stack.sh -b 20240104_143022

# Force rollback without confirmation
./deployment/scripts/rollback/rollback_meow_stack.sh -f
```

---

## 📋 Deployment Scripts Reference

### Main Deployment Script

**File:** `deployment/scripts/deploy/deploy_meow_stack.sh`

```bash
# Full deployment with all safety checks
./deploy_meow_stack.sh

# Validation only (dry run)
./deploy_meow_stack.sh --validate-only

# Skip backup (faster deployment)
./deploy_meow_stack.sh --skip-backup

# Deploy specific component
./deploy_meow_stack.sh --component marketplace

# Disable auto-rollback on failure
./deploy_meow_stack.sh --no-auto-rollback

# Custom environment
ENVIRONMENT=staging ./deploy_meow_stack.sh
```

**Features:**
- ✅ Pre-deployment validation
- ✅ Automatic backup creation
- ✅ Component-wise deployment
- ✅ Health checks and validation
- ✅ Automatic rollback on failure
- ✅ Comprehensive logging

### Zero-Downtime Deployment

**File:** `deployment/scripts/zero-downtime/blue_green_deploy.sh`

```bash
# Standard blue-green deployment
./blue_green_deploy.sh

# Custom port configuration
./blue_green_deploy.sh --blue-port 8000 --green-port 8001

# Extended health check timeout
./blue_green_deploy.sh --health-timeout 600

# Quick traffic switch (advanced)
./blue_green_deploy.sh --switch-delay 5
```

**Blue-Green Process:**
1. 🔍 Detect current deployment (blue/green)
2. 🚀 Start new deployment on alternate color
3. 🏥 Comprehensive health validation
4. 🔄 Gradual traffic switching with monitoring
5. 🛑 Stop old deployment after validation
6. 🚨 Emergency rollback if any step fails

### Comprehensive Rollback

**File:** `deployment/scripts/rollback/rollback_meow_stack.sh`

```bash
# Interactive rollback (default)
./rollback_meow_stack.sh

# List all available backups
./rollback_meow_stack.sh --list

# Rollback specific component
./rollback_meow_stack.sh --component marketplace

# Force rollback (no confirmation)
./rollback_meow_stack.sh --force

# Rollback to specific backup
./rollback_meow_stack.sh --backup-id 20240104_143022
```

**Rollback Features:**
- ✅ Backup integrity validation
- ✅ Service graceful shutdown
- ✅ Database restoration with safety checks
- ✅ Configuration rollback
- ✅ Service restart and validation
- ✅ Rollback reporting and logging

### Deployment Validation

**File:** `deployment/scripts/validation/deployment_validator.sh`

```bash
# Pre-deployment validation
./deployment_validator.sh -t pre

# Post-deployment validation  
./deployment_validator.sh -t post

# Strict mode (fail on warnings)
./deployment_validator.sh -t pre --strict

# Custom environment
./deployment_validator.sh -t pre -e staging
```

**Validation Categories:**
- 🔧 System requirements (Python, SQLite, disk, memory)
- 📁 File structure and permissions
- 🐍 Python dependencies and imports
- 🗄️ Database connectivity and integrity
- 🏥 Service health and endpoints
- 🌐 Network connectivity and ports
- 🔒 Security configuration

---

## 🔄 CI/CD Integration

### Git Hooks

**Pre-receive Hook:** `deployment/ci-cd/hooks/pre-receive`
- Validates commit messages and format
- Scans for potential secrets
- Checks code syntax
- Validates deployment readiness

**Post-receive Hook:** `deployment/ci-cd/hooks/post-receive`
- Triggers automated deployment based on branch
- Creates deployment locks to prevent conflicts
- Executes appropriate deployment strategy
- Performs post-deployment validation

**Installation:**
```bash
# Copy to your git repository hooks
cp deployment/ci-cd/hooks/* /path/to/repo/.git/hooks/
chmod +x /path/to/repo/.git/hooks/*
```

### GitHub Actions

**File:** `deployment/ci-cd/pipelines/github_actions.yml`

**Workflow Stages:**
1. **Validation & Security** - Code quality, security scans, syntax checks
2. **Testing** - Unit tests, integration tests, health simulations
3. **Build & Package** - Create deployment artifacts
4. **Deploy Production** - Blue-green deployment with health checks
5. **Post-Deploy Validation** - Comprehensive validation and rollback triggers

**Branch Strategies:**
- `main/master` → Production deployment
- `staging/release` → Staging deployment  
- `development/dev` → Development deployment
- Pull requests → Validation only

---

## 🏥 Health Checks & Monitoring

### Health Check Endpoints

The deployment system monitors these endpoints:
- `http://localhost:8000/health` - Marketplace API
- `http://localhost:8080/health` - Health monitoring service
- `http://localhost:9090/health` - Orchestration engine

### Health Check Integration

```bash
# Manual health check
cd monitoring && ./scripts/health_check.sh

# Health check with custom timeout
HEALTH_CHECK_TIMEOUT=300 ./scripts/health_check.sh

# Post-deployment validation
./deployment/scripts/validation/deployment_validator.sh -t post
```

### Monitoring Integration

All deployment scripts integrate with the existing monitoring system:
- 📊 Automatic health reporting
- 🚨 Alert generation on failures
- 📈 Performance metric collection
- 📋 Deployment status tracking

---

## 🚨 Emergency Procedures

### Deployment Failure Recovery

**If deployment fails during execution:**
1. Automatic rollback is triggered (if enabled)
2. Services are restored to previous state
3. Failure logs are captured in `deployment/logs/`
4. Alert notifications are sent

**Manual intervention:**
```bash
# Check deployment status
tail -f deployment/logs/deploy_*.log

# Force rollback if auto-rollback failed
./deployment/scripts/rollback/rollback_meow_stack.sh --force

# Validate system after rollback
./deployment/scripts/validation/deployment_validator.sh -t post
```

### Service Recovery

**If services are unresponsive after deployment:**
```bash
# Check service status
ps aux | grep -E "(health_endpoint|monitoring|marketplace)"

# Restart specific services
cd monitoring && ./scripts/health_endpoint.sh restart

# Full system restart
./deployment/scripts/deploy/deploy_meow_stack.sh -c all --skip-backup
```

### Database Recovery

**If database is corrupted:**
```bash
# List available database backups
ls deployment/backup/*/marketplace.db.bak

# Restore from specific backup
./deployment/scripts/rollback/rollback_meow_stack.sh -b BACKUP_ID -c marketplace

# Validate database integrity
sqlite3 molecule-marketplace/marketplace.db "PRAGMA integrity_check;"
```

---

## 📊 Deployment Metrics & Reporting

### Automatic Reporting

All deployment operations generate comprehensive reports:

**Deployment Reports:** `deployment/logs/deployment_report_*.json`
```json
{
  "deployment_timestamp": "2024-01-04T15:30:00Z",
  "deployment_type": "blue_green", 
  "deployment_successful": true,
  "components_deployed": ["marketplace", "monitoring", "orchestration"],
  "deployment_duration": "00:05:23",
  "health_checks_passed": true
}
```

**Validation Reports:** `deployment/logs/validation_report_*.json`
```json
{
  "validation_timestamp": "2024-01-04T15:25:00Z",
  "validation_type": "pre",
  "results": {
    "total_checks": 45,
    "passed": 43,
    "failed": 0,
    "warnings": 2,
    "success_rate": 95
  },
  "deployment_ready": true
}
```

**Rollback Reports:** `deployment/logs/rollback_report_*.json`
```json
{
  "rollback_timestamp": "2024-01-04T15:45:00Z",
  "backup_used": "20240104_152500",
  "rollback_successful": true,
  "components_restored": ["marketplace", "monitoring"],
  "rollback_reason": "health_check_failure"
}
```

### Log Analysis

```bash
# View recent deployment activity
ls -la deployment/logs/ | head -10

# Check deployment success rate
grep -c "deployment_successful.*true" deployment/logs/deployment_report_*.json

# View validation summaries  
grep -E "(passed|failed|warnings)" deployment/logs/validation_report_*.json | tail -5

# Monitor real-time deployment
tail -f deployment/logs/deploy_$(date +%Y%m%d)_*.log
```

---

## 🔧 Configuration Management

### Environment-Specific Configurations

**Production:**
```bash
ENVIRONMENT=production ./deploy_meow_stack.sh
AUTO_ROLLBACK=true
HEALTH_CHECK_TIMEOUT=300
SKIP_BACKUP=false
```

**Staging:**
```bash
ENVIRONMENT=staging ./deploy_meow_stack.sh  
AUTO_ROLLBACK=false
HEALTH_CHECK_TIMEOUT=60
SKIP_BACKUP=true
```

**Development:**
```bash
ENVIRONMENT=development ./deploy_meow_stack.sh
VALIDATE_ONLY=false
COMPONENT=all
```

### Deployment Configuration Files

**Health Configuration:** `monitoring/config/health_config.yaml`
**Alert Rules:** `monitoring/alerts/alert_rules.yaml`
**Deployment Settings:** `deployment/configs/`

---

## 🛡️ Security Considerations

### Deployment Security

- ✅ No secrets in deployment scripts
- ✅ Secure file permissions (755 for scripts)
- ✅ Input validation and sanitization
- ✅ Secure backup handling
- ✅ Process isolation

### Access Control

```bash
# Recommended permissions
chmod 755 deployment/scripts/**/*.sh
chmod 644 deployment/configs/**/*.yaml
chmod 700 deployment/backup/
chmod 600 deployment/logs/*.log
```

### Secret Management

- Use environment variables for secrets
- Never commit credentials to repository
- Rotate deployment keys regularly
- Monitor for secret leakage in logs

---

## 📈 Performance Optimization

### Deployment Speed

**Fast Deployment (when backup exists):**
```bash
./deploy_meow_stack.sh --skip-backup -c marketplace
```

**Parallel Component Deployment:**
```bash
# Deploy components in parallel (advanced)
./deploy_meow_stack.sh -c marketplace &
./deploy_meow_stack.sh -c monitoring &
./deploy_meow_stack.sh -c orchestration &
wait
```

### Resource Optimization

- Database operations use minimal locking
- Health checks are non-blocking
- Backup creation is incremental when possible
- Log rotation prevents disk overflow

---

## 🔬 Testing & Validation

### Testing Deployment Scripts

```bash
# Test deployment in development environment
ENVIRONMENT=development VALIDATE_ONLY=true ./deploy_meow_stack.sh

# Test rollback procedures
./rollback_meow_stack.sh --list
./rollback_meow_stack.sh --backup-id test_backup --no-confirm

# Validate blue-green deployment
./blue_green_deploy.sh --blue-port 19000 --green-port 19001
```

### Continuous Validation

```bash
# Set up continuous validation (cron)
*/5 * * * * cd /path/to/project && ./deployment/scripts/validation/deployment_validator.sh -t post > /dev/null

# Health monitoring integration
cd monitoring && ./scripts/health_check.sh
```

---

## 🆘 Support & Troubleshooting

### Common Issues

**1. Port Conflicts**
```bash
# Check port usage
lsof -i :8000
# Kill conflicting process or use different ports
./blue_green_deploy.sh --blue-port 8002 --green-port 8003
```

**2. Permission Errors**
```bash
# Fix script permissions
chmod +x deployment/scripts/**/*.sh
# Check file ownership
chown -R $USER deployment/
```

**3. Database Lock**
```bash
# Check for database locks
sqlite3 molecule-marketplace/marketplace.db ".timeout 30000"
# Restart database-dependent services
```

**4. Health Check Failures**
```bash
# Increase health check timeout
HEALTH_CHECK_TIMEOUT=600 ./deploy_meow_stack.sh
# Check service logs
tail -f deployment/logs/deploy_*.log
```

### Getting Help

- 📋 Check deployment logs: `deployment/logs/`
- 🔍 Run validation: `./deployment_validator.sh -t post --strict`
- 🏥 Manual health check: `cd monitoring && ./scripts/health_check.sh`
- 📊 Review reports: `deployment/logs/*_report_*.json`

---

## 📝 Changelog & Versioning

**Version 1.0.0** - Initial Release
- ✅ Complete deployment automation
- ✅ Zero-downtime blue-green deployment
- ✅ Comprehensive rollback procedures  
- ✅ CI/CD integration with Git hooks
- ✅ GitHub Actions workflow
- ✅ Deployment validation suite
- ✅ Emergency recovery procedures
- ✅ Production monitoring integration

---

## 🎯 Production Readiness Checklist

- ✅ **Automated Deployment Pipeline** - Complete automation for all components
- ✅ **Database Migration Procedures** - Automatic migration and schema updates
- ✅ **Configuration Management** - Environment-specific configurations
- ✅ **Service Management** - Graceful restart and health verification
- ✅ **Zero-Downtime Deployment** - Blue-green deployment strategies
- ✅ **Complete Rollback System** - Database, configuration, and service rollback
- ✅ **Emergency Procedures** - Automated rollback triggers and manual procedures
- ✅ **CI/CD Integration** - Git hooks and GitHub Actions
- ✅ **Pre-deployment Validation** - Comprehensive validation suite
- ✅ **Post-deployment Verification** - Health checks and monitoring
- ✅ **Production Documentation** - Complete runbooks and emergency procedures
- ✅ **Security Hardening** - Secure deployment practices
- ✅ **Performance Monitoring** - Deployment metrics and reporting

**🎉 100% Production Readiness Achieved!**

The Gas Town MEOW Stack now has enterprise-grade deployment automation with comprehensive safety measures, monitoring integration, and emergency recovery procedures.

---

*For technical support or deployment assistance, refer to the troubleshooting section or review the comprehensive logs generated by each deployment operation.*
