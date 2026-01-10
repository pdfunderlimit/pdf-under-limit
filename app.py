from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
import shutil
import tempfile
import os
import subprocess
import uuid
import math

app = FastAPI()

# ---------------------------
# HTML PAGE RENDERER (UPLOAD)
# ---------------------------
def render_page(title, heading, intro, default_kb, readonly=True):
    readonly_attr = "readonly" if readonly else ""

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
                justify-content: center;
                align-items: center;
                height: 100vh;
            }}
            .card {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                width: 360px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                text-align: center;
            }}
            h2 {{ margin-bottom: 8px; }}
            p {{ font-size: 14px; color: #555; }}
            .hint {{
                font-size: 13px;
                color: #2563eb;
                margin-bottom: 10px;
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
        </style>
    </head>
    <body>
        <div class="card">
            <h2>{heading}</h2>
            <p>{intro}</p>
            <div class="hint">
                Target size: under <strong>{default_kb} KB</strong>
            </div>
            <form action="/compress" method="post" enctype="multipart/form-data">
                <input type="file" name="file" accept="application/pdf" required>
                <input type="number" name="target_kb" value="{default_kb}" {readonly_attr} required>
                <button type="submit">Compress PDF</button>
            </form>
        </div>
    </body>
    </html>
    """

# ---------------------------
# RESULT PAGE (AFTER COMPRESS)
# ---------------------------
def render_result_page(original_kb, compressed_kb, percent, download_id):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Compression Result</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f5f7fa;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }}
            .card {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                width: 360px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .stat {{
                margin: 8px 0;
                font-size: 14px;
            }}
            button {{
                margin-top: 20px;
                padding: 10px;
                width: 100%;
                background: #16a34a;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Compression Complete</h2>
            <div class="stat">Original size: <strong>{original_kb} KB</strong></div>
            <div class="stat">Compressed size: <strong>{compressed_kb} KB</strong></div>
            <div class="stat">Reduced by: <strong>{percent}%</strong></div>

            <form action="/download/{download_id}" method="get">
                <button type="submit">Download Compressed PDF</button>
            </form>
        </div>
    </body>
    </html>
    """

# ---------------------------
# ROUTES
# ---------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    return render_page(
        "Compress PDF Online – Custom Size",
        "Compress PDF to Any Size",
        "Reduce PDF size to any required limit like 777 KB, 998 KB, or 1000 KB. Output will be under the target size.",
        500,
        readonly=False
    )

@app.get("/passport-pdf-size", response_class=HTMLResponse)
def passport_pdf():
    return render_page(
        "Passport PDF Size Less Than 100KB – Free Online Tool",
        "Reduce Passport PDF Size",
        "Compress passport PDF below 100KB for online passport applications.",
        100
    )

@app.get("/compress-pdf-200kb", response_class=HTMLResponse)
def pdf_200kb():
    return render_page(
        "Compress PDF to 200KB Online – Free & Instant",
        "Compress PDF to 200KB",
        "Reduce PDF size below 200KB for government forms and applications.",
        200
    )

@app.get("/government-form-pdf", response_class=HTMLResponse)
def govt_pdf():
    return render_page(
        "Compress PDF for Government Forms – Free & Easy",
        "Compress PDF for Government Forms",
        "Reduce PDF size under 300KB for government form uploads across Indian states.",
        300
    )

@app.get("/compress-pdf-500kb", response_class=HTMLResponse)
def pdf_500kb():
    return render_page(
        "Compress PDF to 500KB Online – Free & Secure",
        "Compress PDF to 500KB",
        "Reduce PDF size to 500KB for online uploads and submissions.",
        500
    )

# ---------------------------
# TEMP STORAGE FOR DOWNLOADS
# ---------------------------
DOWNLOADS = {}

def cleanup(path: str):
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
    except Exception:
        pass

# ---------------------------
# COMPRESSION ENDPOINT
# ---------------------------
@app.post("/compress", response_class=HTMLResponse)
def compress(background_tasks: BackgroundTasks,
             file: UploadFile = File(...),
             target_kb: int = Form(...)):

    work_dir = tempfile.mkdtemp()
    input_path = os.path.join(work_dir, file.filename)

    output_fd, output_path = tempfile.mkstemp(suffix=".pdf")
    os.close(output_fd)

    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    subprocess.run(
        [
            "python3",
            os.path.join(os.getcwd(), "compress_safe.py"),
            input_path,
            output_path,
            str(target_kb),
        ],
        capture_output=True,
        text=True,
    )

    original_kb = math.ceil(os.path.getsize(input_path) / 1024)
    compressed_kb = math.ceil(os.path.getsize(output_path) / 1024)
    percent = round((1 - compressed_kb / original_kb) * 100, 1)

    download_id = str(uuid.uuid4())
    DOWNLOADS[download_id] = output_path

    background_tasks.add_task(cleanup, work_dir)

    return render_result_page(
        original_kb,
        compressed_kb,
        percent,
        download_id
    )

# ---------------------------
# DOWNLOAD ENDPOINT
# ---------------------------
@app.get("/download/{download_id}")
def download(download_id: str, background_tasks: BackgroundTasks):
    path = DOWNLOADS.pop(download_id, None)
    if not path or not os.path.exists(path):
        return {"error": "File expired"}

    size_kb = math.ceil(os.path.getsize(path) / 1024)
    filename = f"compressed_{size_kb}kb.pdf"

    background_tasks.add_task(cleanup, path)

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=filename,
        background=background_tasks,
    )
