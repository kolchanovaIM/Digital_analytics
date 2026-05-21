# ui_manual_mode.py — полная версия с функциями экспорта в PNG и PDF
import traceback
import math
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QLabel, QFrame, QToolButton, QMenu, QGraphicsView, QGraphicsScene,
    QGraphicsDropShadowEffect, QApplication, QGraphicsItem, QGraphicsPathItem,
    QGraphicsLineItem, QGraphicsTextItem, QGraphicsSceneMouseEvent,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QPoint, QEvent, QPointF, QRectF, QLineF
from PyQt6.QtGui import (
    QFont, QColor, QMouseEvent, QBrush, QPixmap, QCursor,
    QPainter, QPainterPath, QPen, QPolygonF, QIcon, QKeyEvent, QAction
)
from PyQt6.QtPrintSupport import QPrinter

GRID_SIZE = 20
HANDLE_RADIUS = 5
MIN_SIZE = 40
MIN_LINE_LENGTH = 20
SNAP_DISTANCE = 20


def qCos(angle_deg: float) -> float:
    return math.cos(math.radians(angle_deg))


def qSin(angle_deg: float) -> float:
    return math.sin(math.radians(angle_deg))


class FlowchartItem(QGraphicsPathItem):
    def __init__(self, shape_type, rect=QRectF(0, 0, 120, 60)):
        super().__init__()
        self.shape_type = shape_type
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setPen(QPen(Qt.GlobalColor.black, 1.5))
        self.setBrush(QBrush(QColor("#E6E6E6")))

        self._create_path(rect)

        self.text_item = QGraphicsTextItem(self)
        self.text_item.setPlainText("")
        self.text_item.setDefaultTextColor(Qt.GlobalColor.black)
        self._center_text()
        self.text_item.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

    def _create_path(self, rect):
        path = QPainterPath()
        w = rect.width()
        h = rect.height()
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
        elif self.shape_type == 'elongated_oval':
            path.addRoundedRect(rect, 15, 15)
        else:
            path.addRect(rect)
        self.setPath(path)

    def _center_text(self):
        rect = self.boundingRect()
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(
            rect.center().x() - text_rect.width() / 2,
            rect.center().y() - text_rect.height() / 2
        )

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            new_pos = value
            snapped_x = round(new_pos.x() / GRID_SIZE) * GRID_SIZE
            snapped_y = round(new_pos.y() / GRID_SIZE) * GRID_SIZE
            return QPointF(snapped_x, snapped_y)
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        self.text_item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.text_item.setFocus()
        super().mouseDoubleClickEvent(event)


class ArrowLine(QGraphicsLineItem):
    def __init__(self, start_point, end_point):
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPen(QPen(Qt.GlobalColor.black, 1.5))
        self.setLine(QLineF(start_point, end_point))

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        line = self.line()
        if line.length() == 0:
            return
        pen = self.pen()
        painter.setPen(pen)
        painter.setBrush(pen.color())
        angle = -line.angle()
        arrow_size = 12
        p2 = line.p2()
        arrow_p1 = p2 - QPointF(
            arrow_size * qCos(angle - 30),
            arrow_size * qSin(angle - 30)
        )
        arrow_p2 = p2 - QPointF(
            arrow_size * qCos(angle + 30),
            arrow_size * qSin(angle + 30)
        )
        arrow = QPolygonF([arrow_p1, p2, arrow_p2])
        painter.drawPolygon(arrow)


class DiagramScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_tool = None
        self.line_start_point = None

    def set_tool(self, tool):
        self.current_tool = tool
        self.line_start_point = None

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            for item in self.selectedItems():
                self.removeItem(item)
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = event.scenePos()
            item = self.itemAt(scene_pos, self.views()[0].transform())
            if item is not None:
                super().mousePressEvent(event)
                return

            snapped = QPointF(round(scene_pos.x() / GRID_SIZE) * GRID_SIZE,
                              round(scene_pos.y() / GRID_SIZE) * GRID_SIZE)

            if self.current_tool in ['process', 'decision', 'startend', 'io', 'loop',
                                     'function', 'semicircle', 'inverted_semicircle',
                                     'inverted_trapezoid', 'elongated_oval']:
                new_item = FlowchartItem(self.current_tool)
                new_item.setPos(snapped)
                self.addItem(new_item)
                return

            elif self.current_tool == 'text':
                text_item = QGraphicsTextItem()
                text_item.setPlainText("Текст")
                text_item.setDefaultTextColor(Qt.GlobalColor.black)
                text_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
                text_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                text_item.setPos(snapped)
                text_item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
                self.addItem(text_item)
                text_item.setFocus()
                return

            elif self.current_tool in ['line', 'dashed_line', 'arrow_line']:
                if self.line_start_point is None:
                    self.line_start_point = snapped
                else:
                    end_point = snapped
                    if self.current_tool == 'arrow_line':
                        line_item = ArrowLine(self.line_start_point, end_point)
                    else:
                        line_item = QGraphicsLineItem(QLineF(self.line_start_point, end_point))
                        line_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                        line_item.setPen(QPen(Qt.GlobalColor.black, 1.5))
                        if self.current_tool == 'dashed_line':
                            pen = line_item.pen()
                            pen.setStyle(Qt.PenStyle.DashLine)
                            line_item.setPen(pen)
                    self.addItem(line_item)
                    self.line_start_point = None
                return
        super().mousePressEvent(event)

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


class HeaderBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("headerBar")
        self.setFixedHeight(36)
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)

        self.menu_btn = QToolButton()
        self.menu_btn.setText("☰")
        self.menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                color: #444444;
                font-size: 18px;
                font-weight: bold;
                padding: 4px 8px;
            }
            QToolButton:hover {
                background: rgba(0,0,0,0.08);
                border-radius: 4px;
            }
        """)
        self.menu_btn.clicked.connect(self._show_menu)
        layout.addWidget(self.menu_btn)

        layout.addStretch()

        self.minimize_btn = QPushButton("–")
        self.maximize_btn = QPushButton("🗖")
        self.close_btn = QPushButton("✕")

        for btn in (self.minimize_btn, self.maximize_btn, self.close_btn):
            btn.setFixedSize(34, 34)
            btn.setObjectName("windowControlButton")
            layout.addWidget(btn)

        self.minimize_btn.setStyleSheet(self._base_style())
        self.maximize_btn.setStyleSheet(self._base_style())
        self.close_btn.setStyleSheet(self._close_style())

        self.minimize_btn.clicked.connect(self.window().showMinimized)
        self.maximize_btn.clicked.connect(self._toggle_maximize)
        self.close_btn.clicked.connect(QApplication.instance().quit)

    def _base_style(self):
        return """
            QPushButton {
                background: rgba(255, 255, 255, 0);
                border: none;
                color: #444444;
                font-size: 18px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(0, 0, 0, 0.08);
            }
        """

    def _close_style(self):
        return """
            QPushButton {
                background: rgba(255, 255, 255, 0);
                border: none;
                color: #444444;
                font-size: 18px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(232, 17, 35, 0.9);
                color: white;
            }
        """

    def _toggle_maximize(self):
        win = self.window()
        if win.isMaximized():
            win.showNormal()
            self.maximize_btn.setText("🗖")
        else:
            win.showMaximized()
            self.maximize_btn.setText("🗗")

    def _show_menu(self):
        """Показывает бургер-меню с опциями экспорта."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:hover {
                background: #DDEEF3;
            }
            QMenu::separator {
                height: 1px;
                background: #ddd;
                margin: 4px 10px;
            }
        """)

        action_png = QAction("Сохранить как PNG", self)
        action_png.triggered.connect(self.window().export_png)
        menu.addAction(action_png)

        action_pdf = QAction("Сохранить как PDF", self)
        action_pdf.triggered.connect(self.window().export_pdf)
        menu.addAction(action_pdf)

        menu.addSeparator()

        action_back = QAction("← Назад", self)
        action_back.triggered.connect(self.window().close)
        menu.addAction(action_back)

        menu.exec(self.menu_btn.mapToGlobal(QPoint(0, self.menu_btn.height())))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if not win.isMaximized():
                self._drag_pos = event.globalPosition().toPoint() - win.pos()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None:
            win = self.window()
            if not win.isMaximized():
                win.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)


def create_tool_icon(shape_type):
    pix = QPixmap(48, 48)
    pix.fill(QColor(255, 255, 255, 0))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(Qt.GlobalColor.black, 2))
    painter.setBrush(QBrush(QColor("#E6E6E6")))
    rect = QRectF(4, 4, 40, 40)
    w = rect.width()
    h = rect.height()
    if shape_type in ('process', 'io'):
        path = QPainterPath()
        if shape_type == 'process':
            path.addRect(rect)
        else:
            skew = min(10, w * 0.3)
            poly = QPolygonF([
                QPointF(rect.left() + skew, rect.top()),
                QPointF(rect.right(), rect.top()),
                QPointF(rect.right() - skew, rect.bottom()),
                QPointF(rect.left(), rect.bottom())
            ])
            path.addPolygon(poly)
        painter.drawPath(path)
    elif shape_type == 'decision':
        poly = QPolygonF([
            QPointF(rect.center().x(), rect.top()),
            QPointF(rect.right(), rect.center().y()),
            QPointF(rect.center().x(), rect.bottom()),
            QPointF(rect.left(), rect.center().y())
        ])
        painter.drawPolygon(poly)
    elif shape_type == 'startend':
        painter.drawEllipse(rect)
    elif shape_type == 'loop':
        d = w * 0.3
        poly = QPolygonF([
            QPointF(rect.left() + d, rect.top()),
            QPointF(rect.right() - d, rect.top()),
            QPointF(rect.right(), rect.center().y()),
            QPointF(rect.right() - d, rect.bottom()),
            QPointF(rect.left() + d, rect.bottom()),
            QPointF(rect.left(), rect.center().y())
        ])
        painter.drawPolygon(poly)
    elif shape_type == 'function':
        painter.drawRect(rect.toAlignedRect())
        painter.drawLine(QPointF(rect.left() + w*0.2, rect.top()), QPointF(rect.left() + w*0.2, rect.bottom()))
        painter.drawLine(QPointF(rect.right() - w*0.2, rect.top()), QPointF(rect.right() - w*0.2, rect.bottom()))
    elif shape_type == 'semicircle':
        path = QPainterPath()
        path.moveTo(rect.left(), rect.bottom())
        path.lineTo(rect.right(), rect.bottom())
        path.lineTo(rect.right(), rect.center().y())
        path.arcTo(rect, 0, 180)
        path.lineTo(rect.left(), rect.bottom())
        path.closeSubpath()
        painter.drawPath(path)
    elif shape_type == 'inverted_semicircle':
        path = QPainterPath()
        path.moveTo(rect.left(), rect.top())
        path.lineTo(rect.right(), rect.top())
        path.lineTo(rect.right(), rect.center().y())
        path.arcTo(rect, 0, -180)
        path.lineTo(rect.left(), rect.top())
        path.closeSubpath()
        painter.drawPath(path)
    elif shape_type == 'inverted_trapezoid':
        poly = QPolygonF([
            QPointF(rect.left(), rect.top()),
            QPointF(rect.right(), rect.top()),
            QPointF(rect.right() - w * 0.2, rect.bottom()),
            QPointF(rect.left() + w * 0.2, rect.bottom())
        ])
        painter.drawPolygon(poly)
    elif shape_type == 'elongated_oval':
        painter.drawRoundedRect(QRectF(2, 10, 44, 28), 10, 10)
    elif shape_type == 'line':
        painter.drawLine(QPointF(8, 40), QPointF(40, 8))
    elif shape_type == 'dashed_line':
        pen = QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(8, 40), QPointF(40, 8))
    elif shape_type == 'arrow_line':
        painter.drawLine(QPointF(8, 40), QPointF(40, 8))
        painter.setBrush(QBrush(Qt.GlobalColor.black))
        arrow_head = QPolygonF([
            QPointF(40, 8),
            QPointF(30, 2),
            QPointF(30, 14)
        ])
        painter.drawPolygon(arrow_head)
    elif shape_type == 'text':
        painter.setPen(QPen(Qt.GlobalColor.black, 3))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "T")
    painter.end()
    return pix


class DraggableToolPalette(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("toolPalette")
        self.setFixedWidth(180)
        self._drag_start_global = None
        self._drag_start_pos = None

        self.setStyleSheet("""
            #toolPalette {
                background: #DDEEF3;
                border-radius: 15px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

        grid = QGridLayout(self)
        grid.setContentsMargins(8, 12, 8, 12)
        grid.setSpacing(8)

        self.buttons = {}
        tools = [
            ("process", create_tool_icon("process")),
            ("decision", create_tool_icon("decision")),
            ("startend", create_tool_icon("startend")),
            ("io", create_tool_icon("io")),
            ("loop", create_tool_icon("loop")),
            ("function", create_tool_icon("function")),
            ("semicircle", create_tool_icon("semicircle")),
            ("inverted_semicircle", create_tool_icon("inverted_semicircle")),
            ("inverted_trapezoid", create_tool_icon("inverted_trapezoid")),
            ("elongated_oval", create_tool_icon("elongated_oval")),
            ("line", create_tool_icon("line")),
            ("dashed_line", create_tool_icon("dashed_line")),
            ("arrow_line", create_tool_icon("arrow_line")),
            ("text", create_tool_icon("text"))
        ]

        positions = [(i // 2, i % 2) for i in range(len(tools))]
        for (row, col), (tool_id, icon) in zip(positions, tools):
            btn = QPushButton()
            btn.setIcon(QIcon(icon))
            btn.setIconSize(btn.size())
            btn.setCheckable(True)
            btn.setFixedSize(64, 64)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 12px;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.8);
                }
                QPushButton:checked {
                    background: rgba(255,255,255,0.95);
                }
            """)
            btn.clicked.connect(lambda checked, t=tool_id: self.select_tool(t))
            grid.addWidget(btn, row, col, Qt.AlignmentFlag.AlignCenter)
            self.buttons[tool_id] = btn

        self.current_tool = None
        self.adjustSize()

    def select_tool(self, tool_id):
        if self.current_tool == tool_id:
            self.buttons[tool_id].setChecked(False)
            self.current_tool = None
        else:
            if self.current_tool is not None:
                self.buttons[self.current_tool].setChecked(False)
            self.buttons[tool_id].setChecked(True)
            self.current_tool = tool_id
        win = self.window()
        if hasattr(win, 'on_tool_changed'):
            win.on_tool_changed(self.current_tool)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_global = event.globalPosition().toPoint()
            self._drag_start_pos = self.pos()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_start_global is not None:
            delta = event.globalPosition().toPoint() - self._drag_start_global
            new_pos = self._drag_start_pos + delta
            parent = self.parentWidget()
            if parent:
                new_x = max(0, min(new_pos.x(), parent.width() - self.width()))
                new_y = max(0, min(new_pos.y(), parent.height() - self.height()))
                self.move(new_x, new_y)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start_global = None
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)


class ManualModeWindow(QMainWindow):
    def __init__(self, main_menu=None):
        super().__init__()
        self.main_menu = main_menu
        self.setWindowTitle("Ручное рисование блок-схемы")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        screen = QApplication.primaryScreen()
        if screen:
            self.resize(screen.availableGeometry().size())

        central = QWidget()
        central.setStyleSheet("background: transparent;")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.header = HeaderBar(self)
        self.header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.header.setStyleSheet("""
            QWidget#headerBar {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #BDD1D5,
                    stop: 1 #97B4BE
                );
                border: none;
            }
        """)
        main_layout.addWidget(self.header)

        self.content = QWidget()
        self.content.setStyleSheet("background: #DDEEF3;")
        main_layout.addWidget(self.content)

        self.canvas_frame = QFrame(self.content)
        self.canvas_frame.setObjectName("canvasFrame")
        self.canvas_frame.setStyleSheet("background: white; border-radius: 0px;")

        self.scene = DiagramScene()
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)
        self.view = QGraphicsView(self.scene, self.canvas_frame)
        self.view.setRenderHints(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setStyleSheet("border: none; background: transparent;")
        self.view.setCursor(Qt.CursorShape.ArrowCursor)

        self.content.installEventFilter(self)

        self.tool_palette = DraggableToolPalette(self.content)
        self.tool_palette.move(30, 30)
        self.tool_palette.raise_()

        self._position_canvas()

        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #BDD1D5,
                    stop: 1 #97B4BE
                );
            }
        """)

    def eventFilter(self, obj, event):
        if obj == self.content and event.type() == QEvent.Type.Resize:
            self._position_canvas()
        return super().eventFilter(obj, event)

    def _position_canvas(self):
        if self.content:
            self.canvas_frame.setGeometry(0, 0, self.content.width(), self.content.height())
            self.view.setGeometry(0, 0, self.content.width(), self.content.height())

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.1 if event.angleDelta().y() > 0 else 0.9
            self.view.scale(factor, factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def on_tool_changed(self, tool_id):
        self.scene.set_tool(tool_id)
        if tool_id in ['line', 'dashed_line', 'arrow_line', 'text']:
            self.view.setCursor(Qt.CursorShape.CrossCursor)
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        elif tool_id is None:
            self.view.setCursor(Qt.CursorShape.ArrowCursor)
            self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        else:
            self.view.setCursor(Qt.CursorShape.CrossCursor)
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def export_png(self):
        """Экспорт сцены в PNG."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как PNG", "flowchart.png", "PNG (*.png)"
        )
        if path:
            rect = self.scene.sceneRect()
            image = QPixmap(int(rect.width()), int(rect.height()))
            image.fill(Qt.GlobalColor.white)
            painter = QPainter(image)
            self.scene.render(painter)
            painter.end()
            if not image.save(path, "PNG"):
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить файл.")
            else:
                QMessageBox.information(self, "Успех", f"Блок-схема сохранена в:\n{path}")

    def export_pdf(self):
        """Экспорт сцены в PDF."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как PDF", "flowchart.pdf", "PDF (*.pdf)"
        )
        if path:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            painter = QPainter(printer)
            self.scene.render(painter)
            painter.end()
            QMessageBox.information(self, "Успех", f"Блок-схема сохранена в:\n{path}")

    def closeEvent(self, event):
        if self.main_menu:
            self.main_menu.show()
        super().closeEvent(event)