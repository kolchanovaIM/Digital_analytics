from __future__ import annotations

import os
from pathlib import Path
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QPointF, QRectF, QRegularExpression
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QPlainTextEdit,
    QGraphicsView, QGraphicsScene, QPushButton, QFileDialog, QMessageBox, QFrame,
    QGraphicsDropShadowEffect, QInputDialog, QSizePolicy, QLabel, QApplication  # <--- Добавьте QSizePolicy сюда
)
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QSyntaxHighlighter, QTextCharFormat,
    QFont, QBrush, QPolygonF, QPainterPath, QLinearGradient
)
from constants import FramelessWindow, base_font, make_tool_button, SCENE_RECT
from core_parser import parse_pseudocode
from export_utils import export_scene_to_png, export_scene_to_pdf
from flowchart_items_2 import FlowchartItem, ManualArrowItem, CommentItem
from line_items import ArrowLine


class PseudocodeHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.formats = {}

        # Настройка цветов
        blue_format = QTextCharFormat()
        blue_format.setForeground(QColor("#1A5F7A"))
        blue_format.setFontWeight(QFont.Weight.Bold)

        orange_format = QTextCharFormat()
        orange_format.setForeground(QColor("#F57C00"))
        orange_format.setFontWeight(QFont.Weight.Bold)

        green_format = QTextCharFormat()
        green_format.setForeground(QColor("#4CAF50"))
        green_format.setFontItalic(True)

        # Регистрация ключевых слов
        keywords_blue = [
            "НАЧАЛО", "КОНЕЦ", "ЕСЛИ", "ТО", "ИНАЧЕ", "КОНЕЦ ЕСЛИ", "КОНЕЦ_ЕСЛИ",
            "ПОКА", "ВЫПОЛНИТЬ", "КОНЕЦ ПОКА", "КОНЕЦ_ПОКА", "ФУНКЦИЯ", "ПРОЦЕДУРА",
            "ПОДПРОГРАММА", "ПАРАЛЛЕЛЬНО", "КОНЕЦ ПАРАЛЛЕЛЬНО", "ГРАНИЦА ЦИКЛА НАЧАЛО:",
            "ГРАНИЦА ЦИКЛА КОНЕЦ", "ГРАНИЦА_ЦИКЛА_НАЧАЛО:", "ГРАНИЦА_ЦИКЛА_КОНЕЦ"
        ]
        for kw in keywords_blue:
            self.formats[kw] = blue_format

        keywords_orange = ["ВВОД", "ВЫВОД", "INPUT", "OUTPUT", "READ", "WRITE", "PRINT"]
        for kw in keywords_orange:
            self.formats[kw] = orange_format

        # Комментарии отдельно
        self.comment_keywords = ["КОММЕНТАРИЙ", "COMMENT", "REM", "//"]
        self.comment_format = green_format

    def highlightBlock(self, text: str) -> None:
        upper_text = text.upper()

        # 1. Проверяем наличие комментариев в строке
        for c_kw in self.comment_keywords:
            idx = upper_text.find(c_kw)
            if idx != -1:
                # Подсвечиваем всю оставшуюся часть строки как комментарий
                self.setFormat(idx, len(text) - idx, self.comment_format)
                # Подсвечиваем ключевые слова только ДО комментария
                upper_text = upper_text[:idx]
                break

        # 2. Подсветка обычных ключевых слов через substring-поиск
        for kw, fmt in self.formats.items():
            start = 0
            while True:
                start = upper_text.find(kw, start)
                if start == -1:
                    break

                # Проверяем границы слова, чтобы "ТО" не подсвечивалось внутри "ГОТОВО"
                before_ok = (start == 0 or not upper_text[start - 1].isalnum() and upper_text[start - 1] != '_')
                end_idx = start + len(kw)
                after_ok = (end_idx == len(upper_text) or not upper_text[end_idx].isalnum() and upper_text[
                    end_idx] != '_')

                if before_ok and after_ok:
                    self.setFormat(start, len(kw), fmt)

                start += len(kw)

    def _is_whole_word(self, text: str, start: int, length: int) -> bool:
        """
        Проверяет, является ли найденная подстрока отдельным словом.
        Защищает от ложного выделения (например, чтобы "ВВОД" не подсвечивался внутри гипотетического "ВВОДНЫЙ").
        """
        # Проверка символа перед словом
        if start > 0:
            prev_char = text[start - 1]
            if prev_char.isalnum() or prev_char == '_':
                return False

        # Проверка символа после слова
        end = start + length
        if end < len(text):
            next_char = text[end]
            if next_char.isalnum() or next_char == '_':
                return False

        return True

class LineNumberArea(QWidget):
    def __init__(self, editor: CodeEditorWithInumbering):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self.code_editor.line_number_area_paint_event(event)


