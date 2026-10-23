from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle, PageBreak, KeepTogether, Image as RLImage)
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "report" / "practice_03_1_report.pdf"
FONT = Path("C:/Windows/Fonts/arial.ttf")
FONT_B = Path("C:/Windows/Fonts/arialbd.ttf")
pdfmetrics.registerFont(TTFont("Arial", str(FONT)))
pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONT_B)))

NAVY = colors.HexColor("#15324A")
TEAL = colors.HexColor("#087E8B")
PALE = colors.HexColor("#EAF3F5")
INK = colors.HexColor("#25313A")
MUTED = colors.HexColor("#5C6A73")
GREEN = colors.HexColor("#247A54")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", fontName="Arial-Bold", fontSize=25, leading=32,
                          textColor=NAVY, alignment=TA_CENTER, spaceAfter=8*mm))
styles.add(ParagraphStyle(name="CoverSub", fontName="Arial", fontSize=15, leading=22,
                          textColor=TEAL, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="H1x", fontName="Arial-Bold", fontSize=17, leading=22,
                          textColor=NAVY, spaceBefore=1*mm, spaceAfter=4*mm, keepWithNext=True))
styles.add(ParagraphStyle(name="H2x", fontName="Arial-Bold", fontSize=11, leading=15,
                          textColor=TEAL, spaceBefore=3*mm, spaceAfter=1.5*mm, keepWithNext=True))
styles.add(ParagraphStyle(name="Bodyx", fontName="Arial", fontSize=9.1, leading=13.2,
                          textColor=INK, spaceAfter=2.3*mm))
styles.add(ParagraphStyle(name="Smallx", fontName="Arial", fontSize=7.8, leading=10.2,
                          textColor=MUTED, spaceAfter=1*mm))
styles.add(ParagraphStyle(name="Cellx", fontName="Arial", fontSize=7.4, leading=9.4,
                          textColor=INK))
styles.add(ParagraphStyle(name="CellHead", fontName="Arial-Bold", fontSize=7.7, leading=9.6,
                          textColor=colors.white))
styles.add(ParagraphStyle(name="Centerx", fontName="Arial", fontSize=9, leading=13,
                          textColor=INK, alignment=TA_CENTER))

def P(text, style="Bodyx"):
    return Paragraph(text, styles[style])

def grid(rows, widths, header=True):
    data = [[P(str(cell), "CellHead" if header and ri == 0 else "Cellx") for cell in row]
            for ri, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#CAD6DA")),
        ("ROWBACKGROUNDS", (0,1 if header else 0), (-1,-1), [colors.white, PALE]),
    ]
    if header:
        commands.append(("BACKGROUND", (0,0), (-1,0), NAVY))
    t.setStyle(TableStyle(commands))
    return t

def on_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, h-8*mm, w, 8*mm, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.rect(0, 0, w, 3*mm, fill=1, stroke=0)
    canvas.setFont("Arial", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(17*mm, 10*mm, "Практична робота 3.1 · IoT-протоколи")
    canvas.drawRightString(w-17*mm, 10*mm, f"Сторінка {doc.page}")
    canvas.restoreState()

doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=17*mm, rightMargin=17*mm,
                      topMargin=17*mm, bottomMargin=17*mm, title="Практична робота 3.1 — IoT-протоколи",
                      author="SnoxJ")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
doc.addPageTemplates([PageTemplate(id="all", frames=frame, onPage=on_page)])
story = []

# Page 1
story += [Spacer(1, 23*mm), P("ПРАКТИЧНА РОБОТА 3.1", "CoverSub"), Spacer(1, 5*mm),
          P("Протоколи обміну даними<br/>в IoT-системах", "CoverTitle"),
          P("Мультипротокольна метеостанція", "CoverSub"), Spacer(1, 13*mm)]
cover = Table([
    [P("Виконавець", "CellHead"), P("SnoxJ", "Cellx")],
    [P("Група", "CellHead"), P("У наданих матеріалах не вказана", "Cellx")],
    [P("Середовище", "CellHead"), P("Python-емулятор · ESP32 firmware · MQTT · HTTP REST · BLE GATT", "Cellx")],
    [P("Дата", "CellHead"), P("23 жовтня 2026 року", "Cellx")],
], colWidths=[37*mm, 125*mm])
cover.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),NAVY), ("BACKGROUND",(1,0),(1,-1),PALE),
                           ("GRID",(0,0),(-1,-1),.5,colors.white), ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                           ("LEFTPADDING",(0,0),(-1,-1),8), ("TOPPADDING",(0,0),(-1,-1),9),
                           ("BOTTOMPADDING",(0,0),(-1,-1),9)]))
