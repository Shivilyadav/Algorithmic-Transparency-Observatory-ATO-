from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mock_models

app = FastAPI(title="ATO API", description="Backend for the Algorithmic Transparency Observatory")

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "System Online", "version": "1.0.0"}

@app.get("/api/dashboard/metrics")
def get_dashboard_metrics():
    return mock_models.get_real_time_metrics()

@app.get("/api/bias/analytics")
def get_bias_analytics():
    return mock_models.get_bias_metrics()

@app.get("/api/xai/explain/{decision_id}")
def get_explanation(decision_id: str):
    return mock_models.get_xai_explanation(decision_id)

@app.get("/api/compliance/logs")
def get_audit_logs():
    return {"logs": mock_models.get_compliance_logs()}

@app.get("/api/decisions/recent")
def get_recent_decisions():
    return mock_models.get_recent_decisions_for_dropdown()

@app.get("/api/database/raw")
def get_raw_database():
    return mock_models.get_raw_database_logs()

@app.get("/api/agents/architectures")
def get_agents():
    return {"architectures": mock_models.get_agent_architectures()}

@app.get("/api/reports/transparency")
def get_transparency():
    return mock_models.get_transparency_report()

@app.get("/api/compliance/report")
def generate_report():
    return mock_models.get_transparency_report()

# Research Lens Endpoints
@app.get("/api/flowchart/stages")
def get_flowchart():
    return mock_models.get_flowchart_stages()

@app.get("/api/governance/compliance")
def get_governance():
    return mock_models.get_governance_compliance_snapshot()

@app.get("/api/data-collection/status")
def get_data_status():
    return mock_models.get_sector_collection_status()

@app.get("/api/evaluation/report")
def get_eval_report():
    return mock_models.get_evaluation_report()

@app.get("/api/fairness/snapshot")
def get_fairness_snapshot():
    return mock_models.get_fairness_snapshot()

if __name__ == "__main__":
    import uvicorn
    # Make sure to run the script inside backend folder: uvicorn main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
