*Automation-Mail-Send*

**Email Automation using Python, Google Scripts & No-Code Tools**

This repository contains multiple approaches to automate sending emails — from simple Python scripts to advanced workflows using Google Apps Script, Zapier, and HTML-styled emails. Each method is documented with its advantages, limitations, and implementation procedure so users can choose the best technique for their needs.


## **Why This Project?**

Email automation is essential for:

* Sending newsletters
* Placement/Recruiter emails
* Bulk academic communication
* Personalized outreach
* Reminder and scheduled campaigns

However, different use-cases require different methods.
Here, you will find **four complete automation workflows**, each with unique strengths.


# ** Methods Included in This Repository**

# **1. Sending Emails Using BCC (Basic Method)**

This is the simplest and quickest way to send the same email to multiple recipients:
Add all emails in **BCC** and send one message.

### Pros

* Extremely easy
* Works in Gmail, Outlook, or any client
* No coding required

### Cons (Important)

* *Looks unprofessional* for formal communication
* Higher chance of going to **Spam**
* Impossible to personalize each recipient’s name
* Many companies block bulk BCC emails
* Not scalable for 100+ recipients


# **2. Automation Using Claude AI + Zapier via MCP Server**

This method combines **Claude AI**, **Zapier**, and a custom-built **MCP (Mail Control Processor) Server** to fully automate personalized email generation and sending. This approach is ideal if you want AI-generated emails, structured workflows, and a scalable system for large outreach campaigns.


## **How It Works**

1. You maintain recipient data in **Google Sheets**.
2. **Zapier** detects a new row (or scheduled batch).
3. Zapier sends the row data to the **MCP Server** (a FastAPI backend).
4. MCP processes the request:

   * Builds a prompt using your custom template
   * Calls **Claude AI** to generate the email subject + HTML body
   * Stores result in SQLite
   * Optionally sends email automatically via SMTP
5. Zapier/Gmail sends the email OR MCP triggers the send itself.


## **MCP Server (Mail Control Processor)**

The MCP server is a lightweight backend that handles:

* AI prompt building
* Calling Claude API
* Rate limiting (preventing token overuse)
* Queueing & retries
* Email templating (HTML via Jinja2)
* Storing generated emails
* Sending via SMTP/Gmail
* Exposing endpoints to Zapier (`/generate_email`, `/status`, `/send_now`)

This ensures the entire pipeline is **reliable**, **async**, and perfectly scalable.


##**Sample Claude Prompt Used by MCP**

```txt
Generate a professional email inviting the recruiter to campus placements.
Use recipient_name, company_name, role, and extra metadata from the payload.
Return output as: 
Line 1 → email subject 
Remaining → full HTML email body.
```

---

## **Zapier Setup**

### **Trigger**

* **New Row in Google Sheets**

### **Action 1**

* **Webhooks by Zapier → POST**
* URL:

  ```
  https://your-mcp-host/generate_email
  ```
* Body (JSON):

  ```json
  {
    "recipient_name": "{{Name}}",
    "recipient_email": "{{Email}}",
    "company_name": "{{Company}}",
    "role": "{{Role}}"
  }
  ```

* Gmail → Send Email
* Use MCP-generated subject + HTML body (via `/status/{job_id}` polling or webhook).

## **Advantages**

* Fully automated personalized email generation
* Supports HTML templates
* Claude AI improves tone, structure, and personalization
* MCP server handles retries, failures, and rate limits
* Scalable for **hundreds or thousands** of emails
* No need for local Python execution — everything runs in cloud

## **Limitations**

* Requires server deployment (Render, Railway, EC2, etc.)
* Claude API usage is billable
* Zapier free plan has task limits
* MCP must be secured with API keys/HTTPS
* Setup complexity is higher than basic Python scripts

## **MCP Server Code (Short Version)**

The full MCP server (FastAPI + Queue + Claude API) is available in this repo.
Here is a **minimal example** of the `/generate_email` endpoint:

```python
@app.post("/generate_email")
async def generate_email(req: GenerateRequest):
    job_id = await enqueue_job(req)
    return {"job_id": job_id, "status": "enqueued"}
```

To run MCP:

```bash
uvicorn mcp_server:app --host 0.0.0.0 --port 8000
```

---

## Why Use This Method?

If you want **AI-level personalization**, **automated sending**, and **enterprise-grade scaling**, this method is the best.
You can:

* Add custom prompting logic
* Track delivery status
* Build dashboards for recruiters
* Schedule batches
* Add analytics later

This solution is essentially a **mini email-automation service powered by AI**, fully under your control.

# **3. Python Automation with HTML Email (main.py)**

This method uses **Python + SMTPLib + HTML templates** to send professional-looking emails.

### ** Features**

* HTML email formatting
* Send to multiple recipients
* Uses Gmail App Password (secure)
* Can embed logos, links, and styled text
* Easy to modify for campaigns

### ** Tech Used**

* `smtplib`
* `ssl`
* `email.mime`
* `pandas` (optional for Excel input)

### ** How to Run**

```bash
pip install -r requirements.txt
python main.py
```

### ** Pros**

* Fully customizable
* Supports HTML & attachments
* No external tools or subscriptions
* Professional looking emails

###  Cons

* Must generate Gmail App Password
* Some servers limit daily sending
* Requires basic Python setup

# **4. Mail Merge Using Google Apps Script (Improved Version)**

This is an advanced method where you use:

* **Google Sheets** → store recipient list
* **Google Apps Script (.gs)** → send mails
* **Custom improvements done by me:**

  * Add **labels** to sent emails
  * **Schedule** mails automatically
  * Personalized subject lines
  * Better logging + fail-safe system

### ** How It Works**

1. Paste script into Google Sheets → Extensions → Apps Script
2. Update sheet names + template
3. Run manually or enable triggers

### **Example Code Snippet**

```javascript
var label = GmailApp.getUserLabelByName("Placement2025");
label.addToThread(sentMail);
```

### ** Pros**

* 100% free
* No Python installation needed
* Can schedule entire campaigns
* Works directly inside Gmail
* Very reliable for bulk sending

### Cons

* limited by Gmail daily quota
* No HTML CSS styling as rich as Python
* Google Script debugging is slightly tricky

---

#  **Repository Structure**

```
Automation-mail-send/
│
├── main.py                 # Python HTML email automation
├── automation.py           # Improved Google Apps Script mail merge
├── sample_email_template.html
├── sample_dataset.xlsx
└── README.md
```


# When Should You Use Which Method?

| Method                       | Use Case                                 | Pros         | Cons             |
| ---------------------------- | ---------------------------------------- | ------------ | ---------------- |
| **BCC**                      | One-time quick mails                     | Easy         | Unprofessional   |
| **Claude + Zapier**          | AI-personalized email campaigns          | No code      | Paid             |
| **Python HTML (main.py)**    | Professional outreach, bulk formal mails | Full control | Setup needed     |
| **Google Script Mail Merge** | Free bulk mail, scheduled                | No install   | Script debugging |


