#!/usr/bin/env python3
"""Plot probe temperature histories to an SVG using only the standard library."""

import html
import re
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
CASE = PROJECT / "case"
POST = CASE / "postProcessing"
OUTPUT = POST / "thermal_convergence.svg"
SOLVER_LOG = CASE / "log.chtMultiRegionSimpleFoam"


def read_solver_times():
    if not SOLVER_LOG.is_file():
        raise SystemExit(f"Solver log not found at {SOLVER_LOG}; run ./case/Allrun first.")
    time_pattern = re.compile(r"^\s*Time\s*=\s*([-+0-9.eE]+)\s*$")
    times = set()
    for line in SOLVER_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        match = time_pattern.match(line)
        if match:
            times.add(float(match.group(1)))
    if not times:
        raise SystemExit(f"No solver iteration times found in {SOLVER_LOG}.")
    return times


def read_probe_file(path):
    records = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        columns = line.split()
        if len(columns) >= 2:
            try:
                records.append((float(columns[0]), float(columns[1])))
            except ValueError:
                continue
    return records


def load_history(name, solver_times):
    matches = sorted(POST.glob(f"{name}/**/T"))
    samples = []
    for path in matches:
        samples.extend(
            sample for sample in read_probe_file(path) if sample[0] in solver_times
        )
    return sorted(samples, key=lambda item: item[0])


def main():
    if not POST.is_dir():
        raise SystemExit(f"No postProcessing directory found at {POST}; run ./case/Allrun first.")
    solver_times = read_solver_times()
    histories = {
        "CPU core": load_history("cpuCoreTemperature", solver_times),
        "Heatsink base": load_history("heatsinkBaseTemperature", solver_times),
    }
    histories = {name: data for name, data in histories.items() if data}
    if not histories:
        raise SystemExit(
            "No temperature probe data found. Expected postProcessing/"
            "{cpuCoreTemperature,heatsinkBaseTemperature}/<time>/T."
        )

    width, height = 900, 560
    left, right, top, bottom = 90, 30, 55, 75
    all_samples = [sample for data in histories.values() for sample in data]
    t_min = min(sample[0] for sample in all_samples)
    t_max = max(sample[0] for sample in all_samples)
    temp_min = min(sample[1] for sample in all_samples)
    temp_max = max(sample[1] for sample in all_samples)
    if t_min == t_max:
        t_max = t_min + 1
    if temp_min == temp_max:
        temp_min -= 0.5
        temp_max += 0.5
    temp_pad = max((temp_max - temp_min) * 0.08, 0.1)
    temp_min -= temp_pad
    temp_max += temp_pad

    def point(sample):
        x = left + (sample[0] - t_min) / (t_max - t_min) * (width - left - right)
        y = height - bottom - (sample[1] - temp_min) / (temp_max - temp_min) * (
            height - top - bottom
        )
        return f"{x:.2f},{y:.2f}"

    colors = {"CPU core": "#d62728", "Heatsink base": "#1f77b4"}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="450" y="30" text-anchor="middle" font-family="sans-serif" '
        'font-size="20">Steady CHT temperature convergence</text>',
        f'<path d="M{left},{top} V{height-bottom} H{width-right}" fill="none" '
        'stroke="#333" stroke-width="1.5"/>',
        f'<text x="450" y="{height-22}" text-anchor="middle" font-family="sans-serif" '
        'font-size="14">Solver iteration / pseudo-time (not physical time)</text>',
        f'<text x="22" y="280" transform="rotate(-90 22 280)" text-anchor="middle" '
        'font-family="sans-serif" font-size="14">Temperature (K)</text>',
        f'<text x="{left}" y="{height-bottom+24}" font-family="sans-serif" '
        f'font-size="12">{t_min:g}</text>',
        f'<text x="{width-right}" y="{height-bottom+24}" text-anchor="end" '
        f'font-family="sans-serif" font-size="12">{t_max:g}</text>',
        f'<text x="{left-10}" y="{height-bottom}" text-anchor="end" '
        f'font-family="sans-serif" font-size="12">{temp_min:.1f}</text>',
        f'<text x="{left-10}" y="{top+4}" text-anchor="end" '
        f'font-family="sans-serif" font-size="12">{temp_max:.1f}</text>',
    ]
    for index, (name, data) in enumerate(histories.items()):
        color = colors[name]
        coordinates = " ".join(point(sample) for sample in data)
        parts.append(
            f'<polyline points="{coordinates}" fill="none" stroke="{color}" '
            'stroke-width="2"/>'
        )
        legend_y = top + 20 + index * 24
        parts.append(
            f'<line x1="{width-220}" y1="{legend_y}" x2="{width-190}" '
            f'y2="{legend_y}" stroke="{color}" stroke-width="3"/>'
        )
        parts.append(
            f'<text x="{width-180}" y="{legend_y+5}" font-family="sans-serif" '
            f'font-size="13">{html.escape(name)}</text>'
        )
    parts.append("</svg>")
    OUTPUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    for name, data in histories.items():
        print(
            f"{name}: {data[0][1]:.3f} K at iteration {data[0][0]:g} -> "
            f"{data[-1][1]:.3f} K at iteration {data[-1][0]:g}"
        )
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
