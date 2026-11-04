# Modular Software Persona Overlay Architecture

> **Document ID:** `DOC-SW-2026-OVERLAY`
> **File:** `docs/software-persona-overlays.md`
> **License:** `Apache-2.0`
> **Target System:** Unified 2-Chassis Hardware Platform (Platform A & B) + R-SCE 12nm Companion ASIC

---

## 1. Architectural Architecture & Layering

The Modular Persona Software Stack decouples demographic feature sets from physical hardware assembly lines. By standardizing manufacturing around two master chassis designs (**Platform A 6.4" Compact** and **Platform B 6.9" Expanded**), demographic differentiation is achieved via signed **Persona Configuration Vector (PCV)** tokens provisioned into the R-SCE Companion ASIC Secure Enclave.

```
+-----------------------------------------------------------------------------------+
|                        MODULAR PERSONA OVERLAY ARCHITECTURE                       |
+-----------------------------------------------------------------------------------+
| LAYER 4: DEMOGRAPHIC OVERLAY  | Gamer | Corporate | Creator | Senior | Lifestyle  |
| (Dynamic UI & Persona Engine) | Mode  | Enterprise| Engine  | Vector | Guard      |
+-------------------------------+-------+-----------+---------+--------+------------+
| LAYER 3: PURPOSE-DRIVEN AI    | NPU Thermal/ | Local Doc/   | Live AV1/| Spatial Voice|
| (On-Device Local Models)      | Frame Interp | Mail Indexer | Transcode| Vector UI  |
+-------------------------------+--------------+--------------+----------+------------+
| LAYER 2: SYSTEM SERVICE FRAMEWORK & KERNEL COMPRESSION                            |
| (CXL-NOC Sync, Dynamic Compression Engine, Zero-Trust Enclave, FEC Transport)     |
+-----------------------------------------------------------------------------------+
| LAYER 1: HARDWARE ABSTRACTION LAYER (HAL)                                         |
| (Unified 4nm Silicon Driver Block | Platform A 6.4" / Platform B 6.9" Displays)   |
+-----------------------------------------------------------------------------------+

```

---

## 2. Persona Configuration Vector (PCV) Token Protocol

The PCV is a 32-bit hardware-enforced bitmask combined with a 256-bit HMAC-SHA256 signature generated during SMT Gate 6 provisioning.

### 2.1 Bitmask Allocations

| Bit Hex | Feature Flag Symbol | Demographic Focus | System Parameter Unlocks |
| --- | --- | --- | --- |
| `0x01` | `GAMER_MODE` | Mobile Esports / Gamers | 144Hz Refresh, GPU Thermal Cap Override, Touch-Sampling 900Hz |
| `0x02` | `CORPORATE_MODE` | Enterprise / Executives | Hardware Optical Trackpad Map, Local Vector Doc AI, Isolated Network Sandbox |
| `0x04` | `CREATOR_MODE` | Bloggers / Vloggers | Real-Time AV1/H.265 Transcoder, 3-Mic Spatial Audio Array, Dual Shutter Map |
| `0x08` | `LIFESTYLE_GUARD` | Privacy-Conscious Users | EXIF Data Auto-Redactor, Background Face Anonymizer, Tracker Blocker |
| `0x10` | `FASHION_PRESET` | Fashion & Design | Ambient Rear-Lighting Control, Ceramic Thermal Curve Tuning |
| `0x20` | `SENIOR_VECTOR_UI` | Elders & Seniors | Vector Geometry Scaler, High-Decibel Clarity Audio Filter |
| `0x40` | `IM_CHATTER_MODE` | Power Messaging / Youth | Tactile Edge Notification Bar, Low-Latency Background Socket Keep-Alive |

---

## 3. Detailed Persona Implementations

### 3.1 Gamer Mode (`0x01` — Platform B Expanded Chassis)

* **Target Hardware:** Platform B (6.9" 0.5" wider aspect ratio with dual vapor-chamber thermal routing).
* **Display Engine Driver:** Unlocks 144Hz LTPO refresh rate and increases touch-sampling response to 900Hz.
* **Silicon Allocation:** Directs the R-SCE ASIC to prioritize low-latency packet decompression over Direct Memory Access (DMA), dropping multiplayer packet jitter to under 0.5ms.

