from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QPushButton, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF
from PyQt6.QtGui import (
    QColor, QPixmap, QPainter, QPainterPath, QPen, QPolygonF, QIcon, QBrush, QMouseEvent
)


def create_tool_icon(shape_type):
    pix = QPixmap(48, 48)
    pix.fill(QColor(255, 255, 255, 0))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(Qt.GlobalColor.black, 2))
    painter.setBrush(QBrush(QColor("#E6E6E6")))
    rect = QRectF(4, 4, 40, 40)
    w, h = rect.width(), rect.height()
    if shape_type in ('process', 'io'):
        path = QPainterPath()
        if shape_type == 'process':
            path.addRect(rect)
        else:
            skew = 10
            poly = QPolygonF([
                QPointF(rect.left() + skew, rect.top()),
                QPointF(rect.right(), rect.top()),
                QPointF(rect.right() - skew, rect.bottom()),
                QPointF(rect.left(), rect.bottom())
            ])
            path.addPolygon(poly)
            path.closeSubpath()
        painter.drawPath(path)
    elif shape_type == 'decision':
        poly = QPolygonF([
            QPointF(rect.center().x(), rect.top()),
            QPointF(rect.right(), rect.center().y()),
            QPointF(rect.center().x(), rect.bottom()),
            QPointF(rect.left(), rect.center().y())
        ])
        painter.drawPolygon(poly)
    elif shape_type == 'startend':
        painter.drawEllipse(rect)
    elif shape_type == 'loop':
        d = w * 0.3
        poly = QPolygonF([
            QPointF(rect.left() + d, rect.top()),
            QPointF(rect.right() - d, rect.top()),
            QPointF(rect.right(), rect.center().y()),
            QPointF(rect.right() - d, rect.bottom()),
            QPointF(rect.left() + d, rect.bottom()),
            QPointF(rect.left(), rect.center().y())
        ])
        painter.drawPolygon(poly)
    elif shape_type == 'function':
        painter.drawRect(rect.toAlignedRect())
        painter.drawLine(QPointF(rect.left() + w*0.2, rect.top()), QPointF(rect.left() + w*0.2, rect.bottom()))
        painter.drawLine(QPointF(rect.right() - w*0.2, rect.top()), QPointF(rect.right() - w*0.2, rect.bottom()))
    elif shape_type == 'semicircle':
        path = QPainterPath()
        path.moveTo(rect.left(), rect.bottom())
        path.lineTo(rect.right(), rect.bottom())
        path.lineTo(rect.right(), rect.center().y())
        path.arcTo(rect, 0, 180)
        path.lineTo(rect.left(), rect.bottom())
        path.closeSubpath()
        painter.drawPath(path)
    elif shape_type == 'inverted_semicircle':
        path = QPainterPath()
        path.moveTo(rect.left(), rect.top())
        path.lineTo(rect.right(), rect.top())
        path.lineTo(rect.right(), rect.center().y())
        path.arcTo(rect, 0, -180)
        path.lineTo(rect.left(), rect.top())
        path.closeSubpath()
        painter.drawPath(path)
    elif shape_type == 'inverted_trapezoid':
        poly = QPolygonF([
            QPointF(rect.left(), rect.top()),
            QPointF(rect.right(), rect.top()),
            QPointF(rect.right() - w * 0.2, rect.bottom()),
            QPointF(rect.left() + w * 0.2, rect.bottom())
        ])
        painter.drawPolygon(poly)
    elif shape_type == 'elongated_oval':
        painter.drawRoundedRect(QRectF(2, 10, 44, 28), 10, 10)
    elif shape_type == 'line':
        painter.drawLine(QPointF(8, 40), QPointF(40, 8))
    elif shape_type == 'dashed_line':
        pen = QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(8, 40), QPointF(40, 8))
    elif shape_type == 'arrow_line':
        painter.drawLine(QPointF(8, 40), QPointF(40, 8))
        painter.setBrush(QBrush(Qt.GlobalColor.black))
        arrow_head = QPolygonF([
            QPointF(40, 8),
            QPointF(30, 8),
            QPointF(40, 18)
        ])
        painter.drawPolygon(arrow_head)
    elif shape_type == 'text':
        painter.setPen(QPen(Qt.GlobalColor.black, 3))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "T")
    painter.end()
    return pix


class DraggableToolPalette(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("toolPalette")
        self.setFixedWidth(180)
        self._drag_start_global = None
        self._drag_start_pos = None

        self.setStyleSheet("""
            #toolPalette {
                background: #DDEEF3;
                border-radius: 15px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

        grid = QGridLayout(self)
        grid.setContentsMargins(8, 12, 8, 12)
        grid.setSpacing(8)

        self.buttons = {}
        tools = [
            ("process", create_tool_icon("process")),
            ("decision", create_tool_icon("decision")),
            ("startend", create_tool_icon("startend")),
            ("io", create_tool_icon("io")),
            ("loop", create_tool_icon("loop")),
            ("function", create_tool_icon("function")),
            ("semicircle", create_tool_icon("semicircle")),
            ("inverted_semicircle", create_tool_icon("inverted_semicircle")),
            ("inverted_trapezoid", create_tool_icon("inverted_trapezoid")),
            ("elongated_oval", create_tool_icon("elongated_oval")),
            ("line", create_tool_icon("line")),
            ("dashed_line", create_tool_icon("dashed_line")),
            ("arrow_line", create_tool_icon("arrow_line")),
            ("text", create_tool_icon("text"))
        ]

        positions = [(i // 2, i % 2) for i in range(len(tools))]
        for (row, col), (tool_id, icon) in zip(positions, tools):
            btn = QPushButton()
            btn.setIcon(QIcon(icon))
            btn.setIconSize(btn.size())
            btn.setCheckable(True)
            btn.setFixedSize(64, 64)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 12px;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.8);
                }
                QPushButton:checked {
                    background: rgba(255,255,255,0.95);
                }
            """)
            btn.clicked.connect(lambda checked, t=tool_id: self.select_tool(t))
            grid.addWidget(btn, row, col, Qt.AlignmentFlag.AlignCenter)
            self.buttons[tool_id] = btn

        self.current_tool = None
        self.adjustSize()

    def select_tool(self, tool_id):
        if self.current_tool == tool_id:
            self.buttons[tool_id].setChecked(False)
            self.current_tool = None
        else:
            if self.current_tool is not None:
                self.buttons[self.current_tool].setChecked(False)
            self.buttons[tool_id].setChecked(True)
            self.current_tool = tool_id
        win = self.window()
        if hasattr(win, 'on_tool_changed'):
            win.on_tool_changed(self.current_tool)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_global = event.globalPosition().toPoint()
            self._drag_start_pos = self.pos()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_start_global is not None:
            delta = event.globalPosition().toPoint() - self._drag_start_global
            new_pos = self._drag_start_pos + delta
            parent = self.parentWidget()
            if parent:
                new_x = max(0, min(new_pos.x(), parent.width() - self.width()))
                new_y = max(0, min(new_pos.y(), parent.height() - self.height()))
                self.move(new_x, new_y)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start_global = None
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)