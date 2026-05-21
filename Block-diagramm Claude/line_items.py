import math
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsLineItem
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPolygonF, QPainterPath


ENDPOINT_RADIUS = 6
ARROW_LEN = 14
ARROW_ANGLE = 25


def _arrow_head(p1: QPointF, p2: QPointF) -> QPolygonF:
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return QPolygonF()
    ux, uy = dx / length, dy / length
    angle = math.radians(ARROW_ANGLE)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    lx1 = p2.x() - ARROW_LEN * (ux * cos_a + uy * (-sin_a))
    ly1 = p2.y() - ARROW_LEN * (ux * sin_a + uy * cos_a)
    lx2 = p2.x() - ARROW_LEN * (ux * cos_a + uy * sin_a)
    ly2 = p2.y() - ARROW_LEN * (ux * (-sin_a) + uy * cos_a)
    return QPolygonF([p2, QPointF(lx1, ly1), QPointF(lx2, ly2)])


class BaseLineItem(QGraphicsItem):
    LINE_SOLID  = "solid_line"
    LINE_DASHED = "dashed_line"
    LINE_ARROW  = "arrow_line"

    def __init__(self, p1: QPointF, p2: QPointF, line_type: str):
        super().__init__()
        self._p1 = QPointF(p1)
        self._p2 = QPointF(p2)
        self._type = line_type
        self._dragging_end = None
        self._drag_offset = QPointF()

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

    def p1(self) -> QPointF:
        return self.mapToScene(self._p1)

    def p2(self) -> QPointF:
        return self.mapToScene(self._p2)

    def set_p2(self, scene_pos: QPointF):
        self.prepareGeometryChange()
        self._p2 = self.mapFromScene(scene_pos)
        self.update()

    def boundingRect(self) -> QRectF:
        pad = ENDPOINT_RADIUS + ARROW_LEN + 4
        x = min(self._p1.x(), self._p2.x()) - pad
        y = min(self._p1.y(), self._p2.y()) - pad
        w = abs(self._p2.x() - self._p1.x()) + 2 * pad
        h = abs(self._p2.y() - self._p1.y()) + 2 * pad
        return QRectF(x, y, w, h)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        dx = self._p2.x() - self._p1.x()
        dy = self._p2.y() - self._p1.y()
        length = math.hypot(dx, dy)
        if length < 1:
            path.addEllipse(self._p1, 4, 4)
            return path
        nx, ny = -dy / length * 5, dx / length * 5
        poly = QPolygonF([
            QPointF(self._p1.x() + nx, self._p1.y() + ny),
            QPointF(self._p2.x() + nx, self._p2.y() + ny),
            QPointF(self._p2.x() - nx, self._p2.y() - ny),
            QPointF(self._p1.x() - nx, self._p1.y() - ny),
        ])
        path.addPolygon(poly)
        path.closeSubpath()
        return path

    def _make_pen(self) -> QPen:
        pen = QPen(QColor("#3A5F6F"), 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        if self._type == self.LINE_DASHED:
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashPattern([6, 4])
        return pen

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self._make_pen())
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(self._p1, self._p2)

        if self._type == self.LINE_ARROW:
            head = _arrow_head(self._p1, self._p2)
            if not head.isEmpty():
                painter.setBrush(QBrush(QColor("#3A5F6F")))
                painter.setPen(QPen(QColor("#3A5F6F"), 1))
                painter.drawPolygon(head)

        if self.isSelected():
            painter.setPen(QPen(QColor("#4A9CB5"), 1))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            r = ENDPOINT_RADIUS
            painter.drawEllipse(self._p1, r, r)
            painter.drawEllipse(self._p2, r, r)

    def _endpoint_at(self, pos: QPointF) -> str | None:
        if QLineF(pos, self._p1).length() <= ENDPOINT_RADIUS + 3:
            return "p1"
        if QLineF(pos, self._p2).length() <= ENDPOINT_RADIUS + 3:
            return "p2"
        return None

    def hoverMoveEvent(self, event):
        if self._endpoint_at(event.pos()):
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        end = self._endpoint_at(event.pos())
        if end:
            self._dragging_end = end
            event.accept()
        else:
            self._dragging_end = None
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging_end:
            self.prepareGeometryChange()
            if self._dragging_end == "p1":
                self._p1 = event.pos()
            else:
                self._p2 = event.pos()
            self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._dragging_end = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            scene = self.scene()
            if scene:
                scene.removeItem(self)
        else:
            super().keyPressEvent(event)