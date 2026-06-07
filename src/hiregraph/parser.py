from __future__ import annotations
import io


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Return plain text from a PDF, DOCX, TXT, or MD file."""
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if name.endswith(".docx"):
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    return file_bytes.decode("utf-8", errors="replace")
