import math

class MultiSheetPacker:
    def __init__(self, sheet_width: float, sheet_height: float, gap: float = 1.0):
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.gap = gap  # Зазор под лазерный рез (в мм)

    def pack(self, parts: list) -> dict:
        # Подготовка списка отдельных элементов (поддерживаем и словари, и объекты)
        flat_parts = []
        for p in parts:
            if isinstance(p, dict):
                p_id = p.get("id")
                p_width = p.get("width")
                p_height = p.get("height")
                p_qty = p.get("quantity", 1)
            else:
                p_id = p.id
                p_width = p.width
                p_height = p.height
                p_qty = p.quantity

            for i in range(p_qty):
                flat_parts.append({
                    "id": f"{p_id}_{i+1}",
                    "part_id": p_id,
                    "w": p_width,
                    "h": p_height
                })

        # Сортировка по убыванию площади
        flat_parts.sort(key=lambda item: item["w"] * item["h"], reverse=True)

        remaining_parts = flat_parts.copy()
        sheets_result = []
        sheet_index = 1

        while remaining_parts:
            placed_parts, unplaced_parts = self._pack_single_sheet(remaining_parts)
            
            # Если ни одну деталь не удалось уложить (деталь больше листа)
            if not placed_parts:
                break

            used_area = sum(p["width"] * p["height"] for p in placed_parts)
            total_area = self.sheet_width * self.sheet_height
            utilization = (used_area / total_area) * 100 if total_area > 0 else 0

            svg_content = self.generate_svg(placed_parts, sheet_index)
            
            # Считаем суммарную длину реза для листа (периметры размещенных деталей)
            cut_length_m = sum(2 * (p["width"] + p["height"]) for p in placed_parts) / 1000.0

            sheets_result.append({
                "sheet_number": sheet_index,
                "placed_parts": placed_parts,
                "utilization_percentage": round(utilization, 2),
                "cut_length_m": round(cut_length_m, 2),
                "svg": svg_content
            })

            remaining_parts = unplaced_parts
            sheet_index += 1

        return {
            "sheets": sheets_result,
            "unplaced_parts": remaining_parts,
            "total_sheets": len(sheets_result)
        }

    def _pack_single_sheet(self, parts: list):
        free_rectangles = [{"x": 0.0, "y": 0.0, "w": self.sheet_width, "h": self.sheet_height}]
        placed_parts = []
        unplaced_parts = []

        for part in parts:
            pw_gap = part["w"] + self.gap
            ph_gap = part["h"] + self.gap

            best_rect_idx = -1
            best_fit_area = float('inf')
            rotated = False

            for idx, rect in enumerate(free_rectangles):
                # Без поворота
                if rect["w"] >= pw_gap and rect["h"] >= ph_gap:
                    area = rect["w"] * rect["h"]
                    if area < best_fit_area:
                        best_fit_area = area
                        best_rect_idx = idx
                        rotated = False
                # С поворотом 90°
                elif rect["w"] >= ph_gap and rect["h"] >= pw_gap:
                    area = rect["w"] * rect["h"]
                    if area < best_fit_area:
                        best_fit_area = area
                        best_rect_idx = idx
                        rotated = True

            if best_rect_idx != -1:
                target_rect = free_rectangles.pop(best_rect_idx)

                actual_w = part["h"] if rotated else part["w"]
                actual_h = part["w"] if rotated else part["h"]

                placed_w_gap = actual_w + self.gap
                placed_h_gap = actual_h + self.gap

                placed_parts.append({
                    "id": part["id"],
                    "x": target_rect["x"],
                    "y": target_rect["y"],
                    "width": actual_w,
                    "height": actual_h,
                    "rotated": rotated
                })

                rem_w = target_rect["w"] - placed_w_gap
                rem_h = target_rect["h"] - placed_h_gap

                if rem_w > 0:
                    free_rectangles.append({
                        "x": target_rect["x"] + placed_w_gap,
                        "y": target_rect["y"],
                        "w": rem_w,
                        "h": target_rect["h"]
                    })
                if rem_h > 0:
                    free_rectangles.append({
                        "x": target_rect["x"],
                        "y": target_rect["y"] + placed_h_gap,
                        "w": placed_w_gap,
                        "h": rem_h
                    })
            else:
                unplaced_parts.append(part)

        return placed_parts, unplaced_parts

    def generate_svg(self, placed_parts: list, sheet_num: int) -> str:
        colors = ["#4EA8DE", "#5E60CE", "#64DFDF", "#7209B7", "#4895EF", "#3A0CA3"]
        svg = [
            f'<svg id="svg-sheet-{sheet_num}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.sheet_width} {self.sheet_height}" width="100%" height="100%">',
            f'  <rect width="{self.sheet_width}" height="{self.sheet_height}" fill="#11111b" stroke="#45475a" stroke-width="2"/>'
        ]
        for i, p in enumerate(placed_parts):
            color = colors[i % len(colors)]
            svg.append(
                f'  <rect x="{p["x"]}" y="{p["y"]}" width="{p["width"]}" height="{p["height"]}" '
                f'fill="{color}" opacity="0.85" stroke="#ffffff" stroke-width="1.5"/>'
            )
            font_size = min(p["width"], p["height"]) / 4
            if font_size > 8:
                svg.append(
                    f'  <text x="{p["x"] + p["width"]/2}" y="{p["y"] + p["height"]/2}" '
                    f'fill="#ffffff" font-size="{min(font_size, 20)}" font-family="sans-serif" '
                    f'text-anchor="middle" dominant-baseline="central">{p["id"]}</text>'
                )
        svg.append('</svg>')
        return "\n".join(svg)
