import io
import ezdxf
from ezdxf import recover
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List

from app.nesting import calculate_sheet_nesting

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
        sheet_dict = {"width": payload.sheet.width, "height": payload.sheet.height}
        parts_list = [p.dict() for p in payload.parts]
        cost_dict = {
            "price_per_sheet": payload.cost_config.price_per_sheet,
            "price_per_meter_cut": payload.cost_config.price_per_meter_cut
        }

        result = calculate_sheet_nesting(
            sheet=sheet_dict,
            parts=parts_list,
            gap=payload.gap,
            cost_config=cost_dict
        )
        return result

    except Exception as e:
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

        sheet_dict = {"width": payload.sheet.width, "height": payload.sheet.height}
        parts_list = [p.dict() for p in payload.parts]
        
        nesting_res = calculate_sheet_nesting(sheet=sheet_dict, parts=parts_list, gap=payload.gap)
        
        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()
        
        sheet_w = payload.sheet.width
        sheet_h = payload.sheet.height
        sheet_offset_x = sheet_w + 300
        
        for idx, sheet_data in enumerate(nesting_res["sheets"]):
            current_offsetX = idx * sheet_offset_x
            
            msp.add_lwpolyline([
                (current_offsetX, 0),
                (current_offsetX + sheet_w, 0),
                (current_offsetX + sheet_w, sheet_h),
                (current_offsetX, sheet_h)
            ], close=True, dxfattribs={'layer': f'Лист_{idx+1}', 'color': 1})
            
            msp.add_text(
                f"Лист {idx+1} ({sheet_w}x{sheet_h} мм)",
                dxfattribs={'layer': f'Лист_{idx+1}', 'height': 25}
            ).set_placement((current_offsetX + 20, sheet_h + 40))

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
