"""
graphviz_constants.py — Константы рендерера блок-схем.

Содержит:
    • NODE_STYLE       — атрибуты Graphviz для каждого типа узла по ГОСТ 19.701-90
    • GRAPH_ATTR       — глобальные атрибуты Digraph
    • NODE_ATTR        — атрибуты узлов по умолчанию
    • EDGE_ATTR        — атрибуты рёбер по умолчанию
    • INVIS_NODE       — атрибуты невидимого вспомогательного узла (якоря, распорки)
    • COMMON_DOT_PATHS — стандартные пути установки Graphviz на разных ОС
"""
from __future__ import annotations

# ── Пути к исполняемому файлу dot ─────────────────────────────────────────────

COMMON_DOT_PATHS: list[str] = [
    r"C:\Program Files\Graphviz\bin",
    r"C:\Program Files (x86)\Graphviz\bin",
    r"C:\Graphviz\bin",
    r"C:\Program Files\Graphviz\bin\dot.exe",
    r"C:\Program Files (x86)\Graphviz\bin\dot.exe",
    "/opt/homebrew/bin",
    "/usr/local/bin",
    "/usr/bin",
    "/snap/bin",
    "/usr/local/opt/graphviz/bin",
]

# ── Атрибуты узлов по типу (ГОСТ 19.701-90) ───────────────────────────────────
# Все блоки залиты белым (fillcolor="white") по требованию.

NODE_STYLE: dict[str, dict[str, str]] = {
    # Начало / Конец — эллипс
    "start": {
        "shape":     "oval",
        "style":     "filled",
        "fillcolor": "white",
        "fontname":  "Arial",
        "fontsize":  "12",
    },
    "end": {
        "shape":     "oval",
        "style":     "filled",
        "fillcolor": "white",
        "fontname":  "Arial",
        "fontsize":  "12",
    },
    # Процесс — прямоугольник
    "process": {
        "shape":     "box",
        "style":     "filled",
        "fillcolor": "white",
        "fontname":  "Arial",
        "fontsize":  "12",
    },
    # Условие — ромб
    "decision": {
        "shape":     "diamond",
        "style":     "filled",
        "fillcolor": "white",
        "fontname":  "Arial",
        "fontsize":  "12",
    },
    # Ввод / Вывод — параллелограмм
    "io": {
        "shape":     "parallelogram",
        "style":     "filled",
        "fillcolor": "white",
        "fontname":  "Arial",
        "fontsize":  "12",
    },
    # Узел слияния — невидимая точка нулевого размера.
    # Не отображается, но корректно пропускает через себя рёбра.
    "merge": {
        "shape":     "point",
        "style":     "invis",
        "width":     "0",
        "height":    "0",
        "margin":    "0",
        "label":     "",
    },
}

# ── Глобальные атрибуты графа ──────────────────────────────────────────────────

GRAPH_ATTR: dict[str, str] = {
    "rankdir":  "TB",           # сверху вниз (Top to Bottom)
    "splines":  "ortho",        # ортогональная маршрутизация рёбер
    "nodesep":  "0.6",          # горизонтальный зазор между узлами
    "ranksep":  "0.7",          # вертикальный зазор между рангами
    "charset":  "UTF-8",        # поддержка кириллицы
    "fontname": "Arial",        # шрифт по умолчанию
    "fontsize": "12",           # размер шрифта по умолчанию
    "newrank":  "true",         # обязательно для корректной работы rank=same
    "margin":   "0",            # отступы графа
    "pad":      "0.5",          # внутренние отступы
}

NODE_ATTR: dict[str, str] = {
    "fontname": "Arial",
    "fontsize": "12",
    "fontcolor": "#1B3A45",
}

EDGE_ATTR: dict[str, str] = {
    "fontname": "Arial",
    "fontsize": "10",
    "fontcolor": "#2C4F5C",
    "color": "#3A5F6F",
    "penwidth": "1.5",
    "arrowsize": "0.8",
}

# ── Атрибуты невидимого вспомогательного узла ─────────────────────────────────
# Используется для якорных узлов обратных дуг (__bot_N / __top_N).
# shape=point + style=invis + нулевые размеры → узел не отображается,
# но участвует в ранжировании и позволяет маршрутизировать рёбра.

INVIS_NODE: dict[str, str] = {
    "shape":     "point",
    "style":     "invis",
    "width":     "0",
    "height":    "0",
    "margin":    "0",
    "label":     "",
    "fixedsize": "true",
}

# ── Дополнительные стили для рёбер ────────────────────────────────────────────

# Стили для различных типов рёбер
EDGE_STYLES: dict[str, dict[str, str]] = {
    "normal": {
        "style": "solid",
        "color": "#3A5F6F",
    },
    "yes": {
        "style": "solid",
        "color": "#4CAF50",
    },
    "no": {
        "style": "solid",
        "color": "#F44336",
    },
    "back": {
        "style": "solid",
        "color": "#9C27B0",
        "penwidth": "2.0",
    },
    "invis": {
        "style": "invis",
        "weight": "100",
    },
}

# ── Параметры маршрутизации обратных дуг ───────────────────────────────────────

BACK_EDGE_CONFIG: dict[str, str | int] = {
    "weight": "100",           # вес невидимых распорок
    "minlen": "2",             # минимальная длина обратной дуги
    "side": "left",            # с какой стороны обходить тело цикла
}