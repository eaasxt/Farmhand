#!/usr/bin/env bash
#
# Farmhand Token Manager
#
# Centralized MCP bearer token lifecycle management.
# Replaces fragile /tmp storage with secure, persistent state files.
#
# Usage:
#   token-manager.sh generate      # Generate new token
#   token-manager.sh get           # Get current token
#   token-manager.sh inject        # Inject token into Claude settings
#   token-manager.sh validate      # Test MCP API with token
#   token-manager.sh rotate        # Generate new token and update all configs

set -euo pipefail

VERSION="1.0.0"
FARMHAND_DIR="$HOME/.farmhand"
CREDENTIALS_FILE="$FARMHAND_DIR/mcp-credentials.json"
MCP_CONFIG_FILE="$HOME/.claude/mcp.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create farmhand directory with secure permissions
init_farmhand_dir() {
    if [[ ! -d "$FARMHAND_DIR" ]]; then
        mkdir -p "$FARMHAND_DIR"
        chmod 700 "$FARMHAND_DIR"  # Owner only
    fi
}

# Generate a new bearer token with metadata
generate_token() {
    local token_id=$(date +%s)
    local timestamp=$(date -Iseconds)

    # Generate 256-bit token using Python or OpenSSL fallback
    local token
    if command -v python3 >/dev/null; then
        token=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    else
        token=$(openssl rand -hex 32)
    fi

    init_farmhand_dir

    # Store token with metadata in secure JSON file
    cat > "$CREDENTIALS_FILE" << JSON_EOF
{
  "mcp_bearer_token": {
    "token": "$token",
    "token_id": "$token_id",
    "generated_at": "$timestamp",
    "version": "$VERSION"
  }
}
JSON_EOF

    # Set secure permissions (read/write owner only)
    chmod 600 "$CREDENTIALS_FILE"

    echo -e "${GREEN}✓ Token generated and stored securely${NC}"
    echo -e "  ID: $token_id"
    echo -e "  File: $CREDENTIALS_FILE"

    # Export to environment for immediate use
    export FARMHAND_MCP_TOKEN="$token"

    return 0
}

# Get current token from credentials file
get_token() {
    if [[ ! -f "$CREDENTIALS_FILE" ]]; then
        echo -e "${RED}✗ No token found. Run 'token-manager.sh generate' first${NC}" >&2
        return 1
    fi

    # Extract token using jq if available, otherwise use sed
    if command -v jq >/dev/null; then
        jq -r '.mcp_bearer_token.token' "$CREDENTIALS_FILE" 2>/dev/null
    else
        sed -n 's/.*"token": "\([^"]*\)".*/\1/p' "$CREDENTIALS_FILE"
    fi
}

# Inject token into Claude Code MCP configuration
inject_token() {
    local token
    if ! token=$(get_token); then
        echo -e "${RED}✗ Cannot inject: no token available${NC}" >&2
        return 1
    fi

    if [[ -z "$token" ]]; then
        echo -e "${RED}✗ Token is empty or invalid${NC}" >&2
        return 1
    fi

    # Ensure Claude directory exists
    mkdir -p "$HOME/.claude"

    # Check if template exists
    local template_file="/home/ubuntu/Farmhand/config/mcp.json.template"
    if [[ ! -f "$template_file" ]]; then
        echo -e "${RED}✗ MCP template not found: $template_file${NC}" >&2
        return 1
    fi

    # Backup existing config if present
    if [[ -f "$MCP_CONFIG_FILE" ]]; then
        cp "$MCP_CONFIG_FILE" "$MCP_CONFIG_FILE.bak"
        echo -e "${YELLOW}  Backed up existing MCP config${NC}"
    fi

    # Inject token into template
    sed "s/YOUR_TOKEN_HERE/$token/g" "$template_file" > "$MCP_CONFIG_FILE"

    # Set secure permissions
    chmod 600 "$MCP_CONFIG_FILE"

    echo -e "${GREEN}✓ Token injected into Claude MCP configuration${NC}"
    echo -e "  Config: $MCP_CONFIG_FILE"

    return 0
}

