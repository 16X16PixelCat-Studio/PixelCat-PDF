import sys
import os
import ctypes
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from pixelcat_engine import PixelCatEngine

# --- WINDOWS TASKBAR FIX ---
try:
    myappid = 'pixelcat.pdf.alpha.v1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

VERSION = "v0.1.1-alpha"
ctk.set_appearance_mode("dark")


class PixelCatPDF(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.engine = PixelCatEngine()
        self.title(f"PixelCat-PDF | {VERSION}")
        self.geometry("1100x850")

        # Protocol to handle clean exit and kill threads
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.icon_tk = None
        self.load_main_icon()

        # State management
        self.current_pdf = None
        self.zoom_level = 1.2
        self.page_images = []
        self.zoom_timer = None

        # Grid config
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
                self.after(500, lambda: self.wm_iconphoto(False, self.icon_tk))
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

        for name, cmd in [("🏠 Viewer", self.show_home), ("✂️ Splitter", self.show_splitter),
                          ("🔗 Merger", self.show_merger), ("🔒 Security", self.show_security)]:
            ctk.CTkButton(self.nav_frame, text=name, anchor="w", command=cmd).pack(fill="x", pady=2)

        ctk.CTkLabel(self.sidebar, text="Zoom Level").pack(pady=(20, 0))
        self.zoom_slider = ctk.CTkSlider(self.sidebar, from_=0.5, to=2.0, command=self.debounce_zoom)
        self.zoom_slider.set(1.2)
        self.zoom_slider.pack(pady=10, padx=20)

        self.mode_switch = ctk.CTkSwitch(self.sidebar, text="Dark Mode", command=self.toggle_mode)
        self.mode_switch.select()
        self.mode_switch.pack(side="bottom", pady=20)

    def setup_main_view(self):
        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew")

        self.home_screen = ctk.CTkScrollableFrame(self.main_view, fg_color="#121212")

        # Tool Screens
        self.split_screen = self.create_tool_screen("Splitter")
        self.start_ent = ctk.CTkEntry(self.split_screen, placeholder_text="Start Page");
        self.start_ent.pack(pady=5)
        self.end_ent = ctk.CTkEntry(self.split_screen, placeholder_text="End Page");
        self.end_ent.pack(pady=5)
        ctk.CTkButton(self.split_screen, text="Run Split", command=self.do_range).pack(pady=10)

        self.merge_screen = self.create_tool_screen("Merger")
        ctk.CTkButton(self.merge_screen, text="Select Files & Merge", command=self.do_merge, height=40).pack(pady=20)

        self.lock_screen = self.create_tool_screen("Security")
        self.pass_ent = ctk.CTkEntry(self.lock_screen, placeholder_text="Set Password", show="*");
        self.pass_ent.pack(pady=10)
        ctk.CTkButton(self.lock_screen, text="Lock PDF", command=self.do_lock).pack()

    def create_tool_screen(self, title):
        frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        ctk.CTkLabel(frame, text=title, font=("Arial", 30, "bold")).pack(pady=20)
        return frame

    def switch(self, target):
        for s in [self.home_screen, self.split_screen, self.merge_screen, self.lock_screen]: s.pack_forget()
        target.pack(expand=True, fill="both")

    def show_home(self):
        self.switch(self.home_screen)

    def show_splitter(self):
        self.switch(self.split_screen)

    def show_merger(self):
        self.switch(self.merge_screen)

    def show_security(self):
        self.switch(self.lock_screen)

    def open_file(self):
        f = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if f and os.path.exists(f):
            self.current_pdf = f
            self.title(f"PixelCat-PDF | {os.path.basename(f)}")
            self.render()

    def debounce_zoom(self, v):
        self.zoom_level = float(v)
        if self.zoom_timer: self.after_cancel(self.zoom_timer)
        self.zoom_timer = self.after(300, self.render)

    def render(self):
        if self.current_pdf and os.path.exists(self.current_pdf):
            threading.Thread(target=self._threaded_render, daemon=True).start()

    def _threaded_render(self):
        try:
            info = self.engine.get_info(self.current_pdf)
            total = info["Pages"]
            render_limit = min(total, 15)

            imgs = [self.engine.get_page_image(self.current_pdf, i, self.zoom_level) for i in range(render_limit)]
            self.after(0, self._update_ui, imgs, total > render_limit)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Render Error", str(e)))

    def _update_ui(self, imgs, is_limited):
        for w in self.home_screen.winfo_children(): w.destroy()
        self.page_images.clear()
        self.page_images = imgs
        for img in self.page_images:
            ctk.CTkLabel(self.home_screen, image=img, text="").pack(pady=10)
        if is_limited:
            ctk.CTkLabel(self.home_screen, text="--- Previewing First 15 Pages ---", text_color="gray").pack(pady=20)

    def do_merge(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        if files:
            out = filedialog.asksaveasfilename(defaultextension=".pdf")
            if out: messagebox.showinfo("PixelCat", self.engine.merge_pdfs(files, out))

    def do_range(self):
        if not self.current_pdf: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if out:
            try:
                msg = self.engine.extract_range(self.current_pdf, out, int(self.start_ent.get()),
                                                int(self.end_ent.get()))
                messagebox.showinfo("PixelCat", msg)
            except ValueError:
                messagebox.showerror("Error", "Enter valid page numbers!")

    def do_lock(self):
        if not self.current_pdf: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if out: messagebox.showinfo("PixelCat", self.engine.protect_pdf(self.current_pdf, out, self.pass_ent.get()))

    def toggle_mode(self):
        ctk.set_appearance_mode("dark" if self.mode_switch.get() == 1 else "light")

    def on_closing(self):
        self.page_images.clear()
        self.destroy()
        sys.exit()


if __name__ == "__main__":
    app = PixelCatPDF()
    app.mainloop()