class CodeEditorWithInumbering(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)

    def line_number_area_width(self) -> int:
        digits = 1
        max_blocks = max(1, self.blockCount())
        while max_blocks >= 10:
            max_blocks /= 10
            digits += 1
        space = 14 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy) -> None:
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRectF(cr.left(), cr.top(), self.line_number_area_width(), cr.height()).toRect())

    def line_number_area_paint_event(self, event) -> None:
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(0, 0, 0, 10))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#7F8C8D"))
                painter.setFont(self.font())
                painter.drawText(0, top, self.line_number_area.width() - 8, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1


class ShapeToolButton(QPushButton):
    def __init__(self, shape_type: str, parent=None):
        super().__init__(parent)
        self.shape_type = shape_type
        self.setFixedSize(46, 46)
        self.setCheckable(True)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pen = QPen(QColor("#17333D"), 2)
        if self.isChecked():
            pen.setColor(QColor("#FFFFFF"))
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        margin = 8
        w = self.width() - 2 * margin
        h = self.height() - 2 * margin
        rect = QRectF(margin, margin, w, h)
        mid_y = rect.top() + h / 2

        if self.shape_type == "process":
            painter.drawRect(rect)
        elif self.shape_type == "circle":
            painter.drawEllipse(rect)
        elif self.shape_type == "decision":
            points = [QPointF(rect.left() + w / 2, rect.top()), QPointF(rect.right(), mid_y),
                      QPointF(rect.left() + w / 2, rect.bottom()), QPointF(rect.left(), mid_y)]
            painter.drawPolygon(QPolygonF(points))
        elif self.shape_type == "io":
            offset = 8
            points = [QPointF(rect.left() + offset, rect.top()), QPointF(rect.right(), rect.top()),
                      QPointF(rect.right() - offset, rect.bottom()), QPointF(rect.left(), rect.bottom())]
            painter.drawPolygon(QPolygonF(points))
        elif self.shape_type == "top_half_circle":
            path = QPainterPath()
            path.moveTo(rect.left(), rect.bottom())
            path.lineTo(rect.right(), rect.bottom())
            path.lineTo(rect.right(), rect.top() + h / 2)
            path.arcTo(rect, 0, 180)
            path.lineTo(rect.left(), rect.bottom())
            path.closeSubpath()
            painter.drawPath(path)

        elif self.shape_type == "bottom_half_circle":
            path = QPainterPath()
            path.moveTo(rect.left(), rect.top())
            path.lineTo(rect.right(), rect.top())
            path.lineTo(rect.right(), rect.bottom() - h / 2)
            path.arcTo(rect, 0, -180)
            path.lineTo(rect.left(), rect.top())
            path.closeSubpath()
            painter.drawPath(path)
        elif self.shape_type == "inv_trapezoid":
            offset = 8
            points = [QPointF(rect.left(), rect.top()), QPointF(rect.right(), rect.top()),
                      QPointF(rect.right() - offset, rect.bottom()), QPointF(rect.left() + offset, rect.bottom())]
            painter.drawPolygon(QPolygonF(points))
        elif self.shape_type == "rounded_rect":
            painter.drawRoundedRect(rect, 6, 6)
        elif self.shape_type == "double_rect":
            painter.drawRect(rect)
            offset = 6
            painter.drawLine(QPointF(rect.left() + offset, rect.top()), QPointF(rect.left() + offset, rect.bottom()))
            painter.drawLine(QPointF(rect.right() - offset, rect.top()), QPointF(rect.right() - offset, rect.bottom()))
        elif self.shape_type == "hexagon":
            offset = 8
            points = [QPointF(rect.left() + offset, rect.top()), QPointF(rect.right() - offset, rect.top()),
                      QPointF(rect.right(), mid_y), QPointF(rect.right() - offset, rect.bottom()),
                      QPointF(rect.left() + offset, rect.bottom()), QPointF(rect.left(), mid_y)]
            painter.drawPolygon(QPolygonF(points))
        elif self.shape_type == "solid_line":
            painter.drawLine(QPointF(rect.left(), mid_y), QPointF(rect.right(), mid_y))
        elif self.shape_type == "arrow_line":
            painter.drawLine(QPointF(rect.left(), mid_y), QPointF(rect.right(), mid_y))
            painter.drawLine(QPointF(rect.right(), mid_y), QPointF(rect.right() - 6, mid_y - 4))
            painter.drawLine(QPointF(rect.right(), mid_y), QPointF(rect.right() - 6, mid_y + 4))
        elif self.shape_type == "dashed_line":
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(QPointF(rect.left(), mid_y), QPointF(rect.right(), mid_y))


class FlowchartGraphicsView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, editor_window: EditorWindow):
        super().__init__(scene)
        self.editor_window = editor_window
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.GRID_STEP = 20
        self.export_mode = False
        if self.editor_window.manual_mode:
            scene.setBackgroundBrush(QColor("#E2E5E6"))
        else:
            scene.setBackgroundBrush(QColor("#FFFFFF"))

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:

        # Во время экспорта вообще не рисуем фон
        if self.export_mode:
            return

        super().drawBackground(painter, rect)

        if not self.editor_window.manual_mode:
            return

        left = int(rect.left()) - (int(rect.left()) % self.GRID_STEP)
        top = int(rect.top()) - (int(rect.top()) % self.GRID_STEP)

        pen = QPen(QColor("#D0D5D7"), 1, Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        for x in range(left, int(rect.right()), self.GRID_STEP):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))

        for y in range(top, int(rect.bottom()), self.GRID_STEP):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

    def wheelEvent(self, event) -> None:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            zoom_in_factor = 1.15
            zoom_out_factor = 1 / zoom_in_factor
            old_pos = self.mapToScene(event.position().toPoint())
            if event.angleDelta().y() > 0:
                self.scale(zoom_in_factor, zoom_in_factor)
            else:
                self.scale(zoom_out_factor, zoom_out_factor)
            new_pos = self.mapToScene(event.position().toPoint())
            delta = new_pos - old_pos
            self.translate(delta.x(), delta.y())
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event) -> None:
        # Строгая проверка: инструмент должен срабатывать ТОЛЬКО в ручном режиме
        # и только если пользователь кликает по пустому месту сцены, а не по кнопкам/элементам
        if self.editor_window.manual_mode and self.editor_window.current_tool:
            if event.button() == Qt.MouseButton.LeftButton:
                # Проверяем, нет ли под курсором уже существующего FlowchartItem
                item_at_click = self.itemAt(event.position().toPoint())
                if item_at_click is not None and isinstance(item_at_click, FlowchartItem):
                    # Если кликнули на существующий блок, даем Qt обработать выделение/перетаскивание
                    super().mousePressEvent(event)
                    return

                scene_pos = self.mapToScene(event.position().toPoint())
                snap_x = round(scene_pos.x() / self.GRID_STEP) * self.GRID_STEP
                snap_y = round(scene_pos.y() / self.GRID_STEP) * self.GRID_STEP
                current_tool = self.editor_window.current_tool

                if current_tool in ["solid_line", "arrow_line", "dashed_line"]:
                    arrow = ManualArrowItem(line_type=current_tool)
                    arrow._p_start = QPointF(snap_x, snap_y)
                    arrow._p_mid = QPointF(snap_x + 40, snap_y)
                    arrow._p_end = QPointF(snap_x + 80, snap_y)
                    arrow.update_handle_positions()
                    self.scene().addItem(arrow)
                    self.scene().clearSelection()
                    arrow.setSelected(True)
                    self.editor_window.reset_tool_selection()
                    return
                else:
                    item = FlowchartItem("Текст", current_tool)
                    item.setPos(snap_x - item.rect.width() / 2, snap_y - item.rect.height() / 2)
                    self.scene().addItem(item)
                    self.scene().clearSelection()
                    item.setSelected(True)
                    self.editor_window.reset_tool_selection()
                    return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        item = self.itemAt(event.position().toPoint())
        if isinstance(item, FlowchartItem):
            old_text = item.text
            new_text, ok = QInputDialog.getMultiLineText(self, "Редактирование блока", "Введите текст для блока:", old_text)
            if ok:
                item.text = new_text if new_text.strip() else " "
                self.fit_text_to_item(item)
                item.prepareGeometryChange()
                item.update()
            return
        super().mouseDoubleClickEvent(event)

    def fit_text_to_item(self, item: FlowchartItem):
        from PyQt6.QtGui import QTextDocument
        font = base_font()
        current_size = 12
        font.setPointSize(current_size)
        padding = 12
        max_w = max(10.0, item.rect.width() - (padding * 2))
        max_h = max(10.0, item.rect.height() - (padding * 2))

        if item.shape_type in ["decision", "if", "условие", "если", "io", "ввод", "вывод"]:
            max_w -= 15

        doc = QTextDocument()
        loop_guard = 0
        while current_size > 5 and loop_guard < 20:
            font.setPointSize(current_size)
            doc.setDefaultFont(font)
            doc.setTextWidth(max_w)
            doc.setPlainText(item.text)

            if doc.size().height() <= max_h:
                break

            current_size -= 1
            loop_guard += 1

        item.custom_font = font


