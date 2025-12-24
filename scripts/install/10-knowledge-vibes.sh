#!/usr/bin/env bash
#
# JohnDeere - Phase 10: Knowledge & Vibes Workflow Layer
#
# Installs the structured workflow system from knowledge_and_vibes:
# - 18 skills for common development patterns
# - 7 slash commands (/prime, /calibrate, /execute, etc.)
# - 3 behavior rules (beads, multi-agent, safety)
# - 8 documentation templates
# - Protocol documentation
#

K_AND_V="$SCRIPT_DIR/vendor/knowledge_and_vibes"

echo -e "${BLUE}[10/10] Installing Knowledge & Vibes workflow...${NC}"

# Ensure submodule is initialized
if [[ ! -d "$K_AND_V/.claude" ]]; then
    echo "    Initializing submodule..."
    git -C "$SCRIPT_DIR" submodule update --init --recursive
fi

# Verify submodule has expected content
if [[ ! -d "$K_AND_V/.claude/skills" ]]; then
    echo -e "${RED}    ERROR: knowledge_and_vibes submodule missing .claude/skills${NC}"
    echo "    Try running: git submodule update --init --recursive"
    return 1
fi

# Create target directories
mkdir -p ~/.claude/skills
mkdir -p ~/.claude/commands
mkdir -p ~/.claude/rules
mkdir -p ~/templates
mkdir -p ~/docs/protocols

# Copy skills (18 skill definitions)
echo "    Installing 18 skills..."
cp -r "$K_AND_V/.claude/skills/"* ~/.claude/skills/

# Copy commands (7 slash commands)
echo "    Installing 7 commands..."
cp -r "$K_AND_V/.claude/commands/"* ~/.claude/commands/

# Copy rules (3 behavior rules)
echo "    Installing 3 rules..."
cp -r "$K_AND_V/.claude/rules/"* ~/.claude/rules/

# Copy templates (8 documentation templates)
echo "    Installing 8 templates..."
cp -r "$K_AND_V/templates/"* ~/templates/

# Copy protocol documentation
echo "    Installing protocol documentation..."
if [[ -d "$K_AND_V/docs/workflow" ]]; then
    cp "$K_AND_V/docs/workflow/"*.md ~/docs/protocols/ 2>/dev/null || true
fi

# Verify installation
SKILLS_COUNT=$(ls ~/.claude/skills/ 2>/dev/null | wc -l)
COMMANDS_COUNT=$(ls ~/.claude/commands/ 2>/dev/null | wc -l)

if [[ "$SKILLS_COUNT" -ge 10 && "$COMMANDS_COUNT" -ge 5 ]]; then
    echo -e "${GREEN}    ✓ Knowledge & Vibes installed ($SKILLS_COUNT skills, $COMMANDS_COUNT commands)${NC}"
else
    echo -e "${YELLOW}    ⚠ Partial installation: $SKILLS_COUNT skills, $COMMANDS_COUNT commands${NC}"
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
