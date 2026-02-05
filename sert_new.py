import barcode
from barcode.writer import ImageWriter
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from PIL import Image
import io
from copy import deepcopy

# ==== Настройки ====#
template_pdf = "сертификат_25_les.pdf"
output_name_pattern = "barcodes_25_les_{}.pdf"  # {} будет номер пачки
x_pos_mm = 220
y_pos_mm = 62

start_number = 10250000001052
end_number = 10250000001262

batch_size = 50  # <--- создаём отдельный файл каждые 50 шт.

# ==== Параметры штрихкода ====
writer_options = {
    "font_size": 6,
    "text_distance": 3.5,
    "module_height": 15.0,
    "module_width": 0.2
}

template = PdfReader(template_pdf)

current_batch = 1   # Начальный номер пачки
counter = 0
writer = PdfWriter()

for num in range(start_number, end_number + 1):
    code = str(num).zfill(14)

    # Генерация изображения штрихкода
    code128 = barcode.get('code128', code, writer=ImageWriter())
    barcode_buffer = io.BytesIO()
    code128.write(barcode_buffer, options=writer_options)
    barcode_buffer.seek(0)
    img = Image.open(barcode_buffer)

    # Создаем PDF-вставку
    overlay_buffer = io.BytesIO()
    c = canvas.Canvas(overlay_buffer, pagesize=landscape(A4))
    c.drawInlineImage(img, x_pos_mm * mm, y_pos_mm * mm, width=60 * mm, height=29 * mm)
    c.save()
    overlay_buffer.seek(0)

    overlay_pdf = PdfReader(overlay_buffer)

    # ВАЖНО: копируем оригинальную страницу, чтобы не портить исходник
    page = deepcopy(template.pages[0])
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

    counter += 1

    # Если пачка заполнилась — сохраняем файл
    if counter == batch_size:
        output_pdf = output_name_pattern.format(current_batch)
        with open(output_pdf, "wb") as f:
            writer.write(f)

        print(f"✅ Сохранён файл: {output_pdf}")

        # Начинаем новую пачку
        writer = PdfWriter()
        current_batch += 1
        counter = 0

# Сохраняем остаток (если не делится ровно)
if counter > 0:
    output_pdf = output_name_pattern.format(current_batch)
    with open(output_pdf, "wb") as f:
        writer.write(f)
    print(f"✅ Сохранён файл: {output_pdf}")

print("🎉 Готово!")
