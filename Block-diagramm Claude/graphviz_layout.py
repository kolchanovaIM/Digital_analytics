"""
graphviz_layout.py — Вспомогательные функции компоновки графа.

Содержит:
    build_digraph()       — создаёт настроенный gv.Digraph с нужными атрибутами
    add_nodes()           — добавляет все узлы ParseResult в граф
    add_normal_edges()    — добавляет обычные рёбра (не back_edge);
                            ребро «нет» у ромба-условия цикла получает
                            явный port :e, чтобы не конфликтовать с
                            обратной дугой, входящей через port :n (сверху).
    pin_start_end()       — фиксирует «Начало» вверху, «Конец» внизу
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import graphviz as gv   # только для аннотаций

from graphviz_constants import (
    EDGE_ATTR,
    GRAPH_ATTR,
    NODE_ATTR,
    NODE_STYLE,
)

# Метки ветви «нет» у ромба-условия цикла
# Эти метки считаются отрицательной ветвью и получают специальную обработку
_NO_LABELS: frozenset[str] = frozenset({"нет", "no", "н", "n", "false", "0", "ложь"})


def build_digraph(gv_module: Any) -> "gv.Digraph":
    """
    Создаёт и возвращает gv.Digraph с глобальными атрибутами из GRAPH_ATTR.

    Параметры
    ---------
    gv_module : модуль graphviz (передаётся снаружи, чтобы избежать
                импорта на уровне модуля при отсутствии пакета)

    Возвращает
    ----------
    gv.Digraph — настроенный объект графа для построения блок-схемы
    """
    return gv_module.Digraph(
        name="flowchart",
        graph_attr=GRAPH_ATTR,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
    )


def add_nodes(
    dot: "gv.Digraph",
    nodes: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    """
    Добавляет все узлы из ParseResult.nodes в граф dot.

    Параметры
    ---------
    dot : gv.Digraph — граф, в который добавляются узлы
    nodes : list[dict] — список узлов из результата парсинга

    Возвращает
    ----------
    (start_ids, end_ids) — списки id узлов типа «start» и «end»
    """
    start_ids: list[str] = []
    end_ids: list[str] = []

    for node in nodes:
        # Получаем стиль для типа узла, по умолчанию — process
        style = dict(NODE_STYLE.get(node["type"], NODE_STYLE["process"]))

        # Извлекаем метку узла
        label = node["label"]

        # Добавляем узел в граф
        dot.node(node["id"], label=label, **style)

        # Запоминаем start и end узлы для последующего позиционирования
        if node["type"] == "start":
            start_ids.append(node["id"])
        elif node["type"] == "end":
            end_ids.append(node["id"])

    return start_ids, end_ids


def _find_back_edge_heads(edges: list[dict[str, Any]]) -> set[str]:
    """
    Возвращает множество id ромбов, в которые входит хотя бы одна back_edge.

    Используется для выбора порта у ребра «нет» таких ромбов.

    Параметры
    ---------
    edges : list[dict] — список всех рёбер графа

    Возвращает
    ----------
    set[str] — множество ID узлов-ромбов, в которые входят обратные дуги
    """
    return {e["to"] for e in edges if e.get("back_edge")}


def add_normal_edges(
    dot: "gv.Digraph",
    edges: list[dict[str, Any]],
) -> None:
    """
    Добавляет обычные рёбра (back_edge=False) в граф dot.

    Особый случай — ребро «нет» из ромба-условия цикла (т.е. из ромба,
    в который входит back_edge):
        • использует tailport="e" (выход вправо из ромба)
        • использует xlabel вместо label, чтобы избежать предупреждения
          Graphviz об ortho+label

    Это не даёт ребру «нет» столкнуться с обратной дугой, входящей
    через port "n" того же ромба.

    Все остальные рёбра добавляются с xlabel (стандарт для splines=ortho).

    Параметры
    ---------
    dot : gv.Digraph — граф, в который добавляются рёбра
    edges : list[dict] — список всех рёбер графа
    """
    # Находим все ромбы, в которые входят обратные дуги
    back_heads = _find_back_edge_heads(edges)

    for edge in edges:
        # Пропускаем обратные дуги — они обрабатываются отдельно
        if edge.get("back_edge"):
            continue

        from_id = edge["from"]
        to_id = edge["to"]
        label = edge.get("label", "")

        # Атрибуты ребра: используем xlabel вместо label для совместимости с ortho
        edge_attrs: dict[str, str] = {"xlabel": label}

        # Специальная обработка для ребра «нет» из ромба с обратной дугой
        # Такое ребро должно уходить вправо, чтобы не пересекаться с обратной дугой,
        # которая входит в ромб сверху (port="n")
        if from_id in back_heads and label.strip().lower() in _NO_LABELS:
            edge_attrs["tailport"] = "e"  # Выход из правой стороны ромба

        # Добавляем ребро в граф
        dot.edge(from_id, to_id, **edge_attrs)


def pin_start_end(
    dot: "gv.Digraph",
    start_ids: list[str],
    end_ids: list[str],
) -> None:
    """
    Фиксирует вертикальное положение «Начало» (top) и «Конец» (bottom),
    и выравнивает «Конец» горизонтально под «Начало».

    Механизм
    --------
    • rank=min для всех start-узлов — они будут в самом верху
    • rank=max для всех end-узлов — они будут в самом низу
    • Невидимое ребро start→end (style=invis):
      dot минимизирует длину рёбер, поэтому прижимает «Конец»
      к тому же горизонтальному столбцу, что и «Начало»

    Параметры
    ---------
    dot : gv.Digraph — граф, в который добавляются ограничения
    start_ids : list[str] — список ID узлов типа «start»
    end_ids : list[str] — список ID узлов типа «end»
    """
    # Фиксируем все start-узлы в верхней части графа
    if start_ids:
        with dot.subgraph(name="rank_start") as sg:
            sg.attr(rank="min")  # минимальный ранг = самый верх
            for nid in start_ids:
                sg.node(nid)

    # Фиксируем все end-узлы в нижней части графа
    if end_ids:
        with dot.subgraph(name="rank_end") as sg:
            sg.attr(rank="max")  # максимальный ранг = самый низ
            for nid in end_ids:
                sg.node(nid)

    # Добавляем невидимое ребро от первого start к первому end
    # Это заставляет dot выровнять их по горизонтали
    if start_ids and end_ids:
        dot.edge(start_ids[0], end_ids[0], style="invis", weight="50")