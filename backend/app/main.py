from fastapi import FastAPI, UploadFile, File, HTTPException
import ezdxf
import math
import tempfile
import os

app = FastAPI(title="Metal Nesting API")

@app.post("/api/v1/dxf/parse")
async def parse_dxf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.dxf'):
        raise HTTPException(status_code=400, detail="Только DXF файлы поддерживаются")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        doc = ezdxf.readfile(tmp_path)
        msp = doc.modelspace()
        
        total_length = 0.0
        pierces = 0
        
        for entity in msp:
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                total_length += math.dist((start.x, start.y), (end.x, end.y))
            
            elif entity.dxftype() == 'CIRCLE':
                radius = entity.dxf.radius
                total_length += 2 * math.pi * radius
                pierces += 1
                
            elif entity.dxftype() == 'LWPOLYLINE':
                points = [p for p in entity.get_points('xy')]
                for i in range(len(points) - 1):
                    total_length += math.dist(points[i], points[i+1])
                if entity.closed:
                    total_length += math.dist(points[-1], points[0])
                    pierces += 1

        return {
            "filename": file.filename,
            "total_cut_length_mm": round(total_length, 2),
            "pierces_count": max(1, pierces),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка парсинга DXF: {str(e)}")
    finally:
        os.remove(tmp_path)
