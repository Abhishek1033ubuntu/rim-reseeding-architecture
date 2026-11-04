"""
RIM Handset Re-Inception: 2-Chassis BOM & Financial Engine
===========================================================
File: models/2_chassis_bom_financial_engine.py
License: Apache-2.0
Description:
    Deterministic P&L modeling engine comparing the Unified 2-Chassis
    Architecture ($7.50 R-SCE ASIC baseline) against an Unconsolidated 7-SKU model.
    Generates component-level BOM breakdowns, CapEx amortizations, and P&L comparative matrices.

Usage:
    python 2_chassis_bom_financial_engine.py --volume 2400000 --asp 285.0
"""

import argparse
import json
from dataclasses import asdict, dataclass, field
from typing import Dict, List


@dataclass
class BOMItem:
    category: str
    description: str
    cost_7sku: float
    cost_unified_asic: float
    is_common: bool = True


@dataclass
class FinancialSummary:
    units_produced: int
    blended_asp: float
    gross_revenue: float
    unit_bom_cost: float
    total_bom_spend: float
    nre_tooling_capex: float
    certification_cost: float
    inventory_scrap_loss: float
    fixed_opex: float
    total_cost: float
    net_operating_profit: float
    operating_margin_pct: float


class TwoChassisFinancialEngine:
    """Calculates component BOMs and operational P&L comparison matrices."""

    def __init__(self, volume: int = 2_400_000, blended_asp: float = 285.0):
        self.volume = volume
        self.blended_asp = blended_asp
        self.bom_items = self._initialize_bom_items()

    def _initialize_bom_items(self) -> List[BOMItem]:
        return [
            BOMItem(
                category="Processing Core",
                description="Main Application Processor (4nm/6nm)",
                cost_7sku=95.00,
                cost_unified_asic=46.00,
                is_common=True,
            ),
            BOMItem(
                category="Proprietary Silicon",
                description="RIM R-SCE 12nm Companion ASIC",
                cost_7sku=0.00,
                cost_unified_asic=7.50,
                is_common=True,
            ),
            BOMItem(
                category="Memory & Storage",
                description="16GB LPDDR5X RAM + 512GB UFS 4.0 Storage",
                cost_7sku=42.00,
                cost_unified_asic=42.00,
                is_common=True,
            ),
            BOMItem(
                category="Display Subsystem",
                description="6.4\" / 6.9\" 120Hz LTPO AMOLED Panel",
                cost_7sku=28.00,
                cost_unified_asic=28.00,
                is_common=False,
            ),
            BOMItem(
                category="Power Management",
                description="5500mAh Silicon-Carbon Cell + 67W PMIC",
                cost_7sku=14.00,
                cost_unified_asic=14.00,
                is_common=True,
            ),
            BOMItem(
                category="Optics & Imaging",
                description="50MP Main OIS + Ultra-Wide Sensor Assembly",
                cost_7sku=24.00,
                cost_unified_asic=24.00,
                is_common=True,
            ),
            BOMItem(
                category="Mechanical Housing",
                description="Platform A/B Structural Enclosure & Glass",
                cost_7sku=16.00,
                cost_unified_asic=16.00,
                is_common=False,
            ),
            BOMItem(
                category="Thermal & Circuitry",
                description="Dual Vapor Chamber & 12-layer HDI PCB Base",
                cost_7sku=9.00,
                cost_unified_asic=9.00,
                is_common=True,
            ),
            BOMItem(
                category="Manufacturing & Test",
                description="Assembly, SMT 6-Gate Inspection & Provisioning",
                cost_7sku=7.00,
                cost_unified_asic=8.00,
                is_common=True,
            ),
        ]

    def compute_bom_summary(self) -> Dict[str, float]:
        unit_bom_7sku = sum(item.cost_7sku for item in self.bom_items)
        unit_bom_unified = sum(item.cost_unified_asic for item in self.bom_items)
        return {
            "unit_bom_7sku": unit_bom_7sku,
            "unit_bom_unified_asic": unit_bom_unified,
            "unit_bom_savings": unit_bom_7sku - unit_bom_unified,
            "unit_bom_savings_pct": ((unit_bom_7sku - unit_bom_unified) / unit_bom_7sku) * 100.0,
        }

    def run_financial_model(self) -> Dict[str, FinancialSummary]:
        bom = self.compute_bom_summary()
        gross_revenue = self.volume * self.blended_asp

        # --- Scenario A: Unconsolidated 7-SKU Model ---
        bom_spend_7sku = self.volume * bom["unit_bom_7sku"]
        tooling_capex_7sku = 7 * 8_500_000.0  # $59.50M
        cert_cost_7sku = 7 * 2_800_000.0     # $19.60M
        scrap_loss_7sku = 0.06 * bom_spend_7sku  # 6.0% inventory mismatch loss
        fixed_opex_7sku = 25_000_000.0
        total_cost_7sku = tooling_capex_7sku + bom_spend_7sku + cert_cost_7sku + scrap_loss_7sku + fixed_opex_7sku
        net_profit_7sku = gross_revenue - total_cost_7sku

        scenario_7sku = FinancialSummary(
            units_produced=self.volume,
            blended_asp=self.blended_asp,
            gross_revenue=gross_revenue,
            unit_bom_cost=bom["unit_bom_7sku"],
            total_bom_spend=bom_spend_7sku,
            nre_tooling_capex=tooling_capex_7sku,
            certification_cost=cert_cost_7sku,
            inventory_scrap_loss=scrap_loss_7sku,
            fixed_opex=fixed_opex_7sku,
            total_cost=total_cost_7sku,
            net_operating_profit=net_profit_7sku,
            operating_margin_pct=(net_profit_7sku / gross_revenue) * 100.0,
        )

        # --- Scenario B: Unified 2-Chassis Architecture (+ $7.50 ASIC) ---
        bom_spend_unified = self.volume * bom["unit_bom_unified_asic"]
        tooling_capex_unified = 22_500_000.0 + 19_000_000.0  # $22.5M ASIC NRE + $19M Tooling
        cert_cost_unified = 7_200_000.0                      # $7.20M unified certs
        scrap_loss_unified = 0.015 * bom_spend_unified       # 1.5% low-DPMO scrap loss
        fixed_opex_unified = 25_000_000.0
        total_cost_unified = tooling_capex_unified + bom_spend_unified + cert_cost_unified + scrap_loss_unified + fixed_opex_unified
        net_profit_unified = gross_revenue - total_cost_unified

        scenario_unified = FinancialSummary(
            units_produced=self.volume,
            blended_asp=self.blended_asp,
            gross_revenue=gross_revenue,
            unit_bom_cost=bom["unit_bom_unified_asic"],
            total_bom_spend=bom_spend_unified,
            nre_tooling_capex=tooling_capex_unified,
            certification_cost=cert_cost_unified,
            inventory_scrap_loss=scrap_loss_unified,
            fixed_opex=fixed_opex_unified,
            total_cost=total_cost_unified,
            net_operating_profit=net_profit_unified,
            operating_margin_pct=(net_profit_unified / gross_revenue) * 100.0,
        )

        return {
            "unconsolidated_7sku": scenario_7sku,
            "unified_2chassis_asic": scenario_unified,
        }


