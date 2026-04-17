from models.intake import (
    PatientIntake, PatientProfile, EnvironmentInfo, ChiefComplaint,
    RespiratorySymptoms, CardiacSymptoms, NeurologicalSymptoms,
    DermatologicalSymptoms, ToxicExposureSymptoms, CancerWarningSigns,
    GeneralSymptoms, RedFlags, MedicalHistory, Sex, ExposureFactor
)

# Case 1: Respiratory + Pollution (Gabès)
case_respiratory_pollution = PatientIntake(
    patient_profile=PatientProfile(
        name="Ahmed Mansour",
        age=45,
        sex=Sex.MALE,
        height=175,
        weight=80
    ),
    environment=EnvironmentInfo(
        city="Gabès",
        neighborhood="Chott El Ferik",
        proximity_to_industrial_zone="visible_from_home_or_work",
        occupation="Worker",
        workplace_exposure=["dust", "chemical fumes"],
        home_exposure=["industrial dust"],
        smoking_status="non-smoker",
        pollution_observations=["visible_smoke", "chemical_smells", "dust_accumulation"],
        symptoms_worse_near=[ExposureFactor.INDUSTRY, ExposureFactor.SMOKE]
    ),
    chief_complaint=ChiefComplaint(
        main_problem="Chronic dry cough and shortness of breath",
        onset="gradual",
        duration="6 months",
        severity=6,
        progression="worsening",
        triggers=["physical exertion", "strong odors"],
        relieving_factors=["rest"]
    ),
    respiratory=RespiratorySymptoms(
        cough=True,
        dyspnea=True,
        chest_tightness=True
    ),
    cardiac=CardiacSymptoms(),
    neurological=NeurologicalSymptoms(),
    dermatological=DermatologicalSymptoms(),
    toxic_exposure=ToxicExposureSymptoms(
        chemical_inhalation=True,
        symptoms_after_exposure=True
    ),
    cancer_warning=CancerWarningSigns(
        fatigue=True
    ),
    general=GeneralSymptoms(
        malaise=True
    ),
    red_flags=RedFlags(),
    medical_history=MedicalHistory(
        asthma=True
    ),
    medications=["Salbutamol inhaler"],
    family_history=["Father had COPD"]
)

# Case 2: Cardiac Chest Pain (Potential Emergency)
case_cardiac_emergency = PatientIntake(
    patient_profile=PatientProfile(
        name="Laila Ben Youssef",
        age=62,
        sex=Sex.FEMALE,
        height=160,
        weight=75
    ),
    environment=EnvironmentInfo(
        city="Gabès",
        neighborhood="Sidi Boulbaba",
        proximity_to_industrial_zone="rarely_noticed",
        occupation="Retired",
        smoking_status="former",
        pollution_observations=[]
    ),
    chief_complaint=ChiefComplaint(
        main_problem="Sudden crushing chest pain",
        onset="sudden",
        duration="30 minutes",
        severity=10,
        progression="constant",
        triggers=["none"],
        relieving_factors=["none"]
    ),
    respiratory=RespiratorySymptoms(
        dyspnea=True
    ),
    cardiac=CardiacSymptoms(
        chest_pain=True,
        palpitations=True
    ),
    neurological=NeurologicalSymptoms(
        dizziness=True
    ),
    dermatological=DermatologicalSymptoms(),
    toxic_exposure=ToxicExposureSymptoms(),
    cancer_warning=CancerWarningSigns(),
    general=GeneralSymptoms(
        nausea=True,
        fever=False
    ),
    red_flags=RedFlags(
        crushing_chest_pain=True,
        severe_breathing_difficulty=True,
        fainting=False
    ),
    medical_history=MedicalHistory(
        hypertension=True,
        diabetes=True
    ),
    medications=["Amlodipine", "Metformin"]
)

# Case 3: Mixed/Unclear Symptoms
case_mixed_generalist = PatientIntake(
    patient_profile=PatientProfile(
        name="Mohamed Trabelsi",
        age=28,
        sex=Sex.MALE,
        height=180,
        weight=70
    ),
    environment=EnvironmentInfo(
        city="Gabès",
        neighborhood="Zrig",
        proximity_to_industrial_zone="very_far",
        occupation="Student",
        smoking_status="non-smoker",
        pollution_observations=[]
    ),
    chief_complaint=ChiefComplaint(
        main_problem="General fatigue and mild joint pain",
        onset="gradual",
        duration="2 weeks",
        severity=3,
        progression="stable",
        triggers=["vague"],
        relieving_factors=["sleep"]
    ),
    respiratory=RespiratorySymptoms(),
    cardiac=CardiacSymptoms(),
    neurological=NeurologicalSymptoms(
        headache=True
    ),
    dermatological=DermatologicalSymptoms(
        itching=True
    ),
    toxic_exposure=ToxicExposureSymptoms(),
    cancer_warning=CancerWarningSigns(),
    general=GeneralSymptoms(
        appetite_loss=True,
        joint_pain=True,
        malaise=True
    ),
    red_flags=RedFlags(),
    medical_history=MedicalHistory(),
    medications=["None"]
)

SAMPLE_CASES = {
    "respiratory_pollution": case_respiratory_pollution,
    "cardiac_emergency": case_cardiac_emergency,
    "mixed_generalist": case_mixed_generalist
}
