from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPainterPath, QPolygonF, QFontMetrics
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsSceneMouseEvent
import math
from constants import (
    DEFAULT_ITEM_HEIGHT,
    DEFAULT_ITEM_WIDTH,
    DECISION_COLOR,
    HANDLE_COLOR,
    IO_COLOR,
    PROCESS_COLOR,
    TERMINAL_COLOR,
)

if TYPE_CHECKING:
    from line_items import BaseLine

HANDLE_SIZE = 8


class ResizeHandle(QGraphicsRectItem):
    def __init__(self, parent: FlowchartItem, corner: int):
        super().__init__(-HANDLE_SIZE / 2, -HANDLE_SIZE / 2, HANDLE_SIZE, HANDLE_SIZE, parent)
        self.parent_item = parent
        self.corner = corner
        self.setBrush(QBrush(QColor(HANDLE_COLOR)))
        self.setPen(QPen(QColor(HANDLE_COLOR)))
        self.setCursor(self._cursor_for_corner(corner))
        self.setZValue(20)
        self.setVisible(False)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

    def mousePressEvent(self, event):
        self._drag_start = event.scenePos()
        self._start_rect = self.parent_item.rect
        self._start_pos = self.parent_item.pos()
        event.accept()

    def mouseMoveEvent(self, event):
        delta = event.scenePos() - self._drag_start
        self.parent_item.resize_from_corner(self.corner, self._start_rect, self._start_pos, delta)
        event.accept()

    def _cursor_for_corner(self, corner: int):
        return {
            0: Qt.CursorShape.SizeFDiagCursor, 1: Qt.CursorShape.SizeVerCursor,
            2: Qt.CursorShape.SizeBDiagCursor, 3: Qt.CursorShape.SizeHorCursor,
            4: Qt.CursorShape.SizeFDiagCursor, 5: Qt.CursorShape.SizeVerCursor,
            6: Qt.CursorShape.SizeBDiagCursor, 7: Qt.CursorShape.SizeHorCursor,
        }.get(corner, Qt.CursorShape.ArrowCursor)


