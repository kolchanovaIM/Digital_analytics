import math

from PyQt6.QtCore import (
    Qt,
    QRectF,
    QPointF,
    QLineF
)

from PyQt6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QAction,
    QPixmap,
    QPolygonF,
    QBrush,
    QIcon
)

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsPolygonItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QFrame,
    QMenu,
    QGridLayout,
    QScrollArea,
    QGraphicsSceneMouseEvent
)

from constants import GRID_SIZE, GRID_COLOR
from export_utils import export_scene_to_pdf, export_scene_to_png


# =========================================================
# HELPERS
# =========================================================

def snap(value):
    return round(value / GRID_SIZE) * GRID_SIZE


# =========================================================
# RESIZE HANDLE
# =========================================================

class ResizeHandle(QGraphicsRectItem):

    SIZE = 10

    def __init__(self, parent_item, position):

        super().__init__(
            -5,
            -5,
            self.SIZE,
            self.SIZE,
            parent_item
        )

        self.parent_item = parent_item
        self.position = position

        self.setBrush(QColor("#2196F3"))

        self.setPen(
            QPen(Qt.GlobalColor.white, 1)
        )

        self.setZValue(999)

        self.dragging = False

    def mousePressEvent(self, event):

        self.dragging = True

        event.accept()

    def mouseMoveEvent(self, event):

        if not self.dragging:
            return

        pos = self.mapToParent(event.pos())

        self.parent_item.resize_from_handle(
            self.position,
            pos
        )

        event.accept()

    def mouseReleaseEvent(self, event):

        self.dragging = False

        event.accept()


# =========================================================
# FLOWCHART ITEM
# =========================================================

class FlowchartItem(QGraphicsPolygonItem):

    def __init__(
        self,
        shape_type="process",
        width=140,
        height=70
    ):

        super().__init__()

        self.shape_type = shape_type

        self.width = width
        self.height = height

        self.lines = []
        self.handles = []

        self.setBrush(
            QBrush(Qt.GlobalColor.white)
        )

        self.setPen(
            QPen(Qt.GlobalColor.black, 2)
        )

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.build_shape()
        self.create_handles()

    # =====================================================
    # BOUNDS
    # =====================================================

    def boundingRect(self):

        return self.polygon().boundingRect().adjusted(
            -15,
            -15,
            15,
            15
        )

    # =====================================================
    # SHAPE
    # =====================================================

    def build_shape(self):

        w = self.width
        h = self.height

        if self.shape_type == "process":

            polygon = QPolygonF([
                QPointF(0, 0),
                QPointF(w, 0),
                QPointF(w, h),
                QPointF(0, h)
            ])

        elif self.shape_type == "decision":

            polygon = QPolygonF([
                QPointF(w / 2, 0),
                QPointF(w, h / 2),
                QPointF(w / 2, h),
                QPointF(0, h / 2)
            ])

        elif self.shape_type == "io":

            offset = 25

            polygon = QPolygonF([
                QPointF(offset, 0),
                QPointF(w, 0),
                QPointF(w - offset, h),
                QPointF(0, h)
            ])

        else:

            polygon = QPolygonF()

            cx = w / 2
            cy = h / 2

            rx = w / 2
            ry = h / 2

            for i in range(40):

                angle = (
                    i / 40
                ) * 2 * math.pi

                x = cx + rx * math.cos(angle)
                y = cy + ry * math.sin(angle)

                polygon.append(
                    QPointF(x, y)
                )

        self.setPolygon(polygon)

    # =====================================================
    # HANDLES
    # =====================================================

    def create_handles(self):

        positions = [
            "top_left",
            "top",
            "top_right",
            "right",
            "bottom_right",
            "bottom",
            "bottom_left",
            "left"
        ]

        for pos in positions:

            handle = ResizeHandle(self, pos)

            handle.hide()

            self.handles.append(handle)

        self.update_handles()

    def update_handles(self):

        w = self.width
        h = self.height

        positions = {
            "top_left": QPointF(0, 0),
            "top": QPointF(w / 2, 0),
            "top_right": QPointF(w, 0),
            "right": QPointF(w, h / 2),
            "bottom_right": QPointF(w, h),
            "bottom": QPointF(w / 2, h),
            "bottom_left": QPointF(0, h),
            "left": QPointF(0, h / 2)
        }

        for handle in self.handles:

            handle.setVisible(self.isSelected())

            handle.setPos(
                positions[handle.position]
            )

    # =====================================================
    # RESIZE
    # =====================================================

    def resize_from_handle(
        self,
        position,
        point
    ):

        min_w = 80
        min_h = 50

        if "right" in position:

            self.width = max(
                min_w,
                point.x()
            )

        if "bottom" in position:

            self.height = max(
                min_h,
                point.y()
            )

        self.prepareGeometryChange()

        self.build_shape()

        self.update_handles()

        self.update_lines()

    # =====================================================
    # LINES
    # =====================================================

    def add_line(self, line):

        if line not in self.lines:
            self.lines.append(line)

    def update_lines(self):

        for line in self.lines:
            line.update_position()

    # =====================================================
    # EVENTS
    # =====================================================

    def itemChange(self, change, value):

        if (
            change ==
            QGraphicsItem.GraphicsItemChange.ItemPositionChange
        ):

            x = snap(value.x())
            y = snap(value.y())

            return QPointF(x, y)

        if (
            change ==
            QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged
        ):

            self.update_lines()

        if (
            change ==
            QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged
        ):

            self.update_handles()

        return super().itemChange(change, value)


