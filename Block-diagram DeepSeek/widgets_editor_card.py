# widgets_editor_card.py — редактор с динамической шириной, начальной высотой ~15 строк
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QPlainTextEdit,
    QGraphicsDropShadowEffect, QApplication
)
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import (
    QFont, QColor, QSyntaxHighlighter, QTextCharFormat, QMouseEvent, QFontMetrics
)


class FlowchartHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0000FF"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = ["если", "то", "иначе", "пока", "для", "начало", "конец", "выполнить"]
        for word in keywords:
            self._rules.append((fr"\b{word}\b", keyword_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#008000"))
        comment_format.setFontItalic(True)
        self._rules.append(("//.*", comment_format))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#FF5500"))
        self._rules.append((r"\b\d+\b", number_format))

    def highlightBlock(self, text):
        import re
        for pattern, fmt in self._rules:
            for match in re.finditer(pattern, text):
                start, end = match.start(), match.end()
                self.setFormat(start, end - start, fmt)


class DraggableEditorCard(QFrame):
    MIN_WIDTH = 300
    MAX_WIDTH = 700
    WIDTH_PADDING = 40
    MIN_HEIGHT = 400         # начальная высота (около 15 строк Consolas 11pt)
    MAX_HEIGHT = 600

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("editorCard")
        self._drag_start_global = None
        self._drag_start_pos = None

        self.setMinimumWidth(self.MIN_WIDTH)
        self.setMaximumWidth(self.MAX_WIDTH)
        self.setStyleSheet("""
            #editorCard {
                background: #DDEEF3;
                border-radius: 15px;
            }
        """)

        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(
            "Пример псевдокода:\n"
            "начало\n"
            "  ввод a, b\n"
            "  если a > b то\n"
            "    a = a - b\n"
            "  иначе\n"
            "    b = b - a\n"
            "  конец\n"
            "конец"
        )
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setStyleSheet("""
            QPlainTextEdit {
                background: white;
                border: none;
                border-radius: 10px;
                margin: 12px;
                padding: 8px;
            }
        """)
        editor_shadow = QGraphicsDropShadowEffect()
        editor_shadow.setBlurRadius(12)
        editor_shadow.setOffset(2, 2)
        editor_shadow.setColor(QColor(0, 0, 0, 25))
        self.editor.setGraphicsEffect(editor_shadow)

        self.editor.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.highlighter = FlowchartHighlighter(self.editor.document())
        card_layout.addWidget(self.editor)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 12, 12)
        btn_layout.addStretch()
        self.generate_btn = QPushButton()
        self.generate_btn.setText("▶")
        self.generate_btn.setFixedSize(50, 50)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                border-radius: 25px;
                color: white;
                font-size: 26px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66BB6A;
            }
        """)
        btn_layout.addWidget(self.generate_btn)
        card_layout.addLayout(btn_layout)

        self.editor.textChanged.connect(self.adjust_size)

        # начальная ширина
        self.setFixedWidth(self.MIN_WIDTH)
        # начальная высота (принудительно)
        self.setFixedHeight(self.MIN_HEIGHT)

    def adjust_size(self):
        """Динамически подстраивает высоту и ширину под содержимое."""
        # ----- высота -----
        doc_height = self.editor.document().size().height()
        editor_margins = 24      # 12+12
        btn_area = 74            # высота кнопки и отступов
        desired_height = int(doc_height + editor_margins + btn_area)

        if desired_height <= self.MIN_HEIGHT:
            # содержимое помещается в минимальный размер
            self.setFixedHeight(self.MIN_HEIGHT)
            self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        elif desired_height >= self.MAX_HEIGHT:
            # содержимое слишком велико – фиксируем максимальную высоту и включаем прокрутку
            self.setFixedHeight(self.MAX_HEIGHT)
            self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            # плавающая высота
            self.setFixedHeight(desired_height)
            self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # ----- ширина -----
        fm = QFontMetrics(self.editor.font())
        max_line_width = 0
        text = self.editor.toPlainText()
        for line in text.splitlines():
            line_width = fm.horizontalAdvance(line)
            if line_width > max_line_width:
                max_line_width = line_width

        total_width = max_line_width + self.WIDTH_PADDING
        final_width = max(self.MIN_WIDTH, min(self.MAX_WIDTH, total_width))
        self.setFixedWidth(final_width)

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