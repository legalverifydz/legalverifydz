"""
ocr.py -- LegalVerifyDZ
================================================================
Optical Character Recognition fallback for scanned (image-only)
PDFs -- contracts that were printed, signed, and scanned back in,
where pdfplumber's normal text-layer extraction finds nothing
because there is no text layer at all, only a picture of text.

WHY THIS IS A SEPARATE MODULE
------------------------------
None of this changes anything for text-based PDFs and Word files --
they keep working exactly as before. This module is only imported
and used as a FALLBACK, the moment normal extraction comes back
empty -- and if its own requirements are missing, it fails safely
with a clear message instead of crashing the page.

EXTERNAL REQUIREMENTS
----------------------
Rendering a PDF page to an image reuses pdfplumber, which the app
already depends on for text extraction (via its pypdfium2 backend --
no new pip package, no ImageMagick/poppler needed for that part).

    pip install pytesseract Pillow

`pytesseract` is only a thin Python wrapper around a real OCR
engine, Tesseract, which is a separate program installed once on the
machine itself (not via pip):

    - Windows: download & run the installer from
      https://github.com/UB-Mannheim/tesseract/wiki
      During setup, tick the "Arabic" and "French" language packs
      (English is included by default). After installing, either add
      the install folder to your system PATH, or set the path
      explicitly below (see TESSERACT_CMD).

    - Linux (Debian/Ubuntu):
      sudo apt install tesseract-ocr tesseract-ocr-ara tesseract-ocr-fra

    - macOS:
      brew install tesseract tesseract-lang

Until Tesseract itself (with the languages you need) is installed,
ocr_pdf() below returns a clear, actionable error message rather
than raising -- the person just won't get OCR for scanned PDFs yet,
everything else keeps working.
================================================================
"""

# If Tesseract is installed but not on your system PATH (common on
# Windows), uncomment and edit this line instead of editing PATH.
# Safe to leave set even when deploying to Streamlit Cloud/Linux: this
# path is only actually used if it exists on the machine running the
# code (see the os.path.exists check below), so the same ocr.py works
# unmodified on your local Windows machine AND on a Linux host.
# TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_CMD = None

DEFAULT_LANGUAGES = "ara+fra+eng"  # OCR all three at once; contracts
                                   # in Algeria are frequently bilingual.
DEFAULT_DPI = 250
MAX_PAGES = 15  # OCR is slow; cap it so a huge scan can't hang the page.


def dependencies_available():
    """True if pdfplumber (for rendering) + pytesseract + Pillow are
    all importable. Does NOT confirm the Tesseract binary itself is
    installed -- that can only be known by actually trying to run it."""

    try:
        import pdfplumber    # noqa: F401
        import pytesseract   # noqa: F401
        from PIL import Image  # noqa: F401
        return True
    except ImportError:
        return False


def ocr_pdf(file_obj, languages=DEFAULT_LANGUAGES, dpi=DEFAULT_DPI, max_pages=MAX_PAGES):
    """
    Attempt to OCR a scanned PDF.

    file_obj: a file-like object opened in binary mode (e.g. the
              Streamlit UploadedFile also accepted by extract_pdf()).

    Returns (text, error):
        (text, None)   on success -- `text` is the recognized text.
        (None, error)  when OCR could not run or found nothing --
                       `error` is a message safe to show the user.

    Never raises: every failure path is caught and turned into an
    error string instead.
    """

    try:
        import pdfplumber
        import pytesseract
    except ImportError:
        return None, (
            "OCR is not available on this installation: the "
            "pytesseract and Pillow packages are not installed. "
            "Run: pip install pytesseract Pillow "
            "(see ocr.py for the full setup, including the separate "
            "Tesseract OCR program)."
        )

    # Only use the hardcoded path if it actually exists on THIS machine.
    # This is what makes the same ocr.py work both locally on Windows
    # (where TESSERACT_CMD may be set to a Windows path) and on a Linux
    # host such as Streamlit Cloud (where that Windows path does not
    # exist, so pytesseract instead finds the apt-installed `tesseract`
    # automatically via the system PATH -- see packages.txt).
    import os
    if TESSERACT_CMD and os.path.exists(TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

    try:
        file_obj.seek(0)
        document = pdfplumber.open(file_obj)
    except Exception:
        return None, "Could not open this PDF for OCR (invalid or corrupted file)."

    page_count = len(document.pages)

    if page_count == 0:
        document.close()
        return None, "This PDF has no pages."

    text_parts = []
    ocr_error = None

    try:
        pages_to_process = min(page_count, max_pages)

        for page_index in range(pages_to_process):
            page = document.pages[page_index]
            rendered = page.to_image(resolution=dpi)
            image = rendered.original  # a PIL.Image

            page_text = pytesseract.image_to_string(image, lang=languages)

            if page_text and page_text.strip():
                text_parts.append(page_text.strip())

    except pytesseract.TesseractNotFoundError:
        ocr_error = (
            "The OCR Python packages are installed, but the Tesseract "
            "OCR program itself was not found on this machine. Install "
            "it separately (see the setup notes at the top of ocr.py) "
            "and make sure it is on your system PATH."
        )
    except Exception as exc:
        ocr_error = "OCR failed unexpectedly: {}".format(exc)
    finally:
        document.close()

    if ocr_error:
        return None, ocr_error

    full_text = "\n\n".join(text_parts).strip()

    if not full_text:
        return None, (
            "OCR ran but could not recognize any text in this document "
            "-- the scan quality may be too low, or the language packs "
            "for this document's language are not installed in Tesseract."
        )

    if page_count > max_pages:
        full_text += (
            "\n\n[Note: only the first {} of {} pages were processed by "
            "OCR.]".format(max_pages, page_count)
        )

    return full_text, None


if __name__ == "__main__":
    if not dependencies_available():
        print(
            "OCR dependencies (pytesseract / Pillow) are not installed "
            "in this environment -- this is expected unless you've "
            "already run: pip install pytesseract Pillow"
        )
    else:
        print(
            "OCR dependencies are importable. To fully verify OCR works, "
            "run ocr_pdf() on an actual scanned PDF file and confirm "
            "Tesseract itself is installed and on PATH."
        )
