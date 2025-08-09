from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QProgressBar
)
from PySide6.QtCore import Qt
import os
import subprocess


class VideoConverterWindow(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.selected_files = []

        self.setStyleSheet("font-size: 14px;")
        self.setWindowTitle("Конвертация видео")
        self.resize(1050, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Конвертация видео")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Выбор формата
        format_layout = QHBoxLayout()
        format_label = QLabel("Выходной формат:")
        self.global_format_combo = QComboBox()
        self.global_format_combo.addItems(["mp4", "avi", "mkv", "mov"])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.global_format_combo)
        layout.addLayout(format_layout)

        # Общий прогресс
        self.progress_overall = QProgressBar()
        self.progress_overall.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_overall.setValue(0)
        layout.addWidget(self.progress_overall)

        # Таблица
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Файл", "Формат", "Входной размер", "Выходной размер",
            "Удалить", "Конвертировать", "Статус"
        ])
        self.table.setColumnWidth(0, 220)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 130)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 130)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Кнопки
        button_layout = QHBoxLayout()
        add_button = QPushButton("Добавить видео")
        add_button.clicked.connect(self.add_video_files)
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

    def add_video_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите видео",
                                                "", "Видео (*.mp4 *.avi *.mkv *.mov)")
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

        # Формат
        ext = os.path.splitext(file_path)[1].lower().replace(".", "")
        target_format = self.global_format_combo.currentText()
        combo_text = f"{ext} → {target_format}" if ext != target_format else f"{ext} → {ext}"

        format_combo = QComboBox()
        format_combo.addItem(combo_text)
        self.table.setCellWidget(row, 1, format_combo)

        # Входной размер
        input_size = os.path.getsize(file_path)
        self.table.setItem(row, 2, QTableWidgetItem(f"{input_size / 1024 / 1024:.2f} MB"))

        # Заглушка для выходного размера
        self.table.setItem(row, 3, QTableWidgetItem("—"))

        # Удалить
        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(lambda _, r=row: self.remove_row(r))
        self.table.setCellWidget(row, 4, delete_btn)

        # Конвертировать
        convert_btn = QPushButton("Конвертировать")
        convert_btn.clicked.connect(lambda _, r=row: self.convert_single(r))
        self.table.setCellWidget(row, 5, convert_btn)

        # Прогресс
        progress = QProgressBar()
        progress.setValue(0)
        progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(row, 6, progress)

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
            widget = self.table.cellWidget(row, 6)
            if isinstance(widget, QProgressBar) and widget.value() == 100:
                completed += 1
        self.progress_overall.setValue(int((completed / total) * 100))

    def convert_all(self):
        for row in range(self.table.rowCount()):
            self.convert_single(row)

    def convert_single(self, row):
        if row >= len(self.selected_files):
            return

        file_path = self.selected_files[row]
        combo = self.table.cellWidget(row, 1)
        selected_conversion = combo.currentText()
        progress_bar = self.table.cellWidget(row, 6)

        try:
            progress_bar.setValue(10)
            if '→' not in selected_conversion:
                raise Exception("Неверный формат выбора")

            from_format, to_format = [s.strip().lower() for s in selected_conversion.split('→')]
            output_path = os.path.splitext(file_path)[0] + f"_converted.{to_format}"

            command = ['ffmpeg', '-y', '-i', file_path, output_path]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if result.returncode != 0:
                raise Exception(result.stderr.decode())

            # Записываем выходной размер
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path)
                self.table.setItem(row, 3, QTableWidgetItem(f"{output_size / 1024 / 1024:.2f} MB"))

            progress_bar.setValue(100)

        except Exception as e:
            from PySide6.QtWidgets import QLabel
            error_label = QLabel("Ошибка: " + str(e))
            error_label.setStyleSheet("color: red;")
            self.table.setCellWidget(row, 6, error_label)
            print(f"Ошибка при конвертации: {e}")

        self.update_progress_bar()

