#!/usr/bin/env python3
"""Generate the reference case's closed, axis-aligned ASCII STL solids."""

from pathlib import Path


CASE = Path(__file__).resolve().parents[1] / "case"
OUTPUT = CASE / "constant" / "triSurface"


def triangle_normal(a, b, c):
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    n = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    magnitude = sum(component * component for component in n) ** 0.5
    if magnitude == 0:
        raise ValueError("Degenerate triangle in generated geometry")
    return tuple(component / magnitude for component in n)


def write_box(name, bounds):
    """Write an outward-oriented, closed box surface in metres."""
    x0, x1, y0, y1, z0, z1 = bounds
    vertices = {
        "000": (x0, y0, z0), "100": (x1, y0, z0),
        "110": (x1, y1, z0), "010": (x0, y1, z0),
        "001": (x0, y0, z1), "101": (x1, y0, z1),
        "111": (x1, y1, z1), "011": (x0, y1, z1),
    }
    faces = (
        ("000", "010", "110", "100"),  # -z
        ("001", "101", "111", "011"),  # +z
        ("000", "100", "101", "001"),  # -y
        ("010", "011", "111", "110"),  # +y
        ("000", "001", "011", "010"),  # -x
        ("100", "110", "111", "101"),  # +x
    )
    path = OUTPUT / f"{name}.stl"
    with path.open("w", encoding="ascii", newline="\n") as stl:
        stl.write(f"solid {name}\n")
        for face in faces:
            a, b, c, d = (vertices[key] for key in face)
            for tri in ((a, b, c), (a, c, d)):
                nx, ny, nz = triangle_normal(*tri)
                stl.write(f"  facet normal {nx:.9g} {ny:.9g} {nz:.9g}\n")
                stl.write("    outer loop\n")
                for x, y, z in tri:
                    stl.write(f"      vertex {x:.9g} {y:.9g} {z:.9g}\n")
                stl.write("    endloop\n  endfacet\n")
        stl.write(f"endsolid {name}\n")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    # All faces lie on the 1.5 mm background grid to avoid poor cut-cell skew.
    write_box("pcb", (-0.024, 0.024, -0.024, 0.024, 0.0045, 0.006))
    write_box("cpu", (-0.0045, 0.0045, -0.0045, 0.0045, 0.006, 0.0075))
    write_box("aluminumBase", (-0.0135, 0.0135, -0.0135, 0.0135, 0.0075, 0.009))

    fin_thickness = 0.003
    fin_length = 0.027
    fin_height = 0.012
    fin_centres = (-0.012, -0.006, 0.0, 0.006, 0.012)
    for index, centre in enumerate(fin_centres):
        write_box(
            f"fin{index}",
            (
                centre - fin_thickness / 2,
                centre + fin_thickness / 2,
                -fin_length / 2,
                fin_length / 2,
                0.009,
                0.009 + fin_height,
            ),
        )
    print(f"Generated {len(list(OUTPUT.glob('*.stl')))} STL solids in {OUTPUT}")


if __name__ == "__main__":
    main()
