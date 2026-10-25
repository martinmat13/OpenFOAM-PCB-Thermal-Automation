# PCB and heatsink conjugate heat transfer

An OpenFOAM.com v2512 reference case for steady natural-convection cooling of
a heated PCB, silicon package, and multi-fin aluminium heatsink. It is intended
as a reproducible portfolio example and as a starting point for replacing the
idealized geometry and material data with measured hardware data.

## Case assumptions

- Closed air enclosure: 90 x 90 x 48 mm, initially at 300 K; enclosure walls
  are held at 300 K to represent a controlled ambient heat sink.
- PCB: 48 x 48 x 1.5 mm FR4; CPU: 9 x 9 x 1.5 mm silicon.
- Heatsink: 27 x 27 x 1.5 mm base and five 3-mm-thick, 12-mm-tall fins.
  The 3-mm nominal fin channels are refined to a nominal 0.75-mm cell size
  (about four cells across each channel).
- A 35 W volumetric source is applied to the CPU solid region.
- Air is modeled as an ideal gas; flow is steady and laminar. Radiation,
  contact resistance, package layers, solder, and fan flow are not included.

These assumptions define a learning benchmark, not a product qualification
model. Review `docs/theory.md` before interpreting results.

## Requirements

- OpenFOAM.com v2512, sourced in the shell (`WM_PROJECT_VERSION= v2512`).
- Python 3.8+ for the standard-library geometry generator and plot utility.
- A POSIX shell; the scripts are Bash scripts.

The run script checks for the required OpenFOAM applications and stops on the first
failed stage. This repository was assembled against the locally installed
v2512 tools; numerical results depend on the local build and hardware.
In a WSL shell with the Debian-packaged installation used for validation, load
the environment with:

```bash
source /usr/lib/openfoam/openfoam2512/etc/bashrc
```

The layer-extrusion controls are explicitly documented in
`case/system/snappyHexMeshDict`, but `addLayers` is off for the baseline mesh so the
split solid-fluid interfaces remain matching. Enable layers only after
checking that the resulting interface faces remain valid on both regions.

## Run

From the repository root, first source OpenFOAM then run:

```bash
chmod +x case/Allrun case/Allclean
./case/Allrun
python3 scripts/plot_convergence.py
```

`case/Allrun` generates closed ASCII STL solids via the project utility,
creates the background mesh,
refines/snaps the CAD surfaces, splits the mesh into the `domain0` air region,
`pcb`, `cpu`, and `aluminum`, copies initial fields from `0.orig/`, checks the
mesh, and runs `chtMultiRegionSimpleFoam`. The complete solver output is saved as
`log.chtMultiRegionSimpleFoam`.

The plot utility reads solver iteration times from
`log.chtMultiRegionSimpleFoam`, pairs them with the CPU and heatsink probe
histories under `postProcessing/`, and writes
`postProcessing/thermal_convergence.svg`. It uses only the Python standard
library. Steady-solver pseudo-time is an iteration index, not physical elapsed
time.

The default 400-iteration limit is a practical first-run cap, not a guarantee
of convergence. Increase `endTime` in `case/system/controlDict` if residuals,
temperature probes, or the energy balance have not stabilized. Reaching
`endTime` is not proof of a converged design result.

To remove generated meshes, times, logs, probes, and generated STL files while
preserving the source dictionaries and initial fields:

```bash
./case/Allclean
```

## Validation methodology

1. Inspect `checkMesh` output for non-manifold faces, negative volumes,
   excessive skewness/non-orthogonality, and the final cell count.
2. Confirm all four mesh regions exist and that each solid-air and
   solid-solid interface has a matching coupled patch on both sides.
3. Refine the fin-channel mesh and compare CPU peak temperature and heat
   balance; the nominal four cells across a channel is a starting point, not
   proof of grid independence.
4. Check CPU-to-ambient heat rejection against the applied 35 W source.
   At convergence, report the imbalance as
   `abs(Qin - Qout)/Qin`; investigate rather than hide a material imbalance.
5. Track residuals and the CPU/heatsink temperature probes. A small residual
   alone is not evidence of a converged heat balance or mesh-independent result.
6. Compare temperatures and heat rates with a documented analytical
   resistance estimate or independent measurement before making design claims.

## Repository map

```text
.
├── case/                   # Complete, runnable OpenFOAM case
│   ├── 0.orig/              # Initial fields copied into 0 after region splitting
│   │   ├── domain0/
│   │   ├── aluminum/
│   │   ├── cpu/
│   │   └── pcb/
│   ├── constant/            # Material models, gravity, region declarations
│   ├── system/              # Mesh, discretization, solver and probe settings
│   │   └── regionTemplates/ # Region dictionaries copied after mesh splitting
│   ├── Allclean
│   └── Allrun
├── docs/
│   └── theory.md           # Portfolio-ready first-principles tutorial
├── scripts/                # Python geometry and plotting utilities
│   ├── generate_geometry.py
│   └── plot_convergence.py
└── README.md
```

## Adapting to hardware

Change dimensions and loads in `scripts/generate_geometry.py`, material
properties in `case/constant/<region>/thermophysicalProperties`, CPU power in
`case/system/cpu/fvOptions`, ambient conditions in `case/0.orig/domain0` fields,
and mesh resolution in `case/system/blockMeshDict` /
`case/system/snappyHexMeshDict`. Keep STL
coordinates in metres and ensure solid volumes meet at shared faces without
overlap or gaps. Regenerate the geometry and rerun `./case/Allrun` after any
geometry change.

## License and attribution

This is an original educational case. No vendor-specific hardware data is
provided. Add a project license and cite the OpenFOAM release used when
publishing or redistributing a derived project.
