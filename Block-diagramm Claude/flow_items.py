import math
from PyQt6.QtWidgets import (
    QGraphicsItem, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QDialog,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont,
    QPolygonF, QPainterPath, QCursor, QLinearGradient
)


HANDLE_SIZE = 8
HANDLE_POSITIONS = [
    "top_left", "top_center", "top_right",
    "mid_left", "mid_right",
    "bot_left", "bot_center", "bot_right",
]
HANDLE_CURSORS = {
    "top_left":    Qt.CursorShape.SizeFDiagCursor,
    "top_center":  Qt.CursorShape.SizeVerCursor,
    "top_right":   Qt.CursorShape.SizeBDiagCursor,
    "mid_left":    Qt.CursorShape.SizeHorCursor,
    "mid_right":   Qt.CursorShape.SizeHorCursor,
    "bot_left":    Qt.CursorShape.SizeBDiagCursor,
    "bot_center":  Qt.CursorShape.SizeVerCursor,
    "bot_right":   Qt.CursorShape.SizeFDiagCursor,
}


def handle_rect(pos_name: str, bounding: QRectF) -> QRectF:
    x, y, w, h = bounding.x(), bounding.y(), bounding.width(), bounding.height()
    hs = HANDLE_SIZE
    centers = {
        "top_left":   QPointF(x,       y),
        "top_center": QPointF(x+w/2,   y),
        "top_right":  QPointF(x+w,     y),
        "mid_left":   QPointF(x,       y+h/2),
        "mid_right":  QPointF(x+w,     y+h/2),
        "bot_left":   QPointF(x,       y+h),
        "bot_center": QPointF(x+w/2,   y+h),
        "bot_right":  QPointF(x+w,     y+h),
    }
    c = centers[pos_name]
    return QRectF(c.x()-hs/2, c.y()-hs/2, hs, hs)


# ── Styled dialog ─────────────────────────────────────────────────────────────