story += [cover, Spacer(1, 13*mm), P("Мета роботи", "H2x"),
          P("Побудувати навчальну IoT-систему моніторингу метеоданих, передати телеметрію через MQTT, надати HTTP REST API та вебпанель, а також описати й реалізувати BLE GATT-профіль для читання показань і налаштування станції."),
          P("Завдання", "H2x"),
          P("Реалізувати спільну модель сенсорів і конфігурації; забезпечити MQTT QoS 1, retained-повідомлення, Last Will та повторне підключення; створити REST-маршрути, історію й діагностику; визначити BLE-сервіси та характеристики; перевірити обмін даними й відновлення після втрати з'єднання."),
          PageBreak()]

# Page 2
story += [P("1. Архітектура та протоколи", "H1x"),
          P("Система має два виконання: настільний симулятор для перевірки потоків даних без сенсорів і прошивку ESP32 для фізичного MQTT/HTTP/BLE. В обох випадках компоненти спираються на ті самі назви каналів і структуру телеметрії."),
          grid([["Рівень", "Функція", "Дані / напрямок"],
                ["Датчики", "BME280, BH1750, MQ-135; потенціометр замість анемометра", "Температура, вологість, тиск, світло, навчальний індекс якості повітря, швидкість вітру"],
                ["Модель", "Фільтрація, калібрування, часові мітки, лічильник послідовності", "Єдине актуальне показання та буфер історії"],
                ["MQTT", "Публікація телеметрії та підписка на конфігурацію", "Брокер Mosquitto; QoS 1; retained стан"],
                ["HTTP REST", "Читання, історія, конфігурація, діагностика", "Вебпанель браузера та JSON API"],
                ["BLE GATT", "Локальне читання/сповіщення та запис конфігурації", "Environmental Sensing 181A + власні сервіси"]], [26*mm,63*mm,73*mm]),
          Spacer(1, 4*mm), P("Порівняння протоколів", "H2x"),
          grid([["Критерій", "MQTT", "HTTP REST", "BLE GATT"],
                ["Топологія", "Публікація/підписка через брокер", "Запит-відповідь клієнт-сервер", "Периферійний пристрій і центральний клієнт"],
                ["Основне застосування", "Потокова телеметрія, статус і команди", "Панель, історія, налаштування", "Налаштування/читання поруч зі станцією"],
                ["Надійність", "QoS 1, LWT, повторне з'єднання", "Повторювані запити, код HTTP", "Notify та повторне з'єднання BLE"],
                ["Обмеження", "Потрібен доступ до брокера", "Запити створюють додатковий трафік", "Коротка відстань; потрібне BLE-радіо"]], [25*mm,46*mm,46*mm,45*mm]),
          Spacer(1, 4*mm), P("Потік даних", "H2x")]
diagram = Table([
    [P("Датчики / симулятор", "Centerx"), P("ESP32 або Python", "Centerx"), P("MQTT-брокер", "Centerx"), P("REST-панель", "Centerx")],
    [P("BME280 · BH1750<br/>MQ-135 · вітер", "Smallx"), P("спільна модель<br/>значення + час", "Smallx"), P("weather_station/#", "Smallx"), P("графік · конфігурація<br/>статус · історія", "Smallx")]
], colWidths=[40*mm]*4)
diagram.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),PALE), ("BOX",(0,0),(-1,-1),.8,TEAL),
                             ("INNERGRID",(0,0),(-1,-1),.5,colors.HexColor("#B7CED2")),
                             ("VALIGN",(0,0),(-1,-1),"MIDDLE"), ("TOPPADDING",(0,0),(-1,-1),7),
                             ("BOTTOMPADDING",(0,0),(-1,-1),7)]))
story += [diagram, PageBreak()]

