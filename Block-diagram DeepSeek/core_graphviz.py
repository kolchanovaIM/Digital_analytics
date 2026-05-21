# core_graphviz.py — добавлен метод export_pdf для сохранения в PDF
import os
import shutil
import subprocess
import tempfile
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt

from dot_utils import shape_for_type


class GraphGenerator:
    @staticmethod
    def check_graphviz_installed() -> bool:
        """Проверяет, установлен ли Graphviz (dot) в системе."""
        return shutil.which('dot') is not None

    @staticmethod
    def error_pixmap(message: str) -> QPixmap:
        """Создаёт изображение с сообщением об ошибке."""
        pixmap = QPixmap(500, 200)
        pixmap.fill(QColor('white'))
        painter = QPainter(pixmap)
        painter.setPen(QColor('red'))
        painter.setFont(QFont('Arial', 10))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, message)
        painter.end()
        return pixmap

    def generate_preview(self, parsed_data: dict) -> QPixmap:
        """Генерирует блок-схему в PNG через Graphviz."""
        # ... (тот же код, что и раньше)
        pass

    def export_pdf(self, parsed_data: dict, output_path: str):
        """
        Экспортирует блок-схему в PDF через Graphviz.
        
        Args:
            parsed_data: словарь с узлами и рёбрами
            output_path: путь для сохранения PDF-файла
        """
        if not self.check_graphviz_installed():
            raise RuntimeError("Graphviz не установлен")

        nodes = parsed_data.get('nodes', [])
        edges = parsed_data.get('edges', [])

        # Строим DOT-описание
        dot_lines = ['digraph G {']
        dot_lines.append('  rankdir=TB;')
        dot_lines.append('  node [fontname="Arial", fontsize=12];')
        dot_lines.append('  edge [fontname="Arial", fontsize=10];')
        dot_lines.append('')

        for node in nodes:
            nid = node['id']
            ntype = node.get('type', 'process')
            label = self._escape_dot_label(node.get('label', ''))

            if ntype == 'merge':
                dot_lines.append(f'  {nid} [label="", shape=point, style=invis];')
                continue

            shape = shape_for_type(ntype)
            dot_lines.append(f'  {nid} [label="{label}", shape={shape}, style=filled, fillcolor="#E6E6E6"];')

        dot_lines.append('')
        for edge in edges:
            src, dst = edge[0], edge[1]
            lbl = edge[2] if len(edge) > 2 else None
            if lbl:
                lbl_escaped = self._escape_dot_label(lbl)
                dot_lines.append(f'  {src} -> {dst} [label="{lbl_escaped}", fontsize=10];')
            else:
                dot_lines.append(f'  {src} -> {dst};')

        dot_lines.append('}')
        dot_text = '\n'.join(dot_lines)

        # Сохраняем в PDF через Graphviz (формат pdf)
        dot_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.dot', delete=False, encoding='utf-8'
            ) as f:
                f.write(dot_text)
                dot_path = f.name

            result = subprocess.run(
                ['dot', '-Tpdf', dot_path, '-o', output_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise RuntimeError(f"Ошибка Graphviz:\n{result.stderr}")

        finally:
            if dot_path and os.path.exists(dot_path):
                try:
                    os.unlink(dot_path)
                except OSError:
                    pass

    def _escape_dot_label(self, text: str) -> str:
        """Экранирует специальные символы для DOT."""
        if not text:
            return ""
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace('{', '\\{')
        text = text.replace('}', '\\}')
        text = text.replace('%', '\\%')
        text = text.replace('\n', '\\n')
        return text