class FlowchartItem(QGraphicsItem):
    def __init__(self, text: str, shape_type: str = "process", parent=None):
        super().__init__(parent)
        self.text = text
        # Переводим в нижний регистр для безопасного сравнения по ГОСТу
        self.shape_type = shape_type.lower() if shape_type else "process"

        # Базовые размеры блока по умолчанию
        self.width = 140
        self.height = 80
        self.rect = QRectF(0, 0, self.width, self.height)
        self._lines: list[BaseLine] = []

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self.font = QFont("Arial", 10)

        # Инициализация интерактивных ручек изменения размера
        self._handles: list[ResizeHandle] = []
        self._init_handles()

    def _init_handles(self):
        """Создает 8 ручек по периметру элемента."""
        for corner in range(8):
            handle = ResizeHandle(self, corner)
            self._handles.append(handle)

    def boundingRect(self) -> QRectF:
        return self.rect.adjusted(-10, -10, 10, 10)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        W = self.rect.width()
        H = self.rect.height()
        left = self.rect.left()
        right = self.rect.right()
        top = self.rect.top()
        bottom = self.rect.bottom()
        cx = self.rect.center().x()
        cy = self.rect.center().y()

        # Мапинг точной геометрической формы по ГОСТ 19.701-90 для кликов мыши
        if self.shape_type in ["decision", "if", "условие", "если"]:
            points = [QPointF(cx, top), QPointF(right, cy), QPointF(cx, bottom), QPointF(left, cy)]
            path.addPolygon(QPolygonF(points))
        elif self.shape_type in ["io", "input", "output", "ввод", "вывод"]:
            skew = 20
            points = [QPointF(left + skew, top), QPointF(right, top), QPointF(right - skew, bottom),
                      QPointF(left, bottom)]
            path.addPolygon(QPolygonF(points))
        elif self.shape_type in ["terminal", "start", "end", "rounded_rect", "начало", "конец"]:
            r = H / 2 if self.shape_type in ["terminal", "start", "end", "начало", "конец"] else 12
            path.addRoundedRect(self.rect, r, r)
        elif self.shape_type in ["preparation", "подготовка", "hexagon"]:
            indent = 20
            points = [QPointF(left + indent, top), QPointF(right - indent, top), QPointF(right, cy),
                      QPointF(right - indent, bottom), QPointF(left + indent, bottom), QPointF(left, cy)]
            path.addPolygon(QPolygonF(points))
        elif self.shape_type in ["loop_start", "граница_цикла_начало"]:
            indent = 15
            points = [QPointF(left, top), QPointF(right, top), QPointF(right, bottom - indent),
                      QPointF(right - indent, bottom), QPointF(left + indent, bottom), QPointF(left, bottom - indent)]
            path.addPolygon(QPolygonF(points))
        elif self.shape_type in ["loop_end", "граница_цикла_конец"]:
            indent = 15
            points = [QPointF(left + indent, top), QPointF(right - indent, top), QPointF(right, top + indent),
                      QPointF(right, bottom), QPointF(left, bottom), QPointF(left, top + indent)]
            path.addPolygon(QPolygonF(points))
        elif self.shape_type in ["connector", "соединитель", "circle"]:
            path.addEllipse(self.rect)
        else:
            path.addRect(self.rect)
        return path

    def background_color(self) -> str:
        if self.shape_type in ["decision", "if", "условие", "если"]:
            return DECISION_COLOR
        elif self.shape_type in ["io", "input", "output", "ввод", "вывод"]:
            return IO_COLOR
        elif self.shape_type in ["terminal", "start", "end", "начало", "конец"]:
            return TERMINAL_COLOR
        return PROCESS_COLOR

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Гарантируем, что shape_type в нижнем регистре без лишних пробелов для точного сравнения
        shape_type_lower = str(self.shape_type).strip().lower() if self.shape_type else "process"

        # Стилизация пера по ГОСТ
        pen = QPen(QColor("#38505B"), 2)
        if self.isSelected():
            pen.setColor(QColor("#1F6FB2"))
            pen.setWidth(3)
        if shape_type_lower in ["comment", "комментарий"]:
            pen.setStyle(Qt.PenStyle.DashLine)

        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(self.background_color())))

        W = self.rect.width()
        H = self.rect.height()
        left = self.rect.left()
        right = self.rect.right()
        top = self.rect.top()
        bottom = self.rect.bottom()
        cx = self.rect.center().x()
        cy = self.rect.center().y()

        # --- ОТРИСОВКА ГЕОМЕТРИИ ПО ТЗ И ГОСТ ---
        if shape_type_lower in ["start", "end", "terminal", "начало", "конец"]:
            painter.drawRoundedRect(self.rect, H / 2, H / 2)

        elif shape_type_lower in ["io", "input", "output", "ввод", "вывод"]:
            skew = 20
            points = [QPointF(left + skew, top), QPointF(right, top), QPointF(right - skew, bottom),
                      QPointF(left, bottom)]
            painter.drawPolygon(QPolygonF(points))

        elif shape_type_lower in ["decision", "if", "условие", "если"]:
            points = [QPointF(cx, top), QPointF(right, cy), QPointF(cx, bottom), QPointF(left, cy)]
            painter.drawPolygon(QPolygonF(points))

        elif shape_type_lower in ["subroutine", "function", "procedure", "подпрограмма", "функция", "процедура",
                                  "double_rect"]:
            painter.drawRect(self.rect)
            indent = 15
            painter.drawLine(QPointF(left + indent, top), QPointF(left + indent, bottom))
            painter.drawLine(QPointF(right - indent, top), QPointF(right - indent, bottom))

        elif shape_type_lower in ["preparation", "подготовка", "hexagon"]:
            indent = 20
            points = [QPointF(left + indent, top), QPointF(right - indent, top), QPointF(right, cy),
                      QPointF(right - indent, bottom), QPointF(left + indent, bottom), QPointF(left, cy)]
            painter.drawPolygon(QPolygonF(points))

        elif shape_type_lower in ["parallel", "параллельно"]:
            painter.drawRect(self.rect)
            painter.drawLine(QPointF(left, top + 6), QPointF(right, top + 6))
            painter.drawLine(QPointF(left, bottom - 6), QPointF(right, bottom - 6))

        elif shape_type_lower in ["loop_start", "граница_цикла_начало"]:
            indent = 15
            points = [QPointF(left, top), QPointF(right, top), QPointF(right, bottom - indent),
                      QPointF(right - indent, bottom), QPointF(left + indent, bottom), QPointF(left, bottom - indent)]
            painter.drawPolygon(QPolygonF(points))

        elif shape_type_lower in ["loop_end", "граница_цикла_конец"]:
            indent = 15
            points = [QPointF(left + indent, top), QPointF(right - indent, top), QPointF(right, top + indent),
                      QPointF(right, bottom), QPointF(left, bottom), QPointF(left, top + indent)]
            painter.drawPolygon(QPolygonF(points))

        elif shape_type_lower in ["connector", "соединитель", "circle"]:
            painter.drawEllipse(self.rect)

        elif shape_type_lower in ["comment", "комментарий"]:
            path = QPainterPath()
            path.moveTo(right, top)
            path.lineTo(left, top)
            path.lineTo(left, bottom)
            path.lineTo(right, bottom)
            painter.drawPath(path)

        else:
            painter.drawRect(self.rect)

        # --- СДВИГИ И РАСЧЁТ ТЕКСТА ---
        painter.setPen(QPen(QColor("#1E2F35")))
        if hasattr(self, 'custom_font'):
            painter.setFont(self.custom_font)
        else:
            painter.setFont(self.font)

        if shape_type_lower in ["decision", "if", "условие", "если", "preparation", "подготовка", "hexagon"]:
            text_rect = self.rect.adjusted(25, 12, -25, -12)
        elif shape_type_lower in ["io", "input", "output", "ввод", "вывод"]:
            text_rect = self.rect.adjusted(22, 10, -22, -10)
        elif shape_type_lower in ["subroutine", "function", "procedure", "подпрограмма", "функция", "процедура",
                                  "double_rect"]:
            text_rect = self.rect.adjusted(22, 10, -22, -10)
        else:
            text_rect = self.rect.adjusted(15, 10, -15, -10)

        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.text)

        for handle in self._handles:
            handle.setVisible(self.isSelected())
            handle.setPos(self._handle_pos(handle.corner))

    def _handle_pos(self, corner: int) -> QPointF:
        x1, y1 = self.rect.left(), self.rect.top()
        x2, y2 = self.rect.right(), self.rect.bottom()
        xc, yc = self.rect.center().x(), self.rect.center().y()
        return {
            0: QPointF(x1, y1), 1: QPointF(xc, y1), 2: QPointF(x2, y1),
            3: QPointF(x2, yc), 4: QPointF(x2, y2), 5: QPointF(xc, y2),
            6: QPointF(x1, y2), 7: QPointF(x1, yc),
        }[corner]

    def resize_from_corner(self, corner: int, start_rect: QRectF, start_pos: QPointF, delta: QPointF) -> None:
        min_w, min_h = 70.0, 40.0
        x, y, w, h = start_pos.x(), start_pos.y(), start_rect.width(), start_rect.height()
        if corner in (0, 6, 7): x += delta.x(); w = max(min_w, w - delta.x())
        if corner in (2, 3, 4): w = max(min_w, w + delta.x())
        if corner in (0, 1, 2): y += delta.y(); h = max(min_h, h - delta.y())
        if corner in (4, 5, 6): h = max(min_h, h + delta.y())

        self.prepareGeometryChange()
        self.setPos(x, y)
        self.rect = QRectF(0, 0, w, h)
        self.update_lines()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for line in self._lines:
                if hasattr(line, 'is_back_edge') and line.is_back_edge:
                    line.update_back_edge_path()  # специальный метод для обратных стрелок
                else:
                    line.update_from_items()
        return super().itemChange(change, value)

    def register_line(self, line: BaseLine) -> None:
        if line not in self._lines: self._lines.append(line)

    def unregister_line(self, line: BaseLine) -> None:
        if line in self._lines: self._lines.remove(line)

    def update_lines(self) -> None:
        for line in list(self._lines): line.update_from_items()

    def connection_point_towards(self, scene_point: QPointF) -> QPointF:
        center = self.sceneBoundingRect().center()
        local = self.mapFromScene(scene_point)
        dx = local.x() - self.rect.center().x()
        dy = local.y() - self.rect.center().y()

        if dx == 0 and dy == 0:
            return self.mapToScene(self.rect.center())

        w, h = self.rect.width() / 2.0, self.rect.height() / 2.0
        scale = min(w / max(1e-4, abs(dx)), h / max(1e-4, abs(dy)))
        return self.mapToScene(QPointF(self.rect.center().x() + dx * scale, self.rect.center().y() + dy * scale))


