# F1 Aerodynamics Simulator: Engineering Report

Author: John Varghese
Date: 9/11/2026
Version: 1.0

## Abstract

This report describes a Python simulator that estimates the downforce, drag and efficiency of an F1-style wing and visualises the flow around its cross-section. Two models are used and kept separate: an analytical finite-wing model (Prandtl lifting-line slope, induced drag and an empirical stall shape) that gives forces in newtons, and a 2D Hess-Smith panel method that computes inviscid pressure distributions and streamlines. Both are verified against analytical results, exact solutions and mesh-convergence studies. The simulator reproduces the central trade-off of wing setup: moving from a low-drag to a high-downforce configuration raises downforce by about 2.5 times at about 5 times the drag. It is not CFD and is not validated against experimental data; its value is as a transparent, tested tool for understanding trends.

## 1. Introduction and objectives

Aerodynamic downforce lets a racing car corner faster than its tyres could manage on mechanical grip alone, but every newton of downforce costs drag. The objective of this project was to build an interactive simulator that makes this relationship visible and quantitative, with these goals:

1. Calculate downforce, drag, CL, CD, L/D and dynamic pressure for an adjustable wing.
2. Visualise airflow and surface pressure, distinguishing computed results from illustration.
3. Compare several wing configurations across angle of attack and airspeed.
4. Be honest about model assumptions, and verify the code rigorously.

## 2. Physics background

### 2.1 Dynamic pressure and force coefficients

Moving air carries kinetic energy per unit volume, the dynamic pressure q = 0.5 * rho * V^2. Aerodynamic forces are expressed through dimensionless coefficients:

    Downforce = q * S * CL
    Drag      = q * S * CD
    Efficiency = Downforce / Drag = CL / CD

where S is the planform area (chord x span). Forces therefore scale with the square of speed and linearly with air density and area.

### 2.2 Bernoulli's principle and pressure distribution

Along a streamline in steady, incompressible, inviscid flow, p + 0.5 * rho * V^2 is constant. Faster flow means lower pressure. The pressure coefficient Cp = (p - p_inf) / q_inf equals 1 at a stagnation point and is negative where the surface flow is faster than the free stream (suction). The net force on a wing is the integral of the pressure difference over its surface. This is equivalent to saying that the wing deflects the airflow and the pressure field transmits the resulting reaction force to the surface.

### 2.3 Angle of attack

For small angles in attached flow, CL varies linearly with angle of attack. Thin-airfoil theory gives a slope of 2*pi per radian (about 0.110 per degree) for a 2D section. Camber shifts the curve so the section produces lift at zero angle, and the zero-lift angle of a NACA 4412 is about -4.2 degrees.

### 2.4 Boundary layer, separation and stall

Air adheres to the surface, forming a thin boundary layer. On the suction side the flow decelerates toward the trailing edge against rising pressure (an adverse pressure gradient). If the boundary layer loses its momentum, it separates from the surface. Separation destroys suction, reduces CL sharply and raises drag: this is stall. Predicting it requires viscous modelling (boundary-layer solvers, RANS CFD or measured polars). Inviscid methods cannot represent it.

### 2.5 Induced drag

A finite wing has a pressure difference between its two surfaces, so air spills around the tips and forms trailing vortices. These vortices tilt the effective flow and add induced drag. For an elliptically loaded wing CDi = CL^2 / (pi * AR), and in general CDi = CL^2 / (pi * e * AR), where AR is the aspect ratio and e the span efficiency. Higher aspect ratio and endplates reduce induced drag.

### 2.6 Downforce: inverted wing versus aircraft wing

The physics is the same, mirrored. An F1 wing is mounted inverted, so the force it generates points toward the track and presses the tyres down, raising grip. The differences are in purpose and environment: an aircraft wing is optimised for high L/D to carry weight efficiently, whereas an F1 wing accepts low L/D to obtain large downforce. F1 wings also operate in strong interaction with the ground, wheels and bodywork and are usually multi-element, with slots that re-energise the boundary layer and delay separation at very high CL.

### 2.7 Effects not modelled

