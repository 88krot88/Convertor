import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel,
    QStackedWidget, QMenuBar, QMenu, QMessageBox, QHBoxLayout, QSizePolicy
)
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtCore import Qt, QSize

from gui.video_converter_window import VideoConverterWindow
from gui.audio_converter_window import AudioConverterWindow
from gui.image_converter_window import ImageConverterWindow
from gui.document_converter_window import DocumentConverterWindow
from gui.pdf_to_image_window import PdfToImageConverterWindow
from gui.pdf_converter_window import PdfConverterWindow
from gui.image_to_pdf_window import ImageToPdfWindow
from utils.resources import resource_path

SETTINGS_PATH = "../settings.json"


class CategoryButton(QWidget):
    def __init__(self, icon_path, text, formats, target_widget, switch_callback):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(3)

        self.button = QPushButton(text)
        self.button.setMinimumHeight(45)
        self.button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.button.setStyleSheet("""
            QPushButton {
                text-align: center;
                font-size: 14px;
                font-weight: bold;
            }
        """)

        icon_path = resource_path(icon_path)
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.button.setIcon(icon)
            self.button.setIconSize(QSize(28, 28))
        else:
            print(f"[✗] Icon not found: {icon_path}")

        self.button.clicked.connect(lambda: switch_callback(target_widget))
        layout.addWidget(self.button)

        self.label = QLabel(formats)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.label)

        self.icon_path = icon_path
        self.text = text

    def update_icon(self, icon_path):
        print(f"[DEBUG] Setting icon: {icon_path}")
        if os.path.exists(icon_path):
            self.button.setIcon(QIcon(icon_path))
        else:
            print(f"[✗] Icon not found: {icon_path}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(resource_path("icons/app_icon.ico")))
        self.setWindowTitle("CONMEL Converter")
        self.resize(600, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.stack = QStackedWidget()

        self.video_window = VideoConverterWindow(self.show_main_menu)
        self.audio_window = AudioConverterWindow(self.show_main_menu)
        self.image_window = ImageConverterWindow(self.show_main_menu)
        self.document_window = DocumentConverterWindow(self.show_main_menu)
        self.pdf_to_image_window = PdfToImageConverterWindow(self.show_main_menu)
        self.pdf_converter_window = PdfConverterWindow(self.show_main_menu)
        self.image_to_pdf_window = ImageToPdfWindow(self.show_main_menu)

        self.logo_label = QLabel()
        self.logo_label.setMinimumSize(600, 600)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.category_buttons = []

        self.init_main_menu()

        self.stack.addWidget(self.menu_widget)
        self.stack.addWidget(self.video_window)
        self.stack.addWidget(self.audio_window)
        self.stack.addWidget(self.image_window)
        self.stack.addWidget(self.document_window)
        self.stack.addWidget(self.pdf_to_image_window)
        self.stack.addWidget(self.pdf_converter_window)
        self.stack.addWidget(self.image_to_pdf_window)

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.central_widget.setLayout(layout)

        self.setMenuBar(self.create_menu_bar())
        self.load_theme()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        pixmap = self.logo_label.pixmap()
        if pixmap:
            self.logo_label.setPixmap(pixmap.scaled(
                self.logo_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def create_menu_bar(self):
        menu_bar = QMenuBar(self)

        about_menu = QMenu("Справка", self)
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about_dialog)
        about_menu.addAction(about_action)

        theme_menu = QMenu("Тема", self)
        dark_theme_action = QAction("🌙 Тёмная", self)
        light_theme_action = QAction("☀️ Светлая", self)
        dark_theme_action.triggered.connect(self.apply_dark_theme)
        light_theme_action.triggered.connect(self.apply_light_theme)
        theme_menu.addAction(dark_theme_action)
        theme_menu.addAction(light_theme_action)

        menu_bar.addMenu(about_menu)
        menu_bar.addMenu(theme_menu)

        return menu_bar

    def show_about_dialog(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("О программе")
        msg.setText(
            "CONMEL Caramel Converter\n"
            "Версия 1.0\n"
            "\nАвтор: Панишева Дарья\n"
            "Студент ТУСУР, ФВС, группа 581\n"
            "\nПринимаются пожертвования на дошик разработчику\n"
            "Сбер 2202 2050 7367 0744\n"
            "\n(c) 2025"
        )
        msg.setIcon(QMessageBox.Information)
        msg.setStyleSheet("font-size: 14px;")
        msg.exec()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                color: #f0f0f0;
                font-size: 14px;
            }
            QPushButton {
                background-color: #444;
                color: white;
                border: 1px solid #666;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QMenuBar {
                background-color: #333;
                color: white;
            }
            QMenu {
                background-color: #444;
                color: white;
            }
            QMenu::item:selected {
                background-color: #555;
            }
        """)
        self.update_logo("dark")
        self.update_button_icons("light")
        self.save_theme("dark")

    def apply_light_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: black;
                font-size: 14px;
            }
            QPushButton {
                background-color: #e0e0e0;
                color: black;
                border: 1px solid #aaa;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QMenuBar {
                background-color: #f0f0f0;
                color: black;
            }
            QMenu {
                background-color: white;
                color: black;
            }
            QMenu::item:selected {
                background-color: #e0e0e0;
            }
        """)
        self.update_logo("light")
        self.update_button_icons("dark")
        self.save_theme("light")

    def update_logo(self, theme):
        path = resource_path(f"icons/logo_{theme}.png")
        if os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.logo_label.setPixmap(pixmap.scaled(
                    self.logo_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))
            else:
                print("[✗] Pixmap is null")
        else:
            print(f"[✗] Logo not found at {path}")
            self.logo_label.clear()

    def update_button_icons(self, suffix):
        for btn, base_icon in self.category_buttons:
            icon_file = f"{base_icon}_{suffix}.png"
            icon_path = resource_path(f"icons/{icon_file}")
            print(f"[DEBUG] Loading button icon: {icon_path}")
            btn.update_icon(icon_path)

    def save_theme(self, theme_name):
        with open(SETTINGS_PATH, "w") as f:
            json.dump({"theme": theme_name}, f)

    def load_theme(self):
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r") as f:
                data = json.load(f)
                if data.get("theme") == "light":
                    self.apply_light_theme()
                else:
                    self.apply_dark_theme()
        else:
            self.apply_dark_theme()

    def init_main_menu(self):
        self.menu_widget = QWidget()
        main_layout = QHBoxLayout(self.menu_widget)

        logo_container = QVBoxLayout()
        logo_container.addStretch()
        logo_container.addWidget(self.logo_label)
        logo_container.addStretch()
        main_layout.addLayout(logo_container, 2)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(12)
        right_layout.setAlignment(Qt.AlignTop)

        label = QLabel("Выберите категорию для конвертации")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(label)

        categories = [
            ("video", "Видео", "MP4, AVI, MKV", self.video_window),
            ("audio", "Аудио", "MP3, WAV, AAC", self.audio_window),
            ("image", "Изображения", "JPG, PNG, BMP", self.image_window),
            ("document", "Документы", "DOCX, TXT, ODT", self.document_window),
            ("pdf_to_image", "PDF → Изображение", "PDF → PNG, JPG", self.pdf_to_image_window),
            ("pdf_converter", "PDF → DOCX / TXT", "PDF → DOCX, TXT", self.pdf_converter_window),
            ("image_to_pdf", "Изображения → PDF", "JPG, PNG → PDF", self.image_to_pdf_window),
        ]

        for base_name, name, formats, widget in categories:
            icon_file = f"{base_name}_light.png"  # по умолчанию загружается светлая тема
            icon_path = f"icons/{icon_file}"
            btn = CategoryButton(icon_path, name, formats, widget, self.stack.setCurrentWidget)
            right_layout.addWidget(btn)
            self.category_buttons.append((btn, base_name))  # сохраняем base_name для подстановки темы

        right_layout.addStretch()

        exit_btn = QPushButton("Выход")
        exit_btn.setMinimumHeight(45)
        exit_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        exit_btn.clicked.connect(QApplication.quit)
        right_layout.addWidget(exit_btn)

        main_layout.addLayout(right_layout, 2)

    def show_main_menu(self):
        self.stack.setCurrentWidget(self.menu_widget)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.showMaximized()
    app.exec()
