from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter


class CanvasView(QGraphicsView):
    ZOOM_FACTOR      = 1.15
    ZOOM_MIN, ZOOM_MAX = 0.05, 20.0

    mouse_pressed  = pyqtSignal(QPointF)
    mouse_moved    = pyqtSignal(QPointF)
    mouse_released = pyqtSignal(QPointF)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("border: none; background: transparent;")
        self._panning   = False
        self._pan_start = QPoint()
        self._drawing_line = False

    def set_drawing_mode(self, active: bool):
        self._drawing_line = active
        self.setCursor(
            Qt.CursorShape.CrossCursor if active else Qt.CursorShape.ArrowCursor
        )

    def wheelEvent(self, event):
        delta  = event.angleDelta().y()
        factor = self.ZOOM_FACTOR if delta > 0 else 1.0 / self.ZOOM_FACTOR
        if self.ZOOM_MIN <= self.transform().m11() * factor <= self.ZOOM_MAX:
            self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning   = True
            self._pan_start = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        if self._drawing_line and event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed.emit(self.mapToScene(event.position().toPoint()))
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            d = event.position().toPoint() - self._pan_start
            self._pan_start = event.position().toPoint()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - d.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - d.y())
            return
        if self._drawing_line:
            self.mouse_moved.emit(self.mapToScene(event.position().toPoint()))
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(
                Qt.CursorShape.CrossCursor if self._drawing_line
                else Qt.CursorShape.ArrowCursor
            )
            return
        if self._drawing_line and event.button() == Qt.MouseButton.LeftButton:
            self.mouse_released.emit(self.mapToScene(event.position().toPoint()))
            return
        super().mouseReleaseEvent(event)