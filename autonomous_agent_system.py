#!/usr/bin/env python3
"""
AUTONOMOUS AGENT SYSTEM
No spiritual nonsense - actual working code
"""

import subprocess
import shlex
import os
import json
import time
from pathlib import Path

class AutonomousAgent:
    def __init__(self):
        self.id = "evez-unix-shell-to-millionaire"
        self.state = "running"
        self.workspace = Path(os.environ.get("EVEZ_WORKSPACE_ROOT", str(Path.home() / ".openclaw" / "workspace"))).expanduser().resolve()
        
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
        """Allow only fixed read-only Git operations in the configured workspace."""
        if operation not in {"status", "diff", "log"}:
            return {"stdout": "", "stderr": "Only git status, diff, and log are allowed", "returncode": 2}
        try:
            root = self.workspace.resolve()
            repo = Path(repo_path).expanduser().resolve()
            if repo != root and root not in repo.parents:
                raise PermissionError("Repository path is outside EVEZ_WORKSPACE_ROOT")
            result = subprocess.run(
                ["git", operation], cwd=str(repo), shell=False,
                capture_output=True, text=True, timeout=30
            )
            return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
        except (OSError, ValueError, PermissionError, subprocess.TimeoutExpired) as exc:
            return {"stdout": "", "stderr": str(exc), "returncode": 1}

    def file_sync(self, source, dest):
        """Copy files only between paths inside the configured workspace."""
        root = self.workspace.resolve()
        src_arg = Path(source).expanduser()
        dst_arg = Path(dest).expanduser()
        src = (root / src_arg if not src_arg.is_absolute() else src_arg).resolve()
        dst = (root / dst_arg if not dst_arg.is_absolute() else dst_arg).resolve()
        if root not in src.parents or root not in dst.parents:
            raise PermissionError("Source and destination must be inside EVEZ_WORKSPACE_ROOT")
        if not src.is_file():
            raise ValueError("Source must be an existing file")
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst = dst.resolve()
        if root not in dst.parents:
            raise PermissionError("Destination escaped EVEZ_WORKSPACE_ROOT")
        dst.write_text(src.read_text())
        return f"Synced {src} -> {dst}"

if __name__ == "__main__":
    agent = AutonomousAgent()
    
    # Actual useful work
    result = agent.git_operation(str(agent.workspace), "status")
    print("Git status:", result["stdout"][:200] if result["stdout"] else "No changes")
    
    print("\nAGENT RUNNING - NO NONSENSE")