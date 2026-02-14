import os
import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter
from PIL import Image, ImageTk

class PixelCatEngine:
    def __init__(self):
        self.brand = "PixelCat-PDF"

    def get_info(self, input_path):
        try:
            reader = PdfReader(input_path)
            return {"Pages": len(reader.pages)}
        except Exception:
            return {"Pages": 0}

    def get_page_image(self, pdf_path, page_num, zoom=1.2, rotation=0):
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)
        page.set_rotation(rotation)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        tk_img = ImageTk.PhotoImage(img)
        doc.close()
        return tk_img

    def get_all_text(self, pdf_path):
        try:
            doc = fitz.open(pdf_path)
            full_text = "".join([page.get_text() for page in doc])
            doc.close()
            return full_text
        except Exception as e:
            return f"Error: {str(e)}"

    def save_organized_pdf(self, input_path, output_path, page_configs):
        try:
            reader = PdfReader(input_path)
            writer = PdfWriter()
            for config in page_configs:
                idx = config['source_idx']
                page = reader.pages[idx]
                page.rotate(config['rotation'])
                writer.add_page(page)
            with open(output_path, "wb") as f:
                writer.write(f)
            return "File organized and saved!"
        except Exception as e:
            return f"Failed to save: {str(e)}"

    def merge_pdfs(self, file_list, output_path):
        try:
            writer = PdfWriter()
            for file in file_list:
                reader = PdfReader(file)
                for page in reader.pages:
                    writer.add_page(page)
            with open(output_path, "wb") as f:
                writer.write(f)
            return f"Merged {len(file_list)} files."
        except Exception as e:
            return f"Merge failed: {str(e)}"

    def extract_range(self, input_path, output_path, start, end):
        try:
            reader = PdfReader(input_path)
            writer = PdfWriter()
            for i in range(start - 1, end):
                if 0 <= i < len(reader.pages):
                    writer.add_page(reader.pages[i])
            with open(output_path, "wb") as f:
                writer.write(f)
            return "Range saved successfully!"
        except Exception as e:
            return f"Error: {str(e)}"

    def protect_pdf(self, input_path, output_path, password):
        try:
            reader = PdfReader(input_path)
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            writer.encrypt(password)
            with open(output_path, "wb") as f:
                writer.write(f)
            return "PDF Protected!"
        except Exception as e:
            return f"Security error: {str(e)}"