"""openclaw.policy — YAML allowlist loader + capability enforcer."""
import yaml
import shlex
from pathlib import Path

DEFAULT_POLICY = {
    "capabilities": {
        "FS_READ": {"allow_paths": ["./runs", "./fixtures", "./state"]},
        "FS_WRITE": {"allow_paths": ["./runs", "./state"]},
        "SHELL": {"allow_commands": ["pwd", "ls", "cat", "echo"], "workdir_jail": "./sandboxes"},
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
    target = Path(path).expanduser().resolve()
    allowed = policy["capabilities"]["FS_READ"].get("allow_paths", [])
    for item in allowed:
        root = Path(item).expanduser().resolve()
        if target == root or root in target.parents:
            return True
    return False


def assert_fs_write(policy: dict, path: str) -> bool:
    target = Path(path).expanduser().resolve()
    allowed = policy["capabilities"]["FS_WRITE"].get("allow_paths", [])
    for item in allowed:
        root = Path(item).expanduser().resolve()
        if target == root or root in target.parents:
            return True
    return False


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
    if argv[0] in {"python", "python3", "ffmpeg", "bash", "sh", "zsh"}:
        return False
    if argv[0] == "pwd":
        return len(argv) == 1
    jail = Path(policy["capabilities"]["SHELL"].get("workdir_jail", "./sandboxes")).resolve()
    if argv[0] == "echo":
        return True
    for arg in argv[1:]:
        if arg.startswith("-"):
            allowed_options = {"-l", "-a", "-la", "-al", "-n"}
            if arg not in allowed_options:
                return False
            continue
        target = Path(arg).expanduser()
        if not target.is_absolute():
            target = jail / target
        target = target.resolve()
        if target != jail and jail not in target.parents:
            return False
    return True
