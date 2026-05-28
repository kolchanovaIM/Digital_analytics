from __future__ import annotations

import math
from typing import Optional, TYPE_CHECKING
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF, QFont
from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsSimpleTextItem

if TYPE_CHECKING:
    from flowchart_items_2 import FlowchartItem


class BaseLine(QGraphicsPathItem):
    def __init__(self, source_item: FlowchartItem, target_item: FlowchartItem, label: str = "",
                 is_back_edge: bool = False, parent=None):
        super().__init__(parent)
        self.source_item = source_item
        self.target_item = target_item
        self.label = label
        self.is_back_edge = is_back_edge

        self._label_item = QGraphicsSimpleTextItem(self.label, self)
        self._label_item.setBrush(QBrush(QColor("#2E4350")))
        self._label_item.setVisible(bool(self.label))

        self._pen = QPen(QColor("#3D5665"), 2)
        self._pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self._pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        if self.is_back_edge:
            self._pen.setStyle(Qt.PenStyle.DashLine)

        self.setZValue(-1)
        self.setFlags(QGraphicsPathItem.GraphicsItemFlag.ItemIsSelectable)

        self.source_item.register_line(self)
        self.target_item.register_line(self)
        self.update_path()

    def update_path(self) -> None:
        """Построение излома линии связи (умные ортогональные связи)."""
        p1 = self.source_item.connection_point_towards(self.target_item.sceneBoundingRect().center())
        p2 = self.target_item.connection_point_towards(self.source_item.sceneBoundingRect().center())

        path = QPainterPath(p1)
        if abs(p1.x() - p2.x()) > 20 and abs(p1.y() - p2.y()) > 20:
            path.lineTo(p1.x(), p2.y())
        path.lineTo(p2)

        self.prepareGeometryChange()
        self.setPath(path)
        if self.label:
            self._label_item.setPos(path.pointAtPercent(0.5) + QPointF(8, -15))

    def paint(self, painter: QPainter, option, widget=None) -> None:
        pen = QPen(self._pen)
        if self.isSelected():
            pen.setColor(QColor("#1F6FB2"))
            pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())
        self._paint_arrow(painter, pen)

    def _paint_arrow(self, painter: QPainter, pen: QPen) -> None:
        """Отрисовка наконечника стрелки на конце пути линии."""
        p1 = self.path().pointAtPercent(0.95)
        p2 = self.path().pointAtPercent(1.0)
        angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
        arrow_size = 12

        p_left = QPointF(
            p2.x() - arrow_size * math.cos(angle - math.pi / 6),
            p2.y() - arrow_size * math.sin(angle - math.pi / 6),
        )
        p_right = QPointF(
            p2.x() - arrow_size * math.cos(angle + math.pi / 6),
            p2.y() - arrow_size * math.sin(angle + math.pi / 6),
        )
        painter.setBrush(QBrush(pen.color()))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(QPolygonF([p2, p_left, p_right]))

    def update_from_items(self) -> None:
        self.update_path()


class ArrowLine(BaseLine):

    def __init__(
            self,
            source_item,
            target_item,
            label="",
            is_back_edge=False,
            parent=None
    ):

        # СНАЧАЛА создаём атрибут
        self.custom_path = None

        # ПОТОМ вызываем BaseLine
        super().__init__(
            source_item,
            target_item,
            label,
            is_back_edge,
            parent
        )

    def boundingRect(self):

        rect = super().boundingRect()

        return rect.adjusted(-40, -40, 40, 40)

    def set_path_points(self, points):

        self.custom_path = points

        self.update_path()

    def update_path(self):

        path = QPainterPath()

        # =====================================
        # CUSTOM PATH (ЦИКЛ)
        # =====================================

        if self.custom_path and len(self.custom_path) > 1:

            path.moveTo(self.custom_path[0])

            for pt in self.custom_path[1:]:
                path.lineTo(pt)

        # =====================================
        # ОБЫЧНАЯ СТРЕЛКА
        # =====================================

        else:

            src_rect = self.source_item.sceneBoundingRect()
            tgt_rect = self.target_item.sceneBoundingRect()

            src_center = src_rect.center()
            tgt_center = tgt_rect.center()

            # ВНИЗ
            if tgt_center.y() > src_center.y():

                start_point = QPointF(
                    src_center.x(),
                    src_rect.bottom()
                )

                end_point = QPointF(
                    tgt_center.x(),
                    tgt_rect.top()
                )

            # ВВЕРХ
            elif tgt_center.y() < src_center.y():

                start_point = QPointF(
                    src_center.x(),
                    src_rect.top()
                )

                end_point = QPointF(
                    tgt_center.x(),
                    tgt_rect.bottom()
                )

            # ГОРИЗОНТАЛЬНО
            else:

                if tgt_center.x() > src_center.x():

                    start_point = QPointF(
                        src_rect.right(),
                        src_center.y()
                    )

                    end_point = QPointF(
                        tgt_rect.left(),
                        tgt_center.y()
                    )

                else:

                    start_point = QPointF(
                        src_rect.left(),
                        src_center.y()
                    )

                    end_point = QPointF(
                        tgt_rect.right(),
                        tgt_center.y()
                    )

            path.moveTo(start_point)

            dx = abs(start_point.x() - end_point.x())
            dy = abs(start_point.y() - end_point.y())

            # Ортогональный маршрут
            if dx > 20 and dy > 20:
                mid_y = (start_point.y() + end_point.y()) / 2

                path.lineTo(start_point.x(), mid_y)
                path.lineTo(end_point.x(), mid_y)

            path.lineTo(end_point)

        self.prepareGeometryChange()

        self.setPath(path)

        # =====================================
        # LABEL
        # =====================================

        if self.label:

            center_pt = path.pointAtPercent(0.5)

            self._label_item.setText(str(self.label))

            self._label_item.setPos(
                center_pt + QPointF(10, -10)
            )

            self._label_item.setVisible(True)

        else:

            self._label_item.setVisible(False)