import fitz  # PyMuPDF
import docx
import io
from typing import Optional


class DocumentParser:
    """Strategy interface for extracting text from raw file bytes."""
    
    @staticmethod
    def parse(file_bytes: bytes, file_type: str) -> Optional[str]:
        if file_type == "application/pdf" or file_type == "pdf":
            return DocumentParser._parse_pdf(file_bytes)
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_type == "docx":
            return DocumentParser._parse_docx(file_bytes)
        elif file_type == "text/plain" or file_type == "txt":
            return DocumentParser._parse_txt(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    @staticmethod
    def _parse_pdf(file_bytes: bytes) -> str:
        text_content = []
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text_content.append(page.get_text())
        return "\n\n".join(text_content)

    @staticmethod
    def _parse_docx(file_bytes: bytes) -> str:
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text])

    @staticmethod
    def _parse_txt(file_bytes: bytes) -> str:
        return file_bytes.decode("utf-8", errors="replace")
