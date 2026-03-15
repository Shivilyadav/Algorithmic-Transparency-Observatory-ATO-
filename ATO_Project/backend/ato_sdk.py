import json
import uuid
import datetime
import os
import sys

# Add the backend directory to path if trying to run from another directory,
# so ato_db can be imported correctly. 
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

import ato_db

def log_decision(model_name: str, sector: str, demographic_group: str, demographic_tag: str, 
                 outcome: int, score: float, features: dict, feature_importance: dict,
                 logic_steps: list = None, has_alert: int = 0, alert_reason: str = ""):
    """
    Log a real AI decision into the Algorithmic Transparency Observatory.
    
    Args:
        model_name: Ex - 'XGBoost Credit Scorer'
        sector: Ex - 'Finance'
        demographic_group: Ex - 'Age' or 'Race'
        demographic_tag: Ex - '18-25' or 'Group A'
        outcome: 1 for Approved/Positive, 0 for Rejected/Negative
        score: The raw probability or calculated score (0.0 to 1.0)
        features: dict of feature names to input values used for this decision
        feature_importance: dict of feature names to their mathematical importance (e.g., from SHAP)
        logic_steps: list of string steps explaining the AI's internal process
        has_alert: 1 if model flagged its own confidence/bias, 0 otherwise
        alert_reason: Human-readable string for why the alert fired
        
    Returns:
        The generated decision ID.
    """
    
    dec_id = "REAL-" + str(uuid.uuid4()).split('-')[0].upper()
    timestamp = datetime.datetime.now().isoformat()
    logic_steps_json = json.dumps(logic_steps) if logic_steps else "[]"
    
    try:
        conn = ato_db.get_connection()
        c = conn.cursor()
        
        # 1. Log the core decision
        c.execute("""
            INSERT INTO decisions 
            (id, model_name, sector, timestamp, demographic_group, demographic_tag, outcome, score, has_alert, alert_reason, logic_steps)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (dec_id, model_name, sector, timestamp, demographic_group, demographic_tag, outcome, score, has_alert, alert_reason, logic_steps_json))
        
        # 2. Log the local interpretability/explainability metrics
        for feature, weight in feature_importance.items():
            input_val = features.get(feature, 0.0)
            c.execute("""
                INSERT INTO feature_importance
                (decision_id, feature_name, importance_weight, input_value)
                VALUES (?, ?, ?, ?)
            """, (dec_id, feature, weight, input_val))
            
        conn.commit()
        return dec_id
        
    except Exception as e:
        print(f"[ATO SDK ERROR] Failed to log decision: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()
