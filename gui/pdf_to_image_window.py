import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt
from pdf2image import convert_from_path
from PIL import Image
from gui.pdf_image_editor_window import PdfImageEditorWindow

class PdfToImageConverterWindow(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.selected_files = []

        self.setStyleSheet("font-size: 14px;")
        self.resize(1200, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Конвертация PDF в изображения")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Глобальный выбор формата изображений
        format_layout = QHBoxLayout()
        format_label = QLabel("Формат изображений:")
        self.global_format_combo = QComboBox()
        self.global_format_combo.addItems(["PNG", "JPEG", "TIFF"])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.global_format_combo)
        layout.addLayout(format_layout)

        self.progress_overall = QProgressBar()
        self.progress_overall.setAlignment(Qt.AlignCenter)
        self.progress_overall.setValue(0)
        layout.addWidget(self.progress_overall)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "Файл", "DPI", "Формат", "Входной размер", "Выходной размер",
            "Редактировать", "Конвертировать", "Удалить", "Статус"
        ])
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 130)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 130)
        self.table.setColumnWidth(7, 80)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        add_button = QPushButton("Добавить PDF")
        add_button.clicked.connect(self.add_pdfs)
        button_layout.addWidget(add_button)

        delete_all_button = QPushButton("Удалить все")
        delete_all_button.clicked.connect(self.clear_all)
        button_layout.addWidget(delete_all_button)
        layout.addLayout(button_layout)

        convert_button = QPushButton("Конвертировать все")
        convert_button.clicked.connect(self.convert_all)
        layout.addWidget(convert_button)

        back_button = QPushButton("Назад")
        back_button.clicked.connect(self.back_callback)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def add_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите PDF файлы",
                                                "", "PDF файлы (*.pdf)")
        for file_path in files:
            if file_path not in self.selected_files and len(self.selected_files) < 50:
                self.selected_files.append(file_path)
                self.add_row(file_path)

    def add_row(self, file_path):
        row = self.table.rowCount()
        self.table.insertRow(row)

        file_name = os.path.basename(file_path)
        self.table.setItem(row, 0, QTableWidgetItem(file_name))

        dpi_combo = QComboBox()
        dpi_combo.addItems(["auto", "72", "96", "150", "300", "600"])
        dpi_combo.setCurrentText("auto")
        self.table.setCellWidget(row, 1, dpi_combo)

        format_combo = QComboBox()
        format_combo.addItems(["PNG", "JPEG", "TIFF"])
        format_combo.setCurrentText(self.global_format_combo.currentText())
        self.table.setCellWidget(row, 2, format_combo)

        input_size = os.path.getsize(file_path)
        self.table.setItem(row, 3, QTableWidgetItem(f"{input_size / 1024:.1f} KB"))

        self.table.setItem(row, 4, QTableWidgetItem("—"))

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(lambda _, f=file_path: self.open_editor(f))
        self.table.setCellWidget(row, 5, edit_btn)

        convert_btn = QPushButton("Конвертировать")
        convert_btn.clicked.connect(lambda _, r=row: self.convert_pdf(r))
        self.table.setCellWidget(row, 6, convert_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(lambda _, r=row: self.remove_row(r))
        self.table.setCellWidget(row, 7, delete_btn)

        progress = QProgressBar()
        progress.setValue(0)
        progress.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row, 8, progress)

    def open_editor(self, file_path):
        self.editor = PdfImageEditorWindow(file_path, self.show)
        self.hide()
        self.editor.show()

    def clear_all(self):
        self.table.setRowCount(0)
        self.selected_files.clear()
        self.progress_overall.setValue(0)

    def remove_row(self, row):
        if 0 <= row < len(self.selected_files):
            self.selected_files.pop(row)
            self.table.removeRow(row)
            self.update_progress_bar()

    def update_progress_bar(self):
        total = self.table.rowCount()
        if total == 0:
            self.progress_overall.setValue(0)
            return

        completed = 0
        for row in range(total):
            widget = self.table.cellWidget(row, 8)
            if isinstance(widget, QProgressBar) and widget.value() == 100:
                completed += 1
        self.progress_overall.setValue(int((completed / total) * 100))

    def convert_all(self):
        for row in range(self.table.rowCount()):
            self.convert_pdf(row)

    def get_folder_size_kb(self, folder):
        total = 0
        for dirpath, _, filenames in os.walk(folder):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    total += os.path.getsize(fp)
        return total // 1024

    def convert_pdf(self, row):
        if row >= len(self.selected_files):
            return

        file_path = self.selected_files[row]
        progress_bar = self.table.cellWidget(row, 8)

        dpi_combo = self.table.cellWidget(row, 1)
        dpi_value = dpi_combo.currentText()

        format_combo = self.table.cellWidget(row, 2)
        image_format = format_combo.currentText().lower()

        try:
            progress_bar.setValue(10)

            state_path = os.path.splitext(file_path)[0] + "_state.json"
            deleted_pages = set()
            rotation_angles = {}

            if os.path.exists(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    deleted_pages = set(state.get("deleted_pages", []))
                    rotation_angles = state.get("rotation_angles", {})

            dpi = None if dpi_value == "auto" else int(dpi_value)
            images = convert_from_path(file_path, dpi=dpi)

            output_folder = os.path.splitext(file_path)[0] + "_images"
            os.makedirs(output_folder, exist_ok=True)

            for i, img in enumerate(images):
                if i in deleted_pages:
                    continue

                angle = rotation_angles.get(str(i), 0)
                if angle != 0:
                    img = img.rotate(angle, expand=True)

                img.save(os.path.join(output_folder, f"page_{i + 1}.{image_format}"), image_format.upper())

            output_size_kb = self.get_folder_size_kb(output_folder)
            self.table.setItem(row, 4, QTableWidgetItem(f"{output_size_kb} КБ"))
            progress_bar.setValue(100)

        except Exception as e:
            error_label = QLabel("Ошибка: " + str(e))
            error_label.setStyleSheet("color: red;")
            self.table.setCellWidget(row, 8, error_label)
            print(f"Ошибка при конвертации PDF: {e}")

        self.update_progress_bar()
