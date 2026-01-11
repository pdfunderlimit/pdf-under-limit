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
        <h3>Frequently Asked Questions</h3>
        {items}
    </div>
    """

# ---------------------------
# PAGE RENDERER
# ---------------------------
def render_page(title, heading, intro, default_kb, request: Request,
                faqs, readonly=True, show_hint=True):

    path = request.url.path
    readonly_attr = "readonly" if readonly else ""

    def active(p): return "active" if path == p else ""

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
  <a href="/passport-pdf-size" class="{active('/passport-pdf-size')}">Passport (100 KB)</a>
  <a href="/compress-pdf-200kb" class="{active('/compress-pdf-200kb')}">200 KB</a>
  <a href="/government-form-pdf" class="{active('/government-form-pdf')}">Govt Forms</a>
  <a href="/compress-pdf-500kb" class="{active('/compress-pdf-500kb')}">500 KB</a>
  <a href="/" class="{active('/')}">Custom</a>
</div>

<div class="card">
<h2>{heading}</h2>
<p>{intro}</p>
{hint_html}

<form id="uploadForm" action="/compress" method="post"
      enctype="multipart/form-data" onsubmit="startLoading()">
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
# RESULT PAGE
# ---------------------------
def render_result(original_kb, compressed_kb, percent, did):
    return f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial;background:#f5f7fa;
display:flex;justify-content:center;align-items:center;height:100vh;">
<div style="background:white;padding:30px;border-radius:10px;width:360px;text-align:center;">
<h2>Compression Complete</h2>
<p>Original: <b>{original_kb} KB</b></p>
<p>Compressed: <b>{compressed_kb} KB</b></p>
<p>Reduced by: <b>{percent}%</b></p>

<form action="/download/{did}">
<button style="background:#16a34a;color:white;padding:10px;
width:100%;border:none;border-radius:6px;">Download PDF</button>
</form>

<button onclick="history.back()" style="margin-top:10px;padding:10px;
width:100%;background:#4f46e5;color:white;border:none;border-radius:6px;">
⬅ Compress Another PDF
</button>
</div>
</body>
</html>
"""

# ---------------------------
# ROUTES
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    faqs = [
        ("Can I compress PDF to any size?", "Yes, choose a custom target size."),
        ("Why size cannot go too low?", "Some PDFs are already optimized."),
        ("Is this free?", "Yes, completely free."),
        ("Is my data safe?", "Files are deleted automatically.")
    ]
    return render_page("Compress PDF Online", "Compress PDF to Any Size",
                       "Reduce PDF size to any required limit.",
                       500, request, faqs, readonly=False, show_hint=False)

@app.get("/passport-pdf-size", response_class=HTMLResponse)
def passport(request: Request):
    faqs = [
        ("Why passport PDF under 100 KB?", "Most portals enforce strict limits."),
        ("Will quality reduce?", "Text remains readable."),
    ]
    return render_page("Passport PDF < 100KB", "Reduce Passport PDF Size",
                       "Compress passport PDF below 100KB.",
                       100, request, faqs)

@app.get("/compress-pdf-200kb", response_class=HTMLResponse)
def pdf200(request: Request):
    faqs = [
        ("Why 200 KB?", "Common govt upload limit."),
    ]
    return render_page("Compress PDF to 200KB", "Compress PDF to 200KB",
                       "Reduce PDF size below 200KB.",
                       200, request, faqs)

@app.get("/government-form-pdf", response_class=HTMLResponse)
def govt(request: Request):
    faqs = [
        ("Do limits vary by state?", "Yes, 300–500 KB is common."),
    ]
    return render_page("Govt Form PDF", "Compress PDF for Government Forms",
                       "Reduce PDF size under 300KB.",
                       300, request, faqs)

@app.get("/compress-pdf-500kb", response_class=HTMLResponse)
def pdf500(request: Request):
    faqs = [
        ("Why 500 KB?", "Better image clarity."),
    ]
    return render_page("Compress PDF to 500KB", "Compress PDF to 500KB",
                       "Reduce PDF size to 500KB.",
                       500, request, faqs)

# ---------------------------
# BACKEND LOGIC
# ---------------------------
DOWNLOADS = {}

def cleanup(p):
    try:
        if os.path.isfile(p): os.remove(p)
        else: shutil.rmtree(p)
    except: pass

@app.post("/compress", response_class=HTMLResponse)
def compress(bg: BackgroundTasks,
             file: UploadFile = File(...),
             target_kb: int = Form(...)):

    work = tempfile.mkdtemp()
    inp = os.path.join(work, file.filename)

    with open(inp, "wb") as f:
        shutil.copyfileobj(file.file, f)

    orig_kb = math.ceil(os.path.getsize(inp)/1024)
    min_kb = max(50, math.ceil(orig_kb*0.1))

    if target_kb < min_kb:
        bg.add_task(cleanup, work)
        return HTMLResponse(f"<p>Minimum allowed: {min_kb} KB</p>", 400)

    fd, out = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    subprocess.run(
        ["python3", "compress_safe.py", inp, out, str(target_kb)]
    )

    comp_kb = math.ceil(os.path.getsize(out)/1024)
    pct = round((1 - comp_kb/orig_kb)*100, 1)

    did = str(uuid.uuid4())
    DOWNLOADS[did] = out
    bg.add_task(cleanup, work)

    return render_result(orig_kb, comp_kb, pct, did)

@app.get("/download/{did}")
def download(did: str, bg: BackgroundTasks):
    path = DOWNLOADS.pop(did, None)
    if not path or not os.path.exists(path):
        return {"error": "Expired"}

    size = math.ceil(os.path.getsize(path)/1024)
    bg.add_task(cleanup, path)

    return FileResponse(path,
        media_type="application/pdf",
        filename=f"compressed_{size}kb.pdf",
        background=bg)
