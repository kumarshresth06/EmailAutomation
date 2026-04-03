import re
import time
import random
import threading
import os
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import smtplib
import pandas as pd
from PIL import Image, ImageTk
import markdown as md_lib
from tkinterweb import HtmlFrame

from data_service import DataHandler
from email_service import EmailSender
from email_guesser import EmailDerivationService

# ── Theme ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Color palette
C = {
    "bg":         ("#FAF9F6", "#0F1117"),   # deepest background
    "surface":    ("#FFFFFF", "#1A1D27"),   # card background
    "surface2":   ("#F4F4F5", "#22263A"),   # elevated card
    "border":     ("#E4E4E7", "#2E3350"),   # subtle border
    "accent":     ("#6C63FF", "#6C63FF"),   # indigo accent
    "accent2":    ("#4F8EF7", "#4F8EF7"),   # blue accent
    "success":    ("#16A34A", "#22C55E"),   # green
    "danger":     ("#DC2626", "#EF4444"),   # red
    "warning":    ("#D97706", "#F59E0B"),   # amber
    "text":       ("#18181B", "#F1F5F9"),   # primary text
    "text_muted": ("#52525B", "#64748B"),   # muted text
    "text_dim":   ("#A1A1AA", "#94A3B8"),   # dim text
    "tag_btn":    ("#E4E4E7", "#2D3555"),   # tag button background
}

FONT_H1    = ("SF Pro Display", 26, "bold")
FONT_H2    = ("SF Pro Display", 18, "bold")
FONT_BODY  = ("SF Pro Text",    16)
FONT_SMALL = ("SF Pro Text",    14)
FONT_MONO  = ("JetBrains Mono", 14)
FONT_LABEL = ("SF Pro Text",    16, "bold")

# Fallback fonts if SF / JetBrains not installed
try:
    import tkinter.font as tkfont
    _test = tkfont.Font(family="SF Pro Display")
    if _test.actual()["family"] not in ("SF Pro Display", ".AppleSystemUIFont"):
        raise ValueError
except Exception:
    FONT_H1    = ("Helvetica Neue", 26, "bold")
    FONT_H2    = ("Helvetica Neue", 18, "bold")
    FONT_BODY  = ("Helvetica Neue", 16)
    FONT_SMALL = ("Helvetica Neue", 14)
    FONT_MONO  = ("Courier New",    14)
    FONT_LABEL = ("Helvetica Neue", 16, "bold")


def make_card(parent, **kwargs):
    """Returns a styled card frame."""
    defaults = dict(
        fg_color=C["surface"],
        corner_radius=12,
        border_width=1,
        border_color=C["border"],
    )
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)


def section_label(parent, text, row=0, column=0, columnspan=1):
    """Section header with accent underline feel."""
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.grid(row=row, column=column, columnspan=columnspan,
           padx=18, pady=(14, 4), sticky="w")
    ctk.CTkLabel(f, text=text, font=FONT_H2,
                 text_color=C["text"]).pack(side="left")
    ctk.CTkLabel(f, text=" ·", font=FONT_H2,
                 text_color=C["accent"]).pack(side="left")
    return f


