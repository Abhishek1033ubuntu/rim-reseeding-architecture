# QMS & Low-DPMO Sub-Vendor Quality Inspection Specification

> **Document ID:** `DOC-QMS-2026-REV3`
> **File:** `docs/qms-dpmo-protocol-spec.md`
> **License:** `Apache-2.0`
> **Target Quality Baseline:** `< 35.0 DPMO` across overall SMT assembly lines

---

## 1. Executive Summary & Quality Strategy

This specification details the inline Quality Management System (QMS) and Incoming Quality Control (IQC) protocols required for Phase 1 manufacturing of RIM Handset platforms. To guarantee a first-pass yield of ≥ 99.4% and keep total inventory scrap loss under 1.5%, quality verification is moved entirely upstream to sub-vendor origins and automated inline Surface Mount Technology (SMT) inspection gates.

Rather than relying on post-sale warranty claims, physical component lots are cryptographically validated prior to shipment, and PCB motherboards pass through six automated inspection checkpoints before chassis mating.

---

## 2. Sub-Vendor Quality & IQC Requirements

Sub-vendors supplying silicon, memory, displays, passive components, and mechanical sub-assemblies must maintain a process capability index ($C_{pk}$) of ≥ 1.67 across key critical-to-quality (CTQ) parameters.

### 2.1 Process Capability Metrics

Process capability is calculated according to standard statistical process control formulas:

$$C_{pk} = \min \left( \frac{\text{USL} - \mu}{3\sigma}, \frac{\mu - \text{LSL}}{3\sigma} \right)$$

* **USL / LSL:** Upper and Lower Specification Limits.
* **$\mu$:** Process mean across 10,000 consecutive sample units.
* **$\sigma$:** Process standard deviation.

### 2.2 Sub-Vendor Audit Matrix

| Component Tier | Sub-Vendor Scope | Mandatory Origin Audit & IQC Protocol | Target $C_{pk}$ |
| --- | --- | --- | --- |
| **Tier 1: Silicon Fabs** | 12nm R-SCE Companion ASIC & Commercial 4nm Main AP | 100% Wafer-Level Acceptance Test (WLFA), BGA Solder Ball Coplanarity check, X-ray void area < 3%. | $\ge 1.80$ |
| **Tier 1: Memory** | 16GB LPDDR5X RAM & 512GB UFS 4.0 Flash | 48-hour High-Temp Burn-In (125°C), High-Speed Signal Parity Validation. | $\ge 1.75$ |
| **Tier 2: Displays** | 6.4" & 6.9" 120Hz LTPO AMOLED Panels | Sub-Pixel Luminance Uniformity, Flexible Printed Circuit (FPC) Bend Fatigue Testing. | $\ge 1.67$ |
| **Tier 2: Power** | 5500mAh Silicon-Carbon Battery Cells | 100% Automated X-ray Layer Alignment, Anode/Cathode Overhang Inspection. | $\ge 2.00$ |

---

## 3. Sequential SMT Inspection Gates

Every motherboard manufacturing line incorporates six automated, non-destructive inspection gates. Failing an inspection gate automatically halts the SMT indexing conveyor to prevent bad assemblies from accumulating high-cost components.

```
 [ BARE HDI PCB ] ──► [ GATE 1: 3D-SPI ] ──► [ PICK-AND-PLACE ] ──► [ GATE 2: PRE-AOI ]
                                                                             │
 [ FBLT & PROVISIONING ] ◄── [ GATE 5: ICT/JTAG ] ◄── [ GATE 4: 3D-AOI ] ◄── [ REFLOW OVEN ] ◄── [ GATE 3: 3D-AXI ]

```

### Gate 1: 3D Solder Paste Inspection (3D-SPI)

* **Location:** Immediate post-stencil printer output.
* **Inspection Parameters:** Solder paste deposit volume, height, area, bridging, and pad coverage offset.
* **Acceptance Criteria:** Solder volume bounded between **85% and 115%** of nominal aperture volume. Maximum height deviation $\le 10\,\mu\text{m}$.

### Gate 2: Pre-Reflow 3D Automated Optical Inspection (Pre-AOI)

