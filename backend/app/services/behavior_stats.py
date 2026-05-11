"""Агрегация курсорных точек для хитмапа."""

from __future__ import annotations

import json
from collections import defaultdict


def build_heatmap(cursor_json_strings: list[str], grid: int = 40, max_cells: int = 600) -> list[dict[str, int]]:
    counts: dict[tuple[int, int], int] = defaultdict(int)
    for raw in cursor_json_strings:
        s = raw.strip()
        if not s:
            continue
        try:
            data = json.loads(s)
        except json.JSONDecodeError:
            continue
        points: list[tuple[int, int]] = []
        if isinstance(data, dict) and "x" in data and "y" in data:
            try:
                points.append((int(data["x"]), int(data["y"])))
            except (TypeError, ValueError):
                continue
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "x" in item and "y" in item:
                    try:
                        points.append((int(item["x"]), int(item["y"])))
                    except (TypeError, ValueError):
                        continue
        for x, y in points:
            gx = (x // grid) * grid + grid // 2
            gy = (y // grid) * grid + grid // 2
            counts[(gx, gy)] += 1
    sorted_cells = sorted(counts.items(), key=lambda it: -it[1])[:max_cells]
    return [{"x": gx, "y": gy, "count": c} for (gx, gy), c in sorted_cells]
