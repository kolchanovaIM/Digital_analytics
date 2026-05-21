"""
graphviz_back_edges.py — Маршрутизация обратных дуг цикла (back_edge=True).

Алгоритм (П-образный маршрут через два якорных узла)
-----------------------------------------------------
Обратная дуга соединяет последний узел тела цикла (tail) с ромбом-условием
(head). Линия обходит всё тело цикла СЛЕВА и входит в верхнюю вершину
ромба строго перпендикулярно (под 90°) к основной стрелке, спускающейся
сверху.

Топология:

    tail:w ──► __bot        (горизонтально влево, выход из хвоста)
                  │
              (вертикально вверх вдоль левой границы тела цикла)
                  │
              __top ──► head:n  (горизонтально вправо, вход сверху в ромб)

Размещение якорей:
    __bot : rank=same с tail        (нижний якорь — уровень последнего узла тела)
    __top : rank=same с pred(head)  (верхний якорь — уровень узла НАД ромбом)

    Размещение __top на ранге предшественника ромба (а не самого ромба)
    гарантирует, что горизонтальный сегмент __top→head:n проходит
    строго НАД ромбом и не конфликтует с рёбрами, входящими в ромб
    с боков. Если предшественник не найден — __top ставится на ранг head
    (запасной вариант).

Распорки (style=invis, weight=100):
    __bot ← tail   выталкивают __bot левее tail
    __top ← head   выталкивают __top левее head

Все три рабочих ребра имеют constraint=false — они не влияют на
вертикальное ранжирование остальных узлов.

Ребро «нет» у ромба:
    Чтобы избежать конфликта с обратной дугой, входящей через :n,
    ребро «нет» использует явный порт :e (east) — уходит вправо
    к следующему узлу после цикла. Это обеспечивается в graphviz_layout.py.

Несколько циклов:
    Каждое back_edge получает уникальную пару __bot_N / __top_N,
    поэтому при нескольких вложенных или последовательных циклах
    линии не сливаются.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import graphviz as gv

from graphviz_constants import INVIS_NODE


def find_predecessor(head_id: str, edges: list[dict[str, Any]]) -> str | None:
    """
    Возвращает id непосредственного предшественника ромба head_id
    по нормальным (не back_edge) рёбрам.

    Нужен для размещения __top на ранге узла НАД ромбом, чтобы
    горизонтальный сегмент обратной дуги шёл строго над ромбом,
    а не сбоку от него.
    """
    predecessors = [
        e["from"] for e in edges
        if e["to"] == head_id and not e.get("back_edge")
    ]
    return predecessors[-1] if predecessors else None


def add_back_edges(
    dot: "gv.Digraph",
    edges: list[dict[str, Any]],
) -> None:
    """
    Добавляет все П-образные обратные дуги (back_edge=True) в граф dot.

    Для каждого back_edge:
    1. Создаёт пару невидимых якорных узлов __bot_N / __top_N.
    2. Размещает __bot на ранге tail, __top на ранге pred(head).
    3. Добавляет распорки, выталкивающие якоря ВЛЕВО.
    4. Строит П-образный маршрут: tail:w → __bot:w → __top:w → head:n

    Параметры
    ---------
    dot   : Digraph, в который добавляются узлы и рёбра
    edges : полный список рёбер ParseResult (включая back_edge и обычные)
    """
    counter = 0

    for edge in edges:
        if not edge.get("back_edge"):
            continue

        counter += 1
        tail = edge["from"]
        head = edge["to"]
        label = edge.get("label", "")

        # Уникальные имена для якорных узлов этого цикла
        bot_id = f"__bot_{counter}"
        top_id = f"__top_{counter}"

        # Находим предшественника ромба-условия
        # Если предшественник есть — ставим __top на его ранг,
        # иначе ставим на ранг самого ромба
        pred = find_predecessor(head, edges)
        top_anchor = pred if pred else head

        # Создаём невидимые якорные узлы
        dot.node(bot_id, **INVIS_NODE)
        dot.node(top_id, **INVIS_NODE)

        # ── Размещение якорей по рангам ──────────────────────────────────────

        # __bot на том же уровне, что и последний узел тела цикла (tail)
        with dot.subgraph(name=f"rank_bot_{counter}") as sg:
            sg.attr(rank="same")
            sg.node(tail)
            sg.node(bot_id)

        # __top на том же уровне, что и предшественник ромба (или сам ромб)
        with dot.subgraph(name=f"rank_top_{counter}") as sg:
            sg.attr(rank="same")
            sg.node(top_anchor)
            sg.node(top_id)

        # ── Невидимые распорки (выравнивание по горизонтали) ─────────────────
        # Эти рёбра заставляют dot расположить якоря левее основных узлов
        # Высокий weight (100) даёт приоритет минимизации длины этих рёбер

        # Распорка: tail → bot (тянет bot влево от tail)
        dot.edge(
            tail, bot_id,
            style="invis",
            weight="100",
            constraint="false",
        )

        # Распорка: top_anchor → top (тянет top влево от предшественника)
        dot.edge(
            top_anchor, top_id,
            style="invis",
            weight="100",
            constraint="false",
        )

        # ── Сегмент 1: tail → bot (горизонтально влево) ──────────────────────
        # Выход из tail через левый порт (w), вход в bot тоже через левый порт
        dot.edge(
            tail, bot_id,
            tailport="w",
            headport="w",
            constraint="false",
            arrowhead="none",
        )

        # ── Сегмент 2: bot → top (вертикально вверх) ─────────────────────────
        # Оба конца на левых портах — Graphviz построит вертикальную линию
        dot.edge(
            bot_id, top_id,
            tailport="w",
            headport="w",
            constraint="false",
            arrowhead="none",
        )

        # ── Сегмент 3: top → head (горизонтально вправо + вход сверху) ───────
        # Выход из top через правый порт (e), вход в head через верхний порт (n)
        # Это даёт вход в ромб строго сверху, под 90° к основному потоку
        # Если есть метка у обратной дуги — отображаем её на этом сегменте
        dot.edge(
            top_id, head,
            label=label,
            tailport="e",
            headport="n",
            constraint="false",
        )