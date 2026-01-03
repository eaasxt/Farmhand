#!/usr/bin/env bash
set -euo pipefail

# farmhand-backup.sh - Backup Farmhand databases
# Bolt-on addition: New script, does not modify existing files
#
# Usage:
#   farmhand-backup.sh              # Backup to default location
#   farmhand-backup.sh --dir /path  # Backup to specific directory
#   farmhand-backup.sh --list       # List existing backups
#   farmhand-backup.sh --restore    # Restore from latest backup
#   farmhand-backup.sh --keep N     # Keep only last N backups (default: 7)

BACKUP_DIR="${FARMHAND_BACKUP_DIR:-$HOME/.farmhand-backups}"
KEEP_BACKUPS=7
ACTION="backup"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --keep)
            KEEP_BACKUPS="$2"
            shift 2
            ;;
        --list)
            ACTION="list"
            shift
            ;;
        --restore)
            ACTION="restore"
            shift
            ;;
        --help|-h)
            echo "Usage: farmhand-backup.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dir PATH    Backup directory (default: ~/.farmhand-backups)"
            echo "  --keep N      Keep last N backups (default: 7)"
            echo "  --list        List existing backups"
            echo "  --restore     Restore from latest backup (interactive)"
            echo "  --help        Show this help"
            echo ""
            echo "Environment:"
            echo "  FARMHAND_BACKUP_DIR    Override default backup directory"
            echo ""
            echo "Databases backed up:"
            echo "  - ~/.beads/beads.db (Beads issue tracker)"
            echo "  - ~/mcp_agent_mail/storage.sqlite3 (Agent Mail)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Database paths
BEADS_DB="${BEADS_DB:-$HOME/.beads/beads.db}"
MCP_DB="$HOME/mcp_agent_mail/storage.sqlite3"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err() { echo -e "${RED}[ERROR]${NC} $1"; }

list_backups() {
    echo "=== Farmhand Backups ==="
    echo "Location: $BACKUP_DIR"
    echo ""

    if [[ ! -d "$BACKUP_DIR" ]]; then
        echo "No backups found."
        return
    fi

    echo "Available backups:"
    ls -lt "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -20 || echo "  (none)"
    echo ""

    if [[ -d "$BACKUP_DIR" ]]; then
        echo "Total size: $(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)"
    fi
}

do_backup() {
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="farmhand_backup_${timestamp}"
    local backup_path="$BACKUP_DIR/$backup_name"

    echo "=== Farmhand Backup ==="
    echo "Timestamp: $timestamp"
    echo "Destination: $BACKUP_DIR"
    echo ""

    mkdir -p "$BACKUP_DIR"
    mkdir -p "$backup_path"

    # Backup Beads DB
    if [[ -f "$BEADS_DB" ]]; then
        echo -n "Backing up Beads DB... "
        if command -v sqlite3 &>/dev/null; then
            sqlite3 "$BEADS_DB" ".backup '$backup_path/beads.db'"
        else
            cp "$BEADS_DB" "$backup_path/beads.db"
        fi
        log_ok "$(du -h "$backup_path/beads.db" | cut -f1)"
    else
        log_warn "Beads DB not found at $BEADS_DB"
    fi

    # Backup MCP Agent Mail DB
    if [[ -f "$MCP_DB" ]]; then
        echo -n "Backing up MCP Agent Mail DB... "
        if command -v sqlite3 &>/dev/null; then
            sqlite3 "$MCP_DB" ".backup '$backup_path/mcp_storage.db'"
        else
            cp "$MCP_DB" "$backup_path/mcp_storage.db"
        fi
        log_ok "$(du -h "$backup_path/mcp_storage.db" | cut -f1)"
    else
        log_warn "MCP DB not found at $MCP_DB"
    fi

    # Backup issues.jsonl if exists
    if [[ -f "$HOME/.beads/issues.jsonl" ]]; then
        echo -n "Backing up issues.jsonl... "
        cp "$HOME/.beads/issues.jsonl" "$backup_path/issues.jsonl"
        log_ok "$(du -h "$backup_path/issues.jsonl" | cut -f1)"
    fi

    # Create tarball
    echo -n "Creating archive... "
    tar -czf "$BACKUP_DIR/${backup_name}.tar.gz" -C "$BACKUP_DIR" "$backup_name"
    rm -rf "$backup_path"
    log_ok "$BACKUP_DIR/${backup_name}.tar.gz"

    # Rotate old backups
    local backup_count
    backup_count=$(ls -1 "$BACKUP_DIR"/*.tar.gz 2>/dev/null | wc -l)
    if [[ $backup_count -gt $KEEP_BACKUPS ]]; then
        echo -n "Rotating old backups (keeping $KEEP_BACKUPS)... "
        ls -1t "$BACKUP_DIR"/*.tar.gz | tail -n +$((KEEP_BACKUPS + 1)) | xargs rm -f
        log_ok "removed $((backup_count - KEEP_BACKUPS)) old backup(s)"
    fi

    echo ""
    echo "=== Backup Complete ==="
    echo "Archive: $BACKUP_DIR/${backup_name}.tar.gz"
    echo "Size: $(du -h "$BACKUP_DIR/${backup_name}.tar.gz" | cut -f1)"
}

do_restore() {
    echo "=== Farmhand Restore ==="
    echo ""

    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_err "No backup directory found at $BACKUP_DIR"
        exit 1
    fi

    local latest
    latest=$(ls -1t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -1)

    if [[ -z "$latest" ]]; then
        log_err "No backups found in $BACKUP_DIR"
        exit 1
    fi

    echo "Latest backup: $latest"
    echo ""
    echo "This will restore:"
    echo "  - $BEADS_DB"
    echo "  - $MCP_DB"
    echo ""
    echo -e "${YELLOW}WARNING: This will overwrite current databases!${NC}"
    read -p "Continue? (yes/no): " confirm

    if [[ "$confirm" != "yes" ]]; then
        echo "Restore cancelled."
        exit 0
    fi

    if systemctl is-active --quiet mcp-agent-mail 2>/dev/null; then
        echo -n "Stopping MCP Agent Mail service... "
        sudo systemctl stop mcp-agent-mail
        log_ok "stopped"
    fi

    local tmpdir
    tmpdir=$(mktemp -d)
    echo -n "Extracting backup... "
    tar -xzf "$latest" -C "$tmpdir"
    log_ok "done"

    local extracted
    extracted=$(ls -1 "$tmpdir")

    if [[ -f "$tmpdir/$extracted/beads.db" ]]; then
        echo -n "Restoring Beads DB... "
        cp "$tmpdir/$extracted/beads.db" "$BEADS_DB"
        log_ok "done"
    fi

    if [[ -f "$tmpdir/$extracted/mcp_storage.db" ]]; then
        echo -n "Restoring MCP Agent Mail DB... "
        cp "$tmpdir/$extracted/mcp_storage.db" "$MCP_DB"
        log_ok "done"
    fi

    if [[ -f "$tmpdir/$extracted/issues.jsonl" ]]; then
        echo -n "Restoring issues.jsonl... "
        cp "$tmpdir/$extracted/issues.jsonl" "$HOME/.beads/issues.jsonl"
        log_ok "done"
    fi

    rm -rf "$tmpdir"

    if systemctl is-enabled --quiet mcp-agent-mail 2>/dev/null; then
        echo -n "Restarting MCP Agent Mail service... "
        sudo systemctl start mcp-agent-mail
        log_ok "started"
    fi

    echo ""
    echo "=== Restore Complete ==="
}

case $ACTION in
    backup) do_backup ;;
    list) list_backups ;;
    restore) do_restore ;;
esac
