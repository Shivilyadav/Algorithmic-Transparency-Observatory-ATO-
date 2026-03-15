import time
import random
import ato_sdk

def run_real_ai_demo():
    print("Starting Real AI Integration Demo...")
    print("This script simulates a real, standalone AI service that makes decisions.")
    print("It computes feature importance locally and pushes it to the ATO Dashboard via the Python SDK.")
    print("-" * 50)
    
    # 1. Define our "Real" Model Architecture
    model_name = "Production Scoring Engine v1.0"
    sector = "Governance"
    
    # Simple linear weights for demonstration, but this could be a loaded XGBoost or PyTorch model
    model_weights = {
        "Public_Engagement": 1.5,
        "Policy_Alignment": 2.0,
        "Budget_Efficiency": 0.8,
        "Risk_Factor": -1.2
    }
    
    decisions_count = 0
    try:
        while True:
            # 2. Get Real-time Input Features (Simulated incoming API request)
            features = {
                "Public_Engagement": random.uniform(10, 100),
                "Policy_Alignment": random.uniform(10, 100),
                "Budget_Efficiency": random.uniform(10, 100),
                "Risk_Factor": random.uniform(0, 50)
            }
            
            demographic_group = "Region"
            demographic_tag = random.choice(["North", "South", "East", "West"])
            
            logic_steps = [
                f"1. Initialization: Received new application from {demographic_tag} region.",
                "2. Feature Loading: Extracted Public Engagement, Policy Alignment, Budget Efficiency, and Risk Factor.",
                "3. Scoring Matrix: Initialized base score to 0.0"
            ]
            
            # 3. Compute Prediction (the "Inference" step)
            raw_score = 0
            feature_importance = {}
            for fname, val in features.items():
                weight = model_weights[fname]
                contribution = weight * (val / 100.0) # Normalized feature contribution
                raw_score += contribution
                feature_importance[fname] = contribution
                logic_steps.append(f" - Applied '{fname}' weight ({weight}): Score adjusted by {contribution:+.2f}")
                
            # Convert raw score to probability [0, 1]
            prob = max(min(raw_score / 4.0, 1.0), 0.0)
            logic_steps.append(f"4. Normalization: Raw score bounds mapped to probability {prob:.2f}")
            
            outcome = 1 if prob > 0.6 else 0
            logic_steps.append(f"5. Thresholding: Threshold is > 0.60. Probability is {prob:.2f}. Engine concluded {'Approved' if outcome else 'Rejected'}")
            
            # 4. Self-Monitoring / Alert Logic
            has_alert = 0
            alert_reason = ""
            if feature_importance.get("Risk_Factor", 0) < -0.5 and outcome == 0:
                has_alert = 1
                alert_reason = "High Sensitivity to Risk Factor detected"
                logic_steps.append(f"6. Compliance Check: [ALERT] Rejection heavily influenced by high sensitivity to Risk Factor.")
            else:
                logic_steps.append(f"6. Compliance Check: Internal constraints satisfied.")
                
            # 5. Log directly to the ATO Dashboard via SDK
            dec_id = ato_sdk.log_decision(
                model_name=model_name,
                sector=sector,
                demographic_group=demographic_group,
                demographic_tag=demographic_tag,
                outcome=outcome,
                score=prob,
                features=features,
                feature_importance=feature_importance,
                logic_steps=logic_steps,
                has_alert=has_alert,
                alert_reason=alert_reason
            )
            
            decisions_count += 1
            print(f"[{decisions_count}] Processed {demographic_tag} application. Outcome: {'Approved' if outcome else 'Rejected'}. Logged as {dec_id}.")
            
            time.sleep(random.uniform(1.0, 3.0)) # Real apps don't process exactly every X seconds
            
    except KeyboardInterrupt:
        print("\nDemo stopped by user.")

if __name__ == "__main__":
    run_real_ai_demo()
