from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class UrgencyLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EMERGENCY = "emergency"

class ExposureFactor(str, Enum):
    INDUSTRY = "industry"
    SEA = "sea"
    DUST = "dust"
    SMOKE = "smoke"

class PatientProfile(BaseModel):
    name: str
    cin: str = Field(..., pattern=r"^\d{8}$", description="Tunisian National ID (8 digits)")
    age: int
    sex: Sex
    height: float # cm
    weight: float # kg

class Proximity(str, Enum):
    WORKS_IN_PLANT = "i_work_in_an_industrial_plant"
    VISIBLE = "visible_from_home_or_work"
    FREQUENT_SMELL = "frequent_chemical_smell"
    RARELY_NOTICED = "rarely_noticed"
    FAR = "very_far"

class EnvironmentInfo(BaseModel):
    city: str = "Gabès"
    neighborhood: str
    proximity_to_industrial_zone: Proximity
    occupation: str
    workplace_exposure: List[str] = Field(default_factory=list)
    home_exposure: List[str] = Field(default_factory=list)
    smoking_status: str # "non-smoker", "former", "current"
    pollution_observations: List[str] = Field(
        default_factory=list, 
        description="e.g. visible smoke, chemical odors, dust on surfaces"
    )
    symptoms_worse_near: List[ExposureFactor] = Field(default_factory=list)

class ChiefComplaint(BaseModel):
    main_problem: str
    onset: str # sudden/gradual
    duration: str
    severity: int = Field(ge=0, le=10)
    progression: str
    triggers: List[str] = Field(default_factory=list)
    relieving_factors: List[str] = Field(default_factory=list)

class RespiratorySymptoms(BaseModel):
    cough: bool = False
    sputum: bool = False
    hemoptysis: bool = False
    dyspnea: bool = False
    wheezing: bool = False
    chest_tightness: bool = False
    pain_on_breathing: bool = False

class CardiacSymptoms(BaseModel):
    chest_pain: bool = False
    palpitations: bool = False
    syncope: bool = False
    leg_swelling: bool = False
    exertional_dyspnea: bool = False
    orthopnea: bool = False

class NeurologicalSymptoms(BaseModel):
    headache: bool = False
    dizziness: bool = False
    memory_issues: bool = False
    confusion: bool = False
    numbness: bool = False
    weakness: bool = False
    tremor: bool = False
    seizure: bool = False
    speech_problems: bool = False
    vision_issues: bool = False

class DermatologicalSymptoms(BaseModel):
    rash: bool = False
    itching: bool = False
    redness: bool = False
    lesions: bool = False
    burns: bool = False
    discoloration: bool = False
    chronic_wounds: bool = False
    chemical_irritation: bool = False

class ToxicExposureSymptoms(BaseModel):
    gas_exposure: bool = False
    chemical_inhalation: bool = False
    heavy_metals: bool = False
    contaminated_water: bool = False
    industrial_incident: bool = False
    symptoms_after_exposure: bool = False

class CancerWarningSigns(BaseModel):
    unexplained_weight_loss: bool = False
    fatigue: bool = False
    night_sweats: bool = False
    persistent_lump: bool = False
    chronic_cough: bool = False
    chronic_lesion: bool = False
    unexplained_pain: bool = False
    hemoptysis: bool = False

class GeneralSymptoms(BaseModel):
    fever: bool = False
    chills: bool = False
    nausea: bool = False
    vomiting: bool = False
    diarrhea: bool = False
    appetite_loss: bool = False
    malaise: bool = False
    joint_pain: bool = False

class RedFlags(BaseModel):
    severe_breathing_difficulty: bool = False
    crushing_chest_pain: bool = False
    fainting: bool = False
    confusion: bool = False
    seizure: bool = False
    hemoptysis: bool = False
    unilateral_weakness: bool = False
    speech_difficulty: bool = False
    cyanosis: bool = False
    severe_allergic_reaction: bool = False
    toxic_exposure_event: bool = False

class MedicalHistory(BaseModel):
    asthma: bool = False
    copd: bool = False
    hypertension: bool = False
    heart_disease: bool = False
    stroke: bool = False
    cancer: bool = False
    neurologic_disease: bool = False
    skin_disease: bool = False
    diabetes: bool = False
    kidney_disease: bool = False
    liver_disease: bool = False
    allergies: List[str] = Field(default_factory=list)
    surgeries: List[str] = Field(default_factory=list)

class PatientIntake(BaseModel):
    patient_profile: PatientProfile
    environment: EnvironmentInfo
    chief_complaint: ChiefComplaint
    respiratory: RespiratorySymptoms = Field(default_factory=RespiratorySymptoms)
    cardiac: CardiacSymptoms = Field(default_factory=CardiacSymptoms)
    neurological: NeurologicalSymptoms = Field(default_factory=NeurologicalSymptoms)
    dermatological: DermatologicalSymptoms = Field(default_factory=DermatologicalSymptoms)
    toxic_exposure: ToxicExposureSymptoms = Field(default_factory=ToxicExposureSymptoms)
    cancer_warning: CancerWarningSigns = Field(default_factory=CancerWarningSigns)
    general: GeneralSymptoms = Field(default_factory=GeneralSymptoms)
    red_flags: RedFlags = Field(default_factory=RedFlags)
    medical_history: MedicalHistory = Field(default_factory=MedicalHistory)
    medications: List[str] = Field(default_factory=list)
    family_history: List[str] = Field(default_factory=list)
    upload_placeholders: List[str] = Field(default_factory=list, description="Placeholders for lab tests, imaging, reports, skin photos")
