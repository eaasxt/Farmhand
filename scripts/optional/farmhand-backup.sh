#!/usr/bin/env bash
# farmhand-backup.sh - Automated backup for Farmhand databases
# Part of Farmhand optional utilities (bolt-on, opt-in)
#
# Usage:
#   ./farmhand-backup.sh              # Run backup now
#   ./farmhand-backup.sh --list       # List available backups
#   ./farmhand-backup.sh --restore    # Interactive restore
#   ./farmhand-backup.sh --prune 30   # Delete backups older than 30 days
#
# Install as systemd timer (optional):
#   sudo cp systemd/farmhand-backup.* /etc/systemd/system/
#   sudo systemctl enable --now farmhand-backup.timer

set -uo pipefail

# Configuration (override via environment)
BACKUP_DIR="${FARMHAND_BACKUP_DIR:-$HOME/.farmhand-backups}"
RETENTION_DAYS="${FARMHAND_BACKUP_RETENTION:-30}"
BEADS_DB="${BEADS_DB:-$HOME/.beads/beads.db}"
MCP_MAIL_DB="$HOME/mcp_agent_mail/storage.sqlite3"
COMPRESS="${FARMHAND_BACKUP_COMPRESS:-true}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --list         List available backups"
    echo "  --restore      Interactive restore from backup"
    echo "  --prune N      Delete backups older than N days (default: $RETENTION_DAYS)"
    echo "  --dry-run      Show what would be backed up without doing it"
    echo "  --help         Show this help"
    echo ""
    echo "Environment:"
    echo "  FARMHAND_BACKUP_DIR        Backup directory (default: ~/.farmhand-backups)"
    echo "  FARMHAND_BACKUP_RETENTION  Days to keep backups (default: 30)"
    echo "  FARMHAND_BACKUP_COMPRESS   Compress backups (default: true)"
}

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

ensure_backup_dir() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        mkdir -p "$BACKUP_DIR"
        chmod 700 "$BACKUP_DIR"
        log_info "Created backup directory: $BACKUP_DIR"
    fi
}

backup_database() {
    local db_path="$1"
    local db_name="$2"
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    
    if [[ ! -f "$db_path" ]]; then
        log_warn "Database not found: $db_path"
        return 1
    fi
    
    local backup_file="$BACKUP_DIR/${db_name}_${timestamp}.db"
    
    # Use SQLite's backup command for consistency
    if command -v sqlite3 &>/dev/null; then
        if sqlite3 "$db_path" ".backup '$backup_file'" 2>/dev/null; then
            if [[ "$COMPRESS" == "true" ]] && command -v gzip &>/dev/null; then
                gzip "$backup_file"
                backup_file="${backup_file}.gz"
            fi
            log_success "Backed up $db_name -> $(basename "$backup_file")"
            return 0
        else
            log_error "SQLite backup failed for $db_name"
            return 1
        fi
    else
        # Fallback to cp
        if cp "$db_path" "$backup_file"; then
            if [[ "$COMPRESS" == "true" ]] && command -v gzip &>/dev/null; then
                gzip "$backup_file"
                backup_file="${backup_file}.gz"
            fi
            log_success "Copied $db_name -> $(basename "$backup_file")"
            return 0
        else
            log_error "Copy failed for $db_name"
            return 1
        fi
    fi
}

run_backup() {
    local dry_run="${1:-false}"
    
    ensure_backup_dir
    
    echo ""
    log_info "Starting Farmhand backup - $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    local success=0
    local failed=0
    local total=0
    
    # Backup beads database
    if [[ -f "$BEADS_DB" ]]; then
        if [[ "$dry_run" == "true" ]]; then
            log_info "[DRY-RUN] Would backup: $BEADS_DB"
        else
            backup_database "$BEADS_DB" "beads" && ((success++)) || ((failed++))
        fi
    else
        log_warn "Beads database not found: $BEADS_DB"
    fi
    
    # Backup MCP Agent Mail database
    if [[ -f "$MCP_MAIL_DB" ]]; then
        if [[ "$dry_run" == "true" ]]; then
            log_info "[DRY-RUN] Would backup: $MCP_MAIL_DB"
        else
            backup_database "$MCP_MAIL_DB" "mcp-agent-mail" && ((success++)) || ((failed++))
        fi
    else
        log_warn "MCP Agent Mail database not found: $MCP_MAIL_DB"
    fi
    
    # Backup agent state
    local state_file="$HOME/.claude/agent-state.json"
    if [[ -f "$state_file" ]]; then
        if [[ "$dry_run" == "true" ]]; then
            log_info "[DRY-RUN] Would backup: $state_file"
        else
            local timestamp
            timestamp=$(date +%Y%m%d_%H%M%S)
            cp "$state_file" "$BACKUP_DIR/agent-state_${timestamp}.json"
            log_success "Backed up agent-state.json"
            ((success++))
        fi
    fi
    
    echo ""
    if [[ "$dry_run" != "true" ]]; then
        log_info "Backup complete: $success succeeded, $failed failed"
        log_info "Backups stored in: $BACKUP_DIR"
    fi
    
    return $failed
}

