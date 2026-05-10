import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    exe_name = "R-Chan"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconsole",
        "--onefile",
        "--name",
        exe_name,
        "--add-data", "resources/daily_template.xlsx;resources",
        "--add-data", "resources/poppo.ico;resources",
        "--add-data", "resources/ctu.ico;resources",
        "--add-data", "resources/rchan.ico;resources",
        "--add-data", "resources/template_weekly.xlsx;resources",
        "--icon=resources/rchan.ico",
        str(ROOT / "app.py"),
    ]
    subprocess.run(cmd, check=True, cwd=str(ROOT))


if __name__ == "__main__":
    main()