class ArrowHandle(QGraphicsItem):
    def __init__(self, parent: ManualArrowItem, handle_type: str):
        super().__init__(parent)
        self.arrow = parent
        self.handle_type = handle_type
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.radius = 6

    def boundingRect(self) -> QRectF:
        return QRectF(-self.radius - 2, -self.radius - 2, self.radius * 2 + 4, self.radius * 2 + 4)

    def paint(self, painter: QPainter, option, widget=None):
        if not self.arrow.isSelected():
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        color = QColor("#FF9800") if self.handle_type == "mid" else QColor("#1F6FB2")
        painter.setPen(QPen(QColor("#FFFFFF"), 1))
        painter.setBrush(color)
        painter.drawEllipse(-self.radius, -self.radius, self.radius * 2, self.radius * 2)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            grid = 20
            new_pos.setX(round(new_pos.x() / grid) * grid)
            new_pos.setY(round(new_pos.y() / grid) * grid)

            self.arrow.update_from_handle(self.handle_type, new_pos)
            return new_pos
        return super().itemChange(change, value)


class ManualArrowItem(QGraphicsItem):
    def __init__(self, line_type: str = "arrow_line"):
        super().__init__()
        self.line_type = line_type

        self._p_start = QPointF(0, 0)
        self._p_mid = QPointF(50, 0)
        self._p_end = QPointF(100, 0)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

        self.h_start = ArrowHandle(self, "start")
        self.h_mid = ArrowHandle(self, "mid")
        self.h_end = ArrowHandle(self, "end")

        self.update_handle_positions()

    def update_handle_positions(self):
        self.h_start.setPos(self._p_start)
        self.h_mid.setPos(self._p_mid)
        self.h_end.setPos(self._p_end)

    def update_from_handle(self, handle_type: str, new_pos: QPointF):
        self.prepareGeometryChange()
        if handle_type == "start":
            self._p_start = new_pos
        elif handle_type == "end":
            self._p_end = new_pos
        elif handle_type == "mid":
            self._p_mid = new_pos

        self.update()

    def boundingRect(self) -> QRectF:
        points = [self._p_start, self._p_mid, self._p_end]
        xs = [p.x() for p in points]
        ys = [p.y() for p in points]
        return QRectF(min(xs) - 20, min(ys) - 20, max(xs) - min(xs) + 40, max(ys) - min(ys) + 40)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pen = QPen(QColor("#38505B"), 2)
        if self.isSelected():
            pen.setColor(QColor("#1F6FB2"))
            pen.setWidth(3)

        if self.line_type == "dashed_line":
            pen.setStyle(Qt.PenStyle.DashLine)

        painter.setPen(pen)

        path = QPainterPath()
        path.moveTo(self._p_start)
        path.lineTo(self._p_mid)
        path.lineTo(self._p_end)
        painter.drawPath(path)

        if self.line_type == "arrow_line":
            self.draw_arrow_head(painter, self._p_mid, self._p_end, pen.color())

        self.h_start.setVisible(self.isSelected())
        self.h_mid.setVisible(self.isSelected())
        self.h_end.setVisible(self.isSelected())

    def draw_arrow_head(self, painter: QPainter, p_from: QPointF, p_to: QPointF, color: QColor):
        dx = p_to.x() - p_from.x()
        dy = p_to.y() - p_from.y()
        angle = math.atan2(dy, dx)

        arrow_size = 12
        arrow_p1 = p_to - QPointF(math.cos(angle - math.pi / 6) * arrow_size,
                                  math.sin(angle - math.pi / 6) * arrow_size)
        arrow_p2 = p_to - QPointF(math.cos(angle + math.pi / 6) * arrow_size,
                                  math.sin(angle + math.pi / 6) * arrow_size)

        arrow_head = QPolygonF([p_to, arrow_p1, arrow_p2])

        painter.setBrush(color)
        painter.setPen(QPen(color, 1))
        painter.drawPolygon(arrow_head)



