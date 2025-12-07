#!/bin/bash
# Installation script for MPDiagnosticAgent
# Creates global 'mpdiag' command

set -e

echo "🚁 MPDiagnosticAgent Installation"
echo "=================================="
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

# Create wrapper script
WRAPPER="/usr/local/bin/mpdiag"

echo "📝 Creating global command 'mpdiag'..."

# Create wrapper (requires sudo)
sudo tee "$WRAPPER" > /dev/null <<EOF
#!/bin/bash
# MPDiagnosticAgent launcher
cd "$SCRIPT_DIR"
python3 "$MAIN_PY" "\$@"
EOF

# Make executable
sudo chmod +x "$WRAPPER"

echo "✅ Installation complete!"
echo ""
echo "Usage:"
echo "  mpdiag              - Launch GUI"
echo "  mpdiag --help       - Show help"
echo ""
echo "You can now run 'mpdiag' from anywhere!"
