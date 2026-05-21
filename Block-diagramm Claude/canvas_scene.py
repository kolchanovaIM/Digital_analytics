from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtCore import QLineF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor


class GridScene(QGraphicsScene):
    GRID_STEP  = 20
    GRID_COLOR = QColor(180, 200, 210, 80)

    def drawBackground(self, painter: QPainter, rect):
        painter.fillRect(rect, QColor("#F4F8FA"))
        pen = QPen(self.GRID_COLOR, 0.5)
        painter.setPen(pen)
        left = int(rect.left()) - int(rect.left()) % self.GRID_STEP
        top  = int(rect.top())  - int(rect.top())  % self.GRID_STEP
        x = left
        while x < rect.right():
            painter.drawLine(QLineF(x, rect.top(), x, rect.bottom()))
            x += self.GRID_STEP
        y = top
        while y < rect.bottom():
            painter.drawLine(QLineF(rect.left(), y, rect.right(), y))
            y += self.GRID_STEP