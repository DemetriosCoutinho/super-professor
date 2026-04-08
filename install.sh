#!/usr/bin/env bash
# super-professor — install script
# Installs skills and agents at user level (~/.claude/)
# After installing, the skills are available in ALL Claude Code sessions.

set -e

PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "super-professor install"
echo "Plugin source: $PLUGIN_DIR"
echo "Claude user dir: $CLAUDE_DIR"
echo ""

# --- skills ---
echo "→ Installing skills..."
mkdir -p "$CLAUDE_DIR/skills"
cp "$PLUGIN_DIR/.claude/skills"/*.md "$CLAUDE_DIR/skills/"
echo "  Installed: $(ls "$PLUGIN_DIR/.claude/skills"/*.md | wc -l | tr -d ' ') skills"

# --- agents ---
echo "→ Installing agents..."
mkdir -p "$CLAUDE_DIR/agents"
cp "$PLUGIN_DIR/.claude/agents"/*.md "$CLAUDE_DIR/agents/"
echo "  Installed: $(ls "$PLUGIN_DIR/.claude/agents"/*.md | wc -l | tr -d ' ') agents"

# --- plugin data (templates + quality contracts) ---
echo "→ Installing plugin data..."
mkdir -p "$CLAUDE_DIR/super-professor/templates"
mkdir -p "$CLAUDE_DIR/super-professor/docs/contracts"
mkdir -p "$CLAUDE_DIR/super-professor/docs/qa"

cp "$PLUGIN_DIR/templates"/*.md "$CLAUDE_DIR/super-professor/templates/"
cp "$PLUGIN_DIR/docs/contracts"/*.md "$CLAUDE_DIR/super-professor/docs/contracts/"
cp "$PLUGIN_DIR/docs/qa"/*.md "$CLAUDE_DIR/super-professor/docs/qa/"
echo "  Installed: templates, contracts, quality-contracts"

echo ""
echo "Done. Run /reload-plugins in Claude Code, then use /lesson-repo-setup in any academic repository."
