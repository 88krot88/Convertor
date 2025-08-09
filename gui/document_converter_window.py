from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QProgressBar, QCheckBox
)
from PySide6.QtCore import Qt
import os
import pypandoc
from PIL import Image
import re
import docx
import tempfile
import subprocess
import uuid

from gui.document_editor_window import DocumentEditorWindow


class DocumentConverterWindow(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.selected_files = []

        self.setStyleSheet("font-size: 14px;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Конвертация документов")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        global_layout = QHBoxLayout()
        global_label = QLabel("Формат для всех:")
        self.global_combo = QComboBox()
        self.global_combo.addItems([
            "markdown → pdf", "markdown → docx", "markdown → odt",
            "docx → pdf", "docx → markdown", "docx → odt",
            "odt → pdf", "odt → markdown", "odt → docx",
            "markdown → html", "html → pdf", "html → docx"
        ])
        self.global_combo.currentTextChanged.connect(self.apply_global_format)
        global_layout.addWidget(global_label)
        global_layout.addWidget(self.global_combo)
        layout.addLayout(global_layout)

        self.grayscale_checkbox = QCheckBox("Конвертировать в сером цвете (для pdf)")
        layout.addWidget(self.grayscale_checkbox)

        self.progress_overall = QProgressBar()
        self.progress_overall.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_overall.setValue(0)
        layout.addWidget(self.progress_overall)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "Файл", "Исходный размер", "Конвертация", "Качество (DPI)",
            "Редактировать", "Конвертировать", "Удалить", "Статус", "Выходной размер"
        ])

        header = self.table.horizontalHeader()
        for i in range(9):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        add_button = QPushButton("Добавить документы")
        add_button.clicked.connect(self.add_documents)
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

    def add_documents(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите документы", "",
            "Документы (*.txt *.docx *.doc *.odt *.md *.html)"
        )
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
            '.txt': ['markdown → pdf', 'markdown → docx', 'markdown → odt'],
            '.docx': ['docx → pdf', 'docx → markdown', 'docx → odt'],
            '.odt': ['odt → pdf', 'odt → markdown', 'odt → docx'],
            '.md': ['markdown → pdf', 'markdown → html'],
            '.html': ['html → pdf', 'html → docx']
        }
        return conversions.get(ext, [])

    def get_pandoc_format(self, ext):
        mapping = {
            '.txt': 'markdown',
            '.md': 'markdown',
            '.docx': 'docx',
            '.odt': 'odt',
            '.html': 'html'
        }
        return mapping.get(ext, None)

    def add_row(self, file_path):
        row = self.table.rowCount()
        self.table.insertRow(row)

        file_name = os.path.basename(file_path)
        ext = os.path.splitext(file_path)[1].lower()
        self.table.setItem(row, 0, QTableWidgetItem(file_name))

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        self.table.setItem(row, 1, QTableWidgetItem(f"{file_size_mb:.2f} MB"))

        combo = QComboBox()
        combo.addItems(self.get_available_conversions(ext))
        self.table.setCellWidget(row, 2, combo)

        dpi_combo = QComboBox()
        dpi_combo.addItems(["auto", "72", "96", "150", "300", "600"])
        dpi_combo.setCurrentText("auto")
        self.table.setCellWidget(row, 3, dpi_combo)

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(lambda _, r=row: self.open_editor(r))
        self.table.setCellWidget(row, 4, edit_btn)

        convert_btn = QPushButton("Конвертировать")
        convert_btn.clicked.connect(lambda _, r=row: self.convert_single(r))
        self.table.setCellWidget(row, 5, convert_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(lambda _, r=row: self.remove_row(r))
        self.table.setCellWidget(row, 6, delete_btn)

        progress = QProgressBar()
        progress.setValue(0)
        progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(row, 7, progress)

        self.table.setItem(row, 8, QTableWidgetItem("—"))

    def open_editor(self, row):
        if row >= len(self.selected_files):
            return
        file_path = self.selected_files[row]
        editor = DocumentEditorWindow(file_path)
        editor.exec()  # Модальное окно

    def apply_global_format(self, format_text):
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 2)
            if combo and format_text in [combo.itemText(i) for i in range(combo.count())]:
                combo.setCurrentText(format_text)

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
            widget = self.table.cellWidget(row, 7)
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
        combo = self.table.cellWidget(row, 2)
        selected_conversion = combo.currentText()
        progress_bar = self.table.cellWidget(row, 7)

        try:
            progress_bar.setValue(10)
            if '→' not in selected_conversion:
                raise Exception("Неверный формат выбора")

            from_format_ui, to_format = [s.strip() for s in selected_conversion.split('→')]
            ext = os.path.splitext(file_path)[1].lower()
            from_format = self.get_pandoc_format(ext)

            if not from_format:
                raise Exception(f"Формат {ext} не поддерживается как входной.")

            ext_map = {'plain': 'txt', 'markdown': 'txt'}
            file_extension = ext_map.get(to_format, to_format)
            output_path = os.path.splitext(file_path)[0] + f"_converted.{file_extension}"

            extra_args = []
            input_path = file_path

            if to_format == 'pdf' and self.grayscale_checkbox.isChecked():
                if from_format == 'markdown':
                    input_path = self.convert_images_to_gray(file_path)
                    from_format = 'markdown'
                elif from_format == 'docx':
                    input_path = self.convert_images_to_gray_docx(file_path)
                    from_format = 'markdown'

            if to_format == 'pdf':
                extra_args.extend([
                    '--pdf-engine=xelatex',
                    '-V', 'mainfont=Arial',
                    '-V', 'lang=ru-RU',
                    '-V', 'geometry=margin=1in'
                ])

            output = pypandoc.convert_file(
                input_path, to_format, format=from_format,
                outputfile=output_path, extra_args=extra_args
            )

            if input_path != file_path and os.path.exists(input_path):
                os.remove(input_path)

            if output is None or output.strip() == "":
                progress_bar.setValue(100)
                self.update_output_size(row, output_path)
            else:
                raise Exception("Ошибка при конвертации (output не пустой)")

        except Exception as e:
            error_label = QLabel("Ошибка: " + str(e))
            error_label.setStyleSheet("color: red;")
            self.table.setCellWidget(row, 7, error_label)
            self.table.setItem(row, 8, QTableWidgetItem("—"))
            print(f"Ошибка при конвертации: {e}")

        self.update_progress_bar()

    def update_output_size(self, row, path):
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            self.table.setItem(row, 8, QTableWidgetItem(f"{size_mb:.2f} MB"))
        else:
            self.table.setItem(row, 8, QTableWidgetItem("—"))

    def convert_images_to_gray_docx(self, docx_path):
        temp_dir = tempfile.mkdtemp()
        gray_images = []
        document = docx.Document(docx_path)
        rels = document.part._rels
        for rel in rels:
            target = rels[rel].target_ref
            if "image" in target:
                image_data = rels[rel]._target.blob
                image_ext = os.path.splitext(target)[1]
                temp_img_path = os.path.join(temp_dir, str(uuid.uuid4()) + image_ext)
                with open(temp_img_path, 'wb') as f:
                    f.write(image_data)
                img = Image.open(temp_img_path).convert('L')
                gray_img_path = os.path.splitext(temp_img_path)[0] + '_gray' + image_ext
                img.save(gray_img_path)
                gray_images.append(gray_img_path)

        text = '\n'.join(p.text for p in document.paragraphs if p.text.strip())
        for img_path in gray_images:
            text += f"\n\n![]({img_path})"

        md_path = os.path.join(temp_dir, 'converted.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(text)

        return md_path

    def convert_images_to_gray(self, filepath):
        image_extensions = ['.png', '.jpg', '.jpeg']
        dir_path = os.path.dirname(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        def replace_image(match):
            img_path = match.group(1)
            full_path = os.path.join(dir_path, img_path)
            if os.path.isfile(full_path) and os.path.splitext(full_path)[1].lower() in image_extensions:
                img = Image.open(full_path).convert('L')
                gray_path = os.path.splitext(full_path)[0] + '_gray' + os.path.splitext(full_path)[1]
                img.save(gray_path)
                return f"![]({os.path.basename(gray_path)})"
            return match.group(0)

        content = re.sub(r'!\[[^\]]*\]\(([^\)]+)\)', replace_image, content)

        gray_md_path = os.path.splitext(filepath)[0] + '_gray_temp.md'
        with open(gray_md_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return gray_md_path
