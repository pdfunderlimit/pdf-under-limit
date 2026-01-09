import subprocess
import sys
import os
import shutil
import tempfile

QUALITY_LEVELS = ["ebook", "screen"]

def get_size_kb(file_path):
    return os.path.getsize(file_path) // 1024

def compress_pdf(input_pdf, output_pdf, quality):
    command = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{quality}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_pdf}",
        input_pdf
    ]
    subprocess.run(command, check=True)

def main():
    if len(sys.argv) != 4:
        print("❌ Usage: python3 compress_safe.py input.pdf output.pdf target_kb")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]

    # Validate target size
    try:
        target_kb = int(sys.argv[3])
        if target_kb <= 0:
            raise ValueError
    except ValueError:
        print("❌ Target size must be a positive number (KB)")
        sys.exit(1)

    # Validate input file
    if not os.path.exists(input_pdf):
        print("❌ Input file does not exist")
        sys.exit(1)

    if not input_pdf.lower().endswith(".pdf"):
        print("❌ Input file is not a PDF")
        sys.exit(1)

    original_size = get_size_kb(input_pdf)

    # Always create a temp output first
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        temp_output = tmp.name

    try:
        # Case 1: already under target
        if original_size <= target_kb:
            shutil.copy(input_pdf, temp_output)
            shutil.move(temp_output, output_pdf)
            print(f"ℹ File already under target size ({original_size} KB)")
            sys.exit(0)

        # Try compression levels
        for quality in QUALITY_LEVELS:
            compress_pdf(input_pdf, temp_output, quality)
            size_kb = get_size_kb(temp_output)
            print(f"Tried {quality}: {size_kb} KB")

            if size_kb <= target_kb:
                shutil.move(temp_output, output_pdf)
                print(f"✅ Success: Final size {size_kb} KB")
                sys.exit(0)

        # Best-effort fallback
        shutil.move(temp_output, output_pdf)
        print("⚠ Could not reach target size. Best compression applied.")
        sys.exit(2)

    finally:
        if os.path.exists(temp_output):
            os.remove(temp_output)

if __name__ == "__main__":
    main()
