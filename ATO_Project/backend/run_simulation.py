import time
import random
import ato_db
from simulated_agents import HRRecruitmentAgent, CreditRiskAgent, HealthcareTriageAgent

def run_simulation(duration_seconds=30):
    print("Initializing Multi-Agent ATO Simulation Environment...")
    ato_db.init_db()
    
    hr_agent = HRRecruitmentAgent()
    finance_agent = CreditRiskAgent()
    health_agent = HealthcareTriageAgent()

    print("--- SIMULATION STARTED ---")
    start_time = time.time()
    
    while time.time() - start_time < duration_seconds:
        # 1. Randomize Applicant Demographics
        demographic_groups = ["Group A", "Group B", "Group C", "Group D"]
        d_tag = random.choice(demographic_groups)
        
        # 2. Randomize Applicant Features for HR
        hr_features = {
            "Years_Experience": random.uniform(0.0, 15.0),
            "Education_Level": random.uniform(1.0, 10.0),
            "Skill_Test_Score": random.uniform(40.0, 100.0),
            "Cultural_Fit": random.uniform(10.0, 100.0) # Base fit before bias
        }
        
        # 3. Randomize Applicant Features for Finance
        fin_features = {
            "Income_Level": random.uniform(30000, 150000) / 1000.0, # in K
            "Credit_History_Years": random.uniform(1.0, 25.0),
            "Debt_To_Income_Ratio": random.uniform(0.1, 0.8),
            "Number_of_Open_Accounts": random.randint(1, 10)
        }
        
        # 4. Randomize Applicant Features for Healthcare
        health_features = {
            "Severity_Score": random.uniform(20.0, 100.0),
            "Vitals_Stability": random.uniform(10.0, 100.0),
            "Resource_Availability": random.uniform(1.0, 10.0),
            "Age_Factor": random.uniform(18.0, 90.0)
        }
        
        # Trigger Agents
        hr_agent.predict(hr_features, "Demographic", d_tag)
        finance_agent.predict(fin_features, "Demographic", d_tag)
        health_agent.predict(health_features, "Demographic", d_tag)
        
        print(f"Processed 3 Candidates for {d_tag}")
        time.sleep(random.uniform(0.5, 2.0)) # Simulate real-time arrival
        
    print("--- SIMULATION COMPLETE ---")

if __name__ == "__main__":
    # Run continuously to generate live data streams
    while True:
        try:
            run_simulation(60) # Generate data continuously in 60s batches
        except KeyboardInterrupt:
            print("Simulation Halted by User.")
            break
