import os
import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QMessageBox
)
from PySide6.QtGui import QPixmap, QImage, QTransform
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from pdf2image import convert_from_path
from PIL import ImageQt


class PdfImageEditorWindow(QDialog):
    def __init__(self, pdf_path, back_callback=None):
        super().__init__()
        self.pdf_path = pdf_path
        self.back_callback = back_callback

        self.setWindowTitle("Редактирование PDF перед конвертацией")
        self.resize(800, 600)

        self.all_images = []
        self.page_indices = []
        self.current_index = 0
        self.deleted_pages = set()
        self.rotation_angles = {}

        self.load_state()
        self.load_images()

        self.init_ui()
        self.update_preview()

    def init_ui(self):
        layout = QVBoxLayout()

        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.page_label)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.view)

        nav_layout = QHBoxLayout()
        prev_btn = QPushButton("← Предыдущая")
        prev_btn.clicked.connect(self.prev_page)
        nav_layout.addWidget(prev_btn)

        next_btn = QPushButton("Следующая →")
        next_btn.clicked.connect(self.next_page)
        nav_layout.addWidget(next_btn)

        layout.addLayout(nav_layout)

        action_layout = QHBoxLayout()

        rotate_left_btn = QPushButton("⟲ Повернуть влево")
        rotate_left_btn.clicked.connect(self.rotate_left)
        action_layout.addWidget(rotate_left_btn)

        rotate_right_btn = QPushButton("⟳ Повернуть вправо")
        rotate_right_btn.clicked.connect(self.rotate_right)
        action_layout.addWidget(rotate_right_btn)

        delete_btn = QPushButton("🗑 Удалить страницу")
        delete_btn.clicked.connect(self.delete_page)
        action_layout.addWidget(delete_btn)

        layout.addLayout(action_layout)

        save_btn = QPushButton("Сохранить и выйти")
        save_btn.clicked.connect(self.save_and_exit)
        layout.addWidget(save_btn)

        close_btn = QPushButton("↩ Выйти без сохранения")
        close_btn.clicked.connect(self.cancel_and_exit)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def load_images(self):
        try:
            self.all_images = convert_from_path(self.pdf_path)
            self.page_indices = [i for i in range(len(self.all_images)) if i not in self.deleted_pages]
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить PDF:\n{e}")

    def update_preview(self):
        if not self.page_indices:
            self.page_label.setText("Все страницы удалены.")
            self.scene.clear()
            return

        page_num = self.page_indices[self.current_index]
        image = self.all_images[page_num]
        angle = self.rotation_angles.get(str(page_num), 0)
        if angle != 0:
            image = image.rotate(angle, expand=True)

        qimage = ImageQt.ImageQt(image)
        pixmap = QPixmap.fromImage(QImage(qimage))

        self.scene.clear()
        self.scene.addPixmap(pixmap)
        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        self.page_label.setText(f"Страница {self.current_index + 1} из {len(self.page_indices)}")

    def prev_page(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_preview()

    def next_page(self):
        if self.current_index < len(self.page_indices) - 1:
            self.current_index += 1
            self.update_preview()

    def rotate_left(self):
        page_num = self.page_indices[self.current_index]
        self.rotation_angles[str(page_num)] = (self.rotation_angles.get(str(page_num), 0) - 90) % 360
        self.update_preview()

    def rotate_right(self):
        page_num = self.page_indices[self.current_index]
        self.rotation_angles[str(page_num)] = (self.rotation_angles.get(str(page_num), 0) + 90) % 360
        self.update_preview()

    def delete_page(self):
        if not self.page_indices:
            return

        page_num = self.page_indices[self.current_index]
        self.deleted_pages.add(page_num)
        self.page_indices.remove(page_num)

        if self.current_index >= len(self.page_indices):
            self.current_index = max(0, len(self.page_indices) - 1)

        self.update_preview()

    def save_state(self):
        state = {
            "deleted_pages": sorted(list(self.deleted_pages)),
            "rotation_angles": self.rotation_angles
        }
        state_path = os.path.splitext(self.pdf_path)[0] + "_state.json"
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        state_path = os.path.splitext(self.pdf_path)[0] + "_state.json"
        if os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    self.deleted_pages = set(state.get("deleted_pages", []))
                    self.rotation_angles = state.get("rotation_angles", {})
            except Exception as e:
                print(f"Не удалось загрузить состояние: {e}")

    def save_and_exit(self):
        self.save_state()
        QMessageBox.information(self, "Сохранено", "Изменения сохранены.")
        if self.back_callback:
            self.back_callback()
        self.accept()

    def cancel_and_exit(self):
        if self.back_callback:
            self.back_callback()
        self.reject()

    def closeEvent(self, event: QCloseEvent):
        self.cancel_and_exit()
        event.accept()
