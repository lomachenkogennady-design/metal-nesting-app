from app.nesting import MultiSheetPacker

def test():
    # Создаем упаковщик для листа 2500x1250 с зазором 1 мм
    packer = MultiSheetPacker(2500, 1250, gap=1.0)
    
    # Тестовые детали
    parts = [
        {"id": "Flanec A", "width": 600, "height": 400, "quantity": 4}
    ]
    
    result = packer.pack(parts)
    print("Результат раскроя:", result)

if __name__ == "__main__":
    test()
