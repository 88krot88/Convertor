from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QProgressBar, QHBoxLayout, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from fpdf import FPDF
import os

from gui.image_pdf_editor_window import ImageToPdfEditorWindow


class ImageToPdfWindow(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.selected_files = []

        self.setStyleSheet("font-size: 14px;")
        self.setWindowTitle("Изображения → PDF")
        self.resize(1000, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Конвертация изображений в PDF")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        self.progress_overall = QProgressBar()
        self.progress_overall.setAlignment(Qt.AlignCenter)
        self.progress_overall.setValue(0)
        layout.addWidget(self.progress_overall)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Выбрать", "Файл", "Входной размер", "Формат", "Удалить",
            "Статус", "Конвертировать", "Редактировать"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Выбрать
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Файл (уменьшен)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)

        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()

        add_button = QPushButton("Добавить изображения")
        add_button.clicked.connect(self.add_images)
        button_layout.addWidget(add_button)

        delete_all_button = QPushButton("Удалить все")
        delete_all_button.clicked.connect(self.clear_all)
        button_layout.addWidget(delete_all_button)

        layout.addLayout(button_layout)

        convert_button = QPushButton("Конвертировать все")
        convert_button.clicked.connect(self.convert_all)
        layout.addWidget(convert_button)

        merge_button = QPushButton("Объединить выбранные в PDF")
        merge_button.clicked.connect(self.convert_selected_to_single_pdf)
        layout.addWidget(merge_button)

        back_button = QPushButton("Назад")
        back_button.clicked.connect(self.back_callback)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите изображения", "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        for file_path in files:
            if file_path not in self.selected_files and len(self.selected_files) < 50:
                self.selected_files.append(file_path)
                self.add_row(file_path)

    def add_row(self, file_path):
        row = self.table.rowCount()
        self.table.insertRow(row)

        checkbox = QCheckBox()
        self.table.setCellWidget(row, 0, checkbox)

        file_name = os.path.basename(file_path)
        self.table.setItem(row, 1, QTableWidgetItem(file_name))

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        self.table.setItem(row, 2, QTableWidgetItem(f"{file_size_mb:.2f} MB"))

        size_combo = QComboBox()
        size_combo.addItems(["A4", "A3", "A5"])
        self.table.setCellWidget(row, 3, size_combo)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(lambda _, r=row: self.remove_row(r))
        self.table.setCellWidget(row, 4, delete_btn)

        progress = QProgressBar()
        progress.setValue(0)
        progress.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row, 5, progress)

        convert_btn = QPushButton("Конвертировать")
        convert_btn.clicked.connect(lambda _, r=row: self.convert_single(r))
        self.table.setCellWidget(row, 6, convert_btn)

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(lambda _, r=row: self.open_editor(r))
        self.table.setCellWidget(row, 7, edit_btn)

    def remove_row(self, row):
        if 0 <= row < len(self.selected_files):
            self.selected_files.pop(row)
            self.table.removeRow(row)
            self.update_progress_bar()

    def clear_all(self):
        self.table.setRowCount(0)
        self.selected_files.clear()
        self.progress_overall.setValue(0)

    def update_progress_bar(self):
        total = self.table.rowCount()
        if total == 0:
            self.progress_overall.setValue(0)
            return

        completed = sum(
            1 for row in range(total)
            if isinstance(self.table.cellWidget(row, 5), QProgressBar)
            and self.table.cellWidget(row, 5).value() == 100
        )
        self.progress_overall.setValue(int((completed / total) * 100))

    def convert_single(self, row):
        if row >= len(self.selected_files):
            return

        file_path = self.selected_files[row]
        progress_bar = self.table.cellWidget(row, 5)
        size_combo = self.table.cellWidget(row, 3)
        page_format = size_combo.currentText() if size_combo else "A4"

        try:
            progress_bar.setValue(10)

            output_path = os.path.splitext(file_path)[0] + "_converted.pdf"
            pdf = FPDF(unit="pt", format=page_format)
            pdf.add_page()

            img = QPixmap(file_path)
            if img.isNull():
                raise Exception("Невозможно загрузить изображение")

            max_width = pdf.w - 60
            img_ratio = img.width() / img.height()
            height = max_width / img_ratio

            pdf.image(file_path, x=30, y=30, w=max_width, h=height)
            pdf.output(output_path)

            progress_bar.setValue(100)

        except Exception as e:
            error_label = QLabel("Ошибка: " + str(e))
            error_label.setStyleSheet("color: red;")
            self.table.setCellWidget(row, 5, error_label)
            print(f"Ошибка при конвертации: {e}")

        self.update_progress_bar()

    def convert_all(self):
        for row in range(self.table.rowCount()):
            self.convert_single(row)

    def convert_selected_to_single_pdf(self):
        selected_paths = [
            self.selected_files[row]
            for row in range(self.table.rowCount())
            if isinstance(self.table.cellWidget(row, 0), QCheckBox) and self.table.cellWidget(row, 0).isChecked()
        ]

        if not selected_paths:
            return

        editor = ImageToPdfEditorWindow(selected_paths, self.show)
        editor.show()
        self.hide()

    def open_editor(self, row):
        if row < len(self.selected_files):
            editor = ImageToPdfEditorWindow([self.selected_files[row]], self.show)
            editor.show()
            self.hide()
