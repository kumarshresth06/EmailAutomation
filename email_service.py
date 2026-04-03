import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd

class EmailSender:
    def __init__(self, email_addr, app_pass, logger=None):
        self.email_addr = email_addr
        self.app_pass = app_pass
        self.logger = logger
        self.smtp_conn = None

    def log(self, msg):
        if self.logger:
            self.logger(msg)
        else:
            print(msg)

    def connect(self):
        self.log(f"Connecting to SMTP server for {self.email_addr}...")
        self.smtp_conn = smtplib.SMTP('smtp.gmail.com', 587)
        self.smtp_conn.starttls()
        self.smtp_conn.login(self.email_addr, self.app_pass)
        self.log("SMTP connected and authenticated.")

    def format_content(self, row, template, subject, placeholders):
        formatted_html = template
        formatted_subject = subject
        has_blank_placeholder = False

        for p in placeholders:
            val = None
            for col in row.index:
                if str(col).lower() == p.lower():
                    val = row[col]
                    break

            if pd.isna(val) or str(val).strip() == '':
                has_blank_placeholder = True
                break
            # Replace in HTML
            formatted_html = formatted_html.replace(f"{{{{{p}}}}}", str(val))
            formatted_subject = formatted_subject.replace(f"{{{{{p}}}}}", str(val))

        if has_blank_placeholder:
            return None, None
            
        return formatted_subject, formatted_html

    def send_email(self, target_email, formatted_subject, formatted_html):
        if not self.smtp_conn:
            raise Exception("SMTP connection not established. Must call connect() first.")
            
        msg = MIMEMultipart('alternative')
        msg['Subject'] = formatted_subject
        msg['From'] = self.email_addr
        msg['To'] = target_email

        part = MIMEText(formatted_html, 'html')
        msg.attach(part)

        self.smtp_conn.sendmail(self.email_addr, target_email, msg.as_string())

    def close(self):
        if self.smtp_conn:
            try:
                self.smtp_conn.quit()
            except:
                pass