# Page 3
story += [P("2. Реалізація", "H1x"), P("2.1 MQTT", "H2x"),
          P("Корінь топіків — <font name='Arial-Bold'>weather_station/</font>. Канали <font name='Arial-Bold'>sensors/{temperature,humidity,pressure,light,air_quality,wind_speed}</font> містять JSON з device_id, місцем, timestamp, sequence, значенням, одиницею та health. QoS 1 гарантує доставку щонайменше один раз; телеметрія та online/status зберігаються retained. Heartbeat іде без retain. Last Will публікує offline, а після з'єднання стан оновлюється на online. Повторне підключення використовує зростаючу затримку 1–30 с; keepalive — 30 с."),
          P("Команди конфігурації приймаються в <font name='Arial-Bold'>weather_station/config/interval</font>, <font name='Arial-Bold'>config/location</font>, <font name='Arial-Bold'>config/calibration</font> та <font name='Arial-Bold'>commands/config</font>. Інтервал обмежено 1–60 секунд."),
          P("2.2 HTTP REST", "H2x"),
          grid([["Маршрут", "Опис"],
                ["GET /api/sensors", "Поточні показання всіх каналів"],
                ["GET /api/sensors/{type}", "Поточне значення вибраного каналу"],
                ["GET /api/history?minutes=60", "Буфер вимірювань за останню годину (емулятор)"],
                ["POST /api/config", "Місце, інтервал і offsets калібрування"],
                ["GET /api/status · /api/diagnostics", "Стан транспорту, сенсорів і пристрою"],
                ["GET /api/ble/profile · /api/docs", "GATT-опис і OpenAPI-маршрути"]], [58*mm,102*mm]),
          Spacer(1, 2*mm), P("Для API налаштовані CORS і обмеження 60 запитів за хвилину на адресу. Вебпанель відображає актуальні значення, стан протоколів, тренд вимірювань, діагностику та форму конфігурації. Емулятор зберігає до 24 годин даних у пам'яті; прошивка тримає погодинний огляд з одним записом за хвилину."),
          P("2.3 BLE GATT", "H2x"),
          grid([["Сервіс", "Характеристики", "Доступ"],
                ["Environmental Sensing 181A", "Температура 2A6E; вологість 2A6F; тиск 2A6D; власні UUID для світла/AQI/вітру", "Read + Notify"],
                ["Configuration (custom)", "Інтервал; місце; offsets калібрування", "Read + Write"],
                ["Diagnostics (custom)", "JSON самодіагностики", "Read + Notify"]], [38*mm,88*mm,34*mm]),
          P("ESP32 використовує LE Secure Connections, MITM і bonding із демонстраційним PIN 123456, який надходить у Serial Monitor. Перед використанням реальної системи PIN потрібно замінити. HTTP-маршрути /api/ble/read і /api/ble/write в настільній версії лише імітують GATT-профіль; Bluetooth-радіо надає ESP32.", "Smallx"),
          PageBreak()]

# Page 4
story += [P("3. Перевірки, результати й висновки", "H1x"),
          grid([["Перевірка", "Результат", "Підтвердження"],
                ["Знімок датчиків та історія", "PASS", "Усі 6 каналів присутні; історія приймає вимірювання"],
                ["Оновлення конфігурації", "PASS", "Значення збережені; некоректний інтервал відхиляється HTTP 400"],
                ["GATT-профіль і запис інтервалу", "PASS", "181A доступний; конфігураційний запис оновлює модель"],
                ["OpenAPI і CORS", "PASS", "Маршрути сформовані; CORS заголовок присутній"],
                ["MQTT publish/subscribe", "PASS", "Локальний Mosquitto; QoS 1, повідомлення отримане"],
                ["Збірка firmware та радіо BLE", "Не завершено", "Завантаження PlatformIO toolchain зависло; радіоперевірка потребує ESP32"]], [50*mm,25*mm,85*mm]),
          Spacer(1, 4*mm), P("Результати та обмеження", "H2x"),
          P("Автоматичні перевірки API завершилися успішно: 4 з 4. Окрема MQTT-перевірка отримала тестове повідомлення через локальний брокер із QoS 1. Це підтверджує роботу настільного симулятора та брокерного обміну. Збірка прошивки не завершилася, оскільки PlatformIO не закінчив завантаження компілятора; фізичне сполучення BLE та читання сенсорів також потребують ESP32, BME280, BH1750, MQ-135 і BLE-клієнта."),
          P("MQ-135 у прошивці дає навчальний індекс із ADC; це не сертифікований AQI або концентрація газу. Потенціометр замінює анемометр. Напругу AOUT MQ-135 слід перевірити й за потреби знизити дільником до меж входу ADC ESP32. Приклад не використовувати як систему безпеки або для керування небезпечним обладнанням."),
          P("Висновок", "H2x"),
          P("У роботі створено навчальну станцію з трьома протоколами та двома варіантами запуску. MQTT забезпечує подієву телеметрію з брокером і збереженим статусом, HTTP надає зручні запити та панель, а BLE GATT призначений для локального доступу до показань і параметрів. Перевірки Python API та MQTT успішні. Для завершення повного фізичного тесту необхідно прошити ESP32 і перевірити реальну BLE-рекламу та сенсорні модулі."),
          P("Файли проєкту", "H2x"),
          P("Python-емулятор: <font name='Arial-Bold'>weatherstation/</font>; панель: <font name='Arial-Bold'>web/index.html</font>; прошивка та конфігурація PlatformIO: <font name='Arial-Bold'>firmware/</font>; інструкція запуску: <font name='Arial-Bold'>README.md</font>. Демонстрація з фізичною платою залежить від наявності зазначених компонентів."),
          P("Джерела", "H2x"),
          P("1. ArduinoMqttClient — MQTT publish, QoS і Last Will: https://github.com/arduino-libraries/ArduinoMqttClient<br/>2. NimBLE-Arduino — BLE GATT і security API: https://github.com/h2zero/NimBLE-Arduino<br/>3. Adafruit BME280 Library: https://github.com/adafruit/Adafruit_BME280_Library<br/>4. ESP32 Arduino Wi-Fi API: https://docs.espressif.com/projects/arduino-esp32/en/latest/api/wifi.html", "Smallx")]

