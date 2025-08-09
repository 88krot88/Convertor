from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QFileDialog, QMessageBox, QDialog
)
from PySide6.QtGui import QPixmap, QImage, QTransform
from PySide6.QtCore import Qt
from PIL import Image, ImageDraw, ImageFont
import os
import tempfile
import uuid
import docx2txt
import json

class DocumentEditorWindow(QDialog):
    def __init__(self, file_path, on_save_callback=None):
        super().__init__()
        self.file_path = file_path
        self.on_save_callback = on_save_callback
        self.setWindowTitle("Редактирование документа")
        self.resize(800, 600)

        self.temp_dir = tempfile.mkdtemp()
        self.page_images = []
        self.current_index = 0
        self.rotation_angles = {}
        self.deleted_pages = set()

        self.load_state()

        self.init_ui()
        self.load_file()
        self.load_state()
        self.update_preview()

    def init_ui(self):
        layout = QVBoxLayout()

        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.page_label)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.view)

        controls = QHBoxLayout()
        prev_btn = QPushButton("← Предыдущая")
        prev_btn.clicked.connect(self.prev_page)
        controls.addWidget(prev_btn)

        next_btn = QPushButton("Следующая →")
        next_btn.clicked.connect(self.next_page)
        controls.addWidget(next_btn)

        rotate_left_btn = QPushButton("⟲ Повернуть влево")
        rotate_left_btn.clicked.connect(self.rotate_left)
        controls.addWidget(rotate_left_btn)

        rotate_right_btn = QPushButton("⟳ Повернуть вправо")
        rotate_right_btn.clicked.connect(self.rotate_right)
        controls.addWidget(rotate_right_btn)

        delete_btn = QPushButton("🗑 Удалить страницу")
        delete_btn.clicked.connect(self.delete_page)
        controls.addWidget(delete_btn)

        layout.addLayout(controls)

        action_buttons_layout = QHBoxLayout()

        save_btn = QPushButton("Сохранить и выйти")
        save_btn.clicked.connect(self.save_and_exit)
        action_buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("↩ Выйти без сохранения")
        cancel_btn.clicked.connect(self.cancel_and_exit)
        action_buttons_layout.addWidget(cancel_btn)

        layout.addLayout(action_buttons_layout)

        self.setLayout(layout)

    def load_file(self):
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext == ".docx":
            text = docx2txt.process(self.file_path)
        elif ext in (".txt", ".md", ".rtf"):
            with open(self.file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            QMessageBox.critical(self, "Ошибка", f"Формат {ext} не поддерживается")
            return

        lines = text.splitlines()
        lines_per_page = 40
        for i in range(0, len(lines), lines_per_page):
            page_text = "\n".join(lines[i:i + lines_per_page])
            img = self.text_to_image(page_text)
            img_path = os.path.join(self.temp_dir, f"page_{uuid.uuid4().hex}.png")
            img.save(img_path)
            self.page_images.append(img_path)
            if i // lines_per_page not in self.rotation_angles:
                self.rotation_angles[i // lines_per_page] = 0

    def text_to_image(self, text, width=800, height=1000, font_size=16):
        img = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        margin = 20
        y = margin
        for line in text.splitlines():
            draw.text((margin, y), line, font=font, fill="black")
            y += font_size + 4
        return img

    def update_preview(self):
        if not self.page_images:
            return

        while self.current_index in self.deleted_pages:
            self.current_index += 1
            if self.current_index >= len(self.page_images):
                self.current_index = 0
            if self.current_index in self.deleted_pages:
                continue
            else:
                break

        image_path = self.page_images[self.current_index]
        angle = self.rotation_angles.get(self.current_index, 0)

        image = QImage(image_path)
        pixmap = QPixmap.fromImage(image)

        if angle != 0:
            transform = QTransform().rotate(angle)
            pixmap = pixmap.transformed(transform)

        self.scene.clear()
        self.scene.addPixmap(pixmap)
        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.page_label.setText(f"Страница {self.current_index + 1} из {len(self.page_images)}")

    def next_page(self):
        original_index = self.current_index
        while True:
            self.current_index = (self.current_index + 1) % len(self.page_images)
            if self.current_index not in self.deleted_pages:
                break
            if self.current_index == original_index:
                break
        self.update_preview()

    def prev_page(self):
        original_index = self.current_index
        while True:
            self.current_index = (self.current_index - 1) % len(self.page_images)
            if self.current_index not in self.deleted_pages:
                break
            if self.current_index == original_index:
                break
        self.update_preview()

    def rotate_left(self):
        self.rotation_angles[self.current_index] = (self.rotation_angles.get(self.current_index, 0) - 90) % 360
        self.update_preview()

    def rotate_right(self):
        self.rotation_angles[self.current_index] = (self.rotation_angles.get(self.current_index, 0) + 90) % 360
        self.update_preview()

    def delete_page(self):
        self.deleted_pages.add(self.current_index)
        self.next_page()

    def save_and_exit(self):
        self.save_changes()
        self.close()

    def cancel_and_exit(self):
        self.close()

    def save_changes(self):
        state = {
            "rotation_angles": self.rotation_angles,
            "deleted_pages": list(self.deleted_pages)
        }
        state_path = self.file_path + ".editstate"
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)

        QMessageBox.information(self, "Сохранено", "Изменения сохранены.")
        self.accept()

    def load_state(self):
        state_path = self.file_path + ".editstate"
        if os.path.exists(state_path):
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
                self.rotation_angles = {int(k): v for k, v in state.get("rotation_angles", {}).items()}
                self.deleted_pages = set(state.get("deleted_pages", []))
