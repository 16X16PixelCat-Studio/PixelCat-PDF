import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QScrollArea,
                             QTextEdit, QFileDialog, QFrame, QSplitter,
                             QStackedWidget, QDialog, QGridLayout, QSlider, QLineEdit, QListWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QPixmap, QPalette, QColor, QIcon, QFont
from pixelcat_engine import PixelCatEngine

# Official Branding
APP_NAME = "PixelCat-PDF-V0.4.0-ALPHA"


class RenderThread(QThread):
    page_rendered = pyqtSignal(int, object)

    def __init__(self, engine, path, total_pages, zoom):
        super().__init__()
        self.engine, self.path, self.total_pages, self.zoom = engine, path, total_pages, zoom

    def run(self):
        for i in range(self.total_pages):
            pix = self.engine.get_page_pixmap(self.path, i, zoom=self.zoom)
            self.page_rendered.emit(i, pix)


class PixelCatPDF(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = PixelCatEngine()
        self.settings_manager = QSettings("PixelCat", "PDF-App")
        self.current_pdf = None
        self.nav_buttons = []
        self.merge_files = []

        # PyInstaller Compatibility Logic
        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        self.icons_path = os.path.join(self.base_path, "icons")
        self.zoom_level = float(self.settings_manager.value("zoom", 0.8))

        self.setWindowTitle(APP_NAME)
        self.resize(1200, 850)

        # Icon Logic
        self.main_icon = self.get_icon("PixelCat-PDF.png")
        self.setWindowIcon(self.main_icon)

        self.set_dark_theme()
        self.setup_ui()
        self.set_active_button(0)

    def set_dark_theme(self):
        app = QApplication.instance()
        app.setStyle("Fusion")
        app.setFont(QFont("Segoe UI", 10))
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(18, 18, 18))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        app.setPalette(palette)

    def get_icon(self, name):
        path = os.path.join(self.icons_path, name)
        return QIcon(path) if os.path.exists(path) else QIcon()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QHBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar Area
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("background-color: #252525; border-right: 1px solid #333;")
        side_layout = QVBoxLayout(self.sidebar)

        title = QLabel("PixelCat")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #3498db; margin: 10px;")
        side_layout.addWidget(title)

        btn_open = QPushButton(" Open PDF")
        btn_open.setIcon(self.get_icon("open.png"))
        btn_open.setFixedHeight(45)
        btn_open.setStyleSheet("background-color: #3498db; font-weight: bold; border-radius: 5px;")
        btn_open.clicked.connect(self.open_file)
        side_layout.addWidget(btn_open)

        nav_items = [
            ("Viewer", 0, "view.png"),
            ("Organizer", 1, "org.png"),
            ("Splitter", 2, "split.png"),
            ("Merger", 3, "merge.png"),
            ("Security", 4, "lock.png")
        ]

        for name, idx, icon_name in nav_items:
            btn = QPushButton(f" {name}")
            btn.setIcon(self.get_icon(icon_name))
            btn.setFixedHeight(45)
            btn.setProperty("idx", idx)
            btn.clicked.connect(lambda checked, i=idx: self.set_active_button(i))
            side_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        side_layout.addStretch()

        btn_settings = QPushButton(" Settings")
        btn_settings.setIcon(self.get_icon("settings.png"))
        btn_settings.setFixedHeight(45)
        btn_settings.setStyleSheet("text-align: left; padding-left: 10px; border: none; background: transparent;")
        btn_settings.clicked.connect(self.open_settings)
        side_layout.addWidget(btn_settings)

        self.main_layout.addWidget(self.sidebar)

        # Content Stack
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self.setup_viewer_screen()  # 0
        self.setup_organizer_screen()  # 1
        self.setup_splitter_screen()  # 2
        self.setup_merger_screen()  # 3
        self.setup_security_screen()  # 4

    def set_active_button(self, index):
        self.stack.setCurrentIndex(index)
        active = "text-align: left; padding-left: 10px; border: none; background-color: #3498db; border-radius: 4px; font-weight: bold;"
        idle = "text-align: left; padding-left: 10px; border: none; background-color: transparent;"
        for btn in self.nav_buttons:
            btn.setStyleSheet(active if btn.property("idx") == index else idle)

    def setup_viewer_screen(self):
        page = QWidget();
        lay = QHBoxLayout(page)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget();
        self.viewer_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget);
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #121212; border: none;")
        self.inspector = QTextEdit();
        self.inspector.setReadOnly(True)
        self.inspector.setFont(QFont("Consolas", 11))
        self.splitter.addWidget(self.scroll_area);
        self.splitter.addWidget(self.inspector)
        self.splitter.setSizes([850, 350])
        lay.addWidget(self.splitter)
        self.stack.addWidget(page)

    def setup_organizer_screen(self):
        page = QWidget();
        lay = QVBoxLayout(page)
        self.org_scroll = QScrollArea()
        self.org_content = QWidget();
        self.org_grid = QGridLayout(self.org_content)
        self.org_grid.setSpacing(20)
        self.org_scroll.setWidget(self.org_content);
        self.org_scroll.setWidgetResizable(True)
        self.org_scroll.setStyleSheet("background-color: #121212; border: none;")
        lay.addWidget(self.org_scroll)
        self.stack.addWidget(page)

    def setup_splitter_screen(self):
        page = QWidget();
        lay = QVBoxLayout(page);
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(QLabel("Split PDF by Range"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.split_start = QLineEdit();
        self.split_start.setPlaceholderText("Start Page");
        self.split_start.setFixedWidth(200)
        self.split_end = QLineEdit();
        self.split_end.setPlaceholderText("End Page");
        self.split_end.setFixedWidth(200)
        btn = QPushButton("Extract Pages");
        btn.setFixedWidth(200);
        btn.setStyleSheet("background-color: #3498db;")
        lay.addWidget(self.split_start);
        lay.addWidget(self.split_end);
        lay.addWidget(btn)
        self.stack.addWidget(page)

    def setup_merger_screen(self):
        page = QWidget();
        lay = QVBoxLayout(page)
        self.merge_list = QListWidget()
        btn_add = QPushButton("Add PDF to Merge")
        btn_add.clicked.connect(self.add_merge_file)
        btn_run = QPushButton("Merge Files")
        btn_run.setStyleSheet("background-color: #27ae60;")
        lay.addWidget(QLabel("Merge Queue:"))
        lay.addWidget(self.merge_list);
        lay.addWidget(btn_add);
        lay.addWidget(btn_run)
        self.stack.addWidget(page)

    def setup_security_screen(self):
        page = QWidget();
        lay = QVBoxLayout(page);
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(QLabel("Password Protection"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.pass_in = QLineEdit();
        self.pass_in.setPlaceholderText("Enter Password");
        self.pass_in.setEchoMode(QLineEdit.EchoMode.Password);
        self.pass_in.setFixedWidth(250)
        btn = QPushButton("Encrypt PDF");
        btn.setFixedWidth(250);
        btn.setStyleSheet("background-color: #e74c3c;")
        lay.addWidget(self.pass_in);
        lay.addWidget(btn)
        self.stack.addWidget(page)

    def add_merge_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if f:
            self.merge_files.append(f)
            self.merge_list.addItem(os.path.basename(f))

    def open_file(self, auto_path=None):
        path = auto_path if auto_path else QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")[0]
        if path:
            self.current_pdf = path
            for i in reversed(range(self.viewer_layout.count())):
                if self.viewer_layout.itemAt(i).widget(): self.viewer_layout.itemAt(i).widget().setParent(None)
            for i in reversed(range(self.org_grid.count())):
                if self.org_grid.itemAt(i).widget(): self.org_grid.itemAt(i).widget().setParent(None)

            pages = self.engine.get_info(path)["Pages"]
            self.render_thread = RenderThread(self.engine, path, pages, self.zoom_level)
            self.render_thread.page_rendered.connect(self.add_page_to_ui)
            self.render_thread.start()
            self.set_active_button(0)

    def add_page_to_ui(self, index, pixmap):
        v_lbl = QLabel()
        v_lbl.setPixmap(pixmap.scaledToWidth(800, Qt.TransformationMode.SmoothTransformation))
        v_lbl.mousePressEvent = lambda e, p=index: self.show_text(p)
        self.viewer_layout.addWidget(v_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        t_frame = QFrame();
        t_lay = QVBoxLayout(t_frame)
        t_lbl = QLabel();
        t_lbl.setPixmap(
            pixmap.scaled(180, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        t_lbl.setStyleSheet("border: 2px solid #333; border-radius: 5px;")
        t_lay.addWidget(t_lbl);
        t_lay.addWidget(QLabel(f"Page {index + 1}"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.org_grid.addWidget(t_frame, divmod(index, 4)[0], divmod(index, 4)[1])

    def show_text(self, page_num):
        text = self.engine.get_page_text(self.current_pdf, page_num)
        self.inspector.setText(text if text.strip() else "[No Text Layer]")

    def open_settings(self):
        dialog = QDialog(self);
        dialog.setWindowTitle("Settings");
        dialog.setWindowIcon(self.get_icon("settings.png"))
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Zoom Quality"))
        slider = QSlider(Qt.Orientation.Horizontal);
        slider.setRange(5, 20);
        slider.setValue(int(self.zoom_level * 10))
        layout.addWidget(slider)
        btn = QPushButton("Apply");
        btn.clicked.connect(lambda: self.save_prefs(slider.value() / 10, dialog))
        layout.addWidget(btn);
        dialog.exec()

    def save_prefs(self, zoom, dialog):
        self.zoom_level = zoom
        self.settings_manager.setValue("zoom", zoom)
        dialog.accept()
        if self.current_pdf: self.open_file(auto_path=self.current_pdf)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PixelCatPDF()
    window.show()
    sys.exit(app.exec())