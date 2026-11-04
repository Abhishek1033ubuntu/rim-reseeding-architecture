"""
RIM Handset Re-Inception: Monte Carlo Product Launch Simulation Engine
======================================================================
File: models/monte_carlo_launch_sim.py
License: Apache-2.0
Description:
    Vectorized Monte Carlo simulation engine evaluating Year 1 market penetration,
    carrier subsidy feedback loops, dynamic pricing elasticity, unit economics,
    and net operating profit distributions across 100,000 trial runs.

Usage:
    python monte_carlo_launch_sim.py --iterations 100000 --target-volume 2400000
"""

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Dict, Tuple

import numpy as np


@dataclass
class SimulationInputs:
    """Input distribution parameters for Monte Carlo trial runs."""
    iterations: int = 100_000
    target_volume_base: float = 2_400_000.0
    blended_asp: float = 285.0
    target_margin: float = 0.2361  # 23.61% baseline target
    
    # TAM parameters (Target Demographics, units/year)
    tam_mean: float = 45_000_000.0
    tam_std: float = 3_500_000.0
    
    # BOM distribution parameters ($)
    bom_min: float = 180.0
    bom_mode: float = 194.50  # Baseline BOM including $7.50 R-SCE ASIC
    bom_max: float = 245.0
    
    # Compression ratio distribution (Payload savings ratio)
    eta_comp_min: float = 0.25
    eta_comp_mode: float = 0.38
    eta_comp_max: float = 0.48
    
    # Carrier subsidy reinvestment fraction distribution
    gamma_sub_min: float = 0.15
    gamma_sub_max: float = 0.45
    
    # Regional ARPU assumptions ($/month)
    arpu_na: float = 58.0
    arpu_eu: float = 32.0
    arpu_in: float = 4.80
    
    # Upfront Fixed Costs & NRE CapEx ($)
    nre_asic_capex: float = 22_500_000.0
    chassis_tooling_capex: float = 19_000_000.0
    certification_cost: float = 7_200_000.0
    fixed_opex: float = 25_000_000.0


