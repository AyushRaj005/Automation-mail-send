!pip install fastapi uvicorn aiohttp aiosqlite jinja2 python-dotenv
# for SMTP sending:
!pip install aiosmtplib
# mcp_server.py
import os
import json
import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta

import aiohttp
import aiosqlite
from jinja2 import Template
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
from aiosmtplib import SMTP, SMTPException

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")  # replace securely
CLAUDE_API_URL = os.getenv("CLAUDE_API_URL", "https://api.your-claude-provider/v1/generate")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")  # use app password

DB_PATH = os.getenv("MCP_DB", "mcp_jobs.db")
MAX_CONCURRENT_WORKERS = int(os.getenv("MAX_WORKERS", "2"))
LLM_RATE_LIMIT_PER_MIN = int(os.getenv("LLM_RATE_LIMIT_PER_MIN", "60"))  # adjustable

logger = logging.getLogger("mcp")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="MCP (Mail Control Processor)")

# Async queue & worker tokens for rate-limiting
task_queue: asyncio.Queue = asyncio.Queue()
llm_tokens = asyncio.Semaphore(LLM_RATE_LIMIT_PER_MIN)  # crude rate control


class GenerateRequest(BaseModel):
    recipient_name: Optional[str]
    recipient_email: EmailStr
    company_name: Optional[str]
    role: Optional[str] = None
    extra: Optional[dict] = None  # arbitrary per-row metadata


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_email TEXT,
            recipient_name TEXT,
            company_name TEXT,
            role TEXT,
            extra TEXT,
            status TEXT,
            subject TEXT,
            html TEXT,
            created_at TEXT,
            updated_at TEXT,
            attempts INTEGER DEFAULT 0,
            error TEXT
        )
        """)
        await db.commit()

@app.on_event("startup")
async def startup_event():
    await init_db()
    # start background workers
    for i in range(MAX_CONCURRENT_WORKERS):
        asyncio.create_task(worker_loop(i))


async def enqueue_job(payload: GenerateRequest) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.utcnow().isoformat()
        await db.execute(
            "INSERT INTO jobs (recipient_email, recipient_name, company_name, role, extra, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                payload.recipient_email,
                payload.recipient_name,
                payload.company_name,
                payload.role,
                json.dumps(payload.extra or {}),
                "PENDING",
                now, now
            )
        )
        await db.commit()
        cur = await db.execute("SELECT last_insert_rowid()")
        row = await cur.fetchone()
        job_id = row[0]
    await task_queue.put(job_id)
    return job_id


@app.post("/generate_email")
async def generate_email(req: GenerateRequest):
    job_id = await enqueue_job(req)
    return {"job_id": job_id, "status": "enqueued"}


@app.get("/status/{job_id}")
async def status(job_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="job not found")
        columns = [c[0] for c in cur.description]
        return dict(zip(columns, row))


# Templating - Jinja2 template for prompt and email body
PROMPT_TEMPLATE = """
You are a professional communications assistant. Compose a short, formal, and personalized email invite for campus recruitment.
Recipient Name: {{ recipient_name }}
Company: {{ company_name }}
Role: {{ role }}
Extra Data: {{ extra }}

Requirements:
- Subject line (1 short sentence).
- Full HTML email body, using polite formal tone. Include a call to action to fill the Job Notification Form link: {{ jnf_link }}
- Keep it concise (max 250 words).
"""

EMAIL_HTML_TEMPLATE = """
<!doctype html>
<html>
  <body>
    <p>Dear {{ recipient_name }},</p>
    <p>
      Warm greetings from National Institute of Technology Meghalaya.
    </p>
    <p>
      We would like to invite {{ company_name }} to participate in our campus placements for {{ role or 'multiple roles' }}.
      Please fill the Job Notification Form here: <a href="{{ jnf_link }}">{{ jnf_link }}</a>.
    </p>
    <p>Regards,<br/>Centre for Career Development, NIT Meghalaya</p>
  </body>
