from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QProgressBar, QComboBox
)
from PySide6.QtCore import Qt
import os
from pdf2docx import Converter as DocxConverter
import pdfplumber


class PdfConverterWindow(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.selected_files = []

        self.setStyleSheet("font-size: 14px;")
        self.setWindowTitle("PDF → DOCX / TXT")
        self.resize(1100, 600)  # немного шире
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Конвертация PDF в DOCX / TXT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        format_layout = QHBoxLayout()
        format_label = QLabel("Формат для всех:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(['docx', 'txt'])
        self.format_combo.currentTextChanged.connect(self.set_all_formats)
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)

        self.progress_overall = QProgressBar()
        self.progress_overall.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_overall.setValue(0)
        layout.addWidget(self.progress_overall)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Файл", "Формат", "Входной размер", "Выходной размер",
            "Удалить", "Статус", "Конвертировать"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()

        add_button = QPushButton("Добавить PDF")
        add_button.clicked.connect(self.add_pdf_files)
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

    def set_all_formats(self, selected_format):
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 1)
            if isinstance(combo, QComboBox):
                combo.setCurrentText(selected_format)

    def add_pdf_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите PDF-файлы", "",
                                                "PDF-файлы (*.pdf)")
        for file_path in files:
            if file_path not in self.selected_files and len(self.selected_files) < 50:
                self.selected_files.append(file_path)
                self.add_row(file_path)

    def clear_all(self):
        self.table.setRowCount(0)
        self.selected_files.clear()
        self.progress_overall.setValue(0)

    def add_row(self, file_path):
        row = self.table.rowCount()
        self.table.insertRow(row)

        file_name = os.path.basename(file_path)
        self.table.setItem(row, 0, QTableWidgetItem(file_name))

        combo = QComboBox()
        combo.addItems(['docx', 'txt'])
        combo.setCurrentText(self.format_combo.currentText())
        self.table.setCellWidget(row, 1, combo)

        input_size_kb = os.path.getsize(file_path) // 1024
        self.table.setItem(row, 2, QTableWidgetItem(f"{input_size_kb} КБ"))
        self.table.setItem(row, 3, QTableWidgetItem("—"))

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(lambda _, r=row: self.remove_row(r))
        self.table.setCellWidget(row, 4, delete_btn)

        progress = QProgressBar()
        progress.setValue(0)
        progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(row, 5, progress)

        convert_btn = QPushButton("Конвертировать")
        convert_btn.clicked.connect(lambda _, r=row: self.convert_single(r))
        self.table.setCellWidget(row, 6, convert_btn)

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
            widget = self.table.cellWidget(row, 5)
            if isinstance(widget, QProgressBar) and widget.value() == 100:
                completed += 1
        self.progress_overall.setValue(int((completed / total) * 100))

    def convert_single(self, row):
        if row >= len(self.selected_files):
            return

        file_path = self.selected_files[row]
        combo = self.table.cellWidget(row, 1)
        to_format = combo.currentText().lower()
        progress_bar = self.table.cellWidget(row, 5)

        try:
            progress_bar.setValue(10)

            output_path = os.path.splitext(file_path)[0] + f"_converted.{to_format}"

            if to_format == "docx":
                converter = DocxConverter(file_path)
                converter.convert(output_path, start=0, end=None)
                converter.close()
            elif to_format == "txt":
                with pdfplumber.open(file_path) as pdf:
                    text = "\n".join(page.extract_text() or '' for page in pdf.pages)
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(text)

            progress_bar.setValue(100)

            if os.path.exists(output_path):
                output_size_kb = os.path.getsize(output_path) // 1024
                self.table.setItem(row, 3, QTableWidgetItem(f"{output_size_kb} КБ"))

            print(f"Успешно сконвертировано: {output_path}")

        except Exception as e:
            error_label = QLabel("Ошибка: " + str(e))
            error_label.setStyleSheet("color: red;")
            self.table.setCellWidget(row, 5, error_label)
            print(f"Ошибка при конвертации: {e}")

        self.update_progress_bar()

    def convert_all(self):
        for row in range(self.table.rowCount()):
            self.convert_single(row)
