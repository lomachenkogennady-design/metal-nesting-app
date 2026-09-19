import io
import ezdxf
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_index():
    print("Testing GET / ...")
    response = client.get("/")
    assert response.status_code == 200
    assert "<html" in response.text.lower()
    print("SUCCESS: GET / returned HTML successfully.")

def test_import_dxf_mock():
    print("Testing POST /api/v1/import/dxf with a generated DXF...")
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (500, 0), (500, 300), (0, 300)], close=True)

    stream = io.StringIO()
    doc.write(stream)
    dxf_bytes = stream.getvalue().encode("utf-8")

    files = {"file": ("test_part.dxf", dxf_bytes, "application/octet-stream")}
    response = client.post("/api/v1/import/dxf", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["parts"]) > 0
    print(f"SUCCESS: DXF import extracted {len(data['parts'])} part(s): {data['parts']}")

def test_nesting_endpoint():
    print("Testing POST /api/v1/nest...")
    payload = {
        "sheet": {
            "width": 2500.0,
            "height": 1250.0
        },
        "gap": 0.8,
        "cost_config": {
            "price_per_sheet": 4500.0,
            "price_per_meter_cut": 65.0
        },
        "parts": [
            {
                "id": "Фланец A",
                "width": 600.0,
                "height": 400.0,
                "quantity": 8
            }
        ]
    }

    response = client.post("/api/v1/nest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "total_sheets" in data
    assert "cost" in data
    assert "sheets" in data
    assert data["cost"]["total"] > 0
    print(f"SUCCESS: Nesting calculation returned total cost: {data['cost']['total']} rub.")

if __name__ == "__main__":
    print("=== STARTING BACKEND AUTOMATED TESTS ===")
    try:
        test_read_index()
        test_import_dxf_mock()
        test_nesting_endpoint()
        print("\nALL TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
