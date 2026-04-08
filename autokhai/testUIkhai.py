import win32com.client

ie = win32com.client.Dispatch("InternetExplorer.Application")
ie.Visible = True
ie.Navigate("about:blank")

while ie.ReadyState != 4:
    pass

ie.Document.Write("""
<html>
<button onclick="alert('Hello')">autokhai</button>
</html>
""")