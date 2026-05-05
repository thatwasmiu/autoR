import win32com.client

KEYWORDS = ["RSA-2103", "RSA-2207", "payment"]

def match_keywords(text, keywords):
    text = (text or "").lower()
    return any(k.lower() in text for k in keywords)

def get_matching_emails():
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder(6)  # 6 = Inbox

    messages = inbox.Items
    messages.Sort("[ReceivedTime]", True)  # newest first

    results = []

    for msg in messages:
        try:
            subject = msg.Subject
            body = msg.Body

            if match_keywords(subject, KEYWORDS) or match_keywords(body, KEYWORDS):
                results.append({
                    "subject": subject,
                    "sender": msg.SenderName,
                    "received": msg.ReceivedTime,
                })

        except Exception:
            # Skip non-mail items (meeting requests, etc.)
            continue

    return results


# emails = get_matching_emails()

# for e in emails[:10]:
#     print(e)


def get_mail_times_from_inbox():
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    
    inbox = outlook.GetDefaultFolder(6)  # 6 = Inbox
    messages = inbox.Items
    messages.Sort("[ReceivedTime]", True)  # newest first

    times = []

    for msg in messages:
        try:
            received = msg.ReceivedTime  # Python datetime
            formatted_time = received.strftime("%I:%M %p")  # HH:MM AM/PM
            times.append(formatted_time)

        except Exception:
            continue  # skip non-mail items

    return times


times = get_mail_times_from_inbox()

for t in times[:10]:
    print(t)    