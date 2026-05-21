from lxml import etree

from flowchart_items import FlowchartItem
from line_items import ArrowLine, SimpleLine, DashedLine


class XMLSerializer:
    @staticmethod
    def save_scene(scene, filename):
        root = etree.Element("flowchart")

        items_xml = etree.SubElement(root, "items")
        lines_xml = etree.SubElement(root, "lines")

        for item in scene.items():
            if isinstance(item, FlowchartItem):
                item_data = item.serialize()

                item_xml = etree.SubElement(items_xml, "item")

                for key, value in item_data.items():
                    item_xml.set(key, str(value))

        for item in scene.items():
            if isinstance(item, (ArrowLine, SimpleLine, DashedLine)):
                line_data = item.serialize()

                line_xml = etree.SubElement(lines_xml, "line")

                for key, value in line_data.items():
                    line_xml.set(key, str(value))

        tree = etree.ElementTree(root)

        tree.write(
            filename,
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8"
        )

    @staticmethod
    def load_scene(scene, filename):
        scene.clear()

        tree = etree.parse(filename)
        root = tree.getroot()

        item_map = {}

        for item_xml in root.find("items"):
            item = FlowchartItem(
                item_xml.get("shape"),
                item_xml.get("text")
            )

            item.item_id = item_xml.get("id")
            item.width = float(item_xml.get("width"))
            item.height = float(item_xml.get("height"))

            item.setPos(
                float(item_xml.get("x")),
                float(item_xml.get("y"))
            )

            item.update_handles()

            scene.addItem(item)
            item_map[item.item_id] = item

        for line_xml in root.find("lines"):
            start = item_map.get(line_xml.get("start_id"))
            end = item_map.get(line_xml.get("end_id"))

            if not start or not end:
                continue

            line_type = line_xml.get("type")

            if line_type == "ArrowLine":
                line = ArrowLine(start, end)
            elif line_type == "DashedLine":
                line = DashedLine(start, end)
            else:
                line = SimpleLine(start, end)

            scene.addItem(line)