import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    exe_name = "autoR"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconsole",
        "--onefile",
        "--name",
        exe_name,
        str(ROOT / "app.py"),
    ]
    subprocess.run(cmd, check=True, cwd=str(ROOT))


if __name__ == "__main__":
    main()

