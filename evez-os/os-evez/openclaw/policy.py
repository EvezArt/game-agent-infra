"""openclaw.policy — YAML allowlist loader + capability enforcer."""
import yaml
import shlex
from pathlib import Path

DEFAULT_POLICY = {
    "capabilities": {
        "FS_READ": {"allow_paths": ["./runs", "./fixtures", "./state"]},
        "FS_WRITE": {"allow_paths": ["./runs", "./state"]},
        "SHELL": {"allow_commands": ["ls", "cat", "echo", "python", "ffmpeg"], "workdir_jail": "./sandboxes"},
        "NET_OUT": {"enabled": False},
    },
    "kill_switch": {"stop_file": "./state/STOP"},
    "budgets": {"max_runtime_seconds": 1800, "max_disk_mb": 512, "max_net_mb": 0},
}


def load_policy(policy_path: Path | None = None) -> dict:
    if policy_path and Path(policy_path).exists():
        with open(policy_path) as f:
            return yaml.safe_load(f)
    return DEFAULT_POLICY


def check_kill_switch(policy: dict, data_dir: Path) -> bool:
    stop_file = Path(data_dir) / "STOP"
    return stop_file.exists()


def assert_fs_read(policy: dict, path: str) -> bool:
    allowed = policy["capabilities"]["FS_READ"].get("allow_paths", [])
    return any(path.startswith(p) for p in allowed)


def assert_fs_write(policy: dict, path: str) -> bool:
    allowed = policy["capabilities"]["FS_WRITE"].get("allow_paths", [])
    return any(path.startswith(p) for p in allowed)


def assert_shell(policy: dict, cmd: str) -> bool:
    """Reject shell operators; only the first executable may come from policy."""
    if not isinstance(cmd, str) or not cmd.strip():
        return False
    if any(op in cmd for op in (";", "|", "&", ">", "<", chr(96), "$", "\\n", "\\r")):
        return False
    try:
        argv = shlex.split(cmd)
    except ValueError:
        return False
    allowed = policy["capabilities"]["SHELL"].get("allow_commands", [])
    if not argv or argv[0] not in allowed:
        return False
    if argv[0] == "python":
        return False
    if argv[0] == "pwd":
        return len(argv) == 1
    return True