# =========================================================
# BASE LINE
# =========================================================

class BaseConnection(QGraphicsLineItem):

    def __init__(
        self,
        start_item,
        end_item
    ):

        super().__init__()

        self.start_item = start_item
        self.end_item = end_item

        self.start_item.add_line(self)
        self.end_item.add_line(self)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )

        self.update_position()

    def update_position(self):

        start = self.start_item.sceneBoundingRect().center()
        end = self.end_item.sceneBoundingRect().center()

        self.setLine(QLineF(start, end))


# =========================================================
# SIMPLE LINE
# =========================================================

class SimpleLine(BaseConnection):

    def __init__(self, start_item, end_item):

        super().__init__(
            start_item,
            end_item
        )

        self.setPen(
            QPen(Qt.GlobalColor.black, 2)
        )


# =========================================================
# DASHED LINE
# =========================================================

class DashedLine(BaseConnection):

    def __init__(self, start_item, end_item):

        super().__init__(
            start_item,
            end_item
        )

        pen = QPen(
            Qt.GlobalColor.black,
            2
        )

        pen.setStyle(Qt.PenStyle.DashLine)

        self.setPen(pen)


# =========================================================
# ARROW LINE
# =========================================================

class ArrowLine(BaseConnection):

    def __init__(self, start_item, end_item):

        super().__init__(
            start_item,
            end_item
        )

        self.setPen(
            QPen(Qt.GlobalColor.black, 2)
        )

    def paint(self, painter, option, widget=None):

        super().paint(
            painter,
            option,
            widget
        )

        line = self.line()

        angle = math.atan2(
            -line.dy(),
            line.dx()
        )

        arrow_size = 12

        p2 = line.p2()

        p1 = QPointF(
            p2.x() - arrow_size * math.cos(angle + 0.4),
            p2.y() + arrow_size * math.sin(angle + 0.4)
        )

        p2b = QPointF(
            p2.x() - arrow_size * math.cos(angle - 0.4),
            p2.y() + arrow_size * math.sin(angle - 0.4)
        )

        arrow = QPolygonF([
            p2,
            p1,
            p2b
        ])

        painter.setBrush(
            Qt.GlobalColor.black
        )

        painter.drawPolygon(arrow)


# =========================================================
# SCENE
# =========================================================

class GraphicsScene(QGraphicsScene):

    def drawBackground(self, painter, rect):

        super().drawBackground(
            painter,
            rect
        )

        painter.setPen(
            QPen(GRID_COLOR)
        )

        left = int(rect.left()) - (
            int(rect.left()) % GRID_SIZE
        )

        top = int(rect.top()) - (
            int(rect.top()) % GRID_SIZE
        )

        x = left

        while x < rect.right():

            painter.drawLine(
                int(x),
                int(rect.top()),
                int(x),
                int(rect.bottom())
            )

            x += GRID_SIZE

        y = top

        while y < rect.bottom():

            painter.drawLine(
                int(rect.left()),
                int(y),
                int(rect.right()),
                int(y)
            )

            y += GRID_SIZE


# =========================================================
# VIEW
# =========================================================

