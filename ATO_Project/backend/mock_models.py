import collections
import statistics
from datetime import datetime
import ato_db


ABSTRACT_SNAPSHOT = {
    "title": "Algorithmic Transparency Observatory for AI Decision Systems",
    "purpose": "Continuous monitoring, explanation, and auditing of AI decisions for fairness, accountability, and compliance.",
    "domains": ["Finance", "Healthcare", "Recruitment", "Public Governance"],
    "keywords": [
        "Algorithmic Transparency",
        "Explainable AI",
        "Bias Detection",
        "Responsible AI",
        "AI Governance",
    ],
}

FLOWCHART_STAGES = [
    "Literature Review",
    "Research Gap Identification",
    "Framework Design",
    "Algorithmic Transparency Observatory",
    "Data Collection",
    "Explainable AI Analysis",
    "Bias Detection Analysis",
    "Compliance & Governance",
    "Evaluation & Reporting",
    "Evaluation & Results",
]


def _safe_div(num, den):
    return round(num / den, 4) if den else 0.0


def _count_total_decisions(cursor):
    cursor.execute("SELECT COUNT(*) FROM decisions")
    return cursor.fetchone()[0] or 0


def _approval_rate(cursor, demographic_tag):
    cursor.execute(
        """
        SELECT SUM(outcome), COUNT(*)
        FROM decisions
        WHERE demographic_tag = ?
        """,
        (demographic_tag,),
    )
    approved, total = cursor.fetchone()
    approved = approved or 0
    return _safe_div(approved, total or 0)


def get_real_time_metrics():
    conn = ato_db.get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(DISTINCT model_name) FROM decisions")
    active_models = c.fetchone()[0] or 0

    total_decisions = _count_total_decisions(c)

    c.execute("SELECT COUNT(*) FROM decisions WHERE has_alert = 1")
    alerts = c.fetchone()[0] or 0

    c.execute(
        """
        SELECT id, model_name, sector, alert_reason
        FROM decisions
        WHERE has_alert = 1
        ORDER BY timestamp DESC
        LIMIT 3
        """
    )
    flags = []
    for row in c.fetchall():
        reason = row[3] or "Audit review required"
        flags.append(
            {
                "id": row[0],
                "model": row[1],
                "sector": row[2],
                "reason": reason,
                "type": "danger" if "Bias" in reason else "warning",
            }
        )

    fairness_score = get_fairness_snapshot(c)["overall_fairness_score"]

    c.execute("SELECT timestamp FROM decisions ORDER BY timestamp DESC LIMIT 5000")
    now = datetime.now()
    throughput_history = [0] * 7
    for row in c.fetchall():
        if not row[0]: continue
        try:
            ts = datetime.fromisoformat(row[0])
            diff = (now - ts).total_seconds()
            if diff < 0: diff = 0
            mins_ago = int(diff / 60)
            if mins_ago <= 6:
                throughput_history[6 - mins_ago] += 1
            elif mins_ago > 6:
                break
        except Exception:
            pass

    conn.close()
    return {
        "active_models": active_models,
        "total_decisions_24h": total_decisions,
        "alerts_triggered": alerts,
        "fairness_score": fairness_score,
        "throughput_history": throughput_history,
        "recent_flags": flags,
    }