# Validate token by testing MCP API connectivity
validate_token() {
    local token
    if ! token=$(get_token); then
        echo -e "${RED}✗ Cannot validate: no token available${NC}" >&2
        return 1
    fi

    echo -e "${BLUE}Testing MCP API connectivity...${NC}"

    # Test if MCP Agent Mail server is running
    if ! curl -s -f http://127.0.0.1:8765/health >/dev/null 2>&1; then
        echo -e "${RED}✗ MCP Agent Mail server not responding on :8765${NC}" >&2
        echo -e "  Try: sudo systemctl restart mcp-agent-mail"
        return 1
    fi

    # Test bearer token authentication
    local response
    if response=$(curl -s -H "Authorization: Bearer $token" \
                       -H "Content-Type: application/json" \
                       -d '{"jsonrpc": "2.0", "method": "ping", "id": 1}' \
                       http://127.0.0.1:8765/mcp/ 2>&1); then

        # Check if response contains error
        if echo "$response" | grep -q '"error"'; then
            echo -e "${RED}✗ Token authentication failed${NC}" >&2
            echo -e "  Response: $response"
            return 1
        else
            echo -e "${GREEN}✓ Token authentication successful${NC}"
            echo -e "  MCP API responding correctly"
            return 0
        fi
    else
        echo -e "${RED}✗ MCP API call failed${NC}" >&2
        echo -e "  Error: $response"
        return 1
    fi
}

# Rotate token (generate new + update all configs)
rotate_token() {
    echo -e "${BLUE}Rotating MCP bearer token...${NC}"

    # Generate new token
    generate_token

    # Inject into Claude config
    inject_token

    # Update MCP Agent Mail .env file
    local mcp_env_file="$HOME/mcp_agent_mail/.env"
    if [[ -f "$mcp_env_file" ]]; then
        local new_token
        new_token=$(get_token)

        # Backup existing .env
        cp "$mcp_env_file" "$mcp_env_file.bak"

        # Update token in .env file
        if grep -q '^HTTP_BEARER_TOKEN=' "$mcp_env_file"; then
            sed -i "s/^HTTP_BEARER_TOKEN=.*/HTTP_BEARER_TOKEN=$new_token/" "$mcp_env_file"
        else
            echo "HTTP_BEARER_TOKEN=$new_token" >> "$mcp_env_file"
        fi

        echo -e "${GREEN}✓ Updated MCP Agent Mail .env file${NC}"
        echo -e "${YELLOW}  MCP Agent Mail server restart required:${NC}"
        echo -e "    sudo systemctl restart mcp-agent-mail"
    fi

    # Validate new setup
    echo ""
    validate_token
}

# Show usage information
show_usage() {
    cat << USAGE_EOF
Farmhand Token Manager v$VERSION

Secure MCP bearer token lifecycle management

USAGE:
    token-manager.sh COMMAND

COMMANDS:
    generate    Generate new bearer token and store securely
    get         Display current token
    inject      Inject token into Claude Code MCP configuration
    validate    Test MCP API connectivity with current token
    rotate      Generate new token and update all configurations

EXAMPLES:
    token-manager.sh generate          # First-time setup
    token-manager.sh inject            # Configure Claude Code
    token-manager.sh validate          # Test API connectivity
    token-manager.sh rotate            # Security token refresh

FILES:
    $CREDENTIALS_FILE    # Secure token storage (600 perms)
    $MCP_CONFIG_FILE            # Claude Code MCP config

ENVIRONMENT:
    FARMHAND_MCP_TOKEN             # Exported by generate command

USAGE_EOF
}

# Main command dispatcher
main() {
    case "${1:-}" in
        generate)
            generate_token
            ;;
        get)
            get_token
            ;;
        inject)
            inject_token
            ;;
        validate)
            validate_token
            ;;
        rotate)
            rotate_token
            ;;
        -h|--help|help)
            show_usage
            ;;
        "")
            echo -e "${RED}✗ No command specified${NC}" >&2
            echo ""
            show_usage
            exit 1
            ;;
        *)
            echo -e "${RED}✗ Unknown command: $1${NC}" >&2
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
