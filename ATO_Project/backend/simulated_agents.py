import ato_db
import random
import uuid
from datetime import datetime

class BaseAIAgent:
    def __init__(self, model_name, sector, base_weights, intercept):
        self.model_name = model_name
        self.sector = sector
        self.base_weights = base_weights
        self.intercept = intercept

    def calculate_score(self, features):
        """Standard Linear Algebra dot-product calculation mimicking ML regression/classification score"""
        score = self.intercept
        contributions = {}
        for feature, value in features.items():
            if feature in self.base_weights:
                weight = self.base_weights[feature] * value
                score += weight
                contributions[feature] = weight
        return score, contributions

    def predict(self, features, demographic_group, demographic_tag):
        # Allow children to override
        score, contributions = self.calculate_score(features)
        
        # Sigmoid activation to get a probability (0 to 1)
        # Assuming score needs normalization for simplistic bounds here
        normalized_score = max(min(score / 100.0, 1.0), 0.0) 
        
        # Decision boundary at 0.5
        outcome = 1 if normalized_score >= 0.5 else 0
        
        # Generate ID
        dec_id = "DEC-" + str(uuid.uuid4()).split('-')[0].upper()
        
        # Self-Monitoring / Alert Logic
        has_alert = 0
        alert_reason = ""
        
        # Basic Outlier checking
        if normalized_score > 0.95 or normalized_score < 0.05:
             has_alert = 1
             alert_reason = "Outlier Score Confidence Detected"
             
        self.log_to_db(dec_id, normalized_score, outcome, demographic_group, demographic_tag, contributions, features, has_alert, alert_reason)

    def log_to_db(self, dec_id, score, outcome, d_group, d_tag, contributions, features, has_alert, alert_reason):
        conn = ato_db.get_connection()
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO decisions 
            (id, model_name, sector, timestamp, demographic_group, demographic_tag, outcome, score, has_alert, alert_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (dec_id, self.model_name, self.sector, datetime.now().isoformat(), d_group, d_tag, outcome, score, has_alert, alert_reason))
        
        for feature, weight in contributions.items():
            input_val = features.get(feature, 0)
            c.execute("""
                INSERT INTO feature_importance
                (decision_id, feature_name, importance_weight, input_value)
                VALUES (?, ?, ?, ?)
            """, (dec_id, feature, weight, input_val))
            
        conn.commit()
        conn.close()

class HRRecruitmentAgent(BaseAIAgent):
    def __init__(self):
        super().__init__(
            model_name="HR Recruitment v2",
            sector="Recruitment",
            base_weights={
                "Years_Experience": 2.5,
                "Education_Level": 5.0,
                "Skill_Test_Score": 1.5,
                "Cultural_Fit": 3.0
            },
            intercept=10.0
        )

    def predict(self, features, demographic_group, demographic_tag):
        # **INTENTIONAL DEMOGRAPHIC BIAS INJECTION FOR ATO TO DETECT**
        # If the demographic tag is 'Group C', artificially lower the Cultural Fit score
        # The ATO dashboard will detect this disparate impact.
        if demographic_group == "Demographic" and demographic_tag == "Group C":
            features["Cultural_Fit"] -= 20.0 # Intentional algorithmic bias
        
        score, contributions = self.calculate_score(features)
        prob = max(min(score / 100.0, 1.0), 0.0)
        outcome = 1 if prob >= 0.6 else 0 # Stricter boundary
        
        has_alert = 0
        alert_reason = ""
        
        # Alert mechanism - flag if cultural fit is deeply negative
        if contributions.get("Cultural_Fit", 0) < -30:
            has_alert = 1
            alert_reason = "Potential Bias: Heavy Negative Cultural Fit Penalty"
            
        dec_id = "DEC-" + str(uuid.uuid4()).split('-')[0].upper()
        self.log_to_db(dec_id, prob, outcome, demographic_group, demographic_tag, contributions, features, has_alert, alert_reason)


class CreditRiskAgent(BaseAIAgent):
    def __init__(self):
        super().__init__(
            model_name="Credit Risk v4",
            sector="Finance",
            base_weights={
                "Income_Level": 0.8,
                "Credit_History_Years": 2.0,
                "Debt_To_Income_Ratio": -4.5,
                "Number_of_Open_Accounts": -0.5
            },
            intercept=40.0
        )

class HealthcareTriageAgent(BaseAIAgent):
    def __init__(self):
        super().__init__(
            model_name="Healthcare Triage Model",
            sector="Healthcare",
            base_weights={
                "Severity_Score": 6.5,
                "Vitals_Stability": 2.0,
                "Resource_Availability": 1.5,
                "Age_Factor": -1.2
            },
            intercept=20.0
        )

    def predict(self, features, demographic_group, demographic_tag):
        # **SUTBLE AGE-BASED BIAS INJECTION**
        # If the demographic is 'Group D' (representing elderly in this simulation), 
        # the model has a hidden bias that lowers triage priority.
        if demographic_group == "Demographic" and demographic_tag == "Group D":
            features["Severity_Score"] -= 15.0 # Hidden bias against elderly priority
        
        score, contributions = self.calculate_score(features)
        prob = max(min(score / 100.0, 1.0), 0.0)
        outcome = 1 if prob >= 0.5 else 0 # Priority Triage
        
        has_alert = 0
        alert_reason = ""
        
        # Alert if age factor is the primary reason for rejection
        if contributions.get("Age_Factor", 0) < -10 and outcome == 0:
            has_alert = 1
            alert_reason = "High Sensitivity to Age detected in Triage decision"
            
        dec_id = "DEC-" + str(uuid.uuid4()).split('-')[0].upper()
        self.log_to_db(dec_id, prob, outcome, demographic_group, demographic_tag, contributions, features, has_alert, alert_reason)