class CommentItem(QGraphicsItem):
    def __init__(self, text: str, src_item: QGraphicsItem = None, tgt_item: QGraphicsItem = None):
        super().__init__()
        self.text = text
        self.src_item = src_item  # Блок-источник стрелки
        self.tgt_item = tgt_item  # Блок-получатель стрелки
        self.padding = 10

        font = QPainter().font() if QPainter() else QFont()
        metrics = QFontMetrics(font)
        lines = self.text.split('\n')
        text_width = max([metrics.horizontalAdvance(l) for l in lines]) if lines else 50
        text_height = metrics.height() * max(len(lines), 1)

        self.text_rect = QRectF(0, 0, text_width + self.padding * 2, text_height + self.padding * 2)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

    def boundingRect(self) -> QRectF:
        # Большой bounding box вокруг, чтобы Qt не обрезал линию пунктира при зуме/движении
        return self.text_rect.adjusted(-1000, -500, 500, 500)

    def get_arrow_center(self) -> QPointF:
        """Динамически находит середину между двумя блоками на сцене"""
        if self.src_item and self.tgt_item:
            p1 = self.src_item.sceneBoundingRect().center()
            p2 = self.tgt_item.sceneBoundingRect().center()
            return QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
        elif self.src_item:
            return self.src_item.sceneBoundingRect().center()
        return QPointF(0, 0)

    def paint(self, painter: QPainter, option, widget) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Отрисовка текста комментария
        painter.setPen(QPen(QColor("#4CAF50"), 1))
        painter.drawText(self.text_rect, Qt.AlignmentFlag.AlignCenter, self.text)

        # 2. Отрисовка скобки ГОСТ
        r = self.text_rect
        painter.setPen(QPen(QColor("#1A5F7A"), 2, Qt.PenStyle.SolidLine))
        painter.drawLine(QPointF(r.left(), r.top()), QPointF(r.left(), r.bottom()))
        painter.drawLine(QPointF(r.left(), r.top()), QPointF(r.left() + 10, r.top()))
        painter.drawLine(QPointF(r.left(), r.bottom()), QPointF(r.left() + 10, r.bottom()))

        # 3. Отрисовка пунктирной линии к середине линии связи
        if self.src_item:
            center_scene = self.get_arrow_center()
            # Переводим точку центра из координат сцены в локальные координаты комментария
            target_pos_local = self.mapFromScene(center_scene)

            start_p = QPointF(r.left(), r.center().y())

            painter.setPen(QPen(QColor("#777777"), 1, Qt.PenStyle.DashLine))
            painter.drawLine(start_p, target_pos_local)