import barcode
from barcode.writer import ImageWriter
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from PIL import Image
import io

# ==== Настройки ====sudo apt-get install python3-venv

template_pdf = "template.pdf"
output_pdf = "barcodes_40_4.pdf"
x_pos_mm = 220
y_pos_mm = 62

start_number = 40100000000237
end_number = 40100000000286

# ==== Параметры writer ====
writer_options = {
    "font_size": 6,  # уменьшенный шрифт подписи
    "text_distance": 3.5,  # расстояние от штрихкода до текста
    "module_height": 15.0,  # высота штрихов (оставим как есть)
    "module_width": 0.2  # ширина штриха
}

# ==== Генерация ====
template = PdfReader(template_pdf)
writer = PdfWriter()

for num in range(start_number, end_number + 1):
    code = str(num).zfill(14)

    # Генерация штрихкода с параметрами
    code128 = barcode.get('code128', code, writer=ImageWriter())
    barcode_buffer = io.BytesIO()
    code128.write(barcode_buffer, options=writer_options)
    barcode_buffer.seek(0)
    img = Image.open(barcode_buffer)

    # Создание PDF с картинкой
    overlay_buffer = io.BytesIO()
    c = canvas.Canvas(overlay_buffer, pagesize=landscape(A4))
    c.drawInlineImage(img, x_pos_mm * mm, y_pos_mm * mm, width=60 * mm, height=29 * mm)
    c.save()
    overlay_buffer.seek(0)

    # Наложение на шаблон
    overlay_pdf = PdfReader(overlay_buffer)
    page = template.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

# Сохраняем результат
with open(output_pdf, "wb") as f:
    writer.write(f)

print(f" Готово! Файл сохранён: {output_pdf}")
