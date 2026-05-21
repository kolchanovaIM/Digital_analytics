import math

from PyQt6.QtWidgets import (
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsLineItem,
    QGraphicsTextItem,
    QGraphicsItem
)

from PyQt6.QtCore import (
    Qt,
    QRectF,
    QPointF,
    QLineF
)

from PyQt6.QtGui import (
    QColor,
    QPen,
    QBrush,
    QPainter,
    QPolygonF,
    QPainterPath,
    QFont
)

from constants import (
    GRID_SIZE,
    GRID_COLOR,
    SHAPE_FILL_COLOR,
    SHAPE_LINE_COLOR
)


# =========================================================
# FLOWCHART ITEM
# =========================================================

class FlowchartItem(QGraphicsRectItem):

    def __init__(
        self,
        shape_type="process",
        text="",
        x=0,
        y=0,
        w=140,
        h=70
    ):

        super().__init__(0, 0, w, h)

        self.shape_type = shape_type

        self.w = w
        self.h = h

        self.setPos(x, y)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )

        self.setBrush(
            QBrush(QColor(SHAPE_FILL_COLOR))
        )

        self.setPen(
            QPen(
                QColor(SHAPE_LINE_COLOR),
                2
            )
        )

        self.text_item = QGraphicsTextItem(
            text,
            self
        )

        self.text_item.setDefaultTextColor(
            QColor("#000000")
        )

        font = QFont("Arial", 10)

        self.text_item.setFont(font)

        self.update_text_position()

    # =====================================================

    def update_text_position(self):

        rect = self.text_item.boundingRect()

        self.text_item.setPos(
            (self.w - rect.width()) / 2,
            (self.h - rect.height()) / 2
        )

    # =====================================================

    def paint(
        self,
        painter,
        option,
        widget=None
    ):

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        painter.setPen(
            self.pen()
        )

        painter.setBrush(
            self.brush()
        )

        w = self.w
        h = self.h

        # =================================================
        # PROCESS
        # =================================================

        if self.shape_type == "process":

            painter.drawRect(
                0,
                0,
                w,
                h
            )

        # =================================================
        # INPUT / OUTPUT
        # =================================================

        elif self.shape_type == "io":

            poly = QPolygonF([
                QPointF(20, 0),
                QPointF(w, 0),
                QPointF(w - 20, h),
                QPointF(0, h)
            ])

            painter.drawPolygon(poly)

        # =================================================
        # DECISION
        # =================================================

        elif self.shape_type == "decision":

            poly = QPolygonF([
                QPointF(w / 2, 0),
                QPointF(w, h / 2),
                QPointF(w / 2, h),
                QPointF(0, h / 2)
            ])

            painter.drawPolygon(poly)

        # =================================================
        # TERMINAL
        # =================================================

        elif self.shape_type == "terminal":

            painter.drawRoundedRect(
                0,
                0,
                w,
                h,
                h / 2,
                h / 2
            )

        # =================================================
        # CONNECTOR
        # =================================================

        elif self.shape_type == "connector":

            painter.drawEllipse(
                0,
                0,
                w,
                h
            )

        else:

            painter.drawRect(
                0,
                0,
                w,
                h
            )


# =========================================================
# CUSTOM LINE ITEM
# =========================================================

class CustomLineItem(QGraphicsLineItem):

    def __init__(
        self,
        p1,
        p2,
        line_type="arrow"
    ):

        super().__init__()

        self.line_type = line_type

        self.setLine(
            QLineF(p1, p2)
        )

        pen = QPen(
            QColor(SHAPE_LINE_COLOR),
            2
        )

        if line_type == "dash":

            pen.setStyle(
                Qt.PenStyle.DashLine
            )

        self.setPen(pen)

    # =====================================================

    def paint(
        self,
        painter,
        option,
        widget=None
    ):

        super().paint(
            painter,
            option,
            widget
        )

        if self.line_type != "arrow":
            return

        line = self.line()

        angle = math.atan2(
            -line.dy(),
            line.dx()
        )

        arrow_size = 12

        p2 = line.p2()

        arrow_p1 = p2 - QPointF(
            math.cos(angle + math.pi / 6)
            * arrow_size,

            -math.sin(angle + math.pi / 6)
            * arrow_size
        )

        arrow_p2 = p2 - QPointF(
            math.cos(angle - math.pi / 6)
            * arrow_size,

            -math.sin(angle - math.pi / 6)
            * arrow_size
        )

        arrow_head = QPolygonF([
            p2,
            arrow_p1,
            arrow_p2
        ])

        painter.setBrush(
            QBrush(
                QColor(SHAPE_LINE_COLOR)
            )
        )

        painter.drawPolygon(
            arrow_head
        )


# =========================================================
# RESIZE HANDLE
# =========================================================

class ResizeHandle(QGraphicsRectItem):

    SIZE = 10

    def __init__(self, parent=None):

        super().__init__(
            0,
            0,
            self.SIZE,
            self.SIZE,
            parent
        )

        self.setBrush(
            QBrush(QColor("#0078D7"))
        )

        self.setPen(
            Qt.PenStyle.NoPen
        )

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )


# =========================================================
# LINE HANDLE
# =========================================================

class LineHandle(QGraphicsRectItem):

    SIZE = 8

    def __init__(self, parent=None):

        super().__init__(
            0,
            0,
            self.SIZE,
            self.SIZE,
            parent
        )

        self.setBrush(
            QBrush(QColor("#FF0000"))
        )

        self.setPen(
            Qt.PenStyle.NoPen
        )

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )


# =========================================================
# MANUAL SCENE
# =========================================================

class ManualScene(QGraphicsScene):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setSceneRect(
            -5000,
            -5000,
            10000,
            10000
        )

    # =====================================================

    def drawBackground(
        self,
        painter,
        rect
    ):

        super().drawBackground(
            painter,
            rect
        )

        pen = QPen(
            QColor(GRID_COLOR),
            1
        )

        painter.setPen(pen)

        left = int(rect.left()) - (
            int(rect.left()) % GRID_SIZE
        )

        top = int(rect.top()) - (
            int(rect.top()) % GRID_SIZE
        )

        # vertical

        x = left

        while x < rect.right():

            painter.drawLine(
                x,
                rect.top(),
                x,
                rect.bottom()
            )

            x += GRID_SIZE

        # horizontal

        y = top

        while y < rect.bottom():

            painter.drawLine(
                rect.left(),
                y,
                rect.right(),
                y
            )

            y += GRID_SIZE