# Thermal design of a PCB and heatsink with conjugate heat transfer

This tutorial explains the physics and numerical choices behind the OpenFOAM
case in this repository. It follows the case from thermodynamics, through heat
transfer and conjugate heat transfer (CHT), to the solver and its numerical
controls.

The reference case uses a 35 W silicon die, an FR4 board, an aluminium
heatsink, and buoyancy-driven air in a small closed enclosure. Its properties
are representative constants, not supplier data. Read the
[case assumptions and run instructions](../README.md) alongside this document.

## 1. Thermodynamics and heat-transfer basics

### 1.1 Temperature, energy, and material properties

Temperature describes a body's thermal state; heat is energy transferred
because of a temperature difference. In this case, absolute temperature is in
kelvin, length in metres, time in seconds, pressure in pascals, and power in
watts.

For a simple material with constant specific heat, the sensible enthalpy
difference is approximately

$$
\Delta h = c_p \Delta T,
$$

where $c_p$ is specific heat capacity in $\mathrm{J/(kg\,K)}$. The specific
enthalpy is energy per unit mass in $\mathrm{J/kg}$. For a simple compressible
substance, enthalpy is $h=e+p/\rho$, where $e$ is internal energy per unit
mass. The case's `sensibleEnthalpy` model uses enthalpy relative to a
reference state; the arbitrary reference does not change the temperature
differences or heat rates of interest.

For an ideal gas,

$$
p = \rho R T,\qquad h \simeq c_p T,\qquad c_p-c_v=R,
$$

where $R$ is the gas-specific constant and $c_v$ is specific heat at constant
volume. The air dictionary uses the `perfectGas` equation of state, constant
$c_p$, constant dynamic viscosity, and a specified Prandtl number. The solids
use constant density, heat capacity, and isotropic conductivity.

### 1.2 Three heat-transfer mechanisms

**Conduction** transports energy through a material. Fourier's law is

$$
\mathbf{q}'' = -k\nabla T,
$$

where $\mathbf{q}''$ is heat flux in $\mathrm{W/m^2}$ and $k$ is thermal
conductivity in $\mathrm{W/(m\,K)}$. The minus sign means heat flows down the
temperature gradient.

**Convection** is energy carried by moving fluid, together with conduction
through the fluid next to a surface. Newton's cooling law is a useful
engineering summary,

$$
\dot Q = h_c A (T_s-T_\infty),
$$

where $h_c$ is a convection coefficient, $A$ is area, and $T_s$ and
$T_\infty$ are the surface and reference-fluid temperatures. In a resolved
CHT calculation, $h_c$ is not prescribed: it can be estimated afterward from
the computed surface heat rate and a clearly stated temperature difference.

**Radiation** transfers energy by electromagnetic emission. It is excluded
from this case; the coupled temperature boundaries specify no radiative heat
flux. This omission can matter for warm, exposed heatsinks.

For a one-dimensional, constant-area layer, conduction resistance is
$R_{\mathrm{cond}}=L/(kA)$; a convection resistance is
$R_{\mathrm{conv}}=1/(h_cA)$. Resistances in series can give a useful
hand-calculation check, but a finned three-dimensional board has parallel and
spreading paths that a simple series network cannot fully represent.

## 2. Governing equations

### 2.1 Fluid mass and momentum

Conservation of mass for a compressible fluid is

$$
\frac{\partial \rho}{\partial t}+\nabla\cdot(\rho\mathbf{u})=0.
$$

The Newtonian-fluid momentum balance is

$$
\frac{\partial(\rho\mathbf{u})}{\partial t}
+\nabla\cdot(\rho\mathbf{u}\mathbf{u})
=-\nabla p+\nabla\cdot\boldsymbol{\tau}+\rho\mathbf{g},
$$

where $\mathbf{u}$ is velocity, $p$ is thermodynamic pressure, and
$\mathbf{g}$ is gravitational acceleration. For a laminar Newtonian fluid,

$$
\boldsymbol{\tau}=\mu\left[\nabla\mathbf{u}+(\nabla\mathbf{u})^T
-\frac{2}{3}(\nabla\cdot\mathbf{u})\mathbf{I}\right],
$$

with dynamic viscosity $\mu$ and identity tensor $\mathbf{I}$. These are
continuum conservation equations; their finite-volume discretization and the
solver's pressure correction are discussed in Section 5.

### 2.2 Buoyancy: ideal gas and Boussinesq models

In this case the air density follows the ideal-gas relation

$$
\rho = \frac{p}{RT}.
$$

At low Mach number, temperature-driven density variation affects buoyancy far
more than it affects the local inertia. A common approximation is Boussinesq:

$$
\rho \simeq \rho_0\left[1-\beta(T-T_0)\right],
$$

