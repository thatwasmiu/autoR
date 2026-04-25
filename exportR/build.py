import subprocess

cmd = [
    "pyinstaller",
    "--clean",
    "--onefile",
    "--noconsole",
    "--name", "eportR",
    "--add-data", "resources/daily_template.xlsx;resources",
    "--add-data", "resources/logo.ico;resources",
    "--add-data", "resources/template_weekly.xlsx;resources",
    "--icon=resources/logo.ico",
    "main.py"
]

subprocess.run(cmd, check=True)