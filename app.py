from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
import shutil
import tempfile
import os
import subprocess

app = FastAPI()

# ---------------------------
# HTML PAGE RENDERER
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
# ROUTES (ORDERED LOGICALLY)
# ---------------------------

# 1️⃣ Custom / Homepage
@app.get("/", response_class=HTMLResponse)
def home():
    return render_page(
        "Compress PDF Online – Custom Size",
        "Compress PDF to Any Size",
        "Reduce PDF size to any required limit like 777 KB, 998 KB, or 1000 KB. Output will be under the target size.",
        500,
        readonly=False
    )

# 2️⃣ Passport (Most strict)
@app.get("/passport-pdf-size", response_class=HTMLResponse)
def passport_pdf():
    return render_page(
        "Passport PDF Size Less Than 100KB – Free Online Tool",
        "Reduce Passport PDF Size",
        "Compress passport PDF below 100KB for online passport applications.",
        100
    )

# 3️⃣ 200 KB
@app.get("/compress-pdf-200kb", response_class=HTMLResponse)
def pdf_200kb():
    return render_page(
        "Compress PDF to 200KB Online – Free & Instant",
        "Compress PDF to 200KB",
        "Reduce PDF size below 200KB for government forms and applications.",
        200
    )

# 4️⃣ Government forms (state-agnostic)
@app.get("/government-form-pdf", response_class=HTMLResponse)
def govt_pdf():
    return render_page(
        "Compress PDF for Government Forms – Free & Easy",
        "Compress PDF for Government Forms",
        "Reduce PDF size under 300KB for government form uploads across Indian states.",
        300
    )

# 5️⃣ 500 KB
@app.get("/compress-pdf-500kb", response_class=HTMLResponse)
def pdf_500kb():
    return render_page(
        "Compress PDF to 500KB Online – Free & Secure",
        "Compress PDF to 500KB",
        "Reduce PDF size to 500KB for online uploads and submissions.",
        500
    )

# ---------------------------
# CLEANUP LOGIC (DO NOT TOUCH)
# ---------------------------
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
@app.post("/compress")
def compress(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_kb: int = Form(...)
):
    # Create temp working directory
    work_dir = tempfile.mkdtemp()
    input_path = os.path.join(work_dir, file.filename)

    # Output file must persist until response finishes
    output_fd, output_path = tempfile.mkstemp(suffix=".pdf")
    os.close(output_fd)

    # Save uploaded file
    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Run compression engine
    result = subprocess.run(
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

    # Validate result
    if result.returncode not in (0, 2) or not os.path.exists(output_path):
        cleanup(work_dir)
        cleanup(output_path)
        return {
            "error": "Compression failed",
            "details": result.stdout + result.stderr,
        }

    # Cleanup after response
    background_tasks.add_task(cleanup, work_dir)
    background_tasks.add_task(cleanup, output_path)

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="compressed.pdf",
        background=background_tasks,
    )
