import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter
from PyQt6.QtGui import QImage, QPixmap


class PixelCatEngine:
    def __init__(self):
        self.brand = "PixelCat-PDF"

    def get_info(self, input_path):
        try:
            reader = PdfReader(input_path)
            return {"Pages": len(reader.pages)}
        except Exception:
            return {"Pages": 0}

    def get_page_pixmap(self, pdf_path, page_num, zoom=1.2):
        """Renders PDF page and converts it directly to a PyQt QPixmap."""
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert fitz pixmap to QImage, then to QPixmap
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(img)

    def get_page_text(self, pdf_path, page_num):
        """Extracts text from a specific page."""
        try:
            doc = fitz.open(pdf_path)
            text = doc[page_num].get_text()
            doc.close()
            return text
        except Exception:
            return ""

    def get_all_text(self, pdf_path):
        """Extracts text from the entire document."""
        try:
            doc = fitz.open(pdf_path)
            full_text = "".join([page.get_text() for page in doc])
            doc.close()
            return full_text
        except Exception as e:
            return f"Error: {str(e)}"