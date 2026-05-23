from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(slots=True)
class NodeData:
    id: int
    text: str
    shape: str


@dataclass(slots=True)
class EdgeData:
    source: int
    target: int
    label: str = ""
    is_back_edge: bool = False


class ParseError(Exception):
    def __init__(self, message: str, line: int | None = None):
        self.line = line
        super().__init__(f"{message}" if line in (None, 0) else f"{message} (строка {line})")


START_KEYWORD = "НАЧАЛО"
END_KEYWORD = "КОНЕЦ"
INPUT_KEYWORD = "ВВОД"
OUTPUT_KEYWORD = "ВЫВОД"
IF_KEYWORD = "ЕСЛИ"
THEN_KEYWORD = "ТО"
ELSE_KEYWORD = "ИНАЧЕ"
ENDIF_KEYWORD = "КОНЕЦ ЕСЛИ"
WHILE_KEYWORD = "ПОКА"
ENDWHILE_KEYWORD = "КОНЕЦ ПОКА"
WHILE_BODY_HINT = "ВЫПОЛНИТЬ"

_CLOSERS = {ELSE_KEYWORD, ENDIF_KEYWORD, ENDWHILE_KEYWORD}


@dataclass(slots=True)
class _Line:
    text: str
    lineno: int
    synthetic: bool = False


@dataclass(slots=True)
class _Stmt:
    kind: str
    text: str = ""
    lineno: int = 0
    then_body: Optional[list] = None
    else_body: Optional[list] = None
    body: Optional[list] = None


