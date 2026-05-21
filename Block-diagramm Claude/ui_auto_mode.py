from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QPlainTextEdit,
    QScrollArea, QSizePolicy, QMessageBox, QMenu,
    QGraphicsDropShadowEffect, QFrame, QFileDialog
)
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import (
    QFont, QPainter, QLinearGradient, QColor, QBrush,
    QSyntaxHighlighter, QTextCharFormat, QAction, QPixmap
)

from core_parser import PseudocodeParser
from core_graphviz import GraphGenerator


# ── Градиентный фон ────────────────────────────────────────────────────────────

class GradientWidget(QWidget):
    def __init__(self, color_start: str, color_end: str,
                 horizontal: bool = True, parent=None):
        super().__init__(parent)
        self._c1 = QColor(color_start)
        self._c2 = QColor(color_end)
        self._horizontal = horizontal

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._horizontal:
            gradient = QLinearGradient(0, 0, self.width(), 0)
        else:
            gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, self._c1)
        gradient.setColorAt(1.0, self._c2)
        painter.fillRect(self.rect(), QBrush(gradient))


# ── Подсветка синтаксиса псевдокода ────────────────────────────────────────────

class FlowchartHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self._rules: list[tuple] = []

        keyword_fmt = QTextCharFormat()
        keyword_fmt.setForeground(QColor("#0066CC"))
        keyword_fmt.setFontWeight(QFont.Weight.Bold)
        keywords = [
            r"\bначало\b", r"\bконец\b", r"\bесли\b", r"\bто\b",
            r"\bиначе\b", r"\bконец\s*если\b", r"\bпока\b",
            r"\bделать\b", r"\bвыполнить\b", r"\bконец\s*пока\b",
            r"\bдля\b", r"\bдо\b", r"\bконец\s*для\b",
            r"\bввод\b", r"\bвывод\b", r"\bвывести\b",
            r"\bstart\b", r"\bend\b", r"\bif\b", r"\bthen\b",
            r"\belse\b", r"\bendif\b", r"\bwhile\b", r"\bdo\b",
            r"\bendwhile\b", r"\bwend\b", r"\bfor\b", r"\bto\b",
            r"\bendfor\b", r"\bnext\b", r"\binput\b", r"\boutput\b",
            r"\bread\b", r"\bwrite\b", r"\bprint\b",
        ]
        for kw in keywords:
            self._rules.append((re.compile(kw, re.IGNORECASE), keyword_fmt))

        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#888888"))
        comment_fmt.setFontItalic(True)
        self._rules.append((re.compile(r"#[^\n]*"), comment_fmt))

        string_fmt = QTextCharFormat()
        string_fmt.setForeground(QColor("#CC6600"))
        self._rules.append((re.compile(r'"[^"]*"'), string_fmt))

        number_fmt = QTextCharFormat()
        number_fmt.setForeground(QColor("#9900AA"))
        self._rules.append((re.compile(r"\b\d+(\.\d+)?\b"), number_fmt))

    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


# ── Главное окно режима автогенерации ──────────────────────────────────────────

