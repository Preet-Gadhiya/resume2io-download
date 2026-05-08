# resume2io-download

Download your [resume.io](https://resume.io) resume as a PDF. Works on free accounts.

resume.io puts PDF export behind a paywall. This tool spins up a headless browser, loads your resume editor with your session cookie, screenshots each page from the canvas, and saves it as a PDF.

---

## Quick start

```bash
git clone https://github.com/Preet-Gadhiya/resume2io-download.git
cd resume2io-download
docker build -t resume2io-download .
docker run -p 8000:8000 resume2io-download
```

Open http://localhost:8000

---

## How to download your resume

### Step 1: Find your Resume ID

Open your resume in the editor and look at the URL:

```
https://resume.io/app/resumes/69570346/edit
                              ^^^^^^^^
                              this is your resume ID
```

### Step 2: Get your session cookie

You need the `_session_id` cookie value from your browser while logged in to resume.io.

**Chrome or Edge:**
1. Go to resume.io and log in
2. Open DevTools (F12 or right-click -> Inspect)
3. Go to the **Application** tab
4. In the left sidebar, expand **Cookies** and click `https://resume.io`
5. Find `_session_id` and copy the value

**Firefox:**
1. Open DevTools -> **Storage** tab
2. Expand **Cookies** -> `https://resume.io`
3. Copy the value of `_session_id`

The cookie expires when you log out or after roughly 30 days. If you get a 401 error, just grab a fresh one.

### Step 3: Download

1. Open http://localhost:8000
2. Enter your resume ID (just the numbers, e.g. `69570346`)
3. Paste your `_session_id` value
4. Click **Download PDF**

It takes around 15-30 seconds while the browser renders the resume. The PDF will download automatically.

---

## API

If you prefer curl:

```bash
curl -X POST "http://localhost:8000/download/69570346" \
  -H "X-Session-Id: your_session_id_here" \
  -o resume.pdf
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

This is for downloading your own resume. Please use it responsibly.
