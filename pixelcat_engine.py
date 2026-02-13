import os
import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter
from PIL import Image, ImageTk

class PixelCatEngine:
    def __init__(self):
        self.brand = "PixelCat-PDF"

    def get_info(self, input_path):
        reader = PdfReader(input_path)
        return {"Pages": len(reader.pages)}

    def get_page_image(self, pdf_path, page_num, zoom=1.2):
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return ImageTk.PhotoImage(img)

    def split_all(self, input_path, output_folder):
        if not os.path.exists(output_folder): os.makedirs(output_folder)
        reader = PdfReader(input_path)
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            with open(os.path.join(output_folder, f"Page_{i+1}.pdf"), "wb") as f:
                writer.write(f)
        return f"Split {len(reader.pages)} pages."

    def extract_range(self, input_path, output_path, start, end):
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for i in range(start - 1, end):
            if 0 <= i < len(reader.pages):
                writer.add_page(reader.pages[i])
        with open(output_path, "wb") as f:
            writer.write(f)
        return "Range saved!"

    def merge_pdfs(self, file_list, output_path):
        """FIXED: Loops through every page of every selected file."""
        writer = PdfWriter()
        total = 0
        for file in file_list:
            reader = PdfReader(file)
            for page in reader.pages:
                writer.add_page(page)
                total += 1
        with open(output_path, "wb") as f:
            writer.write(f)
        return f"Success! Merged {total} pages total."

    def protect_pdf(self, input_path, output_path, password):
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        with open(output_path, "wb") as f:
            writer.write(f)
        return "PDF Password Protected!"