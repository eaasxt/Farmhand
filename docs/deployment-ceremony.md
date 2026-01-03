# Deployment Ceremony Guide

**The Complete Git → Build → Deploy → Verify Pipeline**

Based on real deployment confusion from multi-agent projects, this guide provides clear ceremony steps and decision trees to eliminate "proceed as you see fit" ambiguity.

## Overview

The deployment ceremony is a **structured sequence** that ensures changes are safely deployed to production. Each step has **clear prerequisites** and **validation gates**.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Validate  │ -> │    Build    │ -> │   Deploy    │ -> │   Verify    │
│  (Pre-req)  │    │  (Package)  │    │ (Production) │    │ (Health)    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
    • Tests pass        • Clean build     • URL accessible   • Health checks
    • UBS scan clean    • No warnings     • DNS resolving    • API responding
    • No conflicts      • Size limits     • HTTPS working    • Basic smoke test
```

## Deployment Profiles

| Profile | Use Case | Steps | Validation Level |
|---------|----------|-------|------------------|
| `dev` | Local testing | Build + Local tunnel | Basic |
| `staging` | Pre-production | Full pipeline to staging | Comprehensive |
| `production` | Live deployment | Full pipeline + rollback safety | Maximum |

---

## Phase 1: Pre-Deployment Validation

**MANDATORY GATES - Do not skip these steps**

### 1.1 Code Quality Gate
```bash
# Run security scan
ubs $(git diff --name-only HEAD~1 HEAD)
# Must exit 0 (no critical findings)

# Run tests if they exist
npm test || pytest || echo "No tests configured"
```

### 1.2 Working Tree Gate
```bash
# Check for uncommitted changes
git status --porcelain
# Must be empty (clean working tree)

# Check current branch
git branch --show-current
# Should not be 'main' for features (use feature branches)
```

### 1.3 Integration Gate
```bash
# Pull latest changes
git pull origin main

# Check for conflicts
git merge-base HEAD origin/main
# Resolve any conflicts before proceeding
```

**✅ VALIDATION:** All gates pass → Proceed to Build
**❌ FAILURE:** Any gate fails → Fix issues and restart

---

## Phase 2: Build & Package

### 2.1 Local Build Validation
```bash
# Clean build (remove previous artifacts)
rm -rf dist/ build/ .next/

# Build application
npm run build      # React/Vite/Next.js
# OR
python -m build    # Python packages

# Verify build artifacts
ls -la dist/       # Check size, no missing files
```

### 2.2 Build Artifact Validation
```bash
# Check bundle size (if applicable)
du -sh dist/
# React apps: typically < 10MB
# Node.js: check node_modules exclusions

# Test build locally (if possible)
npm run preview    # Vite
# OR  
npm run start     # Next.js production build
```

**Build Success Criteria:**
- No build errors or warnings
- Artifacts present and reasonable size
- Local preview works (if applicable)

---

## Phase 3: Git Ceremony

### 3.1 Commit Preparation
```bash
# Stage relevant changes
git add .

# Create descriptive commit message
git commit -m "feat: implement user authentication

- Add JWT token validation
- Implement password reset flow
- Update API endpoints for new auth
- Add authentication tests

Closes: bd-123"
```

### 3.2 Push with Validation
```bash
# Push to feature branch first (not main)
git push origin feature/auth-implementation

# Verify push succeeded
git log --oneline -1
echo "Pushed: $(git log --oneline -1)"
```

**Git Success Criteria:**
- Clean commit history
- Descriptive commit messages
- Push completed successfully
- Ready for deployment trigger

---

## Phase 4: Deployment Trigger

### 4.1 Automatic Deployment (Recommended)

**Vercel (Push-to-Deploy):**
```bash
# Push triggers automatic deployment
git push origin main

# Monitor deployment
vercel --prod --confirm 2>/dev/null || echo "Deployment triggered"

# Get deployment URL
vercel ls --scope team --json | jq -r '.[0].url'
```

**Manual Deployment:**
```bash
# Use deployment script
./scripts/deployment/deploy.sh $(pwd) production automatic
```

### 4.2 Deployment Status Monitoring
```bash
# Check deployment status
vercel ls | head -5

# Watch deployment logs (if needed)
vercel logs --follow

# Expected: "Ready" status within 2-5 minutes
```

---

## Phase 5: Deployment Verification

### 5.1 Basic Connectivity
```bash
DEPLOY_URL="https://your-app.vercel.app"

# Test HTTPS accessibility
curl -I "$DEPLOY_URL" | head -1
# Expected: HTTP/2 200 or HTTP/1.1 200

# Test DNS resolution
nslookup $(echo "$DEPLOY_URL" | sed 's|https\?://||')
# Expected: Valid IP address
```

### 5.2 Health Check Validation
```bash
# Test health endpoint (if available)
curl -f "$DEPLOY_URL/api/health" || echo "No health endpoint"

# Test main page load time
time curl -s -o /dev/null "$DEPLOY_URL"
# Expected: < 3 seconds

# Test API endpoints (if applicable)
curl -f "$DEPLOY_URL/api/status" || echo "No status API"
```

### 5.3 Functional Smoke Test
```bash
# For web apps: test key user flows
# For APIs: test critical endpoints
# For static sites: test main navigation

