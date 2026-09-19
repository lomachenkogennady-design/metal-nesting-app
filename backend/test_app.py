from app.nesting import calculate_sheet_nesting

def test_nesting_logic():
    sheet = {"width": 2500, "height": 1250}
    parts = [
        {"id": "Кронштейн", "width": 400, "height": 300, "quantity": 4},
        {"id": "Фланец", "width": 200, "height": 200, "quantity": 10}
    ]
    cost_config = {"price_per_sheet": 5000, "price_per_meter_cut": 50}
    
    data = calculate_sheet_nesting(sheet, parts, gap=0.8, cost_config=cost_config)
    
    assert "total_sheets" in data
    assert "cost" in data
    assert "sheets" in data
    assert data["total_sheets"] > 0
    assert data["cost"]["total"] > 0
    
    print(f"✅ Расчет геометрии и раскроя успешен!")
    print(f"   - Листов использовано: {data['total_sheets']}")
    print(f"   - Общая длина реза: {data['total_cut_meters']} м")
    print(f"   - Металл: {data['cost']['metal']} руб.")
    print(f"   - Резка: {data['cost']['cutting']} руб.")
    print(f"   - Общая стоимость: {data['cost']['total']} руб.")

if __name__ == "__main__":
    print("--- ЗАПУСК ПРОВЕРКИ АЛГОРИТМА ---")
    try:
        test_nesting_logic()
        print("🎉 ВСЕ ПРОВЕРКИ УСПЕШНО ПРОЙДЕНЫ!")
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        exit(1)