class AutoModeWindow(QMainWindow):

    _MENU_STYLE = """
        QMenu {
            background-color: #FFFFFF;
            border: 1px solid #DDEEF3;
            border-radius: 10px;
            padding: 6px;
            font-family: 'Segoe UI', 'Arial', sans-serif;
            font-size: 13px;
            color: #2C3E50;
        }
        QMenu::item {
            padding: 8px 24px 8px 12px;
            border-radius: 6px;
        }
        QMenu::item:selected {
            background-color: #DDEEF3;
            color: #1B3A45;
        }
        QMenu::separator {
            height: 1px;
            background: #DDEEF3;
            margin: 4px 8px;
        }
    """

    _WIN_BTN_BASE = """
        QPushButton {
            background-color: rgba(255,255,255,40);
            color: #1B3A45;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-family: 'Segoe UI','Arial',sans-serif;
            padding: 0px;
        }
        QPushButton:hover   { background-color: rgba(255,255,255,90);  }
        QPushButton:pressed { background-color: rgba(255,255,255,130); }
    """

    _WIN_BTN_CLOSE = """
        QPushButton {
            background-color: rgba(255,255,255,40);
            color: #1B3A45;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-family: 'Segoe UI','Arial',sans-serif;
            padding: 0px;
        }
        QPushButton:hover   { background-color: rgba(220,60,60,200);  color: white; }
        QPushButton:pressed { background-color: rgba(180,30,30,220);  color: white; }
    """

    def __init__(self, main_menu=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FlowChart Designer — Автогенерация")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(900, 600)

        self._main_menu = main_menu
        self._parser    = PseudocodeParser()
        self._generator = GraphGenerator()
        self._drag_pos  = QPoint()
        self._dragging  = False

        # Путь к последнему сгенерированному PNG (для экспорта)
        self._last_png_path: str | None = None

        self._build_ui()

    # ── Построение интерфейса ──────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        root.setStyleSheet("background-color: #FFFFFF;")
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Titlebar
        titlebar = GradientWidget("#BDD1D5", "#97B4BE", horizontal=True)
        titlebar.setFixedHeight(44)
        tb = QHBoxLayout(titlebar)
        tb.setContentsMargins(8, 6, 12, 6)
        tb.setSpacing(6)

        burger_btn = QPushButton("☰")
        burger_btn.setFixedSize(32, 32)
        burger_btn.setStyleSheet(self._WIN_BTN_BASE)
        burger_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        burger_btn.clicked.connect(self._show_burger_menu)
        tb.addWidget(burger_btn)

        title_lbl = QLabel("Создание блок-схемы по алгоритму")
        f = QFont("Segoe UI", 11)
        f.setItalic(True)
        title_lbl.setFont(f)
        title_lbl.setStyleSheet("color: #1B3A45; background: transparent;")
        tb.addWidget(title_lbl)
        tb.addStretch()

        self._status_label = QLabel("Готов к работе")
        self._status_label.setStyleSheet(
            "color: #2C4F5C; background: transparent;"
            "font-size: 11px; font-style: italic;"
        )
        tb.addWidget(self._status_label)
        tb.addSpacing(16)

        btn_min = QPushButton("—")
        btn_min.setFixedSize(32, 32)
        btn_min.setStyleSheet(self._WIN_BTN_BASE)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.clicked.connect(self.showMinimized)
        tb.addWidget(btn_min)

        self._btn_max = QPushButton("□")
        self._btn_max.setFixedSize(32, 32)
        self._btn_max.setStyleSheet(self._WIN_BTN_BASE)
        self._btn_max.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_max.clicked.connect(self._toggle_maximize)
        tb.addWidget(self._btn_max)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(32, 32)
        btn_close.setStyleSheet(self._WIN_BTN_CLOSE)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.close)
        tb.addWidget(btn_close)

        root_layout.addWidget(titlebar)

        # ── Контентная область ─────────────────────────────────────────────────
        content_area = QWidget()
        content_area.setStyleSheet("background-color: #FFFFFF;")
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(28, 24, 28, 24)
        content_layout.setSpacing(24)

        # ── Карточка редактора ─────────────────────────────────────────────────
        editor_card = QWidget()
        editor_card.setObjectName("editorCard")
        editor_card.setStyleSheet("""
            QWidget#editorCard {
                background-color: #DDEEF3;
                border-radius: 16px;
            }
        """)
        editor_card.setMinimumWidth(340)

        card_shadow = QGraphicsDropShadowEffect()
        card_shadow.setBlurRadius(24)
        card_shadow.setOffset(4, 4)
        card_shadow.setColor(QColor(0, 0, 0, 45))
        editor_card.setGraphicsEffect(card_shadow)

        card_layout = QVBoxLayout(editor_card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(8)

        card_title = QLabel("Псевдокод")
        f2 = QFont("Segoe UI", 10)
        f2.setItalic(True)
        card_title.setFont(f2)
        card_title.setStyleSheet("color: #4A7A8A; background: transparent;")
        card_layout.addWidget(card_title)

        editor_wrapper = QWidget()
        editor_wrapper.setStyleSheet("background: transparent;")
        ew_layout = QVBoxLayout(editor_wrapper)
        ew_layout.setContentsMargins(0, 0, 0, 0)
        ew_layout.setSpacing(0)

        self._editor = QPlainTextEdit()
        self._editor.setFont(QFont("Courier New", 11))
        self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 10px;
                color: #1B3A45;
            }
        """)
        self._editor.setPlaceholderText(
            "начало\n"
            "    ввод a, b\n"
            "    если a > b то\n"
            "        вывод a\n"
            "    иначе\n"
            "        вывод b\n"
            "конец"
        )

        editor_shadow = QGraphicsDropShadowEffect()
        editor_shadow.setBlurRadius(12)
        editor_shadow.setOffset(3, 3)
        editor_shadow.setColor(QColor(0, 0, 0, 35))
        self._editor.setGraphicsEffect(editor_shadow)

        self._highlighter = FlowchartHighlighter(self._editor.document())
        ew_layout.addWidget(self._editor)
        card_layout.addWidget(editor_wrapper)

        play_row = QHBoxLayout()
        play_row.setContentsMargins(0, 4, 0, 0)
        play_row.addStretch()

        self._btn_generate = QPushButton("▶")
        self._btn_generate.setFixedSize(48, 48)
        self._btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 24px;
                font-size: 16px;
                padding-left: 3px;
            }
            QPushButton:hover   { background-color: #43A047; }
            QPushButton:pressed { background-color: #388E3C; }
        """)
        self._btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_generate.setToolTip("Сгенерировать блок-схему")
        self._btn_generate.clicked.connect(self._on_generate)
        play_row.addWidget(self._btn_generate)
        card_layout.addLayout(play_row)

        content_layout.addWidget(editor_card, stretch=4)

        # ── Панель превью ──────────────────────────────────────────────────────
        preview_wrapper = QWidget()
        preview_wrapper.setStyleSheet("background: transparent;")
        pw_layout = QVBoxLayout(preview_wrapper)
        pw_layout.setContentsMargins(0, 0, 0, 0)
        pw_layout.setSpacing(0)

        preview_frame = QFrame()
        preview_frame.setObjectName("previewFrame")
        preview_frame.setStyleSheet("""
            QFrame#previewFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)

        preview_shadow = QGraphicsDropShadowEffect()
        preview_shadow.setBlurRadius(24)
        preview_shadow.setOffset(4, 4)
        preview_shadow.setColor(QColor(0, 0, 0, 40))
        preview_frame.setGraphicsEffect(preview_shadow)

        pf_layout = QVBoxLayout(preview_frame)
        pf_layout.setContentsMargins(16, 16, 16, 16)
        pf_layout.setSpacing(0)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll_area.setStyleSheet("""
            QScrollArea { background-color: transparent; border: none; }
            QScrollBar:vertical {
                width: 6px; background: #F0F0F0; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #AACDD6; border-radius: 3px;
            }
            QScrollBar:horizontal {
                height: 6px; background: #F0F0F0; border-radius: 3px;
            }
            QScrollBar::handle:horizontal {
                background: #AACDD6; border-radius: 3px;
            }
        """)

        self._image_label = QLabel("Нажмите ▶ для генерации блок-схемы")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._image_label.setWordWrap(True)
        self._image_label.setStyleSheet(
            "color: #AACDD6; font-size: 14px;"
            "font-style: italic; background: transparent;"
        )

        self._scroll_area.setWidget(self._image_label)
        pf_layout.addWidget(self._scroll_area)

        pw_layout.addWidget(preview_frame)
        content_layout.addWidget(preview_wrapper, stretch=5)

        root_layout.addWidget(content_area, stretch=1)

    # ── Burger-меню ────────────────────────────────────────────────────────────

    def _show_burger_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(self._MENU_STYLE)

        # ── Экспорт PNG ────────────────────────────────────────────────────────
        act_png = QAction("💾  Сохранить как PNG", self)
        act_png.triggered.connect(self._export_png)
        menu.addAction(act_png)

        # ── Экспорт PDF ────────────────────────────────────────────────────────
        act_pdf = QAction("📄  Сохранить как PDF", self)
        act_pdf.triggered.connect(self._export_pdf)
        menu.addAction(act_pdf)

        menu.addSeparator()

        # ── Назад ──────────────────────────────────────────────────────────────
        act_back = QAction("← Назад", self)
        act_back.triggered.connect(self._go_back)
        menu.addAction(act_back)

        btn = self.sender()
        menu.exec(btn.mapToGlobal(QPoint(0, btn.height())))

    # ── Экспорт ────────────────────────────────────────────────────────────────

    def _export_png(self):
        """Сохраняет последнее сгенерированное изображение как PNG."""
        if not self._last_png_path or not Path(self._last_png_path).exists():
            QMessageBox.information(
                self, "Нет изображения",
                "Сначала сгенерируйте блок-схему, нажав ▶."
            )
            return

        dest, _ = QFileDialog.getSaveFileName(
            self, "Сохранить блок-схему как PNG",
            "блок_схема.png",
            "PNG изображения (*.png)"
        )
        if not dest:
            return

        if not dest.lower().endswith(".png"):
            dest += ".png"

        try:
            shutil.copy2(self._last_png_path, dest)
            self._status_label.setText("✓ PNG сохранён")
            QMessageBox.information(
                self, "Готово",
                f"Блок-схема сохранена:\n{dest}"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка сохранения", str(exc))

    def _export_pdf(self):
        """Конвертирует последнее PNG в PDF и сохраняет."""
        if not self._last_png_path or not Path(self._last_png_path).exists():
            QMessageBox.information(
                self, "Нет изображения",
                "Сначала сгенерируйте блок-схему, нажав ▶."
            )
            return

        dest, _ = QFileDialog.getSaveFileName(
            self, "Сохранить блок-схему как PDF",
            "блок_схема.pdf",
            "PDF документы (*.pdf)"
        )
        if not dest:
            return

        if not dest.lower().endswith(".pdf"):
            dest += ".pdf"

        try:
            pixmap = QPixmap(self._last_png_path)
            if pixmap.isNull():
                raise RuntimeError("Не удалось загрузить исходное изображение.")

            from PyQt6.QtGui import QPdfWriter, QPageSize
            from PyQt6.QtCore import QMarginsF, QSizeF

            writer = QPdfWriter(dest)

            # Устанавливаем размер страницы под изображение (в миллиметрах, 96 dpi)
            dpi = 96.0
            mm_per_inch = 25.4
            w_mm = pixmap.width()  / dpi * mm_per_inch
            h_mm = pixmap.height() / dpi * mm_per_inch

            writer.setPageSize(QPageSize(QSizeF(w_mm, h_mm), QPageSize.Unit.Millimeter))
            writer.setPageMargins(QMarginsF(0, 0, 0, 0))
            writer.setResolution(int(dpi))

            painter = QPainter(writer)
            target_rect = painter.viewport()
            painter.drawPixmap(target_rect, pixmap, pixmap.rect())
            painter.end()

            self._status_label.setText("✓ PDF сохранён")
            QMessageBox.information(
                self, "Готово",
                f"Блок-схема сохранена:\n{dest}"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка сохранения PDF", str(exc))

    # ── Навигация ──────────────────────────────────────────────────────────────

    def _go_back(self):
        if self._main_menu is not None:
            self._main_menu.setGeometry(self.geometry())
            if self.isMaximized():
                self._main_menu.showMaximized()
            else:
                self._main_menu.setWindowState(self.windowState())
                self._main_menu.show()
        self.close()

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self._btn_max.setText("□")
        else:
            self.showMaximized()
            self._btn_max.setText("❐")

    # ── Drag оконной рамки ─────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if (event.button() == Qt.MouseButton.LeftButton
                and event.position().y() <= 44):
            self._dragging = True
            self._drag_pos = (event.globalPosition().toPoint()
                              - self.frameGeometry().topLeft())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            if self.isMaximized():
                self.showNormal()
                self._btn_max.setText("□")
                self._drag_pos = QPoint(self.width() // 2, 22)
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)

    # ── Генерация блок-схемы ───────────────────────────────────────────────────

    def _on_generate(self):
        text = self._editor.toPlainText().strip()
        if not text:
            self._status_label.setText("⚠  Редактор пуст")
            return

        ok, msg = self._generator.check_graphviz_installed()
        if not ok:
            QMessageBox.warning(
                self, "Graphviz не найден",
                f"{msg}\n\nУстановите Graphviz и убедитесь, "
                "что папка bin добавлена в PATH."
            )
            self._status_label.setText("✗ Graphviz не найден")
            return

        self._status_label.setText("Разбор псевдокода…")
        parse_result = self._parser.parse(text)

        if not parse_result.is_valid() and not parse_result.nodes:
            errors_str = "\n".join(parse_result.errors)
            QMessageBox.warning(self, "Ошибка парсинга", errors_str)
            self._status_label.setText("✗ Ошибка парсинга")
            return

        self._status_label.setText("Генерация графа…")
        try:
            image_path = self._generator.generate(parse_result)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка генерации", str(exc))
            self._status_label.setText("✗ Ошибка генерации")
            return

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self._status_label.setText("✗ Не удалось загрузить изображение")
            return

        # Сохраняем путь для последующего экспорта
        self._last_png_path = image_path

        self._image_label.setPixmap(pixmap)
        self._image_label.adjustSize()
        self._image_label.setStyleSheet("background: transparent;")

        if parse_result.errors:
            self._status_label.setText(
                f"✓ Готово (предупреждения: {len(parse_result.errors)})"
            )
        else:
            self._status_label.setText("✓ Готово")