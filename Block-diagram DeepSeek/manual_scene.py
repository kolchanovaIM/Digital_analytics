# manual_scene.py
from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsLineItem, QGraphicsTextItem, QGraphicsSceneMouseEvent
)
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF
from PyQt6.QtGui import QColor, QPen, QKeyEvent
from constants import GRID_SIZE
from flowchart_items import FlowchartItem
from line_items import ArrowLine, SimpleLine, DashedLine, DashedArrowLine


class DiagramScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_tool = None
        self.line_start_point = None
        self.temp_line = None

    def set_tool(self, tool):
        self.current_tool = tool
        self.line_start_point = None
        self.clear_temp_line()

    def clear_temp_line(self):
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            for item in self.selectedItems():
                self.removeItem(item)
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = event.scenePos()
            item = self.itemAt(scene_pos, self.views()[0].transform())
            # Если под курсором есть элемент (не временная линия), передаём событие дальше
            if item is not None and item is not self.temp_line:
                super().mousePressEvent(event)
                return

            snapped = QPointF(round(scene_pos.x() / GRID_SIZE) * GRID_SIZE,
                              round(scene_pos.y() / GRID_SIZE) * GRID_SIZE)

            shape_tools = ['process', 'decision', 'startend', 'io', 'loop',
                           'function', 'semicircle', 'inverted_semicircle',
                           'inverted_trapezoid', 'elongated_oval']
            if self.current_tool in shape_tools:
                if self.current_tool == 'elongated_oval':
                    rect = QRectF(0, 0, 160, 60)
                else:
                    rect = QRectF(0, 0, 120, 60)
                new_item = FlowchartItem(self.current_tool, rect)
                new_item.setPos(snapped)
                self.addItem(new_item)
                return

            elif self.current_tool == 'text':
                text_item = QGraphicsTextItem()
                text_item.setPlainText("Текст")
                text_item.setDefaultTextColor(Qt.GlobalColor.black)
                text_item.setFlag(QGraphicsTextItem.GraphicsItemFlag.ItemIsMovable, True)
                text_item.setFlag(QGraphicsTextItem.GraphicsItemFlag.ItemIsSelectable, True)
                text_item.setPos(snapped)
                text_item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
                self.addItem(text_item)
                text_item.setFocus()
                return

            elif self.current_tool in ['line', 'dashed_line', 'arrow_line', 'dashed_arrow_line']:
                if self.line_start_point is None:
                    self.line_start_point = snapped
                    self.temp_line = QGraphicsLineItem(QLineF(snapped, snapped))
                    self.temp_line.setPen(QPen(Qt.GlobalColor.gray, 1, Qt.PenStyle.DashLine))
                    self.addItem(self.temp_line)
                else:
                    end_point = snapped
                    self.clear_temp_line()
                    if self.current_tool == 'arrow_line':
                        line_item = ArrowLine(self.line_start_point, end_point)
                    elif self.current_tool == 'dashed_arrow_line':
                        line_item = DashedArrowLine(self.line_start_point, end_point)
                    elif self.current_tool == 'dashed_line':
                        line_item = DashedLine(self.line_start_point, end_point)
                    else:  # 'line' (сплошная без стрелки)
                        line_item = SimpleLine(self.line_start_point, end_point)
                    self.addItem(line_item)
                    self.line_start_point = None
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self.temp_line and self.current_tool in ['line', 'dashed_line', 'arrow_line', 'dashed_arrow_line']:
            start = self.temp_line.line().p1()
            self.temp_line.setLine(QLineF(start, event.scenePos()))
        super().mouseMoveEvent(event)

    def drawBackground(self, painter, rect):
        painter.setPen(QPen(QColor(220, 220, 220), 0.5))
        left = int(rect.left()) - (int(rect.left()) % GRID_SIZE)
        top = int(rect.top()) - (int(rect.top()) % GRID_SIZE)
        lines = []
        for x in range(left, int(rect.right()), GRID_SIZE):
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), GRID_SIZE):
            lines.append(QLineF(rect.left(), y, rect.right(), y))
        painter.drawLines(lines)