class MonteCarloLaunchEngine:
    """Vectorized simulation engine using NumPy distribution sampling."""

    def __init__(self, inputs: SimulationInputs, region_mix: Dict[str, float]):
        self.inputs = inputs
        self.region_mix = region_mix
        self._validate_region_mix()

    def _validate_region_mix(self) -> None:
        total_weight = sum(self.region_mix.values())
        if not np.isclose(total_weight, 1.0):
            raise ValueError(f"Regional mix weights must sum to 1.0 (got {total_weight:.4f})")

    def calculate_weighted_arpu(self) -> float:
        """Calculate global weighted average ARPU based on regional mix."""
        weighted_arpu = (
            self.region_mix.get("NA", 0.0) * self.inputs.arpu_na +
            self.region_mix.get("EU", 0.0) * self.inputs.arpu_eu +
            self.region_mix.get("IN", 0.0) * self.inputs.arpu_in
        )
        return float(weighted_arpu)

    def run(self) -> Dict[str, float]:
        """Execute N Monte Carlo iterations and compute probabilistic metrics."""
        n = self.inputs.iterations
        rng = np.random.default_rng(seed=42)
        
        # 1. Sample TAM (Normal Distribution)
        tam_samples = rng.normal(loc=self.inputs.tam_mean, scale=self.inputs.tam_std, size=n)
        tam_samples = np.maximum(tam_samples, 20_000_000.0)  # Bound lower limit
        
        # 2. Sample BOM (Triangular Distribution)
        bom_samples = rng.triangular(
            left=self.inputs.bom_min,
            mode=self.inputs.bom_mode,
            right=self.inputs.bom_max,
            size=n
        )
        
        # 3. Sample Network Compression Payload Savings Ratio (PERT approximation via Beta)
        a, b, c = self.inputs.eta_comp_min, self.inputs.eta_comp_mode, self.inputs.eta_comp_max
        alpha = 1 + 4 * (b - a) / (c - a)
        beta_param = 1 + 4 * (c - b) / (c - a)
        eta_comp_samples = a + (c - a) * rng.beta(alpha, beta_param, size=n)
        
        # 4. Sample Carrier Subsidy Re-investment Share (Uniform Distribution)
        gamma_sub_samples = rng.uniform(
            low=self.inputs.gamma_sub_min,
            high=self.inputs.gamma_sub_max,
            size=n
        )
        
        # 5. Sample Brand Sentiment Acceleration Factor (Beta Distribution)
        beta_brand_samples = rng.beta(a=2.0, b=5.0, size=n)
        
        # 6. Evaluate Carrier Subsidy & Pricing Dynamics
        weighted_arpu = self.calculate_weighted_arpu()
        carrier_subsidy = eta_comp_samples * gamma_sub_samples * weighted_arpu * 12.0  # Annual savings passed
        effective_retail_price = np.maximum(
            (bom_samples * (1.0 + self.inputs.target_margin)) - carrier_subsidy,
            149.0  # Floor price boundary
        )
        
        # 7. Calculate Price Elasticity & Adoption Rate
        price_ratio = self.inputs.blended_asp / effective_retail_price
        price_elasticity_factor = np.power(price_ratio, 1.35)
        spec_overprovision_multiplier = 1.25  # 16GB RAM + 6000mAh battery bonus
        
        base_adoption_rate = 0.053  # Base 5.3% capture of target niche
        adoption_velocity = (
            base_adoption_rate * price_elasticity_factor * spec_overprovision_multiplier * (1.0 + 0.3 * beta_brand_samples)
        )
        
        # 8. Compute Unit Volume & Financial Results per Iteration
        simulated_units = np.clip(tam_samples * adoption_velocity, 1_000_000.0, 6_000_000.0)
        
        gross_revenue = simulated_units * self.inputs.blended_asp
        total_bom_spend = simulated_units * bom_samples
        inventory_scrap_loss = 0.015 * total_bom_spend  # 1.5% low-DPMO scrap buffer
        
        total_capex = (
            self.inputs.nre_asic_capex +
            self.inputs.chassis_tooling_capex +
            self.inputs.certification_cost
        )
        
        total_operating_cost = total_bom_spend + inventory_scrap_loss + total_capex + self.inputs.fixed_opex
        net_operating_profit = gross_revenue - total_operating_cost
        operating_margin_pct = (net_operating_profit / gross_revenue) * 100.0
        
        # 9. Extract Probability Distribution Metrics
        results = {
            "iterations": n,
            "weighted_arpu_usd": weighted_arpu,
            
            # Unit Volume Percentiles
            "volume_p10_units": float(np.percentile(simulated_units, 10)),
            "volume_p50_units": float(np.percentile(simulated_units, 50)),
            "volume_p90_units": float(np.percentile(simulated_units, 90)),
            
            # Revenue Percentiles ($)
            "revenue_p10_usd": float(np.percentile(gross_revenue, 10)),
            "revenue_p50_usd": float(np.percentile(gross_revenue, 50)),
            "revenue_p90_usd": float(np.percentile(gross_revenue, 90)),
            
            # Net Operating Profit Percentiles ($)
            "profit_p10_usd": float(np.percentile(net_operating_profit, 10)),
            "profit_p50_usd": float(np.percentile(net_operating_profit, 50)),
            "profit_p90_usd": float(np.percentile(net_operating_profit, 90)),
            
            # Operating Margin Percentiles (%)
            "margin_p10_pct": float(np.percentile(operating_margin_pct, 10)),
            "margin_p50_pct": float(np.percentile(operating_margin_pct, 50)),
            "margin_p90_pct": float(np.percentile(operating_margin_pct, 90)),
            
            # Risk Metrics
            "breakeven_probability_pct": float(np.mean(net_operating_profit > 0) * 100.0),
            "target_volume_achievement_prob_pct": float(np.mean(simulated_units >= self.inputs.target_volume_base) * 100.0),
        }
        
        return results


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RIM Product Launch Monte Carlo Simulation Engine"
    )
    parser.add_argument("--iterations", type=int, default=100_000, help="Number of simulation runs")
    parser.add_argument("--target-volume", type=float, default=2_400_000.0, help="Target Year 1 volume")
    parser.add_argument("--region-mix", type=str, default="NA:0.25,EU:0.20,IN:0.55", help="Regional weighting mix")
    parser.add_argument("--output-json", type=str, default="models/sim_results.json", help="Export summary path")
    return parser.parse_args()


def parse_region_mix(mix_str: str) -> Dict[str, float]:
    pairs = mix_str.split(",")
    mix = {}
    for pair in pairs:
        key, val = pair.split(":")
        mix[key.strip().upper()] = float(val.strip())
    return mix


def main():
    args = parse_arguments()
    region_mix = parse_region_mix(args.region_mix)
    
    inputs = SimulationInputs(
        iterations=args.iterations,
        target_volume_base=args.target_volume
    )
    
    engine = MonteCarloLaunchEngine(inputs=inputs, region_mix=region_mix)
    print(f"[*] Running Monte Carlo Launch Engine ({inputs.iterations:,} iterations)...")
    results = engine.run()
    
    print("\n" + "=" * 65)
    print("      MONTE CARLO LAUNCH SIMULATION RESULTS SUMMARY")
    print("=" * 65)
    print(f"Iterations Evaluated          : {results['iterations']:,}")
    print(f"Weighted Regional ARPU        : ${results['weighted_arpu_usd']:.2f} / month")
    print("-" * 65)
    print(f"Unit Volume (P10 / P50 / P90) : {results['volume_p10_units']:,.0f} | {results['volume_p50_units']:,.0f} | {results['volume_p90_units']:,.0f} units")
    print(f"Gross Revenue (P50 Median)    : ${results['revenue_p50_usd'] / 1e6:.2f} Million")
    print(f"Net Operating Profit (P50)    : ${results['profit_p50_usd'] / 1e6:.2f} Million")
    print(f"Operating Margin (P50 Median) : {results['margin_p50_pct']:.2f}%")
    print("-" * 65)
    print(f"Break-Even Probability        : {results['breakeven_probability_pct']:.1f}%")
    print(f"Target Volume Achieved (≥2.4M): {results['target_volume_achievement_prob_pct']:.1f}%")
    print("=" * 65 + "\n")
    
    with open(args.output_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[+] Detailed simulation results saved to {args.output_json}")


if __name__ == "__main__":
    main()
