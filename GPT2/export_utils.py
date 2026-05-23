from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QRectF, QSizeF, Qt
from PyQt6.QtGui import QImage, QPainter, QPageSize, QPdfWriter
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QGraphicsScene


def export_scene_to_png(scene: QGraphicsScene, filepath: str) -> bool:
    rect = scene.itemsBoundingRect().adjusted(-30, -30, 30, 30)
    if rect.isEmpty():
        QMessageBox.warning(None, "Экспорт PNG", "Сцена пуста.")
        return False
    width = max(1, int(rect.width() * 2))
    height = max(1, int(rect.height() * 2))
    image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    scene.render(painter, target=QRectF(0, 0, width, height), source=rect)
    painter.end()
    ok = image.save(filepath)
    if not ok:
        QMessageBox.critical(None, "Экспорт PNG", "Не удалось сохранить PNG.")
    return ok


def export_scene_to_pdf(scene: QGraphicsScene, filepath: str) -> bool:
    rect = scene.itemsBoundingRect().adjusted(-30, -30, 30, 30)
    if rect.isEmpty():
        QMessageBox.warning(None, "Экспорт PDF", "Сцена пуста.")
        return False
    writer = QPdfWriter(filepath)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setResolution(300)
    painter = QPainter(writer)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    page_rect = QRectF(20, 20, max(1, writer.width() - 40), max(1, writer.height() - 40))
    scene.render(painter, target=page_rect, source=rect)
    painter.end()
    return True

