import sys
import os
import ctypes
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from pixelcat_engine import PixelCatEngine

try:
    myappid = 'pixelcat.pdf.alpha.v2'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

VERSION = "v0.2.0-alpha"
ctk.set_appearance_mode("dark")


class PixelCatPDF(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.engine = PixelCatEngine()
        self.title(f"PixelCat-PDF | {VERSION}")
        self.geometry("1100x850")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.icon_tk = None
        self.load_main_icon()

        self.current_pdf = None
        self.merge_queue = []
        self.organize_data = []  # {'rot': 0, 'deleted': False, 'selected': False}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_view()
        self.show_home()

    def load_main_icon(self):
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            img_path = os.path.join(base_path, "Pixel.png")
            if os.path.exists(img_path):
                self.icon_tk = ImageTk.PhotoImage(Image.open(img_path))
                self.after(200, lambda: self.wm_iconphoto(False, self.icon_tk))
        except Exception:
            pass

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="🐈 PixelCat", font=("Arial", 24, "bold")).pack(pady=20)
        ctk.CTkButton(self.sidebar, text="📂 Open PDF", command=self.open_file, fg_color="#3498db").pack(fill="x",
                                                                                                        padx=20,
                                                                                                        pady=10)
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=10, pady=10)

        for name, cmd in [("🏠 Viewer", self.show_home), ("📑 Organizer", self.show_organizer),
                          ("✂️ Splitter", self.show_splitter), ("🔗 Merger", self.show_merger),
                          ("🔒 Security", self.show_security)]:
            ctk.CTkButton(self.nav_frame, text=name, anchor="w", command=cmd).pack(fill="x", pady=2)

        self.copy_btn = ctk.CTkButton(self.sidebar, text="📋 Copy All Text", command=self.copy_text_to_clipboard,
                                      fg_color="#8e44ad")
        self.copy_btn.pack(side="bottom", pady=10, padx=20)

    def setup_main_view(self):
        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew")
        self.home_screen = ctk.CTkScrollableFrame(self.main_view, fg_color="#121212")

        # Organizer
        self.organizer_screen = self.create_tool_screen("Page Organizer")

        # Control Header
        self.org_controls = ctk.CTkFrame(self.organizer_screen, fg_color="transparent")
        self.org_controls.pack(fill="x", padx=20)
        ctk.CTkButton(self.org_controls, text="🗑️ Delete Selected", fg_color="#e74c3c", command=self.bulk_delete,
                      width=150).pack(side="left", padx=5)
        ctk.CTkButton(self.org_controls, text="🔄 Rotate Selected", fg_color="#f39c12", command=self.bulk_rotate,
                      width=150).pack(side="left", padx=5)
        ctk.CTkButton(self.org_controls, text="💾 Save Changes", fg_color="#27ae60", command=self.do_organize_save,
                      width=150).pack(side="right", padx=5)

        self.org_grid = ctk.CTkScrollableFrame(self.organizer_screen, fg_color="#1a1a1a", height=600)
        self.org_grid.pack(fill="both", expand=True, padx=20, pady=10)

        # Other Screens
        self.split_screen = self.create_tool_screen("Splitter")
        self.merge_screen = self.create_tool_screen("Merger")
        self.lock_screen = self.create_tool_screen("Security")

        # Splitter UI
        self.start_ent = ctk.CTkEntry(self.split_screen, placeholder_text="Start");
        self.start_ent.pack(pady=5)
        self.end_ent = ctk.CTkEntry(self.split_screen, placeholder_text="End");
        self.end_ent.pack(pady=5)
        ctk.CTkButton(self.split_screen, text="Run Split", command=self.do_range).pack(pady=10)

        # Merger UI
        m_btns = ctk.CTkFrame(self.merge_screen, fg_color="transparent")
        m_btns.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(m_btns, text="+ Add", command=self.add_to_merge_queue, fg_color="#27ae60").pack(side="left",
                                                                                                      padx=5)
        ctk.CTkButton(m_btns, text="Merge", command=self.do_merge, fg_color="#3498db").pack(side="right", padx=5)
        self.queue_frame = ctk.CTkScrollableFrame(self.merge_screen, fg_color="#1a1a1a", height=400)
        self.queue_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Security
        self.pass_ent = ctk.CTkEntry(self.lock_screen, placeholder_text="Password", show="*");
        self.pass_ent.pack(pady=10)
        ctk.CTkButton(self.lock_screen, text="Lock PDF", command=self.do_lock).pack()

    def create_tool_screen(self, title):
        frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        ctk.CTkLabel(frame, text=title, font=("Arial", 30, "bold")).pack(pady=10)
        return frame

    def switch(self, target):
        for s in [self.home_screen, self.organizer_screen, self.split_screen, self.merge_screen,
                  self.lock_screen]: s.pack_forget()
        target.pack(expand=True, fill="both")

    def show_home(self):
        self.switch(self.home_screen)

    def show_organizer(self):
        self.switch(self.organizer_screen)
        if self.current_pdf: self.refresh_organizer_view()

    def show_splitter(self):
        self.switch(self.split_screen)

    def show_merger(self):
        self.switch(self.merge_screen)

    def show_security(self):
        self.switch(self.lock_screen)

    # --- Organizer Logic ---
    def refresh_organizer_view(self):
        for w in self.org_grid.winfo_children(): w.destroy()
        cols = 4
        for i, data in enumerate(self.organize_data):
            border = "#3498db" if data['selected'] else "#2b2b2b"
            if data['deleted']: border = "#550000"

            frame = ctk.CTkFrame(self.org_grid, fg_color="#2b2b2b", border_width=3, border_color=border)
            frame.grid(row=i // cols, column=i % cols, padx=10, pady=10)

            img = self.engine.get_page_image(self.current_pdf, i, zoom=0.2, rotation=data['rot'])
            lbl = ctk.CTkLabel(frame, image=img, text="")
            lbl.image = img
            if data['deleted']: lbl.configure(alpha=0.3)  # Fades out deleted pages
            lbl.pack(padx=5, pady=5)

            ctk.CTkLabel(frame, text=f"Page {i + 1}", font=("Arial", 10)).pack()
            lbl.bind("<Button-1>", lambda e, idx=i: self.select_page(idx))

    def select_page(self, idx):
        self.organize_data[idx]['selected'] = not self.organize_data[idx]['selected']
        self.refresh_organizer_view()

    def bulk_delete(self):
        for data in self.organize_data:
            if data['selected']:
                data['deleted'] = not data['deleted']
                data['selected'] = False
        self.refresh_organizer_view()

    def bulk_rotate(self):
        for data in self.organize_data:
            if data['selected']:
                data['rot'] = (data['rot'] + 90) % 360
        self.refresh_organizer_view()

    def do_organize_save(self):
        if not self.current_pdf: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if out:
            configs = [{'source_idx': i, 'rotation': d['rot']} for i, d in enumerate(self.organize_data) if
                       not d['deleted']]
            msg = self.engine.save_organized_pdf(self.current_pdf, out, configs)
            messagebox.showinfo("PixelCat", msg)

    # --- Standard Actions ---
    def open_file(self):
        f = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if f and os.path.exists(f):
            self.current_pdf = f
            pages = self.engine.get_info(f)["Pages"]
            self.organize_data = [{'rot': 0, 'deleted': False, 'selected': False} for _ in range(pages)]
            self.render()

    def render(self):
        if self.current_pdf:
            threading.Thread(target=self._threaded_render, daemon=True).start()

    def _threaded_render(self):
        try:
            imgs = [self.engine.get_page_image(self.current_pdf, i, 1.2) for i in
                    range(min(self.engine.get_info(self.current_pdf)["Pages"], 12))]
            self.after(0, self._update_ui, imgs)
        except:
            pass

    def _update_ui(self, imgs):
        for w in self.home_screen.winfo_children(): w.destroy()
        for img in imgs: ctk.CTkLabel(self.home_screen, image=img, text="").pack(pady=10)

    def add_to_merge_queue(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        for f in files:
            if f not in self.merge_queue: self.merge_queue.append(f)
        self.refresh_queue_ui()

    def refresh_queue_ui(self):
        for w in self.queue_frame.winfo_children(): w.destroy()
        for i, path in enumerate(self.merge_queue):
            row = ctk.CTkFrame(self.queue_frame, fg_color="#2b2b2b")
            row.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(row, text=f"{os.path.basename(path)}").pack(side="left", padx=10)

    def do_merge(self):
        if not self.merge_queue: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if out: messagebox.showinfo("PixelCat", self.engine.merge_pdfs(self.merge_queue, out))

    def do_range(self):
        if not self.current_pdf: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if out: messagebox.showinfo("PixelCat",
                                    self.engine.extract_range(self.current_pdf, out, int(self.start_ent.get()),
                                                              int(self.end_ent.get())))

    def do_lock(self):
        if not self.current_pdf: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if out: messagebox.showinfo("PixelCat", self.engine.protect_pdf(self.current_pdf, out, self.pass_ent.get()))

    def copy_text_to_clipboard(self):
        if not self.current_pdf: return
        text = self.engine.get_all_text(self.current_pdf)
        self.clipboard_clear();
        self.clipboard_append(text);
        self.update()
        messagebox.showinfo("PixelCat", "Text copied!")

    def on_closing(self):
        self.destroy(); sys.exit()


if __name__ == "__main__":
    app = PixelCatPDF()
    app.mainloop()