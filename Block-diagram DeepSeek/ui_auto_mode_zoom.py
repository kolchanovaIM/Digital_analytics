# ui_auto_mode_zoom.py — панель увеличенной высоты с тенью
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QFileDialog, QMessageBox, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QColor


class ZoomPanel(QFrame):
    """Плавающая панель масштабирования и сохранения."""
    def __init__(self, parent, get_original_pixmap_callback, apply_zoom_callback,
                 get_zoom_factor_callback, set_zoom_factor_callback):
        super().__init__(parent)
        self._get_original_pixmap = get_original_pixmap_callback
        self._apply_zoom = apply_zoom_callback
        self._get_zoom_factor = get_zoom_factor_callback
        self._set_zoom_factor = set_zoom_factor_callback

        self.setMinimumSize(260, 60)                     # ширина и высота
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.85);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 10px;
            }
        """)
        # Добавляем тень для объёма
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)        # увеличены вертикальные отступы
        layout.setSpacing(8)

        btn_style = """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 16px;
                color: #333;
                min-width: 30px;
                min-height: 30px;
            }
            QPushButton:hover {
                background: rgba(0, 0, 0, 0.08);
            }
        """

        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setStyleSheet(btn_style)
        self.btn_zoom_out.clicked.connect(self._on_zoom_out)

        self.zoom_label = QPushButton("100%")
        self.zoom_label.setMinimumWidth(60)
        self.zoom_label.setStyleSheet(btn_style)
        self.zoom_label.clicked.connect(self._on_zoom_reset)

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setStyleSheet(btn_style)
        self.btn_zoom_in.clicked.connect(self._on_zoom_in)

        self.btn_save = QPushButton("💾")
        self.btn_save.setToolTip("Сохранить как PNG")
        self.btn_save.setStyleSheet(btn_style)
        self.btn_save.clicked.connect(self.save_image)

        layout.addWidget(self.btn_zoom_out)
        layout.addWidget(self.zoom_label)
        layout.addWidget(self.btn_zoom_in)
        layout.addSpacing(14)
        layout.addWidget(self.btn_save)

    def _on_zoom_in(self):
        factor = self._get_zoom_factor()
        new_zoom = min(factor + 0.1, 3.0)
        if new_zoom != factor:
            self._set_zoom_factor(new_zoom)
            self._apply_zoom()

    def _on_zoom_out(self):
        factor = self._get_zoom_factor()
        new_zoom = max(factor - 0.1, 0.1)
        if new_zoom != factor:
            self._set_zoom_factor(new_zoom)
            self._apply_zoom()

    def _on_zoom_reset(self):
        self._set_zoom_factor(1.0)
        self._apply_zoom()

    def update_zoom_label(self, percent: int):
        self.zoom_label.setText(f"{percent}%")

    def save_image(self):
        pixmap = self._get_original_pixmap()
        if pixmap and not pixmap.isNull():
            fp, _ = QFileDialog.getSaveFileName(
                self, "Сохранить", "flowchart.png", "PNG (*.png)"
            )
            if fp and not pixmap.save(fp, "PNG"):
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить.")
        else:
            QMessageBox.warning(self, "Предупреждение", "Нет изображения.")