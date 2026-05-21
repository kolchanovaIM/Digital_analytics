from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainter, QImage
from PyQt6.QtPrintSupport import QPrinter


def export_scene_to_png(scene, filename):
    rect = scene.itemsBoundingRect()

    image = QImage(
        int(rect.width()) + 50,
        int(rect.height()) + 50,
        QImage.Format.Format_ARGB32
    )

    image.fill(0xFFFFFFFF)

    painter = QPainter(image)
    scene.render(painter, QRectF(), rect)
    painter.end()

    image.save(filename)


def export_scene_to_pdf(scene, filename):
    printer = QPrinter()

    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(filename)

    painter = QPainter(printer)

    rect = scene.itemsBoundingRect()
    scene.render(painter, QRectF(), rect)

    painter.end()