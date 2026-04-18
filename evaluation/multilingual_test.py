import os
import sys
import json
from dotenv import load_dotenv

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.triage_service import TriageAnalysisService
from models.intake import PatientIntake

load_dotenv()

def test_multilingual():
    triage_service = TriageAnalysisService()
    
    # Tunisian Darija Case (Informal)
    darija_intake = {
        "patient_profile": {"name": "Sami", "age": 29, "sex": "male", "height": 182, "weight": 80},
        "environment": {
            "neighborhood": "Industrial Zone",
            "proximity_to_industrial_zone": "visible_from_home_or_work",
            "occupation": "Tech Support",
            "smoking_status": "current",
            "pollution_observations": ["chemical_smells"]
        },
        "chief_complaint": {
            "main_problem": "عندي وجيعة كبيرة في صدري عندها ساعة و مانيش منجم نتنفس بالباهي",
            "onset": "sudden",
            "duration": "1 hour",
            "severity": 9,
            "progression": "worsening"
        }
    }
    
    results = []
    
    # Tunisian Darija Case
    print("Testing Tunisian Darija (Informal) Input...")
    analysis_ar = triage_service.analyze(PatientIntake(**darija_intake))
    results.append({"lang": "Arabic", "summary": analysis_ar.triage_summary})
    
    # French Case
    french_intake = {
        "patient_profile": {"name": "Marie", "age": 45, "sex": "female", "height": 165, "weight": 60},
        "environment": {
            "neighborhood": "Menzel",
            "proximity_to_industrial_zone": "frequent_chemical_smell",
            "occupation": "Artist",
            "smoking_status": "non-smoker",
            "pollution_observations": ["chemical_smells"]
        },
        "chief_complaint": {
            "main_problem": "J'ai une forte toux sèche et des maux de tête importants.",
            "onset": "gradual",
            "duration": "2 days",
            "severity": 6,
            "progression": "stable"
        }
    }
    
    # Arabic Case
    print("Testing Arabic Input...")
    analysis_fr = triage_service.analyze(PatientIntake(**french_intake))
    results.append({"lang": "French", "summary": analysis_fr.triage_summary})

    with open("evaluation/multilingual_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\nMultilingual test complete. View results in evaluation/multilingual_results.json")

if __name__ == "__main__":
    test_multilingual()