Multi-element slot flow, ground effect, tip-vortex and wake structure, and wheel and bodywork interaction are essential in real F1 aerodynamics and are outside the current model (see Section 7).

## 3. Methodology

### 3.1 Software architecture

The code separates physics, visualisation and interface:

    aero/   wing configuration, coefficients, forces, sweeps, panel method, theory
    viz/    Matplotlib figures and shared colour theme
    ui/     Streamlit sidebar, tabs and styling
    tests/  pytest suite
    scripts/ validation report generator

All quantities are SI internally (angles in degrees at the user interface). Wing configurations are immutable objects, so comparison mode is a matter of evaluating several of them with the same functions.

### 3.2 Analytical wing model

Sign convention: the wing is inverted, and a positive angle of attack means more downforce, so CL denotes a downforce coefficient.

1. Finite-wing lift slope: a = a0 / (1 + a0 / (pi * e * AR_eff)), with a0 = 2*pi per radian. AR_eff is the geometric aspect ratio multiplied by an endplate factor.
2. Lift: CL = CL0 + a * alpha below the stall angle, where CL0 represents the camber contribution.
3. Stall: beyond the stall angle, CL falls linearly by a fraction of its stall value over 10 degrees, and a separation drag term grows linearly. This is an empirical shape.
4. Drag: CD = CD0 + CL^2 / (pi * e * AR_eff) + CD_separation.

Default parameters (CL0 = 1.0, stall at 14 degrees, e = 0.9, endplate factor 1.15, CD0 = 0.020) are illustrative, chosen to be plausible and internally consistent.

### 3.3 2D panel method

The airfoil outline (a NACA 4-digit section, 120 panels by default) is divided into straight panels carrying constant-strength sources, plus a single vortex strength shared by all panels. Unknowns are the source strengths and the vortex strength. The equations are:

- No-penetration condition: zero normal velocity at each panel midpoint (N equations).
- Kutta condition: the tangential speeds on the two trailing-edge panels cancel, so the flow leaves the trailing edge smoothly (1 equation).

Solving the linear system gives the surface tangential velocity, hence Cp = 1 - (V/V_inf)^2, and integrating pressure over the panels gives CL and CD. Velocity at any point in the field is the superposition of the free stream and all panel contributions, which provides the pressure map and streamlines. Because the physics is mirror-symmetric, the solver works on an upright airfoil and the plots flip the vertical axis to show the inverted wing.

### 3.4 Computed versus illustrative

Every airflow picture in the application is computed from the panel solution. Nothing is hand-drawn. It is inviscid, 2D and not CFD, and the interface says so.

## 4. Verification and validation

Verification (does the code solve its equations correctly?) is documented in `validation_report.md`, generated by `scripts/run_validation.py`, and supported by an automated test suite.

| Area | Evidence |
|---|---|
| Force scaling | Forces scale with V^2 and with density; geometric similarity (chord and span scaled together) scales forces with area |
| Finite-wing slope | Tends to the thin-airfoil value 2*pi as aspect ratio increases |
| Induced drag | Matches CL^2 / (pi e AR) by hand calculation |
| Panel method, cylinder | Reproduces Cp = 1 - 4 sin^2(theta) with maximum error 0.004 |
| Panel method, airfoils | NACA 0012 at 5 deg: CL = 0.602 versus 0.599 from thin-airfoil theory with thickness correction; NACA 4412 at 0 deg: 0.507 versus 0.498 |
| Reference theory | Thin-airfoil zero-lift angles of NACA 2412 and 4412 (-2.1 and -4.2 deg) match published values |
| Inviscid consistency | Near-zero drag for a closed body, Kutta condition satisfied, lift from pressure integration agrees with Kutta-Joukowski within 3 % |
| Mesh convergence | CL changes by 0.5 % from 120 to 240 panels and the change shrinks with refinement |
| Configuration matrix | 450 combinations of preset, angle, speed and density give finite, positive results with a consistent stall flag |

Validation (is it the right model for reality?) has **not** been performed. No wind-tunnel, track or CFD reference data were used, so absolute accuracy against a real wing is unknown.

