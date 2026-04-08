Sub FindReportEmailsAllFolders_Sorted()

    Dim ns As Outlook.NameSpace
    Dim rootFolder As Outlook.MAPIFolder
    Dim keyword As String
    Dim startDateStr As String, endDateStr As String
    Dim startDate As Date, endDate As Date
    Dim allMails As Collection
    Dim newMail As Outlook.MailItem
    
    ' Ask user for keyword
    keyword = InputBox("Enter keyword to search:", "Search", "")
    If keyword = "" Then Exit Sub
    
    ' Ask user for date range
    startDateStr = InputBox("Nhap ngay bat dau :", "Tu ngay", Format(Date, "yyyy-mm-dd"))
    If startDateStr = "" Then Exit Sub
    endDateStr = InputBox("Nhap ngay ket thuc :", "Toi ngay", Format(Date, "yyyy-mm-dd"))
    If endDateStr = "" Then Exit Sub
    
    ' Convert to Date type
    startDate = CDate(startDateStr)
    endDate = CDate(endDateStr) + 1 - TimeSerial(0, 0, 1) ' include full end day
    
    Set ns = Application.GetNamespace("MAPI")
    Set rootFolder = ns.GetDefaultFolder(olFolderInbox).Parent ' mailbox root
    Set allMails = New Collection
    
    ' Recursively collect matched mails
    Call CollectMails(rootFolder, keyword, startDate, endDate, allMails)
    
    If allMails.Count = 0 Then
    MsgBox "No mails found!!!", vbInformation
        Exit Sub
    End If
    
    ' Sort mails by ReceivedTime descending
    Dim sortedMails() As Object
    sortedMails = SortMailsByDate(allMails)
    
    ' Build HTML table with each email as a column
    Dim result As String
    Dim i As Long
    
    result = "<h3>Search Results for '" & keyword & "' from " & Format(startDate, "yyyy-mm-dd") & " to " & Format(endDate, "yyyy-mm-dd") & "</h3>"
    result = result & "<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;'>"
    
    ' First row: field names
    result = result & "<tr style='background-color:#f2f2f2;'>"
    result = result & "<th>Field</th>"
    For i = LBound(sortedMails) To UBound(sortedMails)
        result = result & "<th>Email " & i & "</th>"
    Next i
    result = result & "</tr>"
    
    ' Rows: Subject, Sender, Date, Time, Folder
    Dim fields As Variant
    fields = Array("Subject", "Time")
    
    Dim f As Long
    For f = LBound(fields) To UBound(fields)
        result = result & "<tr>"
        result = result & "<td style='background-color:#f9f9f9;'><b>" & fields(f) & "</b></td>"
        
        For i = LBound(sortedMails) To UBound(sortedMails)
            Dim mail As Outlook.MailItem
            Set mail = sortedMails(i)
            
            Select Case fields(f)
                Case "Subject"
                    result = result & "<td><a href='outlook:" & mail.EntryID & "'>" & mail.Subject & "</a></td>"
                Case "Time"
                    result = result & "<td>" & Format(mail.ReceivedTime, "HH:nn AM/PM") & "</td>"
            End Select
        Next i
        
        result = result & "</tr>"
    Next f
    
    result = result & "</table>"
    
    ' Build HTML table
    result = result & "<br />"
    result = result & "<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;'>"
    result = result & "<tr style='background-color:#f2f2f2;'><th>STT</th><th>Subject</th><th>Sender</th><th>Date</th><th>Time</th><th>Folder</th></tr>"
    For i = LBound(sortedMails) To UBound(sortedMails)
      Dim email As Outlook.MailItem
      Set email = sortedMails(i)
      result = result & "<tr>"
      result = result & "<td>" & i & "</td>"
      result = result & "<td><a href='outlook:" & mail.EntryID & "'>" & email.Subject & "</a></td>"
      result = result & "<td>" & email.SenderName & "</td>"
      result = result & "<td>" & Format(email.ReceivedTime, "yyyy-mm-dd") & "</td>"
      result = result & "<td>" & Format(email.ReceivedTime, "HH:nn AM/PM") & "</td>"
      result = result & "<td>" & email.Parent.FolderPath & "</td>"
      result = result & "</tr>"
    Next i
    result = result & "</table>"
        ' Create new mail with results
        Set newMail = Application.CreateItem(olMailItem)
        newMail.Subject = "Search Result: " & keyword
        newMail.HTMLBody = result
        newMail.Display

End Sub

'--- Collect matched mails into a collection
Sub CollectMails(f As Outlook.MAPIFolder, keyword As String, startDate As Date, endDate As Date, allMails As Collection)
    Dim mail As Object
    Dim subF As Outlook.MAPIFolder
    
    ' Skip Junk and Deleted Items
    If f.DefaultItemType = olMailItem Then
        If f.Name = "Junk E-mail" Or f.Name = "Deleted Items" Then Exit Sub
    End If
    
    ' Collect mails in this folder
    For Each mail In f.Items
        If TypeOf mail Is Outlook.MailItem Then
            If (InStr(1, LCase(mail.Subject), LCase(keyword)) > 0 _
            Or InStr(1, LCase(mail.Body), LCase(keyword)) > 0 _
            Or InStr(1, LCase(mail.SenderName), LCase(keyword)) > 0) _
            And mail.ReceivedTime >= startDate And mail.ReceivedTime <= endDate Then
                
                allMails.Add mail
            End If
        End If
    Next mail
    
    ' Recurse into subfolders
    For Each subF In f.Folders
        Call CollectMails(subF, keyword, startDate, endDate, allMails)
    Next subF
End Sub

'--- Sort mails by ReceivedTime descending
Function SortMailsByDate(mails As Collection) As Variant
    Dim arr() As Object
    Dim i As Long, j As Long
    Dim temp As Object
    
    ReDim arr(1 To mails.Count)
    
    ' Copy collection to array
    For i = 1 To mails.Count
        Set arr(i) = mails(i)
    Next i
    
    ' Simple bubble sort (ascending)
    For i = 1 To UBound(arr) - 1
        For j = i + 1 To UBound(arr)
            If arr(i).ReceivedTime > arr(j).ReceivedTime Then
                Set temp = arr(i)
                Set arr(i) = arr(j)
                Set arr(j) = temp
            End If
        Next j
    Next i
    
    SortMailsByDate = arr
End Function



