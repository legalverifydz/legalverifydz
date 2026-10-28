"""
ocr.py -- LegalVerifyDZ
================================================================
Optical Character Recognition for scanned contracts: image-only PDFs
and photos/scans saved as JPG / PNG / TIFF / WEBP.

WHAT CHANGED IN THIS VERSION (and why)
---------------------------------------
1. OCR is decided PAGE BY PAGE, not "only when the whole PDF has zero
   text". Phone-scanner apps stamp a tiny digital text line on every
   page ("Scanned by ..."); the old all-or-nothing test saw that stamp,
   decided the PDF was a normal digital one, and analysed 21 characters.
2. Images can be OCR'd directly (ocr_image_file), with EXIF rotation
   fixed, which is how most people actually scan a contract.
3. diagnose() reports exactly what is installed/missing (Python
   packages, the Tesseract program, each language pack), so a failure
   can be identified in one click instead of guessed.
4. Every failure returns a short machine-readable CODE (see ERROR_CODES)
   that app.py translates into an actionable message.
5. Missing language packs no longer fail silently: Tesseract happily
   "recognises" Arabic with only the English model and returns Latin
   gibberish, so the missing pack is reported as a warning.

EXTERNAL REQUIREMENTS
----------------------
    pip install pytesseract Pillow          (pdfplumber is already used
                                              by the app and renders the
                                              PDF pages itself)

plus the Tesseract OCR program, installed once on the machine:
    - Windows: installer from https://github.com/UB-Mannheim/tesseract/wiki
      (tick the Arabic and French language data during setup)
    - Linux/Streamlit Cloud: packages.txt with
      tesseract-ocr, tesseract-ocr-ara, tesseract-ocr-fra
================================================================
"""

import io
import os
import platform
import shutil
import time

# If Tesseract is installed but not on PATH (common on Windows), set the
# full path here. It is only used if that file really exists on the
# machine running the code, so the same file works unmodified on Windows
# and on a Linux host.
# TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_CMD = None

WANTED_LANGUAGES = ("ara", "fra", "eng")  # contracts here are often bilingual
DEFAULT_DPI = 200
MAX_PAGES = 15              # OCR is slow; cap it
MIN_PAGE_CHARS = 40         # a page with fewer digital characters is
                            # considered "possibly scanned"
MIN_QUALITY = 0.60          # below this, OCR output looks like gibberish

# Machine-readable failure codes returned in the 'error' slot.
ERROR_CODES = (
    "deps_missing",        # pytesseract / Pillow not installed
    "tesseract_missing",   # Tesseract program not found
    "tesseract_blocked",   # Windows refuses to run it (WinError 740)
    "no_languages",        # none of the wanted language packs installed
    "open_failed",         # file could not be opened as PDF / image
    "no_pages",
    "no_text",             # OCR ran but found nothing readable
    "unexpected",
)


# ----------------------------------------------------------------
# Environment helpers
# ----------------------------------------------------------------

