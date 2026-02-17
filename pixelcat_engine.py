import fitz
import os


class PixelCatEngine:
    def get_info(self, path):
        """Returns basic info about the PDF."""
        try:
            doc = fitz.open(path)
            res = {"Pages": len(doc), "Encrypted": doc.is_encrypted}
            doc.close()
            return res
        except:
            return {"Pages": 0, "Encrypted": False}

    def get_page_pixmap(self, path, page_num, zoom=1.0):
        """Converts a PDF page into a QPixmap for the viewer."""
        try:
            doc = fitz.open(path)
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            from PyQt6.QtGui import QImage, QPixmap
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            doc.close()
            return QPixmap.fromImage(img)
        except:
            return None

    def extract_pages(self, input_path, start_page, end_page, output_path):
        """Splits specific ranges into a new file."""
        doc = fitz.open(input_path)
        total = len(doc)
        start = max(0, min(start_page, total - 1))
        end = max(0, min(end_page, total - 1))
        if start > end: start, end = end, start

        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start, to_page=end)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        new_doc.save(output_path)
        new_doc.close()
        doc.close()

    def merge_pdfs(self, paths, output_path):
        """Combines multiple files into one."""
        result = fitz.open()
        for path in paths:
            with fitz.open(path) as sub_doc:
                result.insert_pdf(sub_doc)
        result.save(output_path)
        result.close()

    def set_password(self, input_path, output_path, password):
        """Encrypts the PDF with AES-256."""
        doc = fitz.open(input_path)
        doc.save(output_path, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=password)
        doc.close()