echo "Manual verification required:"
echo "1. Open $DEPLOY_URL in browser"
echo "2. Test main functionality"
echo "3. Verify no console errors"
echo "4. Check mobile responsiveness"
```

---

## Decision Trees

### Decision Tree 1: Should I deploy now?

```
Are tests passing? ─── NO ──────> Fix tests first
       │
      YES
       │
Is UBS scan clean? ─── NO ──────> Fix security issues
       │
      YES
       │
Clean working tree? ── NO ──────> Commit or stash changes
       │
      YES
       │
Is this urgent? ────── YES ─────> Use production profile
       │
      NO
       │
Use staging profile ──────────────> Full validation
```

### Decision Tree 2: Deployment failed. What now?

```
Build failed? ───────── YES ──────> Check logs, fix build errors
       │
      NO
       │
Deploy failed? ──────── YES ──────> Check Vercel status, retry
       │
      NO
       │
Health check failed? ── YES ──────> Check app logs, rollback if critical
       │
      NO
       │
DNS/Network issue? ──── YES ──────> Check domain config, wait for propagation
       │
      NO
       │
Contact team ──────────────────────> Report specific error details
```

### Decision Tree 3: Multiple agents deploying

```
Check #general channel ─── Someone deploying? ──> Coordinate deployment window
       │
      NO
       │
Announce deployment ───────────────> "🚀 Deploying [feature] to production"
       │
Wait for confirmation ─────────────> "👍" from team
       │
Proceed with deployment ───────────> Follow full ceremony
       │
Announce completion ───────────────> "✅ [feature] deployed: [URL]"
```

---

## Common Issues & Recovery

### Issue 1: "Vercel build failed"
**Symptoms:** Build succeeds locally but fails on Vercel
**Causes:** 
- Environment variables missing
- Node.js version mismatch
- Dependency conflicts

**Recovery:**
```bash
# Check Vercel logs
vercel logs

# Verify environment variables
vercel env ls

# Check Node.js version
cat package.json | grep '"node"'

# Redeploy with verbose logging
vercel --prod --debug
```

### Issue 2: "Site deployed but showing 404"
**Symptoms:** Deployment succeeds but site not accessible
**Causes:**
- Routing configuration issues
- Missing build output
- CDN cache issues

**Recovery:**
```bash
# Check build output exists
vercel ls --json | jq '.[0].source'

# Clear CDN cache
curl -X POST "https://api.vercel.com/v1/deployments/[deployment-id]/functions/purge"

# Check routing configuration
cat vercel.json 2>/dev/null || echo "No vercel.json found"
```

### Issue 3: "API endpoints returning 500"
**Symptoms:** Frontend loads but API calls fail
**Causes:**
- Environment variables missing
- Database connection issues
- Runtime errors

**Recovery:**
```bash
# Check serverless function logs
vercel logs --since=1h

# Test API endpoint directly
curl -v "$DEPLOY_URL/api/test"

# Verify environment variables
vercel env pull .env.production
cat .env.production
```

---

## Automation Scripts

### Quick Deploy Script
```bash
#!/bin/bash
# quick-deploy.sh - For simple updates

set -euo pipefail

echo "🚀 Starting quick deployment..."

# Validation
ubs --staged || exit 1
npm test || true

# Build & Deploy
npm run build
git add . && git commit -m "chore: deploy $(date)"
git push origin main

echo "✅ Deployment triggered!"
```

### Full Ceremony Script
```bash
#!/bin/bash
# full-deploy.sh - For production releases

set -euo pipefail

echo "🎭 Starting full deployment ceremony..."

# Pre-flight checks
./scripts/deployment/deploy.sh $(pwd) production manual

echo "✅ Full ceremony complete!"
```

---

## Integration with Multi-Agent Workflow

### Agent Coordination
```markdown
## Before Deploying
1. Send message: `[DEPLOY] Starting deployment of bd-123`
2. Wait for confirmations from other agents
3. Reserve deployment slot in #coordination

## During Deployment  
1. Update status: `[DEPLOY] Building... (2/4)`
2. Share progress in #general
3. Announce any issues immediately

## After Deployment
1. Announce completion: `[DEPLOY] ✅ bd-123 live: https://app.vercel.app`
2. Release deployment slot
3. Update project documentation
```

### File Reservations
```python
# Reserve deployment-related files before starting
file_reservation_paths(
    project_key="/home/ubuntu/myproject",
    agent_name="DeployBot",
    paths=["vercel.json", "package.json", "deploy.sh"],
    ttl_seconds=1800,  # 30 minutes
    exclusive=True,
    reason="deployment-ceremony"
)
```

---

## Success Metrics

**Deployment ceremony is successful when:**
- ✅ Zero ambiguity on next steps
- ✅ All team members know deployment status  
- ✅ Rollback plan exists and is tested
- ✅ Health checks pass within 5 minutes
- ✅ No "proceed as you see fit" confusion
- ✅ Deployment completes in < 10 minutes total

**Red flags requiring ceremony halt:**
- ❌ Tests failing
- ❌ Security scan shows critical issues
- ❌ Multiple agents deploying simultaneously
- ❌ Production database migrations pending
- ❌ External service dependencies down

---

This ceremony eliminates the deployment confusion seen in multi-agent projects and ensures reliable, coordinated deployments.