def _import_pytesseract():
    """Returns the configured pytesseract module, or None if the Python
    packages are missing."""
    try:
        import pytesseract
        from PIL import Image  # noqa: F401
    except ImportError:
        return None

    if TESSERACT_CMD and os.path.exists(TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

    return pytesseract


def _classify_exception(exc, pytesseract):
    """Map a low-level exception to one of ERROR_CODES."""
    text = "{} {}".format(type(exc).__name__, exc).lower()

    if getattr(exc, "winerror", None) == 740 or "740" in text \
            or "requires elevation" in text:
        return "tesseract_blocked"

    not_found = getattr(pytesseract, "TesseractNotFoundError", ())
    if not_found and isinstance(exc, not_found):
        return "tesseract_missing"

    if isinstance(exc, FileNotFoundError):
        return "tesseract_missing"

    return "unexpected"


_DIAG_CACHE = {"at": 0.0, "value": None}


def diagnose(refresh=False):
    """
    Inspect the OCR setup WITHOUT processing any document.

    Returns a dict:
        platform, packages{pytesseract,pillow,pdf_rendering},
        tesseract_path, tesseract_version, tesseract_error_code,
        tesseract_error, languages_installed[], languages_missing[],
        ready (OCR can run at all), ready_for_arabic.

    The result is cached for 60 s because it spawns the Tesseract
    process, and Streamlit re-runs the script on every click.
    """

    now = time.time()
    if not refresh and _DIAG_CACHE["value"] and now - _DIAG_CACHE["at"] < 60:
        return _DIAG_CACHE["value"]

    info = {
        "platform": platform.system() or "unknown",
        "packages": {"pytesseract": False, "pillow": False, "pdf_rendering": False},
        "tesseract_path": None,
        "tesseract_version": None,
        "tesseract_error_code": None,
        "tesseract_error": None,
        "languages_installed": [],
        "languages_missing": list(WANTED_LANGUAGES),
        "ready": False,
        "ready_for_arabic": False,
    }

    try:
        import PIL  # noqa: F401
        info["packages"]["pillow"] = True
    except ImportError:
        pass

    try:
        import pypdfium2  # noqa: F401
        info["packages"]["pdf_rendering"] = True
    except ImportError:
        pass

    pytesseract = None
    try:
        import pytesseract as _pt
        info["packages"]["pytesseract"] = True
        pytesseract = _import_pytesseract() or _pt
    except ImportError:
        pass

    if pytesseract is not None:
        cmd = pytesseract.pytesseract.tesseract_cmd
        info["tesseract_path"] = shutil.which(cmd) or (cmd if os.path.exists(cmd) else None)

        try:
            info["tesseract_version"] = str(pytesseract.get_tesseract_version())
            langs = pytesseract.get_languages(config="")
            info["languages_installed"] = sorted(langs)
        except Exception as exc:  # noqa: BLE001 -- we classify, not hide
            info["tesseract_error_code"] = _classify_exception(exc, pytesseract)
            info["tesseract_error"] = "{}: {}".format(type(exc).__name__, exc)

    installed = set(info["languages_installed"])
    info["languages_missing"] = [l for l in WANTED_LANGUAGES if l not in installed]
    info["ready"] = bool(
        info["packages"]["pytesseract"]
        and info["packages"]["pillow"]
        and info["tesseract_version"]
        and installed
    )
    info["ready_for_arabic"] = info["ready"] and "ara" in installed

    _DIAG_CACHE["at"] = now
    _DIAG_CACHE["value"] = info
    return info


def pick_languages(wanted=WANTED_LANGUAGES):
    """Return ('ara+eng', ['fra']) -- the installed subset, and the
    wanted languages that are missing. ('', [...]) if none installed."""
    installed = set(diagnose()["languages_installed"])
    use = [l for l in wanted if l in installed]
    missing = [l for l in wanted if l not in installed]
    return "+".join(use), missing


# ----------------------------------------------------------------
# Image helpers
# ----------------------------------------------------------------

def _prepare(image):
    """Make a photo/scan easier for Tesseract: fix phone rotation,
    grayscale, stretch contrast, upscale small images."""
    from PIL import Image, ImageOps

    image = ImageOps.exif_transpose(image)
    image = image.convert("L")
    image = ImageOps.autocontrast(image)

    if min(image.size) < 1000:
        factor = 2
        image = image.resize(
            (image.width * factor, image.height * factor), Image.LANCZOS
        )
    return image


def text_quality(text):
    """Share of non-space characters that look like real text
    (letters, digits, usual punctuation). Gibberish scores low."""
    chars = [c for c in (text or "") if not c.isspace()]
    if not chars:
        return 0.0
    ok = sum(1 for c in chars if c.isalnum() or c in ".,;:()-–—'\"«»/%،؛؟€$°")
    return ok / len(chars)


def _result(text, error, **info):
    info.setdefault("warnings", [])
    info.setdefault("languages_used", "")
    info.setdefault("languages_missing", [])
    return text, error, info


def _languages_or_error():
    """(lang_string, missing, error_code|None, diag)."""
    diag = diagnose()
    if not diag["packages"]["pytesseract"] or not diag["packages"]["pillow"]:
        return "", [], "deps_missing", diag
    if diag["tesseract_error_code"]:
        return "", [], diag["tesseract_error_code"], diag
    if not diag["tesseract_version"]:
        return "", [], "tesseract_missing", diag
    lang, missing = pick_languages()
    if not lang:
        return "", missing, "no_languages", diag
    return lang, missing, None, diag


def _finish(parts, lang, missing, extra_warnings=None, truncated=None):
    text = "\n\n".join(p for p in parts if p).strip()
    warnings = list(extra_warnings or [])

    if "ara" in missing:
        warnings.append("ara_missing")
    if "fra" in missing:
        warnings.append("fra_missing")
    if truncated:
        warnings.append("truncated")

    if not text:
        return _result(None, "no_text", languages_used=lang,
                       languages_missing=missing, warnings=warnings)

    if text_quality(text) < MIN_QUALITY:
        warnings.append("low_quality")

    return _result(text, None, languages_used=lang,
                   languages_missing=missing, warnings=warnings,
                   truncated=truncated)


# ----------------------------------------------------------------
# Public API
# ----------------------------------------------------------------

def ocr_image_file(file_obj, max_pages=MAX_PAGES):
    """OCR a JPG / PNG / TIFF / WEBP file (multi-page TIFF supported).
    Returns (text, error_code, info)."""

    lang, missing, code, _ = _languages_or_error()
    if code:
        return _result(None, code, languages_missing=missing)

    pytesseract = _import_pytesseract()
    from PIL import Image

    try:
        file_obj.seek(0)
        image = Image.open(io.BytesIO(file_obj.read()))
        frames = getattr(image, "n_frames", 1)
    except Exception:  # noqa: BLE001
        return _result(None, "open_failed", languages_missing=missing)

    parts = []
    try:
        for index in range(min(frames, max_pages)):
            image.seek(index)
            parts.append(
                pytesseract.image_to_string(_prepare(image.copy()), lang=lang).strip()
            )
    except Exception as exc:  # noqa: BLE001
        return _result(None, _classify_exception(exc, pytesseract),
                       languages_missing=missing)

    return _finish(parts, lang, missing,
                   truncated=(frames > max_pages) or None)


def ocr_pdf_pages(file_obj, page_indices=None, dpi=DEFAULT_DPI,
                  max_pages=MAX_PAGES):
    """
    OCR selected pages (all pages if page_indices is None) of a PDF.

    Returns (pages_text, error_code, info) where pages_text maps the
    0-based page index to its recognised text (empty dict on failure).
    """

    lang, missing, code, _ = _languages_or_error()
    if code:
        return {}, code, _result(None, code, languages_missing=missing)[2]

    pytesseract = _import_pytesseract()

    try:
        import pdfplumber
        file_obj.seek(0)
        document = pdfplumber.open(file_obj)
    except Exception:  # noqa: BLE001
        return {}, "open_failed", _result(None, "open_failed")[2]

    pages_text = {}
    try:
        total = len(document.pages)
        if total == 0:
            return {}, "no_pages", _result(None, "no_pages")[2]

        wanted = list(range(total)) if page_indices is None else list(page_indices)
        truncated = len(wanted) > max_pages
        wanted = wanted[:max_pages]

        for index in wanted:
            rendered = document.pages[index].to_image(resolution=dpi)
            text = pytesseract.image_to_string(
                _prepare(rendered.original), lang=lang
            )
            if text and text.strip():
                pages_text[index] = text.strip()
    except Exception as exc:  # noqa: BLE001
        code = _classify_exception(exc, pytesseract)
        return {}, code, _result(None, code, languages_missing=missing)[2]
    finally:
        document.close()

    joined = "\n\n".join(pages_text[i] for i in sorted(pages_text))
    _, error, info = _finish([joined], lang, missing,
                             truncated=truncated or None)
    return (pages_text if error is None else {}), error, info


def ocr_pdf_detailed(file_obj, dpi=DEFAULT_DPI, max_pages=MAX_PAGES):
    """Whole-document OCR. Returns (text, error_code, info)."""
    pages_text, error, info = ocr_pdf_pages(file_obj, None, dpi, max_pages)
    if error:
        return None, error, info
    return "\n\n".join(pages_text[i] for i in sorted(pages_text)), None, info


def ocr_pdf(file_obj, languages=None, dpi=DEFAULT_DPI, max_pages=MAX_PAGES):
    """Backward-compatible wrapper: returns (text, error_message)."""
    text, error, _ = ocr_pdf_detailed(file_obj, dpi=dpi, max_pages=max_pages)
    return text, (None if error is None else "OCR failed: {}".format(error))


def dependencies_available():
    d = diagnose()
    return d["packages"]["pytesseract"] and d["packages"]["pillow"]


if __name__ == "__main__":
    import json
    print(json.dumps(diagnose(refresh=True), indent=2, ensure_ascii=False))
