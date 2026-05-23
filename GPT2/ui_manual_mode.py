from __future__ import annotations

from typing import Optional
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QTransform
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QFrame, QGraphicsScene, QGraphicsView,
    QGridLayout, QHBoxLayout, QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget, QGraphicsDropShadowEffect
)

from constants import (
    DEFAULT_ITEM_HEIGHT, DEFAULT_ITEM_WIDTH, FramelessWindow, GRID_COLOR, GRID_STEP,
    MAX_ZOOM, MIN_ZOOM, base_font, make_tool_button, snap_value
)
from flowchart_items import FlowchartItem
from line_items import ArrowLine, DashedLine, SimpleLine, BaseLine


class CanvasScene(QGraphicsScene):
    def __init__(self, owner: "ManualModeWindow"):
        super().__init__(owner)
        self.owner = owner
        self.current_tool = "select"
        self.start_item: Optional[FlowchartItem] = None
        self.setSceneRect(-10000, -10000, 20000, 20000)

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor("#F3F3F3"))  # Светлый фон под мелкую сетку
        grid_pen = QPen(QColor("#D0D8DC"))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)

        # Отрисовка мелкой сетки в соответствии с "Mask group-1.jpg"
        step = 15
        left = int(rect.left()) - (int(rect.left()) % step)
        top = int(rect.top()) - (int(rect.top()) % step)

        for x in range(left, int(rect.right()), step):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(top, int(rect.bottom()), step):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)


class CanvasView(QGraphicsView):
    def __init__(self, scene: CanvasScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(QColor("#F3F3F3"))


class ManualModeWindow(FramelessWindow):
    def __init__(self, parent=None, previous_window=None):
        super().__init__("Ручной режим", parent)
        self.previous_window = previous_window
        self.setMinimumSize(1200, 800)

        # Шапка окна ("Mask group-1.jpg")
        self.header_panel = QFrame(self)
        self.header_panel.setFixedHeight(45)
        self.header_panel.setStyleSheet("background-color: #9EB4C0; border: none;")
        header_layout = QHBoxLayout(self.header_panel)
        header_layout.setContentsMargins(15, 0, 15, 0)

        self.menu_burger_btn = QPushButton("≡")
        self.menu_burger_btn.setFixedSize(30, 30)
        self.menu_burger_btn.setStyleSheet("font-size: 24px; color: #FFFFFF; background: transparent; border: none;")
        header_layout.addWidget(self.menu_burger_btn, 0, Qt.AlignmentFlag.AlignLeft)
        header_layout.addStretch()

        self.scene = CanvasScene(self)
        self.view = CanvasView(self.scene, self)

        # Вертикальное «облако» панели инструментов слева ("Mask group-1.jpg")
        self.toolbar = QFrame(self)
        self.toolbar.setFixedSize(180, 420)
        self.toolbar.setStyleSheet("background-color: #A3BAC6; border-radius: 35px; border: none;")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(4, 6)
        self.toolbar.setGraphicsEffect(shadow)

        tb_layout = QVBoxLayout(self.toolbar)
        tb_layout.setContentsMargins(15, 25, 15, 25)

        self.tool_grid = QGridLayout()
        self.tool_grid.setSpacing(12)
        tb_layout.addLayout(self.tool_grid)

        # Кнопки инструментов (сетка 2x4)
        self.tool_buttons = {}
        tools = [
            ("process", "▢", "Процесс"), ("decision", "◇", "Решение"),
            ("io", "▱", "Ввод/вывод"), ("terminal", "◯", "Терминатор"),
            ("arrow", "→", "Стрелка"), ("line", "—", "Линия"),
            ("dash", "╌", "Пунктир"), ("select", "↖", "Выбор")
        ]

        btn_style = """
            QPushButton {
                background-color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                color: #4A5A62;
            }
            QPushButton:checked {
                background-color: #D1E4ED;
                border: 2px solid #5A7380;
            }
        """

        for idx, (name, icon_text, tip) in enumerate(tools):
            btn = QPushButton(icon_text)
            btn.setCheckable(True)
            btn.setFixedSize(65, 55)
            btn.setStyleSheet(btn_style)
            btn.setToolTip(tip)
            btn.clicked.connect(lambda checked=False, n=name: self.set_tool(n))
            self.tool_buttons[name] = btn
            self.tool_grid.addWidget(btn, idx // 2, idx % 2)

        # Кнопки экспорта аккуратно вниз панели инструментов
        self.export_png_btn = QPushButton("PNG")
        self.export_png_btn.setFixedHeight(30)
        self.export_png_btn.setStyleSheet("background: white; border-radius: 6px; color: #4A5A62; font-weight: bold;")
        self.export_png_btn.clicked.connect(self.export_png)
        tb_layout.addSpacing(15)
        tb_layout.addWidget(self.export_png_btn)

        # Сборка структуры окна
        container = QWidget(self)
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.view)

        # Наложение плавающего тулбара поверх холста слева
        self.toolbar.setParent(container)
        self.toolbar.move(30, 40)

        window_vbox = QVBoxLayout(self)
        window_vbox.setContentsMargins(0, 0, 0, 0)
        window_vbox.setSpacing(0)
        window_vbox.addWidget(self.header_panel)
        window_vbox.addWidget(container)
        self.body_layout.addWidget(container)

        self.set_tool("select")

    def set_tool(self, tool: str) -> None:
        self.scene.current_tool = tool
        if tool in self.tool_buttons:
            for name, btn in self.tool_buttons.items():
                btn.setChecked(name == tool)
        if tool == "select":
            self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def load_graph_data(self, nodes, edges) -> None:
        self.scene.clear()
        x, y = 100, 100
        for node in nodes:
            item = FlowchartItem(node.text, node.shape, DEFAULT_ITEM_WIDTH, DEFAULT_ITEM_HEIGHT)
            item.setPos(x, y)
            self.scene.addItem(item)
            y += 150

    def export_png(self) -> None:
        filepath, _ = QFileDialog.getSaveFileName(self, "Экспорт PNG", "flowchart.png", "PNG Images (*.png)")
        if filepath:
            from export_utils import export_scene_to_png
            export_scene_to_png(self.scene, filepath)

    def closeEvent(self, event):
        if self.previous_window is not None:
            self.previous_window.show()
        super().closeEvent(event)