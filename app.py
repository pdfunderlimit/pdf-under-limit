from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, FileResponse, Response
from PIL import Image
import tempfile, shutil, os, subprocess, uuid, math, io

app = FastAPI()

# ---------------------------
# COMMON STYLES & PAGE RENDER
# ---------------------------
def render_page(title, mr_h, en_h, mr_p, en_p, default_kb, request, action, accept):
    path = request.url.path
    def active(p): return "active" if path == p else ""

    return f"""
<!DOCTYPE html>
<html>
<head>
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="google-site-verification"
 content="8KCKN-K8i1pT9hfLJb8nGYcLfU0P6z7rHwIG5aox2Q4">

<style>
body {{
  font-family: "Noto Sans Devanagari", "Mangal", Arial, sans-serif;
  background:#f5f7fa; margin:0; padding:20px;
  display:flex; flex-direction:column; align-items:center;
}}
.mr {{ font-size:18px; font-weight:700; color:#111827; }}
.en {{ font-size:14px; color:#374151; }}
.nav {{ display:flex; gap:8px; margin-bottom:20px; }}
.nav a {{
  padding:6px 14px; border-radius:20px;
  background:#e5e7eb; text-decoration:none; color:#111827;
}}
.nav a.active, .nav a:hover {{ background:#4f46e5; color:white; }}
.card {{
  background:white; padding:28px; border-radius:14px;
  width:100%; max-width:380px;
  box-shadow:0 10px 25px rgba(0,0,0,.1);
  text-align:center;
}}
input, button {{
  width:100%; padding:12px; margin-top:12px;
  font-size:14px;
}}
button {{
  background:#4f46e5; color:white;
  border:none; border-radius:10px;
}}
.loading {{ display:none; margin-top:20px; }}
.spinner {{
  width:28px; height:28px;
  border:3px solid #c7d2fe;
  border-top:3px solid #4f46e5;
  border-radius:50%;
  animation:spin 1s linear infinite;
  margin:auto;
}}
@keyframes spin {{ to {{ transform:rotate(360deg); }} }}
</style>
</head>

<body>

<div class="nav">
  <a href="/" class="{active('/')}">PDF</a>
  <a href="/image" class="{active('/image')}">🖼️ Image</a>
</div>

<div class="card">
  <div class="mr">{mr_h}</div>
  <div class="en">{en_h}</div>
  <p class="mr">{mr_p}</p>
  <p class="en">{en_p}</p>

  <form id="f" action="{action}" method="post"
    enctype="multipart/form-data" onsubmit="load()">
    <input type="file" name="file" accept="{accept}" required>
    <input type="number" name="target_kb" value="{default_kb}" required>
    <button>
      <div class="mr">Compress करा</div>
      <div class="en">Compress</div>
    </button>
  </form>

  <div class="loading" id="l">
    <div class="spinner"></div>
    <div class="mr">प्रक्रिया सुरू आहे…</div>
    <div class="en">Processing…</div>
  </div>
</div>

<script>
function load() {{
  document.getElementById('f').style.display='none';
  document.getElementById('l').style.display='block';
}}
</script>

</body></html>
"""

# ---------------------------
# RESULT PAGE
# ---------------------------
def result_page(orig, comp, pct, link):
    return f"""
<html><body style="font-family:Arial;background:#f5f7fa;
display:flex;align-items:center;justify-content:center;padding:20px;">
<div style="background:white;padding:30px;border-radius:14px;
width:100%;max-width:380px;text-align:center;">
<div class="mr">प्रक्रिया पूर्ण झाली</div>
<div class="en">Compression Complete</div>

<p class="mr">मूळ आकार: {orig} KB</p>
<p class="en">Original size: {orig} KB</p>

<p class="mr">नवीन आकार: {comp} KB</p>
<p class="en">Compressed size: {comp} KB</p>

<p class="mr">कमी झाले: {pct}%</p>
<p class="en">Reduced by: {pct}%</p>

<a href="{link}">
<button style="background:#16a34a;margin-top:12px;">
<div class="mr">Download करा</div>
<div class="en">Download</div>
</button>
</a>

<a href="/">
<button style="margin-top:10px;">
<div class="mr">पुन्हा Compress करा</div>
<div class="en">Compress another</div>
</button>
</a>
</div></body></html>
"""

# ---------------------------
# PDF
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def pdf_home(request: Request):
    return render_page(
        "Compress PDF",
        "PDF Compress करा",
        "Compress PDF",
        "PDF आवश्यक आकारात कमी करा",
        "Reduce PDF size",
        500,
        request,
        "/compress-pdf",
        "application/pdf"
    )

@app.post("/compress-pdf", response_class=HTMLResponse)
def compress_pdf(bg: BackgroundTasks,
                 file: UploadFile = File(...),
                 target_kb: int = Form(...)):

    work = tempfile.mkdtemp()
    inp = os.path.join(work, file.filename)
    with open(inp, "wb") as f: shutil.copyfileobj(file.file, f)

    orig = math.ceil(os.path.getsize(inp)/1024)
    if target_kb < 50:
        shutil.rmtree(work)
        return HTMLResponse("Minimum 50 KB", status_code=400)

    fd, out = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    subprocess.run(["python3","compress_safe.py",inp,out,str(target_kb)])

    comp = math.ceil(os.path.getsize(out)/1024)
    pct = round((1-comp/orig)*100,1)
    bg.add_task(shutil.rmtree, work)

    return result_page(orig, comp, pct, f"/download-pdf?f={out}")

@app.get("/download-pdf")
def dl_pdf(f: str, bg: BackgroundTasks):
    bg.add_task(os.remove, f)
    return FileResponse(f, filename="compressed.pdf")

# ---------------------------
# IMAGE
# ---------------------------
@app.get("/image", response_class=HTMLResponse)
def img_home(request: Request):
    return render_page(
        "Compress Image",
        "प्रतिमा Compress करा",
        "Compress Image",
        "JPG किंवा PNG फोटोचा आकार कमी करा",
        "Reduce JPG / PNG size",
        100,
        request,
        "/compress-image",
        "image/jpeg,image/png"
    )

@app.post("/compress-image", response_class=HTMLResponse)
def compress_image(file: UploadFile = File(...),
                   target_kb: int = Form(...)):

    img = Image.open(file.file).convert("RGB")
    buf = io.BytesIO()
    quality = 90

    while quality >= 20:
        buf.seek(0); buf.truncate()
        img.save(buf, format="JPEG", quality=quality)
        if len(buf.getvalue())/1024 <= target_kb:
            break
        quality -= 5

    if len(buf.getvalue())/1024 > target_kb:
        return HTMLResponse("Cannot compress without quality loss")

    fname = f"img_{math.ceil(len(buf.getvalue())/1024)}kb.jpg"
    return FileResponse(io.BytesIO(buf.getvalue()),
                        filename=fname,
                        media_type="image/jpeg")

# ---------------------------
# SEO FILES
# ---------------------------
@app.get("/sitemap.xml", response_class=Response)
def sitemap():
    return Response(
        content="""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://pdf-under-limit.onrender.com/</loc></url>
<url><loc>https://pdf-under-limit.onrender.com/image</loc></url>
</urlset>""",
        media_type="application/xml"
    )

@app.get("/robots.txt", response_class=Response)
def robots():
    return Response(
        content="User-agent: *\nAllow: /\nSitemap: https://pdf-under-limit.onrender.com/sitemap.xml",
        media_type="text/plain"
    )
