from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
import shutil
import tempfile
import os
import subprocess
import uuid

app = FastAPI()
def render_page(title, heading, intro):
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
            h2 {{ margin-bottom: 10px; }}
            p {{ font-size: 14px; color: #555; }}
            input, button {{
                width: 100%;
                margin-top: 12px;
                padding: 10px;
                font-size: 14px;
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
            <form action="/compress" method="post" enctype="multipart/form-data">
                <input type="file" name="file" accept="application/pdf" required>
                <input type="number" name="target_kb" placeholder="Target size (KB)" required>
                <button type="submit">Compress PDF</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
def home():
    return render_page(
        "Compress PDF Online – Free Tool",
        "Compress PDF Online",
        "Reduce PDF size instantly for uploads and forms."
    )

@app.get("/compress-pdf-200kb", response_class=HTMLResponse)
def pdf_200kb():
    return render_page(
        "Compress PDF to 200KB Online – Free & Instant",
        "Compress PDF to 200KB",
        "Reduce PDF size below 200KB for government forms and applications."
    )

@app.get("/compress-pdf-500kb", response_class=HTMLResponse)
def pdf_500kb():
    return render_page(
        "Compress PDF to 500KB Online – Free & Secure",
        "Compress PDF to 500KB",
        "Reduce PDF size to 500KB for online uploads and submissions."
    )

@app.get("/passport-pdf-size", response_class=HTMLResponse)
def passport_pdf():
    return render_page(
        "Passport PDF Size Less Than 100KB – Free Online Tool",
        "Reduce Passport PDF Size",
        "Compress passport PDF below 100KB for online applications."
    )

@app.get("/government-form-pdf", response_class=HTMLResponse)
def govt_pdf():
    return render_page(
        "Compress PDF for Government Forms – Free & Easy",
        "Compress PDF for Government Forms",
        "Fix PDF size errors for government form uploads instantly."
    )

def cleanup(path: str):
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
    except Exception:
        pass

@app.post("/compress")
def compress(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_kb: int = Form(...)
):
    # Create temp working directory (manual, not auto-deleting)
    work_dir = tempfile.mkdtemp()

    input_path = os.path.join(work_dir, file.filename)

    # IMPORTANT: output file must NOT be auto-deleted
    output_fd, output_path = tempfile.mkstemp(suffix=".pdf")
    os.close(output_fd)

    # Save uploaded file
    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Call compression engine
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

    # Cleanup AFTER response is sent
    background_tasks.add_task(cleanup, work_dir)
    background_tasks.add_task(cleanup, output_path)

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="compressed.pdf",
        background=background_tasks,
    )