## 5. Results

### 5.1 Baseline wing

Baseline rear wing (chord 0.35 m, span 0.95 m, 8 degrees, 288 km/h, sea-level air):

| Quantity | Value |
|---|---|
| Dynamic pressure | 3,920 Pa |
| Downforce | 1,971 N (about 201 kgf) |
| Drag | 364 N |
| CL / CD | 1.512 / 0.279 |
| L/D | 5.42 |
| Induced share of drag | about 93 % |
| Power absorbed by drag | about 29 kW |

### 5.2 Effect of angle of attack

Downforce rises roughly linearly with angle up to the stall angle (14 degrees for the baseline), then falls while drag continues to rise. Efficiency L/D decreases monotonically with angle: induced drag grows with CL^2, so each extra degree of downforce is progressively more expensive. In this model the profile drag is constant, so L/D has no interior maximum. Measured and computed 2D airfoil polars typically show an L/D peak at a moderate angle, a property of viscous profile drag that the analytical model omits.

### 5.3 Effect of airspeed

Downforce and drag both scale with V^2, so the absolute difference between wing settings grows rapidly with speed. Drag power scales with V^3.

### 5.4 Configuration comparison

Illustrative presets at 288 km/h:

| Preset | Angle | Downforce | Drag | L/D |
|---|---|---|---|---|
| Low drag (Monza-style) | 4 deg | 1,193 N | 149 N | 7.98 |
| Balanced | 8 deg | 1,971 N | 364 N | 5.42 |
| High downforce (Monaco-style) | 12 deg | 3,018 N | 784 N | 3.85 |

The high-downforce configuration produces about 2.5 times the downforce of the low-drag configuration for about 5 times the drag. Which is better depends on the circuit, and answering that needs a lap-time model.

### 5.5 Panel-method flow

For a NACA 4412 section at 8 degrees the panel method gives a 2D section CL of 1.464 and a peak suction Cp of -3.70 near the leading edge, with Cp close to 1 near the leading edge on the pressure side. The Cp distribution shows a high suction peak that decays along the chord, as expected for a loaded section. These values are inviscid and would be reduced or altered by real viscous effects, especially close to stall.

## 6. Limitations

1. Stall in the analytical model is empirical, not computed.
2. The panel method is 2D and inviscid: no friction drag, no separation, no stall, no tip vortices. At angles beyond stall its flow field is not physically realistic.
3. No Reynolds-number effects, compressibility or turbulence modelling.
4. No ground effect, multi-element interaction, or interference from wheels and bodywork.
5. The preset and default parameters are illustrative, not measured.
6. The analytical and panel results are for different objects (finite wing and 2D section) and are not expected to agree numerically.
7. No experimental or CFD validation has been carried out.

## 7. Future work

1. Multi-element rear wing with slot flow.
2. Ground effect (method of images as a first step) and ride-height sensitivity.
3. Front wing versus rear wing comparison.
4. DRS open versus closed.
5. Sensitivity analysis to rank the most influential parameters.
6. A 2D OpenFOAM RANS case for comparison, which would provide the first validation against a viscous solution.
7. Coupling with a simple lap-time model to compare setups by lap time rather than by force alone.

## 8. Conclusion

The simulator gives a transparent, tested way to explore how angle, geometry and airspeed change downforce and drag, and it reproduces the qualitative trade-offs central to wing setup. Its numerical methods are verified against theory and exact solutions. Its main limits are the absence of viscous modelling and experimental validation, and these define the most valuable next steps.

## References

1. J. Katz, *Race Car Aerodynamics: Designing for Speed*, Bentley Publishers.
2. J. D. Anderson, *Fundamentals of Aerodynamics*, McGraw-Hill.
3. J. Katz and A. Plotkin, *Low-Speed Aerodynamics*, Cambridge University Press.
4. I. H. Abbott and A. E. von Doenhoff, *Theory of Wing Sections*, Dover.
5. J. L. Hess and A. M. O. Smith, "Calculation of potential flow about arbitrary bodies", *Progress in Aerospace Sciences*, vol. 8, 1967.