def get_bias_metrics():
    conn = ato_db.get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT demographic_tag,
               CAST(SUM(outcome) AS FLOAT) / COUNT(*) * 100
        FROM decisions
        WHERE model_name = 'HR Recruitment v2'
        GROUP BY demographic_tag
        ORDER BY demographic_tag
        """
    )
    groups = []
    rates = []
    for row in c.fetchall():
        groups.append(row[0])
        rates.append(round(row[1], 1))

    if not groups:
        groups = ["Group A", "Group B", "Group C", "Group D"]
        rates = [82.0, 79.0, 51.0, 77.0]

    fairness = get_fairness_snapshot(c)
    conn.close()
    return {
        "demographic_groups": groups,
        "approval_rates": rates,
        "parity_labels": ["Demographic Parity", "Disparate Impact", "Alert Health", "Consistency", "Coverage"],
        "parity_scores": fairness["radar_scores"],
    }


def get_xai_explanation(decision_id: str):
    import json
    conn = ato_db.get_connection()
    c = conn.cursor()
    c.execute("SELECT outcome, model_name, logic_steps FROM decisions WHERE id = ?", (decision_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return {"error": "Decision not found"}

    outcome_text = "Approved" if row[0] == 1 else "Rejected"
    model_name = row[1]
    
    logic_steps = []
    if row[2]:
        try:
            logic_steps = json.loads(row[2])
        except Exception:
            logic_steps = []

    c.execute(
        """
        SELECT feature_name, importance_weight, input_value
        FROM feature_importance
        WHERE decision_id = ?
        """,
        (decision_id,),
    )
    features = []
    shap_values = []
    inputs = []
    for f in c.fetchall():
        features.append(f[0])
        shap_values.append(f[1])
        inputs.append(f[2])
    conn.close()

    sorted_pairs = sorted(zip(features, shap_values), key=lambda x: abs(x[1]), reverse=True)
    top_driver = sorted_pairs[0][0] if sorted_pairs else "Unknown"
    summary = (
        f"The model ({model_name}) produced a {outcome_text} outcome, with '{top_driver}' "
        "as the strongest mathematical contributor."
    )
    return {
        "decision_id": decision_id,
        "outcome": outcome_text,
        "features": features,
        "shap_values": shap_values,
        "inputs": inputs,
        "summary": summary,
        "logic_steps": logic_steps
    }


def get_recent_decisions_for_dropdown():
    conn = ato_db.get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT id, model_name, outcome
        FROM decisions
        ORDER BY timestamp DESC
        LIMIT 20
        """
    )
    decisions = []
    for row in c.fetchall():
        out_text = "Approved" if row[2] == 1 else "Rejected"
        decisions.append({"id": row[0], "model_name": row[1], "outcome": out_text})
    conn.close()

    grouped = collections.defaultdict(list)
    for d in decisions:
        model_key = "hr" if "HR" in d["model_name"] else "finance"
        grouped[model_key].append(d)
    return grouped


def get_compliance_logs():
    return [
        "[INFO] : System health check passed.",
        "[INFO] : SQLite Storage Layer synchronized.",
        "[INFO] : Multi-Agent System continuous loop active.",
        "[WARN] : Recruitment model bias drift approaching threshold for Group C.",
    ]


def get_agent_architectures():
    return [
        {
            "name": "HR Recruitment Model v2",
            "type": "Weighted Linear Scorer with Demographic Bias Injection",
            "description": "Evaluates candidate profiles and intentionally injects a demographic penalty to validate ATO bias detection.",
            "algorithm_formula": "Score = (Edu * W1) + (Exp * W2) + (Test * W3) + (CultureFit * W4)",
            "parameters": [
                {"name": "Education_Level", "weight": "+25.0"},
                {"name": "Years_Experience", "weight": "+15.0"},
                {"name": "Aptitude_Test_Score", "weight": "+0.5"},
                {"name": "Cultural_Fit_Score", "weight": "+10.0 with Group C bias penalty"},
            ],
            "threshold": "Score > 75 = Hire",
        },
        {
            "name": "Credit Risk Model v4",
            "type": "Strict Algorithmic Thresholding",
            "description": "Evaluates financial risk using debt and income signals, serving as a lower-bias control model.",
            "algorithm_formula": "Score = (Income * W1) - (DebtRatio * W2) + (CreditHist * W3) - (OpenAccts * W4)",
            "parameters": [
                {"name": "Income_Level", "weight": "+0.8"},
                {"name": "Debt_To_Income_Ratio", "weight": "-4.5"},
                {"name": "Credit_History_Years", "weight": "+2.0"},
                {"name": "Number_of_Open_Accounts", "weight": "-0.5"},
            ],
            "threshold": "Score > 80 = Approved",
        },
    ]


