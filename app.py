from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
import shutil
import tempfile
import os
import subprocess
import uuid

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <body>
        <h2>Compress PDF to Target Size</h2>
        <form action="/compress" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept="application/pdf" required><br><br>
            Target size (KB): <input type="number" name="target_kb" required><br><br>
            <button type="submit">Compress</button>
        </form>
    </body>
    </html>
    """

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
