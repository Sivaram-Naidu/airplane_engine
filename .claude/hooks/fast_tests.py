"""PostToolUse hook: after a Write/Edit to a .py file, run the fast test suite.

Reads the hook payload (JSON) from stdin. Never runs slow tests. On failure, prints the
pytest output to stderr and exits 2 so Claude Code feeds it back to the model.
"""
import json
import os
import subprocess
import sys

try:
    payload = json.load(sys.stdin)
except ValueError:
    sys.exit(0)
path = (payload.get("tool_input") or {}).get("file_path", "") or ""
if not path.endswith(".py"):
    sys.exit(0)

root = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
r = subprocess.run([sys.executable, "-m", "pytest", "-m", "not slow", "-q", "--no-header"],
                   cwd=root, capture_output=True, text=True)
if r.returncode not in (0, 5):  # 5 = no tests collected
    sys.stderr.write("Fast tests FAILED after editing " + path + ":\n" + r.stdout[-3000:] + r.stderr[-1000:])
    sys.exit(2)
sys.exit(0)