class CanvasView(QGraphicsView):

    def __init__(self, window, scene):

        super().__init__(scene)

        self.window = window

        self.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        self.setDragMode(
            QGraphicsView.DragMode.RubberBandDrag
        )

    # =====================================================
    # FIGURE
    # =====================================================

    def add_figure(self, shape, pos):

        x = snap(pos.x())
        y = snap(pos.y())

        item = FlowchartItem(shape)

        item.setPos(x, y)

        self.scene().addItem(item)

        item.setSelected(True)

    # =====================================================
    # LINE
    # =====================================================

    def add_line(
        self,
        line_type,
        start_item,
        end_item
    ):

        if line_type == "arrow":

            line = ArrowLine(
                start_item,
                end_item
            )

        elif line_type == "line":

            line = SimpleLine(
                start_item,
                end_item
            )

        else:

            line = DashedLine(
                start_item,
                end_item
            )

        self.scene().addItem(line)

    # =====================================================
    # MOUSE
    # =====================================================

    def mousePressEvent(self, event):

        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):

            scene_pos = self.mapToScene(
                event.pos()
            )

            clicked_item = self.itemAt(
                event.pos()
            )

            if isinstance(
                clicked_item,
                ResizeHandle
            ):
                clicked_item = clicked_item.parent_item

            tool = self.window.current_tool

            # FIGURES

            if tool in [
                "process",
                "decision",
                "io",
                "terminal"
            ]:

                if clicked_item is None:

                    self.add_figure(
                        tool,
                        scene_pos
                    )

                    return

            # LINES

            elif tool in [
                "arrow",
                "line",
                "dash"
            ]:

                if isinstance(
                    clicked_item,
                    FlowchartItem
                ):

                    if (
                        self.window.line_start_item
                        is None
                    ):

                        self.window.line_start_item = clicked_item

                        clicked_item.setSelected(True)

                        self.setCursor(
                            Qt.CursorShape.CrossCursor
                        )

                    else:

                        if (
                            self.window.line_start_item
                            != clicked_item
                        ):

                            self.add_line(
                                tool,
                                self.window.line_start_item,
                                clicked_item
                            )

                        self.window.line_start_item = None

                        self.setCursor(
                            Qt.CursorShape.ArrowCursor
                        )

                else:

                    self.window.line_start_item = None

                    self.setCursor(
                        Qt.CursorShape.ArrowCursor
                    )

                return

        super().mousePressEvent(event)

    # =====================================================
    # DELETE / ESCAPE
    # =====================================================

    def keyPressEvent(self, event):

        if (
            event.key()
            == Qt.Key.Key_Delete
        ):

            selected = self.scene().selectedItems()

            for item in selected:

                if isinstance(
                    item,
                    FlowchartItem
                ):

                    for line in item.lines[:]:

                        self.scene().removeItem(line)

                self.scene().removeItem(item)

            return

        if (
            event.key()
            == Qt.Key.Key_Escape
        ):

            self.window.line_start_item = None

            self.setCursor(
                Qt.CursorShape.ArrowCursor
            )

            return

        super().keyPressEvent(event)


# =========================================================
# MAIN WINDOW
# =========================================================

