# ui_auto_mode.py — полная версия с функциями экспорта в PNG и PDF в бургер-меню
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QMessageBox, QApplication, QMenu, QFileDialog
)
from PyQt6.QtCore import Qt, QPointF, QPoint
from PyQt6.QtGui import QPixmap, QTransform, QPainter, QAction

try:
    from core_parser import PseudocodeParser
    from core_graphviz import GraphGenerator
    CORE_AVAILABLE = True
except ImportError as e:
    CORE_AVAILABLE = False
    import_error = str(e)

from widgets_header_bar import HeaderBar
from widgets_editor_card import DraggableEditorCard
from ui_auto_mode_zoom import ZoomPanel


class AutoModeWindow(QMainWindow):
    def __init__(self, main_menu=None):
        super().__init__()
        self.main_menu = main_menu
        self.setWindowTitle("Автоматическая генерация блок-схемы")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        screen = QApplication.primaryScreen()
        if screen:
            self.resize(screen.availableGeometry().size())

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Создаём HeaderBar с колбэками для экспорта
        self.header = HeaderBar(
            self,
            export_png_callback=self.export_png,
            export_pdf_callback=self.export_pdf
        )
        main_layout.addWidget(self.header)

        # ----- QGraphicsView с высоким качеством рендеринга -----
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("border: none; background: white;")
        self.view.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform |
            QPainter.RenderHint.TextAntialiasing
        )
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        main_layout.addWidget(self.view, stretch=1)

        # ----- Плавающий редактор -----
        self.editor_card = DraggableEditorCard(central)
        self.editor_card.generate_btn.clicked.connect(self.generate)
        self.editor_card.move(30, 60)
        self.editor_card.raise_()

        # ----- Плавающая панель масштабирования -----
        self.zoom_panel = ZoomPanel(
            central,
            lambda: self._original_pixmap,
            self._apply_zoom,
            lambda: self._zoom_factor,
            lambda val: setattr(self, '_zoom_factor', val)
        )
        self.zoom_panel.move(max(10, self.width() - 280), 50)
        self.zoom_panel.show()
        self.zoom_panel.raise_()

        self._original_pixmap = None
        self._pixmap_item = None
        self._zoom_factor = 1.0

        self.setStyleSheet("""
            QMainWindow {
                background: white;
            }
            #headerBar {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #BDD1D5,
                    stop: 1 #97B4BE
                );
            }
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pixmap_item:
            self.view.centerOn(self._pixmap_item)
        new_x = max(10, self.width() - 280)
        self.zoom_panel.move(new_x, 50)
        self.zoom_panel.raise_()

    def _apply_zoom(self):
        if not self._pixmap_item:
            return

        viewport_center = self.view.mapToScene(
            self.view.viewport().rect().center()
        )

        transform = QTransform().scale(self._zoom_factor, self._zoom_factor)
        self.view.setTransform(transform)

        self.view.centerOn(viewport_center)
        self.view.viewport().update()

        self.zoom_panel.update_zoom_label(int(self._zoom_factor * 100))
        self.zoom_panel.raise_()

    def generate(self):
        if not CORE_AVAILABLE:
            QMessageBox.warning(self, "Ошибка", f"Модуль ядра не загружен:\n{import_error}")
            return

        text = self.editor_card.editor.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Информация", "Введите псевдокод для генерации.")
            return

        parser = PseudocodeParser()
        try:
            parsed = parser.parse(text)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка парсера", str(e))
            return

        gen = GraphGenerator()
        pixmap = gen.generate_preview(parsed)
        if pixmap.isNull():
            QMessageBox.warning(self, "Ошибка", "Не удалось создать изображение блок-схемы.")
            return

        self.scene.clear()
        self._original_pixmap = pixmap
        self._pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self._pixmap_item)

        self._zoom_factor = 1.0
        self.view.resetTransform()
        self.view.centerOn(self._pixmap_item)
        self.zoom_panel.update_zoom_label(100)
        self.zoom_panel.raise_()

    def export_png(self):
        """Экспорт текущей блок-схемы в PNG."""
        if self._original_pixmap and not self._original_pixmap.isNull():
            path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как PNG", "flowchart.png", "PNG (*.png)"
            )
            if path:
                if not self._original_pixmap.save(path, "PNG"):
                    QMessageBox.warning(self, "Ошибка", "Не удалось сохранить файл.")
                else:
                    QMessageBox.information(self, "Успех", f"Блок-схема сохранена в:\n{path}")
        else:
            QMessageBox.warning(self, "Предупреждение", "Нет изображения для сохранения.")

    def export_pdf(self):
        """Экспорт текущей блок-схемы в PDF через Graphviz."""
        if not self._original_pixmap or self._original_pixmap.isNull():
            QMessageBox.warning(self, "Предупреждение", "Нет изображения для экспорта.")
            return

        text = self.editor_card.editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Предупреждение", "Нет псевдокода для генерации PDF.")
            return

        parser = PseudocodeParser()
        try:
            parsed = parser.parse(text)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка парсера", str(e))
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как PDF", "flowchart.pdf", "PDF (*.pdf)"
        )
        if path:
            gen = GraphGenerator()
            if not gen.check_graphviz_installed():
                QMessageBox.warning(
                    self, "Graphviz не найден",
                    "Для экспорта в PDF требуется установленный Graphviz."
                )
                return
            try:
                gen.export_pdf(parsed, path)
                QMessageBox.information(self, "Успех", f"Блок-схема сохранена в:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить PDF:\n{str(e)}")

    def closeEvent(self, event):
        if self.main_menu:
            self.main_menu.show()
        super().closeEvent(event)