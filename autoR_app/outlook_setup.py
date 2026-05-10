import win32com.client
from datetime import datetime
from tkinter import ttk

filters = [
    {
        "required_keywords": ["RSA-2103"],
        "optional_keywords": ["UAT"],
        "folders": ["Inbox"],
        "people": ["Jira@vetc.com.vn"]
    }
]

SKIP_FOLDERS = {
    "deleted items",
    "drafts",
}
outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

class OutLookMailFinder(ttk.Frame):
    def __init__(self, master, headers=[], records=[], metadata_headers=[], on_row_action_callback=None):
        super().__init__(master)

        self.outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        self.filters = []
        self.matched_mails = []
        self._build_sheet()

    def mail_matches_filter(mail, filter_obj, folder_name):
        subject = (mail.Subject or "").lower()
        body = (mail.Body or "").lower()

        content = f"{subject}\n{body}"

        sender = (mail.SenderEmailAddress or "").lower()
        to = (mail.To or "").lower()
        cc = (mail.CC or "").lower()

        # --------------------
        # Folder OR
        # --------------------
        folders = [
            f.lower()
            for f in (filter_obj.get("folders") or [])
        ]

        folder_match = (
            not folders or
            folder_name.lower() in folders
        )

        if not folder_match:
            return False

        # --------------------
        # Required keywords AND
        # --------------------
        required_keywords = [
            k.lower()
            for k in (filter_obj.get("required_keywords") or [])
        ]

        required_match = (
            not required_keywords or
            all(k in content for k in required_keywords)
        )

        if not required_match:
            return False

        # --------------------
        # Optional keywords OR
        # --------------------
        optional_keywords = [
            k.lower()
            for k in (filter_obj.get("optional_keywords") or [])
        ]

        optional_match = (
            not optional_keywords or
            any(k in content for k in optional_keywords)
        )

        if not optional_match:
            return False

        # --------------------
        # People OR
        # --------------------
        people = [
            p.lower()
            for p in (filter_obj.get("people") or [])
        ]

        people_match = (
            not people or
            any(
                p in sender or
                p in to or
                p in cc
                for p in people
            )
        )

        return people_match

    # Example mailbox
    mailbox = outlook.Folders["DatNT4@vetc.com.vn"]

    from_date = datetime(2026, 5, 1)
    to_date = datetime(2026, 5, 8, 23, 59, 59)

    from_str = from_date.strftime("%m/%d/%Y %H:%M %p")
    to_str = to_date.strftime("%m/%d/%Y %H:%M %p")
    for i in range(mailbox.Folders.Count):
        folder = mailbox.Folders.Item(i + 1)

        # Skip unwanted folders
        if folder.Name.lower() in SKIP_FOLDERS:
            continue

        try:
            items = folder.Items

            items.Sort("[ReceivedTime]", True)

            restricted_items = items.Restrict(
                f"[ReceivedTime] >= '{from_str}' "
                f"AND [ReceivedTime] <= '{to_str}'"
            )

            for mail in items:
                # Mail item only
                if mail.Class != 43:
                    continue

                for filter_obj in filters:
                    if mail_matches_filter(mail, filter_obj, folder.Name):
                        matched_mails.append({
                            "subject": mail.Subject,
                            "sender": mail.SenderEmailAddress,
                            "folder": folder.Name,
                        })
                        break

        except Exception as e:
            print(f"Skip folder {folder.Name}: {e}")