where $\rho_0$ is density at reference temperature $T_0$ and $\beta$ is the
volumetric thermal-expansion coefficient. After removing the reference
hydrostatic contribution, the remaining buoyancy force is approximately
$-\rho_0\beta(T-T_0)\mathbf{g}$ (with sign set by the gravity convention).
Boussinesq is appropriate when relative density variations are small. It is
an explanation of a widely used low-Mach model, **not** the equation of state
selected by this case.

The case selects `perfectGas`, so temperature and pressure determine density.
It also uses `p_rgh`, the reduced pressure variable

$$
p_{rgh}=p-\rho gh,
$$

where $gh$ denotes the signed gravitational potential per unit mass relative
to the solver's reference. Thus `p_rgh` is not the thermodynamic pressure
itself. The solver reconstructs thermodynamic pressure for the equation of
state. The `pRefCell` and `pRefValue` entries remove the pressure null space
for the closed domain; they are solver reference settings, not an inlet or
outlet pressure boundary condition.

### 2.3 Fluid energy and solid conduction

For a single-phase fluid, one useful sensible-enthalpy statement is

$$
\frac{\partial(\rho h)}{\partial t}
+\nabla\cdot(\rho\mathbf{u}h)
=\frac{\partial p}{\partial t}
+\mathbf{u}\cdot\nabla p
+\nabla\cdot(k_f\nabla T)
+\Phi+\dot q_v,
$$

where $h$ is specific enthalpy, $k_f$ is fluid conductivity, $\Phi$ is
viscous dissipation, and $\dot q_v$ is a volumetric heat source. The pressure
terms are pressure work. At low speeds they are often small, and the
viscous-dissipation term is usually negligible for electronics cooling, but
they belong to the general enthalpy balance. Turbulent models, when used,
also change the effective transport coefficients.

This is a continuum balance, not a literal transcription of OpenFOAM's
discretized energy equation. `chtMultiRegionSimpleFoam` obtains the
thermodynamic energy variable and transport properties from each region's
thermophysical model; do not infer every solver term from a reduced
low-speed schematic.

For a stationary solid with constant properties, the energy equation is

$$
\rho_s c_{p,s}\frac{\partial T}{\partial t}
=\nabla\cdot(k_s\nabla T)+\dot q'''.
$$

Here $\rho_s$ is solid density, $c_{p,s}$ is solid heat capacity, $k_s$ is
solid conductivity, and $\dot q'''$ is heat generation per unit volume in
$\mathrm{W/m^3}$. At steady state the storage term vanishes:

$$
\nabla\cdot(k_s\nabla T)+\dot q'''=0.
$$

For uniform heating of volume $V$, $\dot q'''=P/V$. In this case the
`scalarSemiImplicitSource` adds 35 W to field `h` over cell zone `cpu`, using
`volumeMode absolute`; it is an integrated power, not a power density. The
source definition is in
[`case/system/cpu/fvOptions`](../case/system/cpu/fvOptions).

### 2.4 Solid-fluid and solid-solid interfaces

For a perfectly bonded interface with no thermal contact resistance,
temperature and normal heat flux are continuous:

$$
T_s=T_f,\qquad
-k_s\nabla T_s\cdot\mathbf{n}
=-k_f\nabla T_f\cdot\mathbf{n}.
$$

The same interface normal $\mathbf{n}$ is used on both sides in this
equation. The coupled temperature boundary conditions exchange heat between
the neighboring region meshes. The case couples air to PCB, CPU, and
aluminium, and also couples the solid regions to each other. Any solder,
thermal-interface material, imperfect contact, or gap should instead be
represented with a layer or a suitable contact-resistance model.

## 3. Natural convection and useful scales

Natural convection starts when gravity acts on temperature-dependent density.
Warm, less-dense air rises; cooler air descends, creating circulation that
carries energy from the package and fin surfaces. The case has no fan or
imposed inlet: the enclosure walls are held at 300 K, and all solid surfaces
are no-slip on the air side.

The following dimensionless groups help judge the flow and compare
correlations:

$$
\mathrm{Pr}=\frac{\nu}{\alpha}
=\frac{\mu c_p}{k_f},\qquad
\mathrm{Ra}_L=\frac{g\beta\Delta T L^3}{\nu\alpha},\qquad
\mathrm{Nu}_L=\frac{h_cL}{k_f}.
$$

Here $\nu=\mu/\rho$ is kinematic viscosity, $\alpha=k_f/(\rho c_p)$ is
thermal diffusivity, $L$ is a characteristic length, and $\Delta T$ is a
stated temperature difference. The Prandtl number compares momentum and
thermal diffusion; Rayleigh number indicates the relative strength of
buoyancy to viscous and thermal diffusion; Nusselt number compares convection
with conduction across the chosen length scale. Correlations for $\mathrm{Nu}$
depend on geometry, orientation, and flow regime, so they are checks rather
than replacements for the resolved case.

