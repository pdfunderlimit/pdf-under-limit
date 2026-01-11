from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from PIL import Image
import shutil, tempfile, os, subprocess, uuid, math, io

app = FastAPI()

# ---------------------------
# PAGE RENDERER
# ---------------------------
def render_page(
    title,
    mr_heading, en_heading,
    mr_intro, en_intro,
    default_kb,
    request: Request,
    action,
    accept,
    readonly=True,
    show_hint=True
):
    path = request.url.path
    readonly_attr = "readonly" if readonly else ""

    def active(p):
        return "active" if path == p else ""

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

<meta name="google-site-verification"
      content="8KCKN-K8i1pT9hfLJb8nGYcLfU0P6z7rHwIG5aox2Q4">

<style>
body {{
    font-family: "Noto Sans Devanagari", "Mangal", Arial, sans-serif;
    background: #f5f7fa;
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
}}

.mr {{ font-size: 17px; font-weight: 700; }}
.en {{ font-size: 14px; color: #374151; }}

.nav {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
}}

.nav a {{
    text-decoration: none;
    padding: 6px 14px;
    border-radius: 20px;
    background: #e5e7eb;
    color: #111827;
    font-size: 13px;
}}

.nav a.active, .nav a:hover {{
    background: #4f46e5;
    color: white;
}}

.card {{
    background: white;
    margin-top: 25px;
    padding: 28px;
    border-radius: 14px;
    max-width: 380px;
    width: 100%;
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    text-align: center;
}}

input, button {{
    width: 100%;
    margin-top: 12px;
    padding: 12px;
    font-size: 14px;
}}

input[readonly] {{ background: #f1f5f9; }}

button {{
    background: #4f46e5;
    color: white;
    border: none;
    border-radius: 10px;
}}

.loading {{ display: none; margin-top: 18px; }}
.spinner {{
    margin: 10px auto;
    width: 28px;
    height: 28px;
    border: 3px solid #c7d2fe;
    border-top: 3px solid #4f46e5;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}}

@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
</style>
</head>

<body>

<div class="nav">
  <a href="/" class="{active('/')}">PDF</a>
  <a href="/compress-image" class="{active('/compress-image')}">🖼️ Image</a>
</div>

<div class="card">
  <h1 class="mr">{mr_heading}</h1>
  <h2 class="en">{en_heading}</h2>

  <p class="mr">{mr_intro}</p>
  <p class="en">{en_intro}</p>

  {hint_html}

  <form id="form" action="{action}" method="post"
        enctype="multipart/form-data" onsubmit="startLoading()">
    <input type="file" name="file" accept="{accept}" required>
    <input type="number" name="target_kb" value="{default_kb}" {readonly_attr} required>

    <button id="btn">
      <div class="mr">Compress करा</div>
      <div class="en">Compress</div>
    </button>
  </form>

  <div class="loading" id="loading">
    <div class="spinner"></div>
    <div class="mr">प्रक्रिया सुरू आहे…</div>
    <div class="en">Processing…</div>
  </div>
</div>

<script>
function startLoading() {{
  document.getElementById("btn").disabled = true;
  document.getElementById("form").style.display = "none";
  document.getElementById("loading").style.display = "block";
}}
</script>

</body>
</html>
"""

# ---------------------------
# PDF HOME
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def pdf_home(request: Request):
    return render_page(
        "Compress PDF Online",
        "PDF Compress करा",
        "Compress PDF",
        "PDF आवश्यक आकारात कमी करा",
        "Reduce PDF size",
        500,
        request,
        "/compress-pdf",
        "application/pdf",
        readonly=False,
        show_hint=False
    )

# ---------------------------
# IMAGE PAGE
# ---------------------------
@app.get("/compress-image", response_class=HTMLResponse)
def image_page(request: Request):
    return render_page(
        "Compress Image Online",
        "Image Compress करा",
        "Compress Image",
        "JPG / PNG फोटो कमी करा",
        "Reduce image size",
        100,
        request,
        "/compress-image",
        "image/jpeg,image/png",
        readonly=False,
        show_hint=False
    )

# ---------------------------
# IMAGE COMPRESSION
# ---------------------------
@app.post("/compress-image", response_class=HTMLResponse)
def compress_image(bg: BackgroundTasks,
                   file: UploadFile = File(...),
                   target_kb: int = Form(...)):

    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        return HTMLResponse("Invalid image format", status_code=400)

    img = Image.open(file.file)
    img = img.convert("RGB")

    orig_buf = io.BytesIO()
    img.save(orig_buf, format="JPEG", quality=95)
    orig_kb = math.ceil(len(orig_buf.getvalue()) / 1024)

    min_kb = max(30, math.ceil(orig_kb * 0.1))
    if target_kb < min_kb:
        return HTMLResponse(
            f"Minimum allowed: {min_kb} KB", status_code=400
        )

    quality = 90
    out_buf = io.BytesIO()

    while quality >= 20:
        out_buf.seek(0)
        out_buf.truncate(0)
        img.save(out_buf, format="JPEG", quality=quality)
        size_kb = len(out_buf.getvalue()) / 1024
        if size_kb <= target_kb:
            break
        quality -= 5

    fname = f"compressed_{math.ceil(size_kb)}kb.jpg"
    bg.add_task(out_buf.close)

    return FileResponse(
        io.BytesIO(out_buf.getvalue()),
        media_type="image/jpeg",
        filename=fname
    )

# ---------------------------
# PDF COMPRESSION (existing)
# ---------------------------
@app.post("/compress-pdf", response_class=HTMLResponse)
def compress_pdf(bg: BackgroundTasks,
                 file: UploadFile = File(...),
                 target_kb: int = Form(...)):

    work = tempfile.mkdtemp()
    inp = os.path.join(work, file.filename)

    with open(inp, "wb") as f:
        shutil.copyfileobj(file.file, f)

    orig_kb = math.ceil(os.path.getsize(inp) / 1024)
    min_kb = max(50, math.ceil(orig_kb * 0.1))

    if target_kb < min_kb:
        bg.add_task(shutil.rmtree, work)
        return HTMLResponse("Target too small", status_code=400)

    fd, out = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    subprocess.run(["python3", "compress_safe.py", inp, out, str(target_kb)])

    bg.add_task(shutil.rmtree, work)
    return FileResponse(
        out,
        media_type="application/pdf",
        filename=f"compressed_{target_kb}kb.pdf",
        background=bg
    )

# ---------------------------
# SITEMAP & ROBOTS
# ---------------------------
@app.get("/sitemap.xml", response_class=Response)
def sitemap():
    return Response(
        content="""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://pdf-under-limit.onrender.com/</loc></url>
  <url><loc>https://pdf-under-limit.onrender.com/compress-image</loc></url>
</urlset>""",
        media_type="application/xml"
    )

@app.get("/robots.txt", response_class=Response)
def robots():
    return Response(
        content="""User-agent: *
Allow: /

Sitemap: https://pdf-under-limit.onrender.com/sitemap.xml
""",
        media_type="text/plain"
    )