# Appendix: screenshots from the running IoT 3 dashboard
SHOT_DIR = ROOT / "report" / "screenshots"
def screenshot(name, max_w, max_h):
    path = SHOT_DIR / name
    iw, ih = ImageReader(str(path)).getSize()
    scale = min(max_w / iw, max_h / ih)
    return RLImage(str(path), width=iw * scale, height=ih * scale)

def shot_cell(title, name, max_w, max_h):
    content = [P(title, "Smallx"), screenshot(name, max_w, max_h)]
    cell = Table([[content]], colWidths=[max_w + 3*mm])
    cell.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"),
                              ("LEFTPADDING", (0,0), (-1,-1), 0),
                              ("RIGHTPADDING", (0,0), (-1,-1), 2),
                              ("TOPPADDING", (0,0), (-1,-1), 2),
                              ("BOTTOMPADDING", (0,0), (-1,-1), 2)]))
    return cell

story += [PageBreak(), P("Додаток А. Скріншоти панелі", "H1x"),
          P("Показання оновлюються в реальному часі. На скриншотах зафіксовано роботу локального симулятора та підключення MQTT.", "Bodyx")]
metric_shots = [
    ("Якість повітря (MQ-135)", "air-quality.png"), ("Вологість", "humidity.png"),
    ("Освітленість", "light.png"), ("Атмосферний тиск", "pressure.png"),
    ("Температура", "temperature.png"), ("Швидкість вітру", "wind-speed.png")]
metric_cells = [shot_cell(label, filename, 76*mm, 20*mm) for label, filename in metric_shots]
metric_grid = Table([[metric_cells[i], metric_cells[i+1]] for i in range(0, 6, 2)],
                    colWidths=[81*mm, 81*mm], hAlign="LEFT")
metric_grid.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"),
                                 ("LEFTPADDING", (0,0), (-1,-1), 0),
                                 ("RIGHTPADDING", (0,0), (-1,-1), 2),
                                 ("TOPPADDING", (0,0), (-1,-1), 3),
                                 ("BOTTOMPADDING", (0,0), (-1,-1), 4)]))
story += [metric_grid, Spacer(1, 2*mm), P("Графік показників за останню годину", "H2x"),
          screenshot("trend.png", 165*mm, 58*mm), PageBreak(),
          P("Додаток А. Протоколи та налаштування", "H1x"),
          P("Стан HTTP REST, MQTT і BLE-профілю, сторінки керування станцією та доступні операції API.", "Bodyx")]
protocol_cell = shot_cell("Стан протоколів і діагностика сенсорів", "protocol-status.png", 69*mm, 52*mm)
settings_cell = shot_cell("Налаштування місця, інтервалу й калібрування", "station-settings.png", 83*mm, 44*mm)
ble_cell = shot_cell("BLE GATT: читання характеристики та запис інтервалу", "ble-gatt.png", 58*mm, 73*mm)
api_cell = shot_cell("Таблиця MQTT, HTTP REST, BLE GATT і топіків", "api-mqtt.png", 88*mm, 31*mm)
appendix_grid = Table([[protocol_cell, settings_cell], [ble_cell, ""]],
                      colWidths=[77*mm, 88*mm], hAlign="LEFT")
appendix_grid.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"),
                                    ("LEFTPADDING", (0,0), (-1,-1), 0),
                                    ("RIGHTPADDING", (0,0), (-1,-1), 2),
                                    ("TOPPADDING", (0,0), (-1,-1), 4),
                                    ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
story += [appendix_grid, Spacer(1, 2*mm),
          P("Інтеграція MQTT, HTTP REST і BLE GATT", "H2x"),
          screenshot("api-mqtt.png", 165*mm, 30*mm)]

doc.build(story)
print(OUT)