## 4. The CHT model in this repository

CHT solves fluid motion and energy in the air while solving conduction in
each solid region. The coupled interface conditions let the solid
temperatures and air-side heat transfer emerge together, rather than imposing
a guessed convection coefficient.

The model consists of:

- **Regions:** `domain0` air, `pcb` FR4, `cpu` silicon, and `aluminum`
  heatsink, declared in
  [`case/constant/regionProperties`](../case/constant/regionProperties).
- **Air:** `heRhoThermo`, `perfectGas`, sensible enthalpy, laminar flow,
  constant transport properties, and gravity $(0,0,-9.81)\ \mathrm{m/s^2}$.
  See [`case/constant/domain0/thermophysicalProperties`](../case/constant/domain0/thermophysicalProperties)
  and [`case/constant/domain0/turbulenceProperties`](../case/constant/domain0/turbulenceProperties).
- **Solids:** `heSolidThermo`, constant isotropic conductivity, constant
  density and heat capacity. The values are in each solid region's
  `thermophysicalProperties` file.
- **Power and boundaries:** 35 W in the CPU; air begins at 300 K; enclosure
  walls are fixed at 300 K; interfaces are coupled; radiation is off. The
  enclosure walls are therefore a prescribed heat sink, not adiabatic
  boundaries or an infinite unmodeled room.
- **Flow regime:** steady, laminar natural convection. Do not enable a
  turbulence model solely to reduce residuals; justify it using physical
  regime, resolution, and an appropriate near-wall treatment.

The 300 K wall condition removes heat from the modeled enclosure and
represents a controlled ambient sink. If the real enclosure is insulated or
exchanges heat with a larger room, model that thermal path instead. For
forced-air cooling, use justified inlet mass-flow/velocity and outlet
pressure conditions rather than retaining this sealed-cavity setup.

## 5. Solver and numerical settings

### 5.1 What `chtMultiRegionSimpleFoam` does

The case uses `chtMultiRegionSimpleFoam`, a steady multi-region solver. In
the fluid it iterates the momentum, pressure/density, and enthalpy equations;
in the solids it iterates the enthalpy/conduction equations. It exchanges
temperature and heat flux at coupled region interfaces during the
multi-region iteration. It is not a physical transient simulation.

For the fluid, SIMPLE (Semi-Implicit Method for Pressure-Linked Equations)
starts from a momentum-predicted velocity, solves a pressure-correction
equation derived to satisfy continuity, and corrects pressure and velocity.
This repeats until the coupled fields converge. In buoyant compressible
flows, density and temperature must also remain consistent through the
thermodynamic model. `p_rgh` improves treatment of the hydrostatic pressure
variation; it does not mean pressure can be omitted from the momentum
balance.

### 5.2 Discretization choices in this case

The common region dictionaries include:

- `ddtSchemes { default steadyState; }`: no physical time derivative is
  advanced; solver iterations are pseudo-time/iteration labels.
- `div(phi,U)` and `div(phi,h)` use bounded upwind convection for a robust
  startup on the baseline mesh. Upwind is diffusive; compare a higher-order
  bounded scheme only after a stable baseline and check that the design
  temperatures and heat balance remain reliable.
- Gradients and interpolation use linear schemes. Laplacians use a limited
  non-orthogonal correction (`limited 0.333`), and surface-normal gradients
  are similarly limited to tolerate snapped, non-orthogonal cells.
- The stress-divergence and pressure-flux terms are explicitly specified for
  the selected compressible formulation.

These entries are in [`case/system/fvSchemesContents`](../case/system/fvSchemesContents)
and are included by the common and per-region `fvSchemes` files.

### 5.3 Linear solvers, relaxation, and stopping

[`case/system/fvSolutionContents`](../case/system/fvSolutionContents)
contains the linear solvers and SIMPLE controls. In the current setup:

- GAMG solves `p_rgh`; PBiCGStab with DILU solves `U` and `h`; PCG with DIC
  solves `rho`.
- `tolerance` is an absolute linear-solver residual target; `relTol` permits
  stopping after a specified relative reduction from the starting residual.
  A nonzero `relTol` can make a linear solve stop before its absolute
  tolerance is reached.
- Under-relaxation factors (0.3 for `p_rgh`, 0.5 for `rho` and `U`, 0.7 for
  `h`) damp field updates to improve steady SIMPLE stability. Lower values
  can stabilize oscillation but slow progress; change them only while
  tracking convergence.
- `residualControl` thresholds in SIMPLE can request early termination when
  equation residuals are sufficiently small. `endTime 400` in
  [`case/system/controlDict`](../case/system/controlDict) is only a cap;
  reaching it does not demonstrate convergence.

