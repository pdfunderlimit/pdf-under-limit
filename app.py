from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, Request
from fastapi.responses import FileResponse, HTMLResponse
import shutil
import tempfile
import os
import subprocess
import uuid
import math

app = FastAPI()

# ---------------------------
# HTML PAGE RENDERER
# ---------------------------
def render_page(title, heading, intro, default_kb, request: Request,
                readonly=True, show_hint=True):

    readonly_attr = "readonly" if readonly else ""
    path = request.url.path

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
                justify-content: center;
                align-items: center;
                height: 100vh;
            }}

            .nav {{
                position: absolute;
                top: 20px;
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
                transition: all 0.2s ease;
            }}

            .nav a:hover {{
                background: #4f46e5;
                color: white;
            }}

            .nav a.active {{
                background: #4f46e5;
                color: white;
                font-weight: bold;
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

            .loading {{
                display: none;
                margin-top: 20px;
                font-size: 14px;
                color: #2563eb;
            }}

            .spinner {{
                margin: 10px auto;
                width: 28px;
                height: 28px;
                border: 3px solid #c7d2fe;
                border-top: 3px solid #4f46e5;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }}

            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>

        <div class="nav">
            <a href="/passport-pdf-size" class="{tab('/passport-pdf-size')}">Passport (100 KB)</a>
            <a href="/compress-pdf-200kb" class="{tab('/compress-pdf-200kb')}">200 KB</a>
            <a href="/government-form-pdf" class="{tab('/government-form-pdf')}">Govt Forms (300 KB)</a>
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
                <button id="submitBtn" type="submit">Compress PDF</button>
            </form>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                Compressing your PDF… this may take a few seconds.
            </div>
        </div>

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
            .stat {{ margin: 8px 0; font-size: 14px; }}
            .download {{
                background: #16a34a;
                color: white;
                border-radius: 6px;
                padding: 10px;
                width: 100%;
                font-size: 15px;
                margin-top: 18px;
                border: none;
                cursor: pointer;
            }}
            .back {{
                background: #2563eb;
                color: white;
                border-radius: 6px;
                padding: 10px;
                width: 100%;
                font-size: 14px;
                margin-top: 10px;
                border: none;
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
                <button class="download">Download Compressed PDF</button>
            </form>

            <button class="back" onclick="history.back()">⬅ Compress Another PDF</button>
        </div>
    </body>
    </html>
    """

# ---------------------------
# ROUTES
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render_page(
        "Compress PDF Online – Custom Size",
        "Compress PDF to Any Size",
        "Reduce PDF size to any required limit.",
        500,
        request,
        readonly=False,
        show_hint=False
    )

@app.get("/passport-pdf-size", response_class=HTMLResponse)
def passport_pdf(request: Request):
    return render_page(
        "Passport PDF Size Less Than 100KB – Free Online Tool",
        "Reduce Passport PDF Size",
        "Compress passport PDF below 100KB for online passport applications.",
        100,
        request
    )

@app.get("/compress-pdf-200kb", response_class=HTMLResponse)
def pdf_200kb(request: Request):
    return render_page(
        "Compress PDF to 200KB Online – Free & Instant",
        "Compress PDF to 200KB",
        "Reduce PDF size below 200KB for government forms and applications.",
        200,
        request
    )

@app.get("/government-form-pdf", response_class=HTMLResponse)
def govt_pdf(request: Request):
    return render_page(
        "Compress PDF for Government Forms – Free & Easy",
        "Compress PDF for Government Forms",
        "Reduce PDF size under 300KB for government form uploads across Indian states.",
        300,
        request
    )

@app.get("/compress-pdf-500kb", response_class=HTMLResponse)
def pdf_500kb(request: Request):
    return render_page(
        "Compress PDF to 500KB Online – Free & Secure",
        "Compress PDF to 500KB",
        "Reduce PDF size to 500KB for online uploads and submissions.",
        500,
        request
    )