class _Parser:
    def __init__(self, raw_text: str):
        lines = []
        for idx, raw in enumerate(raw_text.splitlines(), start=1):
            cleaned = raw.strip()
            if cleaned:
                lines.append(_Line(cleaned, idx))
        if not lines:
            raise ParseError("Редактор пуст", 0)
        if not _is_exact_keyword(lines[0].text, START_KEYWORD):
            lines.insert(0, _Line(START_KEYWORD, 0, True))
        if not _is_exact_keyword(lines[-1].text, END_KEYWORD):
            lines.append(_Line(END_KEYWORD, 0, True))
        self.lines = lines
        self.pos = 0

    def parse(self) -> Tuple[List[NodeData], List[EdgeData]]:
        # ИСПРАВЛЕНО: Вместо stop=None передаем пустое множество set(), чтобы избежать ошибки итерации
        stmts = self._parse_block(stop=set(), context=None)
        if self.pos != len(self.lines):
            line = self.lines[self.pos]
            raise ParseError(f"Лишняя инструкция: {line.text}", line.lineno)
        nodes: List[NodeData] = []
        edges: List[EdgeData] = []
        next_id = 1

        def new_node(text: str, shape: str) -> int:
            nonlocal next_id
            node_id = next_id
            next_id += 1
            nodes.append(NodeData(node_id, text, shape))
            return node_id

        def build_block(block: list[_Stmt]) -> tuple[Optional[int], List[int]]:
            entry_id: Optional[int] = None
            prev_exits: List[int] = []
            for stmt in block:
                stmt_entry, stmt_exits = build_stmt(stmt)
                if stmt_entry is None:
                    continue
                if entry_id is None:
                    entry_id = stmt_entry
                if prev_exits:
                    for src in prev_exits:
                        edges.append(EdgeData(src, stmt_entry))
                prev_exits = stmt_exits
            return entry_id, prev_exits

        def build_stmt(stmt: _Stmt) -> tuple[Optional[int], List[int]]:
            kind = stmt.kind
            if kind == "action":
                node_id = new_node(stmt.text, "process")
                return node_id, [node_id]
            if kind == "start":
                node_id = new_node(START_KEYWORD, "terminal")
                return node_id, [node_id]
            if kind == "end":
                node_id = new_node(END_KEYWORD, "terminal")
                return node_id, [node_id]
            if kind == "input":
                node_id = new_node(stmt.text, "io")
                return node_id, [node_id]
            if kind == "output":
                node_id = new_node(stmt.text, "io")
                return node_id, [node_id]
            if kind == "if":
                decision_id = new_node(stmt.text, "decision")
                then_entry, then_exits = build_block(stmt.then_body or [])
                if then_entry is not None:
                    edges.append(EdgeData(decision_id, then_entry, "да"))
                else:
                    then_exits = []
                else_exits: List[int] = []
                if stmt.else_body is not None:
                    else_entry, else_exits = build_block(stmt.else_body)
                    if else_entry is not None:
                        edges.append(EdgeData(decision_id, else_entry, "нет"))
                    else:
                        else_exits = [decision_id]
                else:
                    else_exits = [decision_id]
                exits = then_exits + else_exits
                return decision_id, exits
            if kind == "while":
                decision_id = new_node(stmt.text, "decision")
                body_entry, body_exits = build_block(stmt.body or [])
                if body_entry is not None:
                    edges.append(EdgeData(decision_id, body_entry, "да"))
                    for src in body_exits:
                        edges.append(EdgeData(src, decision_id, "", True))
                return decision_id, [decision_id]
            raise ParseError(f"Неизвестный тип узла: {kind}", stmt.lineno)

        build_block(stmts)
        return nodes, edges

    def _parse_block(self, stop: set[str], opener: tuple[str, int] = None, **kwargs) -> list[_Stmt]:
        body = []
        stop_set = stop if stop is not None else set()

        while self.pos < len(self.lines):
            line = self.lines[self.pos]

            found_stop = False
            for stop_word in stop_set:
                if _startswith_keyword(line.text, stop_word):
                    found_stop = True
                    break

            if found_stop:
                break

            stmt = self._parse_stmt()
            if stmt:
                body.append(stmt)
        else:
            # ИСПРАВЛЕНО: Ошибка вызывается только если у блока БЫЛО задано стоп-слово,
            # то есть это вложенный блок (IF, WHILE и т.д.), который не встретил закрытия.
            if stop_set:
                if opener:
                    raise ParseError(f"Не найден ожидаемый конец блока для {opener[0]} со строки {opener[1]}", opener[1])
                else:
                    last_line = self.lines[-1].lineno if self.lines else 0
                    raise ParseError("Неожиданный конец файла: блок не был закрыт", last_line)

        return body

    def _parse_stmt(self) -> Optional[_Stmt]:
        if self.pos >= len(self.lines):
            return None
        line = self.lines[self.pos]
        txt = line.text

        if _is_exact_keyword(txt, START_KEYWORD):
            self.pos += 1
            return _Stmt("start", START_KEYWORD, line.lineno)
        if _is_exact_keyword(txt, END_KEYWORD):
            self.pos += 1
            return _Stmt("end", END_KEYWORD, line.lineno)
        if _startswith_keyword(txt, INPUT_KEYWORD):
            self.pos += 1
            return _Stmt("input", txt, line.lineno)
        if _startswith_keyword(txt, OUTPUT_KEYWORD):
            self.pos += 1
            return _Stmt("output", txt, line.lineno)
        if _startswith_keyword(txt, IF_KEYWORD):
            return self._parse_if()
        if _startswith_keyword(txt, WHILE_KEYWORD):
            return self._parse_while()

        # Любая другая строка трактуется как обычное действие (процесс)
        self.pos += 1
        return _Stmt("action", txt, line.lineno)

    def _parse_if(self) -> _Stmt:
        line = self.lines[self.pos]
        raw = line.text
        condition = raw[len(IF_KEYWORD):].strip()
        upper = _normalize(condition)
        if upper.endswith(THEN_KEYWORD):
            condition = condition[: -len(THEN_KEYWORD)].strip()
        text = condition or IF_KEYWORD
        opener_line = line.lineno
        self.pos += 1

        # 1. Считываем ветку "ТО" до ИНАЧЕ или КОНЕЦ ЕСЛИ
        then_body = self._parse_block({ELSE_KEYWORD, ENDIF_KEYWORD}, (IF_KEYWORD, opener_line))
        else_body = None

        # 2. Обрабатываем ветку ИНАЧЕ, если она есть
        if self.pos < len(self.lines):
            current_line = self.lines[self.pos]

            if _startswith_keyword(current_line.text, ELSE_KEYWORD):
                normalized = _normalize(current_line.text)

                # Вариант А: Чистое слово "ИНАЧЕ" на отдельной строке
                if normalized == ELSE_KEYWORD:
                    self.pos += 1
                    else_body = self._parse_block({ENDIF_KEYWORD}, (IF_KEYWORD, opener_line))

                # Вариант Б: Конструкция "ИНАЧЕ ЕСЛИ ..."
                elif normalized.startswith(f"{ELSE_KEYWORD} {IF_KEYWORD}"):
                    rest = current_line.text[len(ELSE_KEYWORD):].strip()

                    # ИСПРАВЛЕНО: Безопасно подменяем строку через создание временного объекта _Line
                    # без мутации оригинального списка полей
                    saved_line = self.lines[self.pos]
                    self.lines[self.pos] = _Line(rest, saved_line.lineno, saved_line.synthetic)

                    else_body = self._parse_block({ENDIF_KEYWORD}, (IF_KEYWORD, opener_line))

                    # Возвращаем исходный объект строки на место
                    self.lines[self.pos] = saved_line

                # Вариант В: Склеенная строка типа "иначе вывод х" или "иначе вы"
                else:
                    rest = current_line.text[len(ELSE_KEYWORD):].strip()

                    # Создаем виртуальную строку для изолированного парсинга команды
                    saved_line = self.lines[self.pos]
                    self.lines[self.pos] = _Line(rest, saved_line.lineno, saved_line.synthetic)

                    # _parse_stmt внутри себя сам сделает self.pos += 1
                    single_stmt = self._parse_stmt()
                    else_body = [single_stmt] if single_stmt else []

                    # Возвращаем исходный объект строки на место
                    self.lines[self.pos - 1] = saved_line
                    # Лишний self.pos += 1 удален!

        # 3. Проверяем закрывающий КОНЕЦ ЕСЛИ
        if self.pos >= len(self.lines) or not _startswith_keyword(self.lines[self.pos].text, ENDIF_KEYWORD):
            raise ParseError(f"Не найден {ENDIF_KEYWORD} для строки {opener_line}", opener_line)

        self.pos += 1
        return _Stmt("if", text, opener_line, then_body=then_body, else_body=else_body)

    def _parse_while(self) -> _Stmt:
        line = self.lines[self.pos]
        raw = line.text
        condition = raw[len(WHILE_KEYWORD):].strip()
        if condition.upper().endswith(WHILE_BODY_HINT):
            condition = condition[: -len(WHILE_BODY_HINT)].strip()
        text = condition or WHILE_KEYWORD
        opener_line = line.lineno
        self.pos += 1
        body = self._parse_block({ENDWHILE_KEYWORD}, (WHILE_KEYWORD, opener_line))
        if self.pos >= len(self.lines) or not _startswith_keyword(self.lines[self.pos].text, ENDWHILE_KEYWORD):
            raise ParseError(f"Не найден {ENDWHILE_KEYWORD} для строки {opener_line}", opener_line)
        self.pos += 1
        return _Stmt("while", text, opener_line, body=body)


def _normalize(text: str) -> str:
    return " ".join(text.strip().upper().split())


def _startswith_keyword(text: str, keyword: str) -> bool:
    return _normalize(text).startswith(keyword)


def _is_exact_keyword(text: str, keyword: str) -> bool:
    return _normalize(text) == keyword


def parse_pseudocode(text: str) -> tuple[list[NodeData], list[EdgeData]]:
    return _Parser(text).parse()