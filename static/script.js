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

document.addEventListener('DOMContentLoaded', () => {
    // 1. Language Initialization
    const langSelect = document.getElementById('lang-select');
    const savedLang = localStorage.getItem('preferred_lang') || 'en';
    setLanguage(savedLang);

    if (langSelect) {
        langSelect.addEventListener('change', (e) => {
            setLanguage(e.target.value);
        });
    }

    // 2. UI Elements
    const form = document.getElementById('triage-form');
    const overlay = document.getElementById('results-overlay');
    const closeBtn = document.querySelector('.close-results');

    // 3. Results UI Controller
    const displayResults = (result) => {
        const lang = localStorage.getItem('preferred_lang') || 'en';
        
        // Use rationale for summary
        document.getElementById('result-summary').textContent = result.rationale || "---";
        
        // Specialty Localization
        const specKey = `spec_${result.selected_specialty.toLowerCase()}`;
        document.getElementById('result-specialty').textContent = translations[lang][specKey] || result.selected_specialty.toUpperCase();
        
        document.getElementById('result-route-text').textContent = result.route_text || "";
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

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const loader = document.createElement('div');
            loader.className = 'loader-overlay';
            loader.innerHTML = '<div class="spinner"></div><p>Analyzing Triage Data...</p>';
            document.body.appendChild(loader);

            const formData = new FormData(form);
            const getCheckboxes = (name) => Array.from(document.querySelectorAll(`input[name="${name}"]:checked`)).map(cb => cb.value);
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
                const response = await fetch('/triage', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (!response.ok) throw new Error('Network error');
                const result = await response.json();
                displayResults(result);
            } catch (err) {
                alert('Connection Error: ' + err.message);
            } finally {
                loader.remove();
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
});

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