Residuals measure equation-solver error, not design accuracy. Also check
temperature histories, total heat balance, mesh sensitivity, and the
physical assumptions. Probe points in `controlDict` record a CPU-core and
heatsink-base temperature; they are not volume maxima.

## 6. Thermal resistance, heat balance, and verification

For a specified heat path,

$$
R_{\mathrm{th}}=\frac{T_{\mathrm{hot}}-T_{\mathrm{reference}}}{\dot Q}
\quad [\mathrm{K/W}].
$$

Always state the temperature measure and the heat rate. A peak cell
temperature, volume average, area average, and package junction temperature
are different quantities. For an approximate CPU-to-ambient system metric,
using the CPU peak and nominal 300 K ambient,

$$
R_{\mathrm{CPU-ambient}}\simeq
\frac{T_{\mathrm{CPU,max}}-300\ \mathrm{K}}{35\ \mathrm{W}}.
$$

This is a system-level metric, not a single material resistance. The probe
histories are useful for tracking iteration stability, but use region-aware
post-processing to obtain the CPU maximum or a defined average and integrate
the outward heat flux on external boundaries.

At a converged steady state, the net heat leaving the model should balance
the applied 35 W (subject to numerical error). Report the relative imbalance
as

$$
\epsilon_Q=\frac{\left|Q_{\mathrm{in}}-Q_{\mathrm{out}}\right|}
{Q_{\mathrm{in}}}.
$$

Include every heat-rejection boundary and use consistent outward-normal sign
conventions. An imbalance can indicate incomplete convergence, incorrect
source units, or a missing heat path.

Before using a result for design, check:

1. `checkMesh` for invalid cells, skewness, non-orthogonality, and cell count.
2. That all four regions and both sides of every coupled interface exist.
3. Residual and probe-temperature histories, plus the integrated heat
   balance; small residuals alone are insufficient.
4. Sensitivity of CPU temperature and heat balance to systematic mesh
   refinement, particularly through the 3 mm fin channels and thin solids.
5. Sensitivity to material data, wall/ambient conditions, and omitted physics.
6. Agreement with an analytical estimate or a documented experiment.

The background mesh is nominally 1.5 mm, with local fin-channel refinement
to about 0.75 mm (roughly four cells across a nominal 3 mm gap). Snapping
changes actual cell sizes, so inspect the generated mesh; the nominal count
does not establish grid independence.

## 7. Limitations and next model improvements

The baseline omits radiation, anisotropic copper planes and vias, package
layers, solder, contact resistance, temperature-dependent properties, fan
curves, enclosure leakage, and nonuniform die power. Any of these may
materially change temperatures. Replace representative inputs with measured
or sourced properties, represent important layers and thermal contacts,
match the real enclosure and flow conditions, validate against measurements,
and document uncertainty before making product claims.

## 8. Learning resources

Follow this sequence; the case files are the most direct way to connect each
topic to an implemented setting.

1. **Thermodynamics and properties:** review ideal-gas behavior, sensible
   enthalpy, heat capacity, and units in the [OpenStax University Physics,
   Volume 2](https://openstax.org/details/books/university-physics-volume-2).
   For property definitions and reference data, consult
   [NIST Chemistry WebBook](https://webbook.nist.gov/chemistry/).
2. **Heat transfer:** study Fourier conduction, convection, radiation, and
   thermal resistance in [MIT OpenCourseWare 2.51 Intermediate Heat and Mass
   Transfer](https://ocw.mit.edu/courses/2-51-intermediate-heat-and-mass-transfer-fall-2008/).
   Use correlations only when geometry and regime assumptions match.
3. **Natural convection and dimensionless groups:** derive and interpret
   $\mathrm{Pr}$, $\mathrm{Ra}$, and $\mathrm{Nu}$ before selecting a
   correlation. Compare the correlation's boundary conditions and geometry
   with the enclosed, finned PCB case.
4. **Finite volume and OpenFOAM:** use the
   [OpenFOAM.com documentation overview](https://www.openfoam.com/documentation/overview)
   to browse the Fundamentals, Processing, and Post-processing guides. Start
   with conservation laws and finite-volume discretization, then read the
   solver and dictionary sections for multi-region heat transfer,
   thermophysical models, `fvSchemes`, and `fvSolution`. The online guide may
   default to a newer release; check documentation and tutorials for the
   installed OpenFOAM.com release (v2512), since Foundation and OpenCFD
   releases can differ.
5. **Apply it to this case:** trace
   [`regionProperties`](../case/constant/regionProperties),
   the air and solid `thermophysicalProperties`,
   [`fvOptions`](../case/system/cpu/fvOptions),
   [`fvSchemesContents`](../case/system/fvSchemesContents),
   [`fvSolutionContents`](../case/system/fvSolutionContents), and
   [`controlDict`](../case/system/controlDict). Compare each dictionary
   setting to the equation or assumption it represents, then run the
   validation checks in Section 6.
