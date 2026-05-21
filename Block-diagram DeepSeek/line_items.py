# line_items.py
import math
from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsLineItem, QGraphicsRectItem, QGraphicsEllipseItem
)
from PyQt6.QtCore import Qt, QPointF, QLineF
from PyQt6.QtGui import (
    QColor, QBrush, QPen, QPolygonF, QTransform
)
from constants import GRID_SIZE, MIN_LINE_LENGTH, SNAP_DISTANCE
from flowchart_items import FlowchartItem   # для проверки фигур при прилипании


# ====================== РУЧКИ ДЛЯ ЛИНИЙ ======================
class LineEndpointHandle(QGraphicsRectItem):
    """Ручка для изменения конца линии."""
    def __init__(self, parent_line, index):
        super().__init__(-5, -5, 10, 10, parent_line)
        self.parent_line = parent_line
        self.index = index       # 0 = start, 1 = end
        self.setPen(QPen(QColor("#FF5500"), 1.5))
        self.setBrush(QBrush(Qt.GlobalColor.white))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(10)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def setPosSilent(self, pos):
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)
        self.setPos(pos)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.parent_line:
                self.parent_line.update_endpoint(self.index, value)
            return self.pos()
        return super().itemChange(change, value)


class CenterHandle(QGraphicsEllipseItem):
    """Центральная ручка для перемещения всей линии."""
    def __init__(self, parent_line):
        super().__init__(-6, -6, 12, 12, parent_line)
        self.parent_line = parent_line
        self.setPen(QPen(QColor("#0078D7"), 1.5))
        self.setBrush(QBrush(QColor("#0078D7")))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(10)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def setPosSilent(self, pos):
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)
        self.setPos(pos)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.parent_line and not self.parent_line._moving:
                old_center = self.parent_line._drag_center
                new_center = value
                delta = new_center - old_center
                snapped = QPointF(round(new_center.x() / GRID_SIZE) * GRID_SIZE,
                                  round(new_center.y() / GRID_SIZE) * GRID_SIZE)
                final_delta = snapped - old_center
                self.parent_line.translate_by(final_delta)
                return self.pos()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_line._drag_center = self.parent_line.line().center()
        super().mousePressEvent(event)


# ====================== СТРЕЛОЧНАЯ ЛИНИЯ (ОРИГИНАЛЬНАЯ) ======================
class ArrowLine(QGraphicsLineItem):
    """Линия со стрелкой и полным набором ручек."""
    def __init__(self, start_point, end_point):
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPen(QPen(Qt.GlobalColor.black, 1.5))
        self.setLine(QLineF(start_point, end_point))
        self.setZValue(1)

        self.start_handle = LineEndpointHandle(self, 0)
        self.end_handle = LineEndpointHandle(self, 1)
        self.center_handle = CenterHandle(self)
        self.handles = [self.start_handle, self.end_handle, self.center_handle]
        for h in self.handles:
            h.setVisible(False)

        self._moving = False
        self._drag_center = None
        self._update_handle_positions()

    def _update_handle_positions(self):
        line = self.line()
        self.start_handle.setPosSilent(line.p1())
        self.end_handle.setPosSilent(line.p2())
        self.center_handle.setPosSilent(line.center())

    def translate_by(self, delta: QPointF):
        line = self.line()
        new_line = QLineF(line.p1() + delta, line.p2() + delta)
        self.setLine(new_line)
        self._update_handle_positions()

    def update_endpoint(self, index, new_local_pos: QPointF):
        line = self.line()
        snapped = QPointF(round(new_local_pos.x() / GRID_SIZE) * GRID_SIZE,
                          round(new_local_pos.y() / GRID_SIZE) * GRID_SIZE)
        snapped = self._snap_to_nearby_figures(snapped, index)

        if index == 0:
            new_line = QLineF(snapped, line.p2())
        else:
            new_line = QLineF(line.p1(), snapped)

        if new_line.length() < MIN_LINE_LENGTH:
            return

        self.setLine(new_line)
        self._update_handle_positions()

    def _snap_to_nearby_figures(self, point: QPointF, exclude_index: int) -> QPointF:
        scene = self.scene()
        if not scene:
            return point
        scene_point = point
        items = scene.items(scene_point, Qt.ItemSelectionMode.IntersectsItemShape,
                            Qt.SortOrder.DescendingOrder, QTransform())
        for item in items:
            if isinstance(item, FlowchartItem):
                center = item.mapToScene(item.boundingRect().center())
                if QLineF(scene_point, center).length() <= SNAP_DISTANCE:
                    return center
        return point

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            for h in self.handles:
                h.setVisible(bool(value))
            if value:
                self._update_handle_positions()
        return super().itemChange(change, value)

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        line = self.line()
        if line.length() == 0:
            return
        pen = self.pen()
        painter.setPen(pen)
        painter.setBrush(QBrush(pen.color()))
        angle = math.atan2(-line.dy(), line.dx())
        arrow_size = 12
        p2 = line.p2()
        arrow_p1 = p2 - QPointF(
            arrow_size * math.cos(angle - math.pi / 6),
            -arrow_size * math.sin(angle - math.pi / 6)
        )
        arrow_p2 = p2 - QPointF(
            arrow_size * math.cos(angle + math.pi / 6),
            -arrow_size * math.sin(angle + math.pi / 6)
        )
        painter.drawPolygon(QPolygonF([p2, arrow_p1, arrow_p2]), Qt.FillRule.WindingFill)


