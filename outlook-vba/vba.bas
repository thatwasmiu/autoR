Sub FindReportEmailsAllFolders_Sorted()

    Dim ns As Outlook.NameSpace
    Dim rootFolder As Outlook.MAPIFolder
    Dim startDateStr As String, endDateStr As String
    Dim startDate As Date, endDate As Date
    Dim newMail As Outlook.MailItem
    
    Dim keywordInput As String
    Dim keywords() As String
    Dim i As Long, r As Long
    
    keywordInput = InputBox("Enter keywords (separate by ,):", "Search", "")
    If keywordInput = "" Then Exit Sub
    keywords = Split(keywordInput, ",")
    
    startDateStr = InputBox("Nhap ngay bat dau :", "Tu ngay", Format(Date, "yyyy-mm-dd"))
    If startDateStr = "" Then Exit Sub
    endDateStr = InputBox("Nhap ngay ket thuc :", "Toi ngay", Format(Date, "yyyy-mm-dd"))
    If endDateStr = "" Then Exit Sub
    
    startDate = CDate(startDateStr)
    endDate = CDate(endDateStr) + 1 - TimeSerial(0, 0, 1)
    
    Set ns = Application.GetNamespace("MAPI")
    Set rootFolder = ns.GetDefaultFolder(olFolderInbox).Parent
    
    ' Store results per keyword
    Dim results() As Variant
    ReDim results(LBound(keywords) To UBound(keywords))
    
    Dim maxRows As Long: maxRows = 0
    
    ' Collect per keyword
    For i = LBound(keywords) To UBound(keywords)
        
        Dim allMails As Collection
        Set allMails = New Collection
        
        Dim singleKeyword(0 To 0) As String
        singleKeyword(0) = Trim(keywords(i))
        
        Call CollectMails(rootFolder, singleKeyword, startDate, endDate, allMails)
        
        If allMails.Count > 0 Then
            results(i) = SortMailsByDate(allMails)
            If UBound(results(i)) > maxRows Then maxRows = UBound(results(i))
        Else
            results(i) = Empty
        End If
        
    Next i
    
    ' Build HTML
    Dim result As String
    result = "<h3>Search Results for '" & keywordInput & "'</h3>"
    result = result & "<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;'>"
    result = result & "<tr style='background-color:#f2f2f2;'><th>Keyword</th><th>Time</th><th>Mail</th></tr>"

    Dim idx As Long, k As Variant

    ' Loop keywords IN INPUT ORDER
    For i = LBound(keywords) To UBound(keywords)
        
        k = Trim(keywords(i))
        If k = "" Then GoTo NextK
        
        Dim hasResult As Boolean
        hasResult = False
        
        ' Check results for THIS keyword
        If Not IsEmpty(results(i)) Then
            
            For idx = LBound(results(i)) To UBound(results(i))
                
                Dim email As Outlook.MailItem
                Set email = results(i)(idx)
                
                hasResult = True
                
                result = result & "<tr>"
                result = result & "<td>" & k & "</td>"
                
                result = result & "<td>" & Format(email.ReceivedTime, "hh:nn AM/PM") & "</td>"
                result = result & "<td>" & Format(email.ReceivedTime, "yyyy-mm-dd") & "<br/>"
                result = result & "<a href='outlook:" & email.EntryID & "'>" & email.Subject & "</a><br/>"
                result = result & "Sender: " & email.SenderName & "<br/>"
                result = result & "To: " & email.To & "<br/>"
                result = result & "CC: " & email.CC & "<br/>"
                result = result & "Folder: <b>" & email.Parent.FolderPath & "</b></td>"
                result = result & "CC: " & email.Body & "<br/>"
                result = result & "</tr>"
                
            Next idx
            
        End If
        
        ' No result for this keyword
        If Not hasResult Then
            result = result & "<tr>"
            result = result & "<td>" & k & "</td>"
            result = result & "<td colspan='2'>Not found: " & k & "</td>"
            result = result & "</tr>"
        End If

NextK:
    Next i

    result = result & "</table>"
    
    Set newMail = Application.CreateItem(olMailItem)
    newMail.Subject = "Search Result: " & keywordInput
    newMail.HTMLBody = result
    newMail.Display

End Sub

'--- Collect matched mails into a collection
Sub CollectMails(f As Outlook.MAPIFolder, keywords() As String, startDate As Date, endDate As Date, allMails As Collection)
    Dim mail As Object
    Dim subF As Outlook.MAPIFolder
    
    ' Skip Junk and Deleted Items
    If f.DefaultItemType = olMailItem Then
        If f.Name = "Junk Email" Or f.Name = "Drafts" Or f.Name = "Deleted Items" Then Exit Sub
    End If
    
    ' Collect mails in this folder
    For Each mail In f.Items
        If TypeOf mail Is Outlook.MailItem Then
            Dim k As Variant
            Dim found As Boolean
            found = False
            
            For Each k In keywords
                k = Trim(LCase(k))
                
                If k <> "" Then
                    If InStr(1, LCase(mail.Subject), k) > 0 _
                    Or InStr(1, LCase(mail.Body), k) > 0 _
                    Or InStr(1, LCase(mail.SenderName), k) > 0 Then
                        found = True
                        Exit For
                    End If
                End If
            Next
            
            If found _
            And mail.ReceivedTime >= startDate And mail.ReceivedTime <= endDate Then
                
                allMails.Add mail
            End If
        End If
    Next mail
    
    ' Recurse into subfolders
    For Each subF In f.Folders
        Call CollectMails(subF, keywords, startDate, endDate, allMails)
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