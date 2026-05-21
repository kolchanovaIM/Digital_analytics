# core_parser.py — переработанный парсер с корректной обработкой вложенных конструкций
import re

class PseudocodeParser:
    def __init__(self):
        self._id = 0
        self.nodes = []
        self.edges = []
        self._stack = []          # стек контекстов для вложенных блоков
        self._prev_id = None      # текущий последний узел

    def _new_id(self):
        self._id += 1
        return f"n{self._id}"

    def _add_node(self, node_type: str, label: str) -> str:
        nid = self._new_id()
        self.nodes.append({'id': nid, 'type': node_type, 'label': label})
        return nid

    def _add_edge(self, from_id: str, to_id: str, label: str = None):
        edge = (from_id, to_id)
        if label:
            edge = (from_id, to_id, label)
        self.edges.append(edge)

    def _top_context(self):
        """Возвращает верхний контекст стека или None."""
        return self._stack[-1] if self._stack else None

    def parse(self, text: str) -> dict:
        self._id = 0
        self.nodes = []
        self.edges = []
        self._stack = []

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return {'nodes': self.nodes, 'edges': self.edges}

        self._prev_id = self._add_node('start', 'Начало')

        for line in lines:
            if line.startswith('//') or line.startswith('#'):
                continue

            low = line.lower().strip()
            if low in ('начало', 'start', 'конец', 'end'):
                continue

            # ---------- УСЛОВИЕ (если) ----------
            if low.startswith('если') or low.startswith('if '):
                cond = self._extract_condition(line, 'если', 'if')
                cond_id = self._add_node('decision', cond)
                self._add_edge(self._prev_id, cond_id)      # вход в ромб

                # контекст условия
                ctx = {
                    'type': 'if',
                    'decision_id': cond_id,
                    'wait_true': True,       # ожидаем первый оператор для ветки "да"
                    'wait_false': False,
                    'if_end': None,          # последний узел тела if (заполнится при else)
                    'else_present': False,
                    'else_end': None
                }
                self._stack.append(ctx)
                self._prev_id = cond_id
                continue

            # ---------- ИНАЧЕ ----------
            if low == 'иначе' or low == 'else':
                top = self._top_context()
                if not top or top['type'] != 'if':
                    continue
                # завершаем тело if
                top['wait_true'] = False
                top['if_end'] = self._prev_id
                top['else_present'] = True
                top['wait_false'] = True     # теперь ждём первый оператор else
                self._prev_id = top['decision_id']   # тело else пойдёт от условия
                continue

            # ---------- КОНЕЦ ЕСЛИ ----------
            if low in ('конец если', 'конец_если', 'endif'):
                top = self._top_context()
                if not top or top['type'] != 'if':
                    continue
                # извлекаем контекст
                self._stack.pop()
                dec_id = top['decision_id']
                # создаём невидимый узел слияния
                merge_id = self._new_id()
                self.nodes.append({'id': merge_id, 'type': 'merge', 'label': ''})

                if top['else_present']:
                    # есть else: соединяем конец тела if и конец тела else с merge
                    if top['if_end']:
                        self._add_edge(top['if_end'], merge_id)
                    if top.get('else_end'):
                        self._add_edge(top['else_end'], merge_id)
                    # рёбра "да" и "нет" уже должны были быть добавлены при первых операторах
                    # если ветка пуста, добавляем прямое ребро от decision к merge
                    if not top.get('if_end') and top['wait_true']:
                        self._add_edge(dec_id, merge_id, 'да')
                    if not top.get('else_end') and top['wait_false']:
                        self._add_edge(dec_id, merge_id, 'нет')
                else:
                    # только if: соединяем конец тела if с merge, и добавляем ребро "нет" от decision
                    if top.get('if_end'):
                        self._add_edge(top['if_end'], merge_id)
                    else:
                        # тело if пусто
                        self._add_edge(dec_id, merge_id, 'да')
                    self._add_edge(dec_id, merge_id, 'нет')

                self._prev_id = merge_id
                continue

            # ---------- ЦИКЛ ПОКА ----------
            if low.startswith('пока') or low.startswith('while '):
                cond = self._extract_condition(line, 'пока', 'while')
                cond_id = self._add_node('decision', cond)
                self._add_edge(self._prev_id, cond_id)      # вход в цикл

                ctx = {
                    'type': 'while',
                    'decision_id': cond_id,
                    'wait_true': True,       # ожидаем первый оператор тела цикла (ветка "да")
                    'loop_end': None         # последний узел тела цикла
                }
                self._stack.append(ctx)
                self._prev_id = cond_id
                continue

            # ---------- КОНЕЦ ПОКА ----------
            if low in ('конец пока', 'конец_пока', 'endwhile'):
                top = self._top_context()
                if not top or top['type'] != 'while':
                    continue
                self._stack.pop()
                dec_id = top['decision_id']

                # создаём выход из цикла
                exit_id = self._new_id()
                self.nodes.append({'id': exit_id, 'type': 'merge', 'label': ''})

                # обратная связь (тело цикла → ромб)
                if top.get('loop_end'):
                    self._add_edge(top['loop_end'], dec_id, 'да')
                else:
                    # тело цикла пусто
                    self._add_edge(dec_id, dec_id, 'да')

                # ветка "нет" из ромба наружу
                self._add_edge(dec_id, exit_id, 'нет')

                self._prev_id = exit_id
                continue

            # ---------- ВВОД / ВЫВОД И ДРУГИЕ ОПЕРАТОРЫ ----------
            # Определяем тип узла
            if low.startswith('ввод') or low.startswith('input'):
                expr = line[len('ввод'):].strip() if low.startswith('ввод') else line[len('input'):].strip()
                node_type = 'io'
            elif low.startswith('вывод') or low.startswith('output'):
                expr = line[len('вывод'):].strip() if low.startswith('вывод') else line[len('output'):].strip()
                node_type = 'io'
            else:
                node_type = 'process'
                expr = line

            node_id = self._add_node(node_type, expr)

            # Обрабатываем ожидающие рёбра из вершины стека
            top = self._top_context()
            if top:
                if top.get('wait_true'):
                    # первый оператор ветки "да"
                    self._add_edge(top['decision_id'], node_id, 'да')
                    top['wait_true'] = False
                    if top['type'] == 'if':
                        top['if_end'] = node_id
                    elif top['type'] == 'while':
                        top['loop_end'] = node_id
                elif top.get('wait_false'):
                    # первый оператор ветки "нет" (для if-else)
                    self._add_edge(top['decision_id'], node_id, 'нет')
                    top['wait_false'] = False
                    top['else_end'] = node_id
                else:
                    # обычное ребро от предыдущего узла
                    self._add_edge(self._prev_id, node_id)
                    # обновляем конечный узел текущего контекста
                    if top['type'] == 'if':
                        if top.get('else_present'):
                            top['else_end'] = node_id
                        else:
                            top['if_end'] = node_id
                    elif top['type'] == 'while':
                        top['loop_end'] = node_id
            else:
                # нет активного контекста – просто соединяем
                self._add_edge(self._prev_id, node_id)

            self._prev_id = node_id

        # Закрываем оставшиеся открытые конструкции (на случай незавершённого ввода)
        while self._stack:
            top = self._stack.pop()
            dec_id = top['decision_id']
            merge_id = self._new_id()
            self.nodes.append({'id': merge_id, 'type': 'merge', 'label': ''})
            if top['type'] == 'if':
                if top.get('if_end'):
                    self._add_edge(top['if_end'], merge_id)
                if top.get('else_end'):
                    self._add_edge(top['else_end'], merge_id)
                self._add_edge(dec_id, merge_id, 'нет')
            elif top['type'] == 'while':
                if top.get('loop_end'):
                    self._add_edge(top['loop_end'], dec_id, 'да')
                self._add_edge(dec_id, merge_id, 'нет')
            self._prev_id = merge_id

        # Завершаем алгоритм
        end_id = self._add_node('end', 'Конец')
        self._add_edge(self._prev_id, end_id)
        return {'nodes': self.nodes, 'edges': self.edges}

    def _extract_condition(self, line: str, rus: str, eng: str) -> str:
        for prefix in (rus, eng):
            if line.lower().startswith(prefix):
                cond = line[len(prefix):].strip()
                cond = re.sub(r'\s*(то|then)\s*$', '', cond, flags=re.IGNORECASE)
                return cond
        return "условие"