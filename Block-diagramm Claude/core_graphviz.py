"""
core_graphviz.py — Генерация блок-схем через Graphviz.

Формы фигур по ГОСТ 19.701-90:
    start / end  → oval         (эллипс)
    process      → box          (прямоугольник)
    decision     → diamond      (ромб)
    io           → parallelogram (параллелограмм)

Все блоки залиты белым (fillcolor="white").

Обратные дуги циклов (back_edge=True):
    Линия огибает тело цикла справа и входит в верхнюю вершину
    ромба-условия строго сверху (под 90° к основной стрелке).
    Реализовано через два невидимых якорных узла:
        __bot_N (rank=same с последним узлом тела)
        __top_N (rank=same с ромбом-условием)
    Подробнее — см. graphviz_back_edges.py.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

try:
    import graphviz  # noqa: F401
    _GRAPHVIZ_PKG_AVAILABLE = True
except ImportError:
    _GRAPHVIZ_PKG_AVAILABLE = False

from graphviz_constants import COMMON_DOT_PATHS
from graphviz_layout import add_nodes, add_normal_edges, build_digraph, pin_start_end
from graphviz_back_edges import add_back_edges


class GraphGenerator:
    """
    Генератор блок-схем по ГОСТ 19.701-90 на базе Graphviz.

    Использование:
        gen = GraphGenerator()
        ok, msg = gen.check_graphviz_installed()
        if ok:
            path = gen.generate(parse_result)   # возвращает путь к PNG
    """

    def __init__(self, output_dir: Optional[str] = None):
        self._output_dir = Path(output_dir) if output_dir else Path(tempfile.gettempdir())
        self._output_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ─────────────────────────────────────────────────────────

    def check_graphviz_installed(self) -> tuple[bool, str]:
        """
        Проверяет наличие исполняемого файла dot в PATH и стандартных путях.

        Returns:
            (True, путь_к_dot)  — если найден
            (False, сообщение)  — если не найден
        """
        dot_in_path = shutil.which("dot")
        if dot_in_path:
            return True, dot_in_path

        exe_name = "dot.exe" if sys.platform == "win32" else "dot"
        for dir_path in COMMON_DOT_PATHS:
            candidate = Path(dir_path) / exe_name
            if candidate.is_file():
                os.environ["PATH"] = (
                    str(candidate.parent) + os.pathsep + os.environ.get("PATH", "")
                )
                return True, str(candidate)

        return (
            False,
            "Исполняемый файл dot не найден.\n"
            "Скачайте Graphviz с https://graphviz.org/download/ "
            "и убедитесь, что папка bin добавлена в переменную PATH.",
        )

    def generate(self, parse_result) -> str:
        """
        Принимает ParseResult из core_parser и возвращает путь к PNG-файлу.

        Последовательность сборки графа:
            1. build_digraph()      — создать Digraph с глобальными атрибутами
            2. add_nodes()          — добавить все узлы (start/end/process/io/decision)
            3. pin_start_end()      — зафиксировать «Начало» вверху, «Конец» внизу
            4. add_normal_edges()   — добавить обычные рёбра (не back_edge)
            5. add_back_edges()     — добавить П-образные обратные дуги циклов

        Raises:
            RuntimeError — если Graphviz не установлен или генерация не удалась.
            ImportError  — если Python-пакет graphviz не установлен.
        """
        if not _GRAPHVIZ_PKG_AVAILABLE:
            raise ImportError(
                "Python-пакет 'graphviz' не установлен.\n"
                "Выполните: pip install graphviz"
            )

        import graphviz as gv  # noqa: PLC0415

        ok, msg = self.check_graphviz_installed()
        if not ok:
            raise RuntimeError(msg)

        # 1. Создаём граф
        dot = build_digraph(gv)

        # 2. Добавляем узлы
        start_ids, end_ids = add_nodes(dot, parse_result.nodes)

        # 3. Фиксируем Начало / Конец
        pin_start_end(dot, start_ids, end_ids)

        # 4. Обычные рёбра (включая «нет» с явным портом :e у ромбов циклов)
        add_normal_edges(dot, parse_result.edges)

        # 5. Обратные дуги циклов (П-образный маршрут справа, вход сверху в ромб)
        add_back_edges(dot, parse_result.edges)

        # 6. Рендер в PNG
        output_base = str(self._output_dir / "flowchart_output")
        dot.render(
            filename=output_base,
            format="png",
            cleanup=True,
        )

        result_path = output_base + ".png"
        if not Path(result_path).exists():
            raise RuntimeError(f"Graphviz не создал файл: {result_path}")

        return result_path
