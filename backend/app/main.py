from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

from app.nesting import MultiSheetPacker

app = FastAPI(title="Metal Nesting API")

class Sheet(BaseModel):
    width: float
    height: float

class Part(BaseModel):
    id: str
    width: float
    height: float
    quantity: int

class NestingRequest(BaseModel):
    sheet: Sheet
    parts: List[Part]
    gap: Optional[float] = 1.0  # Минимальный зазор под лазерный рез в мм

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.post("/api/v1/nest")
def calculate_nesting(data: NestingRequest):
    packer = MultiSheetPacker(data.sheet.width, data.sheet.height, gap=data.gap)
    result = packer.pack(data.parts)
    
    return {
        "status": "success",
        "sheet": data.sheet,
        "gap": data.gap,
        "total_sheets": result["total_sheets"],
        "sheets": result["sheets"],
        "unplaced_parts": result["unplaced_parts"]
    }
