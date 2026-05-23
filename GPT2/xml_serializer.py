from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QGraphicsScene

from flowchart_items import FlowchartItem
from line_items import ArrowLine, BaseLine, DashedLine


def scene_to_xml(scene: QGraphicsScene) -> str:
    root = ET.Element("flowchart")
    items_el = ET.SubElement(root, "items")
    lines_el = ET.SubElement(root, "lines")
    for item in scene.items():
        if isinstance(item, FlowchartItem):
            attrs = item.serialize()
            ET.SubElement(items_el, "item", {k: str(v) for k, v in attrs.items()})
        elif isinstance(item, BaseLine):
            attrs = item.serialize()
            ET.SubElement(lines_el, "line", {k: str(v) for k, v in attrs.items()})
    return ET.tostring(root, encoding="unicode")


def save_scene_to_xml(scene: QGraphicsScene, filepath: str) -> None:
    Path(filepath).write_text(scene_to_xml(scene), encoding="utf-8")


def load_scene_from_xml(scene: QGraphicsScene, filepath: str) -> None:
    tree = ET.parse(filepath)
    root = tree.getroot()
    scene.clear()
    items_map: dict[int, FlowchartItem] = {}
    items_el = root.find("items")
    if items_el is not None:
        for item_el in items_el.findall("item"):
            item = FlowchartItem(
                item_el.get("text", ""),
                item_el.get("shape", "process"),
                int(float(item_el.get("w", "140"))),
                int(float(item_el.get("h", "70"))),
            )
            item.item_id = int(item_el.get("id", "0"))
            item.setPos(float(item_el.get("x", "0")), float(item_el.get("y", "0")))
            scene.addItem(item)
            items_map[item.item_id] = item
    lines_el = root.find("lines")
    if lines_el is not None:
        for line_el in lines_el.findall("line"):
            src = items_map.get(int(line_el.get("source_id", "0")))
            dst = items_map.get(int(line_el.get("target_id", "0")))
            if not src or not dst:
                continue
            label = line_el.get("label", "")
            back = line_el.get("is_back_edge", "False") == "True"
            line_type = line_el.get("type", "ArrowLine")
            if line_type == "DashedLine":
                line = DashedLine(src, dst, label, back)
            elif line_type == "SimpleLine":
                line = DashedLine(src, dst, label, back)
            else:
                line = ArrowLine(src, dst, label, back)
            scene.addItem(line)
            line.update_from_items()