class TextInputDialog(QDialog):
    def __init__(self, current_text: str = "", parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedWidth(340)
        self._result_text = current_text
        self._build_ui(current_text)

    def _build_ui(self, current_text: str):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet(
            "QWidget#card { background-color: #FFFFFF; border-radius: 16px; }"
        )
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 70))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(44)

        def paint_header(event, _h=header):
            p = QPainter(_h)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            g = QLinearGradient(0, 0, _h.width(), 0)
            g.setColorAt(0.0, QColor("#BDD1D5"))
            g.setColorAt(1.0, QColor("#97B4BE"))
            path = QPainterPath()
            path.addRoundedRect(QRectF(_h.rect()), 16, 16)
            path.addRect(QRectF(0, 16, _h.width(), 28))
            p.fillPath(path, QBrush(g))

        header.paintEvent = paint_header

        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 0, 12, 0)
        title_lbl = QLabel("Текст фигуры")
        tf = QFont("Segoe UI", 11)
        tf.setItalic(True)
        title_lbl.setFont(tf)
        title_lbl.setStyleSheet("color: #1B3A45; background: transparent;")
        hl.addWidget(title_lbl)
        hl.addStretch()

        btn_x = QPushButton("✕")
        btn_x.setFixedSize(28, 28)
        btn_x.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,40); color: #1B3A45;
                border: none; border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { background: rgba(220,60,60,180); color: white; }
        """)
        btn_x.clicked.connect(self.reject)
        hl.addWidget(btn_x)
        card_layout.addWidget(header)

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(20, 16, 20, 20)
        bl.setSpacing(16)

        self._edit = QLineEdit(current_text)
        self._edit.setPlaceholderText("Введите текст…")
        self._edit.setFont(QFont("Segoe UI", 11))
        self._edit.setStyleSheet("""
            QLineEdit {
                background-color: #DDEEF3; border: none; border-radius: 10px;
                padding: 10px 14px; color: #1B3A45;
                font-family: 'Segoe UI','Arial',sans-serif;
            }
            QLineEdit:focus { background-color: #CCE5EE; }
        """)
        self._edit.returnPressed.connect(self._accept)
        bl.addWidget(self._edit)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_cancel = QPushButton("Отмена")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #EBF5FF; color: #2C3E50; border: none;
                border-radius: 10px; font-size: 13px; font-style: italic;
                font-family: 'Segoe UI','Arial',sans-serif; padding: 0 18px;
            }
            QPushButton:hover { background-color: #D0E8FA; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Применить")
        btn_ok.setMinimumHeight(38)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; border: none;
                border-radius: 10px; font-size: 13px; font-style: italic;
                font-family: 'Segoe UI','Arial',sans-serif; padding: 0 18px;
            }
            QPushButton:hover { background-color: #43A047; }
        """)
        btn_ok.clicked.connect(self._accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        bl.addLayout(btn_row)
        card_layout.addWidget(body)
        outer.addWidget(card)

    def _accept(self):
        self._result_text = self._edit.text()
        self.accept()

    def get_text(self) -> str:
        return self._result_text


# ── FlowItem ──────────────────────────────────────────────────────────────────

class FlowItem(QGraphicsItem):
    TYPE_RECT       = "rect"
    TYPE_PREDEFINED = "predefined"
    TYPE_DIAMOND    = "diamond"
    TYPE_HEXAGON    = "hexagon"
    TYPE_TERMINATOR = "terminator"
    TYPE_IO         = "io"
    TYPE_MANUAL_OP  = "manual_op"
    TYPE_LOOP_LIMIT = "loop_limit"
    TYPE_CONNECTOR  = "connector"

    MIN_W, MIN_H = 60, 36

    def __init__(self, shape_type: str, x: float, y: float, w=140, h=70):
        super().__init__()
        self._type = shape_type
        self._rect = QRectF(0, 0, w, h)
        self._text = ""

        # resize state — all in scene coordinates
        self._resizing     = None       # active handle name or None
        self._anchor_x     = 0.0       # scene X that must not move
        self._anchor_y     = 0.0       # scene Y that must not move
        self._fix_x        = False     # True when this axis has a fixed anchor
        self._fix_y        = False

        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

    # ── geometry ──────────────────────────────────────────────────────────────
    def boundingRect(self) -> QRectF:
        pad = HANDLE_SIZE + 2
        return self._rect.adjusted(-pad, -pad, pad, pad)

    # ── paint ─────────────────────────────────────────────────────────────────
    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#3A5F6F"), 1.6))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        r, t = self._rect, self._type

        if t == self.TYPE_RECT:
            painter.drawRect(r)
        elif t == self.TYPE_PREDEFINED:
            painter.drawRect(r)
            off = 10
            painter.drawLine(QPointF(r.left()+off,  r.top()),
                             QPointF(r.left()+off,  r.bottom()))
            painter.drawLine(QPointF(r.right()-off, r.top()),
                             QPointF(r.right()-off, r.bottom()))
        elif t == self.TYPE_DIAMOND:
            cx, cy = r.center().x(), r.center().y()
            painter.drawPolygon(QPolygonF([
                QPointF(cx, r.top()), QPointF(r.right(), cy),
                QPointF(cx, r.bottom()), QPointF(r.left(), cy),
            ]))
        elif t == self.TYPE_HEXAGON:
            off = min(r.width() * 0.2, 20)
            cy  = r.center().y()
            painter.drawPolygon(QPolygonF([
                QPointF(r.left()+off,  r.top()),
                QPointF(r.right()-off, r.top()),
                QPointF(r.right(),     cy),
                QPointF(r.right()-off, r.bottom()),
                QPointF(r.left()+off,  r.bottom()),
                QPointF(r.left(),      cy),
            ]))
        elif t == self.TYPE_TERMINATOR:
            painter.drawRoundedRect(r, r.height()/2, r.height()/2)
        elif t == self.TYPE_IO:
            off = r.height() * 0.25
            painter.drawPolygon(QPolygonF([
                QPointF(r.left()+off,  r.top()),
                QPointF(r.right(),     r.top()),
                QPointF(r.right()-off, r.bottom()),
                QPointF(r.left(),      r.bottom()),
            ]))
        elif t == self.TYPE_MANUAL_OP:
            off = r.height() * 0.25
            painter.drawPolygon(QPolygonF([
                QPointF(r.left(),      r.top()),
                QPointF(r.right(),     r.top()),
                QPointF(r.right()-off, r.bottom()),
                QPointF(r.left()+off,  r.bottom()),
            ]))
        elif t == self.TYPE_LOOP_LIMIT:
            rad = min(r.width(), r.height()) * 0.22
            path = QPainterPath()
            path.addRoundedRect(r, rad, rad)
            painter.drawPath(path)
        elif t == self.TYPE_CONNECTOR:
            painter.drawEllipse(r)


        if self._text:
            inner = self._inner_rect()
            font  = self._fit_font(painter, self._text, inner)
            painter.setFont(font)
            painter.setPen(QPen(QColor("#1B3A45")))
            painter.drawText(
                inner,
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                self._text,
            )

        if self.isSelected():
            painter.setPen(QPen(QColor("#4A9CB5"), 1))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            for name in HANDLE_POSITIONS:
                painter.drawRect(handle_rect(name, self._rect))

    def _inner_rect(self) -> QRectF:
        r, t = self._rect, self._type
        ph, pv = r.width() * 0.12, r.height() * 0.12
        if t in (self.TYPE_IO, self.TYPE_MANUAL_OP):
            ph = r.height() * 0.3
        elif t == self.TYPE_DIAMOND:
            ph, pv = r.width() * 0.18, r.height() * 0.18
        return r.adjusted(ph, pv, -ph, -pv)

    def _fit_font(self, painter: QPainter, text: str, rect: QRectF) -> QFont:
        font = QFont("Segoe UI", 10)
        for size in range(12, 5, -1):
            font.setPointSize(size)
            painter.setFont(font)
            bound = painter.boundingRect(rect, Qt.TextFlag.TextWordWrap, text)
            if bound.width() <= rect.width() and bound.height() <= rect.height():
                break
        return font

    def set_text(self, text: str):
        self._text = text
        self.update()

    def get_text(self) -> str:
        return self._text

    # ── handle hit-test ───────────────────────────────────────────────────────
    def _handle_at(self, pos: QPointF) -> str | None:
        for name in HANDLE_POSITIONS:
            if handle_rect(name, self._rect).contains(pos):
                return name
        return None

    # ── hover ─────────────────────────────────────────────────────────────────
    def hoverMoveEvent(self, event):
        h = self._handle_at(event.pos())
        self.setCursor(QCursor(
            HANDLE_CURSORS[h] if h else Qt.CursorShape.SizeAllCursor
        ))
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().hoverLeaveEvent(event)

    # ── mouse ─────────────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        h = self._handle_at(event.pos())
        if h:
            self._resizing = h
            self._setup_anchor(h)
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            event.accept()
        else:
            self._resizing = None
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing:
            self._apply_resize(event.scenePos())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resizing:
            self._resizing = None
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        view = None
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
        dlg = TextInputDialog(self._text, parent=view)
        if view:
            sc = self.mapToScene(self._rect.center())
            vp = view.mapFromScene(sc)
            gp = view.mapToGlobal(vp)
            dlg.move(gp.x() - dlg.width()//2, gp.y() - dlg.height()//2)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.set_text(dlg.get_text())
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            s = self.scene()
            if s:
                s.removeItem(self)
        else:
            super().keyPressEvent(event)

    # ── resize ────────────────────────────────────────────────────────────────
    def _setup_anchor(self, handle: str):
        """
        Record the scene-coordinate of the side/corner that must stay fixed.
        Also record which axes are actually being resized.
        """
        r = self._rect

        # Local coordinates of the FIXED (opposite) point
        # X axis
        if "left" in handle:
            fixed_local_x = r.right()
            self._fix_x   = True
        elif "right" in handle:
            fixed_local_x = r.left()
            self._fix_x   = True
        else:
            fixed_local_x = r.left()   # won't be used
            self._fix_x   = False

        # Y axis
        if "top" in handle:
            fixed_local_y = r.bottom()
            self._fix_y   = True
        elif "bot" in handle:
            fixed_local_y = r.top()
            self._fix_y   = True
        else:
            fixed_local_y = r.top()    # won't be used
            self._fix_y   = False

        # Convert to scene coordinates ONCE and store
        scene_pt       = self.mapToScene(QPointF(fixed_local_x, fixed_local_y))
        self._anchor_x = scene_pt.x()
        self._anchor_y = scene_pt.y()

        # For axes that don't resize, remember current scene bounds so they
        # never drift regardless of how many move steps accumulate
        sp = self.scenePos()
        self._stable_scene_left   = sp.x()
        self._stable_scene_top    = sp.y()
        self._stable_w            = r.width()
        self._stable_h            = r.height()

    def _apply_resize(self, mouse_scene: QPointF):
        """
        Rebuild the item rect so that:
        - the anchor side stays at _anchor_x / _anchor_y  (scene coords)
        - the dragged side follows the mouse
        - the non-resized axes stay exactly where they were at press time
        """
        mx, my = mouse_scene.x(), mouse_scene.y()

        handle = self._resizing

        # ── X axis ────────────────────────────────────────────────────────
        if self._fix_x:
            ax = self._anchor_x
            if "left" in handle:
                # anchor is on the RIGHT, mouse moves the LEFT side
                raw_left  = mx
                raw_right = ax
            else:
                # anchor is on the LEFT, mouse moves the RIGHT side
                raw_left  = ax
                raw_right = mx

            # enforce minimum width keeping anchor side fixed
            if raw_right - raw_left < self.MIN_W:
                if "left" in handle:
                    raw_left = raw_right - self.MIN_W
                else:
                    raw_right = raw_left + self.MIN_W

            new_left = raw_left
            new_w    = raw_right - raw_left
        else:
            # X unchanged — use the values snapshotted at press time
            new_left = self._stable_scene_left
            new_w    = self._stable_w

        # ── Y axis ────────────────────────────────────────────────────────
        if self._fix_y:
            ay = self._anchor_y
            if "top" in handle:
                raw_top    = my
                raw_bottom = ay
            else:
                raw_top    = ay
                raw_bottom = my

            if raw_bottom - raw_top < self.MIN_H:
                if "top" in handle:
                    raw_top = raw_bottom - self.MIN_H
                else:
                    raw_bottom = raw_top + self.MIN_H

            new_top = raw_top
            new_h   = raw_bottom - raw_top
        else:
            new_top = self._stable_scene_top
            new_h   = self._stable_h

        # ── Apply ─────────────────────────────────────────────────────────
        self.prepareGeometryChange()
        self.setPos(new_left, new_top)
        self._rect = QRectF(0, 0, new_w, new_h)
        self.update()