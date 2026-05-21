"""
xml_manager.py — Управление сериализацией блок-схем в XML и обратно.

Поддерживает:
    • Сохранение блок-схемы в XML-формате
    • Загрузку блок-схемы из XML
    • Преобразование между XML и внутренними структурами
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from dataclasses import dataclass, field
from pathlib import Path
import uuid

from PyQt6.QtCore import QPointF


@dataclass
class SerializedNode:
    """Сериализованное представление узла блок-схемы."""
    id: str
    type: str
    x: float
    y: float
    width: float
    height: float
    text: str
    node_type: str = "flow_item"  # flow_item или line


@dataclass
class SerializedLine:
    """Сериализованное представление линии/связи."""
    id: str
    type: str  # arrow, solid, dashed
    x1: float
    y1: float
    x2: float
    y2: float
    node_type: str = "line"


@dataclass
class FlowchartData:
    """Полные данные блок-схемы для сериализации."""
    nodes: list[SerializedNode] = field(default_factory=list)
    lines: list[SerializedLine] = field(default_factory=list)
    version: str = "1.0"


class XMLManager:
    """Менеджер для работы с XML-файлами блок-схем."""

    @staticmethod
    def save_to_xml(data: FlowchartData, filepath: str | Path) -> bool:
        """
        Сохраняет блок-схему в XML-файл.

        Args:
            data: Данные блок-схемы
            filepath: Путь для сохранения

        Returns:
            bool: Успешность операции
        """
        try:
            root = ET.Element("flowchart")
            root.set("version", data.version)
            root.set("generator", "FlowChart Designer")

            # Сохраняем узлы
            nodes_elem = ET.SubElement(root, "nodes")
            for node in data.nodes:
                node_elem = ET.SubElement(nodes_elem, "node")
                node_elem.set("id", node.id)
                node_elem.set("type", node.type)
                node_elem.set("node_type", node.node_type)

                ET.SubElement(node_elem, "x").text = str(node.x)
                ET.SubElement(node_elem, "y").text = str(node.y)
                ET.SubElement(node_elem, "width").text = str(node.width)
                ET.SubElement(node_elem, "height").text = str(node.height)
                ET.SubElement(node_elem, "text").text = node.text

            # Сохраняем линии
            lines_elem = ET.SubElement(root, "lines")
            for line in data.lines:
                line_elem = ET.SubElement(lines_elem, "line")
                line_elem.set("id", line.id)
                line_elem.set("type", line.type)
                line_elem.set("node_type", line.node_type)

                ET.SubElement(line_elem, "x1").text = str(line.x1)
                ET.SubElement(line_elem, "y1").text = str(line.y1)
                ET.SubElement(line_elem, "x2").text = str(line.x2)
                ET.SubElement(line_elem, "y2").text = str(line.y2)

            # Создаём pretty XML
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")
            tree.write(str(filepath), encoding="utf-8", xml_declaration=True)

            return True

        except Exception as e:
            print(f"Ошибка сохранения XML: {e}")
            return False

    @staticmethod
    def load_from_xml(filepath: str | Path) -> FlowchartData | None:
        """
        Загружает блок-схему из XML-файла.

        Args:
            filepath: Путь к XML-файлу

        Returns:
            FlowchartData или None при ошибке
        """
        try:
            tree = ET.parse(str(filepath))
            root = tree.getroot()

            data = FlowchartData()
            data.version = root.get("version", "1.0")

            # Загружаем узлы
            nodes_elem = root.find("nodes")
            if nodes_elem is not None:
                for node_elem in nodes_elem.findall("node"):
                    node = SerializedNode(
                        id=node_elem.get("id", str(uuid.uuid4())),
                        type=node_elem.get("type", "rect"),
                        node_type=node_elem.get("node_type", "flow_item"),
                        x=float(node_elem.findtext("x", "0")),
                        y=float(node_elem.findtext("y", "0")),
                        width=float(node_elem.findtext("width", "140")),
                        height=float(node_elem.findtext("height", "70")),
                        text=node_elem.findtext("text", "")
                    )
                    data.nodes.append(node)

            # Загружаем линии
            lines_elem = root.find("lines")
            if lines_elem is not None:
                for line_elem in lines_elem.findall("line"):
                    line = SerializedLine(
                        id=line_elem.get("id", str(uuid.uuid4())),
                        type=line_elem.get("type", "arrow_line"),
                        node_type=line_elem.get("node_type", "line"),
                        x1=float(line_elem.findtext("x1", "0")),
                        y1=float(line_elem.findtext("y1", "0")),
                        x2=float(line_elem.findtext("x2", "0")),
                        y2=float(line_elem.findtext("y2", "0"))
                    )
                    data.lines.append(line)

            return data

        except Exception as e:
            print(f"Ошибка загрузки XML: {e}")
            return None

    @staticmethod
    def export_from_scene(scene, filepath: str | Path) -> bool:
        """
        Экспортирует текущую сцену в XML.

        Args:
            scene: QGraphicsScene с элементами
            filepath: Путь для сохранения

        Returns:
            bool: Успешность операции
        """
        from flow_items import FlowItem
        from line_items import BaseLineItem

        data = FlowchartData()

        for item in scene.items():
            if isinstance(item, FlowItem):
                node = SerializedNode(
                    id=item.item_id if hasattr(item, 'item_id') else str(uuid.uuid4()),
                    type=item.get_type(),
                    x=item.scenePos().x(),
                    y=item.scenePos().y(),
                    width=item.get_width(),
                    height=item.get_height(),
                    text=item.get_text()
                )
                data.nodes.append(node)

            elif isinstance(item, BaseLineItem):
                line = SerializedLine(
                    id=item.line_id if hasattr(item, 'line_id') else str(uuid.uuid4()),
                    type=item.get_line_type(),
                    x1=item.p1().x(),
                    y1=item.p1().y(),
                    x2=item.p2().x(),
                    y2=item.p2().y()
                )
                data.lines.append(line)

        return XMLManager.save_to_xml(data, filepath)

    @staticmethod
    def import_to_scene(scene, filepath: str | Path) -> bool:
        """
        Импортирует данные из XML в сцену.

        Args:
            scene: QGraphicsScene для заполнения
            filepath: Путь к XML-файлу

        Returns:
            bool: Успешность операции
        """
        from flow_items import FlowItem
        from line_items import BaseLineItem

        data = XMLManager.load_from_xml(filepath)
        if not data:
            return False

        # Очищаем сцену
        scene.clear()

        # Восстанавливаем узлы
        for node in data.nodes:
            item = FlowItem(
                node.type,
                node.x,
                node.y,
                node.width,
                node.height
            )
            item.set_text(node.text)
            if hasattr(item, 'item_id'):
                item.item_id = node.id
            scene.addItem(item)

        # Восстанавливаем линии
        for line_data in data.lines:
            line = BaseLineItem(
                QPointF(line_data.x1, line_data.y1),
                QPointF(line_data.x2, line_data.y2),
                line_data.type
            )
            if hasattr(line, 'line_id'):
                line.line_id = line_data.id
            scene.addItem(line)

        return True