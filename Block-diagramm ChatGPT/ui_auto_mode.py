from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import (
    QColor,
    QTextCharFormat,
    QSyntaxHighlighter,
    QPixmap,
    QFont
)

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QPlainTextEdit,
    QFileDialog,
    QMessageBox,
    QScrollArea
)

from core_parser import (
    PseudoCodeParser,
    ParseError
)

from core_graphviz import GraphvizGenerator
from ui_manual_mode import ManualModeWindow


# =========================================================
# HIGHLIGHTER
# =========================================================

class Highlighter(QSyntaxHighlighter):

    def __init__(self, doc):

        super().__init__(doc)

        self.words = [
            "НАЧАЛО",
            "КОНЕЦ",
            "ЕСЛИ",
            "ИНАЧЕ",
            "ТО",
            "ПОКА",
            "КОНЕЦ ЕСЛИ",
            "КОНЕЦ ПОКА",
            "ВВОД",
            "ВЫВОД"
        ]

        self.format = QTextCharFormat()

        self.format.setForeground(
            QColor("#1565C0")
        )

    def highlightBlock(self, text):

        upper = text.upper()

        for word in self.words:

            if word in upper:

                start = upper.index(word)

                self.setFormat(
                    start,
                    len(word),
                    self.format
                )


# =========================================================
# WINDOW
# =========================================================

class AutoModeWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.drag_pos = QPoint()

        self.parser = PseudoCodeParser()

        self.generator = GraphvizGenerator(self)

        self.scale_factor = 1.0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
        )

        self.resize(1280, 720)

        self.setStyleSheet("""
            QWidget{
                background:#ECECEC;
            }
        """)

        self.setup_ui()

    # =====================================================
    # UI
    # =====================================================

    def setup_ui(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # =========================================
        # TOP BAR
        # =========================================

        bar = QWidget()

        bar.setFixedHeight(52)

        bar.setStyleSheet("""
            background:qlineargradient(
                x1:0,
                y1:0,
                x2:1,
                y2:1,
                stop:0 #BDD1D5,
                stop:1 #A9C0C8
            );
        """)

        bar_layout = QHBoxLayout(bar)

        burger = QPushButton("☰")

        burger.setFixedSize(42, 36)

        burger.setStyleSheet("""
            QPushButton{
                background:transparent;
                border:none;
                color:#6E7E84;
                font-size:28px;
            }
        """)

        burger.clicked.connect(self.close)

        bar_layout.addWidget(burger)

        bar_layout.addStretch()

        root.addWidget(bar)

        # =========================================
        # CONTENT
        # =========================================

        content = QWidget()

        content_layout = QHBoxLayout(content)

        content_layout.setContentsMargins(
            16,
            16,
            16,
            16
        )

        # =========================================
        # LEFT PANEL
        # =========================================

        left = QWidget()

        left.setFixedWidth(390)

        left.setStyleSheet("""
            background:#BDD1D5;
            border-radius:34px;
        """)

        left_layout = QVBoxLayout(left)

        left_layout.setContentsMargins(
            34,
            34,
            34,
            34
        )

        self.editor = QPlainTextEdit()

        self.editor.setPlaceholderText(
            "НАЧАЛО\n"
            "ВВОД A\n"
            "ЕСЛИ A > 0 ТО\n"
            "ВЫВОД A\n"
            "КОНЕЦ ЕСЛИ\n"
            "КОНЕЦ"
        )

        self.editor.setStyleSheet("""
            QPlainTextEdit{
                background:transparent;
                border:none;
                font-size:15px;
                color:#4A4A4A;
            }
        """)

        self.editor.setFont(
            QFont("Consolas", 14)
        )

        Highlighter(
            self.editor.document()
        )

        left_layout.addWidget(self.editor)

        # PLAY BUTTON

        play_row = QHBoxLayout()

        play_row.addStretch()

        play = QPushButton("▶")

        play.setFixedSize(44, 44)

        play.setStyleSheet("""
            QPushButton{
                background:#54E07B;
                border:none;
                border-radius:22px;
                color:white;
                font-size:18px;
            }

            QPushButton:hover{
                background:#43D86D;
            }
        """)

        play.clicked.connect(self.generate)

        play_row.addWidget(play)

        left_layout.addLayout(play_row)

        content_layout.addWidget(left)

        # =========================================
        # RIGHT
        # =========================================

        right = QWidget()

        right_layout = QVBoxLayout(right)

        toolbar = QHBoxLayout()

        for text, callback in [
            ("−", self.zoom_out),
            ("100%", self.reset_zoom),
            ("+", self.zoom_in),
            ("PNG", self.save_png),
            ("✎", self.edit_manual)
        ]:

            btn = QPushButton(text)

            btn.setFixedHeight(36)

            btn.setStyleSheet("""
                QPushButton{
                    background:white;
                    border:none;
                    border-radius:14px;
                    padding:0 16px;
                    font-size:15px;
                }

                QPushButton:hover{
                    background:#E6EEF3;
                }
            """)

            btn.clicked.connect(callback)

            toolbar.addWidget(btn)

        toolbar.addStretch()

        self.preview = QLabel()

        self.preview.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setWidget(self.preview)

        scroll.setStyleSheet("""
            QScrollArea{
                border:none;
                background:#ECECEC;
            }
        """)

        right_layout.addLayout(toolbar)
        right_layout.addWidget(scroll)

        content_layout.addWidget(right, 1)

        root.addWidget(content)

    # =====================================================
    # GENERATE
    # =====================================================

    def generate(self):

        try:

            nodes, edges = self.parser.parse(
                self.editor.toPlainText()
            )

            graph = self.generator.build_graph(
                nodes,
                edges
            )

            path = "preview"

            graph.render(
                path,
                format="png",
                cleanup=True
            )

            self.current_pixmap = QPixmap(
                path + ".png"
            )

            self.update_preview()

        except ParseError as e:

            QMessageBox.warning(
                self,
                "Ошибка",
                str(e)
            )

    # =====================================================
    # PREVIEW
    # =====================================================

    def update_preview(self):

        if not hasattr(
            self,
            "current_pixmap"
        ):
            return

        scaled = self.current_pixmap.scaled(
            self.current_pixmap.size()
            * self.scale_factor,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.preview.setPixmap(scaled)

    # =====================================================
    # ZOOM
    # =====================================================

    def zoom_in(self):

        self.scale_factor *= 1.15

        self.update_preview()

    def zoom_out(self):

        self.scale_factor *= 0.85

        self.update_preview()

    def reset_zoom(self):

        self.scale_factor = 1.0

        self.update_preview()

    # =====================================================
    # SAVE
    # =====================================================

    def save_png(self):

        if not hasattr(
            self,
            "current_pixmap"
        ):
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "PNG",
            "",
            "PNG (*.png)"
        )

        if path:

            self.current_pixmap.save(path)

    # =====================================================
    # MANUAL
    # =====================================================

    def edit_manual(self):

        self.window = ManualModeWindow()

        self.window.show()

    # =====================================================
    # DRAG
    # =====================================================

    def mousePressEvent(self, event):

        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):

            self.drag_pos = (
                event.globalPosition().toPoint()
            )

    def mouseMoveEvent(self, event):

        if (
            event.buttons()
            == Qt.MouseButton.LeftButton
        ):

            delta = (
                event.globalPosition().toPoint()
                - self.drag_pos
            )

            self.move(
                self.pos() + delta
            )

            self.drag_pos = (
                event.globalPosition().toPoint()
            )