* **Location:** Post high-speed component pick-and-place indexing.
* **Inspection Parameters:** Component presence, polarity (Pin-1 alignment), axial displacement ($\Delta x, \Delta y, \Delta \theta$), and package skew.
* **Acceptance Criteria:** Maximum allowable placement offset $\le 15\,\mu\text{m}$. Zero missing components across 0201/01005 passives.

### Gate 3: 3D Automated X-ray Inspection (3D-AXI)

* **Location:** Post-reflow cooling chamber.
* **Inspection Parameters:** Multi-layer volumetric X-ray reconstruction of hidden Fine-Pitch BGA joints under the R-SCE Companion ASIC and primary Application Processor.
* **Acceptance Criteria:** Individual solder ball voiding capped at **$\le 5\%$** of total joint cross-sectional area. Zero Head-in-Pillow (HiP) or micro-bridging defects allowed.

### Gate 4: Post-Reflow 3D Automated Optical Inspection (Post-AOI)

* **Location:** Post-cooling zone output.
* **Inspection Parameters:** 3D solder fillet profile, wetting angle, tombstoning, billboarding, coplanarity, and solder balling.
* **Acceptance Criteria:** Solder wetting angle $\ge 30^\circ$, minimum fillet height $\ge 50\%$ of component termination height.

### Gate 5: In-Circuit Testing (ICT) & Boundary Scan

* **Location:** Automated pogo-pin bed-of-nails fixture.
* **Inspection Parameters:** Low-voltage node resistance, impedance testing, rail shorts, and IEEE 1149.1 / IEEE 1149.6 JTAG boundary scans across AP-to-ASIC high-speed interconnects.
* **Acceptance Criteria:** 100% trace continuity across PCIe/MIPI lines without powering up main processor cores.

### Gate 6: Functional Board-Level Test (FBLT) & Cryptographic Provisioning

* **Location:** Final electronic module testing station.
* **Execution:** Powers board under controlled thermal profiling, runs R-SCE ASIC hardware compression diagnostics, injects signed Persona Configuration Vectors (PCV), and writes unique device cryptographic keys into the hardware Secure Enclave.

---

## 4. DPMO Allocation & Mathematical Formulas

Defects Per Million Opportunities (DPMO) is evaluated dynamically across all active SMT shifts:

$$\text{DPMO} = \left( \frac{\text{Total Defective Units Detected}}{\text{Total Units Produced} \times \text{Opportunities Per Unit}} \right) \times 1,000,000$$

Where Opportunities Per Unit ($O$) for Platform A/B motherboard is fixed at $O = 4,850$ placement and solder joint opportunities per board.

### Target DPMO Budget Allocation

| Process Stage | Max Allowed DPMO | Controlling Inspection Gate | First-Pass Yield Target |
| --- | --- | --- | --- |
| **Solder Paste Printing** | $< 8.0 \text{ DPMO}$ | Gate 1 (3D-SPI) | $\ge 99.92\%$ |
| **Component Placement** | $< 5.0 \text{ DPMO}$ | Gate 2 (Pre-AOI) | $\ge 99.95\%$ |
| **Reflow & BGA Jointing** | $< 12.0 \text{ DPMO}$ | Gate 3 (3D-AXI) & Gate 4 (Post-AOI) | $\ge 99.88\%$ |
| **Electrical & Boundary Scan** | $< 6.0 \text{ DPMO}$ | Gate 5 (ICT/JTAG) | $\ge 99.94\%$ |
| **Functional & Provisioning** | $< 4.0 \text{ DPMO}$ | Gate 6 (FBLT) | $\ge 99.96\%$ |
| **TOTAL SMT LINE AGGREGATE** | **$< 35.0 \text{ DPMO}$** | **All Gates (1–6)** | **$\ge 99.40\%$** |

---

## 5. Pre-Sales Pipeline & MES Closed-Loop Integration

The QMS connects directly to the factory Manufacturing Execution System (MES) via an automated Level 3 ISA-95 control loop:

1. **Demand Signal Ingestion:** D2C pre-order velocity and carrier EDI allocations update daily production demand.
2. **Dynamic Assembly Ratio:** SMT lines adjust chassis mating ratios between Platform A (6.4" Compact) and Platform B (6.9" Expanded) while running a continuous common-core PCB assembly.
3. **Traceability Hash:** Each unit's 2D Matrix Code links component serial numbers, Gate 1–6 inspection telemetry, and injected PCV tokens into an immutable manufacturing audit record.
