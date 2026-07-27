import os
import subprocess
import sys
from pathlib import Path


class ExecutorAgent:
    def run(self, test_path: str) -> dict:
        project_root = Path(__file__).resolve().parents[2]
        command = [sys.executable, "-m", "pytest", "-q", test_path]
        completed = subprocess.run(
            command,
            cwd=str(project_root),
            env=os.environ.copy(),
            text=True,
            capture_output=True,
        )
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "command": " ".join(command),
        }
