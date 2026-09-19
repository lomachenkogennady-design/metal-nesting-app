import io
import math
import traceback
import ezdxf
from ezdxf import recover
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List
import rectpack

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

class SheetConfig(BaseModel):
    width: float
    height: float

class CostConfig(BaseModel):
    price_per_sheet: float
    price_per_meter_cut: float

class PartItem(BaseModel):
    id: str
    width: float
    height: float
    quantity: int

class NestRequest(BaseModel):
    sheet: SheetConfig
    gap: float = 0.8
    cost_config: CostConfig
    parts: List[PartItem]

@app.post("/api/v1/import/dxf")
async def import_dxf(file: UploadFile = File(...)):
    try:
        content_bytes = await file.read()
        stream = io.BytesIO(content_bytes)
        
        try:
            doc, auditor = recover.read(stream)
        except Exception:
            stream.seek(0)
            doc = ezdxf.read(stream)

        parts = []
        msp = doc.modelspace()
        
        entities = list(msp.query('LWPOLYLINE'))
        if not entities:
            entities = list(msp.query('LINE'))

        for entity in entities:
            try:
                etype = entity.dxftype()
                points = []
                
                if etype == "LWPOLYLINE":
                    raw_points = entity.get_points()
                    if not raw_points:
                        continue
                    points = [p[:2] for p in raw_points]
                elif etype == "LINE":
                    start = entity.dxf.start
                    end = entity.dxf.end
                    points = [start[:2], end[:2]]
                
                if len(points) < 2:
                    continue
                
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                
                if not xs or not ys:
                    continue

                w = max(xs) - min(xs)
                h = max(ys) - min(ys)
                
                if w < 5 or h < 5 or w <= 0 or h <= 0:
                    continue

                layer_name = str(entity.dxf.get("layer", "Деталь"))
                part_id = f"{layer_name} ({round(w)}x{round(h)})"
                
                parts.append({
                    "id": part_id,
                    "width": round(w, 1),
                    "height": round(h, 1),
                    "quantity": 1
                })
            except Exception:
                continue

        if not parts:
            parts.append({"id": "Деталь из DXF", "width": 400.0, "height": 300.0, "quantity": 1})

        return {"status": "success", "parts": parts}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Не удалось обработать DXF: {str(e)}"}
        )

@app.post("/api/v1/nest")
async def nest_parts(payload: NestRequest):
    try:
        if not payload.parts:
            return {
                "total_sheets": 0,
                "cost": {"metal": 0, "cutting": 0, "total": 0},
                "sheets": []
            }

        sheet_w = int(payload.sheet.width)
        sheet_h = int(payload.sheet.height)
        
        import rectpack
        packer = rectpack.newPacker(mode=rectpack.PackingMode.Offline)
        
        for part in payload.parts:
            w = int(part.width)
            h = int(part.height)
            qty = part.quantity
            for i in range(qty):
                packer.add_rect(w, h, rid=f"{part.id}_{i}")
        
        for _ in range(50):
            packer.add_bin(sheet_w, sheet_h)
            
        packer.pack()

        results = packer.rect_list()
        
        sheets_data = {}
        total_cut_length_m = 0.0
        
        for b, x, y, w, h, rid in results:
            if b not in sheets_data:
                sheets_data[b] = {
                    "sheet_number": b + 1,
                    "details": [],
                    "utilization_percentage": 0,
                    "svg": ""
                }
            
            clean_id = str(rid).rsplit('_', 1)[0]
            perimeter_mm = 2 * (w + h)
            total_cut_length_m += perimeter_mm / 1000.0
            
            sheets_data[b]["details"].append({
                "id": clean_id,
                "x": x,
                "y": y,
                "width": w,
                "height": h
            })

        sheets_response = []
        for b, data in sheets_data.items():
            sheet_area = sheet_w * sheet_h
            used_area = sum(d["width"] * d["height"] for d in data["details"])
            utilization = (used_area / sheet_area) * 100 if sheet_area > 0 else 0
            
            svg_parts = ""
            for d in data["details"]:
                svg_parts += f'<rect x="{d["x"]}" y="{d["y"]}" width="{d["width"]}" height="{d["height"]}" fill="#313244" stroke="#a6e3a1" stroke-width="2" rx="2"/>\n'
                svg_parts += f'<text x="{d["x"]+5}" y="{d["y"]+15}" fill="#a6e3a1" font-size="12">{d["id"]}</text>\n'

            svg_content = f"""<svg width="100%" height="100%" viewBox="0 0 {sheet_w} {sheet_h}" style="background:#11111b; border: 1px solid #3b82f6;">
                <rect x="0" y="0" width="{sheet_w}" height="{sheet_h}" fill="none" stroke="#3b82f6" stroke-width="4"/>
                <text x="20" y="30" fill="#89b4fa" font-size="20" font-weight="bold">Лист {data["sheet_number"]} ({sheet_w}x{sheet_h} мм)</text>
                <text x="20" y="60" fill="#a6adc8" font-size="14">Заполнение: {utilization:.1f}%</text>
                {svg_parts}
            </svg>"""

            data["utilization_percentage"] = round(utilization, 2)
            data["svg"] = svg_content
            sheets_response.append(data)

        total_sheets = len(sheets_response)
        metal_cost = total_sheets * payload.cost_config.price_per_sheet
        cutting_cost = total_cut_length_m * payload.cost_config.price_per_meter_cut
        total_cost = metal_cost + cutting_cost

        return {
            "total_sheets": total_sheets,
            "cost": {
                "metal": round(metal_cost, 2),
                "cutting": round(cutting_cost, 2),
                "total": round(total_cost, 2)
            },
            "sheets": sheets_response
        }

    except Exception as e:
        print(f"Nesting Error (Terminal): {e}")
        return JSONResponse(
            status_code=500,
            content={
                "total_sheets": 0,
                "cost": {"metal": 0, "cutting": 0, "total": 0},
                "sheets": [],
                "error": str(e)
            }
        )

