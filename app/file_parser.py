"""File parser — extracts text from uploaded PDF and TXT files."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# WHY ThreadPoolExecutor: pdfplumber is a synchronous, CPU-bound library.
# Running it directly in an async context would block the event loop,
# preventing other requests from being served. asyncio.run_in_executor
# offloads it to a thread pool so the event loop stays responsive.
_executor = ThreadPoolExecutor(max_workers=2)

ALLOWED_EXTENSIONS = {".txt", ".pdf"}
MAX_PDF_PAGES = 20
PDF_MAGIC_BYTES = b"%PDF-"


def _extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from PDF bytes (runs in thread pool, not async)."""
    import io
    import pdfplumber

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        pages = pdf.pages[:MAX_PDF_PAGES]
        texts = [page.extract_text() or "" for page in pages]
    return "\n\n".join(texts).strip()


async def parse_file(filename: str, content: bytes) -> str:
    """Parse an uploaded file and return extracted text.

    Args:
        filename: Original filename (used for extension detection).
        content: Raw file bytes.

    Returns:
        Extracted text content.

    Raises:
        ValueError: If file type is not supported or validation fails.
    """
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    if ext == ".txt":
        return content.decode("utf-8").strip()

    if ext == ".pdf":
        # Validate magic bytes — prevents someone from uploading a .exe renamed to .pdf
        if not content[:5].startswith(PDF_MAGIC_BYTES):
            raise ValueError("File does not appear to be a valid PDF")

        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(_executor, _extract_pdf_text, content)

        if not text:
            raise ValueError("Could not extract text from PDF — file may be image-only")

        return text

    raise ValueError(f"Unhandled file type: {ext}")
