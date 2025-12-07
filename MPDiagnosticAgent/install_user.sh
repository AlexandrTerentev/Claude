#!/bin/bash
# User installation script for MPDiagnosticAgent
# Creates 'agent_ran' command in ~/bin (no sudo required)

set -e

echo "🚁 MPDiagnosticAgent User Installation"
echo "======================================"
echo ""

# Get absolute path to this script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MAIN_PY="$SCRIPT_DIR/main.py"

# Check if main.py exists
if [ ! -f "$MAIN_PY" ]; then
    echo "❌ Error: main.py not found in $SCRIPT_DIR"
    exit 1
fi

echo "📂 Installation directory: $SCRIPT_DIR"
echo ""

# Create ~/bin if it doesn't exist
mkdir -p "$HOME/bin"

# Create wrapper script
WRAPPER="$HOME/bin/agent_ran"

echo "📝 Creating command 'agent_ran' in ~/bin..."

# Create wrapper
cat > "$WRAPPER" <<EOF
#!/bin/bash
# MPDiagnosticAgent launcher
cd "$SCRIPT_DIR"
python3 "$MAIN_PY" "\$@"
EOF

# Make executable
chmod +x "$WRAPPER"

echo "✅ Installation complete!"
echo ""

# Check if ~/bin is in PATH
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo "⚠️  WARNING: ~/bin is not in your PATH"
    echo ""
    echo "Add this to your ~/.bashrc:"
    echo "  export PATH=\"\$HOME/bin:\$PATH\""
    echo ""
    echo "Then run: source ~/.bashrc"
    echo ""
fi

echo "Usage:"
echo "  agent_ran              - Launch GUI"
echo "  agent_ran --help       - Show help"
echo "  agent_ran --cli        - Launch CLI mode"
echo ""
echo "You can now run 'agent_ran' from anywhere!"