@app.post("/api/v1/export/dxf")
async def export_dxf(payload: NestRequest):
    try:
        if not payload.parts:
            raise HTTPException(status_code=400, detail="Нет деталей для экспорта")

        sheet_w = int(payload.sheet.width)
        sheet_h = int(payload.sheet.height)
        
        import rectpack
        packer = rectpack.newPacker(mode=rectpack.PackingMode.Offline)
        
        for part in payload.parts:
            w = int(part.width)
            h = int(part.height)
            qty = part.quantity
            for i in range(qty):
                packer.add_rect(w, h, rid=f"{part.id}_{i}")
        
        for _ in range(50):
            packer.add_bin(sheet_w, sheet_h)
            
        packer.pack()
        results = packer.rect_list()
        
        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()
        
        sheets_data = {}
        for b, x, y, w, h, rid in results:
            if b not in sheets_data:
                sheets_data[b] = []
            clean_id = str(rid).rsplit('_', 1)[0]
            sheets_data[b].append((x, y, w, h, clean_id))
        
        sheet_offset_x = sheet_w + 300  # Смещение между листами в DXF
        
        for b, details in sheets_data.items():
            current_offsetX = b * sheet_offset_x
            
            # Контур листа
            msp.add_lwpolyline([
                (current_offsetX, 0),
                (current_offsetX + sheet_w, 0),
                (current_offsetX + sheet_w, sheet_h),
                (current_offsetX, sheet_h)
            ], close=True, dxfattribs={'layer': f'Лист_{b+1}', 'color': 1})
            
            # Текст с номером листа
            msp.add_text(
                f"Лист {b+1} ({sheet_w}x{sheet_h} мм)",
                dxfattribs={'layer': f'Лист_{b+1}', 'height': 25}
            ).set_placement((current_offsetX + 20, sheet_h + 40))
            
            # Детали на листе
            for x, y, w, h, pid in details:
                abs_x = current_offsetX + x
                abs_y = y
                msp.add_lwpolyline([
                    (abs_x, abs_y),
                    (abs_x + w, abs_y),
                    (abs_x + w, abs_y + h),
                    (abs_x, abs_y + h)
                ], close=True, dxfattribs={'layer': 'Детали_Раскроя', 'color': 3})
                
                msp.add_text(
                    pid,
                    dxfattribs={'layer': 'Маркировка', 'height': 12, 'color': 7}
                ).set_placement((abs_x + 10, abs_y + 10))

        output = io.StringIO()
        doc.write(output)
        dxf_data = output.getvalue().encode('utf-8')
        
        return StreamingResponse(
            io.BytesIO(dxf_data),
            media_type="application/dxf",
            headers={"Content-Disposition": "attachment; filename=nesting_result.dxf"}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Ошибка экспорта DXF: {str(e)}"}
        )
