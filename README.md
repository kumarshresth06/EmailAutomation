# Cold Outreach Automator

A robust, simple-to-use desktop application built in Python for automating personalized cold outreach email campaigns. 

The software ingests contact data from `.csv` and `.xlsx` files, dynamically templates fields utilizing `{{Column_Name}}` replacement logic against an injected HTML UI template, throttles outgoing requests to mitigate Gmail spam flags, and intrinsically saves the state of the iteration per-batch so no emails are sent redundantly.

## ⚙️ Project Design & Architecture
To sustain a scalable and testable logic matrix, the monolithic structure has been broken out into encapsulated components adhering to single-responsibility bounds:

- **`main.py`**: The application router pulling up the main threading loop.
- **`app_ui.py`**: A `customtkinter` based graphical user interface representing the frontend layer. Validates states, runs async threading for sending loops, exposes logging feedback.
- **`data_service.py`**: Data extraction handler (`DataHandler` object layer). Ingests Pandas DataFrames, executes constraint checks against `NaN/Empty` values, creates/manages `Status` flags marking which targets have been serviced, and immediately saves to disk to protect data retention mid-crash.
- **`email_service.py`**: Direct SMTP client class (`EmailSender`). Marshals dynamic formatting mechanisms connecting `{{Column}}` constraints cleanly against strings, and manages secure packet transport via `smtplib` + `MIMEText`.

## 🚀 Features & Functionality
- **Rich Text HTML Editor Inline**: The main dashboard possesses formatting logic wrapping highlighted strings locally in `<b>`, `<i>`, or `<a href="...">` nodes dynamically. Use double braces `{{}}` directly mapped to columns.
- **Test-First Safety Policy**: By default, the `Start Campaign` button is restricted dynamically. You *must* fire a `Send Test Email` first, which samples your first clean dataset row, configures the output, and shoots it directly back into your linked login inbox. Alternatively, check the `Override` box to bypass.
- **Automated Anti-Spam Human Emulator**: In bulk mode, trailing successful dispatches face a mandatory jitter-delay traversing a `45-90` seconds timeout constraint natively thwarting rapid-burst suspension penalties standard on generic Gmail accounts.
- **Idempotency**: It implicitly traces iterations under tracking columns `Status` & `Date_Sent` injected intelligently on start. Subsequent batch restarts skip emails designated successfully "Sent".

## 🛠 Usage
1. Provide standard Python `3.9+` environment.
2. Install standard configurations:
   ```bash
   pip3 install -r requirements.txt
   ```
3. Boot the application instance:
   ```bash
   python3 main.py
   ```
4. Input App Passwords (Make sure standard `2-Step Verification` is mapped on your active Gmail), browse a CSV target containing `Email` columns, inject HTML logic, and execute!

## 🧪 Tests Configuration 
The backend structures are secured against automated validation sweeps. Built using `pytest`, ensuring secure behavior handling null validations natively, and leveraging library `unittest.mock` configurations mapping to SMTP instances so local execution ignores networking requests.

To run the full suite:
```bash
python3 -m pytest tests/
```
Or native fallback:
```bash
pytest tests/
```