class StatusDot(ctk.CTkFrame):
    """Animated pulsing status indicator."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, width=10, height=10,
                         corner_radius=5, fg_color=C["text_muted"], **kwargs)
        self._state = "idle"
        self._anim_id = None

    def set_state(self, state: str):
        colors = {"idle": C["text_muted"], "running": C["accent"],
                  "success": C["success"], "error": C["danger"]}
        self._state = state
        color = colors.get(state, C["text_muted"])
        self.configure(fg_color=color)
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None
        if state == "running":
            self._pulse()

    def _pulse(self):
        import math
        self._phase = getattr(self, "_phase", 0) + 0.15
        t = (math.sin(self._phase) + 1) / 2
        r = int(0x6C + t * (0xFF - 0x6C))
        g = int(0x63 + t * (0xFF - 0x63))
        b = int(0xFF)
        color = f"#{r:02x}{g:02x}{b:02x}"
        self.configure(fg_color=color)
        if self._state == "running":
            self._anim_id = self.after(60, self._pulse)


class TagButton(ctk.CTkButton):
    """Compact HTML tag insertion button."""
    def __init__(self, parent, label, **kwargs):
        super().__init__(
            parent, text=label, width=36, height=26,
            font=("Helvetica Neue", 11, "bold"),
            fg_color=C["tag_btn"], hover_color=C["accent"],
            text_color=C["text_dim"], corner_radius=6,
            border_width=0,
            **kwargs,
        )


# ── Help Viewer ───────────────────────────────────────────────────────────────
def get_help_css():
    mode = ctk.get_appearance_mode()
    if mode == "Light":
        return """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #FAF9F6;
    color: #18181B;
    font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
    font-size: 16px;
    line-height: 1.75;
    padding: 28px 36px 48px;
}
h1, h2, h3 {
    font-weight: 700;
    margin-top: 32px;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #E4E4E7;
}
h1 { font-size: 26px; color: #18181B; margin-top: 0; }
h2 { font-size: 22px; color: #3F3F46; }
h3 { font-size: 18px; color: #52525B; }
p  { margin: 10px 0; color: #3F3F46; }
ul, ol {
    margin: 8px 0 8px 22px;
    color: #3F3F46;
}
li { margin: 6px 0; }
a  { color: #6C63FF; text-decoration: none; }
a:hover { text-decoration: underline; }
blockquote {
    border-left: 3px solid #6C63FF;
    background: #FFFFFF;
    margin: 14px 0;
    padding: 10px 18px;
    border-radius: 0 8px 8px 0;
    color: #52525B;
    font-style: italic;
}
code {
    background: #F4F4F5;
    color: #6C63FF;
    padding: 1px 6px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 15px;
}
pre {
    background: #F4F4F5;
    border: 1px solid #E4E4E7;
    border-radius: 8px;
    padding: 14px 18px;
    overflow-x: auto;
    margin: 14px 0;
}
pre code {
    background: transparent;
    padding: 0;
    color: #52525B;
}
hr {
    border: none;
    border-top: 1px solid #E4E4E7;
    margin: 28px 0;
}
strong { color: #18181B; font-weight: 700; }
em     { color: #52525B; }
"""
    else:
        return """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #0F1117;
    color: #F1F5F9;
    font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
    font-size: 16px;
    line-height: 1.75;
    padding: 28px 36px 48px;
}
h1, h2, h3 {
    font-weight: 700;
    margin-top: 32px;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #2E3350;
}
h1 { font-size: 26px; color: #F1F5F9; margin-top: 0; }
h2 { font-size: 22px; color: #CBD5E1; }
h3 { font-size: 18px; color: #94A3B8; }
p  { margin: 10px 0; color: #CBD5E1; }
ul, ol {
    margin: 8px 0 8px 22px;
    color: #CBD5E1;
}
li { margin: 6px 0; }
a  { color: #6C63FF; text-decoration: none; }
a:hover { text-decoration: underline; }
blockquote {
    border-left: 3px solid #6C63FF;
    background: #1A1D27;
    margin: 14px 0;
    padding: 10px 18px;
    border-radius: 0 8px 8px 0;
    color: #94A3B8;
    font-style: italic;
}
code {
    background: #22263A;
    color: #6C63FF;
    padding: 1px 6px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 15px;
}
pre {
    background: #22263A;
    border: 1px solid #2E3350;
    border-radius: 8px;
    padding: 14px 18px;
    overflow-x: auto;
    margin: 14px 0;
}
pre code {
    background: transparent;
    padding: 0;
    color: #94A3B8;
}
hr {
    border: none;
    border-top: 1px solid #2E3350;
    margin: 28px 0;
}
strong { color: #F1F5F9; font-weight: 700; }
em     { color: #94A3B8; }
"""


class HelpWindow(ctk.CTkToplevel):
    """Floating help window that renders helper.md as styled HTML."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Help & Documentation")
        self.geometry("780x680")
        self.minsize(600, 480)
        self.configure(fg_color=C["bg"])
        self.resizable(True, True)

        # ── Titlebar ────────────────────────────────────────────────────────
        bar = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0,
                           border_width=0, height=52)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        ctk.CTkLabel(bar, text="📖  Help & Documentation",
                     font=FONT_H2, text_color=C["text"]
                     ).pack(side="left", padx=20, pady=14)

        ctk.CTkButton(
            bar, text="✕  Close", width=80, height=30,
            font=FONT_SMALL, corner_radius=6,
            fg_color=C["surface2"], hover_color=C["danger"],
            text_color=C["text_dim"],
            command=self.destroy
        ).pack(side="right", padx=16, pady=11)

        ctk.CTkFrame(self, height=2, fg_color=C["accent"],
                     corner_radius=0).pack(fill="x", side="top")

        # ── HTML render area ────────────────────────────────────────────────
        container = ctk.CTkFrame(self, fg_color=C["surface"],
                                 corner_radius=0)
        container.pack(fill="both", expand=True, padx=0, pady=0)

        self._frame = HtmlFrame(container, messages_enabled=False)
        self._frame.pack(fill="both", expand=True, padx=0, pady=0)

        self._load_content()
        self.after(100, self.lift)   # ensure it appears on top
        self.focus_force()

    def _load_content(self):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        helper_path = os.path.join(base_path, "helper.md")
        try:
            raw = open(helper_path, "r", encoding="utf-8").read()
            body_html = md_lib.markdown(
                raw,
                extensions=["fenced_code", "tables", "nl2br", "sane_lists"]
            )
            full_html = f"""<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='UTF-8'>
<style>{get_help_css()}</style>
</head>
<body>
{body_html}
</body></html>"""
            self._frame.load_html(full_html)
        except FileNotFoundError:
            self._frame.load_html(
                f"<html><body style='background:#0F1117;color:#EF4444;padding:24px;'>"
                f"<h2>helper.md not found</h2>"
                f"<p>Expected at: <code>{helper_path}</code></p>"
                f"</body></html>"
            )
        except Exception as e:
            self._frame.load_html(
                f"<html><body style='background:#0F1117;color:#EF4444;padding:24px;'>"
                f"<h2>Error loading help</h2><p>{e}</p></body></html>"
            )


class ColdOutreachUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cold Outreach Automator")
        self.geometry("980x820")
        self.minsize(880, 720)
        self.configure(fg_color=C["bg"])

        self.stop_event = threading.Event()
        self.filepath = None
        self.output_path = None
        self.is_running = False
        self.test_email_sent = False
        self._emails_sent = 0
        self._emails_total = 0

        self._build_header()
        self._build_body()

    # ── Header ─────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0,
                           border_width=0, height=68)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        # App icon from assets/icon.png
        _icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        try:
            pil_img = Image.open(_icon_path)
            # Set window icon (titlebar)
            tk_icon = ImageTk.PhotoImage(pil_img.resize((64, 64), Image.LANCZOS))
            self.iconphoto(True, tk_icon)
            self._tk_icon = tk_icon  # prevent GC

            # Header logo (44×44)
            ctk_img = ctk.CTkImage(light_image=pil_img,
                                   dark_image=pil_img, size=(44, 44))
            logo_lbl = ctk.CTkLabel(hdr, image=ctk_img, text="")
            logo_lbl.pack(side="left", padx=(16, 10), pady=12)
        except Exception:
            # Fallback to emoji badge if image can't load
            logo_box = ctk.CTkFrame(hdr, width=40, height=40,
                                    corner_radius=10, fg_color=C["accent"])
            logo_box.pack(side="left", padx=(16, 10), pady=12)
            logo_box.pack_propagate(False)
            ctk.CTkLabel(logo_box, text="✉", font=("Helvetica Neue", 20),
                         text_color="white").pack(expand=True)

        title_col = ctk.CTkFrame(hdr, fg_color="transparent")
        title_col.pack(side="left")
        ctk.CTkLabel(title_col, text="Cold Outreach Automator",
                     font=FONT_H1, text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(title_col, text="Personalised email campaigns at scale",
                     font=FONT_SMALL, text_color=C["text_muted"]).pack(anchor="w")

        # Theme switcher
        self.theme_switch = ctk.CTkOptionMenu(
            hdr, values=["System", "Light", "Dark"],
            command=self._change_theme,
            width=90, height=34, font=FONT_SMALL,
            fg_color=C["surface2"], button_color=C["surface2"],
            button_hover_color=C["border"], text_color=C["text_dim"]
        )
        current_mode = ctk.get_appearance_mode().capitalize()
        self.theme_switch.set(current_mode if current_mode in ["Light", "Dark"] else "System")
        self.theme_switch.pack(side="right", padx=(8, 20), pady=17)

        # Help button
        ctk.CTkButton(
            hdr, text="?  Help", width=80, height=34,
            font=FONT_SMALL, corner_radius=8,
            fg_color=C["surface2"], hover_color=C["accent"],
            text_color=C["text_dim"], border_width=1, border_color=C["border"],
            command=self._open_help
        ).pack(side="right", padx=(8, 8), pady=17)

        # Status indicator (right side)
        status_row = ctk.CTkFrame(hdr, fg_color="transparent")
        status_row.pack(side="right", padx=(0, 4))
        self._status_dot = StatusDot(status_row)
        self._status_dot.pack(side="left", padx=(0, 6))
        self._status_lbl = ctk.CTkLabel(status_row, text="Idle",
                                        font=FONT_SMALL, text_color=C["text_muted"])
        self._status_lbl.pack(side="left")

        # Thin accent line under header
        ctk.CTkFrame(self, height=2, fg_color=C["accent"],
                     corner_radius=0).pack(fill="x", side="top")

    # ── Body ───────────────────────────────────────────────────────────────────
    def _build_body(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=C["bg"],
                                        scrollbar_button_color=C["border"],
                                        scrollbar_button_hover_color=C["accent"])
        scroll.pack(fill="both", expand=True, padx=0, pady=0)
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        # ── Step 1 & 2 side by side ────────────────────────────────────────────
        top_row = ctk.CTkFrame(scroll, fg_color="transparent")
        top_row.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 0))
        top_row.grid_columnconfigure(0, weight=1)
        top_row.grid_columnconfigure(1, weight=1)

        self._build_credentials(top_row, col=0)
        self._build_data_source(top_row, col=1)

        # ── Step 3: Template ───────────────────────────────────────────────────
        self._build_template(scroll, row=1)

        # ── Step 4: Actions + Progress ─────────────────────────────────────────
        self._build_actions(scroll, row=2)

        # ── Step 5: Activity Log ───────────────────────────────────────────────
        self._build_log(scroll, row=3)

    # ── Credentials Card ───────────────────────────────────────────────────────
    def _build_credentials(self, parent, col):
        card = make_card(parent)
        card.grid(row=0, column=col, padx=(0, 8), pady=0, sticky="nsew")
        card.grid_columnconfigure(1, weight=1)

        self._step_header(card, "01", "SMTP Credentials", row=0)

        self._field_label(card, "Gmail Address", row=1)
        self.email_entry = ctk.CTkEntry(
            card, placeholder_text="you@gmail.com",
            fg_color=C["surface2"], border_color=C["border"],
            text_color=C["text"], placeholder_text_color=C["text_muted"],
            font=FONT_BODY, height=38, corner_radius=8)
        self.email_entry.grid(row=2, column=0, columnspan=2,
                              padx=16, pady=(0, 10), sticky="ew")

        self._field_label(card, "App Password", row=3)
        self.password_entry = ctk.CTkEntry(
            card, show="●", placeholder_text="16-char app password",
            fg_color=C["surface2"], border_color=C["border"],
            text_color=C["text"], placeholder_text_color=C["text_muted"],
            font=FONT_BODY, height=38, corner_radius=8)
        self.password_entry.grid(row=4, column=0, columnspan=2,
                                 padx=16, pady=(0, 18), sticky="ew")

    # ── Data Source Card ───────────────────────────────────────────────────────
    def _build_data_source(self, parent, col):
        card = make_card(parent)
        card.grid(row=0, column=col, padx=(8, 0), pady=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        self._step_header(card, "02", "Recipient Data", row=0)

        # Drop zone
        self._drop_zone = ctk.CTkFrame(card, fg_color=C["surface2"],
                                       corner_radius=10, border_width=1,
                                       border_color=C["border"], height=100)
        self._drop_zone.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        self._drop_zone.grid_propagate(False)
        self._drop_zone.grid_columnconfigure(0, weight=1)
        self._drop_zone.grid_rowconfigure(0, weight=1)
        self._drop_zone.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self._drop_zone, text="📂",
                     font=("Helvetica Neue", 28)).grid(row=0, column=0, pady=(10, 0))
        self._file_hint = ctk.CTkLabel(
            self._drop_zone, text="No file selected",
            font=FONT_SMALL, text_color=C["text_muted"], wraplength=220)
        self._file_hint.grid(row=1, column=0, padx=8, pady=(2, 10))

        self._out_hint = ctk.CTkLabel(
            card, text="",
            font=FONT_SMALL, text_color=C["text_dim"], wraplength=350)
        self._out_hint.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="ew")

        self.btn_browse = ctk.CTkButton(
            card, text="Browse CSV / Excel",
            font=FONT_LABEL, height=38, corner_radius=8,
            fg_color=C["accent2"], hover_color="#3B7DE8",
            command=self.browse_file)
        self.btn_browse.grid(row=3, column=0, padx=16, pady=(0, 18), sticky="ew")

    # ── Template Card ──────────────────────────────────────────────────────────
    def _build_template(self, parent, row):
        card = make_card(parent)
        card.grid(row=row, column=0, columnspan=2,
                  padx=16, pady=(12, 0), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(3, weight=1)

        self._step_header(card, "03", "Email Template", row=0)

        self._field_label(card, "Subject Line", row=1)
        self.subject_entry = ctk.CTkEntry(
            card, placeholder_text="Your compelling subject line here…",
            fg_color=C["surface2"], border_color=C["border"],
            text_color=C["text"], placeholder_text_color=C["text_muted"],
            font=FONT_BODY, height=38, corner_radius=8)
        self.subject_entry.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="ew")

        # Toolbar
        tb = ctk.CTkFrame(card, fg_color="transparent")
        tb.grid(row=3, column=0, padx=16, pady=(0, 6), sticky="w")

        ctk.CTkLabel(tb, text="HTML:", font=FONT_SMALL,
                     text_color=C["text_muted"]).pack(side="left", padx=(0, 8))

        tags = [
            ("B",   "<b>",             "</b>"),
            ("I",   "<i>",             "</i>"),
            ("U",   "<u>",             "</u>"),
            ("Link","<a href=\"URL\">", "</a>"),
            ("¶",   "<p>",             "</p>"),
            ("↵",   "<br>\n",          ""),
        ]
        for lbl, open_t, close_t in tags:
            TagButton(tb, lbl,
                      command=lambda o=open_t, c=close_t: self.insert_tag(o, c)
                      ).pack(side="left", padx=2)

        ctk.CTkLabel(tb, text="  Use {{Column_Name}} for personalisation",
                     font=FONT_SMALL, text_color=C["text_muted"]).pack(side="left", padx=8)

        # Text area
        self.template_text = ctk.CTkTextbox(
            card, wrap="word", height=200,
            fg_color=C["surface2"], border_color=C["border"], border_width=1,
            text_color=C["text"], font=FONT_MONO, corner_radius=8)
        self.template_text.grid(row=4, column=0, padx=16, pady=(0, 18), sticky="nsew")
        self.template_text.insert("1.0",
            "<p>Hi {{First Name}},</p>\n\n"
            "<p>I came across {{Company}} and was really impressed. "
            "I wanted to reach out about an opportunity that could be a great fit.</p>\n\n"
            "<p>Would love to connect — are you open to a quick chat?</p>\n\n"
            "<p>Best regards,<br>\nYour Name</p>")
        card.grid_rowconfigure(4, weight=1)

    # ── Actions Card ──────────────────────────────────────────────────────────
    def _build_actions(self, parent, row):
        card = make_card(parent)
        card.grid(row=row, column=0, columnspan=2,
                  padx=16, pady=(12, 0), sticky="ew")
        card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._step_header(card, "04", "Launch", row=0)

        # Buttons
        btn_cfg = dict(font=FONT_LABEL, height=44, corner_radius=10)

        self.btn_test = ctk.CTkButton(
            card, text="⚡  Send Test Email",
            fg_color=C["surface2"], hover_color=C["accent"],
            border_width=1, border_color=C["accent"],
            text_color=C["text"], **btn_cfg,
            command=self.send_test_email)
        self.btn_test.grid(row=1, column=0, padx=(16, 6), pady=(0, 6), sticky="ew")

        self.btn_start = ctk.CTkButton(
            card, text="🚀  Start Campaign",
            fg_color=C["success"], hover_color="#16A34A",
            text_color="white", state="disabled", **btn_cfg,
            command=self.start_campaign)
        self.btn_start.grid(row=1, column=1, padx=6, pady=(0, 6), sticky="ew")

        self.override_var = ctk.BooleanVar(value=False)
        self.chk_override = ctk.CTkCheckBox(
            card, text="Skip test validation",
            variable=self.override_var,
            font=FONT_SMALL, text_color=C["text_dim"],
            fg_color=C["accent"], hover_color=C["accent2"],
            checkmark_color="white",
            command=self.update_start_button_state)
        self.chk_override.grid(row=1, column=2, padx=6, pady=(0, 6))

        self.btn_stop = ctk.CTkButton(
            card, text="⛔  Stop Campaign",
            fg_color=C["surface2"], hover_color=C["danger"],
            border_width=1, border_color=C["danger"],
            text_color=C["danger"], state="disabled", **btn_cfg,
            command=self.stop_campaign)
        self.btn_stop.grid(row=1, column=3, padx=(6, 16), pady=(0, 6), sticky="ew")

        # Progress area
        prog_frame = ctk.CTkFrame(card, fg_color="transparent")
        prog_frame.grid(row=2, column=0, columnspan=4,
                        padx=16, pady=(0, 16), sticky="ew")
        prog_frame.grid_columnconfigure(0, weight=1)

        self._prog_bar = ctk.CTkProgressBar(
            prog_frame, height=6, corner_radius=3,
            fg_color=C["surface2"], progress_color=C["accent"])
        self._prog_bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self._prog_bar.set(0)

        stat_row = ctk.CTkFrame(prog_frame, fg_color="transparent")
        stat_row.grid(row=1, column=0, sticky="ew")
        stat_row.grid_columnconfigure(1, weight=1)

        self._prog_lbl = ctk.CTkLabel(stat_row, text="Ready",
                                      font=FONT_SMALL, text_color=C["text_muted"])
        self._prog_lbl.grid(row=0, column=0, sticky="w")

        self._counter_lbl = ctk.CTkLabel(stat_row, text="",
                                         font=FONT_SMALL, text_color=C["accent"])
        self._counter_lbl.grid(row=0, column=1, sticky="e")

    # ── Activity Log ──────────────────────────────────────────────────────────
    def _build_log(self, parent, row):
        card = make_card(parent)
        card.grid(row=row, column=0, columnspan=2,
                  padx=16, pady=(12, 24), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        hdr_row = ctk.CTkFrame(card, fg_color="transparent")
        hdr_row.grid(row=0, column=0, padx=16, pady=(14, 6), sticky="ew")
        hdr_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr_row, text="Activity Log",
                     font=FONT_H2, text_color=C["text"]).grid(row=0, column=0, sticky="w")

        self.btn_clear = ctk.CTkButton(
            hdr_row, text="Clear", width=60, height=26,
            font=FONT_SMALL, corner_radius=6,
            fg_color=C["surface2"], hover_color=C["border"],
            text_color=C["text_muted"],
            command=self._clear_log)
        self.btn_clear.grid(row=0, column=1, sticky="e")

        self.log_box = ctk.CTkTextbox(
            card, height=180,
            fg_color=C["surface2"], border_color=C["border"], border_width=1,
            text_color=C["text"], font=FONT_MONO,
            corner_radius=8, state="disabled")
        self.log_box.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")

        self._update_log_tags()

    def _update_log_tags(self):
        """Update standard Tkinter tag configs based on currenct appearance mode"""
        mode = ctk.get_appearance_mode()
        idx = 0 if mode == "Light" else 1
        inner = self.log_box._textbox
        inner.tag_config("ts",      foreground=C["text_muted"][idx])
        inner.tag_config("info",    foreground=C["text_dim"][idx])
        inner.tag_config("success", foreground=C["success"][idx])
        inner.tag_config("error",   foreground=C["danger"][idx])
        inner.tag_config("warning", foreground=C["warning"][idx])

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _step_header(self, parent, num, title, row):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=0, columnspan=2, padx=16, pady=(16, 10), sticky="w")

        badge = ctk.CTkFrame(f, width=26, height=26, corner_radius=6,
                             fg_color=C["accent"])
        badge.pack(side="left", padx=(0, 8))
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=num, font=("Helvetica Neue", 10, "bold"),
                     text_color="white").pack(expand=True)

        ctk.CTkLabel(f, text=title, font=FONT_H2,
                     text_color=C["text"]).pack(side="left")

    def _field_label(self, parent, text, row):
        ctk.CTkLabel(parent, text=text, font=FONT_LABEL,
                     text_color=C["text_dim"]).grid(
            row=row, column=0, columnspan=2, padx=16, pady=(0, 4), sticky="w")

    # ── Help ────────────────────────────────────────────────────────────────────
    def _open_help(self):
        """Open (or focus) the help window."""
        if hasattr(self, "_help_win") and self._help_win.winfo_exists():
            self._help_win.lift()
            self._help_win.focus_force()
        else:
            self._help_win = HelpWindow(self)

    def _change_theme(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        self._update_log_tags()

    # ── UI State ───────────────────────────────────────────────────────────────
    def set_status(self, state: str, label: str):
        self._status_dot.set_state(state)
        self._status_lbl.configure(text=label, text_color={
            "idle":    C["text_muted"],
            "running": C["accent"],
            "success": C["success"],
            "error":   C["danger"],
        }.get(state, C["text_muted"]))

    def update_progress(self, sent, total, label=""):
        frac = (sent / total) if total > 0 else 0
        self._prog_bar.set(frac)
        self._prog_lbl.configure(text=label or f"Sent {sent} / {total}")
        self._counter_lbl.configure(text=f"{int(frac*100)}%" if total else "")

    def toggle_ui_state(self, running: bool):
        state = "disabled" if running else "normal"
        for w in (self.email_entry, self.password_entry,
                  self.btn_browse, self.subject_entry,
                  self.template_text, self.chk_override):
            w.configure(state=state)

        if running:
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal",
                                    fg_color=C["danger"],
                                    text_color="white")
            self.btn_test.configure(state="disabled")
            self.set_status("running", "Campaign running…")
        else:
            self.update_start_button_state()
            self.btn_stop.configure(state="disabled",
                                    fg_color=C["surface2"],
                                    text_color=C["danger"])
            self.btn_test.configure(state="normal")
            self.set_status("idle", "Idle")

    def update_start_button_state(self):
        if self.is_running:
            return
        enabled = self.test_email_sent or self.override_var.get()
        self.btn_start.configure(state="normal" if enabled else "disabled")

    # ── Logging ────────────────────────────────────────────────────────────────
    def log(self, message: str):
        self.after(0, self._append_log, message)

    def _append_log(self, message: str):
        self.log_box.configure(state="normal")
        inner = self.log_box._textbox
        ts = datetime.now().strftime("%H:%M:%S")

        # Determine tag based on message content
        msg_lower = message.lower()
        if "error" in msg_lower or "fail" in msg_lower:
            tag = "error"
        elif "success" in msg_lower or "sent" in msg_lower:
            tag = "success"
        elif "waiting" in msg_lower or "stop" in msg_lower or "warn" in msg_lower:
            tag = "warning"
        else:
            tag = "info"

        inner.insert("end", f"[{ts}] ", "ts")
        inner.insert("end", f"{message}\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    # ── File browse ────────────────────────────────────────────────────────────
    def browse_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv")])
        if filename:
            try:
                base, ext = os.path.splitext(filename)
                results_file = f"{base}_CAMPAIGN{ext}"
                
                if base.endswith("_CAMPAIGN"):
                    self.filepath = filename
                    self.output_path = filename
                elif os.path.exists(results_file):
                    # Ask to resume
                    res = messagebox.askyesno(
                        "Resume Campaign?",
                        f"A campaign results file already exists for this list:\n\n"
                        f"{os.path.basename(results_file)}\n\n"
                        f"Would you like to RESUME this campaign (sending only unsent emails)?"
                    )
                    if res:
                        self.filepath = results_file
                        self.output_path = results_file
                        self.log(f"🔄 Resume mode: Using existing results file.")
                    else:
                        self.filepath = filename
                        self.output_path = results_file
                        self.log(f"🆕 Start fresh: Re-initializing results file.")
                else:
                    self.filepath = filename
                    self.output_path = results_file
                    self.log(f"📂 Loaded: {filename}")
                
                handler = DataHandler(self.filepath, output_path=self.output_path)

                handler.load_data()
                if not handler.has_email_column() and not handler.has_fallback_columns():
                    messagebox.showerror(
                        "Validation Error",
                        "The file MUST have an 'Email' column OR all three: "
                        "'First Name', 'Last Name', 'Company'.")
                    return
                # self.filepath is already set above correctly
                short = self.filepath.split("/")[-1]
                out_short = self.output_path.split("/")[-1]
                self._file_hint.configure(text=f"✅ {short}",
                                          text_color=C["success"])
                self._out_hint.configure(text=f"↳ Campaign Results: {out_short}")
                self.log(f"Results will be saved/updated at: {self.output_path}")
            except Exception as e:

                messagebox.showerror("Validation Error",
                                     f"Could not read file: {e}")


    # ── HTML tag insertion ─────────────────────────────────────────────────────
    def insert_tag(self, start_tag, end_tag):
        try:
            sel_start = self.template_text.tag_ranges("sel")[0]
            sel_end   = self.template_text.tag_ranges("sel")[1]
            selected  = self.template_text.get(sel_start, sel_end)
            self.template_text.delete(sel_start, sel_end)
            self.template_text.insert(sel_start,
                                      f"{start_tag}{selected}{end_tag}")
        except Exception:
            pos = self.template_text.index("insert")
            self.template_text.insert(pos, f"{start_tag}{end_tag}")

    # ── Stop ───────────────────────────────────────────────────────────────────
    def stop_campaign(self):
        self.log("⚠️  Stop requested — finishing current operation…")
        self.stop_event.set()

    # ── Test Email ─────────────────────────────────────────────────────────────
    def send_test_email(self):
        user_email = self.email_entry.get().strip()
        app_pass   = self.password_entry.get().strip()
        subject    = self.subject_entry.get().strip()
        template   = self.template_text.get("1.0", "end-1c").strip()

        if not all([user_email, app_pass, self.filepath, subject, template]):
            messagebox.showerror("Missing Information",
                                 "Please fill out all fields and select a data file.")
            return

        self.is_running = True
        self.stop_event.clear()
        self.toggle_ui_state(True)
        self.set_status("running", "Sending test…")
        self.log("Sending test email to your own address…")
        threading.Thread(target=self.run_test_task,
                         args=(user_email, app_pass, subject, template),
                         daemon=True).start()

    def run_test_task(self, email_addr, app_pass, subject, template):
        data_handler = DataHandler(self.filepath, output_path=self.output_path, logger=self.log)
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
            err_msg = f"Missing columns in data file for placeholders: {', '.join(missing_cols)}"
            self.log(f"ERROR: {err_msg}")
            self.is_running = False
            self.after(0, lambda e=err_msg: messagebox.showerror("Missing Placeholders", e))
            self.after(0, lambda: self.toggle_ui_state(False))
            return

        if not data_handler.has_email_column() and not data_handler.has_fallback_columns():
            self.log("ERROR: Spreadsheet must have 'Email' OR 'First Name', 'Last Name', 'Company'.")
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
            return

        sample_row = data_handler.get_sample_row(placeholders)
        if sample_row is None:
            self.log("ERROR: No fully populated row found for test sample.")
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
            return

        email_sender = EmailSender(email_addr, app_pass, logger=self.log)
        fmt_subj, fmt_html = email_sender.format_content(
            sample_row, template, subject, placeholders)

        try:
            email_sender.connect()
            email_sender.send_email(email_addr, fmt_subj, fmt_html)
            self.log("✅ Test email sent successfully!")
            self.test_email_sent = True
            self.after(0, lambda: self.set_status("success", "Test passed"))
        except smtplib.SMTPAuthenticationError:
            self.log("ERROR: SMTP Authentication failed — check your App Password.")
            self.after(0, lambda: self.set_status("error", "Auth failed"))
        except Exception as e:
            self.log(f"ERROR: {e}")
            self.after(0, lambda: self.set_status("error", "Error"))
        finally:
            email_sender.close()
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))

    # ── Campaign ───────────────────────────────────────────────────────────────
    def start_campaign(self):
        user_email = self.email_entry.get().strip()
        app_pass   = self.password_entry.get().strip()
        subject    = self.subject_entry.get().strip()
        template   = self.template_text.get("1.0", "end-1c").strip()

        if not all([user_email, app_pass, self.filepath, subject, template]):
            messagebox.showerror("Missing Information",
                                 "Please fill out all fields and select a data file.")
            return

        self.is_running = True
        self._emails_sent = 0
        self._emails_total = 0
        self.stop_event.clear()
        self.toggle_ui_state(True)
        self.log("🚀 Starting campaign…")
        threading.Thread(target=self.run_campaign_task,
                         args=(user_email, app_pass, subject, template),
                         daemon=True).start()

    def run_campaign_task(self, email_addr, app_pass, subject, template):
        data_handler = DataHandler(self.filepath, output_path=self.output_path, logger=self.log)
        try:
            data_handler.load_data()
            
            # Initial check for already sent rows
            already_sent = 0
            if 'Status' in data_handler.df.columns:
                already_sent = len(data_handler.df[data_handler.df['Status'].str.lower() == 'sent'])
            
            if already_sent > 0:
                self.log(f"📋 Found {already_sent} recipients already marked as 'Sent'. Skipping them.")
            
        except Exception as e:
            self.log(f"ERROR loading file: {e}")
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
            return

        placeholders = set(re.findall(r'\{\{(.*?)\}\}', template))
        placeholders.update(re.findall(r'\{\{(.*?)\}\}', subject))

        missing_cols = data_handler.get_missing_placeholders(placeholders)
        if missing_cols:
            err_msg = f"Missing columns in data file for placeholders: {', '.join(missing_cols)}"
            self.log(f"ERROR: {err_msg}")
            self.is_running = False
            self.after(0, lambda e=err_msg: messagebox.showerror("Missing Placeholders", e))
            self.after(0, lambda: self.toggle_ui_state(False))
            return

        if not data_handler.has_email_column() and not data_handler.has_fallback_columns():
            self.log("ERROR: Spreadsheet missing required columns.")
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
            return

        email_sender      = EmailSender(email_addr, app_pass, logger=self.log)
        derivation_service = EmailDerivationService(logger=self.log)

        try:
            email_sender.connect()
        except Exception as e:
            self.log(f"ERROR connecting to SMTP: {e}")
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
            return

        total_rows = len(data_handler.df)
        self._emails_total = total_rows
        rows_processed = 0

        try:
            for index, row in data_handler.df.iterrows():
                if self.stop_event.is_set():
                    self.log("Campaign stopped by user.")
                    break

                target_email = ""
                if data_handler.email_col and not pd.isna(row[data_handler.email_col]):
                    target_email = str(row[data_handler.email_col]).strip()

                status = str(row.get('Status', '')).strip().lower()

                if target_email in ('', 'nan'):
                    fn = row.get('First Name', '')
                    ln = row.get('Last Name', '')
                    co = row.get('Company', '')
                    target_email = derivation_service.guess_email(fn, ln, co)

                if not target_email:
                    self.log(f"Row {index}: No email and derivation failed — skipping.")
                    continue

                if status == 'sent':
                    continue

                formatted_subj, formatted_html = email_sender.format_content(
                    row, template, subject, placeholders)

                if formatted_html is None:
                    self.log(f"Row {index} → {target_email}: blank placeholder — skipping.")
                    continue

                self.log(f"Sending to {target_email}…")
                try:
                    email_sender.send_email(target_email, formatted_subj, formatted_html)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    data_handler.mark_sent(index, timestamp)
                    rows_processed += 1
                    self.log(f"✅ Sent successfully → {target_email}")
                    self.after(0, lambda s=rows_processed, t=total_rows:
                               self.update_progress(s, t, f"Sent {s} of {t}"))
                except Exception as e:
                    self.log(f"Failed → {target_email}: {e}")
                    continue

                if not self.stop_event.is_set():
                    delay = random.randint(45, 90)
                    self.log(f"⏳ Throttling — waiting {delay}s before next email…")
                    for _ in range(delay):
                        if self.stop_event.is_set():
                            break
                        time.sleep(1)

            self.log(f"✅ Campaign complete — {rows_processed} email(s) sent this run.")
            self.after(0, lambda: self.set_status("success",
                                                   f"Done — {rows_processed} sent"))
        finally:
            email_sender.close()
            self.is_running = False
            self.after(0, lambda: self.toggle_ui_state(False))
            self.after(0, lambda: self._prog_bar.set(1 if rows_processed else 0))
