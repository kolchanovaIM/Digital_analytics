"""
core_parser.py — Парсер псевдокода в граф узлов (Control Flow Graph).

Структура узла (dict):
    {
        "id":       str,           # уникальный идентификатор
        "type":     str,           # "start" | "end" | "process" | "decision" | "io"
        "label":    str,           # текст внутри фигуры (кириллица поддерживается)
        "next":     list[str],     # id следующих узлов
        "branch":   str | None,    # "yes" / "no" для ветвей decision, иначе None
    }

Структура ребра (dict):
    {
        "from":      str,   # id источника
        "to":        str,   # id получателя
        "label":     str,   # метка ("да" / "нет" / "")
        "back_edge": bool,  # True — обратная дуга цикла (рисуется сбоку)
    }

Узлы типа "merge" не создаются. Концы веток подключаются напрямую
к следующему содержательному узлу при помощи списка "открытых выходов".
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParseResult:
    """Результат парсинга: список узлов и список рёбер."""
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        return len(self.errors) == 0


# ── Токены ────────────────────────────────────────────────────────────────────

@dataclass
class Token:
    kind: str          # START | END | IF | ELSE | ENDIF | WHILE | ENDWHILE
                       # FOR | ENDFOR | INPUT | OUTPUT | ASSIGN
    value: str         # нормализованный текст (для INPUT/OUTPUT — без ключевого слова)
    condition: str = ""  # условие для IF / WHILE / FOR


def _tokenize(lines: list[str]) -> list[Token]:
    """Превращает очищенные строки в список токенов."""
    KW_START    = re.compile(r"^(начало|start)$", re.IGNORECASE)
    KW_END      = re.compile(r"^(конец|end)$", re.IGNORECASE)
    KW_IF       = re.compile(r"^(если|if)\s+(.+?)(?:\s+(то|then))?\s*$", re.IGNORECASE)
    KW_ELSE     = re.compile(r"^(иначе|else)$", re.IGNORECASE)
    KW_ENDIF    = re.compile(r"^(конец\s*если|endif)$", re.IGNORECASE)
    KW_WHILE    = re.compile(
        r"^(пока|while)\s+(.+?)(?:\s+(делать|выполнить|do))?\s*$", re.IGNORECASE
    )
    KW_ENDWHILE = re.compile(r"^(конец\s*пока|endwhile|wend)$", re.IGNORECASE)
    KW_FOR      = re.compile(
        r"^(для|for)\s+(.+?)\s+(до|to)\s+(.+?)(?:\s+(делать|do))?\s*$", re.IGNORECASE
    )
    KW_ENDFOR   = re.compile(r"^(конец\s*для|endfor|next)$", re.IGNORECASE)
    KW_INPUT    = re.compile(r"^(ввод|input|read)\s+(.+)$", re.IGNORECASE)
    KW_OUTPUT   = re.compile(r"^(вывод|вывести|print|output|write)\s+(.+)$", re.IGNORECASE)

    tokens: list[Token] = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue

        if KW_START.match(s):
            tokens.append(Token("START", s))
        elif KW_END.match(s):
            tokens.append(Token("END", s))
        elif m := KW_IF.match(s):
            tokens.append(Token("IF", s, condition=m.group(2).strip()))
        elif KW_ELSE.match(s):
            tokens.append(Token("ELSE", s))
        elif KW_ENDIF.match(s):
            tokens.append(Token("ENDIF", s))
        elif m := KW_WHILE.match(s):
            tokens.append(Token("WHILE", s, condition=m.group(2).strip()))
        elif KW_ENDWHILE.match(s):
            tokens.append(Token("ENDWHILE", s))
        elif m := KW_FOR.match(s):
            var_expr = m.group(2).strip()
            to_expr  = m.group(4).strip()
            tokens.append(Token("FOR", s, condition=f"{var_expr} до {to_expr}"))
        elif KW_ENDFOR.match(s):
            tokens.append(Token("ENDFOR", s))
        elif m := KW_INPUT.match(s):
            # Нормализуем список переменных; ключевое слово не входит в лейбл
            vars_str = ", ".join(v.strip() for v in m.group(2).split(","))
            tokens.append(Token("INPUT", vars_str))
        elif m := KW_OUTPUT.match(s):
            # Только содержимое; ключевое слово не входит в лейбл
            tokens.append(Token("OUTPUT", m.group(2).strip()))
        else:
            tokens.append(Token("ASSIGN", s))

    return tokens


# ── Тип «открытого выхода» ───────────────────────────────────────────────────
#
# Exit = (from_id, edge_label, back_edge_flag)
# Когда станет известен следующий узел — из этого строится ребро.

Exit = tuple[str, str, bool]


class PseudocodeParser:
    """
    Рекурсивный парсер псевдокода → граф потока управления.

    Ключевые свойства:
    • Узлы типа «merge» не создаются. Открытые выходы веток накапливаются
      и соединяются напрямую со следующим содержательным узлом.
    • Обратные дуги цикла помечаются back_edge=True — рендерер блок-схем
      использует этот флаг для маршрутизации линии сбоку (headport=n,
      constraint=false).
    • Поддерживаются вложенные конструкции любой глубины.
    """

    def __init__(self):
        self._counter = 0
        self._nodes: list[dict[str, Any]] = []
        self._edges: list[dict[str, Any]] = []
        self._errors: list[str] = []

    # ── Public API ────────────────────────────────────────────────────────

    def parse(self, text: str) -> ParseResult:
        self._counter = 0
        self._nodes = []
        self._edges = []
        self._errors = []

        lines = text.splitlines()
        tokens = _tokenize(lines)

        if not tokens:
            self._errors.append("Текст пуст или не содержит операторов.")
            return ParseResult(errors=self._errors)

        _entry, _exits, pos = self._parse_block(tokens, 0, stop_at=set())

        if pos < len(tokens):
            remaining = [t.value for t in tokens[pos:]]
            self._errors.append(
                "Необработанные токены (возможно, пропущен конец конструкции): "
                f"{remaining}"
            )

        return ParseResult(
            nodes=self._nodes,
            edges=self._edges,
            errors=self._errors,
        )

    # ── Node / Edge helpers ───────────────────────────────────────────────

    def _new_id(self) -> str:
        self._counter += 1
        return f"node_{self._counter}"

    def _add_node(self, node_type: str, label: str) -> str:
        nid = self._new_id()
        self._nodes.append({
            "id":     nid,
            "type":   node_type,
            "label":  label,
            "next":   [],
            "branch": None,
        })
        return nid

    def _add_edge(
        self,
        from_id: str,
        to_id: str,
        label: str = "",
        back_edge: bool = False,
    ) -> None:
        self._edges.append({
            "from":      from_id,
            "to":        to_id,
            "label":     label,
            "back_edge": back_edge,
        })
        for node in self._nodes:
            if node["id"] == from_id:
                if to_id not in node["next"]:
                    node["next"].append(to_id)
                break

    def _wire_exits(self, exits: list[Exit], to_id: str) -> None:
        """Замыкает все открытые выходы на узел to_id."""
        for from_id, label, back_edge in exits:
            self._add_edge(from_id, to_id, label, back_edge)

    # ── Recursive block parser ────────────────────────────────────────────

    def _parse_block(
        self,
        tokens: list[Token],
        pos: int,
        stop_at: set[str],
    ) -> tuple[str | None, list[Exit], int]:
        """
        Разбирает последовательность операторов начиная с pos.
        Останавливается при достижении стоп-токена или конца списка.

        Возвращает:
            entry  — id первого созданного узла (None если блок пуст)
            exits  — список открытых Exit-троек
            pos    — позиция после обработанных токенов
        """
        entry: str | None = None
        exits: list[Exit] = []

        while pos < len(tokens):
            tok = tokens[pos]
            if tok.kind in stop_at:
                break

            # ── Конструкции, которые сами управляют exits ────────────────
            if tok.kind == "IF":
                pos += 1
                dec_id, exits, pos = self._parse_if(tok, tokens, pos, exits)
                if entry is None:
                    entry = dec_id
                continue

            if tok.kind == "WHILE":
                pos += 1
                dec_id, exits, pos = self._parse_while(tok, tokens, pos, exits)
                if entry is None:
                    entry = dec_id
                continue

            if tok.kind == "FOR":
                pos += 1
                dec_id, exits, pos = self._parse_for(tok, tokens, pos, exits)
                if entry is None:
                    entry = dec_id
                continue

            # ── Простые узлы ─────────────────────────────────────────────
            if tok.kind == "START":
                nid = self._add_node("start", "Начало")
            elif tok.kind == "END":
                nid = self._add_node("end", "Конец")
            elif tok.kind == "INPUT":
                nid = self._add_node("io", tok.value)
            elif tok.kind == "OUTPUT":
                nid = self._add_node("io", tok.value)
            elif tok.kind == "ASSIGN":
                nid = self._add_node("process", tok.value)
            else:
                self._errors.append(
                    f"Неожиданный токен «{tok.kind}: {tok.value}» — пропускается."
                )
                pos += 1
                continue

            self._wire_exits(exits, nid)
            if entry is None:
                entry = nid
            exits = [(nid, "", False)]
            pos += 1

        return entry, exits, pos

    # ── IF / ELSE / ENDIF ─────────────────────────────────────────────────

    def _parse_if(
        self,
        tok: Token,
        tokens: list[Token],
        pos: int,
        prev_exits: list[Exit],
    ) -> tuple[str, list[Exit], int]:
        """
        Строит ромб-узел decision, разбирает ветки then/else.

        Возвращает (dec_id, merged_exits, pos).
        merged_exits — объединённые открытые концы обеих веток;
        они все замкнутся на следующий узел после конструкции.
        """
        dec_id = self._add_node("decision", tok.condition + "?")
        self._wire_exits(prev_exits, dec_id)

        # Ветка «да»
        then_entry, then_exits, pos = self._parse_block(
            tokens, pos, stop_at={"ELSE", "ENDIF"}
        )
        if then_entry is not None:
            self._add_edge(dec_id, then_entry, "да")
        else:
            # Пустое тело then — открытый выход прямо от ромба
            then_exits = [(dec_id, "да", False)]

        # Ветка «нет»
        has_else = pos < len(tokens) and tokens[pos].kind == "ELSE"
        if has_else:
            pos += 1  # пропускаем ELSE
            else_entry, else_exits, pos = self._parse_block(
                tokens, pos, stop_at={"ENDIF"}
            )
            if else_entry is not None:
                self._add_edge(dec_id, else_entry, "нет")
            else:
                else_exits = [(dec_id, "нет", False)]
        else:
            # Нет ветки else — открытый выход «нет» от ромба
            else_exits = [(dec_id, "нет", False)]

        # Пропускаем ENDIF
        if pos < len(tokens) and tokens[pos].kind == "ENDIF":
            pos += 1
        else:
            self._errors.append(
                f"Ожидался 'конец если'/'endif' после условия «{tok.condition}»."
            )

        merged: list[Exit] = []
        merged.extend(then_exits)
        merged.extend(else_exits)
        return dec_id, merged, pos

    # ── WHILE ─────────────────────────────────────────────────────────────

    def _parse_while(
        self,
        tok: Token,
        tokens: list[Token],
        pos: int,
        prev_exits: list[Exit],
    ) -> tuple[str, list[Exit], int]:
        """
        Строит ромб-условие, тело цикла и обратную дугу.

        Возвращает (dec_id, exits, pos).
        exits содержит одну открытую тройку (dec_id, "нет", False) —
        она замкнётся на первый узел после цикла.
        """
        dec_id = self._add_node("decision", tok.condition + "?")
        self._wire_exits(prev_exits, dec_id)

        body_entry, body_exits, pos = self._parse_block(
            tokens, pos, stop_at={"ENDWHILE"}
        )
        if pos < len(tokens) and tokens[pos].kind == "ENDWHILE":
            pos += 1
        else:
            self._errors.append(
                f"Ожидался 'конец пока'/'endwhile' после условия «{tok.condition}»."
            )

        if body_entry is not None:
            self._add_edge(dec_id, body_entry, "да")
            # Обратные дуги: конец(ы) тела → ромб (back_edge=True)
            for from_id, lbl, _ in body_exits:
                self._add_edge(from_id, dec_id, lbl, back_edge=True)
        else:
            # Пустое тело — петля сразу на условие
            self._add_edge(dec_id, dec_id, "да", back_edge=True)

        # Открытый выход «нет» → первый узел после цикла
        return dec_id, [(dec_id, "нет", False)], pos

    # ── FOR ───────────────────────────────────────────────────────────────

    def _parse_for(
        self,
        tok: Token,
        tokens: list[Token],
        pos: int,
        prev_exits: list[Exit],
    ) -> tuple[str, list[Exit], int]:
        """
        Обрабатывает FOR-цикл аналогично WHILE.
        """
        dec_id = self._add_node("decision", tok.condition + "?")
        self._wire_exits(prev_exits, dec_id)

        body_entry, body_exits, pos = self._parse_block(
            tokens, pos, stop_at={"ENDFOR"}
        )
        if pos < len(tokens) and tokens[pos].kind == "ENDFOR":
            pos += 1
        else:
            self._errors.append(
                f"Ожидался 'конец для'/'endfor' после условия «{tok.condition}»."
            )

        if body_entry is not None:
            self._add_edge(dec_id, body_entry, "да")
            for from_id, lbl, _ in body_exits:
                self._add_edge(from_id, dec_id, lbl, back_edge=True)
        else:
            self._add_edge(dec_id, dec_id, "да", back_edge=True)

        return dec_id, [(dec_id, "нет", False)], pos