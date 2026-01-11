from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, Request
from fastapi.responses import FileResponse, HTMLResponse
import shutil, tempfile, os, subprocess, uuid, math

app = FastAPI()

# ---------------------------
# FAQ RENDERER
# ---------------------------
def render_faq(faqs):
    faq_html = ""
    for q, a in faqs:
        faq_html += f"""
        <div class="faq-item">
            <button class="faq-question" onclick="this.nextElementSibling.classList.toggle('open')">
                {q}
            </button>
            <div class="faq-answer">{a}</div>
        </div>
        """
    return f"""
    <div class="faq">
        <h3>Frequently Asked Questions</h3>
        {faq_html}
    </div>
    """

# ---------------------------
# HTML PAGE RENDERER
# ---------------------------
def render_page(title, heading, intro, default_kb, request: Request,
                faqs, readonly=True, show_hint=True):

    path = request.url.path
    readonly_attr = "readonly" if readonly else ""

    def tab(url):
        return "active" if path == url else ""

    hint_html = (
        f'<div class="hint">Target size: under <strong>{default_kb} KB</strong></div>'
        if show_hint else ""
    )

    return f"""
<!DOCTYPE html>
<html>
<head>
<title>{title}</title>
<meta name="description" content="{intro}">
<style>
body {{
    font-family: Arial, sans-serif;
    background: #f5f7fa;
    display: flex;
    flex-direction: column;
    align-items: center;
}}

.nav {{
    margin-top: 20px;
    display: flex;
    gap: 10px;
}}

.nav a {{
    text-decoration: none;
    font-size: 13px;
    padding: 6px 12px;
    border-radius: 20px;
    background: #e5e7eb;
    color: #111827;
}}

.nav a.active, .nav a:hover {{
    background: #4f46e5;
    color: white;
}}

.card {{
    background: white;
    margin-top: 30px;
    padding: 30px;
    border-radius: 10px;
    width: 360px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    text-align: center;
}}

.hint {{
    font-size: 13px;
    color: #2563eb;
}}

input, button {{
    width: 100%;
    margin-top: 12px;
    padding: 10px;
    font-size: 14px;
}}

input[readonly] {{
    background: #f1f5f9;
}}

button {{
    background: #4f46e5;
    color: white;
    border: none;
    border-radius: 6px;
}}

.loading {{
    display: none;
    margin-top: 15px;
    color: #2563eb;
}}

.spinner {{
    margin: 10px auto;
    width: 26px;
    height: 26px;
    border: 3px solid #c7d2fe;
    border-top: 3px solid #4f46e5;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}}

@keyframes spin {{
    0% {{ transform: rotate(0deg); }}
    100% {{ transform: rotate(360deg); }}
}}

.faq {{
    margin: 40px 0;
    width: 360px;
}}

.faq h3 {{
    font-size: 16px;
    margin-bottom: 10px;
}}

.faq-item {{
    margin-bottom: 8px;
}}

.faq-question {{
    width: 100%;
    background: #eef2ff;
    color: #1e1b4b;
    padding: 10px;
    border: none;
    text-align: left;
    border-radius: 6px;
    cursor: pointer;
}}

.faq-answer {{
    display: none;
    padding: 10px;
    font-size: 13px;
    color: #374151;
}}

.faq-answer.open {{
    display: block;
}}
</style>
</head>

<body>

<div class="nav">
  <a href="/passport-pdf-size" class="{tab('/passport-pdf-size')}">Passport (100 KB)</a>
  <a href="/compress-pdf-200kb" class="{tab('/compress-pdf-200kb')}">200 KB</a>
  <a href="/government-form-pdf" class="{tab('/government-form-pdf')}">Govt Forms</a>
  <a href="/compress-pdf-500kb" class="{tab('/compress-pdf-500kb')}">500 KB</a>
  <a href="/" class="{tab('/')}">Custom</a>
</div>

<div class="card">
<h2>{heading}</h2>
<p>{intro}</p>
{hint_html}

<form id="uploadForm" action="/compress" method="post" enctype="multipart/form-data"
      onsubmit="startLoading()">
<input type="file" name="file" accept="application/pdf" required>
<input type="number" name="target_kb" value="{default_kb}" {readonly_attr} required>
<button id="submitBtn">Compress PDF</button>
</form>

<div class="loading" id="loading">
<div class="spinner"></div>
Compressing your PDF… please wait.
</div>
</div>

{render_faq(faqs)}

<script>
function startLoading() {{
    document.getElementById("submitBtn").disabled = true;
    document.getElementById("uploadForm").style.display = "none";
    document.getElementById("loading").style.display = "block";
}}
</script>

</body>
</html>
"""

# ---------------------------
# ROUTES WITH PAGE-SPECIFIC FAQ
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    faqs = [
        ("Can I compress PDF to any size?", "Yes, you can choose a custom size like 250 KB, 500 KB or more."),
        ("Why PDF cannot go below certain size?", "Some PDFs already contain optimized text and images."),
        ("Is this tool free?", "Yes, this tool is completely free to use."),
        ("Is my PDF safe?", "Your file is processed temporarily and deleted automatically.")
    ]
    return render_page("Compress PDF Online", "Compress PDF to Any Size",
                       "Reduce PDF size to any required limit.", 500, request, faqs, readonly=False, show_hint=False)

@app.get("/passport-pdf-size", response_class=HTMLResponse)
def passport_pdf(request: Request):
    faqs = [
        ("Why passport PDF must be under 100 KB?", "Most passport portals enforce strict size limits."),
        ("Will text or photo become unclear?", "Text remains readable; images are optimized safely."),
        ("Is Aadhaar or passport data safe?", "Files are deleted after processing.")
    ]
    return render_page("Passport PDF Size < 100KB", "Reduce Passport PDF Size",
                       "Compress passport PDF below 100KB.", 100, request, faqs)

@app.get("/compress-pdf-200kb", response_class=HTMLResponse)
def pdf_200kb(request: Request):
    faqs = [
        ("Why 200 KB limit is common?", "Many government forms accept PDFs under 200 KB."),
        ("Can I compress multiple times?", "Yes, you can re-upload and compress again."),
    ]
    return render_page("Compress PDF to 200KB", "Compress PDF to 200KB",
                       "Reduce PDF size below 200KB.", 200, request, faqs)

@app.get("/government-form-pdf", response_class=HTMLResponse)
def govt_pdf(request: Request):
    faqs = [
        ("Do states have different limits?", "Yes, some states accept 300 KB, others 500 KB."),
        ("Is this suitable for govt forms?", "Yes, it is designed for govt uploads."),
    ]
    return render_page("Govt Form PDF Compression", "Compress PDF for Government Forms",
                       "Reduce PDF size under 300KB.", 300, request, faqs)

@app.get("/compress-pdf-500kb", response_class=HTMLResponse)
def pdf_500kb(request: Request):
    faqs = [
        ("Why choose 500 KB?", "500 KB keeps better image quality."),
        ("Is quality preserved?", "Yes, text clarity is preserved."),
    ]
    return render_page("Compress PDF to 500KB", "Compress PDF to 500KB",
                       "Reduce PDF size to 500KB.", 500, request, faqs)
