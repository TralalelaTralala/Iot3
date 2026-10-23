# IoT 3.1 - мультипротокольна метеостанція

Навчальний проєкт об'єднує MQTT для телеметрії, HTTP REST для вебпанелі та BLE GATT для локального читання й налаштування. Є два варіанти запуску:

1. **Емулятор для ПК** - Python генерує показання датчиків, публікує MQTT і піднімає REST-дашборд. BLE GATT-профіль можна перевірити через API навіть на комп'ютері без Bluetooth-адаптера.
2. **Прошивка ESP32** - `firmware/` містить реальний клієнт MQTT, REST-сервер та BLE GATT peripheral із PIN-сполученням. Для фізичного радіозв'язку потрібні ESP32, BLE-адаптер на телефоні та сенсори.

Емулятор не видає програмні значення за реальні вимірювання. MQ-135 показує навчальний індекс із аналогового сигналу; для реального AQI/ppm потрібні калібрування та газова модель. Анемометр у комплекті замінено потенціометром.

## Швидкий запуск Python-емулятора (Windows)

Потрібні Python 3.10+ та MQTT-брокер Mosquitto на `127.0.0.1:1883`. Якщо локальний брокер не запущений, REST-дашборд працюватиме, а MQTT автоматично повторюватиме підключення.

1. Запустіть `start.bat` подвійним клацанням або в PowerShell.
2. Відкрийте <http://127.0.0.1:5000/>.
3. Перевірте API на <http://127.0.0.1:5000/api/docs>.
4. Зупинка - `Ctrl+C` у вікні консолі.

Перший запуск створює `.venv`, встановлює Flask і Paho MQTT, а з `config.example.json` створює `config.json`. Передавання даних через MQTT не потребує зовнішнього доступу до Інтернету.

## MQTT

Корінь топіків `weather_station/`. Кожне сенсорне повідомлення — JSON з `device_id`, `location`, `timestamp`, `sequence`, значенням, одиницею та станом датчика. Телеметрія має QoS 1 і retain; online/battery/diagnostics — retain; heartbeat публікується без retain. Last Will публікує `status/online=false`; при відновленні з'єднання стан стає `true`. Перепідключення збільшує затримку від 1 до 30 секунд. Keepalive — 30 секунд.

Топіки команд: `weather_station/config/interval`, `weather_station/config/location`, `weather_station/config/calibration` або JSON команда в `weather_station/commands/config`.

```json
{"interval_seconds": 5, "location": "Аудиторія 12", "calibration": {"temperature": 0.3}}
```

Конфігурація валідується спільним шаром моделі. Допустимий інтервал вимірювання: 1–60 секунд.

## REST API та вебпанель

| Метод і шлях | Призначення |
|---|---|
| `GET /api/sensors` | Усі останні показання |
| `GET /api/sensors/{type}` | Одне показання: `temperature`, `humidity`, `pressure`, `light`, `air_quality`, `wind_speed` |
| `GET /api/history?minutes=60` | Історія сенсорів за останню годину |
| `POST /api/config` | Зміна місця, інтервалу, корекції калібрування |
| `GET /api/status` | Uptime і стани HTTP, MQTT, BLE профілю |
| `GET /api/diagnostics` | Самодіагностика сенсорів, offsets, кількість вимірювань |
| `GET /api/ble/profile` | UUID та властивості GATT |
| `GET /api/docs` | OpenAPI JSON, побудований із маршрутів Flask |

Для API увімкнено CORS і простий ліміт 60 запитів за хвилину на IP. Емулятор зберігає до 3 600 останніх зразків у пам'яті, тож довжина фактичного часового вікна залежить від інтервалу вимірювання. ESP32 записує одну точку за хвилину й показує до години історії. До прикладу конфігурації застосовується `Content-Type: application/json`.

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/sensors
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/config -ContentType 'application/json' -Body '{"interval_seconds":5,"location":"Аудиторія 12"}'
```

## BLE GATT

- Environmental Sensing Service `181A`: температура `2A6E`, вологість `2A6F`, тиск `2A6D`; значення read/notify.
- Власна Configuration Service `7a1b0001-3f4d-4c82-9b67-0f12a58c0001`: інтервал, локація, offsets калібрування; read/write.
- Власна Diagnostic Service `7a1b0002-3f4d-4c82-9b67-0f12a58c0002`: JSON self-test; read/notify.
- Освітлення, AQI та вітер мають власні UUID в Environmental Sensing Service.
- Прошивка вимагає bonding, MITM та LE Secure Connections; демонстраційний PIN `123456` друкується в Serial Monitor. Змініть його перед реальним використанням.

У настільному емуляторі HTTP-маршрути `/api/ble/read/...` і `/api/ble/write/...` відтворюють GATT-читалку/запис для тестів; це **не Bluetooth-радіозв'язок**. Справжня реклама та захищене сполучення реалізовані у прошивці ESP32.

## Прошивка і підключення

Для збірки потрібні PlatformIO Core/VS Code та плата ESP32 DevKit. Підключіть BME280 і BH1750 до I²C (SDA 21, SCL 22, 3.3 V). MQ-135 AOUT підключається до ADC GPIO34; якщо модуль видає до 5 V, використайте дільник напруги до безпечного рівня ADC ESP32. Потенціометр: крайні виводи до 3.3 V/GND, повзунок до GPIO35. Земля має бути спільною.

1. Скопіюйте `firmware/include/secrets.example.h` як `firmware/include/secrets.h` і впишіть Wi-Fi та адресу MQTT-брокера, доступну з мережі ESP32.
2. У папці `firmware/` виконайте `pio run`.
3. Прошийте firmware: `pio run -t upload`.
4. Завантажте вебфайли LittleFS: `pio run -t uploadfs`.
5. Відкрийте Serial Monitor (`pio device monitor`), прочитайте IP пристрою та PIN, потім відкрийте IP у браузері.
6. У nRF Connect проскануйте `WeatherStation-IoT`, під'єднайтеся й введіть PIN із Serial Monitor для secure pairing.

Під час навчальної демонстрації використовуйте приватну локальну мережу. Демонстраційний PIN і MQTT без TLS/пароля не підходять для production.

## Перевірки та звіт

- `python -m unittest discover -s tests -v` - REST, валідація, CORS, OpenAPI і GATT-профіль.
- `python tests/check_mqtt.py` - перевірка publish/subscribe та QoS/retain проти локального Mosquitto.
- `report/practice_03_1_report.pdf` - звіт українською з архітектурою, таблицею протоколів, тестуванням і обмеженнями симуляції.
- `iot3_project.zip` - повний код Python-емулятора, прошивки ESP32, панелі й тестів.