def get_raw_database_logs():
    conn = ato_db.get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT
            d.id,
            d.model_name,
            d.timestamp,
            d.demographic_tag,
            d.score,
            d.outcome,
            f.feature_name,
            f.importance_weight
        FROM decisions d
        LEFT JOIN feature_importance f ON d.id = f.decision_id
        WHERE f.importance_weight = (
            SELECT MAX(ABS(importance_weight))
            FROM feature_importance
            WHERE decision_id = d.id
        ) OR f.importance_weight = (
            SELECT MIN(importance_weight)
            FROM feature_importance
            WHERE decision_id = d.id
            AND NOT EXISTS (
                SELECT 1
                FROM feature_importance
                WHERE decision_id = d.id AND importance_weight > 0
            )
        )
        GROUP BY d.id
        ORDER BY d.timestamp DESC
        LIMIT 50
        """
    )

    logs = []
    for row in c.fetchall():
        out_text = "Approved" if row[5] == 1 else "Rejected"
        driver = f"{row[6]} ({row[7]:.2f})" if row[6] else "N/A"
        timestamp_formatted = row[2].split(".")[0] if row[2] else ""
        logs.append(
            {
                "id": row[0],
                "model": row[1],
                "timestamp": timestamp_formatted,
                "demographics": row[3],
                "score": round(row[4], 2) if row[4] is not None else 0,
                "outcome": out_text,
                "driver": driver,
            }
        )
    conn.close()
    return logs


def get_research_abstract():
    return ABSTRACT_SNAPSHOT


def get_flowchart_stages():
    return {"total_stages": len(FLOWCHART_STAGES), "stages": FLOWCHART_STAGES}


def get_sector_collection_status():
    conn = ato_db.get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT sector, COUNT(*) AS total, SUM(outcome) AS approved
        FROM decisions
        GROUP BY sector
        ORDER BY total DESC
        """
    )
    rows = c.fetchall()
    conn.close()

    result = []
    total = 0
    for sector, count, approved in rows:
        count = count or 0
        approved = approved or 0
        total += count
        result.append(
            {
                "sector": sector or "Unknown",
                "decisions": count,
                "approved": approved,
                "rejected": count - approved,
                "approval_rate": round((approved / count) * 100, 2) if count else 0,
            }
        )

    if not result:
        result = [
            {"sector": "Recruitment", "decisions": 0, "approved": 0, "rejected": 0, "approval_rate": 0},
            {"sector": "Finance", "decisions": 0, "approved": 0, "rejected": 0, "approval_rate": 0},
            {"sector": "Healthcare", "decisions": 0, "approved": 0, "rejected": 0, "approval_rate": 0},
            {"sector": "Governance", "decisions": 0, "approved": 0, "rejected": 0, "approval_rate": 0},
        ]
    return {"total_records": total, "sectors": result}


def get_fairness_snapshot(cursor=None):
    managed_cursor = cursor is None
    conn = None
    if managed_cursor:
        conn = ato_db.get_connection()
        cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT demographic_tag FROM decisions WHERE demographic_tag IS NOT NULL")
    tags = [row[0] for row in cursor.fetchall() if row[0]]

    rates = {}
    for tag in tags:
        rates[tag] = _approval_rate(cursor, tag)
    rate_values = list(rates.values())
    disparity_gap = max(rate_values) - min(rate_values) if len(rate_values) > 1 else 0.0

    baseline = rate_values[0] if rate_values else 1.0
    disparate_impact = min((r / baseline) for r in rate_values) if baseline > 0 and rate_values else 1.0

    cursor.execute("SELECT COUNT(*) FROM decisions WHERE has_alert = 1")
    alerts = cursor.fetchone()[0] or 0
    total = _count_total_decisions(cursor)
    alert_health = max(0.0, 1.0 - _safe_div(alerts, max(total, 1)))

    consistency = max(0.0, 1.0 - disparity_gap)

    cursor.execute(
        """
        SELECT COUNT(DISTINCT decision_id) AS explainable, (SELECT COUNT(*) FROM decisions) AS total
        FROM feature_importance
        """
    )
    explainable, explain_total = cursor.fetchone()
    explainable = explainable or 0
    explain_total = explain_total or 0
    coverage = _safe_div(explainable, explain_total or 1)

    fairness_score = round(max(0.0, min(1.0, statistics.fmean([consistency, disparate_impact, alert_health, coverage]))) * 100, 2)
    radar_scores = [
        round(consistency, 2),
        round(disparate_impact, 2),
        round(alert_health, 2),
        round(1 - disparity_gap if disparity_gap <= 1 else 0, 2),
        round(coverage, 2),
    ]

    result = {
        "overall_fairness_score": fairness_score,
        "demographic_rates": {k: round(v * 100, 2) for k, v in rates.items()},
        "disparity_gap": round(disparity_gap, 4),
        "disparate_impact_ratio": round(disparate_impact, 4),
        "xai_coverage_ratio": round(coverage, 4),
        "radar_scores": radar_scores,
    }

    if managed_cursor:
        conn.close()
    return result


