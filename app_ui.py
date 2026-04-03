import re
import time
import random
import threading
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox
import smtplib
import pandas as pd

from data_service import DataHandler
from email_service import EmailSender
from email_guesser import EmailDerivationService

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ColdOutreachUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cold Outreach Automator")
        self.geometry("900x750")
        self.minsize(900, 700)
        
        self.stop_event = threading.Event()
        self.filepath = None
        self.is_running = False
        self.test_email_sent = False

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=3)
        self.grid_rowconfigure(4, weight=1)

        self.cred_frame = ctk.CTkFrame(self)
        self.cred_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.cred_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.cred_frame, text="Gmail Address:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.email_entry = ctk.CTkEntry(self.cred_frame, placeholder_text="your.email@gmail.com")
        self.email_entry.grid(row=0, column=1, padx=10, pady=5, sticky="we")
        
        ctk.CTkLabel(self.cred_frame, text="App Password:", font=("Arial", 12, "bold")).grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.password_entry = ctk.CTkEntry(self.cred_frame, show="*", placeholder_text="16-character-password")
        self.password_entry.grid(row=1, column=1, padx=10, pady=5, sticky="we")

        self.data_frame = ctk.CTkFrame(self)
        self.data_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.data_frame.grid_columnconfigure(1, weight=1)

        self.btn_browse = ctk.CTkButton(self.data_frame, text="Browse CSV/Excel", command=self.browse_file)
        self.btn_browse.grid(row=0, column=0, padx=10, pady=10)
        self.lbl_filepath = ctk.CTkLabel(self.data_frame, text="No file selected", text_color="gray")
        self.lbl_filepath.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.template_frame = ctk.CTkFrame(self)
        self.template_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.template_frame.grid_columnconfigure(1, weight=1)
        self.template_frame.grid_rowconfigure(2, weight=1)
        
        ctk.CTkLabel(self.template_frame, text="Subject Line:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.subject_entry = ctk.CTkEntry(self.template_frame, placeholder_text="Enter subject line here")
        self.subject_entry.grid(row=0, column=1, padx=10, pady=5, sticky="we")

        self.toolbar_frame = ctk.CTkFrame(self.template_frame, fg_color="transparent")
        self.toolbar_frame.grid(row=1, column=1, padx=10, pady=0, sticky="w")
        
        ctk.CTkButton(self.toolbar_frame, text="B", width=30, command=lambda: self.insert_tag("<b>", "</b>")).pack(side="left", padx=2)
        ctk.CTkButton(self.toolbar_frame, text="I", width=30, command=lambda: self.insert_tag("<i>", "</i>")).pack(side="left", padx=2)
        ctk.CTkButton(self.toolbar_frame, text="Link", width=40, command=lambda: self.insert_tag('<a href="URL_HERE">', "</a>")).pack(side="left", padx=2)
        ctk.CTkButton(self.toolbar_frame, text="Paragraph", width=70, command=lambda: self.insert_tag("<p>", "</p>")).pack(side="left", padx=2)
        ctk.CTkButton(self.toolbar_frame, text="Line Break", width=70, command=lambda: self.insert_tag("<br>\n", "")).pack(side="left", padx=2)
        
        ctk.CTkLabel(self.template_frame, text="HTML Template\n(Use {{Column_Name}}):", font=("Arial", 12, "bold")).grid(row=2, column=0, padx=10, pady=5, sticky="ne")
        self.template_text = ctk.CTkTextbox(self.template_frame, wrap="word")
        self.template_text.grid(row=2, column=1, padx=10, pady=5, sticky="nsew")

        sample_template = (
            "<p>Hi {{First Name}},</p>\n\n"
            "<p>I noticed your great work recently at {{Company}} and wanted to reach out regarding an opportunity.</p>\n\n"
            "<p>Best regards,<br>\nYour Name</p>"
        )
        self.template_text.insert("1.0", sample_template)

        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.action_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.btn_test = ctk.CTkButton(self.action_frame, text="Send Test Email", fg_color="#3B82F6", hover_color="#2563EB", command=self.send_test_email)
        self.btn_test.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.btn_start = ctk.CTkButton(self.action_frame, text="Start Campaign", fg_color="green", hover_color="darkgreen", command=self.start_campaign, state="disabled")
        self.btn_start.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.override_var = ctk.BooleanVar(value=False)
        self.chk_override = ctk.CTkCheckBox(self.action_frame, text="Override Test Valid.", variable=self.override_var, command=self.update_start_button_state)
        self.chk_override.grid(row=0, column=2, padx=10, pady=10)
        
        self.btn_stop = ctk.CTkButton(self.action_frame, text="Stop/Cancel", fg_color="red", hover_color="darkred", state="disabled", command=self.stop_campaign)
        self.btn_stop.grid(row=0, column=3, padx=10, pady=10, sticky="ew")

        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(0, weight=1)
        
        self.log_box = ctk.CTkTextbox(self.log_frame, height=150, state="disabled")
        self.log_box.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    def log(self, message):
        self.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_box.configure(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{ts}] {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def insert_tag(self, start_tag, end_tag):
        try:
            sel_start = self.template_text.tag_ranges("sel")[0]
            sel_end = self.template_text.tag_ranges("sel")[1]
            selected_text = self.template_text.get(sel_start, sel_end)
            self.template_text.delete(sel_start, sel_end)
            self.template_text.insert(sel_start, f"{start_tag}{selected_text}{end_tag}")
        except:
            cursor_pos = self.template_text.index("insert")
            self.template_text.insert(cursor_pos, f"{start_tag}{end_tag}")

    def update_start_button_state(self):
        if self.is_running: return
        if self.test_email_sent or self.override_var.get():
            self.btn_start.configure(state="normal")
        else:
            self.btn_start.configure(state="disabled")

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv")])
        if filename:
            try:
                handler = DataHandler(filename)
                handler.load_data()
                if not handler.has_email_column() and not handler.has_fallback_columns():
                    messagebox.showerror("Validation Error", "The selected file MUST contain an 'Email' column OR all three: 'First Name', 'Last Name', 'Company'.")
                    return
                self.filepath = filename
                self.lbl_filepath.configure(text=filename, text_color=("black", "white"))
                self.log(f"Selected & Validated file: {filename}")
            except Exception as e:
                messagebox.showerror("Validation Error", f"Could not read the file properly: {str(e)}")

    def toggle_ui_state(self, running):
        state = "disabled" if running else "normal"
        self.email_entry.configure(state=state)
        self.password_entry.configure(state=state)
        self.btn_browse.configure(state=state)
        self.subject_entry.configure(state=state)
        self.template_text.configure(state=state)
        self.chk_override.configure(state=state)
        
        if running:
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            if hasattr(self, 'btn_test'):
                self.btn_test.configure(state="disabled")
        else:
            self.update_start_button_state()
            self.btn_stop.configure(state="disabled")
            if hasattr(self, 'btn_test'):
                self.btn_test.configure(state="normal")

    def stop_campaign(self):
        self.log("Stop requested... Will stop after current operation finishes.")
        self.stop_event.set()

    def send_test_email(self):
        user_email = self.email_entry.get().strip()
        app_pass = self.password_entry.get().strip()
        subject = self.subject_entry.get().strip()
        template = self.template_text.get("1.0", "end-1c").strip()

        if not all([user_email, app_pass, self.filepath, subject, template]):
            messagebox.showerror("Missing Information", "Please fill out all fields and select a data file.")
            return

        self.is_running = True
        self.stop_event.clear()
        self.toggle_ui_state(True)
        self.log("Sending test email to your own address...")

        threading.Thread(target=self.run_test_task, args=(user_email, app_pass, subject, template), daemon=True).start()

    def run_test_task(self, email_addr, app_pass, subject, template):
        data_handler = DataHandler(self.filepath, logger=self.log)
        try:
            data_handler.load_data()
        except Exception as e:
            self.log(f"ERROR loading file: {e}")
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
            return

        placeholders = set(re.findall(r'\{\{(.*?)\}\}', template))
        placeholders.update(re.findall(r'\{\{(.*?)\}\}', subject))
        
        missing_cols = data_handler.get_missing_placeholders(placeholders)
        if missing_cols:
            self.log(f"ERROR: Missing columns in data: {', '.join(missing_cols)}")
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
            return
            
        if not data_handler.has_email_column() and not data_handler.has_fallback_columns():
            self.log("ERROR: Spreadsheet must have an 'Email' column OR 'First Name', 'Last Name', 'Company'.")
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
            return

        sample_row = data_handler.get_sample_row(placeholders)
        if sample_row is None:
            self.log("ERROR: Could not find any fully populated row in your data to use as a test sample.")
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
            return

        email_sender = EmailSender(email_addr, app_pass, logger=self.log)
        formatted_subject, formatted_html = email_sender.format_content(sample_row, template, subject, placeholders)
        
        try:
            email_sender.connect()
            email_sender.send_email(email_addr, formatted_subject, formatted_html)
            self.log("Success! Test email sent to your own address.")
            self.test_email_sent = True
        except smtplib.SMTPAuthenticationError:
            self.log("ERROR: SMTP Authentication Failed. Check App Password.")
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
        finally:
            email_sender.close()
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))

    def start_campaign(self):
        user_email = self.email_entry.get().strip()
        app_pass = self.password_entry.get().strip()
        subject = self.subject_entry.get().strip()
        template = self.template_text.get("1.0", "end-1c").strip()

        if not all([user_email, app_pass, self.filepath, subject, template]):
            messagebox.showerror("Missing Information", "Please fill out all fields and select a data file.")
            return

        self.is_running = True
        self.stop_event.clear()
        self.toggle_ui_state(True)
        self.log("Starting campaign...")

        threading.Thread(target=self.run_campaign_task, args=(user_email, app_pass, subject, template), daemon=True).start()

    def run_campaign_task(self, email_addr, app_pass, subject, template):
        data_handler = DataHandler(self.filepath, logger=self.log)
        try:
            data_handler.load_data()
        except Exception as e:
            self.log(f"ERROR loading file: {e}")
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
            return

        placeholders = set(re.findall(r'\{\{(.*?)\}\}', template))
        placeholders.update(re.findall(r'\{\{(.*?)\}\}', subject))
        
        missing_cols = data_handler.get_missing_placeholders(placeholders)
        if missing_cols:
            self.log(f"ERROR: Missing columns in data: {', '.join(missing_cols)}")
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
            return
            
        if not data_handler.has_email_column() and not data_handler.has_fallback_columns():
            self.log("ERROR: Spreadsheet must have an 'Email' column OR 'First Name', 'Last Name', 'Company'.")
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
            return

        email_sender = EmailSender(email_addr, app_pass, logger=self.log)
        derivation_service = EmailDerivationService(logger=self.log)

        try:
            email_sender.connect()
        except Exception as e:
            self.log(f"ERROR connecting to SMTP: {e}")
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
            return

        rows_processed = 0

        try:
            for index, row in data_handler.df.iterrows():
                if self.stop_event.is_set():
                    self.log("Campaign stopped by user.")
                    break

                # Extract Target Email
                target_email = ""
                if data_handler.email_col and not pd.isna(row[data_handler.email_col]):
                    target_email = str(row[data_handler.email_col]).strip()
                
                status = str(row['Status']).strip().lower()

                if target_email == 'nan' or not target_email:
                    # Trigger Derivation Hook
                    fn = row.get('First Name', '')
                    ln = row.get('Last Name', '')
                    co = row.get('Company', '')
                    
                    target_email = derivation_service.guess_email(fn, ln, co)

                if not target_email:
                    self.log(f"Row {index}: Missing explicit address and derivation failed. Skipping.")
                    continue

                if status == 'sent':
                    continue

                formatted_subject, formatted_html = email_sender.format_content(row, template, subject, placeholders)
                
                if formatted_html is None:
                    self.log(f"ERROR: Row {index} to {target_email} has blank placeholders. Skipping.")
                    continue

                self.log(f"Sending to {target_email}...")
                try:
                    email_sender.send_email(target_email, formatted_subject, formatted_html)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    data_handler.mark_sent(index, timestamp)
                    self.log(f"Success. Sending state saved.")
                    rows_processed += 1
                except Exception as e:
                    self.log(f"Failed sending to {target_email}: {str(e)}")
                    continue
                    
                if not self.stop_event.is_set():
                    delay = random.randint(45, 90)
                    self.log(f"Waiting {delay} seconds before next email (throttling)...")
                    for _ in range(delay):
                        if self.stop_event.is_set():
                            break
                        time.sleep(1)

            self.log(f"Campaign finished. Total emails sent this run: {rows_processed}")
        finally:
            email_sender.close()
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
