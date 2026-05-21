from __future__ import annotations

import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSizePolicy, QMenu,
    QGraphicsDropShadowEffect, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, QLineF, QSizeF, QMarginsF
from PyQt6.QtGui import (
    QPainter, QLinearGradient, QColor, QBrush, QFont, QAction,
    QPixmap, QPdfWriter, QPageSize
)

from canvas_scene import GridScene
from canvas_view  import CanvasView
from flow_items   import FlowItem
from line_items   import BaseLineItem
from tool_palette import ToolPalette, LINE_TYPES


# ── Градиентный фон ────────────────────────────────────────────────────────────

class GradientWidget(QWidget):
    def __init__(self, c1: str, c2: str, horizontal: bool = False, parent=None):
        super().__init__(parent)
        self._c1 = QColor(c1)
        self._c2 = QColor(c2)
        self._horizontal = horizontal

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g = (QLinearGradient(0, 0, self.width(), 0) if self._horizontal
             else QLinearGradient(0, 0, 0, self.height()))
        g.setColorAt(0.0, self._c1)
        g.setColorAt(1.0, self._c2)
        p.fillRect(self.rect(), QBrush(g))


# ── Окно ручного рисования ─────────────────────────────────────────────────────

class ManualModeWindow(QMainWindow):

    _MENU_STYLE = """
        QMenu {
            background-color: #FFFFFF;
            border: 1px solid #DDEEF3;
            border-radius: 10px;
            padding: 6px;
            font-family: 'Segoe UI','Arial',sans-serif;
            font-size: 13px;
            color: #2C3E50;
        }
        QMenu::item {
            padding: 8px 24px 8px 12px;
            border-radius: 6px;
        }
        QMenu::item:selected {
            background-color: #DDEEF3;
            color: #1B3A45;
        }
        QMenu::separator {
            height: 1px;
            background: #DDEEF3;
            margin: 4px 8px;
        }
    """

    _WIN_BTN_BASE = """
        QPushButton {
            background-color: rgba(255,255,255,40);
            color: #1B3A45; border: none; border-radius: 6px;
            font-size: 14px; font-family: 'Segoe UI','Arial',sans-serif;
            padding: 0px;
        }
        QPushButton:hover   { background-color: rgba(255,255,255,90);  }
        QPushButton:pressed { background-color: rgba(255,255,255,130); }
    """

    _WIN_BTN_CLOSE = """
        QPushButton {
            background-color: rgba(255,255,255,40);
            color: #1B3A45; border: none; border-radius: 6px;
            font-size: 14px; font-family: 'Segoe UI','Arial',sans-serif;
            padding: 0px;
        }
        QPushButton:hover   { background-color: rgba(220,60,60,200);  color: white; }
        QPushButton:pressed { background-color: rgba(180,30,30,220);  color: white; }
    """

    def __init__(self, main_menu=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FlowChart Designer — Ручное рисование")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(900, 600)

        self._main_menu   = main_menu
        self._drag_pos    = QPoint()
        self._dragging    = False
        self._active_tool = ""
        self._tmp_line    = None
        self._line_start  = None

        self._build_ui()

    # ── Построение интерфейса ─────────────────────────────────────────────────

    def _build_ui(self):
        root = GradientWidget("#BDD1D5", "#97B4BE")
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Titlebar
        titlebar = GradientWidget("#BDD1D5", "#97B4BE", horizontal=True)
        titlebar.setFixedHeight(44)
        tb = QHBoxLayout(titlebar)
        tb.setContentsMargins(8, 6, 12, 6)
        tb.setSpacing(6)

        btn_burger = QPushButton("☰")
        btn_burger.setFixedSize(32, 32)
        btn_burger.setStyleSheet(self._WIN_BTN_BASE)
        btn_burger.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_burger.clicked.connect(self._show_burger_menu)
        tb.addWidget(btn_burger)

        lbl = QLabel("Ручное рисование блок-схемы")
        f = QFont("Segoe UI", 11)
        f.setItalic(True)
        lbl.setFont(f)
        lbl.setStyleSheet("color: #1B3A45; background: transparent;")
        tb.addWidget(lbl)
        tb.addStretch()

        btn_min = QPushButton("—")
        btn_min.setFixedSize(32, 32)
        btn_min.setStyleSheet(self._WIN_BTN_BASE)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.clicked.connect(self.showMinimized)
        tb.addWidget(btn_min)

        self._btn_max = QPushButton("□")
        self._btn_max.setFixedSize(32, 32)
        self._btn_max.setStyleSheet(self._WIN_BTN_BASE)
        self._btn_max.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_max.clicked.connect(self._toggle_maximize)
        tb.addWidget(self._btn_max)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(32, 32)
        btn_close.setStyleSheet(self._WIN_BTN_CLOSE)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.close)
        tb.addWidget(btn_close)

        root_layout.addWidget(titlebar)

        # Canvas card
        self._canvas_card = QWidget(root)
        self._canvas_card.setObjectName("canvasCard")
        self._canvas_card.setStyleSheet("""
            QWidget#canvasCard {
                background-color: #F4F8FA;
                border-radius: 20px;
            }
        """)
        card_shadow = QGraphicsDropShadowEffect()
        card_shadow.setBlurRadius(32)
        card_shadow.setOffset(4, 8)
        card_shadow.setColor(QColor(0, 0, 0, 55))
        self._canvas_card.setGraphicsEffect(card_shadow)

        card_layout = QVBoxLayout(self._canvas_card)
        card_layout.setContentsMargins(0, 0, 0, 0)

        self._scene = GridScene()
        self._scene.setSceneRect(QRectF(-40000, -40000, 80000, 80000))

        self._canvas = CanvasView(self._scene)
        self._canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._canvas.mouse_pressed.connect(self._on_canvas_press)
        self._canvas.mouse_moved.connect(self._on_canvas_move)
        self._canvas.mouse_released.connect(self._on_canvas_release)
        card_layout.addWidget(self._canvas)

        work_container = QWidget()
        work_container.setStyleSheet("background: transparent;")
        wc_layout = QVBoxLayout(work_container)
        wc_layout.setContentsMargins(20, 12, 20, 20)
        wc_layout.addWidget(self._canvas_card)
        root_layout.addWidget(work_container, stretch=1)

        # Floating palette
        self._palette = ToolPalette(root)
        self._palette.tool_selected.connect(self._on_tool_selected)
        self._palette.raise_()

    # ── Layout ───────────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_palette()

    def showEvent(self, event):
        super().showEvent(event)
        self._reposition_palette()

    def _reposition_palette(self):
        root = self.centralWidget()
        if root and self._palette:
            self._palette.move(28, 60)
            self._palette.raise_()
            avail_h = root.height() - 80
            self._palette.setFixedHeight(max(100, avail_h))

    # ── Tool selection ────────────────────────────────────────────────────────

    def _on_tool_selected(self, tool: str):
        self._active_tool = tool
        is_lasso = (tool == "lasso")
        self._canvas.set_lasso_mode(is_lasso)
        self._canvas.set_drawing_mode(tool != "" and not is_lasso)
        if not tool:
            self._canvas.setDragMode(CanvasView.DragMode.NoDrag)

    # ── Canvas events ─────────────────────────────────────────────────────────

    def _on_canvas_press(self, scene_pos: QPointF):
        if not self._active_tool or self._active_tool == "lasso":
            return
        if self._active_tool in LINE_TYPES:
            self._line_start = scene_pos
            self._tmp_line   = BaseLineItem(
                scene_pos, scene_pos, self._active_tool
            )
            self._scene.addItem(self._tmp_line)
        else:
            self._place_shape(self._active_tool, scene_pos)

    def _on_canvas_move(self, scene_pos: QPointF):
        if self._tmp_line is not None:
            self._tmp_line.set_p2(scene_pos)

    def _on_canvas_release(self, scene_pos: QPointF):
        if self._tmp_line is None:
            return
        if QLineF(self._line_start, scene_pos).length() < 5:
            self._scene.removeItem(self._tmp_line)
        else:
            self._tmp_line.set_p2(scene_pos)
        self._tmp_line   = None
        self._line_start = None

    # ── Shape factory ─────────────────────────────────────────────────────────

    def _place_shape(self, stype: str, scene_pos: QPointF):
        w, h = 140, 70
        if stype == FlowItem.TYPE_CONNECTOR:
            w, h = 50, 50
        elif stype == FlowItem.TYPE_DIAMOND:
            w, h = 120, 80
        elif stype in (FlowItem.TYPE_WHILE, FlowItem.TYPE_FOR):
            w, h = 160, 70
        item = FlowItem(
            stype,
            scene_pos.x() - w / 2,
            scene_pos.y() - h / 2,
            w, h
        )
        self._scene.addItem(item)

    # ── Delete ────────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            for item in self._scene.selectedItems():
                self._scene.removeItem(item)
        else:
            super().keyPressEvent(event)

    # ── Burger-меню ───────────────────────────────────────────────────────────

    def _show_burger_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(self._MENU_STYLE)

        act_png = QAction("💾  Сохранить как PNG", self)
        act_png.triggered.connect(self._export_png)
        menu.addAction(act_png)

        act_pdf = QAction("📄  Сохранить как PDF", self)
        act_pdf.triggered.connect(self._export_pdf)
        menu.addAction(act_pdf)

        menu.addSeparator()

        act_back = QAction("← Назад", self)
        act_back.triggered.connect(self._go_back)
        menu.addAction(act_back)

        btn = self.sender()
        menu.exec(btn.mapToGlobal(QPoint(0, btn.height())))

    # ── Экспорт ───────────────────────────────────────────────────────────────

    def _render_scene_to_pixmap(self) -> QPixmap | None:
        """
        Рендерит все видимые элементы сцены в QPixmap (белый фон, 2× разрешение).
        Возвращает None если сцена пуста.
        """
        items = [it for it in self._scene.items() if it.isVisible()]
        if not items:
            return None

        rect = self._scene.itemsBoundingRect()
        if rect.isEmpty():
            return None

        pad = 40.0
        rect = rect.adjusted(-pad, -pad, pad, pad)

        scale = 2.0
        w = max(1, int(rect.width()  * scale))
        h = max(1, int(rect.height() * scale))

        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.GlobalColor.white)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self._scene.render(painter, source=rect)
        painter.end()

        return pixmap

    def _export_png(self):
        """Экспортирует содержимое холста в PNG."""
        pixmap = self._render_scene_to_pixmap()
        if pixmap is None:
            QMessageBox.information(
                self, "Холст пуст",
                "Добавьте элементы на холст перед сохранением."
            )
            return

        dest, _ = QFileDialog.getSaveFileName(
            self, "Сохранить блок-схему как PNG",
            "блок_схема.png",
            "PNG изображения (*.png)"
        )
        if not dest:
            return
        if not dest.lower().endswith(".png"):
            dest += ".png"

        if pixmap.save(dest, "PNG"):
            QMessageBox.information(
                self, "Готово",
                f"Блок-схема сохранена:\n{dest}"
            )
        else:
            QMessageBox.critical(
                self, "Ошибка",
                "Не удалось сохранить файл PNG."
            )

    def _export_pdf(self):
        """Экспортирует содержимое холста в PDF."""
        pixmap = self._render_scene_to_pixmap()
        if pixmap is None:
            QMessageBox.information(
                self, "Холст пуст",
                "Добавьте элементы на холст перед сохранением."
            )
            return

        dest, _ = QFileDialog.getSaveFileName(
            self, "Сохранить блок-схему как PDF",
            "блок_схема.pdf",
            "PDF документы (*.pdf)"
        )
        if not dest:
            return
        if not dest.lower().endswith(".pdf"):
            dest += ".pdf"

        try:
            dpi = 96.0
            mm_per_inch = 25.4
            w_mm = pixmap.width()  / dpi * mm_per_inch
            h_mm = pixmap.height() / dpi * mm_per_inch

            writer = QPdfWriter(dest)
            writer.setPageSize(
                QPageSize(QSizeF(w_mm, h_mm), QPageSize.Unit.Millimeter)
            )
            writer.setPageMargins(QMarginsF(0, 0, 0, 0))
            writer.setResolution(int(dpi))

            painter = QPainter(writer)
            painter.drawPixmap(painter.viewport(), pixmap, pixmap.rect())
            painter.end()

            QMessageBox.information(
                self, "Готово",
                f"Блок-схема сохранена:\n{dest}"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка сохранения PDF", str(exc))

    # ── Window controls ───────────────────────────────────────────────────────

    def _go_back(self):
        if self._main_menu:
            self._main_menu.setGeometry(self.geometry())
            if self.isMaximized():
                self._main_menu.showMaximized()
            else:
                self._main_menu.show()
        self.close()

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self._btn_max.setText("□")
        else:
            self.showMaximized()
            self._btn_max.setText("❐")

    def mousePressEvent(self, event):
        if (event.button() == Qt.MouseButton.LeftButton
                and event.position().y() <= 44):
            self._dragging = True
            self._drag_pos = (event.globalPosition().toPoint()
                              - self.frameGeometry().topLeft())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            if self.isMaximized():
                self.showNormal()
                self._btn_max.setText("□")
                self._drag_pos = QPoint(self.width() // 2, 22)
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)