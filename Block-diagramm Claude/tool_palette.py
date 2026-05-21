import math

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QPixmap, QIcon,
    QPainterPath, QPolygonF
)

from flow_items import FlowItem
from line_items import BaseLineItem


TOOL_DEFS = [
    (FlowItem.TYPE_RECT,        "Процесс"),
    (FlowItem.TYPE_PREDEFINED,  "Функция"),
    (FlowItem.TYPE_DIAMOND,     "Решение"),
    (FlowItem.TYPE_HEXAGON,     "Цикл for"),
    (FlowItem.TYPE_TERMINATOR,  "Терминатор"),
    (FlowItem.TYPE_IO,          "Данные"),
    (FlowItem.TYPE_MANUAL_OP,   "Руч. оп."),
    (FlowItem.TYPE_LOOP_LIMIT,  "Гр. цикла"),
    (FlowItem.TYPE_CONNECTOR,   "Соедин."),
    (BaseLineItem.LINE_ARROW,   "Стрелка"),
    (BaseLineItem.LINE_SOLID,   "Линия"),
    (BaseLineItem.LINE_DASHED,  "Пунктир"),
]

LINE_TYPES = {BaseLineItem.LINE_ARROW, BaseLineItem.LINE_SOLID, BaseLineItem.LINE_DASHED}


def _make_icon(shape_type: str) -> QIcon:
    pm = QPixmap(44, 44)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor("#2C4F5C"), 1.6)
    p.setPen(pen)
    p.setBrush(QBrush(QColor("#FFFFFF")))
    m = 5

    if shape_type == FlowItem.TYPE_RECT:
        p.drawRect(QRectF(m, m + 6, 44 - 2*m, 32))

    elif shape_type == FlowItem.TYPE_PREDEFINED:
        r = QRectF(m, m + 6, 44 - 2*m, 32)
        p.drawRect(r)
        off = 6
        p.drawLine(QPointF(r.left() + off, r.top()), QPointF(r.left() + off, r.bottom()))
        p.drawLine(QPointF(r.right() - off, r.top()), QPointF(r.right() - off, r.bottom()))

    elif shape_type == FlowItem.TYPE_DIAMOND:
        p.drawPolygon(QPolygonF([
            QPointF(22, 5), QPointF(39, 22),
            QPointF(22, 39), QPointF(5, 22),
        ]))

    elif shape_type == FlowItem.TYPE_HEXAGON:
        p.drawPolygon(QPolygonF([
            QPointF(12, 5), QPointF(32, 5), QPointF(39, 22),
            QPointF(32, 39), QPointF(12, 39), QPointF(5, 22),
        ]))

    elif shape_type == FlowItem.TYPE_TERMINATOR:
        p.drawRoundedRect(QRectF(m, 13, 44 - 2*m, 18), 9, 9)

    elif shape_type == FlowItem.TYPE_IO:
        p.drawPolygon(QPolygonF([
            QPointF(11, 8), QPointF(39, 8),
            QPointF(33, 36), QPointF(5, 36),
        ]))

    elif shape_type == FlowItem.TYPE_MANUAL_OP:
        p.drawPolygon(QPolygonF([
            QPointF(5, 8), QPointF(39, 8),
            QPointF(33, 36), QPointF(11, 36),
        ]))

    elif shape_type == FlowItem.TYPE_LOOP_LIMIT:
        path = QPainterPath()
        path.addRoundedRect(QRectF(m, 10, 44 - 2*m, 24), 8, 8)
        p.drawPath(path)

    elif shape_type == FlowItem.TYPE_CONNECTOR:
        p.drawEllipse(QRectF(10, 10, 24, 24))

    elif shape_type == BaseLineItem.LINE_SOLID:
        p.drawLine(QPointF(6, 22), QPointF(38, 22))

    elif shape_type == BaseLineItem.LINE_DASHED:
        dash_pen = QPen(QColor("#2C4F5C"), 1.8)
        dash_pen.setStyle(Qt.PenStyle.DashLine)
        dash_pen.setDashPattern([5, 3])
        p.setPen(dash_pen)
        p.drawLine(QPointF(6, 22), QPointF(38, 22))

    elif shape_type == BaseLineItem.LINE_ARROW:
        p1 = QPointF(6, 22)
        p2 = QPointF(36, 22)
        p.drawLine(p1, p2)
        angle = math.radians(25)
        al = 10
        head = QPolygonF([
            p2,
            QPointF(p2.x() - al * math.cos(angle), p2.y() - al * math.sin(angle)),
            QPointF(p2.x() - al * math.cos(angle), p2.y() + al * math.sin(angle)),
        ])
        p.setBrush(QBrush(QColor("#2C4F5C")))
        p.setPen(QPen(QColor("#2C4F5C"), 1))
        p.drawPolygon(head)

    p.end()
    return QIcon(pm)


class ToolPalette(QWidget):
    tool_selected = pyqtSignal(str)

    _BTN_STYLE = """
        QPushButton {
            background-color: rgba(255,255,255,160);
            border: none;
            border-radius: 10px;
        }
        QPushButton:hover {
            background-color: rgba(180,220,235,200);
        }
        QPushButton:checked {
            background-color: rgba(74,156,181,180);
            border: 1.5px solid #3A7A96;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Widget)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            ToolPalette {
                background-color: rgba(221,238,243,230);
                border-radius: 20px;
            }
        """)
        self.setFixedWidth(130)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(3, 6)
        shadow.setColor(QColor(0, 0, 0, 55))
        self.setGraphicsEffect(shadow)

        self._drag_pos: QPoint = QPoint()
        self._dragging: bool   = False
        self._buttons: dict[str, QPushButton] = {}

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 14, 10, 14)
        layout.setSpacing(6)

        lbl = QLabel("Фигуры")
        f   = lbl.font()
        f.setPointSize(9)
        f.setItalic(True)
        lbl.setFont(f)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #4A7A8A; background: transparent;")
        layout.addWidget(lbl)

        grid = QWidget()
        grid.setStyleSheet("background: transparent;")
        grid_layout = QHBoxLayout(grid)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(4)

        col_l = QVBoxLayout()
        col_l.setSpacing(4)
        col_r = QVBoxLayout()
        col_r.setSpacing(4)

        for i, (stype, tooltip) in enumerate(TOOL_DEFS):
            btn = QPushButton()
            btn.setFixedSize(44, 44)
            btn.setIcon(_make_icon(stype))
            btn.setIconSize(btn.size())
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(
                lambda checked, st=stype, b=btn: self._on_click(st, b)
            )
            self._buttons[stype] = btn
            (col_l if i % 2 == 0 else col_r).addWidget(btn)

        col_l.addStretch()
        col_r.addStretch()
        grid_layout.addLayout(col_l)
        grid_layout.addLayout(col_r)
        layout.addWidget(grid)
        layout.addStretch()

    def _on_click(self, shape_type: str, btn: QPushButton):
        for b in self._buttons.values():
            if b is not btn:
                b.setChecked(False)
        self.tool_selected.emit(shape_type if btn.isChecked() else "")

    def deselect_all(self):
        for b in self._buttons.values():
            b.setChecked(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            parent  = self.parentWidget()
            if parent:
                new_pos.setX(max(0, min(new_pos.x(), parent.width()  - self.width())))
                new_pos.setY(max(0, min(new_pos.y(), parent.height() - self.height())))
            self.move(new_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)