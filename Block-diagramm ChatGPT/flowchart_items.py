import uuid

from PyQt6.QtCore import QRectF, Qt, QPointF
from PyQt6.QtGui import (
    QBrush,
    QPen,
    QPolygonF,
    QPainterPath
)
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsTextItem,
    QInputDialog
)

from constants import (
    PROCESS_COLOR,
    DECISION_COLOR,
    IO_COLOR,
    TERMINAL_COLOR
)


class ResizeHandle(QGraphicsItem):
    SIZE = 8

    def __init__(self, parent, position):
        super().__init__(parent)

        self.position_name = position
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def boundingRect(self):
        return QRectF(0, 0, self.SIZE, self.SIZE)

    def paint(self, painter, option, widget=None):
        painter.setBrush(Qt.GlobalColor.white)
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawRect(0, 0, self.SIZE, self.SIZE)


class FlowchartItem(QGraphicsItem):
    def __init__(self, shape_type="process", text="Блок"):
        super().__init__()

        self.item_id = str(uuid.uuid4())

        self.shape_type = shape_type

        self.width = 140
        self.height = 70

        self.lines = []

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.text_item = QGraphicsTextItem(text, self)
        self.text_item.setDefaultTextColor(Qt.GlobalColor.black)
        self.text_item.setPos(20, 20)

        self.handles = []
        self.create_handles()

    def create_handles(self):
        for pos in range(8):
            handle = ResizeHandle(self, pos)
            handle.hide()
            self.handles.append(handle)

        self.update_handles()

    def update_handles(self):
        positions = [
            (0, 0),
            (self.width / 2, 0),
            (self.width, 0),
            (0, self.height / 2),
            (self.width, self.height / 2),
            (0, self.height),
            (self.width / 2, self.height),
            (self.width, self.height)
        ]

        for handle, pos in zip(self.handles, positions):
            handle.setPos(pos[0] - 4, pos[1] - 4)

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget=None):
        painter.setPen(QPen(Qt.GlobalColor.black, 2))

        if self.shape_type == "process":
            painter.setBrush(QBrush(PROCESS_COLOR))
            painter.drawRect(0, 0, self.width, self.height)

        elif self.shape_type == "decision":
            painter.setBrush(QBrush(DECISION_COLOR))

            polygon = QPolygonF([
                QPointF(self.width / 2, 0),
                QPointF(self.width, self.height / 2),
                QPointF(self.width / 2, self.height),
                QPointF(0, self.height / 2)
            ])

            painter.drawPolygon(polygon)

        elif self.shape_type == "io":
            painter.setBrush(QBrush(IO_COLOR))

            polygon = QPolygonF([
                QPointF(20, 0),
                QPointF(self.width, 0),
                QPointF(self.width - 20, self.height),
                QPointF(0, self.height)
            ])

            painter.drawPolygon(polygon)

        elif self.shape_type == "terminal":
            painter.setBrush(QBrush(TERMINAL_COLOR))
            painter.drawEllipse(0, 0, self.width, self.height)

        if self.isSelected():
            for handle in self.handles:
                handle.show()
        else:
            for handle in self.handles:
                handle.hide()

    def mouseDoubleClickEvent(self, event):
        text, ok = QInputDialog.getText(
            None,
            "Редактирование",
            "Введите текст:",
            text=self.text_item.toPlainText()
        )

        if ok:
            self.text_item.setPlainText(text)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            for line in self.lines:
                line.update_position()

        return super().itemChange(change, value)

    def serialize(self):
        return {
            "id": self.item_id,
            "shape": self.shape_type,
            "x": self.pos().x(),
            "y": self.pos().y(),
            "width": self.width,
            "height": self.height,
            "text": self.text_item.toPlainText()
        }