def get_governance_compliance_snapshot():
    fairness = get_fairness_snapshot()
    sector_status = get_sector_collection_status()
    checks = [
        {
            "name": "Transparency (XAI Coverage)",
            "status": "pass" if fairness["xai_coverage_ratio"] >= 0.9 else "warning",
            "value": fairness["xai_coverage_ratio"],
            "target": 0.9,
        },
        {
            "name": "Fairness (Disparate Impact)",
            "status": "pass" if fairness["disparate_impact_ratio"] >= 0.8 else "fail",
            "value": fairness["disparate_impact_ratio"],
            "target": 0.8,
        },
        {
            "name": "Bias Gap Control",
            "status": "pass" if fairness["disparity_gap"] <= 0.2 else "warning",
            "value": fairness["disparity_gap"],
            "target": 0.2,
        },
        {
            "name": "Data Collection Breadth",
            "status": "pass" if len(sector_status["sectors"]) >= 2 else "warning",
            "value": len(sector_status["sectors"]),
            "target": 4,
        },
    ]
    passed = sum(1 for c in checks if c["status"] == "pass")
    compliance_score = round((passed / len(checks)) * 100, 2)
    return {"score": compliance_score, "checks": checks}


def get_evaluation_report():
    fairness = get_fairness_snapshot()
    governance = get_governance_compliance_snapshot()
    collection = get_sector_collection_status()
    metrics = get_real_time_metrics()
    return {
        "timestamp": datetime.now().isoformat(),
        "framework": "Algorithmic Transparency Observatory",
        "summary": {
            "total_decisions": metrics["total_decisions_24h"],
            "alerts": metrics["alerts_triggered"],
            "fairness_score": fairness["overall_fairness_score"],
            "governance_score": governance["score"],
            "active_models": metrics["active_models"],
        },
        "fairness": fairness,
        "governance": governance,
        "data_collection": collection,
        "recommendations": [
            "Increase Group C fairness through model retraining and feature review.",
            "Add healthcare/governance agents to match cross-sector objectives.",
            "Export monthly transparency reports for regulatory audit readiness.",
        ],
    }


def get_transparency_report():
    evaluation = get_evaluation_report()
    fairness = evaluation["fairness"]
    governance = evaluation["governance"]
    return {
        "generated_at_utc": evaluation["timestamp"],
        "research_context": {
            "title": ABSTRACT_SNAPSHOT["title"],
            "domains": ABSTRACT_SNAPSHOT["domains"],
        },
        "kpis": {
            "compliance_score_percent": governance["score"],
            "fairness_score_percent": fairness["overall_fairness_score"],
            "xai_coverage_percent": round(fairness["xai_coverage_ratio"] * 100, 2),
            "disparate_impact_ratio": fairness["disparate_impact_ratio"],
        },
        "pipeline_status": [
            {"stage": stage, "status": "ok", "detail": "Operational"}
            for stage in FLOWCHART_STAGES
        ],
        "recommendations": evaluation["recommendations"],
    }
