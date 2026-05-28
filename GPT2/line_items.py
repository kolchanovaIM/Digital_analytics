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
        self._my_label = label

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
        print(f"UPDATE_PATH CALLED: label = '{self.label}'")

        """Построение излома линии связи (умные ортогональные связи)."""

        # Если задан кастомный путь (для обратных стрелок)
        if hasattr(self, 'custom_path') and self.custom_path and len(self.custom_path) > 1:
            path = QPainterPath()
            path.moveTo(self.custom_path[0])
            for pt in self.custom_path[1:]:
                path.lineTo(pt)
            self.setPath(path)
            if self.label and len(self.custom_path) > 2:
                mid_index = len(self.custom_path) // 2
                center_pt = self.custom_path[mid_index]
                self._label_item.setPos(center_pt + QPointF(10, -10))
                self._label_item.setVisible(True)
            return

        # Получаем границы блоков
        src_rect = self.source_item.sceneBoundingRect()
        tgt_rect = self.target_item.sceneBoundingRect()
        src_center = src_rect.center()
        tgt_center = tgt_rect.center()

        # Определяем направление и точки подключения
        path = QPainterPath()

        # ВЕТКА "ДА" (всегда справа от ромба)
        if self.label == "да":
            # Стрелка выходит из правой грани ромба
            start_point = QPointF(src_rect.right(), src_center.y())
            # Входит в левую грань целевого блока
            end_point = QPointF(tgt_rect.left(), tgt_center.y())

            path.moveTo(start_point)
            # Ортогональный маршрут: вправо → вниз/вверх → влево
            mid_x = (src_rect.right() + tgt_rect.left()) / 2
            path.lineTo(mid_x, start_point.y())
            path.lineTo(mid_x, end_point.y())
            path.lineTo(end_point)

        # ВЕТКА "НЕТ" (всегда слева от ромба)
        elif self.label == "нет":
            # Стрелка выходит из левой грани ромба
            start_point = QPointF(src_rect.left(), src_center.y())
            # Входит в правую грань целевого блока
            end_point = QPointF(tgt_rect.right(), tgt_center.y())

            path.moveTo(start_point)
            # Ортогональный маршрут: влево → вниз/вверх → вправо
            mid_x = (src_rect.left() + tgt_rect.right()) / 2
            path.lineTo(mid_x, start_point.y())
            path.lineTo(mid_x, end_point.y())
            path.lineTo(end_point)

        # ОБЫЧНАЯ СТРЕЛКА (без явной метки)
        else:
            # Определяем направление по положению целевого блока
            if tgt_center.y() > src_center.y():
                # Цель снизу
                start_point = QPointF(src_center.x(), src_rect.bottom())
                end_point = QPointF(tgt_center.x(), tgt_rect.top())

                path.moveTo(start_point)
                if abs(start_point.x() - end_point.x()) > 20:
                    mid_y = (start_point.y() + end_point.y()) / 2
                    path.lineTo(start_point.x(), mid_y)
                    path.lineTo(end_point.x(), mid_y)
                path.lineTo(end_point)

            elif tgt_center.y() < src_center.y():
                # Цель сверху
                start_point = QPointF(src_center.x(), src_rect.top())
                end_point = QPointF(tgt_center.x(), tgt_rect.bottom())

                path.moveTo(start_point)
                if abs(start_point.x() - end_point.x()) > 20:
                    mid_y = (start_point.y() + end_point.y()) / 2
                    path.lineTo(start_point.x(), mid_y)
                    path.lineTo(end_point.x(), mid_y)
                path.lineTo(end_point)

            else:
                # Горизонтальное расположение
                if tgt_center.x() > src_center.x():
                    start_point = QPointF(src_rect.right(), src_center.y())
                    end_point = QPointF(tgt_rect.left(), tgt_center.y())
                else:
                    start_point = QPointF(src_rect.left(), src_center.y())
                    end_point = QPointF(tgt_rect.right(), tgt_center.y())

                path.moveTo(start_point)
                path.lineTo(end_point)

        self.prepareGeometryChange()
        self.setPath(path)

        # Обновляем позицию метки
        if self.label:
            center_pt = path.pointAtPercent(0.5)
            self._label_item.setPos(center_pt + QPointF(8, -15))
            self._label_item.setVisible(True)
        else:
            self._label_item.setVisible(False)

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

    def update_from_items(self):
        # Если это обратная стрелка с кастомным путём — не пересчитываем
        if hasattr(self, 'custom_path') and self.custom_path:
            return
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

    def update_path(self) -> None:
        print(f"UPDATE_PATH CALLED: label = '{self.label}'")

        """Построение излома линии связи (умные ортогональные связи)."""

        # Если задан кастомный путь (для обратных стрелок)
        if hasattr(self, 'custom_path') and self.custom_path and len(self.custom_path) > 1:
            path = QPainterPath()
            path.moveTo(self.custom_path[0])
            for pt in self.custom_path[1:]:
                path.lineTo(pt)
            self.setPath(path)
            if self.label and len(self.custom_path) > 2:
                mid_index = len(self.custom_path) // 2
                center_pt = self.custom_path[mid_index]
                self._label_item.setPos(center_pt + QPointF(10, -10))
                self._label_item.setVisible(True)
            return

        # Получаем границы блоков
        src_rect = self.source_item.sceneBoundingRect()
        tgt_rect = self.target_item.sceneBoundingRect()
        src_center = src_rect.center()
        tgt_center = tgt_rect.center()

        # Определяем направление и точки подключения
        path = QPainterPath()

        # ВЕТКА "ДА" (всегда справа от ромба)
        if self.label == "да":
            # Стрелка выходит из правой грани ромба
            start_point = QPointF(src_rect.right(), src_center.y())
            # Входит в левую грань целевого блока
            end_point = QPointF(tgt_rect.left(), tgt_center.y())

            path.moveTo(start_point)
            # Ортогональный маршрут: вправо → вниз/вверх → влево
            mid_x = (src_rect.right() + tgt_rect.left()) / 2
            path.lineTo(mid_x, start_point.y())
            path.lineTo(mid_x, end_point.y())
            path.lineTo(end_point)

        # ВЕТКА "НЕТ" (всегда слева от ромба)
        elif self.label == "нет":
            # Стрелка выходит из левой грани ромба
            start_point = QPointF(src_rect.left(), src_center.y())
            # Входит в правую грань целевого блока
            end_point = QPointF(tgt_rect.right(), tgt_center.y())

            path.moveTo(start_point)
            # Ортогональный маршрут: влево → вниз/вверх → вправо
            mid_x = (src_rect.left() + tgt_rect.right()) / 2
            path.lineTo(mid_x, start_point.y())
            path.lineTo(mid_x, end_point.y())
            path.lineTo(end_point)

        # ОБЫЧНАЯ СТРЕЛКА (без явной метки)
        else:
            # Определяем направление по положению целевого блока
            if tgt_center.y() > src_center.y():
                # Цель снизу
                start_point = QPointF(src_center.x(), src_rect.bottom())
                end_point = QPointF(tgt_center.x(), tgt_rect.top())

                path.moveTo(start_point)
                if abs(start_point.x() - end_point.x()) > 20:
                    mid_y = (start_point.y() + end_point.y()) / 2
                    path.lineTo(start_point.x(), mid_y)
                    path.lineTo(end_point.x(), mid_y)
                path.lineTo(end_point)

            elif tgt_center.y() < src_center.y():
                # Цель сверху
                start_point = QPointF(src_center.x(), src_rect.top())
                end_point = QPointF(tgt_center.x(), tgt_rect.bottom())

                path.moveTo(start_point)
                if abs(start_point.x() - end_point.x()) > 20:
                    mid_y = (start_point.y() + end_point.y()) / 2
                    path.lineTo(start_point.x(), mid_y)
                    path.lineTo(end_point.x(), mid_y)
                path.lineTo(end_point)

            else:
                # Горизонтальное расположение
                if tgt_center.x() > src_center.x():
                    start_point = QPointF(src_rect.right(), src_center.y())
                    end_point = QPointF(tgt_rect.left(), tgt_center.y())
                else:
                    start_point = QPointF(src_rect.left(), src_center.y())
                    end_point = QPointF(tgt_rect.right(), tgt_center.y())

                path.moveTo(start_point)
                path.lineTo(end_point)

        self.prepareGeometryChange()
        self.setPath(path)

        # Обновляем позицию метки
        if self.label:
            center_pt = path.pointAtPercent(0.5)
            self._label_item.setPos(center_pt + QPointF(8, -15))
            self._label_item.setVisible(True)
        else:
            self._label_item.setVisible(False)

    def set_path_points(self, points):
        """Устанавливает кастомный путь из списка точек."""
        self.custom_path = points
        self.update_path()

    def update_back_edge_path(self):
        """Пересчитывает обходной путь для обратной стрелки при перемещении блоков."""
        if not self.custom_path:
            return

        # Пересчитываем точки на основе новых позиций блоков
        src_rect = self.source_item.sceneBoundingRect()
        tgt_rect = self.target_item.sceneBoundingRect()

        start_pos = QPointF(src_rect.center().x(), src_rect.bottom())
        end_pos = QPointF(tgt_rect.center().x(), tgt_rect.top())

        max_width = max(src_rect.width(), tgt_rect.width())
        offset_x = max_width + 50

        self.custom_path = [
            start_pos,
            QPointF(start_pos.x(), start_pos.y() + 30),
            QPointF(start_pos.x() + offset_x, start_pos.y() + 30),
            QPointF(end_pos.x() + offset_x, end_pos.y() - 30),
            QPointF(end_pos.x(), end_pos.y() - 30),
            end_pos
        ]

        self.update_path()