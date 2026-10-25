# Thermal design of a PCB and heatsink with conjugate heat transfer

## 1. What the model predicts

Conjugate heat transfer (CHT) solves heat conduction in solids and fluid
momentum/energy in the adjacent air, coupling temperature and heat flux at
their common interfaces. Unlike a prescribed convection coefficient, the
air-side heat-transfer coefficient emerges from the resolved flow and thermal
boundary layer. The example case uses a 35 W silicon die, an FR4 board, an
aluminium heatsink, and buoyancy-driven air in a small enclosure.

Use absolute temperature in kelvin, SI length in metres, and watts for the heat
source. Material data and geometry here are representative constants, not
datasheet values.

## 2. Governing equations

### 2.1 Fluid conservation

For a Newtonian fluid, mass conservation is

\[
\frac{\partial \rho}{\partial t}+\nabla\cdot(\rho\mathbf{u})=0.
\]

The momentum equation is

\[
\frac{\partial(\rho\mathbf{u})}{\partial t}
+\nabla\cdot(\rho\mathbf{u}\mathbf{u})
=-\nabla p+\nabla\cdot\boldsymbol{\tau}+\rho\mathbf{g},
\]

where \(\mathbf{u}\) is velocity, \(p\) is thermodynamic pressure,
\(\mathbf{g}\) is gravitational acceleration, and
\(\boldsymbol{\tau}=\mu[\nabla\mathbf{u}+(\nabla\mathbf{u})^T
-\frac{2}{3}(\nabla\cdot\mathbf{u})\mathbf{I}]\) is the viscous stress.
The provided case uses steady, laminar flow; use a turbulence model only when
the flow regime and mesh support it.

### 2.2 Buoyancy and the Boussinesq approximation

For modest temperature differences, density variation is small except in the
gravity term. The Boussinesq model sets

\[
\rho \simeq \rho_0[1-\beta(T-T_0)]
\]

in buoyancy while treating density as constant elsewhere. Here \(\beta\) is
the thermal expansion coefficient and \(T_0\) is a reference temperature.
After absorbing the reference hydrostatic pressure into modified pressure,
the buoyancy contribution is approximately

\[
\rho_0\mathbf{g}-\rho_0\beta(T-T_0)\mathbf{g}.
\]

This approximation is appropriate when \(\beta|T-T_0|\ll1\), often used as a
rule-of-thumb for temperature differences of a few tens of kelvin in air.
The included v2512 case uses the ideal-gas equation of state, not a
Boussinesq thermo model; this retains density variation in the case's
compressible buoyant formulation. The Boussinesq equations above explain the
common low-Mach approximation and must not be mistaken for the selected
thermophysical dictionary.

### 2.3 Energy in air and solids

The fluid sensible-enthalpy equation can be written schematically as

\[
\frac{\partial(\rho h)}{\partial t}
+\nabla\cdot(\rho\mathbf{u}h)
=\nabla\cdot(k_f\nabla T)+\Phi+\dot q_v,
\]

where \(h\) is sensible enthalpy, \(k_f\) is fluid conductivity, \(\Phi\)
denotes viscous dissipation (usually negligible for slow electronics cooling),
and \(\dot q_v\) is a volumetric source if one is placed in the fluid.

For a stationary solid with constant properties,

\[
\rho_s c_{p,s}\frac{\partial T}{\partial t}
=\nabla\cdot(k_s\nabla T)+\dot q'''.
\]

In this case the 35 W CPU source is a volumetric source in the CPU solid:
\(\dot q'''=P/V_{\rm CPU}\) for a uniform source. The OpenFOAM
`scalarSemiImplicitSource` uses `volumeMode absolute`, so its integrated
source is 35 W across the selected CPU cell zone. A power density instead
requires `volumeMode specific` and units consistent with the solver's
enthalpy equation.

### 2.4 Solid-fluid interface conditions

At a perfectly bonded interface with no contact resistance,

