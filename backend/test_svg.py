import requests

url = "http://127.0.0.1:8000/api/v1/nest/svg"

payload = {
    "sheet": {
        "width": 1000,
        "height": 1000
    },
    "parts": [
        {"id": "Plate_A", "width": 400, "height": 300, "quantity": 3},
        {"id": "Plate_B", "width": 500, "height": 200, "quantity": 2},
        {"id": "Square_C", "width": 200, "height": 200, "quantity": 4}
    ]
}

try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        filename = "nesting_result.svg"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"✅ SVG чертеж успешно сгенерирован и сохранен в файл: {filename}")
        print("Размер файла:", len(response.text), "байт")
    else:
        print(f"❌ Ошибка сервера: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