### 3.2 Corporate Enterprise (`0x02` — Platform A Compact Chassis)

* **Local Document Indexer:** Executes an isolated lightweight Vector Database running strictly on the local NPU. Indexes PDFs, spreadsheets, and emails without routing data to external cloud APIs.
* **Optical Trackpad Interoperability:** Maps kernel touch events to fine-grained desktop cursor mechanics, reviving classic tactile navigation efficiency for enterprise power users.
* **Zero-Trust Network Sandbox:** Enforces hardware-level AES-256-GCM encryption on all outbound enterprise network sockets.

### 3.3 Creator & Blogger Engine (`0x04` — Platform B Expanded Chassis)

* **Live AV1 Hardware Pipeline:** Intercepts raw camera frames and applies real-time AV1 quantization matrix scaling based on live 5G/6G Channel State Information (CSI).
* **3-Mic Spatial Audio Array:** Directs hardware beamforming algorithms across the three-microphone array, isolating primary speech while canceling ambient street noise.

### 3.4 Senior Vector-Scaled Adaptive UI (`0x20` — Platform A Compact Chassis)

Standard mobile operating systems apply scaling multipliers to text strings, causing UI clipping, button overflow, and layout breaking. The Senior Persona activates the **Vector Geometry Rendering Engine**.

```
Standard OS Scaling:   [ BUTTON TEXT OVERFLOW... ] (Layout Clipped / Truncated)
Vector UI Engine:      ┌─────────────────────────┐
                       │  LARGE VECTOR TEXT      │ (Layout Padding & Target Scale)
                       └─────────────────────────┘

```

#### Vector UI Scaling Equations

Given base UI layout bounding box dimensions $(W_{\text{base}}, H_{\text{base}})$ and padding vectors $\vec{P}_{\text{base}}$, the transformation engine computes scaled bounding geometry without boundary collision:

$$W_{\text{scaled}} = W_{\text{base}} \times \left( 1 + \kappa \cdot (\mathcal{S} - 1) \right)$$

$$H_{\text{scaled}} = H_{\text{base}} \times \left( 1 + \kappa \cdot (\mathcal{S} - 1) \right)$$

$$\vec{P}_{\text{scaled}} = \vec{P}_{\text{base}} \odot \begin{bmatrix} \beta_x \\ \beta_y \end{bmatrix}$$

* $\mathcal{S}$: Font magnification scale factor ($1.0 \le \mathcal{S} \le 2.5$).
* $\kappa$: Layout damping factor ($\kappa = 0.65$) preventing component overlap.
* $\vec{P}_{\text{scaled}}$: Dynamic padding vector maintaining touch-target clearance ($\ge 48\text{dp}$).

---

## 4. Cross-Platform Feature Interoperability

```
+----------------------------------------------------------------------------------------------------+
|                               PERSONA INTEROPERABILITY & MATRIX                                     |
+--------------------------+-----------------------+-----------------------+-------------------------+
| PERSONA OVERLAY          | PRIMARY CHASSIS BASE  | R-SCE ASIC ENGINE     | SYSTEM MEMORY FOOTPRINT |
+--------------------------+-----------------------+-----------------------+-------------------------+
| Gamer Mode               | Platform B (6.9")     | High-Speed Decompress | 180 MB                  |
| Corporate Enterprise     | Platform A (6.4")     | Hardware AES-256 DMA  | 240 MB (Incl. VectorDB) |
| Creator Engine           | Platform B (6.9")     | Live AV1 Transcoder   | 160 MB                  |
| Lifestyle Privacy Guard  | Platform A (6.4")     | EXIF Hash Redactor    | 95 MB                   |
| Senior Vector UI         | Platform A (6.4")     | Geometry Vector Engine| 110 MB                  |
| IM-Chatter               | Platform B (6.9")     | Low-Latency Keep-Alive| 85 MB                   |
+----------------------------------------------------------------------------------------------------+

```

---

## 5. Security & Tamper Resistance

1. **Secure Enclave Ingestion:** PCV masks are written exclusively to write-once-protected register blocks inside the R-SCE ASIC.
2. **Signature Verification:** During boot, the system kernel verifies the 256-bit HMAC-SHA256 signature (`pcv_enclave_provisioner.py`). If signature verification fails, the device reverts to standard Base System mode (`0x00`), disabling demographic feature overlays.