# ====================== БАЗОВЫЙ КЛАСС ЛИНИЙ ======================
class BaseLine(QGraphicsLineItem):
    """Общая логика для всех типов линий (сплошная, пунктирная, со стрелкой или без)."""

    def __init__(self, start_point, end_point, has_arrow=False, pen_style=Qt.PenStyle.SolidLine):
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPen(QPen(Qt.GlobalColor.black, 1.5, pen_style))
        self.setLine(QLineF(start_point, end_point))
        self.setZValue(1)

        self.has_arrow = has_arrow
        self.pen_style = pen_style

        self.start_handle = LineEndpointHandle(self, 0)
        self.end_handle = LineEndpointHandle(self, 1)
        self.center_handle = CenterHandle(self)
        self.handles = [self.start_handle, self.end_handle, self.center_handle]
        for h in self.handles:
            h.setVisible(False)

        self._moving = False
        self._drag_center = None
        self._update_handle_positions()

    def _update_handle_positions(self):
        line = self.line()
        self.start_handle.setPosSilent(line.p1())
        self.end_handle.setPosSilent(line.p2())
        self.center_handle.setPosSilent(line.center())

    def translate_by(self, delta: QPointF):
        line = self.line()
        new_line = QLineF(line.p1() + delta, line.p2() + delta)
        self.setLine(new_line)
        self._update_handle_positions()

    def update_endpoint(self, index, new_local_pos: QPointF):
        line = self.line()
        snapped = QPointF(round(new_local_pos.x() / GRID_SIZE) * GRID_SIZE,
                          round(new_local_pos.y() / GRID_SIZE) * GRID_SIZE)
        snapped = self._snap_to_nearby_figures(snapped, index)

        if index == 0:
            new_line = QLineF(snapped, line.p2())
        else:
            new_line = QLineF(line.p1(), snapped)

        if new_line.length() < MIN_LINE_LENGTH:
            return

        self.setLine(new_line)
        self._update_handle_positions()

    def _snap_to_nearby_figures(self, point: QPointF, exclude_index: int) -> QPointF:
        scene = self.scene()
        if not scene:
            return point
        scene_point = point
        items = scene.items(scene_point, Qt.ItemSelectionMode.IntersectsItemShape,
                            Qt.SortOrder.DescendingOrder, QTransform())
        for item in items:
            if isinstance(item, FlowchartItem):
                center = item.mapToScene(item.boundingRect().center())
                if QLineF(scene_point, center).length() <= SNAP_DISTANCE:
                    return center
        return point

    def set_line_style(self, pen_style: Qt.PenStyle):
        pen = self.pen()
        pen.setStyle(pen_style)
        self.setPen(pen)
        self.pen_style = pen_style

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            for h in self.handles:
                h.setVisible(bool(value))
            if value:
                self._update_handle_positions()
        return super().itemChange(change, value)

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if not self.has_arrow:
            return
        line = self.line()
        if line.length() == 0:
            return
        pen = self.pen()
        painter.setPen(pen)
        painter.setBrush(QBrush(pen.color()))
        angle = math.atan2(-line.dy(), line.dx())
        arrow_size = 12
        p2 = line.p2()
        arrow_p1 = p2 - QPointF(
            arrow_size * math.cos(angle - math.pi / 6),
            -arrow_size * math.sin(angle - math.pi / 6)
        )
        arrow_p2 = p2 - QPointF(
            arrow_size * math.cos(angle + math.pi / 6),
            -arrow_size * math.sin(angle + math.pi / 6)
        )
        painter.drawPolygon(QPolygonF([p2, arrow_p1, arrow_p2]), Qt.FillRule.WindingFill)


# ====================== КОНКРЕТНЫЕ ТИПЫ ЛИНИЙ ======================
class SimpleLine(BaseLine):
    """Сплошная линия без стрелки."""
    def __init__(self, start_point, end_point):
        super().__init__(start_point, end_point,
                         has_arrow=False, pen_style=Qt.PenStyle.SolidLine)


class DashedLine(BaseLine):
    """Пунктирная линия без стрелки."""
    def __init__(self, start_point, end_point):
        super().__init__(start_point, end_point,
                         has_arrow=False, pen_style=Qt.PenStyle.DashLine)


class DashedArrowLine(BaseLine):
    """Пунктирная линия со стрелкой."""
    def __init__(self, start_point, end_point):
        super().__init__(start_point, end_point,
                         has_arrow=True, pen_style=Qt.PenStyle.DashLine)