class EditorWindow(FramelessWindow):
    def __init__(self, main_menu_callback, manual_mode: bool = False, parent=None):
        super().__init__("", parent)

        # Скрываем текстовый лейбл заголовка, если он есть в title_bar
        if hasattr(self, 'title_bar'):
            for child in self.title_bar.findChildren(QLabel):
                child.hide()
        self.main_menu_callback = main_menu_callback
        self.manual_mode = manual_mode
        self.current_tool = None
        self.returning_to_menu = False
        self.resize(1100, 750)

        # Перекраска верхней панели (title_bar) в небесно-голубой градиент главного меню
        if hasattr(self, 'title_bar'):
            self.title_bar.setObjectName("TitleBar")
            # Устанавливаем прозрачный фон для кнопок, чтобы градиент был виден сквозь них
            self.title_bar.setStyleSheet("""
                        QPushButton {
                            background-color: transparent; 
                            border: none;
                        }
                    """)
            self.title_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            # Скрываем текстовый заголовок
            for child in self.title_bar.findChildren(QLabel):
                child.hide()

            # Принудительное растяжение
            self.title_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            # Скрываем текстовый заголовок, как вы и просили
            for child in self.title_bar.findChildren(QLabel):
                child.hide()

        content_widget = QWidget()
        self.body_layout.addWidget(content_widget, 1)

        self.main_layout = QHBoxLayout(content_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.scene = QGraphicsScene(-SCENE_RECT // 2, -SCENE_RECT // 2, SCENE_RECT, SCENE_RECT)
        self.view = FlowchartGraphicsView(self.scene, self)
        self.main_layout.addWidget(self.view, 1)

        if self.manual_mode:
            self._init_floating_toolbar()
        else:
            self._init_floating_code_editor()

        self._init_burger_menu()

        # Создаем кнопку бургер-меню
        self.burger_btn = make_tool_button("☰", "Открыть меню")
        self.burger_btn.setFixedSize(36, 36)

        # Стилизуем кнопку под светлый/голубой градиент панели (текст темно-синий)
        self.burger_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #17333D;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(23, 51, 61, 0.1);
                border-radius: 4px;
            }
        """)
        self.burger_btn.clicked.connect(self.toggle_burger_menu)

        # Интегрируем кнопку в крайнюю левую часть верхней панели
        if hasattr(self, 'title_bar') and self.title_bar.layout():
            # Вставляем кнопку в самый левый угол верхнего бара (индекс 0)
            self.title_bar.layout().insertWidget(0, self.burger_btn)
        else:
            # Резервный вариант, если слоя нет
            self.burger_btn.setParent(self)
            self.burger_btn.move(10, 4)
            self.burger_btn.raise_()

    def _init_floating_code_editor(self):
        self.floating_panel = QFrame(self)
        self.floating_panel.setObjectName("FloatingEditor")
        self.floating_panel.setStyleSheet(
            """
            QFrame#FloatingEditor { 
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1, 
                    stop: 0 #DDEDF3, stop: 1 #BACCD4
                ); 
                border-radius: 36px; 
                border: 1px solid rgba(151, 180, 190, 0.5); 
            }
            QPlainTextEdit { background-color: transparent; border: none; color: #17333D; padding-right: 35px; }
            """
        )
        self.panel_width = 360
        self.panel_height = 460
        self.floating_panel.setGeometry(25, 120, self.panel_width, self.panel_height)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 45))
        shadow.setOffset(4, 10)
        self.floating_panel.setGraphicsEffect(shadow)

        panel_layout = QVBoxLayout(self.floating_panel)
        panel_layout.setContentsMargins(25, 25, 25, 25)

        self.code_edit = CodeEditorWithInumbering()
        self.code_edit.setFont(base_font())
        self.code_edit.setPlaceholderText("НАЧАЛО\nВВЕДИ x\nЕСЛИ x > 0 ТО\n  ВЫВОД x\nИНАЧЕ\n  ВЫВОД -x\nКОНЕЦ ЕСЛИ\nКОНЕЦ")
        panel_layout.addWidget(self.code_edit)

        self.highlighter = PseudocodeHighlighter(self.code_edit.document())

        self.btn_compile = QPushButton("▶", self.floating_panel)
        self.btn_compile.setFixedSize(46, 46)
        self.btn_compile.setStyleSheet(
            """
            QPushButton { background-color: #A3D3C4; border-radius: 23px; border: none; font-size: 16px; color: #2ECC71; font-weight: bold; padding-left: 2px; }
            QPushButton:hover { background-color: #B4E2D5; color: #27AE60; }
            QPushButton:pressed { background-color: #92C4B5; }
            """
        )
        self.btn_compile.clicked.connect(self.refresh_flowchart)
        self._reposition_compile_button()

    def closeEvent(self, event):


        # Если закрываем для возврата в меню —
        # НЕ завершаем приложение
        if self.returning_to_menu:
            event.accept()
            return

        # Иначе это крестик окна
        QApplication.quit()

    def _reposition_compile_button(self):
        if hasattr(self, 'btn_compile') and hasattr(self, 'floating_panel'):
            margin = 15
            bx = self.floating_panel.width() - self.btn_compile.width() - margin
            by = self.floating_panel.height() - self.btn_compile.height() - margin
            self.btn_compile.move(bx, by)

    def _init_floating_toolbar(self):
        self.toolbar_panel = QFrame(self)
        self.toolbar_panel.setObjectName("FloatingToolbar")
        self.toolbar_panel.setStyleSheet(
            """
            QFrame#FloatingToolbar { 
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1, 
                    stop: 0 #DDEDF3, stop: 1 #BACCD4
                ); 
                border-radius: 24px; 
                border: 1px solid #A2B8C2; 
            }
            QPushButton { background-color: #FFFFFF; border: 1px solid #7FA4B2; border-radius: 12px; }
            QPushButton:hover { background-color: #EBF3F5; }
            QPushButton:checked { background-color: #1F6FB2; border: 1px solid #154F80; }
            """
        )
        self.toolbar_panel.setGeometry(25, 120, 130, 430)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 35))
        shadow.setOffset(2, 6)
        self.toolbar_panel.setGraphicsEffect(shadow)

        grid = QGridLayout(self.toolbar_panel)
        grid.setContentsMargins(14, 14, 14, 14)
        grid.setSpacing(10)

        self.tool_buttons: dict[str, ShapeToolButton] = {}
        tools = [
            ("process", 0, 0), ("circle", 0, 1), ("decision", 1, 0), ("io", 1, 1),
            ("top_half_circle", 2, 0), ("bottom_half_circle", 2, 1), ("inv_trapezoid", 3, 0), ("rounded_rect", 3, 1),
            ("double_rect", 4, 0), ("hexagon", 4, 1), ("solid_line", 5, 0), ("arrow_line", 5, 1), ("dashed_line", 6, 0)
        ]
        for tool_type, row, col in tools:
            btn = ShapeToolButton(tool_type)
            btn.clicked.connect(lambda checked, t=tool_type: self.select_tool(t))
            grid.addWidget(btn, row, col)
            self.tool_buttons[tool_type] = btn

    def select_tool(self, tool_type: str):
        for t, btn in self.tool_buttons.items():
            if t != tool_type:
                btn.setChecked(False)
        if self.tool_buttons[tool_type].isChecked():
            self.current_tool = tool_type
            self.view.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.reset_tool_selection()

    def reset_tool_selection(self):
        self.current_tool = None
        self.view.setCursor(Qt.CursorShape.ArrowCursor)
        for btn in self.tool_buttons.values():
            btn.setChecked(False)

    def _init_burger_menu(self):
        self.burger_panel = QFrame(self)
        self.burger_panel.setObjectName("BurgerMenu")
        self.burger_panel.setStyleSheet(
            """
            QFrame#BurgerMenu { 
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1, 
                    stop: 0 #DDEDF3, stop: 1 #BACCD4
                ); 
                border-right: 1px solid #97B4BE; 
            }
            QPushButton { background-color: rgba(255, 255, 255, 0.5); border: 1px solid rgba(55,80,90,0.25); border-radius: 8px; padding: 10px; font-weight: bold; color: #17333D; text-align: left; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.8); }
            """
        )
        panel_layout = QVBoxLayout(self.burger_panel)
        panel_layout.setContentsMargins(15, 60, 15, 15)
        panel_layout.setSpacing(12)

        self.btn_save_pdf = QPushButton("Сохранить в pdf")
        self.btn_save_png = QPushButton("Сохранить в png")
        self.btn_back_menu = QPushButton("Назад в меню")

        self.btn_save_pdf.clicked.connect(self.action_export_pdf)
        self.btn_save_png.clicked.connect(self.action_export_png)
        self.btn_back_menu.clicked.connect(self.action_back_to_menu)

        panel_layout.addWidget(self.btn_save_pdf)
        panel_layout.addWidget(self.btn_save_png)
        panel_layout.addWidget(self.btn_back_menu)
        panel_layout.addStretch(1)

        self.burger_width = 240
        self.burger_panel.setGeometry(-self.burger_width, 42, self.burger_width, self.height() - 42)
        self.burger_is_open = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        header_height = self.title_bar.height() if hasattr(self, 'title_bar') else 42
        if hasattr(self, 'burger_panel'):
            self.burger_panel.setFixedHeight(self.height() - header_height)
            self.burger_panel.move(0 if self.burger_is_open else -self.burger_width, header_height)
        if not self.manual_mode and hasattr(self, 'floating_panel'):
            self.floating_panel.setFixedHeight(self.height() - 170)
            self._reposition_compile_button()
        if hasattr(self, 'burger_btn'):
            self.burger_btn.raise_()
        if hasattr(self, 'burger_panel') and self.burger_is_open:
            self.burger_panel.raise_()

    def toggle_burger_menu(self):
        self.anim = QPropertyAnimation(self.burger_panel, b"pos")
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Узнаем точную высоту верхней панели, чтобы меню выезжало ровно под ней
        header_height = self.title_bar.height() if hasattr(self, 'title_bar') else 42

        if not self.burger_is_open:
            self.anim.setStartValue(self.burger_panel.pos())
            self.anim.setEndValue(QPointF(0, header_height))
            self.burger_is_open = True
            self.burger_btn.setText("✕")
            self.burger_panel.raise_()
            if hasattr(self, 'title_bar'):
                self.title_bar.raise_()  # Чтобы панель перекрывала выезжающий виджет сверху
            self.burger_btn.raise_()
        else:
            self.anim.setStartValue(self.burger_panel.pos())
            self.anim.setEndValue(QPointF(-self.burger_width, header_height))
            self.burger_is_open = False
            self.burger_btn.setText("☰")
            if not self.manual_mode and hasattr(self, 'floating_panel'):
                self.floating_panel.raise_()
            elif self.manual_mode and hasattr(self, 'toolbar_panel'):
                self.toolbar_panel.raise_()
            self.burger_btn.raise_()
        self.anim.start()

    def _calculate_back_edge_path(self, src_item, tgt_item):
        src_rect = src_item.sceneBoundingRect()
        tgt_rect = tgt_item.sceneBoundingRect()

        start_pos = QPointF(src_rect.center().x(), src_rect.bottom())
        end_pos = QPointF(tgt_rect.center().x(), tgt_rect.top())

        # Проверяем, есть ли блоки слева и справа
        scene_rect = self.scene.sceneRect()
        left_space = abs(scene_rect.left() - min(src_rect.left(), tgt_rect.left()))
        right_space = abs(scene_rect.right() - max(src_rect.right(), tgt_rect.right()))

        # Выбираем сторону с большим свободным пространством
        if right_space > left_space:
            offset_x = max(src_rect.width(), tgt_rect.width()) + 60  # вправо
        else:
            offset_x = -(max(src_rect.width(), tgt_rect.width()) + 60)  # влево

        mid1 = QPointF(start_pos.x(), start_pos.y() + 30)
        mid2 = QPointF(start_pos.x() + offset_x, start_pos.y() + 30)
        mid3 = QPointF(end_pos.x() + offset_x, end_pos.y() - 30)
        mid4 = QPointF(end_pos.x(), end_pos.y() - 30)

        return [start_pos, mid1, mid2, mid3, mid4, end_pos]

    def refresh_flowchart(self):
        if self.manual_mode:
            return
        text = self.code_edit.toPlainText()
        if not text.strip():
            self.scene.clear()
            return
        try:
            nodes, edges = parse_pseudocode(text)
            if not nodes:
                self.scene.clear()
                return

            self.scene.clear()
            items_map: dict[int, FlowchartItem] = {}

            # --- 1. СТРУКТУРНЫЙ АНАЛИЗ ГРАФА ---
            outgoing_edges: dict[int, list] = {n.id: [] for n in nodes}
            incoming_edges: dict[int, list] = {n.id: [] for n in nodes}
            nodes_dict = {n.id: n for n in nodes}

            for edge in edges:
                if edge.source in outgoing_edges:
                    outgoing_edges[edge.source].append(edge)
                if edge.target in incoming_edges:
                    incoming_edges[edge.target].append(edge)

            # Константы шага сетки
            LEVEL_HEIGHT = 140
            BRANCH_OFFSET_X = 200

            node_positions: dict[int, QPointF] = {}
            processed_nodes = set()

            # Находим стартовый узел
            start_nodes = [n for n in nodes if not incoming_edges[n.id]]
            start_node_id = start_nodes[0].id if start_nodes else nodes[0].id

            queue = [(start_node_id, 0.0, -150.0)]

            # --- 2. РАСЧЕТ КООРДИНАТ С ИЗОЛЯЦИЕЙ ВЕТВЕЙ ---
            while queue:
                node_id, x, y = queue.pop(0)
                if node_id in processed_nodes:
                    continue

                node = nodes_dict[node_id]
                node_positions[node_id] = QPointF(x, y)
                processed_nodes.add(node_id)

                if node.shape == "decision" and len(outgoing_edges[node_id]) >= 2:
                    true_next_id = None
                    false_next_id = None

                    for edge in outgoing_edges[node_id]:
                        if edge.label and edge.label.lower() in ["да", "yes", "то"]:
                            true_next_id = edge.target
                        else:
                            false_next_id = edge.target

                    if not true_next_id and not false_next_id:
                        true_next_id = outgoing_edges[node_id][0].target
                        false_next_id = outgoing_edges[node_id][1].target

                    merge_node_id = None
                    visited_lookahead = set()

                    def find_merge_point(start_id):
                        curr = start_id
                        while curr and curr not in visited_lookahead:
                            visited_lookahead.add(curr)
                            if len(incoming_edges[curr]) > 1:
                                return curr
                            next_out = outgoing_edges[curr]
                            curr = next_out[0].target if next_out else None
                        return None

                    merge_node_id = find_merge_point(true_next_id) or find_merge_point(false_next_id)

                    def trace_branch(start_id, stop_id):
                        branch = []
                        curr = start_id
                        while curr and curr not in processed_nodes and curr != stop_id:
                            if len(incoming_edges[curr]) > 1:
                                break
                            branch.append(curr)
                            if nodes_dict[curr].shape == "decision":
                                break
                            next_out = outgoing_edges[curr]
                            curr = next_out[0].target if next_out else None
                        return branch

                    branch_start_y = y + LEVEL_HEIGHT

                    true_branch = trace_branch(true_next_id, merge_node_id) if true_next_id else []
                    curr_y_true = branch_start_y
                    for b_node in true_branch:
                        node_positions[b_node] = QPointF(-BRANCH_OFFSET_X, curr_y_true)
                        processed_nodes.add(b_node)
                        curr_y_true += LEVEL_HEIGHT

                    false_branch = trace_branch(false_next_id, merge_node_id) if false_next_id else []
                    curr_y_false = branch_start_y
                    for b_node in false_branch:
                        node_positions[b_node] = QPointF(BRANCH_OFFSET_X, curr_y_false)
                        processed_nodes.add(b_node)
                        curr_y_false += LEVEL_HEIGHT

                    if not merge_node_id:
                        last_true_node = true_branch[-1] if true_branch else true_next_id
                        if last_true_node and outgoing_edges[last_true_node]:
                            merge_node_id = outgoing_edges[last_true_node][0].target

                    if merge_node_id:
                        next_y = max(curr_y_true, curr_y_false)
                        queue.append((merge_node_id, 0.0, next_y))
                else:
                    next_edges = outgoing_edges[node_id]
                    if next_edges:
                        nxt_id = next_edges[0].target
                        if nxt_id not in processed_nodes:
                            queue.append((nxt_id, x, y + LEVEL_HEIGHT))

            # --- 3. СОЗДАНИЕ ОСНОВНЫХ БЛОКОВ СХЕМЫ ---
            comments_queue = []

            for node in nodes:
                display_text = node.text.strip()
                upper_text = display_text.upper()

                if upper_text in [
                    "ТО", "THEN", "ИНАЧЕ", "ELSE",
                    "КОНЕЦ ЕСЛИ", "КОНЕЦ_ЕСЛИ", "END IF", "END_IF",
                    "КОНЕЦ ПОКА", "КОНЕЦ_ПОКА", "END WHILE", "END_WHILE",
                    "КОНЕЦ ПАРАЛЛЕЛЬНО", "КОНЕЦ_ПАРАЛЛЕЛЬНО", "END PARALLEL", "END_PARALLEL",
                    "ГРАНИЦА ЦИКЛА КОНЕЦ", "ГРАНИЦА_ЦИКЛА_КОНЕЦ", "END LOOP", "END_LOOP"
                ]:
                    continue

                # Извлечение комментариев
                is_comment = False
                for c_kw in ["КОММЕНТАРИЙ ", "COMMENT ", "REM "]:
                    if upper_text.startswith(c_kw):
                        display_text = display_text[len(c_kw):].strip()
                        is_comment = True
                        break
                if upper_text.startswith("//"):
                    display_text = display_text[2:].strip()
                    is_comment = True

                pos = node_positions.get(node.id, QPointF(0, node.id * LEVEL_HEIGHT - 150))

                if is_comment:
                    comments_queue.append((node, display_text, pos))
                    continue

                # Очистка ключевых слов
                keywords_to_remove = [
                    "ВВОД ", "INPUT ", "READ ", "ВЫВОД ", "OUTPUT ", "WRITE ", "PRINT ",
                    "ПОКА ", "WHILE ", "ЕСЛИ ", "IF ", "ПОДПРОГРАММА ", "SUBROUTINE ",
                    "ФУНКЦИЯ ", "FUNCTION ", "ПРОЦЕДУРА ", "PROCEDURE ", "CALL ", "ТО",
                    "ПОДГОТОВКА ", "PREPARATION ", "FOR ", "ПАРАЛЛЕЛЬНО ", "PARALLEL ",
                    "ГРАНИЦА ЦИКЛА НАЧАЛО:", "ГРАНИЦА_ЦИКЛА_НАЧАЛО:", "LOOP START:", "СОЕДИНИТЕЛЬ ",
                    "ПОДПРОГРАММА ", "SUBROUTINE ", "ФУНКЦИЯ ", "FUNCTION ", "ПРОЦЕДУРА ", "PROCEDURE ", "CALL "
                ]
                for kw in keywords_to_remove:
                    if upper_text.startswith(kw):
                        display_text = display_text[len(kw):].strip()
                        break

                upper_display = display_text.upper()
                if upper_display.endswith(" ВЫПОЛНИТЬ"):
                    display_text = display_text[:-10].strip()
                elif upper_display.endswith(" DO"):
                    display_text = display_text[:-3].strip()
                elif upper_display.endswith(" ТО"):
                    display_text = display_text[:-3].strip()
                elif upper_display.endswith(" THEN"):
                    display_text = display_text[:-5].strip()

                node_upper = node.text.strip().upper()
                current_shape = node.shape.lower() if node.shape else "process"

                if any(node_upper.startswith(kw) for kw in
                       ["ПОДПРОГРАММА", "SUBROUTINE", "ФУНКЦИЯ", "FUNCTION", "ПРОЦЕДУРА", "PROCEDURE", "CALL"]):
                    current_shape = "subroutine"

                # Изменяем создание элемента: вместо node.shape передаем current_shape
                item = FlowchartItem(display_text, current_shape)
                item.item_id = node.id
                # ====================================================================

                item.setPos(pos.x() - item.rect.width() / 2, pos.y() - item.rect.height() / 2)
                self.scene.addItem(item)
                items_map[node.id] = item

            # --- 4. СОЗДАНИЕ ВСЕХ СТРЕЛОК ---
            for edge in edges:
                print(f"Edge: {edge.source} -> {edge.target}, label={edge.label}, is_back={edge.is_back_edge}")
                src_item = items_map.get(edge.source)
                tgt_item = items_map.get(edge.target)

                if not src_item or not tgt_item:
                    continue

                label = getattr(edge, "label", "") or ""

                if src_item.shape_type == "decision":
                    label_lower = label.lower()
                    if label_lower in ["да", "yes", "то"]:
                        label = "Да"
                    elif label_lower in ["нет", "no", "иначе"]:
                        label = "Нет"
                    elif not label:
                        src_center = src_item.sceneBoundingRect().center()
                        tgt_center = tgt_item.sceneBoundingRect().center()
                        label = "Да" if tgt_center.x() < src_center.x() else "Нет"

                is_back = getattr(edge, "is_back_edge", False)
                line = ArrowLine(src_item, tgt_item, label, is_back)
                line.update_path()  # ← ЯВНО ВЫЗЫВАЕМ МЕТОД
                self.scene.addItem(line)

                # -----------------------------------------------
                # ОБРАТНАЯ СТРЕЛКА ЦИКЛА
                # -----------------------------------------------
                if is_back:
                    points = self._calculate_back_edge_path(src_item, tgt_item)
                    line.custom_path = points
                    line.update_path()  # Обновляем путь с кастомными точками
                else:
                    line.update_from_items()

                self.scene.addItem(line)

                if is_back:
                    # Получаем границы блоков в сцене
                    src_rect = src_item.sceneBoundingRect()
                    tgt_rect = tgt_item.sceneBoundingRect()

                    # Точка выхода из последнего блока тела цикла (нижний центр)
                    start_pos = QPointF(src_rect.center().x(), src_rect.bottom())

                    # Точка входа в ромб-условие (верхний центр)
                    end_pos = QPointF(tgt_rect.center().x(), tgt_rect.top())

                    # Динамическое смещение вправо (зависит от ширины блоков)
                    max_width = max(src_rect.width(), tgt_rect.width())
                    offset_x = max_width + 50  # смещение на ширину самого широкого блока + отступ

                    # Строим обходной путь: вниз → вправо → вверх → влево → вверх
                    mid1 = QPointF(start_pos.x(), start_pos.y() + 30)
                    mid2 = QPointF(start_pos.x() + offset_x, start_pos.y() + 30)
                    mid3 = QPointF(end_pos.x() + offset_x, end_pos.y() - 30)
                    mid4 = QPointF(end_pos.x(), end_pos.y() - 30)

                    line.custom_path = [start_pos, mid1, mid2, mid3, mid4, end_pos]

                line.update_path()
                line.update()

            # --- 5. СОЗДАНИЕ И ПОЗИЦИОНИРОВАНИЕ КОММЕНТАРИЕВ (ОТ СЕРЕДИНЫ СТРЕЛКИ) ---
            for c_node, c_text, c_pos in comments_queue:
                src_block = None
                tgt_block = None

                # Находим блоки, между которыми пролегает стрелка, к которой относится комментарий
                # Сначала берем блок, из которого комментарий "выходит"
                for edge in edges:
                    if edge.target == c_node.id:
                        src_block = items_map.get(edge.source)
                        break

                if src_block:
                    # Теперь находим следующий блок алгоритма, к которому шла ветка от src_block
                    for edge in edges:
                        if edge.source == src_block.item_id and edge.target in items_map:
                            tgt_block = items_map.get(edge.target)
                            break

                # Создаем комментарий, передавая ему оба блока для расчета середины линии между ними
                comment_item = CommentItem(c_text, src_item=src_block, tgt_item=tgt_block)

                if src_block:
                    # Позиционируем блок комментария справа от середины воображаемой линии
                    center_point = comment_item.get_arrow_center()
                    comment_item.setPos(center_point.x() + 90, center_point.y() - 25)
                else:
                    comment_item.setPos(c_pos.x() + 120, c_pos.y() - 20)

                self.scene.addItem(comment_item)

            self.scene.update()
            self.view.centerOn(0, 0)

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            QMessageBox.warning(self, "Ошибка рендеринга", f"Произошел сбой при расчете сетки ветвлений:\n{str(e)}")

    def action_export_pdf(self):

        self.toggle_burger_menu()

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить в PDF",
            "",
            "PDF Files (*.pdf)"
        )

        if not filepath:
            return

        self.view.export_mode = True

        self.view.viewport().update()
        QApplication.processEvents()

        old_brush = self.scene.backgroundBrush()

        self.scene.setBackgroundBrush(
            QBrush(Qt.BrushStyle.NoBrush)
        )

        ok = export_scene_to_png(self.scene, filepath)

        self.scene.setBackgroundBrush(old_brush)

        self.view.export_mode = False

        self.view.viewport().update()

        if ok:
            QMessageBox.information(
                self,
                "Экспорт PDF",
                "Схема успешно сохранена!"
            )

    def action_export_png(self):

        self.toggle_burger_menu()

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить в PNG",
            "",
            "PNG Files (*.png)"
        )

        if not filepath:
            return

        # Включаем режим экспорта
        self.view.export_mode = True

        self.view.viewport().update()
        QApplication.processEvents()

        old_brush = self.scene.backgroundBrush()

        self.scene.setBackgroundBrush(
            QBrush(Qt.BrushStyle.NoBrush)
        )

        ok = export_scene_to_png(self.scene, filepath)

        self.scene.setBackgroundBrush(old_brush)

        self.view.export_mode = False

        self.view.viewport().update()

        if ok:
            QMessageBox.information(
                self,
                "Экспорт PNG",
                "Схема успешно сохранена!"
            )

    def action_back_to_menu(self):

        self.returning_to_menu = True

        self.close()

        if self.main_menu_callback:
            self.main_menu_callback()

    def paintEvent(self, event):
        super().paintEvent(event)
        if hasattr(self, 'title_bar'):
            painter = QPainter(self)
            # Определяем область отрисовки (верхняя панель)
            rect = self.title_bar.rect()

            # Создаем градиент
            gradient = QLinearGradient(0, 0, rect.width(), 0)
            gradient.setColorAt(0, QColor("#DDEDF3"))
            gradient.setColorAt(0.5, QColor("#BACCD4"))
            gradient.setColorAt(1, QColor("#A2B8C2"))

            # Рисуем градиент на фоне title_bar
            painter.fillRect(rect, gradient)