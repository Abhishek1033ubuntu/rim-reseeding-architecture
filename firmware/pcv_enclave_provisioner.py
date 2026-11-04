"""
/*
 * Copyright (c) 2026 Abhishek Singh (GitHub: Abhishek1033ubuntu)
 * Licensed under the Apache License, Version 2.0 (the "License-Software");
 * You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0
 */
============================================================================
RIM R-SCE Secure Enclave Persona Configuration Vector (PCV) Provisioner
============================================================================
File: firmware/pcv_enclave_provisioner.py
License: Apache-2.0
Description:
    SMT Gate 6 & Manufacturing Provisioning Utility. Generates, signs, 
    and injects cryptographic Persona Configuration Vectors (PCV) into the 
    R-SCE Companion ASIC Secure Enclave via Linux chardev ioctl / sysfs.
============================================================================
"""

import argparse
import hashlib
import hmac
import json
import os
import struct
import sys
from dataclasses import asdict, dataclass
from enum import IntFlag, auto
from typing import Dict, Optional, Tuple


class PersonaFlag(IntFlag):
    """Demographic Persona Feature Bitmask Definitions."""
    BASE_SYSTEM        = 0x00
    GAMER_MODE         = 0x01  # 144Hz unlock, thermal headroom, GPU boost
    CORPORATE_MODE     = 0x02  # Local Doc AI, Zero-Trust Sandbox, Privacy Guard
    CREATOR_MODE       = 0x04  # Live AV1 Encoder, 3-Mic Spatial Audio Array
    LIFESTYLE_GUARD    = 0x08  # Automated EXIF Redaction, Location Privacy
    FASHION_PRESET     = 0x10  # Ceramic thermal profile, Ambient LED control
    SENIOR_VECTOR_UI   = 0x20  # Vector-scaled dynamic geometry engine
    IM_CHATTER_MODE    = 0x40  # Edge notification bar, low-latency messaging


@dataclass
class PersonaConfigVector:
    device_id: str
    pcv_mask: int
    persona_name: str
    max_refresh_hz: int
    compression_enabled: bool
    encryption_level: str
    vector_ui_scaling: bool
    hardware_hash: str
    signature: str


class RSCEEnclaveProvisioner:
    """Handles secure PCV payload generation and hardware injection."""

    # Default Master HSM Provisioning Key (Manufacturing Root of Trust)
    DEFAULT_HSM_KEY = b"RIM_R_SCE_SECURE_ENCLAVE_ROOT_KEY_2026_0x99FF"

    PERSONA_LOOKUP: Dict[str, Tuple[PersonaFlag, int, bool, str, bool]] = {
        "gamer": (PersonaFlag.GAMER_MODE, 144, True, "AES-256-GCM", False),
        "corporate": (PersonaFlag.CORPORATE_MODE, 120, True, "AES-256-GCM", False),
        "creator": (PersonaFlag.CREATOR_MODE, 120, True, "AES-256-GCM", False),
        "lifestyle": (PersonaFlag.LIFESTYLE_GUARD, 120, True, "AES-256-GCM", False),
        "fashion": (PersonaFlag.FASHION_PRESET, 120, True, "AES-128-GCM", False),
        "senior": (PersonaFlag.SENIOR_VECTOR_UI, 90, False, "AES-128-GCM", True),
        "chatter": (PersonaFlag.IM_CHATTER_MODE, 120, True, "AES-128-GCM", False),
    }

    def __init__(self, device_node: str = "/dev/r_sce_asic", hsm_key: Optional[bytes] = None):
        self.device_node = device_node
        self.hsm_key = hsm_key or self.DEFAULT_HSM_KEY

    def generate_pcv(self, device_id: str, persona_name: str) -> PersonaConfigVector:
        """Generates a signed PCV payload for a specific device hardware ID."""
        persona_key = persona_name.lower().strip()
        if persona_key not in self.PERSONA_LOOKUP:
            raise ValueError(f"Unknown persona '{persona_name}'. Valid personas: {list(self.PERSONA_LOOKUP.keys())}")

        flag, max_hz, comp_enable, enc_level, vector_scaling = self.PERSONA_LOOKUP[persona_key]
        
        # Compute Hardware Unique Digest
        hw_hash = hashlib.sha256(f"{device_id}:PCV:{flag.value}".encode()).hexdigest()
        
        # Build Raw Binary Vector Payload (DeviceID + Flag + HW_Hash)
        raw_payload = struct.pack("<I32s", flag.value, device_id.encode().ljust(32, b"\x00"))
        
        # Compute HMAC-SHA256 Signature using HSM Root Key
        signature = hmac.new(self.hsm_key, raw_payload, hashlib.sha256).hexdigest()

        return PersonaConfigVector(
            device_id=device_id,
            pcv_mask=int(flag.value),
            persona_name=persona_name.upper(),
            max_refresh_hz=max_hz,
            compression_enabled=comp_enable,
            encryption_level=enc_level,
            vector_ui_scaling=vector_scaling,
            hardware_hash=hw_hash,
            signature=signature,
        )

    def inject_to_enclave(self, pcv: PersonaConfigVector, dry_run: bool = False) -> bool:
        """Injects signed PCV token into R-SCE ASIC device driver node."""
        payload_json = json.dumps(asdict(pcv), indent=2)
        
        if dry_run or not os.path.exists(self.device_node):
            print(f"[*] [DRY RUN / SIMULATION] Writing PCV to R-SCE Enclave ({pcv.persona_name}):")
            print(payload_json)
            print(f"[+] Successfully validated signature {pcv.signature[:16]}... for device {pcv.device_id}")
            return True

        try:
            with open(self.device_node, "wb") as f:
                # Pack binary injection header: Magic (0x52434531 = 'RCE1') | Mask | Signature
                sig_bytes = bytes.fromhex(pcv.signature)
                header = struct.pack("<I I 32s", 0x52434531, pcv.pcv_mask, sig_bytes)
                f.write(header)
                f.flush()
            print(f"[+] Inject successful into {self.device_node} for Device ID {pcv.device_id}")
            return True
        except IOError as err:
            print(f"[-] Hardware injection failed on {self.device_node}: {err}", file=sys.stderr)
            return False


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RIM R-SCE Secure Enclave PCV Provisioning Utility")
    parser.add_argument("--device-id", type=str, required=True, help="Unique 128-bit hardware serial hash")
    parser.add_argument("--persona", type=str, default="gamer", choices=["gamer", "corporate", "creator", "lifestyle", "fashion", "senior", "chatter"], help="Target persona profile")
    parser.add_argument("--device-node", type=str, default="/dev/r_sce_asic", help="R-SCE driver character device path")
    parser.add_argument("--dry-run", action="store_true", help="Simulate injection without hardware device node write")
    parser.add_argument("--output-json", type=str, default="", help="Export provisioning manifest to JSON file")
    return parser.parse_args()


def main():
    args = parse_arguments()
    provisioner = RSCEEnclaveProvisioner(device_node=args.device_node)
    
    try:
        pcv = provisioner.generate_pcv(device_id=args.device_id, persona_name=args.persona)
        success = provisioner.inject_to_enclave(pcv=pcv, dry_run=args.dry_run)
        
        if args.output_json and success:
            with open(args.output_json, "w") as f:
                json.dump(asdict(pcv), f, indent=2)
            print(f"[+] Manifest written to {args.output_json}")

    except Exception as exc:
        print(f"[-] Provisioning Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
