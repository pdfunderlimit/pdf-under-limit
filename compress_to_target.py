import subprocess
import sys
import os

QUALITY_LEVELS = ["ebook", "screen"]

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

def get_size_kb(file_path):
    return os.path.getsize(file_path) // 1024

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 compress_to_target.py input.pdf output.pdf target_kb")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    target_kb = int(sys.argv[3])

    for quality in QUALITY_LEVELS:
        compress_pdf(input_pdf, output_pdf, quality)
        size_kb = get_size_kb(output_pdf)

        print(f"Tried {quality}: {size_kb} KB")

        if size_kb <= target_kb:
            print(f"✅ Success: Final size {size_kb} KB")
            sys.exit(0)

    print("⚠ Could not reach target size, best effort applied.")