def main():
    parser = argparse.ArgumentParser(description="RIM 2-Chassis Financial Model Engine")
    parser.add_argument("--volume", type=int, default=2_400_000, help="Year 1 Target Volume")
    parser.add_argument("--asp", type=float, default=285.0, help="Blended Average Selling Price")
    parser.add_argument("--output-json", type=str, default="models/financial_summary.json", help="Export summary path")
    args = parser.parse_args()

    engine = TwoChassisFinancialEngine(volume=args.volume, blended_asp=args.asp)
    results = engine.run_financial_model()
    bom = engine.compute_bom_summary()

    print("\n" + "=" * 75)
    print("         2-CHASSIS UNIFIED ARCHITECTURE P&L FINANCIAL SUMMARY")
    print("=" * 75)
    print(f"Target Production Volume : {args.volume:,} units")
    print(f"Blended Selling Price    : ${args.asp:.2f}")
    print(f"Unit BOM (7-SKU Model)   : ${bom['unit_bom_7sku']:.2f}")
    print(f"Unit BOM (Unified ASIC)  : ${bom['unit_bom_unified_asic']:.2f}  (Savings: ${bom['unit_bom_savings']:.2f} / unit)")
    print("-" * 75)
    
    u = results["unified_2chassis_asic"]
    s = results["unconsolidated_7sku"]
    
    print(f"{'METRIC':<30} | {'UNCONSOLIDATED 7-SKU':<20} | {'UNIFIED 2-CHASSIS + ASIC':<20}")
    print("-" * 75)
    print(f"{'Gross Revenue':<30} | ${s.gross_revenue / 1e6:>18.2f}M | ${u.gross_revenue / 1e6:>18.2f}M")
    print(f"{'NRE & Tooling CapEx':<30} | ${s.nre_tooling_capex / 1e6:>18.2f}M | ${u.nre_tooling_capex / 1e6:>18.2f}M")
    print(f"{'Production BOM Spend':<30} | ${s.total_bom_spend / 1e6:>18.2f}M | ${u.total_bom_spend / 1e6:>18.2f}M")
    print(f"{'Inventory Scrap Loss':<30} | ${s.inventory_scrap_loss / 1e6:>18.2f}M | ${u.inventory_scrap_loss / 1e6:>18.2f}M")
    print(f"{'Total Operating Cost':<30} | ${s.total_cost / 1e6:>18.2f}M | ${u.total_cost / 1e6:>18.2f}M")
    print("-" * 75)
    print(f"{'Net Operating Profit':<30} | ${s.net_operating_profit / 1e6:>18.2f}M | ${u.net_operating_profit / 1e6:>18.2f}M")
    print(f"{'Operating Profit Margin':<30} | {s.operating_margin_pct:>19.2f}% | {u.operating_margin_pct:>19.2f}%")
    print("=" * 75 + "\n")

    json_export = {
        "bom_summary": bom,
        "unconsolidated_7sku": asdict(s),
        "unified_2chassis_asic": asdict(u),
    }
    with open(args.output_json, "w") as f:
        json.dump(json_export, f, indent=2)
    print(f"[+] Financial summary export written to {args.output_json}")


if __name__ == "__main__":
    main()
