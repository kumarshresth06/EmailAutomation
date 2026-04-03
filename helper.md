# How to Define Placeholders

Since we are using a Rich Text (HTML) template, the easiest and most standard way to define placeholders is using double curly braces that exactly match your Excel column headers.

For example, if your Excel sheet has columns named **Name**, **Company**, and **Role**, your email template would look like this:

> Hi {{Name}},
>
> I was looking at the recent work {{Company}} is doing and was really impressed. I'm reaching out because I saw you are hiring for the {{Role}} position, and my background as a Software Engineer makes me a great fit.
>
> You can view my resume here: [Link to Google Drive]

The software will read the column headers and automatically swap the tags with the corresponding row data.

---

# Guide: Setting Up Gmail App Passwords

Since you are using a third-party script to access your Gmail, Google requires a specific 16-character "App Password" to bypass standard web login. Here is how to get it:

1. **Enable 2-Step Verification:** Go to your Google Account Security page. Scroll down to "How you sign in to Google" and ensure 2-Step Verification is turned ON. *(You cannot generate an App Password without this).* 

2. **Find App Passwords:** On that same Security page, use the search bar at the top and type "App passwords". *(Google recently moved this menu, so searching is the fastest way to find it).*

3. **Create the Password:** 
    * You may be prompted to enter your normal Google password to verify it's you.
    * In the "Select app" dropdown, choose **Mail**.
    * In the "Select device" dropdown, choose **Other (Custom name)** and type something like *"Cold Email Script"*.
    * Click **Generate**.

4. **Save it:** A yellow box will appear with a 16-character code. Copy this and save it somewhere safe. You will paste this into our software's UI. Google will not show you this code again once you close the window.

---

# Required Data Format (CSV/Excel)

The application accepts data files in both **CSV (`.csv`)** and **Excel (`.xlsx`)** formats. For the software to correctly read your contacts and populate the templates, ensure your spreadsheet conforms to the following rules:

1. **Mandatory Placeholders:**
    * The spreadsheet **MUST** include a column representing the recipient's email named exactly **`Email`** or **`email`**.
    * **Alternatively**, if exact emails are unknown, your spreadsheet MUST contain exactly these three columns: **`First Name`**, **`Last Name`**, and **`Company`**.

2. **Additional Placeholders:**
    * A user might want some additional placeholders. You can define any placeholder in the email template using the format `{{PLACEHOLDER_NAME}}`.
    * The name **MUST** be present in the attached Excel/CSV file as a column.
    * **If any placeholder used in your template is completely missing from your file, the system will throw an error.** The column name mapping is case-insensitive, meaning `{{Role}}` in your template will match a column named `role` or `ROLE` in your file.

3. **Tracking Columns (Auto-Generated):**
    * The script will automatically add two columns to your file: **`Status`** and **`Date_Sent`**.
    * `Status` will be updated to *"Sent"* when an email successfully fires off.
    * `Date_Sent` records the timestamp of operation.
    * **Tip:** Because it relies on these columns, it will not send duplicates. Do not remove or manually edit them while a campaign is paused or ongoing.

---

# Application Features & Flow Guidelines

1. **HTML Formatting Toolbar:**
    * Directly above the text template section are quick formatting buttons (`B`, `I`, `Link`, `Paragraph`, `Line Break`).
    * You can highlight any string in your workspace and click a button to instantly wrap it in standard HTML tags, empowering users to compose rich emails straight from the UI without requiring an external IDE.
    * For custom links, insert the link frame, then manually change `"URL_HERE"` to the hyperlink of your preference while leaving the `""` quotes untouched.

2. **Test-First Validation Policies:**
    * Mass-emailing cold contacts entails a high risk of bounce rates if a template is accidentally incorrectly routed. Thus, the system enables an enforced policy.
    * **By default, the `Start Campaign` bulk tool will be greyed out.** You cannot start a full run out of the gate.
    * You must fill out the criteria and click the **`Send Test Email`** parameter first. It will scrape the very first fully-populated row from your imported sheet and attempt to transmit a customized sample strictly to your inbox.
    * Once this action runs returning an affirmative condition, the `Start Campaign` functionality will light up.
    * *Power User Override:* A checkbox titled **"Override Test Valid."** exists alongside it. When checked, the start action becomes immediately accessible.

3. **Dynamic Email Derivation (Google Search Scraper):**
    * If your uploaded spreadsheet misses an exact `Email` column completely, the system triggers the derivation engine inline.
    * It scrubs probable domains from the supplied `Company` strings, generates standard corporate heuristics (`first.last`, `f_last`, etc.), and actively pipes queries against Google implicitly via HTTP headers!
    * By evaluating HTML search returns for recognized regex overlaps against the inferred domain, it dynamically executes its 'best shot' to pull a finalized mailing constraint prior to failure.

4. **In-Built Anti-Spam Throttling:**
    * Sending dozens of synchronized emails sequentially often flags standard Google accounts as aggressive spam vectors, leading to suspension tracking limits.
    * This software leverages a randomly generated wait window ranging strictly between **45 to 90 seconds** traversing successive dispatches. 
    * Please account for this intended operational behavior in your workflow cadence.