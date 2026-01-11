from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, Request
from fastapi.responses import FileResponse, HTMLResponse
import shutil, tempfile, os, subprocess, uuid, math

app = FastAPI()

# ---------------------------
# FAQ RENDERER
# ---------------------------
def render_faq(faqs):
    items = ""
    for q, a in faqs:
        items += f"""
        <div class="faq-item">
            <button class="faq-question"
                onclick="this.nextElementSibling.classList.toggle('open')">
                {q}
            </button>
            <div class="faq-answer">{a}</div>
        </div>
        """
    return f"""
    <div class="faq">
        <h3>Frequently Asked Questions<br>
        <span class="mr">नेहमी विचारले जाणारे प्रश्न</span></h3>
        {items}
    </div>
    """

# ---------------------------
# PAGE RENDERER
# ---------------------------
def render_page(title, heading_en, heading_mr,
                intro_en, intro_mr,
                default_kb, request: Request,
                faqs, readonly=True, show_hint=True):

    path = request.url.path
    readonly_attr = "readonly" if readonly else ""

    def active(p): return "active" if path == p else ""

    hint_html = (
        f"""
        <div class="hint">
            Target size: under <strong>{default_kb} KB</strong><br>
            <span class="mr">लक्ष्य आकार: <strong>{default_kb} KB</strong> पेक्षा कमी</span>
        </div>
        """ if show_hint else ""
    )

    return f"""
<!DOCTYPE html>
<html>
<head>
<title>{title}</title>
<meta name="description" content="{intro_en}">
<style>
body {{
    font-family: Arial, sans-serif;
    background: #f5f7fa;
    display: flex;
    flex-direction: column;
    align-items: center;
}}

.mr {{
    font-size: 13px;
    color: #374151;
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
    cursor: pointer;
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

.faq-question {{
    width: 100%;
    background: #eef2ff;
    padding: 10px;
    border: none;
    text-align: left;
    border-radius: 6px;
}}

.faq-answer {{
    display: none;
    padding: 10px;
    font-size: 13px;
}}

.faq-answer.open {{
    display: block;
}}
</style>
</head>

<body>

<div class="nav">
  <a href="/passport-pdf-size" class="{active('/passport-pdf-size')}">Passport</a>
  <a href="/compress-pdf-200kb" class="{active('/compress-pdf-200kb')}">200 KB</a>
  <a href="/government-form-pdf" class="{active('/government-form-pdf')}">Govt Forms</a>
  <a href="/compress-pdf-500kb" class="{active('/compress-pdf-500kb')}">500 KB</a>
  <a href="/" class="{active('/')}">Custom</a>
</div>

<div class="card">
<h2>{heading_en}</h2>
<div class="mr">{heading_mr}</div>

<p>{intro_en}<br>
<span class="mr">{intro_mr}</span></p>

{hint_html}

<form id="uploadForm" action="/compress" method="post"
      enctype="multipart/form-data" onsubmit="startLoading()">
<input type="file" name="file" accept="application/pdf" required>
<input type="number" name="target_kb" value="{default_kb}" {readonly_attr} required>

<button id="submitBtn">
Compress PDF<br>
<span class="mr">PDF संकुचित करा</span>
</button>
</form>

<div class="loading" id="loading">
<div class="spinner"></div>
Compressing your PDF… please wait<br>
<span class="mr">तुमची PDF प्रक्रिया सुरू आहे… कृपया थांबा</span>
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
# ROUTES (example)
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render_page(
        "Compress PDF Online",
        "Compress PDF to Any Size",
        "तुमची PDF आवश्यक आकारात कमी करा",
        "Reduce PDF size to any required limit.",
        "कोणत्याही आवश्यक मर्यादेत PDF फाईल संकुचित करा.",
        500, request,
        faqs=[
            ("Is this tool free?", "Yes, this tool is completely free.")
        ],
        readonly=False,
        show_hint=False
    )

# (Other routes remain SAME as previous final file)
