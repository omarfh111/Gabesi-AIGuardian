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
        const response = await fetch(`/api/patient/history?cin=${encodeURIComponent(cin)}`);
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
    const url = `/api/patient/history/report/pdf?cin=${encodeURIComponent(cin)}&case_id=${encodeURIComponent(caseId)}`;
    const response = await fetch(url);
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
    const btnOpenHistory = document.getElementById('btn-open-history');
    const historyModal = document.getElementById('history-modal');
    const btnCloseHistory = document.getElementById('btn-close-history');
    const btnLoadHistory = document.getElementById('btn-load-history');
    const historyCinInput = document.getElementById('history-cin-input');
    const historyRecords = document.getElementById('history-records');

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
        const response = await fetch('/api/chat', {
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
document.addEventListener('DOMContentLoaded', () => {
    const btnConsult = document.getElementById('btn-consult');
    if (btnConsult) {
        btnConsult.addEventListener('click', async () => {
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
                const response = await fetch('/api/chat', {
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
        });
    }

    const btnSendChat = document.getElementById('btn-send-chat');
    if (btnSendChat) btnSendChat.addEventListener('click', sendMessage);

    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
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
                const response = await fetch('/api/chat', {
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

                const response = await fetch('/api/bilan/upload', {
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
                const finalizeResp = await fetch('/api/step3/finalize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ cin: chatCIN })
                });
                const finalizeData = await finalizeResp.json();
                if (!finalizeResp.ok || finalizeData.status !== 'success') {
                    throw new Error(finalizeData.detail || 'Step 3 analysis failed');
                }

                latestStep3Cin = finalizeData.cin || chatCIN;
                latestStep3ReportUrl = finalizeData.report_pdf_url || `/api/step3/report/pdf?cin=${encodeURIComponent(latestStep3Cin)}`;

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
        btnDownloadFinalReport.addEventListener('click', async () => {
            const reportUrl = latestStep3ReportUrl || (latestStep3Cin ? `/api/step3/report/pdf?cin=${encodeURIComponent(latestStep3Cin)}` : null);
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
        });
    }
});
