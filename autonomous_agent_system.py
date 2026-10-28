#!/usr/bin/env python3
"""
AUTONOMOUS AGENT SYSTEM
No spiritual nonsense - actual working code
"""

import subprocess
import shlex
import json
import time
from pathlib import Path

class AutonomousAgent:
    def __init__(self):
        self.id = "evez-unix-shell-to-millionaire"
        self.state = "running"
        
    def execute_task(self, command):
        """Execute only read-only inspection commands; arbitrary shell is disabled."""
        if not isinstance(command, str) or any(op in command for op in (";", "|", "&", ">", "<", "`", "$", "\n", "\r")):
            return {"stdout": "", "stderr": "Shell syntax is blocked", "returncode": 2}
        try:
            argv = shlex.split(command)
        except ValueError as exc:
            return {"stdout": "", "stderr": str(exc), "returncode": 2}
        if not argv:
            return {"stdout": "", "stderr": "Command required", "returncode": 2}
        if argv[0] == "pwd" and len(argv) == 1:
            pass
        elif argv[0] == "ls":
            pass
        elif argv[0] == "git" and len(argv) >= 2 and argv[1] in {"status", "diff"}:
            if len(argv) > 2:
                return {"stdout": "", "stderr": "Git arguments are blocked", "returncode": 2}
        else:
            return {"stdout": "", "stderr": "Allowed commands: pwd, ls, git status, git diff", "returncode": 2}
        result = subprocess.run(argv, shell=False, capture_output=True, text=True, timeout=30)
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    
    def git_operation(self, repo_path, operation):
        """Autonomous git operations"""
        cmd = f"cd {repo_path} && git {operation}"
        return self.execute_task(cmd)
    
    def file_sync(self, source, dest):
        """Keep files synchronized"""
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(Path(source).read_text())
        return f"Synced {source} -> {dest}"

if __name__ == "__main__":
    agent = AutonomousAgent()
    
    # Actual useful work
    result = agent.git_operation("/root/.openclaw/workspace", "status")
    print("Git status:", result["stdout"][:200] if result["stdout"] else "No changes")
    
    print("\nAGENT RUNNING - NO NONSENSE")