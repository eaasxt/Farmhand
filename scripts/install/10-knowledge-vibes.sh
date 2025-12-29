#!/usr/bin/env bash
#
# Farmhand - Phase 10: Knowledge & Vibes Workflow Layer
#
# Installs the structured workflow system:
# - 13 base skills from knowledge_and_vibes submodule
# - 14 Farmhand-specific skills (some override K&V versions)
# - 10 K&V commands + 3 Farmhand commands
# - 3 behavior rules (beads, multi-agent, safety)
# - 8+ documentation templates
# - Protocol documentation
#

# Use local variable to avoid clobbering parent's SCRIPT_DIR when sourced
_SCRIPT_DIR_10="${SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
K_AND_V="$_SCRIPT_DIR_10/vendor/knowledge_and_vibes"

echo -e "${BLUE}[10/10] Installing Knowledge & Vibes workflow...${NC}"

# Ensure submodule is initialized
if [[ ! -d "$K_AND_V/.claude" ]]; then
    echo "    Initializing submodule..."
    git -C "$_SCRIPT_DIR_10" submodule update --init --recursive
fi

# Verify submodule has expected content
if [[ ! -d "$K_AND_V/.claude/skills" ]]; then
    echo -e "${RED}    ERROR: knowledge_and_vibes submodule missing .claude/skills${NC}"
    echo "    Try running: git submodule update --init --recursive"
    exit 1
fi

# Create target directories
mkdir -p ~/.claude/skills
mkdir -p ~/.claude/commands
mkdir -p ~/.claude/rules
mkdir -p ~/templates
mkdir -p ~/docs/protocols

# Copy K&V base skills (13 skill definitions)
echo "    Installing K&V base skills..."
cp -r "$K_AND_V/.claude/skills/"* ~/.claude/skills/

# Copy Farmhand-specific skills (14 skills, some override K&V versions)
echo "    Installing Farmhand skills..."
if [[ -d "$_SCRIPT_DIR_10/config/skills" ]]; then
    cp -r "$_SCRIPT_DIR_10/config/skills/"* ~/.claude/skills/
else
    echo -e "${YELLOW}    Warning: Farmhand skills not found at $_SCRIPT_DIR_10/config/skills${NC}"
fi

# Copy K&V commands (10 slash commands)
echo "    Installing K&V commands..."
cp -r "$K_AND_V/.claude/commands/"* ~/.claude/commands/

# Copy Farmhand-specific commands (3 additional commands)
echo "    Installing Farmhand commands..."
if [[ -d "$_SCRIPT_DIR_10/config/commands" ]]; then
    cp -r "$_SCRIPT_DIR_10/config/commands/"* ~/.claude/commands/
else
    echo -e "${YELLOW}    Warning: Farmhand commands not found at $_SCRIPT_DIR_10/config/commands${NC}"
fi

# Copy rules (3 behavior rules)
echo "    Installing 3 rules..."
cp -r "$K_AND_V/.claude/rules/"* ~/.claude/rules/

# Copy templates (8 documentation templates)
echo "    Installing 8 templates..."
cp -r "$K_AND_V/templates/"* ~/templates/

# Copy AGENTS.md template (for multi-agent coordination)
echo "    Installing AGENTS.md template..."
if [[ -f "$_SCRIPT_DIR_10/config/AGENTS.md" ]]; then
    cp "$_SCRIPT_DIR_10/config/AGENTS.md" ~/templates/AGENTS.md
    echo "    Template at ~/templates/AGENTS.md (copy to project roots)"
fi

# Copy protocol documentation
echo "    Installing protocol documentation..."
if [[ -d "$K_AND_V/docs/workflow" ]]; then
    cp "$K_AND_V/docs/workflow/"*.md ~/docs/protocols/ 2>/dev/null || true
fi

# Verify installation
SKILLS_COUNT=$(ls ~/.claude/skills/ 2>/dev/null | wc -l)
COMMANDS_COUNT=$(ls ~/.claude/commands/ 2>/dev/null | wc -l)

# Expected: 13 K&V + 14 Farmhand = ~24 skills (some overlap), 10 K&V + 3 Farmhand = 13 commands
if [[ "$SKILLS_COUNT" -ge 20 && "$COMMANDS_COUNT" -ge 10 ]]; then
    echo -e "${GREEN}    ✓ Workflow layer installed ($SKILLS_COUNT skills, $COMMANDS_COUNT commands)${NC}"
elif [[ "$SKILLS_COUNT" -ge 13 && "$COMMANDS_COUNT" -ge 7 ]]; then
    echo -e "${YELLOW}    ⚠ Partial installation: $SKILLS_COUNT skills, $COMMANDS_COUNT commands (Farmhand skills may be missing)${NC}"
else
    echo -e "${RED}    ✗ Installation incomplete: $SKILLS_COUNT skills, $COMMANDS_COUNT commands${NC}"
fi

echo ""
echo "    Available slash commands:"
echo "      /prime         - Start session, register agent, claim work"
echo "      /next-bead     - Close current task, UBS scan, claim next"
echo "      /execute       - Parallel multi-agent execution"
echo "      /calibrate     - 5-phase alignment check"
echo "      /decompose-task - Break work into test-first beads"
echo "      /ground        - Verify claims against code/docs"
echo "      /release       - End session, cleanup"
echo ""
