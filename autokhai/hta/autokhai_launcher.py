import os
import tempfile
import subprocess

hta_content = r"""
<html>
<head>
<HTA:APPLICATION BORDER="thin" CAPTION="yes" SHOWINTASKBAR="yes"/>
<script>
function run(){
    var shell = new ActiveXObject("WScript.Shell");
    shell.Run("autokhai_internal.exe");
}
</script>
</head>

<body>
<button onclick="run()" style="width:120px;height:40px;">autokhai</button>
</body>
</html>
"""

# write HTA to temp
temp_dir = tempfile.gettempdir()
hta_path = os.path.join(temp_dir, "autokhai.hta")

with open(hta_path, "w", encoding="utf-8") as f:
    f.write(hta_content)

# launch HTA
subprocess.Popen(["mshta.exe", hta_path])

# pyinstaller --onefile autokhai_internal.py 
# pyinstaller --onefile --add-binary ".\dist\autokhai_internal.exe;." autokhai_launcher.py 
