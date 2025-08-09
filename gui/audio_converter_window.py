from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt
import os
import subprocess

class AudioConverterWindow(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.selected_files = []

        self.setStyleSheet("font-size: 14px;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Конвертация аудио")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        format_layout = QHBoxLayout()
        format_label = QLabel("Формат для всех:")
        self.global_format_combo = QComboBox()
        self.global_format_combo.addItems([
            "mp3 → wav", "mp3 → flac", "mp3 → ogg",
            "wav → mp3", "wav → flac", "wav → ogg",
            "flac → mp3", "flac → wav",
            "ogg → mp3", "ogg → wav"
        ])
        self.global_format_combo.currentTextChanged.connect(self.apply_global_format)
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.global_format_combo)
        layout.addLayout(format_layout)

        self.progress_overall = QProgressBar()
        self.progress_overall.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_overall.setValue(0)
        layout.addWidget(self.progress_overall)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Файл", "Исходный размер", "Конвертация", "Конвертировать", "Удалить",
            "Статус", "Выходной размер"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Файл
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Исходный размер
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Конвертация
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Конвертировать
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Удалить (делаем поуже)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Статус (расширяем)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Выходной размер

        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()

        add_button = QPushButton("Добавить аудио")
        add_button.clicked.connect(self.add_audio_files)
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

    def add_audio_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите аудио",
                                                "", "Аудио (*.mp3 *.wav *.flac *.ogg)")
        for file_path in files:
            if file_path not in self.selected_files and len(self.selected_files) < 50:
                self.selected_files.append(file_path)
                self.add_row(file_path)

    def clear_all(self):
        self.table.setRowCount(0)
        self.selected_files.clear()
        self.progress_overall.setValue(0)

    def get_available_conversions(self, ext):
        conversions = {
            '.mp3': ['mp3 → wav', 'mp3 → flac', 'mp3 → ogg'],
            '.wav': ['wav → mp3', 'wav → flac', 'wav → ogg'],
            '.flac': ['flac → mp3', 'flac → wav'],
            '.ogg': ['ogg → mp3', 'ogg → wav']
        }
        return conversions.get(ext, [])

    def add_row(self, file_path):
        row = self.table.rowCount()
        self.table.insertRow(row)

        file_name = os.path.basename(file_path)
        self.table.setItem(row, 0, QTableWidgetItem(file_name))

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        size_item = QTableWidgetItem(f"{file_size_mb:.2f} MB")
        self.table.setItem(row, 1, size_item)

        ext = os.path.splitext(file_path)[1].lower()
        combo = QComboBox()
        combo.addItems(self.get_available_conversions(ext))
        self.table.setCellWidget(row, 2, combo)

        convert_btn = QPushButton("Конвертировать")
        convert_btn.clicked.connect(lambda _, r=row: self.convert_single(r))
        self.table.setCellWidget(row, 3, convert_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(lambda _, r=row: self.remove_row(r))
        self.table.setCellWidget(row, 4, delete_btn)

        progress = QProgressBar()
        progress.setValue(0)
        progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(row, 5, progress)

        self.table.setItem(row, 6, QTableWidgetItem("—"))

    def remove_row(self, row):
        if 0 <= row < self.table.rowCount():
            file_path = self.selected_files[row]
            self.selected_files.remove(file_path)
            self.table.removeRow(row)
            self.update_progress_bar()

    def update_progress_bar(self):
        total = self.table.rowCount()
        if total == 0:
            self.progress_overall.setValue(0)
            return

        completed = 0
        for row in range(total):
            widget = self.table.cellWidget(row, 4)
            if isinstance(widget, QProgressBar) and widget.value() == 100:
                completed += 1
        self.progress_overall.setValue(int((completed / total) * 100))

    def apply_global_format(self, text):
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 2)
            if combo and combo.findText(text) != -1:
                combo.setCurrentText(text)

    def convert_single(self, row):
        if row >= len(self.selected_files):
            return

        file_path = self.selected_files[row]
        combo = self.table.cellWidget(row, 2)
        progress_bar = self.table.cellWidget(row, 4)

        try:
            selected_conversion = combo.currentText()
            progress_bar.setValue(10)

            if '→' not in selected_conversion:
                raise Exception("Неверный формат выбора")

            from_format, to_format = [s.strip().lower() for s in selected_conversion.split('→')]
            output_path = os.path.splitext(file_path)[0] + f"_converted.{to_format}"

            command = ['ffmpeg', '-y', '-i', file_path, output_path]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                raise Exception(result.stderr.decode())

            progress_bar.setValue(100)

            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                self.table.setItem(row, 5, QTableWidgetItem(f"{size_mb:.2f} MB"))

        except Exception as e:
            error_label = QLabel("Ошибка: " + str(e))
            error_label.setStyleSheet("color: red;")
            self.table.setCellWidget(row, 4, error_label)
            self.table.setItem(row, 5, QTableWidgetItem("—"))
            print(f"Ошибка при конвертации файла {file_path}: {e}")

        self.update_progress_bar()

    def convert_all(self):
        for row in range(self.table.rowCount()):
            self.convert_single(row)
