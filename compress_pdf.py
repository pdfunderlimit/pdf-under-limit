import subprocess
import sys

def compress_pdf(input_pdf, output_pdf, quality="ebook"):
    """
    quality options:
    screen   -> smallest size (lowest quality)
    ebook    -> balanced (recommended)
    printer  -> higher quality
    """

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

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 compress_pdf.py input.pdf output.pdf")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]

    compress_pdf(input_pdf, output_pdf)
    print("✅ Compression complete")
