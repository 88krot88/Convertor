from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QProgressBar
)
from PySide6.QtCore import Qt
from PIL import Image
import os


class ImageConverterWindow(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.selected_files = []

        self.setStyleSheet("font-size: 14px;")
        self.setWindowTitle("Конвертация изображений")
        self.resize(950, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Конвертация изображений")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Глобальный выбор формата для всех изображений
        global_layout = QHBoxLayout()
        global_label = QLabel("Формат для всех:")
        self.global_combo = QComboBox()
        self.global_combo.addItems([
            "png → jpeg", "png → bmp", "png → tiff", "png → webp",
            "jpeg → png", "jpeg → bmp", "jpeg → tiff", "jpeg → webp",
            "bmp → jpeg", "bmp → png", "bmp → tiff", "bmp → webp",
            "tiff → jpeg", "tiff → png", "tiff → bmp", "tiff → webp",
            "webp → jpeg", "webp → png", "webp → bmp", "webp → tiff"
        ])
        self.global_combo.currentTextChanged.connect(self.apply_global_format)
        global_layout.addWidget(global_label)
        global_layout.addWidget(self.global_combo)
        layout.addLayout(global_layout)

        # Общий прогресс
        self.progress_overall = QProgressBar()
        self.progress_overall.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_overall.setValue(0)
        layout.addWidget(self.progress_overall)

        # Таблица
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Файл", "Формат", "Удалить", "Конвертировать", "Статус", "Входной размер", "Выходной размер"
        ])
        self.table.setColumnWidth(0, 220)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 130)
        self.table.setColumnWidth(5, 130)
        self.table.setColumnWidth(6, 130)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Кнопки
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

        back_button = QPushButton("Назад")
        back_button.clicked.connect(self.back_callback)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите изображения",
                                                "", "Изображения (*.png *.jpg "
                                                    "*.jpeg *.bmp *.tiff *.webp)")
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
        target_format = self.global_combo.currentText()
        combo_text = f"{ext} → {target_format}" if ext != target_format else f"{ext} → {ext}"

        format_combo = QComboBox()
        format_combo.addItem(combo_text)
        self.table.setCellWidget(row, 1, format_combo)

        # Удалить
        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(lambda _, r=row: self.remove_row(r))
        self.table.setCellWidget(row, 2, delete_btn)

        # Конвертировать
        convert_btn = QPushButton("Конвертировать")
        convert_btn.clicked.connect(lambda _, r=row: self.convert_single(r))
        self.table.setCellWidget(row, 3, convert_btn)

        # Статус
        progress = QProgressBar()
        progress.setValue(0)
        progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(row, 4, progress)

        # Входной размер
        if os.path.exists(file_path):
            input_size = os.path.getsize(file_path)
            self.table.setItem(row, 5, QTableWidgetItem(f"{input_size / 1024:.1f} KB"))
        else:
            self.table.setItem(row, 5, QTableWidgetItem("—"))

        # Выходной размер (заполнится после конвертации)
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

    def convert_all(self):
        for row in range(self.table.rowCount()):
            self.convert_single(row)

    def convert_single(self, row):
        if row >= len(self.selected_files):
            return

        file_path = self.selected_files[row]
        combo = self.table.cellWidget(row, 1)
        selected_conversion = combo.currentText()
        progress_bar = self.table.cellWidget(row, 4)

        try:
            progress_bar.setValue(10)
            if '→' not in selected_conversion:
                raise Exception("Неверный формат выбора")

            from_format, to_format = [s.strip().lower() for s in selected_conversion.split('→')]
            output_path = os.path.splitext(file_path)[0] + f"_converted.{to_format}"

            image = Image.open(file_path)
            image = image.convert("RGB") if to_format in ["jpeg", "jpg"] else image
            format_map = {
                "jpg": "JPEG",
                "jpeg": "JPEG",
                "png": "PNG",
                "bmp": "BMP",
                "tiff": "TIFF",
                "webp": "WEBP"
            }
            image_format = format_map.get(to_format.lower(), to_format.upper())
            image.save(output_path, format=image_format)

            # Получить размер
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path)
                self.table.setItem(row, 6, QTableWidgetItem(f"{output_size / 1024:.1f} KB"))

            progress_bar.setValue(100)

        except Exception as e:
            from PySide6.QtWidgets import QLabel
            error_label = QLabel("Ошибка: " + str(e))
            error_label.setStyleSheet("color: red;")
            self.table.setCellWidget(row, 4, error_label)
            print(f"Ошибка при конвертации изображения: {e}")

        self.update_progress_bar()

    def apply_global_format(self, conversion_text):
        try:
            _, to_format = [s.strip().lower() for s in conversion_text.split("→")]
        except ValueError:
            return

        for row in range(self.table.rowCount()):
            file_path = self.selected_files[row]
            ext = os.path.splitext(file_path)[1].lower().replace(".", "")
            combo = self.table.cellWidget(row, 1)
            if combo:
                combo.clear()
                if ext != to_format:
                    combo.addItem(f"{ext} → {to_format}")
                else:
                    combo.addItem(f"{ext} → {ext}")

