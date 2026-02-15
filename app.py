import sys
import os
import ctypes
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from pixelcat_engine import PixelCatEngine

try:
    myappid = 'pixelcat.pdf.alpha.v3'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

VERSION = "v0.3.0"
ctk.set_appearance_mode("dark")


class PixelCatPDF(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.engine = PixelCatEngine()
        self.title(f"PixelCat-PDF | {VERSION}")
        self.geometry("1200x850")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.icons_path = os.path.join(self.base_path, "icons")

        self.icon_tk = None
        self.settings_icon_tk = None
        self.load_main_icon()

        self.current_pdf = None
        self.merge_queue = []
        self.organize_data = []
        self.settings_window = None

        # Increased initial scroll sensitivity
        self.scroll_speed = 5

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_view()
        self.show_home()

    def load_main_icon(self):
        try:
            img_path = os.path.join(self.icons_path, "PixelCat-PDF.png")
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

        nav_items = [
            ("🏠 Viewer", self.show_home),
            ("📑 Organizer", self.show_organizer),
            ("✂️ Splitter", self.show_splitter),
            ("🔗 Merger", self.show_merger),
            ("🔒 Security", self.show_security)
        ]

        for name, cmd in nav_items:
            ctk.CTkButton(self.nav_frame, text=name, anchor="w", command=cmd).pack(fill="x", pady=2)

        ctk.CTkButton(self.nav_frame, text="⚙️ Settings", anchor="w", command=self.open_settings).pack(fill="x",
                                                                                                       pady=(20, 2))

        self.copy_btn = ctk.CTkButton(self.sidebar, text="📋 Copy All Text", command=self.copy_text_to_clipboard,
                                      fg_color="#8e44ad")
        self.copy_btn.pack(side="bottom", pady=10, padx=20)

    def setup_main_view(self):
        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew")

        self.home_screen = ctk.CTkFrame(self.main_view, fg_color="transparent")

        self.pdf_scroll = ctk.CTkScrollableFrame(self.home_screen, fg_color="#121212")
        self.pdf_scroll.pack(side="left", fill="both", expand=True, padx=(5, 2), pady=5)

        # Bind scrolling to our high-speed logic
        self.pdf_scroll.bind_all("<MouseWheel>", self._on_mousewheel)

        self.text_inspector_frame = ctk.CTkFrame(self.home_screen, width=350)
        self.text_inspector_frame.pack(side="right", fill="y", padx=(2, 5), pady=5)
        ctk.CTkLabel(self.text_inspector_frame, text="Text Inspector", font=("Arial", 12, "bold")).pack(pady=5)
        self.text_inspector = ctk.CTkTextbox(self.text_inspector_frame, width=340, activate_scrollbars=True)
        self.text_inspector.pack(fill="both", expand=True, padx=5, pady=5)
        self.text_inspector.insert("0.0", "Select a page to extract text...")

        self.organizer_screen = self.create_tool_screen("Page Organizer")
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

        self.split_screen = self.create_tool_screen("Splitter")
        self.merge_screen = self.create_tool_screen("Merger")
        self.lock_screen = self.create_tool_screen("Security")

        self.start_ent = ctk.CTkEntry(self.split_screen, placeholder_text="Start");
        self.start_ent.pack(pady=5)
        self.end_ent = ctk.CTkEntry(self.split_screen, placeholder_text="End");
        self.end_ent.pack(pady=5)
        ctk.CTkButton(self.split_screen, text="Run Split", command=self.do_range).pack(pady=10)

        m_btns = ctk.CTkFrame(self.merge_screen, fg_color="transparent")
        m_btns.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(m_btns, text="+ Add", command=self.add_to_merge_queue, fg_color="#27ae60").pack(side="left",
                                                                                                      padx=5)
        ctk.CTkButton(m_btns, text="Merge", command=self.do_merge, fg_color="#3498db").pack(side="right", padx=5)
        self.queue_frame = ctk.CTkScrollableFrame(self.merge_screen, fg_color="#1a1a1a", height=400)
        self.queue_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.pass_ent = ctk.CTkEntry(self.lock_screen, placeholder_text="Password", show="*");
        self.pass_ent.pack(pady=10)
        ctk.CTkButton(self.lock_screen, text="Lock PDF", command=self.do_lock).pack()

    def _on_mousewheel(self, event):
        """High-speed scroll logic"""
        # units determines the distance per wheel notch. Increased by factor of 2.
        self.pdf_scroll._parent_canvas.yview_scroll(int(-2 * (event.delta / 120) * self.scroll_speed), "units")

    def create_tool_screen(self, title):
        frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        ctk.CTkLabel(frame, text=title, font=("Arial", 30, "bold")).pack(pady=10)
        return frame

    def open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = ctk.CTkToplevel(self)
            self.settings_window.title("Settings")
            self.settings_window.geometry("450x400")
            self.settings_window.attributes("-topmost", True)

            try:
                s_icon_path = os.path.join(self.icons_path, "settings.png")
                if os.path.exists(s_icon_path):
                    self.settings_icon_tk = ImageTk.PhotoImage(Image.open(s_icon_path))
                    self.settings_window.after(200,
                                               lambda: self.settings_window.wm_iconphoto(False, self.settings_icon_tk))
            except:
                pass

            ctk.CTkLabel(self.settings_window, text="⚙️ Application Settings", font=("Arial", 20, "bold")).pack(pady=20)

            self.mode_switch = ctk.CTkSwitch(self.settings_window, text="Dark Mode", command=self.toggle_mode)
            self.mode_switch.pack(pady=10)
            if ctk.get_appearance_mode() == "Dark": self.mode_switch.select()

            ctk.CTkLabel(self.settings_window, text="Scroll Speed Sensitivity").pack(pady=(20, 0))
            # Max speed bumped to 50
            self.speed_slider = ctk.CTkSlider(self.settings_window, from_=1, to=50, command=self.update_scroll_speed)
            self.speed_slider.set(self.scroll_speed)
            self.speed_slider.pack(pady=10)

            ctk.CTkButton(self.settings_window, text="Done", command=self.settings_window.destroy).pack(pady=30)
        else:
            self.settings_window.focus()

    def toggle_mode(self):
        mode = "dark" if self.mode_switch.get() else "light"
        ctk.set_appearance_mode(mode)

    def update_scroll_speed(self, value):
        self.scroll_speed = int(value)

    def switch(self, target):
        for s in [self.home_screen, self.organizer_screen, self.split_screen, self.merge_screen, self.lock_screen]:
            s.pack_forget()
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
            total = self.engine.get_info(self.current_pdf)["Pages"]
            imgs = [self.engine.get_page_image(self.current_pdf, i, 1.2) for i in range(min(total, 15))]
            self.after(0, self._update_ui, imgs)
        except:
            pass

    def _update_ui(self, imgs):
        for w in self.pdf_scroll.winfo_children(): w.destroy()
        for i, img in enumerate(imgs):
            lbl = ctk.CTkLabel(self.pdf_scroll, image=img, text="")
            lbl.image = img
            lbl.pack(pady=10)
            lbl.bind("<Button-1>", lambda e, p=i: self.load_text_to_inspector(p))
        self.load_text_to_inspector(0)

    def load_text_to_inspector(self, page_num):
        if self.current_pdf:
            text = self.engine.get_page_text(self.current_pdf, page_num)
            self.text_inspector.delete("0.0", "end")
            self.text_inspector.insert("0.0", text if text.strip() else "[No text layer found]")

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

    def add_to_merge_queue(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        for f in files:
            if f not in self.merge_queue: self.merge_queue.append(f)
        self.refresh_queue_ui()

    def refresh_queue_ui(self):
        for w in self.queue_frame.winfo_children(): w.destroy()
        for path in self.merge_queue:
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