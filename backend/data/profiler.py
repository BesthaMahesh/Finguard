from typing import Dict, Any
import pandas as pd
import numpy as np

class DataProfiler:
    """
    Generates high-level statistical profile and distribution summaries of transaction data.
    """

    @staticmethod
    def profile_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        total_rows = len(df)
        fraud_count = int(df["isFraud"].sum()) if "isFraud" in df.columns else 0
        fraud_ratio = round(fraud_count / max(1, total_rows), 5)
        
        type_breakdown = {}
        if "type" in df.columns:
            type_counts = df["type"].value_counts().to_dict()
            type_breakdown = {k: int(v) for k, v in type_counts.items()}

        amount_stats = {}
        if "amount" in df.columns:
            amount_stats = {
                "min": round(float(df["amount"].min()), 2),
                "max": round(float(df["amount"].max()), 2),
                "mean": round(float(df["amount"].mean()), 2),
                "median": round(float(df["amount"].median()), 2),
                "p95": round(float(df["amount"].quantile(0.95)), 2),
            }

        step_range = {
            "min_step": int(df["step"].min()) if "step" in df.columns else 1,
            "max_step": int(df["step"].max()) if "step" in df.columns else 1,
            "total_simulated_days": round((int(df["step"].max()) if "step" in df.columns else 1) / 24, 1)
        }

        # Fraud rate by type
        fraud_by_type = {}
        if "type" in df.columns and "isFraud" in df.columns:
            grouped = df.groupby("type")["isFraud"].agg(["count", "sum"])
            for t, row in grouped.iterrows():
                fraud_by_type[str(t)] = {
                    "total": int(row["count"]),
                    "fraud_count": int(row["sum"]),
                    "fraud_rate": round(float(row["sum"] / max(1, row["count"])), 4)
                }

        return {
            "total_transactions": total_rows,
            "total_frauds": fraud_count,
            "fraud_rate_pct": round(fraud_ratio * 100, 3),
            "type_distribution": type_breakdown,
            "fraud_by_type": fraud_by_type,
            "amount_statistics": amount_stats,
            "step_range": step_range,
            "source_dataset": "PaySim Financial Synthetic Log"
        }
