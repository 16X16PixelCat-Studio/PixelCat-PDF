import sys
import os
import ctypes
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QScrollArea,
                             QFileDialog, QFrame, QStackedWidget, QLineEdit,
                             QListWidget, QMessageBox, QSlider, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPalette, QColor, QIcon
from pixelcat_engine import PixelCatEngine

# Fix the Taskbar Icon for Windows
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('pixelcat.pdf.v0.4.1')
except:
    pass


class RenderThread(QThread):
    """Worker thread to render pages without freezing the UI."""
    page_rendered = pyqtSignal(int, object)
    finished = pyqtSignal()

    def __init__(self, engine, path, total_pages, zoom):
        super().__init__()
        self.engine, self.path, self.total_pages, self.zoom = engine, path, total_pages, zoom

    def run(self):
        for i in range(self.total_pages):
            pix = self.engine.get_page_pixmap(self.path, i, zoom=self.zoom)
            if pix:
                self.page_rendered.emit(i, pix)
        self.finished.emit()


class PixelCatPDF(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = PixelCatEngine()
        self.current_pdf = None
        self.nav_buttons = []
        self.range_rows = []
        self.merge_queue = []

        # Path logic for icons (Works for script and .exe)
        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        self.icons_path = os.path.join(self.base_path, "icons")
        icon_file = os.path.join(self.icons_path, "PixelCat-PDF.ico")

        self.setWindowTitle("PixelCat-PDF v0.4.1")
        self.resize(1100, 850)
        if os.path.exists(icon_file):
            self.setWindowIcon(QIcon(icon_file))

        self.set_dark_theme()
        self.setup_ui()
        self.set_active_button(0)

    def set_dark_theme(self):
        app = QApplication.instance()
        app.setStyle("Fusion")
        p = QPalette()
        p.setColor(QPalette.ColorRole.Window, QColor(25, 25, 25))
        p.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        p.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        p.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
        app.setPalette(p)

    def setup_ui(self):
        central = QWidget();
        self.setCentralWidget(central)
        layout = QHBoxLayout(central);
        layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = QFrame();
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("background-color: #1e1e1e; border-right: 1px solid #333;")
        side_lay = QVBoxLayout(self.sidebar)

        title = QLabel("PIXELCAT");
        title.setStyleSheet("color: #3498db; font-size: 18px; font-weight: bold; margin: 15px;")
        side_lay.addWidget(title)

        btn_open = QPushButton(" Open PDF");
        btn_open.setFixedHeight(40)
        btn_open.setStyleSheet("background-color: #3498db; font-weight: bold;")
        btn_open.clicked.connect(self.open_file);
        side_lay.addWidget(btn_open)

        menus = [("Viewer", 0), ("Splitter", 1), ("Merger", 2), ("Security", 3), ("Settings", 4)]
        for name, idx in menus:
            btn = QPushButton(f" {name}");
            btn.setProperty("idx", idx);
            btn.setFixedHeight(40)
            btn.clicked.connect(lambda ch, i=idx: self.set_active_button(i))
            side_lay.addWidget(btn);
            self.nav_buttons.append(btn)

        side_lay.addStretch()

        # Sidebar Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 1px solid #444; border-radius: 3px; text-align: center; height: 15px; } QProgressBar::chunk { background-color: #3498db; }")
        self.progress_bar.setVisible(False)
        side_lay.addWidget(self.progress_bar)

        self.stack = QStackedWidget()
        layout.addWidget(self.sidebar);
        layout.addWidget(self.stack)

        self.setup_viewer();
        self.setup_splitter();
        self.setup_merger();
        self.setup_security();
        self.setup_settings()

    def set_active_button(self, index):
        self.stack.setCurrentIndex(index)
        for btn in self.nav_buttons:
            btn.setStyleSheet("background-color: #3498db; font-weight: bold;" if btn.property(
                "idx") == index else "background-color: transparent;")

    def setup_viewer(self):
        page = QWidget();
        l = QVBoxLayout(page)
        self.v_scroll = QScrollArea()
        self.v_container = QWidget();
        self.v_lay = QVBoxLayout(self.v_container)
        self.v_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_scroll.setWidget(self.v_container);
        self.v_scroll.setWidgetResizable(True)
        l.addWidget(self.v_scroll);
        self.stack.addWidget(page)

    def open_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF (*.pdf)")
        if f:
            self.current_pdf = f
            while self.v_lay.count():
                item = self.v_lay.takeAt(0);
                w = item.widget()
                if w: w.deleteLater()

            info = self.engine.get_info(f)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(info["Pages"])
            self.progress_bar.setValue(0)

            self.rt = RenderThread(self.engine, f, info["Pages"], 0.8)
            self.rt.page_rendered.connect(self.add_viewer_page)
            self.rt.finished.connect(lambda: self.progress_bar.setVisible(False))
            self.rt.start()

    def add_viewer_page(self, i, pix):
        lbl = QLabel()
        lbl.setPixmap(pix.scaledToWidth(800, Qt.TransformationMode.SmoothTransformation))
        lbl.setStyleSheet("margin-bottom: 20px; border: 1px solid #444;")
        self.v_lay.addWidget(lbl)
        self.progress_bar.setValue(i + 1)

    def setup_splitter(self):
        page = QWidget();
        main_lay = QVBoxLayout(page);
        main_lay.setContentsMargins(30, 30, 30, 30)
        self.split_scroll = QScrollArea()
        self.split_container = QWidget();
        self.rows_layout = QVBoxLayout(self.split_container)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.split_scroll.setWidget(self.split_container);
        self.split_scroll.setWidgetResizable(True)
        main_lay.addWidget(QLabel("<h2>Multi-Splitter</h2>"))
        main_lay.addWidget(self.split_scroll)
        btn_add = QPushButton("+ Add Range Row");
        btn_add.setFixedHeight(40)
        btn_add.clicked.connect(self.add_range_row)
        btn_run = QPushButton("RUN ALL SPLITS");
        btn_run.setFixedHeight(40)
        btn_run.setStyleSheet("background-color: #e67e22; font-weight: bold;")
        btn_run.clicked.connect(self.run_multi_split)
        main_lay.addWidget(btn_add);
        main_lay.addWidget(btn_run)
        self.stack.addWidget(page);
        self.add_range_row()

    def add_range_row(self):
        f = QFrame();
        f.setStyleSheet("background-color: #2a2a2a; border-radius: 5px;");
        l = QHBoxLayout(f)
        s = QLineEdit();
        s.setPlaceholderText("Start");
        e = QLineEdit();
        e.setPlaceholderText("End")
        d = QPushButton("X");
        d.setFixedWidth(30);
        d.clicked.connect(lambda: f.deleteLater())
        l.addWidget(QLabel(f"File {len(self.range_rows) + 1}:"));
        l.addWidget(s);
        l.addWidget(QLabel("-"));
        l.addWidget(e);
        l.addWidget(d)
        self.rows_layout.addWidget(f);
        self.range_rows.append({"frame": f, "start": s, "end": e})

    def run_multi_split(self):
        if not self.current_pdf: return
        out_dir = QFileDialog.getExistingDirectory(self, "Select Folder")
        if out_dir:
            active_rows = [r for r in self.range_rows if r["frame"].isVisible()]
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(len(active_rows))

            for i, r in enumerate(active_rows):
                try:
                    self.engine.extract_pages(self.current_pdf, int(r["start"].text()) - 1, int(r["end"].text()) - 1,
                                              os.path.join(out_dir, f"Part_{i + 1}.pdf"))
                    self.progress_bar.setValue(i + 1)
                except:
                    continue
            self.progress_bar.setVisible(False)
            QMessageBox.information(self, "Success", "All ranges extracted!")

    def setup_merger(self):
        page = QWidget();
        lay = QVBoxLayout(page);
        lay.setContentsMargins(30, 30, 30, 30)
        self.mlist = QListWidget();
        lay.addWidget(self.mlist)
        b_add = QPushButton("Add PDF");
        b_add.clicked.connect(self.add_to_merge_list)
        b_run = QPushButton("Merge All");
        b_run.setStyleSheet("background-color: #27ae60; font-weight: bold;")
        b_run.clicked.connect(self.run_merger)
        lay.addWidget(b_add);
        lay.addWidget(b_run);
        self.stack.addWidget(page)

    def add_to_merge_list(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Add PDFs", "", "PDF (*.pdf)")
        for f in files:
            self.merge_queue.append(f)
            self.mlist.addItem(os.path.basename(f))

    def run_merger(self):
        if len(self.merge_queue) < 2: return
        out, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", "", "PDF (*.pdf)")
        if out: self.engine.merge_pdfs(self.merge_queue, out); QMessageBox.information(self, "Done", "Merged.")

    def setup_security(self):
        page = QWidget();
        lay = QVBoxLayout(page);
        lay.setContentsMargins(40, 40, 40, 40)
        lay.addWidget(QLabel("<h2>Security</h2>"))
        self.pw_input = QLineEdit();
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addWidget(self.pw_input)
        btn_lock = QPushButton("Save Encrypted PDF");
        btn_lock.setStyleSheet("background-color: #c0392b; font-weight: bold; height: 40px;")
        btn_lock.clicked.connect(self.run_security);
        lay.addWidget(btn_lock);
        lay.addStretch();
        self.stack.addWidget(page)

    def run_security(self):
        if not self.current_pdf or not self.pw_input.text(): return
        out, _ = QFileDialog.getSaveFileName(self, "Save", "", "PDF (*.pdf)")
        if out: self.engine.set_password(self.current_pdf, out, self.pw_input.text())

    def setup_settings(self):
        page = QWidget();
        lay = QVBoxLayout(page);
        lay.setContentsMargins(40, 40, 40, 40)
        lay.addWidget(QLabel("<h2>Settings</h2>"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal);
        self.zoom_slider.setRange(50, 150)
        lay.addWidget(QLabel("Viewer Zoom:"));
        lay.addWidget(self.zoom_slider);
        lay.addStretch();
        self.stack.addWidget(page)


if __name__ == "__main__":
    app = QApplication(sys.argv);
    window = PixelCatPDF();
    window.show();
    sys.exit(app.exec())