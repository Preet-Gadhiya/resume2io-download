# resume2io-download

Download your [resume.io](https://resume.io) resume or cover letter as a PDF. Works on free accounts.

resume.io puts PDF export behind a paywall. This tool opens your document editor in a headless browser, waits for the canvas to render, screenshots each page, and saves it as a PDF.

---

## Quick start

```bash
git clone https://github.com/Preet-Gadhiya/resume2io-download.git
cd resume2io-download
docker compose up --build
```

Open http://localhost:8000

If port 8000 is already in use on your machine:

```bash
PORT=8001 docker compose up --build
```

---

## How to download your document

### Step 1: Find your Document ID

Open your resume or cover letter in the editor and look at the URL:

```
https://resume.io/app/resumes/69570346/edit
                              ^^^^^^^^
                              this is your document ID
```

### Step 2: Get your session cookie

You need the `_session_id` cookie value from your browser while logged in to resume.io.

**Chrome or Edge:**
1. Go to resume.io and log in
2. Open DevTools (F12 or right-click -> Inspect)
3. Go to the **Application** tab
4. In the left sidebar expand **Cookies** and click `https://resume.io`
5. Find `_session_id` and copy the value

**Firefox:**
1. Open DevTools -> **Storage** tab
2. Expand **Cookies** -> `https://resume.io`
3. Copy the value of `_session_id`

The cookie expires when you log out or after roughly 30 days. If you get a 401 error, grab a fresh one.

### Step 3: Download

1. Open http://localhost:8000
2. Pick **Resume** or **Cover Letter**
3. Enter your document ID
4. Paste your `_session_id` value
5. Click **Download PDF**

Takes around 15-30 seconds while the browser renders the document.

---

## API

```bash
# Resume
curl -X POST "http://localhost:8000/download/resume/69570346" \
  -H "X-Session-Id: your_session_id_here" \
  -o resume.pdf

# Cover letter
curl -X POST "http://localhost:8000/download/cover_letter/12345678" \
  -H "X-Session-Id: your_session_id_here" \
  -o cover_letter.pdf
```

---

## Running without Docker

You need Python 3.12+ and [uv](https://github.com/astral-sh/uv).

```bash
uv sync
python -m playwright install chromium
python app/main.py
```

---

## Disclaimer

This is for downloading your own documents. Please use it responsibly.
