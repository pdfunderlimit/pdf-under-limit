from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
import shutil, tempfile, os, subprocess, uuid, math

app = FastAPI()

# ---------------------------
# FAQ RENDERER (BILINGUAL)
# ---------------------------
def render_faq(faqs):
    items = ""
    for mr_q, en_q, mr_a, en_a in faqs:
        items += f"""
        <div class="faq-item">
            <button class="faq-question"
                onclick="this.nextElementSibling.classList.toggle('open')">
                <div class="mr">{mr_q}</div>
                <div class="en">{en_q}</div>
            </button>
            <div class="faq-answer">
                <div class="mr">{mr_a}</div>
                <div class="en">{en_a}</div>
            </div>
        </div>
        """
    return f"""
    <div class="faq">
        <h3>
          नेहमी विचारले जाणारे प्रश्न
          <div class="en">Frequently Asked Questions</div>
        </h3>
        {items}
    </div>
    """

# ---------------------------
# PAGE RENDERER
# ---------------------------
def render_page(title, mr_heading, en_heading,
                mr_intro, en_intro,
                default_kb, request: Request,
                faqs, readonly=True, show_hint=True):

    path = request.url.path
    readonly_attr = "readonly" if readonly else ""

    def active(p): return "active" if path == p else ""

    hint_html = (
        f"""
        <div class="hint">
            <div class="mr"><strong>{default_kb} KB पेक्षा कमी</strong></div>
            <div class="en">Target size under {default_kb} KB</div>
        </div>
        """ if show_hint else ""
    )

    return f"""
<!DOCTYPE html>
<html>
<head>
<title>{title}</title>
<meta name="description" content="{en_intro}">
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body {{
    font-family: "Noto Sans Devanagari", "Mangal", "Kalimati", "Kokila", Arial, sans-serif;
    background: #f5f7fa;
    margin: 0;
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
}}

.mr {{
    font-size: 16px;
    font-weight: 600;
    line-height: 1.6;
    color: #111827;
}}

.en {{
    font-size: 13px;
    color: #374151;
    line-height: 1.4;
}}

.nav {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
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
    margin-top: 25px;
    padding: 28px;
    border-radius: 12px;
    max-width: 380px;
    width: 100%;
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    text-align: center;
}}

input, button {{
    width: 100%;
    margin-top: 12px;
    padding: 11px;
    font-size: 14px;
}}

input[readonly] {{
    background: #f1f5f9;
}}

button {{
    background: #4f46e5;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
}}

button .mr {{
    color: white;
}}

.loading {{
    display: none;
    margin-top: 16px;
    color: #1e3a8a;
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
    to {{ transform: rotate(360deg); }}
}}

.faq {{
    margin: 40px 0;
    max-width: 380px;
    width: 100%;
}}

.faq-question {{
    width: 100%;
    background: #eef2ff;
    padding: 12px;
    border: none;
    text-align: left;
    border-radius: 8px;
    cursor: pointer;
}}

.faq-answer {{
    display: none;
    background: white;
    padding: 12px;
    margin-top: 6px;
    border-radius: 8px;
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
  <h1 class="mr">{mr_heading}</h1>
  <h2 class="en">{en_heading}</h2>

  <p class="mr">{mr_intro}</p>
  <p class="en">{en_intro}</p>

  {hint_html}

  <form id="uploadForm" action="/compress" method="post"
        enctype="multipart/form-data" onsubmit="startLoading()">
    <input type="file" name="file" accept="application/pdf" required>
    <input type="number" name="target_kb" value="{default_kb}" {readonly_attr} required>

    <button id="submitBtn">
      <div class="mr">PDF compress करा</div>
      <div class="en">Compress PDF</div>
    </button>
  </form>

  <div class="loading" id="loading">
    <div class="spinner"></div>
    <div class="mr">PDF compress होत आहे… कृपया थांबा</div>
    <div class="en">Compressing your PDF… please wait</div>
  </div>

  <p class="mr" style="margin-top:14px;">
    तुमची PDF फाईल कुठेही जतन केली जात नाही.
  </p>
  <p class="en">
    Your PDF files are not stored and are deleted automatically.
  </p>
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
# ROUTES
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render_page(
        "Compress PDF Online – Free Tool",
        "तुमची PDF आवश्यक आकारात कमी करा",
        "Compress PDF to Any Size",
        "कोणत्याही आवश्यक मर्यादेत PDF compress करा",
        "Reduce PDF size to any required limit",
        500, request,
        faqs=[],
        readonly=False,
        show_hint=False
    )

@app.get("/passport-pdf-size", response_class=HTMLResponse)
def passport(request: Request):
    return render_page(
        "Passport PDF Size Less Than 100KB",
        "पासपोर्ट PDF 100 KB पेक्षा कमी करा",
        "Reduce Passport PDF Size",
        "पासपोर्ट अर्जासाठी PDF compress करा",
        "Compress PDF for passport applications",
        100, request,
        faqs=[]
    )

@app.get("/compress-pdf-200kb", response_class=HTMLResponse)
def pdf200(request: Request):
    return render_page(
        "Compress PDF to 200KB",
        "PDF 200 KB पर्यंत compress करा",
        "Compress PDF to 200KB",
        "सरकारी फॉर्मसाठी PDF कमी करा",
        "Reduce PDF size below 200KB",
        200, request,
        faqs=[]
    )

@app.get("/government-form-pdf", response_class=HTMLResponse)
def govt(request: Request):
    return render_page(
        "Compress PDF for Government Forms",
        "सरकारी फॉर्मसाठी PDF compress करा",
        "Compress PDF for Government Forms",
        "राज्य व केंद्र सरकारी पोर्टलसाठी",
        "For state & central government portals",
        300, request,
        faqs=[]
    )

@app.get("/compress-pdf-500kb", response_class=HTMLResponse)
def pdf500(request: Request):
    return render_page(
        "Compress PDF to 500KB",
        "PDF 500 KB पर्यंत compress करा",
        "Compress PDF to 500KB",
        "गुणवत्ता राखून PDF कमी करा",
        "Keep better quality while compressing",
        500, request,
        faqs=[]
    )

# ---------------------------
# SITEMAP.XML (SEO STEP 3)
# ---------------------------
@app.get("/sitemap.xml", response_class=Response)
def sitemap():
    return Response(
        content="""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://pdf-under-limit.onrender.com/</loc>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://pdf-under-limit.onrender.com/passport-pdf-size</loc>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://pdf-under-limit.onrender.com/compress-pdf-200kb</loc>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://pdf-under-limit.onrender.com/government-form-pdf</loc>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://pdf-under-limit.onrender.com/compress-pdf-500kb</loc>
    <priority>0.9</priority>
  </url>
