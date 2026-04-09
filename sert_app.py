import os
import io
from copy import deepcopy

# noinspection PyPackageRequirements
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QFileDialog, QVBoxLayout, QMessageBox
)

import barcode
from barcode.writer import ImageWriter
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from PIL import Image

import logging
import sys

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

log_path = os.path.join(get_app_dir(), "error.log")

logging.basicConfig(
    filename=log_path,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def generate_barcodes(
    template_pdf,
    output_name,
    start_number,
    end_number,
    batch_size,
    output_dir
):
    writer_options = {
        "font_size": 6,
        "text_distance": 3.5,
        "module_height": 15.0,
        "module_width": 0.2
    }

    template = PdfReader(template_pdf)

    x_pos_mm = 220
    y_pos_mm = 62

    current_batch = 1
    counter = 0
    writer = PdfWriter()

    os.makedirs(output_dir, exist_ok=True)

    base_name, ext = os.path.splitext(output_name)

    batch_start = start_number

    for num in range(start_number, end_number + 1):
        code = str(num).zfill(14)

        code128 = barcode.get('code128', code, writer=ImageWriter())
        barcode_buffer = io.BytesIO()
        code128.write(barcode_buffer, options=writer_options)
        barcode_buffer.seek(0)
        img = Image.open(barcode_buffer)

        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=landscape(A4))
        c.drawInlineImage(img, x_pos_mm * mm, y_pos_mm * mm,
                          width=60 * mm, height=29 * mm)
        c.save()
        overlay_buffer.seek(0)

        overlay_pdf = PdfReader(overlay_buffer)

        page = deepcopy(template.pages[0])
        page.merge_page(overlay_pdf.pages[0])
        writer.add_page(page)

        counter += 1

        if counter == batch_size:
            batch_end = num

            filename = f"{base_name}_{current_batch}_{batch_start}-{batch_end}{ext}"
            output_path = os.path.join(output_dir, filename)

            with open(output_path, "wb") as f:
                writer.write(f)

            writer = PdfWriter()
            current_batch += 1
            counter = 0
            batch_start = num + 1

    # остаток
    if counter > 0:
        batch_end = end_number

        filename = f"{base_name}_{current_batch}_{batch_start}-{batch_end}{ext}"
        output_path = os.path.join(output_dir, filename)

        with open(output_path, "wb") as f:
            writer.write(f)

def is_valid_pdf(path):
    if not os.path.isfile(path):
        return False
    if not path.lower().endswith(".pdf"):
        return False
    try:
        PdfReader(path)
        return True
    except:
        return False

def is_valid_number(value):
    return value.isdigit() and len(value) == 14


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор штрихкодов")
        self.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout()

        # PDF
        self.label_pdf = QLabel("Шаблон PDF:")
        self.input_pdf = QLineEdit()
        self.btn_pdf = QPushButton("Выбрать PDF")
        self.btn_pdf.clicked.connect(self.select_pdf)

        # папка
        self.label_dir = QLabel("Папка сохранения:")
        self.input_dir = QLineEdit()
        self.btn_dir = QPushButton("Выбрать папку")
        self.btn_dir.clicked.connect(self.select_dir)

        # диапазон
        self.label_start = QLabel("Начальный номер:")
        self.input_start = QLineEdit()

        self.label_end = QLabel("Конечный номер:")
        self.input_end = QLineEdit()

        # имя файла
        self.label_output = QLabel("Имя выходного файла:")
        self.input_output = QLineEdit()
        self.input_output.setPlaceholderText("result.pdf")

        # batch
        self.label_batch = QLabel("Размер пачки (по умолчанию 50):")
        self.input_batch = QLineEdit()
        self.input_batch.setPlaceholderText("50")

        # кнопка
        self.btn_run = QPushButton("🚀 Запустить")
        self.btn_run.clicked.connect(self.run)

        self.status = QLabel("")

        # layout
        layout.addWidget(self.label_pdf)
        layout.addWidget(self.input_pdf)
        layout.addWidget(self.btn_pdf)

        layout.addWidget(self.label_dir)
        layout.addWidget(self.input_dir)
        layout.addWidget(self.btn_dir)

        layout.addWidget(self.label_start)
        layout.addWidget(self.input_start)

        layout.addWidget(self.label_end)
        layout.addWidget(self.input_end)

        layout.addWidget(self.label_output)
        layout.addWidget(self.input_output)

        layout.addWidget(self.label_batch)
        layout.addWidget(self.input_batch)

        layout.addWidget(self.btn_run)
        layout.addWidget(self.status)

        self.setLayout(layout)

    def select_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать PDF", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.input_pdf.setText(file_path)

    def select_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Выбрать папку")
        if folder:
            self.input_dir.setText(folder)

    def run(self):
        template = self.input_pdf.text()
        start = self.input_start.text()
        end = self.input_end.text()
        output = self.input_output.text()
        if not output.lower().endswith(".pdf"):
            output += ".pdf"
        output_dir = self.input_dir.text()
        batch = self.input_batch.text()

        # проверка PDF
        if not is_valid_pdf(template):
            logging.error("Неправильный шаблон")
            QMessageBox.critical(self, "Ошибка", "Выбранный файл не является корректным PDF")
            return

        # проверка чисел
        if not is_valid_number(start) or not is_valid_number(end):
            logging.error("Неправильное кольчество символов")
            QMessageBox.critical(self, "Ошибка", "Номера должны состоять ровно из 14 цифр")
            return

        if start > end:
            logging.error("Начальный номер больше конечного")
            QMessageBox.critical(self, "Ошибка", "Начальный номер больше конечного")
            return

        if not template or not start or not end or not output:
            QMessageBox.warning(self, "Ошибка", "Заполните поле НОМЕР!")
            return

        if not output_dir:
            QMessageBox.warning(self, "Ошибка", "Выберите папку сохранения")
            return

        try:
            start = int(start)
            end = int(end)
        except:
            QMessageBox.critical(self, "Ошибка", "Номера должны быть числами")
            return

        if batch:
            try:
                batch = int(batch)
            except:
                QMessageBox.critical(self, "Ошибка", "Размер пачки должен быть числом")
                return
        else:
            batch = 50

        try:
            self.status.setText("Обработка...")
            QApplication.processEvents()

            generate_barcodes(template, output, start, end, batch, output_dir)

            self.status.setText("Готово")
            QMessageBox.information(self, "Успех", "Файлы созданы")


        except Exception as e:

            self.status.setText("Ошибка")

            logging.exception("Ошибка при генерации")

            QMessageBox.critical(self, "Ошибка", str(e))


if __name__ == "__main__":
    app = QApplication([])
    window = App()
    window.show()
    app.exec()