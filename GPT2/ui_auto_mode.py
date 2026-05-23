from __future__ import annotations

import tempfile
from pathlib import Path

from PyQt6.QtCore import Qt, QRegularExpression, QSize
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap, QTextCharFormat, QSyntaxHighlighter, QIcon
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect
)

from constants import (
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    KEYWORD_COLOR,
    PREVIEW_MAX_SCALE,
    PREVIEW_MIN_SCALE,
    PREVIEW_SCALE_STEP,
    FramelessWindow,
    TOOLBAR_BG,
    base_font,
)
from core_graphviz import build_graphviz_png
from core_parser import ParseError, parse_pseudocode
from ui_manual_mode import ManualModeWindow


class PseudocodeHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#2B5B84"))
        fmt.setFontWeight(QFont.Weight.Bold)
        keywords = ["НАЧАЛО", "КОНЕЦ", "ВВОД", "ВЫВОД", "ЕСЛИ", "ТО", "ИНАЧЕ", "КОНЕЦ ЕСЛИ", "ПОКА", "КОНЕЦ ПОКА"]
        for kw in keywords:
            self.rules.append((QRegularExpression(rf"\b{QRegularExpression.escape(kw)}\b"), fmt))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class PreviewLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap()
        self._scale = 1.0
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def setPixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self._update_display()

    def zoom(self, factor: float) -> None:
        self._scale = max(PREVIEW_MIN_SCALE, min(PREVIEW_MAX_SCALE, self._scale * factor))
        self._update_display()

    def set_zoom(self, scale: float) -> None:
        self._scale = max(PREVIEW_MIN_SCALE, min(PREVIEW_MAX_SCALE, scale))
        self._update_display()

    def _update_display(self) -> None:
        if self._pixmap.isNull():
            super().setPixmap(QPixmap())
            return
        width = max(1, int(self._pixmap.width() * self._scale))
        height = max(1, int(self._pixmap.height() * self._scale))
        scaled = self._pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
        super().setPixmap(scaled)
        self.adjustSize()


