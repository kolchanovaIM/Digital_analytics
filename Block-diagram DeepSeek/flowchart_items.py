# flowchart_items.py — фигуры без текста по умолчанию, текст добавляется пользователем
import math
from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem, QGraphicsRectItem
)
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QColor, QBrush, QPainterPath, QPen, QPolygonF, QFont, QFontMetrics
)
from constants import GRID_SIZE, MIN_SIZE


class FlowchartItem(QGraphicsPathItem):
    def __init__(self, shape_type, rect=QRectF(0, 0, 120, 60)):
        super().__init__()
        self.shape_type = shape_type
        self._resizing = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setPen(QPen(Qt.GlobalColor.black, 1.5))
        self.setBrush(QBrush(QColor("#E6E6E6")))

        self.current_rect = rect
        self._create_path(self.current_rect)

        # Текст — изначально пустой, пользователь добавит двойным кликом
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setPlainText("")  # Пустая строка вместо названия типа
        self.text_item.setDefaultTextColor(Qt.GlobalColor.black)
        self._center_text()
        # Запрещаем редактирование до двойного клика
        self.text_item.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self.handles = []
        self._create_handles()

        self._adjusting_font = False
        self.text_item.document().contentsChanged.connect(self._on_text_changed)
        # Шрифт по умолчанию
        self.text_item.setFont(QFont("Arial", 11))

    def _create_path(self, rect):
        path = QPainterPath()
        w, h = rect.width(), rect.height()
        if self.shape_type == 'process':
            path.addRect(rect)
        elif self.shape_type == 'decision':
            poly = QPolygonF([
                QPointF(rect.center().x(), rect.top()),
                QPointF(rect.right(), rect.center().y()),
                QPointF(rect.center().x(), rect.bottom()),
                QPointF(rect.left(), rect.center().y())
            ])
            path.addPolygon(poly)
            path.closeSubpath()
        elif self.shape_type == 'startend':
            path.addEllipse(rect)
        elif self.shape_type == 'io':
            skew = 20
            poly = QPolygonF([
                QPointF(rect.left() + skew, rect.top()),
                QPointF(rect.right(), rect.top()),
                QPointF(rect.right() - skew, rect.bottom()),
                QPointF(rect.left(), rect.bottom())
            ])
            path.addPolygon(poly)
            path.closeSubpath()
        elif self.shape_type == 'loop':
            d = w * 0.3
            poly = QPolygonF([
                QPointF(rect.left() + d, rect.top()),
                QPointF(rect.right() - d, rect.top()),
                QPointF(rect.right(), rect.center().y()),
                QPointF(rect.right() - d, rect.bottom()),
                QPointF(rect.left() + d, rect.bottom()),
                QPointF(rect.left(), rect.center().y())
            ])
            path.addPolygon(poly)
            path.closeSubpath()
        elif self.shape_type == 'function':
            path.addRect(rect)
            x_left = rect.left() + w * 0.2
            x_right = rect.right() - w * 0.2
            path.moveTo(x_left, rect.top())
            path.lineTo(x_left, rect.bottom())
            path.moveTo(x_right, rect.top())
            path.lineTo(x_right, rect.bottom())
        elif self.shape_type == 'semicircle':
            path.moveTo(rect.left(), rect.bottom())
            path.lineTo(rect.right(), rect.bottom())
            path.lineTo(rect.right(), rect.center().y())
            path.arcTo(rect, 0, 180)
            path.lineTo(rect.left(), rect.bottom())
            path.closeSubpath()
        elif self.shape_type == 'inverted_semicircle':
            path.moveTo(rect.left(), rect.top())
            path.lineTo(rect.right(), rect.top())
            path.lineTo(rect.right(), rect.center().y())
            path.arcTo(rect, 0, -180)
            path.lineTo(rect.left(), rect.top())
            path.closeSubpath()
        elif self.shape_type == 'inverted_trapezoid':
            poly = QPolygonF([
                QPointF(rect.left(), rect.top()),
                QPointF(rect.right(), rect.top()),
                QPointF(rect.right() - w * 0.2, rect.bottom()),
                QPointF(rect.left() + w * 0.2, rect.bottom())
            ])
            path.addPolygon(poly)
            path.closeSubpath()
        elif self.shape_type == 'elongated_oval':
            path.addRoundedRect(rect, 15, 15)
        else:
            path.addRect(rect)
        self.setPath(path)

    def _center_text(self):
        rect = self.current_rect
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(
            rect.center().x() - text_rect.width() / 2,
            rect.center().y() - text_rect.height() / 2
        )

    def _on_text_changed(self):
        if self._adjusting_font:
            return
        self._adjust_font_size()
        self._center_text()

    def _adjust_font_size(self):
        if self._adjusting_font:
            return
        self._adjusting_font = True
        rect = self.current_rect
        text = self.text_item.toPlainText()
        if not text:
            self._adjusting_font = False
            return
        margin = 10.0
        available_w = rect.width() - 2 * margin
        available_h = rect.height() - 2 * margin
        if available_w <= 0 or available_h <= 0:
            self._adjusting_font = False
            return
        font = self.text_item.font()
        for size in range(24, 5, -1):
            font.setPointSize(size)
            fm = QFontMetrics(font)
            text_rect = fm.boundingRect(
                QRectF(0, 0, available_w, 10000).toRect(),
                Qt.TextFlag.TextWordWrap, text
            )
            if text_rect.width() <= available_w and text_rect.height() <= available_h:
                self.text_item.setFont(font)
                break
        else:
            font.setPointSize(6)
            self.text_item.setFont(font)
        self._adjusting_font = False

    def _create_handles(self):
        for i in range(4):
            handle = HandleItem(self, i)
            self.handles.append(handle)
        self._update_handle_positions()

    def _update_handle_positions(self):
        rect = self.current_rect
        corners = [rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()]
        for h, pos in zip(self.handles, corners):
            h.setPosSilent(pos)

    def resize_by_handle(self, handle_index, local_pos):
        if self._resizing:
            return
        self._resizing = True

        new_rect = QRectF(self.current_rect)
        snapped = QPointF(round(local_pos.x() / GRID_SIZE) * GRID_SIZE,
                          round(local_pos.y() / GRID_SIZE) * GRID_SIZE)

        if handle_index == 0:
            new_rect.setTopLeft(snapped)
        elif handle_index == 1:
            new_rect.setTopRight(snapped)
        elif handle_index == 2:
            new_rect.setBottomRight(snapped)
        elif handle_index == 3:
            new_rect.setBottomLeft(snapped)

        if new_rect.width() >= MIN_SIZE and new_rect.height() >= MIN_SIZE:
            self.prepareGeometryChange()
            self.current_rect = new_rect
            self._create_path(new_rect)
            self._update_handle_positions()
            self._center_text()
            self._adjust_font_size()

        self._resizing = False

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            for h in self.handles:
                h.setVisible(bool(value))
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._update_handle_positions()
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        pos = self.pos()
        snapped_x = round(pos.x() / GRID_SIZE) * GRID_SIZE
        snapped_y = round(pos.y() / GRID_SIZE) * GRID_SIZE
        self.setPos(snapped_x, snapped_y)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        # Разрешаем редактирование текста при двойном клике
        self.text_item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.text_item.setFocus()
        # Не устанавливаем текст — пользователь вводит свой
        super().mouseDoubleClickEvent(event)


class HandleItem(QGraphicsRectItem):
    """Ручка для изменения размера фигур."""
    def __init__(self, parent_flowchart, index):
        super().__init__(-5, -5, 10, 10, parent_flowchart)
        self.parent_item = parent_flowchart
        self.index = index
        self.setPen(QPen(QColor("#0078D7"), 1.5))
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
            if self.parent_item and not self.parent_item._resizing:
                self.parent_item.resize_by_handle(self.index, value)
            return self.pos()
        return super().itemChange(change, value)