from math import atan2, sin, cos

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPen, QPolygonF
from PyQt6.QtWidgets import QGraphicsLineItem


class BaseLine(QGraphicsLineItem):
    def __init__(self, start_item=None, end_item=None):
        super().__init__()

        self.start_item = start_item
        self.end_item = end_item

        self.setFlags(
            QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable
        )

        if self.start_item:
            self.start_item.lines.append(self)

        if self.end_item:
            self.end_item.lines.append(self)

        self.update_position()

    def update_position(self):
        if not self.start_item or not self.end_item:
            return

        start = self.start_item.sceneBoundingRect().center()
        end = self.end_item.sceneBoundingRect().center()

        self.setLine(start.x(), start.y(), end.x(), end.y())

    def serialize(self):
        return {
            "type": self.__class__.__name__,
            "start_id": self.start_item.item_id,
            "end_id": self.end_item.item_id
        }


class SimpleLine(BaseLine):
    def __init__(self, start_item=None, end_item=None):
        super().__init__(start_item, end_item)
        self.setPen(QPen(Qt.GlobalColor.black, 2))


class DashedLine(BaseLine):
    def __init__(self, start_item=None, end_item=None):
        super().__init__(start_item, end_item)

        pen = QPen(Qt.GlobalColor.black, 2)
        pen.setStyle(Qt.PenStyle.DashLine)

        self.setPen(pen)


class ArrowLine(BaseLine):
    def __init__(self, start_item=None, end_item=None):
        super().__init__(start_item, end_item)
        self.setPen(QPen(Qt.GlobalColor.black, 2))

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

        line = self.line()

        angle = atan2(
            -(line.dy()),
            line.dx()
        )

        arrow_size = 12

        p1 = line.p2() - QPointF(
            sin(angle + 1.0) * arrow_size,
            cos(angle + 1.0) * arrow_size
        )

        p2 = line.p2() - QPointF(
            sin(angle - 1.0) * arrow_size,
            cos(angle - 1.0) * arrow_size
        )

        arrow_head = QPolygonF([
            line.p2(),
            p1,
            p2
        ])

        painter.setBrush(Qt.GlobalColor.black)
        painter.drawPolygon(arrow_head)