class AutoModeWindow(FramelessWindow):
    def __init__(self, parent=None, previous_window=None):
        super().__init__("Автоматический режим", parent)
        self.previous_window = previous_window
        self.setMinimumSize(1200, 800)
        self.setStyleSheet("background-color: #FFFFFF;")

        # Создание верхней панели (Header) в соответствии с "Mask group.png"
        self.header_panel = QFrame(self)
        self.header_panel.setFixedHeight(45)
        self.header_panel.setStyleSheet("background-color: #B2C8D2; border: none;")
        header_layout = QHBoxLayout(self.header_panel)
        header_layout.setContentsMargins(15, 0, 15, 0)

        self.menu_burger_btn = QPushButton("≡")
        self.menu_burger_btn.setFixedSize(30, 30)
        self.menu_burger_btn.setStyleSheet("font-size: 24px; color: #556B75; background: transparent; border: none;")
        header_layout.addWidget(self.menu_burger_btn, 0, Qt.AlignmentFlag.AlignLeft)
        header_layout.addStretch()

        # Основной контент
        root = QWidget(self)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(30, 20, 30, 20)
        root_layout.setSpacing(40)

        # Левая панель редактора в форме облака ("Mask group.png")
        self.left_container = QFrame(root)
        self.left_container.setFixedSize(360, 520)
        self.left_container.setStyleSheet("background-color: #DCEDF6; border-radius: 40px;")

        # Эффект тени для панели редактора
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(4, 10)
        self.left_container.setGraphicsEffect(shadow)

        left_layout = QVBoxLayout(self.left_container)
        left_layout.setContentsMargins(25, 25, 25, 25)

        self.editor = QPlainTextEdit(self.left_container)
        self.editor.setFont(base_font("Courier New", DEFAULT_FONT_SIZE))
        self.editor.setPlaceholderText("НАЧАЛО\nВВОД A\n...")
        self.editor.setStyleSheet("background: transparent; border: none; color: #4A5A62;")
        self.highlighter = PseudocodeHighlighter(self.editor.document())
        left_layout.addWidget(self.editor, 1)

        # Круглая неоново-зеленая кнопка запуска "▶" в углу редактора
        self.generate_btn = QPushButton("▶", self.left_container)
        self.generate_btn.setFixedSize(44, 44)
        self.generate_btn.setStyleSheet(
            """
            QPushButton {
                background: #86FFA2;
                border: none;
                color: #204A27;
                font-size: 16px;
                font-weight: bold;
                border-radius: 22px;
            }
            QPushButton:hover { background: #6EFF8F; }
            """
        )
        self.generate_btn.clicked.connect(self.generate_flowchart)
        left_layout.addWidget(self.generate_btn, 0, Qt.AlignmentFlag.AlignRight)

        # Правая панель холста визуализации
        right = QFrame(root)
        right.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_container = QScrollArea(right)
        self.preview_container.setWidgetResizable(True)
        self.preview_container.setStyleSheet("QScrollArea { border: none; background: #FFFFFF; }")
        self.preview_label = PreviewLabel()
        self.preview_container.setWidget(self.preview_label)
        right_layout.addWidget(self.preview_container, 1)

        # Тулбар масштабирования/экспорта (аккуратно снизу)
        self.preview_toolbar = QFrame(right)
        self.preview_toolbar.setStyleSheet(f"background: #F0F4F6; border-radius: 12px;")
        ptl = QHBoxLayout(self.preview_toolbar)
        ptl.setContentsMargins(8, 6, 8, 6)
        ptl.setSpacing(6)

        self.zoom_out_btn = QPushButton("-")
        self.zoom_pct_btn = QPushButton("100%")
        self.zoom_in_btn = QPushButton("+")
        self.save_png_btn = QPushButton("Сохранить")
        self.send_manual_btn = QPushButton("Редактировать вручную")

        for btn in (self.zoom_out_btn, self.zoom_pct_btn, self.zoom_in_btn, self.save_png_btn, self.send_manual_btn):
            btn.setFixedHeight(32)
            btn.setStyleSheet(
                "QPushButton { background: white; border: 1px solid #CCD6DB; border-radius: 6px; padding: 0 12px; }")
            ptl.addWidget(btn)

        self.zoom_out_btn.clicked.connect(lambda: self.zoom_preview(1 / PREVIEW_SCALE_STEP))
        self.zoom_in_btn.clicked.connect(lambda: self.zoom_preview(PREVIEW_SCALE_STEP))
        self.zoom_pct_btn.clicked.connect(self.reset_preview_zoom)
        self.save_png_btn.clicked.connect(self.save_preview_png)
        self.send_manual_btn.clicked.connect(self.send_to_manual)
        right_layout.addWidget(self.preview_toolbar, 0)

        root_layout.addWidget(self.left_container)
        root_layout.addWidget(right, 1)

        # Компоновка хедера и тела
        main_area = QWidget(self)
        main_vbox = QVBoxLayout(main_area)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)
        main_vbox.addWidget(self.header_panel)
        main_vbox.addWidget(root)

        self.body_layout.addWidget(main_area)

    def generate_flowchart(self) -> None:
        try:
            nodes, edges = parse_pseudocode(self.editor.toPlainText())
        except ParseError as exc:
            QMessageBox.warning(self, "Ошибка разбора", str(exc))
            return
        temp_dir = Path(tempfile.gettempdir())
        png_path = temp_dir / "flowchart_preview.png"
        result = build_graphviz_png(nodes, edges, str(png_path), self)
        if result:
            self._preview_png = result
            pixmap = QPixmap(result)
            self.preview_label.set_zoom(1.0)
            self.preview_label.setPixmap(pixmap)
            self._current_scale = 1.0
            self.zoom_pct_btn.setText("100%")

    def zoom_preview(self, factor: float) -> None:
        self.preview_label.zoom(factor)
        self._current_scale = max(PREVIEW_MIN_SCALE, min(PREVIEW_MAX_SCALE, self._current_scale * factor))
        self.zoom_pct_btn.setText(f"{int(self._current_scale * 100)}%")

    def reset_preview_zoom(self) -> None:
        self.preview_label.set_zoom(1.0)
        self._current_scale = 1.0
        self.zoom_pct_btn.setText("100%")

    def save_preview_png(self) -> None:
        if not self._preview_png:
            QMessageBox.information(self, "Сохранение", "Сначала сгенерируйте схему.")
            return
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить PNG", "flowchart.png", "PNG Images (*.png)")
        if filepath:
            Path(filepath).write_bytes(Path(self._preview_png).read_bytes())

    def send_to_manual(self) -> None:
        try:
            nodes, edges = parse_pseudocode(self.editor.toPlainText())
        except ParseError as exc:
            QMessageBox.warning(self, "Ошибка разбора", str(exc))
            return
        self.manual_window = ManualModeWindow(previous_window=self)
        self.manual_window.load_graph_data(nodes, edges)
        self.hide()
        self.manual_window.show()

    def closeEvent(self, event):
        if self.previous_window is not None:
            self.previous_window.show()
        super().closeEvent(event)