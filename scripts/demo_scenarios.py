"""
FinGuard Live Demo Scenario Runner
Allows presenters to inject and score 3 distinct real-world financial risk scenarios live on demand:
1. Low-Risk Routine Merchant Payment (Fast-Tracked, 0 LLM latency)
2. High-Risk Account Takeover & Rapid Liquidation (Full 9-Agent Deep Forensic Path)
3. Structured Pass-Through Mule Transfer (Regulatory Rule Flags & Grounded Citations)
"""

import sys
import os
import argparse
import json

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.schemas.risk import RiskAnalyzeRequest
from backend.api.v1.endpoints.risk import analyze_transaction_risk

DEMO_SCENARIOS = {
    "1": {
        "name": "Scenario 1: Low-Risk Routine Merchant Payment",
        "description": "Benign merchant payment with adequate residual balance.",
        "payload": {
            "type": "PAYMENT",
            "amount": 28.50,
            "name_orig": "C1928374650",
            "old_balance_org": 4200.00,
            "new_balance_orig": 4171.50,
            "name_dest": "M9876543210",
            "old_balance_dest": 0.0,
            "new_balance_dest": 0.0,
            "use_multi_agent": True
        }
    },
    "2": {
        "name": "Scenario 2: High-Risk Account Takeover & Rapid Liquidation",
        "description": "Account completely drained to 0 in a single wire transfer to unverified counterparty.",
        "payload": {
            "type": "TRANSFER",
            "amount": 350000.00,
            "name_orig": "C1004928172",
            "old_balance_org": 350000.00,
            "new_balance_orig": 0.00,
            "name_dest": "C9988776655",
            "old_balance_dest": 0.00,
            "new_balance_dest": 0.00,
            "use_multi_agent": True
        }
    },
    "3": {
        "name": "Scenario 3: Structuring / Smurfing & High-Velocity Mule Transfer",
        "description": "Wire transfer structured just beneath standard $10,000 reporting threshold with zero destination balance.",
        "payload": {
            "type": "TRANSFER",
            "amount": 9950.00,
            "name_orig": "C3344556677",
            "old_balance_org": 10000.00,
            "new_balance_orig": 50.00,
            "name_dest": "C8877665544",
            "old_balance_dest": 0.00,
            "new_balance_dest": 0.00,
            "use_multi_agent": True
        }
    }
}

def run_scenario(scenario_key: str):
    if scenario_key not in DEMO_SCENARIOS:
        print(f"Invalid scenario '{scenario_key}'. Choose 1, 2, or 3.")
        return

    sc = DEMO_SCENARIOS[scenario_key]
    print("\n" + "=" * 70)
    print(f"  EXECUTING {sc['name'].upper()}")
    print(f"  Description: {sc['description']}")
    print("=" * 70)

    req = RiskAnalyzeRequest(**sc["payload"])
    user = {"username": "live_presenter", "role": "analyst"}

    print("\n[FinGuard] Dispatching to LangGraph Orchestration Plane...")
    response = analyze_transaction_risk(req, current_user=user)

    print("\n" + "-" * 70)
    print("  ORCHESTRATION RESULT & EVALUATION")
    print("-" * 70)
    print(f"  Composite Risk Score:     {response.risk_score} / 100")
    print(f"  Operational Risk Level:   {response.risk_level}")
    print(f"  ML Fraud Probability:    {response.fraud_probability:.4f}")
    print(f"  Requires Human Review:    {'YES (4-Eyes Checkpoint)' if response.requires_human_review else 'NO (Fast-Tracked)'}")
    print(f"  Rule Flags Triggered:     {[r.get('rule_id', r) for r in response.rule_flags] if response.rule_flags else 'None'}")
    
    if response.feature_contributions:
        print("\n  Top TreeSHAP Feature Attributions:")
        for feat in response.feature_contributions[:3]:
            impact_sign = "+" if feat.get("impact") == "INCREASES_RISK" else "-"
            print(f"   • {feat.get('display_name', feat.get('feature_name'))}: {impact_sign}{feat.get('absolute_impact', 0):.2f}")

    if response.policy_citations:
        print("\n  Retrieved Regulatory Policy Citations (ChromaDB RAG):")
        for cit in response.policy_citations[:2]:
            print(f"   • {cit.get('document_id')} ({cit.get('section')}): Relevance {int(cit.get('relevance_score', 0) * 100)}%")

    print("\n  Agent Workflow Timeline:")
    for step in (response.workflow_timeline or []):
        print(f"   [{step.get('status')}] {step.get('agent')}: {step.get('duration_ms')}ms")

    print("\n" + "=" * 70)
    print("  Scenario execution completed successfully.")
    print("=" * 70 + "\n")

def main():
    parser = argparse.ArgumentParser(description="FinGuard Live Demo Scenario Runner")
    parser.add_argument("--scenario", "-s", choices=["1", "2", "3"], default=None,
                        help="Select scenario: 1 (Low-Risk), 2 (Critical Takeover), 3 (Structuring)")
    args = parser.parse_args()

    if args.scenario:
        run_scenario(args.scenario)
    else:
        print("\n========================================================")
        print("  FinGuard Live Scenario Selector")
        print("========================================================")
        print("1. Scenario 1: Low-Risk Routine Merchant Payment ($28.50)")
        print("2. Scenario 2: Critical Account Takeover & Liquidation ($350,000)")
        print("3. Scenario 3: Structuring & Mule Transfer ($9,950)")
        print("========================================================")
        choice = input("Enter scenario number (1, 2, or 3) [default: 2]: ").strip() or "2"
        run_scenario(choice)

if __name__ == "__main__":
    main()