list_backups() {
    ensure_backup_dir
    
    echo ""
    log_info "Available backups in $BACKUP_DIR:"
    echo ""
    
    if [[ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]]; then
        log_warn "No backups found"
        return 0
    fi
    
    # Group by database type
    for db_type in beads mcp-agent-mail agent-state; do
        local files
        files=$(ls -1t "$BACKUP_DIR"/${db_type}_*.* 2>/dev/null || true)
        if [[ -n "$files" ]]; then
            echo -e "${BLUE}$db_type:${NC}"
            echo "$files" | while read -r f; do
                local size
                size=$(du -h "$f" | cut -f1)
                local date
                date=$(stat -c %y "$f" 2>/dev/null | cut -d'.' -f1 || stat -f %Sm "$f" 2>/dev/null)
                echo "  $(basename "$f") ($size) - $date"
            done
            echo ""
        fi
    done
}

restore_backup() {
    ensure_backup_dir
    
    echo ""
    log_info "Available backups:"
    echo ""
    
    local backups=()
    local i=1
    
    while IFS= read -r f; do
        [[ -z "$f" ]] && continue
        backups+=("$f")
        local size
        size=$(du -h "$f" | cut -f1)
        echo "  $i) $(basename "$f") ($size)"
        ((i++))
    done < <(ls -1t "$BACKUP_DIR"/*.db* "$BACKUP_DIR"/*.json 2>/dev/null)
    
    if [[ ${#backups[@]} -eq 0 ]]; then
        log_warn "No backups available to restore"
        return 1
    fi
    
    echo ""
    read -rp "Enter backup number to restore (or 'q' to quit): " choice
    
    if [[ "$choice" == "q" ]]; then
        return 0
    fi
    
    if ! [[ "$choice" =~ ^[0-9]+$ ]] || [[ $choice -lt 1 ]] || [[ $choice -gt ${#backups[@]} ]]; then
        log_error "Invalid selection"
        return 1
    fi
    
    local backup_file="${backups[$((choice-1))]}"
    local basename
    basename=$(basename "$backup_file")
    
    # Determine destination
    local dest=""
    if [[ "$basename" == beads_* ]]; then
        dest="$BEADS_DB"
    elif [[ "$basename" == mcp-agent-mail_* ]]; then
        dest="$MCP_MAIL_DB"
    elif [[ "$basename" == agent-state_* ]]; then
        dest="$HOME/.claude/agent-state.json"
    else
        log_error "Unknown backup type: $basename"
        return 1
    fi
    
    echo ""
    log_warn "This will overwrite: $dest"
    read -rp "Are you sure? (yes/no): " confirm
    
    if [[ "$confirm" != "yes" ]]; then
        log_info "Restore cancelled"
        return 0
    fi
    
    # Create backup of current file
    if [[ -f "$dest" ]]; then
        cp "$dest" "${dest}.pre-restore"
        log_info "Created pre-restore backup: ${dest}.pre-restore"
    fi
    
    # Restore
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" > "$dest"
    else
        cp "$backup_file" "$dest"
    fi
    
    log_success "Restored: $basename -> $dest"
}

prune_backups() {
    local days="${1:-$RETENTION_DAYS}"
    
    ensure_backup_dir
    
    log_info "Pruning backups older than $days days..."
    
    local count=0
    while IFS= read -r f; do
        [[ -z "$f" ]] && continue
        rm -f "$f"
        log_info "Deleted: $(basename "$f")"
        ((count++))
    done < <(find "$BACKUP_DIR" -type f -mtime +"$days" 2>/dev/null)
    
    if [[ $count -eq 0 ]]; then
        log_info "No old backups to prune"
    else
        log_success "Pruned $count old backup(s)"
    fi
}

main() {
    local action="backup"
    local dry_run="false"
    local prune_days=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --list)
                action="list"
                shift
                ;;
            --restore)
                action="restore"
                shift
                ;;
            --prune)
                action="prune"
                prune_days="${2:-$RETENTION_DAYS}"
                shift 2 || shift
                ;;
            --dry-run)
                dry_run="true"
                shift
                ;;
            --help|-h)
                usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    case $action in
        backup)
            run_backup "$dry_run"
            ;;
        list)
            list_backups
            ;;
        restore)
            restore_backup
            ;;
        prune)
            prune_backups "$prune_days"
            ;;
    esac
}

main "$@"
