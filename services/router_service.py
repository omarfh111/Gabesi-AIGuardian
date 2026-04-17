from typing import List, Optional
from models.analysis import TriageAnalysis, SpecialtyScore
from models.router import RouterDecision

class RouterService:
    SUPPORTED_SPECIALTIES = [
        "pneumologist", "cardiologist", "oncologist", 
        "neurologist", "dermatologist", "toxicologist", "generalist"
    ]

    def route(self, analysis: TriageAnalysis) -> RouterDecision:
        # 1. Normalize and Map Variants
        mapping = {
            "pulmonology": "pneumologist",
            "pulmonologist": "pneumologist",
            "cardiology": "cardiologist",
            "cardiovascular": "cardiologist",
            "oncology": "oncologist",
            "neurology": "neurologist",
            "dermatology": "dermatologist",
            "dermatological": "dermatologist",
            "toxicology": "toxicologist",
        }

        if not analysis.suspected_domains:
            return RouterDecision(
                selected_specialty="generalist",
                confidence=1.0,
                rationale="No specific domain identified by analysis engine.",
                route_text="This case should be directed to a generalist for initial evaluation."
            )

        # Apply boosting logic if relevant (simulated based on analysis summary/domains)
        # Note: In a more complex system, we'd pass the Intake data here too.
        # Sort domains by score
        sorted_domains = sorted(analysis.suspected_domains, key=lambda x: x.score, reverse=True)
        
        # Check for Emergency
        is_emergency = analysis.urgency.lower() == "emergency" or analysis.red_flag_triggered
        
        # Process domains
        processed_domains = []
        for d in sorted_domains:
            mapped_name = mapping.get(d.specialty.lower(), d.specialty.lower())
            if mapped_name in self.SUPPORTED_SPECIALTIES:
                processed_domains.append((mapped_name, d.score))
        
        if not processed_domains:
            selected = "generalist"
            confidence = 0.5
            alternatives = []
        else:
            selected, confidence = processed_domains[0]
            alternatives = [name for name, score in processed_domains[1:] if score > 0.4]

        # Handle alternatives
        # (already handled above)
        
        # Build rationale
        if is_emergency:
            rationale = f"EMERGENCY: {analysis.triage_summary}"
            route_text = f"CRITICAL: Immediate referral to EMERGENCY CARE and consultation with a {selected}."
            if analysis.red_flag_triggered:
                route_text = "RED FLAG TRIGGERED. " + route_text
        else:
            rationale = analysis.triage_summary
            route_text = f"Based on the triage analysis, this case should be directed to a {selected}."
            if alternatives:
                route_text += f" Secondary considerations: {', '.join(alternatives)}."

        return RouterDecision(
            selected_specialty=selected,
            confidence=confidence,
            rationale=rationale,
            alternate_specialties=alternatives,
            route_text=route_text,
            urgency=analysis.urgency,
            disclaimer=analysis.disclaimer
        )