class ManualModeWindow(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.current_tool = None
        self.line_start_item = None

        self.setup_ui()

    # =====================================================
    # UI
    # =====================================================

    def setup_ui(self):

        self.resize(1200, 700)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        # TITLE

        layout.addWidget(
            self.create_title()
        )

        # CONTENT

        content = QWidget()

        content_layout = QHBoxLayout(content)

        content_layout.setContentsMargins(
            10,
            10,
            10,
            10
        )

        # TOOLBAR

        toolbar = self.create_toolbar()

        content_layout.addWidget(toolbar)

        # SCENE

        self.scene = GraphicsScene()

        self.scene.setSceneRect(
            -5000,
            -5000,
            10000,
            10000
        )

        self.view = CanvasView(
            self,
            self.scene
        )

        self.view.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

        content_layout.addWidget(
            self.view,
            1
        )

        layout.addWidget(content)

    # =====================================================
    # TITLE
    # =====================================================

    def create_title(self):

        frame = QFrame()

        frame.setFixedHeight(42)

        frame.setStyleSheet("""
            background:#BDD1D5;
        """)

        layout = QHBoxLayout(frame)

        label = QLabel(
            "Ручное рисование"
        )

        close_btn = QPushButton("✕")

        close_btn.clicked.connect(
            self.close
        )

        layout.addWidget(label)

        layout.addStretch()

        layout.addWidget(close_btn)

        return frame

    # =====================================================
    # TOOLBAR
    # =====================================================

    def create_toolbar(self):

        frame = QFrame()

        frame.setFixedWidth(210)

        frame.setStyleSheet("""
            QFrame{
                background:#DDEEF3;
                border-radius:14px;
            }

            QPushButton{
                background:white;
                border:none;
                border-radius:10px;
            }

            QPushButton:hover{
                background:#CDE6F8;
            }
        """)

        layout = QVBoxLayout(frame)

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        content = QWidget()

        grid = QGridLayout(content)

        tools = [
            ("process", self.icon_process()),
            ("decision", self.icon_decision()),
            ("io", self.icon_io()),
            ("terminal", self.icon_terminal()),
            ("arrow", self.icon_arrow()),
            ("line", self.icon_line()),
            ("dash", self.icon_dash())
        ]

        row = 0
        col = 0

        for tool, icon in tools:

            btn = QPushButton()

            btn.setFixedSize(80, 60)

            btn.setIcon(QIcon(icon))

            btn.setIconSize(icon.size())

            btn.clicked.connect(
                lambda checked=False,
                       t=tool: self.select_tool(t)
            )

            grid.addWidget(
                btn,
                row,
                col
            )

            col += 1

            if col >= 2:

                col = 0
                row += 1

        png_btn = QPushButton("PNG")
        pdf_btn = QPushButton("PDF")

        png_btn.clicked.connect(
            self.export_png
        )

        pdf_btn.clicked.connect(
            self.export_pdf
        )

        grid.addWidget(
            png_btn,
            row + 1,
            0
        )

        grid.addWidget(
            pdf_btn,
            row + 1,
            1
        )

        scroll.setWidget(content)

        layout.addWidget(scroll)

        return frame

    # =====================================================
    # TOOL
    # =====================================================

    def select_tool(self, tool):

        self.current_tool = tool

        if tool in [
            "arrow",
            "line",
            "dash"
        ]:

            self.line_start_item = None

    # =====================================================
    # EXPORT
    # =====================================================

    def export_png(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "PNG",
            "",
            "PNG (*.png)"
        )

        if path:

            export_scene_to_png(
                self.scene,
                path
            )

    def export_pdf(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "PDF",
            "",
            "PDF (*.pdf)"
        )

        if path:

            export_scene_to_pdf(
                self.scene,
                path
            )

    # =====================================================
    # ICONS
    # =====================================================

    def create_icon(self):

        pixmap = QPixmap(70, 50)

        pixmap.fill(
            Qt.GlobalColor.transparent
        )

        painter = QPainter(pixmap)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        painter.setPen(
            QPen(
                Qt.GlobalColor.black,
                3
            )
        )

        return pixmap, painter

    def icon_process(self):

        pixmap, painter = self.create_icon()

        painter.drawRect(
            10,
            10,
            50,
            30
        )

        painter.end()

        return pixmap

    def icon_decision(self):

        pixmap, painter = self.create_icon()

        polygon = QPolygonF([
            QPointF(35, 5),
            QPointF(60, 25),
            QPointF(35, 45),
            QPointF(10, 25)
        ])

        painter.drawPolygon(polygon)

        painter.end()

        return pixmap

    def icon_io(self):

        pixmap, painter = self.create_icon()

        polygon = QPolygonF([
            QPointF(20, 10),
            QPointF(60, 10),
            QPointF(50, 40),
            QPointF(10, 40)
        ])

        painter.drawPolygon(polygon)

        painter.end()

        return pixmap

    def icon_terminal(self):

        pixmap, painter = self.create_icon()

        painter.drawEllipse(
            10,
            10,
            50,
            30
        )

        painter.end()

        return pixmap

    def icon_arrow(self):

        pixmap, painter = self.create_icon()

        painter.drawLine(
            10,
            25,
            55,
            25
        )

        arrow = QPolygonF([
            QPointF(55, 25),
            QPointF(45, 18),
            QPointF(45, 32)
        ])

        painter.setBrush(
            Qt.GlobalColor.black
        )

        painter.drawPolygon(arrow)

        painter.end()

        return pixmap

    def icon_line(self):

        pixmap, painter = self.create_icon()

        painter.drawLine(
            10,
            25,
            60,
            25
        )

        painter.end()

        return pixmap

    def icon_dash(self):

        pixmap, painter = self.create_icon()

        pen = QPen(
            Qt.GlobalColor.black,
            3
        )

        pen.setStyle(
            Qt.PenStyle.DashLine
        )

        painter.setPen(pen)

        painter.drawLine(
            10,
            25,
            60,
            25
        )

        painter.end()

        return pixmap