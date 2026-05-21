from dataclasses import dataclass


@dataclass
class NodeData:
    node_id: str
    text: str
    shape: str


@dataclass
class EdgeData:
    source: str
    target: str
    label: str = ""
    is_back_edge: bool = False


class ParseError(Exception):
    pass


class PseudoCodeParser:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.counter = 0

    def next_id(self):
        self.counter += 1
        return f"node_{self.counter}"

    def add_node(self, text, shape):
        node = NodeData(
            node_id=self.next_id(),
            text=text,
            shape=shape
        )

        self.nodes.append(node)
        return node

    def add_edge(
        self,
        source,
        target,
        label="",
        is_back_edge=False
    ):
        self.edges.append(
            EdgeData(
                source=source,
                target=target,
                label=label,
                is_back_edge=is_back_edge
            )
        )

    def parse(self, text: str):

        if not text.strip():
            raise ParseError(
                "Редактор пуст. Введите алгоритм для генерации."
            )

        self.nodes.clear()
        self.edges.clear()
        self.counter = 0

        raw_lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        normalized = [line.upper() for line in raw_lines]

        if "НАЧАЛО" not in normalized:
            raw_lines.insert(0, "НАЧАЛО")

        if "КОНЕЦ" not in normalized:
            raw_lines.append("КОНЕЦ")

        lines = raw_lines

        previous_node = None

        if_stack = []
        while_stack = []

        for index, line in enumerate(lines):

            upper = line.upper()

            # =========================================
            # НАЧАЛО
            # =========================================

            if upper == "НАЧАЛО":

                node = self.add_node(line, "oval")

                if previous_node:
                    self.add_edge(
                        previous_node.node_id,
                        node.node_id
                    )

                previous_node = node
                continue

            # =========================================
            # КОНЕЦ
            # =========================================

            if upper == "КОНЕЦ":

                node = self.add_node(line, "oval")

                if previous_node:
                    self.add_edge(
                        previous_node.node_id,
                        node.node_id
                    )

                previous_node = node
                continue

            # =========================================
            # ЕСЛИ
            # =========================================

            if upper.startswith("ЕСЛИ") and upper.endswith("ТО"):

                condition = (
                    line[4:-2]
                    .replace("ТО", "")
                    .strip()
                )

                decision = self.add_node(
                    condition,
                    "diamond"
                )

                if previous_node:
                    self.add_edge(
                        previous_node.node_id,
                        decision.node_id
                    )

                merge_node = self.add_node(
                    "",
                    "merge"
                )

                if_stack.append({
                    "decision": decision,
                    "merge": merge_node,
                    "true_end": None,
                    "false_end": None,
                    "in_else": False,
                    "first_edge_added": False
                })

                previous_node = decision
                continue

            # =========================================
            # ИНАЧЕ
            # =========================================

            if upper == "ИНАЧЕ":

                if not if_stack:
                    raise ParseError(
                        f"ИНАЧЕ без ЕСЛИ "
                        f"в строке {index + 1}"
                    )

                block = if_stack[-1]

                block["true_end"] = previous_node
                block["in_else"] = True
                block["first_edge_added"] = False

                previous_node = block["decision"]

                continue

            # =========================================
            # КОНЕЦ ЕСЛИ
            # =========================================

            if upper == "КОНЕЦ ЕСЛИ":

                if not if_stack:
                    raise ParseError(
                        f"Непарный КОНЕЦ ЕСЛИ "
                        f"в строке {index + 1}"
                    )

                block = if_stack.pop()

                merge = block["merge"]

                if block["in_else"]:

                    block["false_end"] = previous_node

                    self.add_edge(
                        block["true_end"].node_id,
                        merge.node_id
                    )

                    self.add_edge(
                        block["false_end"].node_id,
                        merge.node_id
                    )

                else:

                    block["true_end"] = previous_node

                    self.add_edge(
                        block["decision"].node_id,
                        merge.node_id,
                        label="нет"
                    )

                    self.add_edge(
                        block["true_end"].node_id,
                        merge.node_id
                    )

                previous_node = merge

                continue

            # =========================================
            # ПОКА
            # =========================================

            if upper.startswith("ПОКА"):

                condition = (
                    line.replace("ПОКА", "")
                    .replace("ВЫПОЛНИТЬ", "")
                    .strip()
                )

                decision = self.add_node(
                    condition,
                    "diamond"
                )

                if previous_node:
                    self.add_edge(
                        previous_node.node_id,
                        decision.node_id
                    )

                exit_node = self.add_node(
                    "",
                    "merge"
                )

                while_stack.append({
                    "decision": decision,
                    "exit": exit_node,
                    "body_end": None,
                    "first_edge_added": False
                })

                previous_node = decision

                continue

            # =========================================
            # КОНЕЦ ПОКА
            # =========================================

            if upper == "КОНЕЦ ПОКА":

                if not while_stack:
                    raise ParseError(
                        f"Непарный КОНЕЦ ПОКА "
                        f"в строке {index + 1}"
                    )

                block = while_stack.pop()

                body_end = previous_node

                self.add_edge(
                    body_end.node_id,
                    block["decision"].node_id,
                    is_back_edge=True
                )

                self.add_edge(
                    block["decision"].node_id,
                    block["exit"].node_id,
                    label="нет"
                )

                previous_node = block["exit"]

                continue

            # =========================================
            # ОБЫЧНОЕ ДЕЙСТВИЕ
            # =========================================

            shape = "rectangle"

            if (
                upper.startswith("ВВОД")
                or upper.startswith("ВЫВОД")
            ):
                shape = "parallelogram"

            node = self.add_node(line, shape)

            if previous_node:

                edge_added = False

                # =====================================
                # IF
                # =====================================

                if if_stack:

                    block = if_stack[-1]

                    if previous_node == block["decision"]:

                        label = (
                            "нет"
                            if block["in_else"]
                            else "да"
                        )

                        self.add_edge(
                            previous_node.node_id,
                            node.node_id,
                            label=label
                        )

                        block["first_edge_added"] = True
                        edge_added = True

                # =====================================
                # WHILE
                # =====================================

                if while_stack and not edge_added:

                    block = while_stack[-1]

                    if previous_node == block["decision"]:

                        self.add_edge(
                            previous_node.node_id,
                            node.node_id,
                            label="да"
                        )

                        block["first_edge_added"] = True
                        edge_added = True

                # =====================================
                # ОБЫЧНОЕ РЕБРО
                # =====================================

                if not edge_added:

                    self.add_edge(
                        previous_node.node_id,
                        node.node_id
                    )

            previous_node = node

        # =========================================
        # ПРОВЕРКА БЛОКОВ
        # =========================================

        if if_stack:
            raise ParseError(
                "Не закрыт блок ЕСЛИ"
            )

        if while_stack:
            raise ParseError(
                "Не закрыт блок ПОКА"
            )

        return self.nodes, self.edges