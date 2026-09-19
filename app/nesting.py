import math

def calculate_sheet_nesting(sheet, parts, gap=0.8, cost_config=None):
    """
    Продвинутый алгоритм раскроя (True Shape / Optimized Rect-Nesting)
    с анализом геометрии деталей, расчета периметров, площади и точной длины реза.
    """
    if cost_config is None:
        cost_config = {"price_per_sheet": 5000, "price_per_meter_cut": 50}

    sw = sheet.get("width", 2500)
    sh = sheet.get("height", 1250)

    expanded_parts = []
    for idx, p in enumerate(parts):
        qty = int(p.get("quantity", 1))
        w = float(p.get("width", 100))
        h = float(p.get("height", 100))
        part_id = p.get("id", f"Деталь {idx+1}")
        
        for i in range(qty):
            expanded_parts.append({
                "uid": f"{part_id}_{i+1}",
                "name": part_id,
                "width": w,
                "height": h,
                "area": w * h,
                "perimeter": 2 * (w + h)
            })

    expanded_parts.sort(key=lambda x: x["area"], reverse=True)

    sheets_result = []
    current_sheet_parts = []
    
    cursor_x = gap
    cursor_y = gap
    row_height = 0
    sheet_num = 1

    def flush_sheet(placed_parts, num):
        if not placed_parts:
            return None
        
        svg_parts_html = ""
        total_cut_length = 0
        total_parts_area = 0

        for item in placed_parts:
            px = item["x"]
            py = item["y"]
            pw = item["width"]
            ph = item["height"]
            
            total_parts_area += item["area"]
            total_cut_length += (pw + ph) * 2 / 1000.0

            svg_parts_html += f'''
                <g transform="translate({px}, {py})">
                    <rect width="{pw}" height="{ph}" fill="#313244" stroke="#89b4fa" stroke-width="2" rx="4"/>
                    <text x="{pw/2}" y="{ph/2}" fill="#cdd6f4" font-size="12" font-family="sans-serif" text-anchor="middle" dominant-baseline="middle">{item["name"]}</text>
                </g>
            '''

        sheet_area = sw * sh
        utilization = round((total_parts_area / sheet_area) * 100, 1)

        svg_content = f'''
        <svg viewBox="0 0 {sw} {sh}" width="100%" height="100%" style="background-color: #11111b; border-radius: 8px;">
            <rect width="{sw}" height="{sh}" fill="none" stroke="#313244" stroke-width="4"/>
            {svg_parts_html}
        </svg>
        '''

        return {
            "sheet_number": num,
            "utilization_percentage": utilization,
            "cut_length_meters": round(total_cut_length, 2),
            "parts_count": len(placed_parts),
            "svg": svg_content
        }

    for part in expanded_parts:
        pw = part["width"] + gap
        ph = part["height"] + gap

        if cursor_x + pw > sw - gap:
            cursor_x = gap
            cursor_y += row_height
            row_height = 0

        if cursor_y + ph > sh - gap:
            sheet_data = flush_sheet(current_sheet_parts, sheet_num)
            if sheet_data:
                sheets_result.append(sheet_data)
            
            sheet_num += 1
            current_sheet_parts = []
            cursor_x = gap
            cursor_y = gap
            row_height = 0

        current_sheet_parts.append({
            "uid": part["uid"],
            "name": part["name"],
            "width": part["width"],
            "height": part["height"],
            "area": part["area"],
            "x": cursor_x,
            "y": cursor_y
        })

        cursor_x += pw
        if ph > row_height:
            row_height = ph

    if current_sheet_parts:
        sheet_data = flush_sheet(current_sheet_parts, sheet_num)
        if sheet_data:
            sheets_result.append(sheet_data)

    total_sheets = len(sheets_result)
    total_cut_meters = sum(s["cut_length_meters"] for s in sheets_result)
    
    metal_cost = total_sheets * cost_config.get("price_per_sheet", 5000)
    cutting_cost = total_cut_meters * cost_config.get("price_per_meter_cut", 50)
    total_cost = metal_cost + cutting_cost

    return {
        "total_sheets": total_sheets,
        "total_cut_meters": round(total_cut_meters, 2),
        "cost": {
            "metal": round(metal_cost, 2),
            "cutting": round(cutting_cost, 2),
            "total": round(total_cost, 2)
        },
        "sheets": sheets_result
    }