</urlset>
""",
        media_type="application/xml"
    )

# ---------------------------
# BACKEND LOGIC
# ---------------------------
DOWNLOADS = {}

def cleanup(p):
    try:
        if os.path.isfile(p): os.remove(p)
        else: shutil.rmtree(p)
    except:
        pass

@app.post("/compress", response_class=HTMLResponse)
def compress(bg: BackgroundTasks,
             file: UploadFile = File(...),
             target_kb: int = Form(...)):

    work = tempfile.mkdtemp()
    inp = os.path.join(work, file.filename)

    with open(inp, "wb") as f:
        shutil.copyfileobj(file.file, f)

    orig_kb = math.ceil(os.path.getsize(inp) / 1024)
    min_kb = max(50, math.ceil(orig_kb * 0.1))

    if target_kb < min_kb:
        bg.add_task(cleanup, work)
        return HTMLResponse(
            f"<p>किमान आकार: {min_kb} KB<br>Minimum size allowed</p>",
            status_code=400
        )

    fd, out = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    subprocess.run(
        ["python3", "compress_safe.py", inp, out, str(target_kb)]
    )

    comp_kb = math.ceil(os.path.getsize(out) / 1024)
    pct = round((1 - comp_kb / orig_kb) * 100, 1)

    did = str(uuid.uuid4())
    DOWNLOADS[did] = out
    bg.add_task(cleanup, work)

    return f"""
    <html><body style="font-family:Arial;background:#f5f7fa;
    display:flex;justify-content:center;align-items:center;padding:20px;">
    <div style="background:white;padding:30px;border-radius:12px;
    max-width:380px;width:100%;text-align:center;">
    <div class="mr">PDF compress पूर्ण झाले</div>
    <div class="en">Compression Complete</div>

    <p class="mr">मूळ आकार: {orig_kb} KB</p>
    <p class="en">Original size: {orig_kb} KB</p>

    <p class="mr">compress झालेला आकार: {comp_kb} KB</p>
    <p class="en">Compressed size: {comp_kb} KB</p>

    <p class="mr">कमी झाले: {pct}%</p>
    <p class="en">Reduced by: {pct}%</p>

    <form action="/download/{did}">
      <button style="background:#16a34a;color:white;padding:12px;
      width:100%;border:none;border-radius:8px;">
      <div class="mr">PDF डाउनलोड करा</div>
      <div class="en">Download PDF</div>
      </button>
    </form>

    <button onclick="window.location.href='/'"
      style="margin-top:12px;padding:12px;width:100%;
      background:#4f46e5;color:white;border:none;border-radius:8px;">
      <div class="mr">दुसरी PDF compress करा</div>
      <div class="en">Compress another PDF</div>
    </button>
    </div></body></html>
    """

@app.get("/download/{did}")
def download(did: str, bg: BackgroundTasks):
    path = DOWNLOADS.pop(did, None)
    if not path or not os.path.exists(path):
        return {"error": "Expired"}

    size = math.ceil(os.path.getsize(path) / 1024)
    bg.add_task(cleanup, path)

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"compressed_{size}kb.pdf",
        background=bg
    )
