import React, { useEffect, useRef } from 'react';
import './Medical.css';
import { API_BASE_URL } from '../config';

const Medical = () => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    let isMounted = true;
    try {
        const translations = {
            en: {
                app_title: "Gabès Triage",
                nav_profile: "Patient Profile",
                nav_environment: "Environment",
                nav_complaint: "Chief Complaint",
                nav_symptoms: "Symptom Groups",
                nav_red_flags: "Red Flags",
                nav_history: "Medical History",
                nav_uploads: "Uploads",
                badge_preliminary: "Phase: Preliminary Triage",
                badge_location: "📍 Gabès, Tunisia",
                sec_profile: "Patient Profile",
                label_name: "Full Name",
                ph_name: "John Doe",
                label_cin: "CIN (National ID)",
                ph_cin: "12345678",
                label_age: "Age",
                label_sex: "Sex at Birth",
                opt_male: "Male",
                opt_female: "Female",
                opt_other: "Other",
                label_height: "Height (cm)",
                label_weight: "Weight (kg)",
                sec_environment: "Location & Environment",
                desc_environment: "We ask these questions because the unique industrial environment of Gabès can impact your health.",
                label_neighborhood: "Neighborhood / Area (Gabès)",
                ph_neighborhood: "e.g. Chott El Ferik",
                label_proximity: "Proximity to Industrial Plants",
                opt_prox_work: "I work in an industrial plant",
                opt_prox_visible: "Visible from home or work",
                opt_prox_smell: "I often smell chemicals/gas",
                opt_prox_rarely: "I rarely notice any industry signs",
                opt_prox_far: "I live/work very far from the industrial zone",
                label_occupation: "Occupation",
                ph_occupation: "e.g. Teacher, Nurse, Worker",
                label_work_exposure: "Specific Workplace Exposures",
                ph_work_exposure: "e.g. Asbestos, Specific Chemicals",
                label_smoking: "Smoking Status",
                opt_smoke_never: "Never smoked",
                opt_smoke_former: "Former smoker",
                opt_smoke_current: "Current smoker",
                label_obs: "Environmental Observations at Home/Work:",
                opt_obs_smoke: "Visible smoke or flares",
                opt_obs_odor: "Strong chemical odors",
                opt_obs_dust: "White/Black dust on surfaces",
                opt_obs_noise: "Industrial noise",
                label_worse_near: "Symptoms feel worse near:",
                opt_wn_industry: "Industry",
                opt_wn_sea: "Sea",
                opt_wn_dust: "Dust",
                opt_wn_smoke: "Smoke",
                sec_complaint: "Chief Complaint",
                label_main_problem: "Main Problem",
                ph_main_problem: "Describe what is going on...",
                label_onset: "Onset",
                opt_onset_gradual: "Gradual",
                opt_onset_sudden: "Sudden",
                label_severity: "Severity (0-10)",
                label_duration: "Duration",
                ph_duration: "e.g. 3 days / 2 weeks",
                label_progression: "Progression (Change)",
                ph_progression: "e.g. Getting worse, stable",
                sec_symptoms: "Symptom Groups",
                grp_respiratory: "Respiratory",
                symp_cough: "Cough",
                symp_dyspnea: "Dyspnea",
                symp_wheezing: "Wheezing",
                symp_hemoptysis: "Hemoptysis",
                symp_chest_tight: "Chest Tightness",
                grp_cardiac: "Cardiac",
                symp_chest_pain: "Chest Pain",
                symp_palpitations: "Palpitations",
                symp_syncope: "Syncope",
                symp_leg_swelling: "Leg Swelling",
                grp_neurological: "Neurological",
                symp_headache: "Headache",
                symp_dizziness: "Dizziness",
                symp_weakness: "Weakness",
                symp_seizure: "Seizure",
                sec_red_flags: "Red Flags (Emergency)",
                desc_red_flags: "Mark any critical symptoms below.",
                symp_severe_resp: "Severe Breathing Difficulty",
                symp_crushing_pain: "Crushing Chest Pain",
                symp_confusion: "Confusion/Fainting",
                symp_toxic_event: "Major Toxic Exposure Event",
                sec_history: "Medical History",
                hist_asthma: "Asthma",
                hist_copd: "COPD",
                hist_hypertension: "Hypertension",
                hist_diabetes: "Diabetes",
                hist_heart: "Heart Disease",
                label_medications: "Current Medications",
                ph_medications: "List medications...",
                label_family_history: "Family History",
                ph_family_history: "Note chronic diseases...",
                btn_submit: "Analyze & Triage",
                btn_reset: "Reset Form",
                btn_consult: "Consult Specialist",
                btn_transfer: "Transfer me to Specialist",
                ph_chat_input: "Type your message...",
                res_title: "Triage Analysis Result",
                res_summary: "Summary",
                res_specialty: "Recommended Specialty",
                res_next_steps: "Next Steps",
                res_disclaimer_title: "Medical Disclaimer:",
                res_urgency_placeholder: "LOW",
                urg_low: "LOW URGENCY",
                urg_moderate: "MODERATE URGENCY",
                urg_high: "HIGH URGENCY",
                urg_emergency: "EMERGENCY / RED FLAG",
                spec_generalist: "Generalist / GP",
                spec_pneumologist: "Pneumologist",
                spec_cardiologist: "Cardiologist",
                spec_oncologist: "Oncologist",
                spec_neurologist: "Neurologist",
                spec_dermatologist: "Dermatologist",
                spec_toxicologist: "Toxicologist"
            },
            fr: {
                app_title: "Triage de Gabès",
                nav_profile: "Profil du Patient",
                nav_environment: "Environnement",
                nav_complaint: "Motif de Consultation",
                nav_symptoms: "Groupes de Symptômes",
                nav_red_flags: "Signes d'Urgence",
                nav_history: "Antécédents",
                nav_uploads: "Documents",
                badge_preliminary: "Phase: Triage Préliminaire",
                badge_location: "📍 Gabès, Tunisie",
                sec_profile: "Profil du Patient",
                label_name: "Nom Complet",
                ph_name: "Jean Dupont",
                label_cin: "CIN (N° d'identité)",
                ph_cin: "12345678",
                label_age: "Âge",
                label_sex: "Sexe à la naissance",
                opt_male: "Homme",
                opt_female: "Femme",
                opt_other: "Autre",
                label_height: "Taille (cm)",
                label_weight: "Poids (kg)",
                sec_environment: "Localisation & Environnement",
                desc_environment: "Ces questions nous aident car l'environnement industriel de Gabès peut impacter votre santé.",
                label_neighborhood: "Quartier / Zone (Gabès)",
                ph_neighborhood: "ex: Chott El Ferik",
                label_proximity: "Proximité des Usines",
                opt_prox_work: "Je travaille dans une usine industrielle",
                opt_prox_visible: "Visible de la maison/travail",
                opt_prox_smell: "Odeurs chimiques fréquentes",
                opt_prox_rarely: "Rarement remarqué",
                opt_prox_far: "Très loin de la zone industrielle",
                label_occupation: "Profession",
                ph_occupation: "ex: Enseignant, Ouvrier, Infirmier",
                label_work_exposure: "Expositions spécifiques au travail",
                ph_work_exposure: "ex: Amiante, Produits Chimiques",
                label_smoking: "Tabagisme",
                opt_smoke_never: "Jamais fumé",
                opt_smoke_former: "Ancien fumeur",
                opt_smoke_current: "Fumeur actuel",
                label_obs: "Observations Environnementales :",
                opt_obs_smoke: "Fumée ou torchères visibles",
                opt_obs_odor: "Fortes odeurs chimiques",
                opt_obs_dust: "Poussière blanche/noire",
                opt_obs_noise: "Bruit industriel",
                label_worse_near: "Symptômes pires près de :",
                opt_wn_industry: "L'industrie",
                opt_wn_sea: "La mer",
                opt_wn_dust: "La poussière",
                opt_wn_smoke: "La fumée",
                sec_complaint: "Motif de Consultation",
                label_main_problem: "Problème Principal",
                ph_main_problem: "Décrivez ce qui se passe...",
                label_onset: "Apparition",
                opt_onset_gradual: "Progressive",
                opt_onset_sudden: "Soudaine",
                label_severity: "Sévérité (0-10)",
                label_duration: "Durée",
                ph_duration: "ex: 3 jours / 2 semaines",
                label_progression: "Progression",
                ph_progression: "ex: S'aggrave, stable",
                sec_symptoms: "Groupes de Symptômes",
                grp_respiratory: "Respiratoire",
                symp_cough: "Toux",
                symp_dyspnea: "Dyspnée",
                symp_wheezing: "Sifflement",
                symp_hemoptysis: "Hémoptysie",
                symp_chest_tight: "Oppression Thoracique",
                grp_cardiac: "Cardiaque",
                symp_chest_pain: "Douleur Thoracique",
                symp_palpitations: "Palpitations",
                symp_syncope: "Syncope",
                symp_leg_swelling: "Œdème des jambes",
                grp_neurological: "Neurologique",
                symp_headache: "Maux de tête",
                symp_dizziness: "Vertiges",
                symp_weakness: "Faiblesse",
                symp_seizure: "Convulsions",
                sec_red_flags: "Signes d'Alerte (Urgence)",
                desc_red_flags: "Cochez tout symptôme critique.",
                symp_severe_resp: "Détresse Respiratoire",
                symp_crushing_pain: "Douleur Thoracique Intense",
                symp_confusion: "Confusion / Evanouissement",
                symp_toxic_event: "Exposition Toxique Majeure",
                sec_history: "Antécédents Médicaux",
                hist_asthma: "Asthme",
                hist_copd: "BPCO",
                hist_hypertension: "Hypertension",
                hist_diabetes: "Diabète",
                hist_heart: "Maladie Cardiaque",
                label_medications: "Traitements actuels",
                ph_medications: "Liste des médicaments...",
                label_family_history: "Antécédents familiaux",
                ph_family_history: "Notez les maladies chroniques...",
                btn_submit: "Analyser & Trier",
                btn_reset: "Réinitialiser",
                btn_consult: "Consulter le spécialiste",
                btn_transfer: "Me transférer au spécialiste",
                ph_chat_input: "Tapez votre message...",
                res_title: "Résultat de l'Analyse",
                res_summary: "Résumé",
                res_specialty: "Spécialité Recommandée",
                res_next_steps: "Prochaines Étapes",
                res_disclaimer_title: "Avis Médical :",
                res_urgency_placeholder: "FAIBLE",
                urg_low: "URGENCE FAIBLE",
                urg_moderate: "URGENCE MODÉRÉE",
                urg_high: "URGENCE ÉLEVÉE",
                urg_emergency: "URGENCE / ALERTE",
                spec_generalist: "Généraliste",
                spec_pneumologist: "Pneumologue",
                spec_cardiologist: "Cardiologue",
                spec_oncologist: "Oncologue",
                spec_neurologist: "Neurologue",
                spec_dermatologist: "Dermatologue",
                spec_toxicologist: "Toxicologue"
            },
            ar: {
                app_title: "فرز قابس الطبي",
                nav_profile: "ملف المريض",
                nav_environment: "البيئة",
                nav_complaint: "الشكوى الرئيسية",
                nav_symptoms: "مجموعات الأعراض",
                nav_red_flags: "علامات الخطر",
                nav_history: "التاريخ الطبي",
                nav_uploads: "المرفقات",
                badge_preliminary: "المرحلة: الفرز الأولي",
                badge_location: "📍 قابس، تونس",
                sec_profile: "ملف المريض",
                label_name: "الاسم الكامل",
                ph_name: "محمد علي",
                label_cin: "رقم بطاقة التعريف (CIN)",
                ph_cin: "12345678",
                label_age: "العمر",
                label_sex: "الجنس عند الولادة",
                opt_male: "ذكر",
                opt_female: "أنثى",
                opt_other: "آخر",
                label_height: "الطول (سم)",
                label_weight: "الوزن (كجم)",
                sec_environment: "الموقع والبيئة",
                desc_environment: "نسأل هذه الأسئلة لأن البيئة الصناعية الفريدة في قابس يمكن أن تؤثر على صحتك.",
                label_neighborhood: "الحي / المنطقة (قابس)",
                ph_neighborhood: "مثال: شط الفريك",
                label_proximity: "القرب من المصانع الصناعية",
                opt_prox_work: "أعمل في مصنع صناعي",
                opt_prox_visible: "مرئي من المنزل أو العمل",
                opt_prox_smell: "أشم روائح كيميائية غالباً",
                opt_prox_rarely: "نادراً ما ألاحظ ذلك",
                opt_prox_far: "أعيش/أعمل بعيداً جداً",
                label_occupation: "المهنة",
                ph_occupation: "مثال: معلم، عامل، ممرض",
                label_work_exposure: "التعرض المهني الخاص",
                ph_work_exposure: "مثال: أميانت، مواد كيميائية",
                label_smoking: "حالة التدخين",
                opt_smoke_never: "لم أدخن أبداً",
                opt_smoke_former: "مدخن سابق",
                opt_smoke_current: "مدخن حالي",
                label_obs: "ملاحظات بيئية في المنزل/العمل:",
                opt_obs_smoke: "دخان أو شعلات مرئية",
                opt_obs_odor: "روائح كيميائية قوية",
                opt_obs_dust: "غبار أبيض/أسود على الأسطح",
                opt_obs_noise: "ضجيج صناعي",
                label_worse_near: "الأعراض تزداد سوءاً بالقرب من:",
                opt_wn_industry: "المصانع",
                opt_wn_sea: "البحر",
                opt_wn_dust: "الغبار",
                opt_wn_smoke: "الدخان",
                sec_complaint: "الشكوى الرئيسية",
                label_main_problem: "المشكلة الرئيسية",
                ph_main_problem: "صف ما الذي يحدث معك...",
                label_onset: "بداية الأعراض",
                opt_onset_gradual: "تدريجي",
                opt_onset_sudden: "مفاجئ",
                label_severity: "الحدة (0-10)",
                label_duration: "المدة",
                ph_duration: "مثال: 3 أيام / أسبوعين",
                label_progression: "تطور المرض",
                ph_progression: "مثال: يزداد سوءاً، مستقر",
                sec_symptoms: "مجموعات الأعراض",
                grp_respiratory: "الجهاز التنفسي",
                symp_cough: "سعال",
                symp_dyspnea: "ضيق تنفس",
                symp_wheezing: "تزييق/صفير",
                symp_hemoptysis: "سعال مصحوب بدم",
                symp_chest_tight: "ضيق في الصدر",
                grp_cardiac: "القلب",
                symp_chest_pain: "ألم في الصدر",
                symp_palpitations: "خفقان",
                symp_syncope: "إغماء",
                symp_leg_swelling: "تورم الساقين",
                grp_neurological: "الأعصاب",
                symp_headache: "صداع",
                symp_dizziness: "دوار",
                symp_weakness: "وهن/ضعف",
                symp_seizure: "تشنجات",
                sec_red_flags: "علامات الخطر (طوارئ)",
                desc_red_flags: "حدد أي أعراض حرجة أدناه.",
                symp_severe_resp: "صعوبة شديدة في التنفس",
                symp_crushing_pain: "ألم ضاغط في الصدر",
                symp_confusion: "ارتباك / فقدان وعي",
                symp_toxic_event: "تعرض لمادة سامة",
                sec_history: "التاريخ الطبي",
                hist_asthma: "ربو",
                hist_copd: "انسداد رئوي مزمن",
                hist_hypertension: "ضغط الدم",
                hist_diabetes: "سكري",
                hist_heart: "أمراض القلب",
                label_medications: "الأدوية الحالية",
                ph_medications: "قائمة الأدوية...",
                label_family_history: "التاريخ العائلي",
                ph_family_history: "ملاحظات حول الأمراض المزمنة...",
                btn_submit: "تحليل وفرز",
                btn_reset: "إعادة تعيين",
                btn_consult: "استشر أخصائي",
                btn_transfer: "حولني إلى أخصائي",
                ph_chat_input: "اكتب رسالتك...",
                res_title: "نتائج تحليل الفرز",
                res_summary: "ملخص",
                res_specialty: "التخصص الموصى به",
                res_next_steps: "الخطوات التالية",
                res_disclaimer_title: "إخلاء مسؤولية طبي:",
                res_urgency_placeholder: "منخفض",
                urg_low: "حالة عادية",
                urg_moderate: "حالة متوسطة",
                urg_high: "حالة عاجلة",
                urg_emergency: "حالة طارئة / خطر",
                spec_generalist: "طبيب عام",
                spec_pneumologist: "طبيب أمراض صدرية",
                spec_cardiologist: "طبيب قلب",
                spec_oncologist: "طبيب أورام",
                spec_neurologist: "طبيب أعصاب",
                spec_dermatologist: "طبيب جلدية",
                spec_toxicologist: "طبيب سموم"
            }
        };
        
        /**
         * Robust Language Setter
         * @param {string} lang 'en' | 'fr' | 'ar'
         */
        const setLanguage = function(lang) {
            try {
                if (!translations[lang]) lang = 'en';
        
                // Update Document Attributes
                document.documentElement.lang = lang;
                document.documentElement.dir = (lang === 'ar' ? 'rtl' : 'ltr');
        
                // Update All Text Elements
                document.querySelectorAll('[data-i18n]').forEach(el => {
                    const key = el.getAttribute('data-i18n');
                    if (translations[lang][key]) {
                        el.innerText = translations[lang][key];
                    }
                });
        
                // Update All Placeholders
                document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
                    const key = el.getAttribute('data-i18n-placeholder');
                    if (translations[lang][key]) {
                        el.placeholder = translations[lang][key];
                    }
                });
        
                // Sync Select Box Value
                const select = document.getElementById('lang-select');
                if (select) select.value = lang;
        
                // Persist
                localStorage.setItem('preferred_lang', lang);
            } catch (e) {
                console.error("Language switch failed:", e);
            }
        };
        
        let currentRecommendedSpecialty = 'generalist';
        
        function formatIsoDate(value) {
            if (!value) return 'N/A';
            const parsed = new Date(value);
            if (Number.isNaN(parsed.getTime())) return value;
            return parsed.toLocaleString();
        }
        
        function renderHistoryRecords(records, cin) {
            const container = document.getElementById('history-records');
            if (!container) return;
            container.innerHTML = '';
        
            if (!records || !records.length) {
                container.innerHTML = '<div class="history-record-card">No previous medical records found for this CIN.</div>';
                return;
            }
        
            records.forEach((record) => {
                const card = document.createElement('div');
                card.className = 'history-record-card';
                const summary = (record.summary || '').trim() || 'No summary available.';
                card.innerHTML = `
                    <div class="history-record-title">Case ${record.case_id}</div>
                    <div class="history-record-meta">
                        Patient: ${record.patient_name || 'N/A'} | Age: ${record.age || 'N/A'} |
                        Specialty: ${record.specialty || 'N/A'} | Urgency: ${record.urgency || 'N/A'} |
                        Date: ${formatIsoDate(record.indexed_at)}
                    </div>
                    <div class="history-record-summary">${summary}</div>
                    <div class="history-record-actions">
                        <button class="btn-secondary btn-download-history-record" data-cin="${cin}" data-case-id="${record.case_id}">
                            Download PDF
                        </button>
                    </div>
                `;
                container.appendChild(card);
            });
        }
        
        async function loadMedicalHistory() {
            const cinInput = document.getElementById('history-cin-input');
            const statusEl = document.getElementById('history-status');
            const cin = (cinInput?.value || '').trim();
            if (!cin) {
                statusEl.textContent = 'Please enter CIN first.';
                return;
            }
            statusEl.textContent = 'Loading medical records...';
        
            try {
                const response = await fetch(API_BASE_URL + `/api/v1/medical/api/patient/history?cin=${encodeURIComponent(cin)}`);
                const data = await response.json();
                if (!response.ok || data.status !== 'success') {
                    throw new Error(data.detail || 'Failed to load medical history.');
                }
                renderHistoryRecords(data.records || [], cin);
                statusEl.textContent = `${data.count || 0} record(s) loaded.`;
            } catch (err) {
                statusEl.textContent = `Error: ${err.message}`;
                renderHistoryRecords([], cin);
            }
        }
        
        async function downloadHistoryRecordPdf(cin, caseId) {
            const url = `/api/v1/medical/api/patient/history/report/pdf?cin=${encodeURIComponent(cin)}&case_id=${encodeURIComponent(caseId)}`;
            const response = await fetch(API_BASE_URL + url);
            if (!response.ok) {
                let detail = 'Failed to download history PDF.';
                try {
                    const errData = await response.json();
                    detail = errData?.detail || detail;
                } catch (_) {}
                throw new Error(detail);
            }
            const blob = await response.blob();
            const objectUrl = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = objectUrl;
            link.download = `medical_history_${cin}_${caseId}.pdf`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(objectUrl);
        }
        
        (() => {
            const root = containerRef.current;
            
            // 1. Language Initialization
            const langSelect = root.querySelector('#lang-select');
            const savedLang = localStorage.getItem('preferred_lang') || 'en';
            setLanguage(savedLang);
        
            if (langSelect) {
                langSelect.addEventListener('change', (e) => {
                    setLanguage(e.target.value);
                });
            }
        
            // 2. UI Elements - Use scoped selection for React compatibility
            const form = root.querySelector('#triage-form');
            const overlay = root.querySelector('#results-overlay');

            if (form) {
                console.log("Attaching form listener");
                form.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    console.log("Form submitted, preventDefault called");
                    
                    const loader = document.createElement('div');
                    loader.className = 'loader-overlay';
                    loader.innerHTML = '<div class="spinner"></div><p>Analyzing Triage Data...</p>';
                    document.body.appendChild(loader);

                    const formData = new FormData(form);
                    const getCheckboxes = (name) => Array.from(root.querySelectorAll(`input[name="${name}"]:checked`)).map(cb => cb.value);
                    const getBooleans = (name, keys) => {
                        const vals = {};
                        const checked = getCheckboxes(name);
                        keys.forEach(k => vals[k] = checked.includes(k));
                        return vals;
                    };

                    const payload = {
                        patient_profile: {
                            name: formData.get('name'),
                            cin: formData.get('cin'),
                            age: parseInt(formData.get('age') || 0),
                            sex: formData.get('sex'),
                            height: parseFloat(formData.get('height') || 0),
                            weight: parseFloat(formData.get('weight') || 0)
                        },
                        environment: {
                            city: "Gabès",
                            neighborhood: formData.get('neighborhood'),
                            proximity_to_industrial_zone: formData.get('proximity'),
                            occupation: formData.get('occupation'),
                            workplace_exposure: (formData.get('workplace_exposure') || "").split(',').map(s => s.trim()).filter(s => s),
                            smoking_status: formData.get('smoking_status'),
                            pollution_observations: getCheckboxes('pollution_obs'),
                            symptoms_worse_near: getCheckboxes('worse_near')
                        },
                        chief_complaint: {
                            main_problem: formData.get('main_problem'),
                            onset: formData.get('onset'),
                            duration: formData.get('duration'),
                            severity: parseInt(formData.get('severity') || 0),
                            progression: formData.get('progression')
                        },
                        respiratory: getBooleans('resp', ['cough', 'dyspnea', 'wheezing', 'hemoptysis', 'chest_tightness']),
                        cardiac: getBooleans('cardiac', ['chest_pain', 'palpitations', 'syncope', 'leg_swelling']),
                        neurological: getBooleans('neuro', ['headache', 'dizziness', 'weakness', 'seizure']),
                        red_flags: getBooleans('red_flags', ['severe_breathing_difficulty', 'crushing_chest_pain', 'confusion', 'toxic_exposure_event']),
                        medical_history: {
                            asthma: getCheckboxes('history').includes('asthma'),
                            copd: getCheckboxes('history').includes('copd'),
                            hypertension: getCheckboxes('history').includes('hypertension'),
                            diabetes: getCheckboxes('history').includes('diabetes'),
                            heart_disease: getCheckboxes('history').includes('heart_disease')
                        },
                        medications: (formData.get('medications') || "").split(',').map(s => s.trim()).filter(s => s),
                        family_history: (formData.get('family_history') || "").split(',').map(s => s.trim()).filter(s => s)
                    };

                    try {
                        const response = await fetch(API_BASE_URL + '/api/v1/medical/triage', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        if (!response.ok) throw new Error('Network error');
                        const result = await response.json();
                        displayResults(result);
                    } catch (err) {
                        console.error("Submit error:", err);
                        alert('Connection Error: ' + err.message);
                    } finally {
                        loader.remove();
                    }
                });
            }
            const closeBtn = root.querySelector('.close-results');
            const btnOpenHistory = root.querySelector('#btn-open-history');
            const historyModal = root.querySelector('#history-modal');
            const btnCloseHistory = root.querySelector('#btn-close-history');
            const btnLoadHistory = root.querySelector('#btn-load-history');
            const historyCinInput = root.querySelector('#history-cin-input');
            const historyRecords = root.querySelector('#history-records');
        
            // 3. Results UI Controller
            const displayResults = (result) => {
                const lang = localStorage.getItem('preferred_lang') || 'en';
                
                // Use rationale for summary
                document.getElementById('result-summary').textContent = result.rationale || "---";
                
                // Specialty Localization
                const specKey = `spec_${result.selected_specialty.toLowerCase()}`;
                document.getElementById('result-specialty').textContent = translations[lang][specKey] || result.selected_specialty.toUpperCase();
                currentRecommendedSpecialty = (result.selected_specialty || 'generalist').toLowerCase();
                
                document.getElementById('result-route-text').textContent = result.route_text || "";
                document.getElementById('result-next-step').textContent = result.route_text || result.rationale || "";
                document.getElementById('result-disclaimer').textContent = result.disclaimer || "";
                
                // Urgency Indicators
                const urgencyEl = document.getElementById('result-urgency');
                if (urgencyEl && result.urgency) {
                    const urgency = result.urgency.toLowerCase();
                    urgencyEl.className = `urgency-indicator urgency-${urgency}`;
                    const urgencyKey = `urg_${urgency}`;
                    urgencyEl.textContent = translations[lang][urgencyKey] || urgency.toUpperCase();
                }
        
                overlay.classList.remove('hidden');
            };
        
            // 4. Form Actions
            if (closeBtn) closeBtn.addEventListener('click', () => overlay.classList.add('hidden'));
        
            if (btnOpenHistory && historyModal) {
                btnOpenHistory.addEventListener('click', () => {
                    historyModal.classList.remove('hidden');
                    const intakeCin = (document.getElementById('cin')?.value || '').trim();
                    if (historyCinInput && intakeCin && !historyCinInput.value) {
                        historyCinInput.value = intakeCin;
                    }
                });
            }
            if (btnCloseHistory && historyModal) {
                btnCloseHistory.addEventListener('click', () => historyModal.classList.add('hidden'));
            }
            if (historyModal) {
                historyModal.addEventListener('click', (e) => {
                    if (e.target === historyModal) historyModal.classList.add('hidden');
                });
            }
            if (btnLoadHistory) {
                btnLoadHistory.addEventListener('click', loadMedicalHistory);
            }
            if (historyCinInput) {
                historyCinInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        loadMedicalHistory();
                    }
                });
            }
            if (historyRecords) {
                historyRecords.addEventListener('click', async (e) => {
                    const target = e.target;
                    if (!(target instanceof HTMLElement)) return;
                    const btn = target.closest('.btn-download-history-record');
                    if (!btn) return;
                    const cin = btn.getAttribute('data-cin') || '';
                    const caseId = btn.getAttribute('data-case-id') || '';
                    const statusEl = document.getElementById('history-status');
                    if (!cin || !caseId) return;
                    try {
                        if (statusEl) statusEl.textContent = `Downloading PDF for case ${caseId}...`;
                        await downloadHistoryRecordPdf(cin, caseId);
                        if (statusEl) statusEl.textContent = `Downloaded case ${caseId}.`;
                    } catch (err) {
                        if (statusEl) statusEl.textContent = `Download error: ${err.message}`;
                    }
                });
            }
            // 5. Scroll Spy
            const navItems = document.querySelectorAll('.nav-item');
            window.addEventListener('scroll', () => {
                let current = '';
                document.querySelectorAll('.form-section').forEach(section => {
                    if (pageYOffset >= section.offsetTop - 100) current = section.getAttribute('id');
                });
                navItems.forEach(item => {
                    item.classList.remove('active');
                    if (item.getAttribute('href').includes(current)) item.classList.add('active');
                });
            });
        })();
        
        // 6. Global Loader Styles
        const style = document.createElement('style');
        style.textContent = `
            .loader-overlay {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(255,255,255,0.8); backdrop-filter: blur(4px);
                display: flex; flex-direction: column; align-items: center; justify-content: center;
                z-index: 2000;
            }
            .spinner {
                width: 40px; height: 40px; border: 4px solid var(--border);
                border-top-color: var(--primary); border-radius: 50%;
                animation: spin 1s linear infinite; margin-bottom: 1rem;
            }
            @keyframes spin { to { transform: rotate(360deg); } }
        `;
        document.head.appendChild(style);
        
        // --- Agentic Chat Logic ---
        let currentAgent = null;
        let chatCIN = null;
        let suggestedSpecialty = null;
        let latestStep3Cin = null;
        let latestStep3ReportUrl = null;
        
        function normalizeAgentName(agentName) {
            const raw = (agentName || "generalist").toLowerCase().trim();
            const mapping = {
                pneumologue: "pneumologist",
                cardiologue: "cardiologist",
                neurologue: "neurologist",
                oncologue: "oncologist",
                dermatologue: "dermatologist",
                toxicologue: "toxicologist"
            };
            return mapping[raw] || raw;
        }
        
        function showBilanPanel(visible) {
            const panel = document.getElementById('bilan-upload-panel-chat');
            if (!panel) return;
            panel.classList.toggle('is-hidden', !visible);
        }
        
        function detectBilanRequestFromText(text) {
            const msg = (text || '').toLowerCase();
            if (!msg) return false;
            if (msg.includes('[request_bilan_sanguin]')) return true;
        
            const keywords = [
                'blood test',
                'bilan sanguin',
                'lab test',
                'laboratory test',
                'toxicology screening',
                'analyse sanguine'
            ];
            const requestWords = ['please', 'must', 'need', 'required', 'should', 'devez', 'il faut'];
            const hasKeyword = keywords.some(k => msg.includes(k));
            const hasRequestWord = requestWords.some(k => msg.includes(k));
            return hasKeyword && hasRequestWord;
        }
        
        function appendMessage(role, text) {
            const container = document.getElementById('chat-messages');
            if (!container) return;
            
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${role}`;
            
            // Process basic formatting: Newlines -> BR, **text** -> bold, numeric lists
            let formattedText = text
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/^(\d+\.)\s/gm, '<strong>$1</strong> ') // Bold list numbers
                .replace(/\[SUGGEST_TRANSFER:.*?\]/g, ''); // Hide the trigger tag from UI
        
            const plain = formattedText.replace(/<br>/g, '').replace(/<strong>|<\/strong>/g, '').trim();
            if (!plain && /\[SUGGEST_TRANSFER:\s*\w+\]/i.test(text || '')) {
                formattedText = 'Specialist recommends transfer to toxicologist for targeted toxic exposure evaluation.';
            }
                
            msgDiv.innerHTML = formattedText;
            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
        }
        
        function formatStep3FinalMessage(finalizeData) {
            const tox = finalizeData?.toxicology_final || {};
            const bilan = finalizeData?.bilan_analysis || {};
        
            const abnormalMarkers = (bilan.abnormal_markers || [])
                .map(m => `- ${m.marker || 'Marker'}: ${m.finding || 'No finding'} (${m.severity || 'N/A'})`)
                .join('\n') || '- No explicit abnormal markers listed.';
            const toxicSignals = (bilan.toxicology_signals || []).map(s => `- ${s}`).join('\n') || '- No specific toxicology signal extracted from bilan.';
            const symptoms = (tox.symptoms_consolidated || []).map(s => `- ${s}`).join('\n') || '- Not explicitly listed.';
            const abnormalities = (tox.abnormalities_consolidated || []).map(s => `- ${s}`).join('\n') || '- Not explicitly listed.';
            const exposureAgents = (tox.likely_exposure_agents || []).map(s => `- ${s}`).join('\n') || '- Not explicitly listed.';
            const differential = (tox.differential_diagnosis || [])
                .map(d => `- ${d.condition || 'Condition'} (confidence: ${d.confidence || 'N/A'}) -> ${d.reasoning || 'No reasoning provided.'}`)
                .join('\n') || '- No differential diagnosis documented.';
            const recommendedActions = (tox.recommended_actions || []).map(a => `- ${a}`).join('\n') || '- No specific action listed.';
            const erActions = (tox.immediate_er_actions || []).map(a => `- ${a}`).join('\n') || '- No emergency action listed.';
            const monitoringPlan = (tox.monitoring_plan || []).map(a => `- ${a}`).join('\n') || '- No monitoring plan listed.';
            const uncertainties = (tox.uncertainties_and_limits || []).map(a => `- ${a}`).join('\n') || '- No limitations listed.';
        
            const urgencyLine = tox.urgent
                ? 'URGENT CARE REQUIRED NOW'
                : (tox.urgency_level ? `Urgency level: ${String(tox.urgency_level).toUpperCase()}` : 'Urgency level: MODERATE');
        
            return [
                'Final Toxicology Report',
                '',
                '1) Bilan Expert Summary',
                bilan.bilan_summary || 'No bilan summary available.',
                '',
                '2) Bilan Abnormal Markers',
                abnormalMarkers,
                '',
                '3) Toxicology Signals From Bilan',
                toxicSignals,
                '',
                '4) Symptoms Consolidated',
                symptoms,
                '',
                '5) Abnormalities Consolidated',
                abnormalities,
                '',
                '6) Suspected Exposure Agents',
                exposureAgents,
                '',
                '7) Clinical Toxicology Assessment',
                tox.toxicology_assessment || 'No toxicology assessment available.',
                '',
                '8) Differential Diagnosis',
                differential,
                '',
                '9) Clinical Reasoning',
                tox.clinical_reasoning || 'No extended reasoning provided.',
                '',
                '10) Recommended Actions',
                recommendedActions,
                '',
                '11) Immediate ER Actions',
                erActions,
                '',
                '12) Monitoring Plan',
                monitoringPlan,
                '',
                '13) Uncertainties and Limits',
                uncertainties,
                '',
                '14) Urgency Decision',
                urgencyLine,
                tox.urgent_instruction || '',
                '',
                '15) Integrated Final Narrative',
                tox.final_global_report || 'No final narrative report text provided.',
                '',
                'The detailed PDF report is now available from the download button below.'
            ].filter(Boolean).join('\n');
        }
        
        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if (!text) return;
        
            appendMessage('patient', text);
            input.value = '';
        
            try {
                const response = await fetch(API_BASE_URL + '/api/v1/medical/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        cin: chatCIN, 
                        message: text,
                        agent: currentAgent
                    })
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    appendMessage('agent', data.response);
                    const meta = data.meta || {};
        
                    if (meta.request_bilan_sanguin || detectBilanRequestFromText(data.response)) {
                        showBilanPanel(true);
                        appendMessage('agent', 'Please upload your blood test PDF to continue analysis.');
                    }
                    if (meta.suggested_transfer) {
                        suggestedSpecialty = normalizeAgentName(meta.suggested_transfer);
                        const actions = document.getElementById('chat-actions');
                        actions.classList.remove('hidden');
                        const btnTransfer = document.getElementById('btn-transfer');
                        if (btnTransfer) {
                            const displayName = suggestedSpecialty.charAt(0).toUpperCase() + suggestedSpecialty.slice(1);
                            btnTransfer.textContent = `Transfer me to ${displayName}`;
                        }
                    }
                    
                    // Dynamic Transfer Detection
                    const transferMatch = data.response.match(/\[SUGGEST_TRANSFER:\s*(\w+)\]/);
                    if (transferMatch) {
                        suggestedSpecialty = normalizeAgentName(transferMatch[1]);
                        const actions = document.getElementById('chat-actions');
                        actions.classList.remove('hidden');
                        
                        // Update transfer button text
                        const btnTransfer = document.getElementById('btn-transfer');
                        if (btnTransfer) {
                            const displayName = suggestedSpecialty.charAt(0).toUpperCase() + suggestedSpecialty.slice(1);
                            btnTransfer.textContent = `Transfer me to ${displayName}`;
                        }
                    }
                } else {
                    appendMessage('agent', 'Error: ' + data.detail);
                }
            } catch (err) {
                console.error('Chat error:', err);
                appendMessage('agent', 'Sorry, I encountered an error. Please try again.');
            }
        }
        
        // Event Listeners for Chat
        (() => {
            const btnConsult = document.getElementById('btn-consult');
            if (btnConsult) {
                btnConsult.onclick = async () => {
                    chatCIN = document.getElementById('cin').value;
                    currentAgent = normalizeAgentName(currentRecommendedSpecialty);
                    latestStep3Cin = null;
                    latestStep3ReportUrl = null;
                    
                    // UI Transition
                    document.getElementById('results-overlay').classList.add('hidden');
                    document.getElementById('chat-section').classList.remove('hidden');
                    showBilanPanel(false);
                    document.getElementById('report-actions')?.classList.add('hidden');
                    
                    // Set Agent Name
                    document.getElementById('agent-name').textContent = `${currentAgent.charAt(0).toUpperCase() + currentAgent.slice(1)} Agent`;
                    
                    // Dynamic Initialization
                    appendMessage('agent', 'Analyzing your medical history...');
                    
                    try {
                        const response = await fetch(API_BASE_URL + '/api/v1/medical/api/chat', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                cin: chatCIN, 
                                message: "[INITIALIZE]",
                                agent: currentAgent
                            })
                        });
                        const data = await response.json();
                        
                        // Clear the "Analyzing" message and show the real greeting
                        const messagesContainer = document.getElementById('chat-messages');
                        messagesContainer.lastElementChild?.remove();
                        
                        if (data.status === 'success') {
                            appendMessage('agent', data.response);
                            const initMeta = data.meta || {};
                            if (initMeta.request_bilan_sanguin || detectBilanRequestFromText(data.response)) {
                                showBilanPanel(true);
                            }
                        }
                    } catch (err) {
                        console.error('Init error:', err);
                        appendMessage('agent', 'Hello. I am here to help. How can I assist you?');
                    }
                };
            }

        
            const btnSendChat = document.getElementById('btn-send-chat');
            if (btnSendChat) btnSendChat.onclick = sendMessage;
        
            const chatInput = document.getElementById('chat-input');
            if (chatInput) {
                chatInput.onkeypress = (e) => {
                    if (e.key === 'Enter') sendMessage();
                };
            }
        
            const closeChat = document.querySelector('.close-chat');
            if (closeChat) {
                closeChat.addEventListener('click', () => {
                    document.getElementById('chat-section').classList.add('hidden');
                });
            }
        
            const btnTransfer = document.getElementById('btn-transfer');
            if (btnTransfer) {
                btnTransfer.addEventListener('click', async () => {
                    if (!suggestedSpecialty) return;
                    
                    currentAgent = normalizeAgentName(suggestedSpecialty); 
                    document.getElementById('chat-actions').classList.add('hidden');
                    
                    // Switch UI based on specialty
                    const nameEl = document.getElementById('agent-name');
                    const avatarEl = document.getElementById('agent-avatar');
                    
                    const config = {
                        pneumologist: { name: "Pneumologist Agent", icon: "🫁" },
                        pneumologue: { name: "Pneumologist Agent", icon: "🫁" },
                        cardiologist: { name: "Cardiologist Agent", icon: "🫀" },
                        cardiologue: { name: "Cardiologist Agent", icon: "🫀" },
                        neurologist: { name: "Neurologist Agent", icon: "🧠" },
                        oncologist: { name: "Oncologist Agent", icon: "🔬" },
                        dermatologist: { name: "Dermatologist Agent", icon: "🧴" },
                        toxicologist: { name: "Toxicologist Agent", icon: "🧪" }
                    };
                    
                    const agentUI = config[suggestedSpecialty] || { name: `${suggestedSpecialty} Agent`, icon: "🩺" };
                    nameEl.textContent = agentUI.name;
                    avatarEl.textContent = agentUI.icon;
                    
                    appendMessage('agent', `Transferring your clinical notes to the ${agentUI.name}...`);
                    
                    try {
                        const response = await fetch(API_BASE_URL + '/api/v1/medical/api/chat', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                cin: chatCIN, 
                                message: "[INITIALIZE]",
                                agent: currentAgent
                            })
                        });
                        const data = await response.json();
                        
                        if (data.status === 'success') {
                            appendMessage('agent', data.response);
                        }
                    } catch (err) {
                        console.error('Transfer error:', err);
                        appendMessage('agent', 'Hello. I am the Pneumologist. I have reviewed your case from the GP. How are you breathing now?');
                    }
                });
            }
        
            const btnUploadBilanChat = document.getElementById('btn-upload-bilan-chat');
            if (btnUploadBilanChat) {
                btnUploadBilanChat.addEventListener('click', async () => {
                    const statusEl = document.getElementById('bilan-upload-status-chat');
                    const fileInput = document.getElementById('bilan-file-chat');
                    const file = fileInput?.files?.[0];
        
                    if (!chatCIN) {
                        statusEl.textContent = 'CIN is missing. Please restart consultation from triage.';
                        return;
                    }
                    if (!file) {
                        statusEl.textContent = 'Please choose a PDF file.';
                        return;
                    }
        
                    statusEl.textContent = 'Uploading blood test PDF...';
                    try {
                        const formData = new FormData();
                        formData.append('cin', chatCIN);
                        formData.append('file', file);
        
                        const response = await fetch(API_BASE_URL + '/api/v1/medical/api/bilan/upload', {
                            method: 'POST',
                            body: formData
                        });
                        const data = await response.json();
                        if (!response.ok || data.status !== 'success') {
                            throw new Error(data.detail || data.message || 'Upload failed');
                        }
        
                        statusEl.textContent = 'Blood test uploaded successfully.';
                        showBilanPanel(false);
                        appendMessage('agent', 'Blood test received. Launching integrated toxicology analysis...');
        
                        // Run Step 3 orchestrator directly instead of re-initializing question flow.
                        const finalizeResp = await fetch(API_BASE_URL + '/api/v1/medical/api/step3/finalize', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ cin: chatCIN })
                        });
                        const finalizeData = await finalizeResp.json();
                        if (!finalizeResp.ok || finalizeData.status !== 'success') {
                            throw new Error(finalizeData.detail || 'Step 3 analysis failed');
                        }
        
                        latestStep3Cin = finalizeData.cin || chatCIN;
                        const rawUrl = finalizeData.report_pdf_url || `/api/step3/report/pdf?cin=${encodeURIComponent(latestStep3Cin)}`;
                        latestStep3ReportUrl = rawUrl.startsWith('http') ? rawUrl : API_BASE_URL + '/api/v1/medical' + rawUrl;
        
                        // Keep toxicologist as active UI owner for continuity.
                        currentAgent = normalizeAgentName('toxicologist');
                        const nameEl = document.getElementById('agent-name');
                        const avatarEl = document.getElementById('agent-avatar');
                        if (nameEl) nameEl.textContent = 'Toxicologist Agent';
                        if (avatarEl) avatarEl.textContent = '🧪';
        
                        appendMessage('agent', formatStep3FinalMessage(finalizeData));
                        document.getElementById('report-actions')?.classList.remove('hidden');
                    } catch (err) {
                        statusEl.textContent = `Upload error: ${err.message}`;
                    }
                });
            }
        
            const btnDownloadFinalReport = document.getElementById('btn-download-final-report');
            if (btnDownloadFinalReport) {
                btnDownloadFinalReport.onclick = async () => {
                    const reportUrl = latestStep3ReportUrl || (latestStep3Cin ? API_BASE_URL + `/api/v1/medical/api/step3/report/pdf?cin=${encodeURIComponent(latestStep3Cin)}` : null);
                    if (!reportUrl) {
                        appendMessage('agent', 'No final report is available yet. Please complete blood-test analysis first.');
                        return;
                    }
        
                    try {
                        const response = await fetch(reportUrl);
                        if (!response.ok) {
                            let detail = 'Failed to download PDF report.';
                            try {
                                const errData = await response.json();
                                detail = errData?.detail || detail;
                            } catch (_) {}
                            throw new Error(detail);
                        }
                        const blob = await response.blob();
                        const objectUrl = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        const filename = `medical_report_${latestStep3Cin || chatCIN || 'patient'}.pdf`;
                        link.href = objectUrl;
                        link.download = filename;
                        document.body.appendChild(link);
                        link.click();
                        link.remove();
                        URL.revokeObjectURL(objectUrl);
                    } catch (err) {
                        appendMessage('agent', `Could not download final report: ${err.message}`);
                    }
                };
            }
        })();
        
    } catch(e) { console.error('Medical script error:', e); }
  }, []);

  return (
    <div className="medical-page" ref={containerRef} dangerouslySetInnerHTML={{ __html: `<div class="app-container">
        <aside class="sidebar">
            <div class="logo">
                <span class="logo-icon">🩺</span>
                <h1 data-i18n="app_title">Gabès Triage</h1>
            </div>
            <nav class="form-nav">
                <a href="#profile" class="nav-item active" data-i18n="nav_profile">Patient Profile</a>
                <a href="#environment" class="nav-item" data-i18n="nav_environment">Environment</a>
                <a href="#complaint" class="nav-item" data-i18n="nav_complaint">Chief Complaint</a>
                <a href="#symptoms" class="nav-item" data-i18n="nav_symptoms">Symptom Groups</a>
                <a href="#red-flags" class="nav-item danger" data-i18n="nav_red_flags">Red Flags</a>
                <a href="#history" class="nav-item" data-i18n="nav_history">Medical History</a>
            </nav>
        </aside>

        <main class="content">
            <header class="top-bar">
                <div class="status-badge" data-i18n="badge_preliminary">Phase: Preliminary Triage</div>
                <div class="lang-selector">
                    <span style="font-size: 0.8rem; opacity: 0.7;">🌐</span>
                    <select id="lang-select" class="lang-select">
                        <option value="en">English</option>
                        <option value="fr">Français</option>
                        <option value="ar">العربية</option>
                    </select>
                </div>
                <button id="btn-open-history" class="btn-secondary btn-history">Medical History</button>
                <div class="location-badge" data-i18n="badge_location">📍 Gabès, Tunisia</div>
            </header>

            <form id="triage-form" class="triage-form">
                <!-- Section: Profile -->
                <section id="profile" class="form-section">
                    <h2 data-i18n="sec_profile">Patient Profile</h2>
                    <div class="grid-2">
                        <div class="form-group">
                            <label for="name" data-i18n="label_name">Full Name</label>
                            <input type="text" id="name" name="name" required data-i18n-placeholder="ph_name" placeholder="John Doe">
                        </div>
                        <div class="form-group">
                            <label for="age" data-i18n="label_age">Age</label>
                            <input type="number" id="age" name="age" required min="0" max="120">
                        </div>
                        <div class="form-group">
                            <label for="cin" data-i18n="label_cin">CIN (National ID)</label>
                            <input type="text" id="cin" name="cin" required pattern="\\d{8}" maxlength="8" data-i18n-placeholder="ph_cin" placeholder="12345678">
                        </div>
                        <div class="form-group">
                            <label for="sex" data-i18n="label_sex">Sex at Birth</label>
                            <select id="sex" name="sex" required>
                                <option value="male" data-i18n="opt_male">Male</option>
                                <option value="female" data-i18n="opt_female">Female</option>
                                <option value="other" data-i18n="opt_other">Other</option>
                            </select>
                        </div>
                        <div class="grid-2">
                            <div class="form-group">
                                <label for="height" data-i18n="label_height">Height (cm)</label>
                                <input type="number" id="height" name="height" required>
                            </div>
                            <div class="form-group">
                                <label for="weight" data-i18n="label_weight">Weight (kg)</label>
                                <input type="number" id="weight" name="weight" required>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Section: Environment -->
                <section id="environment" class="form-section">
                    <h2 data-i18n="sec_environment">Location & Environment</h2>
                    <p class="section-desc" data-i18n="desc_environment">We ask these questions because the unique industrial environment of Gabès can impact your health.</p>
                    <div class="grid-2">
                        <div class="form-group">
                            <label for="neighborhood" data-i18n="label_neighborhood">Neighborhood / Area (Gabès)</label>
                            <input type="text" id="neighborhood" name="neighborhood" required data-i18n-placeholder="ph_neighborhood" placeholder="e.g. Chott El Ferik">
                        </div>
                        <div class="form-group">
                            <label for="proximity" data-i18n="label_proximity">Proximity to Industrial Plants</label>
                            <select id="proximity" name="proximity" required>
                                <option value="i_work_in_an_industrial_plant" data-i18n="opt_prox_work">I work in an industrial plant</option>
                                <option value="visible_from_home_or_work" data-i18n="opt_prox_visible">Visible from home or work</option>
                                <option value="frequent_chemical_smell" data-i18n="opt_prox_smell">I often smell chemicals/gas</option>
                                <option value="rarely_noticed" data-i18n="opt_prox_rarely">I rarely notice any industry signs</option>
                                <option value="very_far" data-i18n="opt_prox_far">I live/work very far from the industrial zone</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="occupation" data-i18n="label_occupation">Occupation</label>
                            <input type="text" id="occupation" name="occupation" required data-i18n-placeholder="ph_occupation" placeholder="e.g. Teacher, Nurse, Worker">
                        </div>
                        <div class="form-group">
                            <label for="smoking_status" data-i18n="label_smoking">Smoking Status</label>
                            <select id="smoking_status" name="smoking_status" required>
                                <option value="non-smoker" data-i18n="opt_smoke_never">Never smoked</option>
                                <option value="former" data-i18n="opt_smoke_former">Former smoker</option>
                                <option value="current" data-i18n="opt_smoke_current">Current smoker</option>
                            </select>
                        </div>
                        <div class="form-group span-2">
                            <label for="workplace_exposure" data-i18n="label_work_exposure">Specific Workplace Exposures</label>
                            <input type="text" id="workplace_exposure" name="workplace_exposure" data-i18n-placeholder="ph_work_exposure" placeholder="e.g. Asbestos, Lead, Specific Chemicals (comma separated)">
                        </div>
                    </div>
                    <div class="checkbox-group">
                        <label data-i18n="label_obs">Environmental Observations at Home/Work:</label>
                        <div class="checkbox-options grid-2">
                            <label><input type="checkbox" name="pollution_obs" value="visible_smoke"> <span data-i18n="opt_obs_smoke">Visible smoke or flares</span></label>
                            <label><input type="checkbox" name="pollution_obs" value="chemical_smells"> <span data-i18n="opt_obs_odor">Strong chemical odors</span></label>
                            <label><input type="checkbox" name="pollution_obs" value="dust_accumulation"> <span data-i18n="opt_obs_dust">White/Black dust on surfaces</span></label>
                            <label><input type="checkbox" name="pollution_obs" value="noise"> <span data-i18n="opt_obs_noise">Industrial noise</span></label>
                        </div>
                    </div>
                    <div class="checkbox-group margin-top">
                        <label data-i18n="label_worse_near">Symptoms feel worse near:</label>
                        <div class="checkbox-options">
                            <label><input type="checkbox" name="worse_near" value="industry"> <span data-i18n="opt_wn_industry">Industry</span></label>
                            <label><input type="checkbox" name="worse_near" value="sea"> <span data-i18n="opt_wn_sea">Sea</span></label>
                            <label><input type="checkbox" name="worse_near" value="dust"> <span data-i18n="opt_wn_dust">Dust</span></label>
                            <label><input type="checkbox" name="worse_near" value="smoke"> <span data-i18n="opt_wn_smoke">Smoke</span></label>
                        </div>
                    </div>
                </section>

                <!-- Section: Complaint -->
                <section id="complaint" class="form-section">
                    <h2 data-i18n="sec_complaint">Chief Complaint</h2>
                    <div class="form-group">
                        <label for="main_problem" data-i18n="label_main_problem">Main Problem</label>
                        <textarea id="main_problem" name="main_problem" required rows="3" data-i18n-placeholder="ph_main_problem" placeholder="Describe what is going on..."></textarea>
                    </div>
                    <div class="grid-2">
                        <div class="form-group">
                            <label for="onset" data-i18n="label_onset">Onset</label>
                            <select id="onset" name="onset">
                                <option value="gradual" data-i18n="opt_onset_gradual">Gradual</option>
                                <option value="sudden" data-i18n="opt_onset_sudden">Sudden</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="severity" data-i18n="label_severity">Severity (0-10)</label>
                            <input type="number" id="severity" name="severity" min="0" max="10">
                        </div>
                        <div class="form-group">
                            <label for="duration" data-i18n="label_duration">Duration</label>
                            <input type="text" id="duration" name="duration" required data-i18n-placeholder="ph_duration" placeholder="e.g. 3 days">
                        </div>
                        <div class="form-group">
                            <label for="progression" data-i18n="label_progression">Progression</label>
                            <input type="text" id="progression" name="progression" required data-i18n-placeholder="ph_progression" placeholder="e.g. Getting worse at night">
                        </div>
                    </div>
                </section>

                <!-- Section: Symptoms -->
                <section id="symptoms" class="form-section">
                    <h2 data-i18n="sec_symptoms">Symptom Groups</h2>
                    <div class="accordion">
                        <div class="accordion-item">
                            <h3 data-i18n="grp_respiratory">Respiratory</h3>
                            <div class="checkbox-grid">
                                <label><input type="checkbox" name="resp" value="cough"> <span data-i18n="symp_cough">Cough</span></label>
                                <label><input type="checkbox" name="resp" value="dyspnea"> <span data-i18n="symp_dyspnea">Dyspnea</span></label>
                                <label><input type="checkbox" name="resp" value="wheezing"> <span data-i18n="symp_wheezing">Wheezing</span></label>
                                <label><input type="checkbox" name="resp" value="hemoptysis"> <span data-i18n="symp_hemoptysis">Hemoptysis</span></label>
                                <label><input type="checkbox" name="resp" value="chest_tightness"> <span data-i18n="symp_chest_tight">Chest Tightness</span></label>
                            </div>
                        </div>
                        <div class="accordion-item">
                            <h3 data-i18n="grp_cardiac">Cardiac</h3>
                            <div class="checkbox-grid">
                                <label><input type="checkbox" name="cardiac" value="chest_pain"> <span data-i18n="symp_chest_pain">Chest Pain</span></label>
                                <label><input type="checkbox" name="cardiac" value="palpitations"> <span data-i18n="symp_palpitations">Palpitations</span></label>
                                <label><input type="checkbox" name="cardiac" value="syncope"> <span data-i18n="symp_syncope">Syncope</span></label>
                                <label><input type="checkbox" name="cardiac" value="leg_swelling"> <span data-i18n="symp_leg_swelling">Leg Swelling</span></label>
                            </div>
                        </div>
                        <div class="accordion-item">
                            <h3 data-i18n="grp_neurological">Neurological</h3>
                            <div class="checkbox-grid">
                                <label><input type="checkbox" name="neuro" value="headache"> <span data-i18n="symp_headache">Headache</span></label>
                                <label><input type="checkbox" name="neuro" value="dizziness"> <span data-i18n="symp_dizziness">Dizziness</span></label>
                                <label><input type="checkbox" name="neuro" value="weakness"> <span data-i18n="symp_weakness">Weakness</span></label>
                                <label><input type="checkbox" name="neuro" value="seizure"> <span data-i18n="symp_seizure">Seizure</span></label>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Section: Red Flags -->
                <section id="red-flags" class="form-section danger-zone">
                    <h2 data-i18n="sec_red_flags">Red Flags (Emergency)</h2>
                    <p class="warning" data-i18n="desc_red_flags">Mark any critical symptoms below.</p>
                    <div class="checkbox-grid">
                        <label><input type="checkbox" name="red_flags" value="severe_breathing_difficulty"> <span data-i18n="symp_severe_resp">Severe Breathing Difficulty</span></label>
                        <label><input type="checkbox" name="red_flags" value="crushing_chest_pain"> <span data-i18n="symp_crushing_pain">Crushing Chest Pain</span></label>
                        <label><input type="checkbox" name="red_flags" value="confusion"> <span data-i18n="symp_confusion">Confusion/Fainting</span></label>
                        <label><input type="checkbox" name="red_flags" value="toxic_exposure_event"> <span data-i18n="symp_toxic_event">Major Toxic Exposure Event</span></label>
                    </div>
                </section>

                <!-- Section: History -->
                <section id="history" class="form-section">
                    <h2 data-i18n="sec_history">Medical History</h2>
                    <div class="checkbox-grid">
                        <label><input type="checkbox" name="history" value="asthma"> <span data-i18n="hist_asthma">Asthma</span></label>
                        <label><input type="checkbox" name="history" value="copd"> <span data-i18n="hist_copd">COPD</span></label>
                        <label><input type="checkbox" name="history" value="hypertension"> <span data-i18n="hist_hypertension">Hypertension</span></label>
                        <label><input type="checkbox" name="history" value="diabetes"> <span data-i18n="hist_diabetes">Diabetes</span></label>
                        <label><input type="checkbox" name="history" value="heart_disease"> <span data-i18n="hist_heart">Heart Disease</span></label>
                    </div>
                    <div class="grid-2 margin-top">
                        <div class="form-group">
                            <label for="medications" data-i18n="label_medications">Current Medications</label>
                            <textarea id="medications" name="medications" rows="2" data-i18n-placeholder="ph_medications" placeholder="List medications separated by commas..."></textarea>
                        </div>
                        <div class="form-group">
                            <label for="family_history" data-i18n="label_family_history">Family History</label>
                            <textarea id="family_history" name="family_history" rows="2" data-i18n-placeholder="ph_family_history" placeholder="Note chronic diseases in family..."></textarea>
                        </div>
                    </div>
                </section>

                <div class="form-actions">
                    <button type="submit" class="btn-primary" data-i18n="btn_submit">Analyze & Triage</button>
                    <button type="reset" class="btn-secondary" data-i18n="btn_reset">Reset Form</button>
                </div>
            </form>

            <!-- Results Overlay -->
            <div id="results-overlay" class="results-overlay hidden">
                <div class="results-card">
                    <button class="close-results">&times;</button>
                    <header class="results-header">
                        <div class="urgency-indicator" id="result-urgency" data-i18n="res_urgency_placeholder">LOW</div>
                        <h2 data-i18n="res_title">Triage Analysis Result</h2>
                    </header>
                    <div class="results-body">
                        <div class="result-item">
                            <h3 data-i18n="res_summary">Summary</h3>
                            <p id="result-summary"></p>
                        </div>
                        <div class="result-item">
                            <h3 data-i18n="res_specialty">Recommended Specialty</h3>
                            <div class="specialty-badge" id="result-specialty">Generalist</div>
                            <p id="result-route-text" class="route-text"></p>
                        </div>
                        <div class="result-item">
                            <h3 data-i18n="res_next_steps">Next Steps</h3>
                            <p id="result-next-step"></p>
                        </div>
                        <div class="disclaimer-box">
                            <strong data-i18n="res_disclaimer_title">Medical Disclaimer:</strong>
                            <p id="result-disclaimer"></p>
                        </div>
                        <div class="form-actions result-actions">
                            <button id="btn-consult" class="btn-primary" data-i18n="btn_consult">Consult Specialist</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Agentic Chat Section -->
            <div id="chat-section" class="chat-section hidden">
                <div class="chat-container">
                    <header class="chat-header">
                        <div class="agent-info">
                            <div class="agent-avatar" id="agent-avatar">🩺</div>
                            <div>
                                <h3 id="agent-name">Medical Agent</h3>
                                <span id="agent-status">Online</span>
                            </div>
                        </div>
                        <button class="close-chat">&times;</button>
                    </header>
                    <div id="chat-messages" class="chat-messages">
                        <!-- Messages appended here -->
                    </div>
                    <div class="chat-input-area">
                        <input type="text" id="chat-input" data-i18n-placeholder="ph_chat_input" placeholder="Type your message...">
                        <button id="btn-send-chat" class="btn-send">
                            <svg viewBox="0 0 24 24" width="24" height="24">
                                <path fill="currentColor" d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path>
                            </svg>
                        </button>
                    </div>
                    <div id="bilan-upload-panel-chat" class="chat-bilan-upload is-hidden">
                        <div class="upload-inline">
                            <input type="file" id="bilan-file-chat" accept=".pdf,application/pdf">
                            <button id="btn-upload-bilan-chat" class="btn-secondary">Upload Blood Test PDF</button>
                        </div>
                        <p id="bilan-upload-status-chat" class="upload-status"></p>
                    </div>
                    <div id="chat-actions" class="chat-actions hidden">
                        <button id="btn-transfer" class="btn-secondary danger" data-i18n="btn_transfer">Transfer me to Specialist</button>
                    </div>
                    <div id="report-actions" class="chat-actions hidden">
                        <button id="btn-download-final-report" class="btn-secondary">Download Final Report PDF</button>
                    </div>
                </div>
            </div>

            <div id="history-modal" class="history-modal hidden">
                <div class="history-modal-card">
                    <header class="history-modal-header">
                        <h3>Medical History</h3>
                        <button id="btn-close-history" class="close-history">&times;</button>
                    </header>
                    <div class="history-modal-body">
                        <div class="history-search-row">
                            <input type="text" id="history-cin-input" maxlength="8" placeholder="Enter CIN (8 digits)">
                            <button id="btn-load-history" class="btn-primary">Load Records</button>
                        </div>
                        <p id="history-status" class="history-status"></p>
                        <div id="history-records" class="history-records"></div>
                    </div>
                </div>
            </div>
        </main>
    </div>` }} />
  );
};

export default Medical;