</html>
"""

JNF_LINK = os.getenv("JNF_LINK", "https://example.com/job-notification-form")


async def call_claude_api(prompt_text: str) -> dict:
    """Generic async call to LLM endpoint — replace details with your provider's API."""
    headers = {
        "Authorization": f"Bearer {CLAUDE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt_text,
        "max_tokens": 800
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(CLAUDE_API_URL, headers=headers, json=payload, timeout=60) as resp:
            text = await resp.text()
            if resp.status != 200:
                logger.error("LLM API error %s: %s", resp.status, text)
                raise Exception(f"LLM API error: {resp.status}")
            # Adapt parsing depending on LLM provider response shape
            try:
                data = await resp.json()
            except:
                data = {"raw_text": text}
            return data


async def generate_using_llm(job_id: int, job_row: dict):
    # Build prompt
    prompt_t = Template(PROMPT_TEMPLATE)
    prompt = prompt_t.render(
        recipient_name=job_row["recipient_name"] or "Recruiter",
        company_name=job_row["company_name"] or "",
        role=job_row["role"] or "",
        extra=json.loads(job_row["extra"] or "{}"),
        jnf_link=JNF_LINK
    )

    # crude rate limiting: allow at most LLM_RATE_LIMIT_PER_MIN requests per minute.
    # Here we use a semaphore and sleep - for production, use token bucket or external rate limiter.
    async with llm_tokens:
        # release token after 60/limit seconds
        revoke_delay = 60.0 / max(1, LLM_RATE_LIMIT_PER_MIN)
        asyncio.create_task(release_llm_token_after_delay(revoke_delay))

        logger.info("Calling LLM for job %s", job_id)
        api_resp = await call_claude_api(prompt)

        # parse output; provider-specific. Replace this by your chosen mapping
        # Example: assume api_resp contains {"choices":[{"text": "...subject\n\n<html>..."}]}
        output_text = ""
        if isinstance(api_resp, dict):
            # crude extraction
            output_text = api_resp.get("output_text") or api_resp.get("choices", [{}])[0].get("text") or str(api_resp)
        else:
            output_text = str(api_resp)

    # Simple split: first line -> subject, rest -> html
    # You should use more robust parsing or JSON-formatted LLM response
    subject = (output_text.splitlines()[0] if output_text else "Campus Placement Invitation")
    body_html = "\n".join(output_text.splitlines()[1:]) or Template(EMAIL_HTML_TEMPLATE).render(
        recipient_name=job_row["recipient_name"] or "Recruiter",
        company_name=job_row["company_name"] or "",
        role=job_row["role"] or "",
        jnf_link=JNF_LINK
    )
    return {"subject": subject.strip(), "html": body_html}


async def release_llm_token_after_delay(delay):
    await asyncio.sleep(delay)
    try:
        llm_tokens.release()
    except Exception:
        pass


async def worker_loop(worker_id: int):
    logger.info("Worker %d started", worker_id)
    while True:
        job_id = await task_queue.get()
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                cur = await db.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
                row = await cur.fetchone()
                if not row:
                    logger.error("Job not found: %s", job_id)
                    continue
                desc = [d[0] for d in cur.description]
                job_row = dict(zip(desc, row))

            # Attempt generation with retries
            attempts = 0
            max_attempts = 3
            backoff = 2
            while attempts < max_attempts:
                try:
                    await update_job_status(job_id, "IN_PROGRESS")
                    llm_result = await generate_using_llm(job_id, job_row)
                    await save_generated(job_id, llm_result["subject"], llm_result["html"])
                    # Optionally, send automatically:
                    # await send_email_smtp(job_row["recipient_email"], llm_result["subject"], llm_result["html"])
                    await update_job_status(job_id, "READY")
                    break
                except Exception as e:
                    attempts += 1
                    await update_job_attempts(job_id, attempts, str(e))
                    logger.exception("Error generating for job %s attempt %s", job_id, attempts)
                    await asyncio.sleep(backoff ** attempts)
            else:
                await update_job_status(job_id, "FAILED")
        except Exception as e:
            logger.exception("Worker loop fatal error")
        finally:
            task_queue.task_done()


async def update_job_status(job_id: int, status: str):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE jobs SET status=?, updated_at=? WHERE id=?", (status, now, job_id))
        await db.commit()


async def update_job_attempts(job_id: int, attempts: int, error_text: str = ""):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE jobs SET attempts=?, error=?, updated_at=? WHERE id=?", (attempts, error_text, now, job_id))
        await db.commit()


async def save_generated(job_id: int, subject: str, html: str):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE jobs SET subject=?, html=?, updated_at=? WHERE id=?", (subject, html, now, job_id))
        await db.commit()


# Example SMTP send function
async def send_email_smtp(to_email: str, subject: str, html_body: str, from_email: Optional[str] = None):
    message = f"From: {from_email or SMTP_USER}\r\nTo: {to_email}\r\nSubject: {subject}\r\nContent-Type: text/html\r\n\r\n{html_body}"
    try:
        smtp = SMTP(hostname=SMTP_HOST, port=SMTP_PORT, use_tls=True)
        await smtp.connect()
        await smtp.login(SMTP_USER, SMTP_PASS)
        await smtp.sendmail(SMTP_USER, [to_email], message)
        await smtp.quit()
        logger.info("Sent email to %s", to_email)
    except SMTPException as e:
        logger.exception("SMTP send failed")
        raise


@app.post("/send_now/{job_id}")
async def send_now(job_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT recipient_email, subject, html FROM jobs WHERE id=?", (job_id,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="job not found")
        recipient_email, subject, html = row
    if not subject or not html:
        raise HTTPException(status_code=400, detail="job not ready")
    try:
        await send_email_smtp(recipient_email, subject, html)
        await update_job_status(job_id, "SENT")
        return {"status": "sent"}
    except Exception as e:
        await update_job_status(job_id, "SEND_FAILED")
        return {"status": "failed", "error": str(e)}
