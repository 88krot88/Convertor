import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QMessageBox, QFileDialog, QSizePolicy
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from PIL import Image, ImageQt


class ImageToPdfEditorWindow(QWidget):
    def __init__(self, image_paths, back_callback):
        super().__init__()
        self.setWindowTitle("Редактор изображений перед сохранением в PDF")
        self.setMinimumSize(800, 600)

        self.image_paths = image_paths
        self.images = [Image.open(path).convert("RGB") for path in image_paths]
        self.rotation_angles = {}
        self.deleted_indices = set()
        self.current_index = 0
        self.back_callback = back_callback

        self.load_state()
        self.init_ui()
        self.update_preview()

    def init_ui(self):
        layout = QVBoxLayout()

        self.page_info_label = QLabel()
        self.page_info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.page_info_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setScaledContents(True)
        layout.addWidget(self.image_label, stretch=1)

        nav_layout = QHBoxLayout()
        prev_button = QPushButton("← Назад")
        prev_button.clicked.connect(self.prev_image)
        nav_layout.addWidget(prev_button)

        next_button = QPushButton("Вперёд →")
        next_button.clicked.connect(self.next_image)
        nav_layout.addWidget(next_button)

        layout.addLayout(nav_layout)

        action_layout = QHBoxLayout()

        rotate_left_button = QPushButton("⟲ Влево")
        rotate_left_button.clicked.connect(lambda: self.rotate_image(-90))
        action_layout.addWidget(rotate_left_button)

        rotate_right_button = QPushButton("⟳ Вправо")
        rotate_right_button.clicked.connect(lambda: self.rotate_image(90))
        action_layout.addWidget(rotate_right_button)

        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self.delete_image)
        action_layout.addWidget(delete_button)

        save_button = QPushButton("Сохранить как PDF")
        save_button.clicked.connect(self.save_as_pdf)
        action_layout.addWidget(save_button)

        cancel_button = QPushButton("↩ Выйти без сохранения")
        cancel_button.clicked.connect(self.cancel_and_exit)
        action_layout.addWidget(cancel_button)

        layout.addLayout(action_layout)
        self.setLayout(layout)

    def update_preview(self):
        visible_indices = [i for i in range(len(self.images)) if i not in self.deleted_indices]
        if not visible_indices:
            self.page_info_label.setText("Все изображения удалены.")
            self.image_label.clear()
            return

        index = visible_indices[self.current_index]
        image = self.images[index]
        angle = self.rotation_angles.get(str(index), 0)
        if angle != 0:
            image = image.rotate(angle, expand=True)

        qimage = ImageQt.ImageQt(image)
        pixmap = QPixmap.fromImage(QImage(qimage))

        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        self.page_info_label.setText(
            f"Изображение {self.current_index + 1} из {len(visible_indices)}"
        )

    def next_image(self):
        visible_indices = [i for i in range(len(self.images)) if i not in self.deleted_indices]
        if self.current_index < len(visible_indices) - 1:
            self.current_index += 1
            self.update_preview()

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_preview()

    def rotate_image(self, angle_delta):
        visible_indices = [i for i in range(len(self.images)) if i not in self.deleted_indices]
        if not visible_indices:
            return
        index = visible_indices[self.current_index]
        self.rotation_angles[str(index)] = (self.rotation_angles.get(str(index), 0) + angle_delta) % 360
        self.update_preview()

    def delete_image(self):
        visible_indices = [i for i in range(len(self.images)) if i not in self.deleted_indices]
        if not visible_indices:
            return
        index = visible_indices[self.current_index]
        self.deleted_indices.add(index)
        if self.current_index >= len(visible_indices) - 1:
            self.current_index = max(0, len(visible_indices) - 2)
        self.update_preview()

    def save_as_pdf(self):
        output_path, _ = QFileDialog.getSaveFileName(self, "Сохранить PDF", "", "PDF Files (*.pdf)")
        if not output_path:
            return

        visible_indices = [i for i in range(len(self.images)) if i not in self.deleted_indices]
        if not visible_indices:
            QMessageBox.warning(self, "Внимание", "Нет изображений для сохранения.")
            return

        processed_images = []
        for i in visible_indices:
            img = self.images[i]
            angle = self.rotation_angles.get(str(i), 0)
            if angle != 0:
                img = img.rotate(angle, expand=True)
            processed_images.append(img.convert("RGB"))

        try:
            processed_images[0].save(
                output_path, save_all=True, append_images=processed_images[1:], format="PDF"
            )
            self.save_state()
            QMessageBox.information(self, "Успех", "Файл PDF успешно сохранён.")
            self.back_callback()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить PDF:\n{e}")

    def cancel_and_exit(self):
        self.back_callback()
        self.close()

    def save_state(self):
        state = {
            "rotation_angles": self.rotation_angles,
            "deleted_indices": sorted(list(self.deleted_indices))
        }
        state_path = "image_to_pdf_state.json"
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        state_path = "image_to_pdf_state.json"
        if os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    self.deleted_indices = set(state.get("deleted_indices", []))
                    self.rotation_angles = state.get("rotation_angles", {})
            except Exception as e:
                print(f"Не удалось загрузить состояние: {e}")

    def closeEvent(self, event):
        if callable(self.back_callback):
            self.back_callback()
        event.accept()