\[
T_s=T_f,\qquad
-k_s\nabla T_s\cdot\mathbf{n}
=-k_f\nabla T_f\cdot\mathbf{n}.
\]

The coupled temperature boundary condition enforces heat-flux continuity
between the two region meshes. If a real package has thermal-interface
material, solder, imperfect contact, or a gap, represent those layers or
contact resistance explicitly instead of assuming perfect contact.

## 3. Pressure-velocity coupling for electronics cooling

Pressure is not advanced by an independent thermodynamic evolution equation
in the incompressible limit. The discretized momentum equation first gives a
provisional velocity. A pressure-correction equation is then derived by
substituting that velocity into continuity. Correcting pressure and velocity
restores mass conservation. SIMPLE performs this pressure/velocity correction
iteratively for steady calculations; PIMPLE/PISO variants are more typical for
transient cases.

For natural convection, gravity and temperature-dependent density (or a
Boussinesq density correction) create a pressure gradient and weak recirculating
velocity. That circulation transports heat from the package and fin surfaces.
In electronics cooling, the pressure field is generally a small dynamic
perturbation on atmospheric pressure, but its correction is essential: even a
small mass imbalance can distort the predicted buoyant plume and heat-transfer
rate. OpenFOAM's `p_rgh` is a pressure variable with the hydrostatic component
removed, which improves numerical conditioning in buoyant flows.

For forced-air cooling, provide physically justified inlet velocity/flow and
outlet pressure conditions; do not retain the sealed-cavity boundary
conditions unchanged.

## 4. Thermal resistance and extracting it

For a specified heat path,

\[
R_{\rm th}=\frac{T_{\rm hot}-T_{\rm reference}}{Q}
\quad [\mathrm{K/W}].
\]

Possible reference temperatures include the die-to-case, case-to-heatsink,
heatsink-to-air, and die-to-ambient differences. State the temperature
definition and heat rate every time: a maximum cell temperature, volume
average, interface area average, or package junction temperature are not
interchangeable.

For this case, record the CPU peak (or a specified volume average) and ambient
reference of 300 K. If all 35 W is rejected to that ambient, a first system
estimate is

\[
R_{\rm die-ambient}=\frac{T_{\rm CPU}-300\ \mathrm{K}}{35\ \mathrm{W}}.
\]

The probe functions track a CPU-core and heatsink-base point for convergence;
they are not by themselves a volume maximum or a complete thermal-resistance
measurement. Use region-aware post-processing (for example, sample CPU
`T` maximum and integrate normal heat flux over the outer heat-rejection
boundary) for reported values. Verify the integrated heat leaving all
external boundaries balances the 35 W source. An imbalance can indicate
incomplete convergence, a missing boundary path, or inconsistent source units.

## 5. Numerical strategy and verification

The solver is `chtMultiRegionSimpleFoam`: the flow region uses steady
finite-volume convection/diffusion and SIMPLE pressure correction; the solid
regions solve conduction in enthalpy form. Bounded upwind advection and
under-relaxation favour robustness for a first steady solution. More
accurate second-order convection can be tested after a stable baseline.

The fin channel is 3 mm wide. The 1.5-mm background mesh is locally refined
at the fins to about 0.75 mm, giving approximately four cells across the
nominal gap. Check the
actual mesh after snapping: local cell sizes and cut cells mean the target is
not a guaranteed count. Confirm multiple cells through thin solids and perform
a systematic mesh refinement study. Report residual history, probe
temperature history, global energy imbalance, mesh quality, mesh count, and
the sensitivity of the design metric to refinement.

## 6. Model limitations

The reference case omits radiation, anisotropic PCB copper planes, vias,
component/package layers, fan curves, enclosure leakage, contact resistance,
temperature-dependent material properties, and nonuniform die power maps.
These can dominate actual hardware temperatures. Replace the simplified
geometry and properties, establish appropriate ambient or forced-flow
boundaries, validate against measurements, and document uncertainty before
using results for design release.
