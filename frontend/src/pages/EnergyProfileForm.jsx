import { useState, useEffect, useRef, useCallback } from "react";
import "./Energy.css";

/* ─────────────────────────────────────────────────────────────
   Gabès bounding box (tight)
   SW: 33.70°N 9.90°E   NE: 34.10°N 10.35°E
───────────────────────────────────────────────────────────── */
const GABES_BOUNDS = {
  sw: { lat: 33.70, lng: 9.90 },
  ne: { lat: 34.10, lng: 10.35 },
};
const GABES_CENTER = { lat: 33.8815, lng: 10.0982 };

/* ─── Leaflet (no API key needed) ────────────────────────────── */
function MapPicker({ value, onChange }) {
  const mapRef = useRef(null);
  const leafletMap = useRef(null);
  const markerRef = useRef(null);

  useEffect(() => {
    if (leafletMap.current) return; // already initialised

    // Dynamically load Leaflet CSS + JS
    if (!document.getElementById("leaflet-css")) {
      const link = document.createElement("link");
      link.id = "leaflet-css";
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(link);
    }

    const loadLeaflet = () => {
      if (window.L) {
        initMap();
      } else {
        const script = document.createElement("script");
        script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
        script.onload = initMap;
        document.head.appendChild(script);
      }
    };

    loadLeaflet();

    function initMap() {
      const L = window.L;
      const bounds = L.latLngBounds(
        [GABES_BOUNDS.sw.lat, GABES_BOUNDS.sw.lng],
        [GABES_BOUNDS.ne.lat, GABES_BOUNDS.ne.lng]
      );

      const map = L.map(mapRef.current, {
        center: [GABES_CENTER.lat, GABES_CENTER.lng],
        zoom: 12,
        maxBounds: bounds,
        maxBoundsViscosity: 1.0,
        minZoom: 10,
      });

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
      }).addTo(map);

      // Draw restriction outline
      L.rectangle(bounds, {
        color: "#00e5ff",
        weight: 2,
        fillOpacity: 0.04,
        dashArray: "6 4",
      }).addTo(map);

      // If we already have coords place the marker
      if (value?.lat && value?.lng) {
        markerRef.current = L.marker([value.lat, value.lng], {
          draggable: true,
        }).addTo(map);
        markerRef.current.on("dragend", (e) => {
          const { lat, lng } = e.target.getLatLng();
          handleLatLng(lat, lng);
        });
      }

      map.on("click", (e) => {
        const { lat, lng } = e.latlng;
        if (
          lat < GABES_BOUNDS.sw.lat ||
          lat > GABES_BOUNDS.ne.lat ||
          lng < GABES_BOUNDS.sw.lng ||
          lng > GABES_BOUNDS.ne.lng
        ) {
          return; // outside – ignore
        }
        handleLatLng(lat, lng);
      });

      leafletMap.current = map;

      function handleLatLng(lat, lng) {
        if (markerRef.current) {
          markerRef.current.setLatLng([lat, lng]);
        } else {
          markerRef.current = L.marker([lat, lng], { draggable: true }).addTo(map);
          markerRef.current.on("dragend", (ev) => {
            const p = ev.target.getLatLng();
            handleLatLng(p.lat, p.lng);
          });
        }
        // Reverse geocode with Nominatim
        fetch(
          `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`
        )
          .then((r) => r.json())
          .then((d) => {
            const label =
              d.address?.suburb ||
              d.address?.village ||
              d.address?.quarter ||
              d.address?.city_district ||
              d.address?.city ||
              "Gabès";
            onChange({ lat, lng, label });
          })
          .catch(() => onChange({ lat, lng, label: "Gabès" }));
      }
    }

    return () => {
      if (leafletMap.current) {
        leafletMap.current.remove();
        leafletMap.current = null;
        markerRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <div ref={mapRef} className="map-container" />;
}

/* ─── Open-Meteo fetch helper ─────────────────────────────────── */
async function fetchSolarData(lat, lng) {
  // Simpler: use current-weather for avg temp + derive solar hours for Gabès
  const weatherUrl =
    `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}` +
    `&daily=sunshine_duration,shortwave_radiation_sum,temperature_2m_max,temperature_2m_min` +
    `&forecast_days=16&timezone=Africa%2FTunis`;

  const res = await fetch(weatherUrl);
  if (!res.ok) throw new Error("Open-Meteo unreachable");
  const d = await res.json();

  const daily = d.daily;
  // avg temp from 16-day forecast
  const avgMax =
    daily.temperature_2m_max.reduce((a, b) => a + b, 0) /
    daily.temperature_2m_max.length;
  const avgMin =
    daily.temperature_2m_min.reduce((a, b) => a + b, 0) /
    daily.temperature_2m_min.length;
  const avgTemp = ((avgMax + avgMin) / 2).toFixed(1);

  // sunshine_duration is in seconds/day; annualise
  const avgSunSec =
    daily.sunshine_duration.reduce((a, b) => a + b, 0) /
    daily.sunshine_duration.length;
  const annualSunHours = Math.round((avgSunSec / 3600) * 365);

  // Derive solar orientation from Sun path at this latitude/longitude
  // (simplified: Gabès is south-facing optimal → detect deviation)
  const orientation = deriveOrientation(lng);

  return { avgTemp, annualSunHours, orientation };
}

function deriveOrientation() {
  // Gabès longitude ~10.1°E — buildings facing south is ideal in North Africa
  // We keep it as "sud" since this is an auto-suggestion
  return "sud";
}

function computeCO2(kwh) {
  // Tunisia grid factor: 0.48 kg CO2 / kWh (ANME)
  return Math.round(kwh * 12 * 0.48);
}

/* ─── Step config ─────────────────────────────────────────────── */
const STEPS = [
  { id: "identite", label: "Identité", icon: "👤" },
  { id: "logement", label: "Logement", icon: "🏠" },
  { id: "consommation", label: "Consommation", icon: "⚡" },
  { id: "transport", label: "Transport", icon: "🚗" },
];

/* ─── Initial form state ──────────────────────────────────────── */
const INITIAL = {
  identite: {
    nom: "",
    prenom: "",
    age: "",
    salaire_tnd_accumulé: "",
    marier: "non",
    nb_enfants: 0,
    age_moyen_enfants: "",
    depenses_mensuelles_tnd: "",
    credits_en_cours_tnd: "",
    epargne_tnd: "",
    revenus_supplementaires_tnd: "",
    propriete_logement: "locataire",
    budget_renovation_tnd: "",
  },
  logement: {
    type_maison: "appartement",
    nb_etages: 0,
    surface_m2: "",
    emplacement: "",
    emplacement_coords: null,
    environement: "urbain",
    orientation_solaire: "",      // from API
    isolation_quality: "moyenne",
    type_chauffage: "climatiseur",
    type_eau_chaude: "chauffe_eau_electrique",
    equipements_energie: [],
    jardin_ou_terrasse: false,
  },
  consommation: {
    avg_facture_steg_tnd: "",
    meteo_avg_celsius: "",        // from API
    consommation_kwh_mensuelle: "",
    heures_soleil_annuelles: "",  // from API
    taux_co2_kg_par_an: "",       // computed
    eau_consommation_m3_mois: "",
    transport: {
      type_vehicule: "voiture_essence",
      km_par_mois: "",
    },
  },
};

const EQUIPEMENTS_OPTIONS = [
  "climatiseur", "lave_linge", "refrigerateur", "television",
  "ordinateur", "chauffe_eau_solaire", "lave_vaisselle", "congelateur",
];

/* ══════════════════════════════════════════════════════════════
   Main Component
══════════════════════════════════════════════════════════════ */
export default function ProfileForm({ onBack, onSubmit }) {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(INITIAL);
  const [apiLoading, setApiLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState(null); // null | "ok" | "err"
  const [jsonPreview, setJsonPreview] = useState(null);
  const [downloaded, setDownloaded] = useState(false);
  const [errors, setErrors] = useState({});

  /* ── nested patch helper ─────────────────────────────────── */
  const patch = useCallback((section, key, value) => {
    setForm((prev) => ({
      ...prev,
      [section]: { ...prev[section], [key]: value },
    }));
  }, []);

  const patchTransport = useCallback((key, value) => {
    setForm((prev) => ({
      ...prev,
      consommation: {
        ...prev.consommation,
        transport: { ...prev.consommation.transport, [key]: value },
      },
    }));
  }, []);

  /* ── Auto-compute CO2 when kWh changes ───────────────────── */
  useEffect(() => {
    const kwh = parseFloat(form.consommation.consommation_kwh_mensuelle);
    if (!isNaN(kwh) && kwh > 0) {
      const co2Update = setTimeout(() => {
        patch("consommation", "taux_co2_kg_par_an", computeCO2(kwh));
      }, 0);
      return () => clearTimeout(co2Update);
    }
    return undefined;
  }, [form.consommation.consommation_kwh_mensuelle, patch]);

  /* ── Fetch solar/meteo data when coords change ───────────── */
  const handleLocationChange = useCallback(
    async (locObj) => {
      patch("logement", "emplacement", locObj.label);
      patch("logement", "emplacement_coords", { lat: locObj.lat, lng: locObj.lng });

      setApiLoading(true);
      setApiStatus(null);
      try {
        const { avgTemp, annualSunHours, orientation } = await fetchSolarData(
          locObj.lat,
          locObj.lng
        );
        patch("consommation", "meteo_avg_celsius", avgTemp);
        patch("consommation", "heures_soleil_annuelles", annualSunHours);
        patch("logement", "orientation_solaire", orientation);
        setApiStatus("ok");
      } catch {
        setApiStatus("err");
      } finally {
        setApiLoading(false);
      }
    },
    [patch]
  );

  /* ── Equipment toggle ────────────────────────────────────── */
  const toggleEquipement = (item) => {
    setForm((prev) => {
      const list = prev.logement.equipements_energie;
      const next = list.includes(item)
        ? list.filter((x) => x !== item)
        : [...list, item];
      return { ...prev, logement: { ...prev.logement, equipements_energie: next } };
    });
  };

  /* ── Basic validation per step ───────────────────────────── */
  const validate = () => {
    const e = {};
    if (step === 0) {
      if (!form.identite.nom) e.nom = "Requis";
      if (!form.identite.prenom) e.prenom = "Requis";
      if (!form.identite.age) e.age = "Requis";
      if (!form.identite.salaire_tnd_accumulé) e.salaire = "Requis";
    }
    if (step === 1) {
      if (!form.logement.emplacement) e.emplacement = "Sélectionnez un point sur la carte";
      if (!form.logement.surface_m2) e.surface = "Requis";
    }
    if (step === 2) {
      if (!form.consommation.avg_facture_steg_tnd) e.facture = "Requis";
      if (!form.consommation.consommation_kwh_mensuelle) e.kwh = "Requis";
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const next = () => {
    if (validate()) {
      setStep((s) => Math.min(s + 1, STEPS.length - 1));
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      // Auto-scroll to top of form to show errors
      const card = document.querySelector(".pf-card");
      if (card) card.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };
  const prev = () => setStep((s) => Math.max(s - 1, 0));

  /* ── Build final JSON & download ────────────────────────── */
  const buildJson = () => {
    const { emplacement_coords, ...logementRest } = form.logement;
    return {
      identite: {
        ...form.identite,
        age: Number(form.identite.age),
        salaire_tnd_accumulé: Number(form.identite.salaire_tnd_accumulé),
        nb_enfants: Number(form.identite.nb_enfants),
        age_moyen_enfants: Number(form.identite.age_moyen_enfants) || 0,
        depenses_mensuelles_tnd: Number(form.identite.depenses_mensuelles_tnd),
        credits_en_cours_tnd: Number(form.identite.credits_en_cours_tnd),
        epargne_tnd: Number(form.identite.epargne_tnd),
        revenus_supplementaires_tnd: Number(form.identite.revenus_supplementaires_tnd),
        budget_renovation_tnd: Number(form.identite.budget_renovation_tnd),
      },
      logement: {
        ...logementRest,
        nb_etages: Number(logementRest.nb_etages),
        surface_m2: Number(logementRest.surface_m2),
        coords: emplacement_coords,
      },
      consommation: {
        avg_facture_steg_tnd: Number(form.consommation.avg_facture_steg_tnd),
        meteo_avg_celsius: Number(form.consommation.meteo_avg_celsius),
        consommation_kwh_mensuelle: Number(form.consommation.consommation_kwh_mensuelle),
        heures_soleil_annuelles: Number(form.consommation.heures_soleil_annuelles),
        taux_co2_kg_par_an: Number(form.consommation.taux_co2_kg_par_an),
        eau_consommation_m3_mois: Number(form.consommation.eau_consommation_m3_mois),
        transport: {
          type_vehicule: form.consommation.transport.type_vehicule,
          km_par_mois: Number(form.consommation.transport.km_par_mois),
        },
      },
    };
  };

  const handleSubmit = () => {
    if (!validate()) {
      const card = document.querySelector(".pf-card");
      if (card) card.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    const json = buildJson();
    setJsonPreview(json);
  };

  const downloadJson = () => {
    const blob = new Blob([JSON.stringify(jsonPreview, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `profil_${jsonPreview.identite.nom}_${jsonPreview.identite.prenom}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setDownloaded(true);
  };

  /* ─────────────────── RENDER ─────────────────────────────── */
  if (jsonPreview) {
    return (
      <JsonSuccess
        data={jsonPreview}
        onDownload={downloadJson}
        onBack={onBack}
        downloaded={downloaded}
        onLaunch={() => onSubmit(jsonPreview)}
      />
    );
  }

  return (
    <div className="pf-root energy-unified-profile">
      {/* Header */}
      <div className="pf-header">
        <button className="pf-back-btn" onClick={onBack}>← Retour</button>
        <h1 className="pf-title">Profil Énergétique</h1>
        <p className="pf-subtitle">
          Remplissez votre profil pour générer une analyse IA personnalisée
        </p>
      </div>

      {/* Step indicator */}
      <div className="pf-stepper">
        {STEPS.map((s, i) => (
          <div
            key={s.id}
            className={`pf-step ${i === step ? "pf-step--active" : ""} ${i < step ? "pf-step--done" : ""}`}
            onClick={() => i < step && setStep(i)}
          >
            <div className="pf-step__circle">
              {i < step ? "✓" : s.icon}
            </div>
            <span className="pf-step__label">{s.label}</span>
            {i < STEPS.length - 1 && <div className="pf-step__line" />}
          </div>
        ))}
      </div>

      {/* Card */}
      <div className="pf-card">
        {step === 0 && <StepIdentite form={form.identite} patch={(k, v) => patch("identite", k, v)} errors={errors} />}
        {step === 1 && (
          <StepLogement
            form={form.logement}
            patch={(k, v) => patch("logement", k, v)}
            onLocationChange={handleLocationChange}
            toggleEquipement={toggleEquipement}
            apiLoading={apiLoading}
            apiStatus={apiStatus}
            errors={errors}
          />
        )}
        {step === 2 && <StepConsommation form={form.consommation} patch={(k, v) => patch("consommation", k, v)} errors={errors} />}
        {step === 3 && <StepTransport form={form.consommation.transport} patch={patchTransport} />}
      </div>

      {/* Navigation */}
      <div className="pf-nav">
        {step > 0 && (
          <button className="pf-btn pf-btn--secondary" onClick={prev}>
            ← Précédent
          </button>
        )}
        {step < STEPS.length - 1 ? (
          <button className="pf-btn pf-btn--primary" onClick={next}>
            Suivant →
          </button>
        ) : (
          <button className="pf-btn pf-btn--submit" onClick={handleSubmit}>
            🎯 Générer le profil JSON
          </button>
        )}
      </div>

      {/* Progress bar */}
      <div className="pf-progress-bar">
        <div
          className="pf-progress-fill"
          style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
        />
      </div>
    </div>
  );
}

/* ══════════════════ STEP 1 — Identité ══════════════════════ */
function StepIdentite({ form, patch, errors }) {
  return (
    <div className="pf-fields">
      <div className="pf-section-title">
        <span>👤</span> Informations personnelles
      </div>

      <div className="pf-row">
        <Field label="Prénom" error={errors.prenom}>
          <input className={`pf-input ${errors.prenom ? "pf-input--err" : ""}`} value={form.prenom}
            onChange={(e) => patch("prenom", e.target.value)} placeholder="Sami" />
        </Field>
        <Field label="Nom" error={errors.nom}>
          <input className={`pf-input ${errors.nom ? "pf-input--err" : ""}`} value={form.nom}
            onChange={(e) => patch("nom", e.target.value)} placeholder="Ben Ali" />
        </Field>
      </div>

      <div className="pf-row">
        <Field label="Âge" error={errors.age}>
          <input className={`pf-input ${errors.age ? "pf-input--err" : ""}`} type="number" min="18" max="100"
            value={form.age} onChange={(e) => patch("age", e.target.value)} placeholder="38" />
        </Field>
        <Field label="Situation matrimoniale">
          <select className="pf-input" value={form.marier} onChange={(e) => patch("marier", e.target.value)}>
            <option value="non">Célibataire</option>
            <option value="oui">Marié(e)</option>
            <option value="divorce">Divorcé(e)</option>
          </select>
        </Field>
      </div>

      <div className="pf-row">
        <Field label="Nb. enfants">
          <input className="pf-input" type="number" min="0" max="20"
            value={form.nb_enfants} onChange={(e) => patch("nb_enfants", e.target.value)} />
        </Field>
        <Field label="Âge moyen enfants">
          <input className="pf-input" type="number" min="0" max="30"
            value={form.age_moyen_enfants} onChange={(e) => patch("age_moyen_enfants", e.target.value)} placeholder="0" />
        </Field>
      </div>

      <div className="pf-section-title" style={{ marginTop: "24px" }}>
        <span>💰</span> Situation financière
      </div>

      <div className="pf-row">
        <Field label="Salaire mensuel (TND)" error={errors.salaire}>
          <input className={`pf-input ${errors.salaire ? "pf-input--err" : ""}`} type="number"
            value={form.salaire_tnd_accumulé} onChange={(e) => patch("salaire_tnd_accumulé", e.target.value)} placeholder="2500" />
        </Field>
        <Field label="Revenus supplémentaires (TND)">
          <input className="pf-input" type="number"
            value={form.revenus_supplementaires_tnd} onChange={(e) => patch("revenus_supplementaires_tnd", e.target.value)} placeholder="200" />
        </Field>
      </div>

      <div className="pf-row">
        <Field label="Dépenses mensuelles (TND)">
          <input className="pf-input" type="number"
            value={form.depenses_mensuelles_tnd} onChange={(e) => patch("depenses_mensuelles_tnd", e.target.value)} placeholder="1800" />
        </Field>
        <Field label="Crédits en cours (TND/mois)">
          <input className="pf-input" type="number"
            value={form.credits_en_cours_tnd} onChange={(e) => patch("credits_en_cours_tnd", e.target.value)} placeholder="300" />
        </Field>
      </div>

      <div className="pf-row">
        <Field label="Épargne actuelle (TND)">
          <input className="pf-input" type="number"
            value={form.epargne_tnd} onChange={(e) => patch("epargne_tnd", e.target.value)} placeholder="5000" />
        </Field>
        <Field label="Budget rénovation énergétique (TND)">
          <input className="pf-input" type="number"
            value={form.budget_renovation_tnd} onChange={(e) => patch("budget_renovation_tnd", e.target.value)} placeholder="3000" />
        </Field>
      </div>

      <Field label="Statut propriété">
        <div className="pf-radio-group">
          {["proprietaire", "locataire"].map((v) => (
            <label key={v} className={`pf-radio ${form.propriete_logement === v ? "pf-radio--active" : ""}`}>
              <input type="radio" name="propriete" value={v} checked={form.propriete_logement === v}
                onChange={() => patch("propriete_logement", v)} />
              {v === "proprietaire" ? "🏡 Propriétaire" : "🔑 Locataire"}
            </label>
          ))}
        </div>
      </Field>
    </div>
  );
}

/* ══════════════════ STEP 2 — Logement ══════════════════════ */
function StepLogement({ form, patch, onLocationChange, toggleEquipement, apiLoading, apiStatus, errors }) {
  return (
    <div className="pf-fields">
      <div className="pf-section-title"><span>🏠</span> Type de logement</div>

      <div className="pf-row">
        <Field label="Type de logement">
          <select className="pf-input" value={form.type_maison} onChange={(e) => patch("type_maison", e.target.value)}>
            <option value="appartement">Appartement</option>
            <option value="maison">Maison individuelle</option>
            <option value="villa">Villa</option>
            <option value="studio">Studio</option>
          </select>
        </Field>
        <Field label="Étages">
          <input className="pf-input" type="number" min="0" max="50"
            value={form.nb_etages} onChange={(e) => patch("nb_etages", e.target.value)} />
        </Field>
      </div>

      <div className="pf-row">
        <Field label="Surface (m²)" error={errors.surface}>
          <input className={`pf-input ${errors.surface ? "pf-input--err" : ""}`} type="number"
            value={form.surface_m2} onChange={(e) => patch("surface_m2", e.target.value)} placeholder="85" />
        </Field>
        <Field label="Qualité isolation">
          <select className="pf-input" value={form.isolation_quality} onChange={(e) => patch("isolation_quality", e.target.value)}>
            <option value="faible">Faible</option>
            <option value="moyenne">Moyenne</option>
            <option value="bonne">Bonne</option>
          </select>
        </Field>
      </div>

      <div className="pf-row">
        <Field label="Environnement">
          <select className="pf-input" value={form.environement} onChange={(e) => patch("environement", e.target.value)}>
            <option value="urbain">Urbain</option>
            <option value="periurbain">Péri-urbain</option>
            <option value="rural">Rural</option>
          </select>
        </Field>
        <Field label="Type chauffage">
          <select className="pf-input" value={form.type_chauffage} onChange={(e) => patch("type_chauffage", e.target.value)}>
            <option value="climatiseur">Climatiseur</option>
            <option value="gaz">Gaz</option>
            <option value="electricite">Électricité directe</option>
            <option value="pompe_chaleur">Pompe à chaleur</option>
          </select>
        </Field>
      </div>

      <Field label="Eau chaude sanitaire">
        <select className="pf-input" value={form.type_eau_chaude} onChange={(e) => patch("type_eau_chaude", e.target.value)}>
          <option value="chauffe_eau_electrique">Chauffe-eau électrique</option>
          <option value="chauffe_eau_gaz">Chauffe-eau gaz</option>
          <option value="chauffe_eau_solaire">Chauffe-eau solaire</option>
          <option value="thermodynamique">Thermodynamique</option>
        </select>
      </Field>

      <div className="pf-row" style={{ gap: "12px" }}>
        <label className="pf-checkbox">
          <input type="checkbox" checked={form.jardin_ou_terrasse}
            onChange={(e) => patch("jardin_ou_terrasse", e.target.checked)} />
          <span>🌿 Jardin / Terrasse</span>
        </label>
      </div>

      {/* Équipements */}
      <div className="pf-section-title" style={{ marginTop: "20px" }}><span>🔌</span> Équipements énergivores</div>
      <div className="pf-chips">
        {EQUIPEMENTS_OPTIONS.map((item) => (
          <button
            key={item}
            type="button"
            className={`pf-chip ${form.equipements_energie.includes(item) ? "pf-chip--active" : ""}`}
            onClick={() => toggleEquipement(item)}
          >
            {item.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      {/* Map */}
      <div className="pf-section-title" style={{ marginTop: "20px" }}>
        <span>📍</span> Emplacement — Gabès uniquement
        {errors.emplacement && <span className="pf-field-error"> · {errors.emplacement}</span>}
      </div>
      <p className="pf-map-hint">Cliquez sur la carte pour épingler votre adresse. Les données météo et solaires seront récupérées automatiquement.</p>

      <MapPicker value={form.emplacement_coords} onChange={onLocationChange} />

      {/* API status */}
      {(apiLoading || apiStatus || form.emplacement) && (
        <div className="pf-api-status">
          {apiLoading && (
            <div className="pf-api-item pf-api-item--loading">
              <span className="pf-spinner" /> Récupération des données météo &amp; solaires…
            </div>
          )}
          {!apiLoading && apiStatus === "ok" && (
            <div className="pf-api-item pf-api-item--ok">
              ✅ Données récupérées via Open-Meteo
            </div>
          )}
          {!apiLoading && apiStatus === "err" && (
            <div className="pf-api-item pf-api-item--err">
              ⚠️ Open-Meteo indisponible — saisissez manuellement
            </div>
          )}
          {form.emplacement && (
            <div className="pf-api-item pf-api-item--info">
              📍 {form.emplacement}
              {form.orientation_solaire && ` · Orientation: ${form.orientation_solaire}`}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ══════════════════ STEP 3 — Consommation ═══════════════════ */
function StepConsommation({ form, patch, errors }) {
  return (
    <div className="pf-fields">
      <div className="pf-section-title"><span>⚡</span> Consommation électrique</div>

      <div className="pf-row">
        <Field label="Facture STEG moyenne (TND/mois)" error={errors.facture}>
          <input className={`pf-input ${errors.facture ? "pf-input--err" : ""}`} type="number"
            value={form.avg_facture_steg_tnd} onChange={(e) => patch("avg_facture_steg_tnd", e.target.value)} placeholder="80" />
        </Field>
        <Field label="Consommation mensuelle (kWh)" error={errors.kwh}>
          <input className={`pf-input ${errors.kwh ? "pf-input--err" : ""}`} type="number"
            value={form.consommation_kwh_mensuelle} onChange={(e) => patch("consommation_kwh_mensuelle", e.target.value)} placeholder="320" />
        </Field>
      </div>

      <div className="pf-row">
        <Field label="Eau consommée (m³/mois)">
          <input className="pf-input" type="number"
            value={form.eau_consommation_m3_mois} onChange={(e) => patch("eau_consommation_m3_mois", e.target.value)} placeholder="8" />
        </Field>
      </div>

      {/* Read-only API fields */}
      <div className="pf-section-title" style={{ marginTop: "24px" }}>
        <span>🌡️</span> Données récupérées automatiquement
      </div>

      <div className="pf-api-fields">
        <ApiField
          label="Température moyenne (°C)"
          value={form.meteo_avg_celsius}
          unit="°C"
          icon="🌡️"
          onChange={(v) => patch("meteo_avg_celsius", v)}
        />
        <ApiField
          label="Heures soleil annuelles"
          value={form.heures_soleil_annuelles}
          unit="h/an"
          icon="☀️"
          onChange={(v) => patch("heures_soleil_annuelles", v)}
        />
        <ApiField
          label="Empreinte CO₂ estimée"
          value={form.taux_co2_kg_par_an}
          unit="kg/an"
          icon="🌿"
          readonly
          hint="Calculé depuis votre consommation kWh × 0.48 (facteur réseau tunisien)"
        />
      </div>
    </div>
  );
}

/* ══════════════════ STEP 4 — Transport ═════════════════════ */
function StepTransport({ form, patch }) {
  return (
    <div className="pf-fields">
      <div className="pf-section-title"><span>🚗</span> Mobilité &amp; Transport</div>

      <Field label="Type de véhicule">
        <div className="pf-vehicle-grid">
          {[
            { value: "voiture_essence", label: "⛽ Essence" },
            { value: "voiture_diesel", label: "🛢️ Diesel" },
            { value: "electrique", label: "⚡ Électrique" },
            { value: "velo", label: "🚲 Vélo" },
            { value: "transport_commun", label: "🚌 Commun" },
          ].map((v) => (
            <button
              key={v.value}
              type="button"
              className={`pf-vehicle-btn ${form.type_vehicule === v.value ? "pf-vehicle-btn--active" : ""}`}
              onClick={() => patch("type_vehicule", v.value)}
            >
              {v.label}
            </button>
          ))}
        </div>
      </Field>

      <Field label="Kilomètres par mois">
        <div style={{ position: "relative" }}>
          <input className="pf-input" type="number" min="0"
            value={form.km_par_mois} onChange={(e) => patch("km_par_mois", e.target.value)} placeholder="600" />
          <span className="pf-input-unit">km/mois</span>
        </div>
      </Field>

      <div className="pf-summary-box">
        <div className="pf-summary-row">
          <span>🚗 Type</span>
          <strong>{form.type_vehicule?.replace(/_/g, " ") || "—"}</strong>
        </div>
        <div className="pf-summary-row">
          <span>📏 Distance</span>
          <strong>{form.km_par_mois || "—"} km/mois</strong>
        </div>
        {form.type_vehicule === "voiture_essence" && form.km_par_mois && (
          <div className="pf-summary-row">
            <span>🌿 CO₂ transport</span>
            <strong>{Math.round(form.km_par_mois * 0.12 * 12)} kg/an</strong>
          </div>
        )}
      </div>
    </div>
  );
}

/* ══════════════════ Success Screen ═════════════════════════ */
function JsonSuccess({ data, onDownload, onBack, downloaded, onLaunch }) {
  return (
    <div className="pf-root energy-unified-profile">
      <div className="pf-success">
        <div className="pf-success__icon">🎉</div>
        <h2 className="pf-success__title">Profil généré avec succès !</h2>
        <p className="pf-success__sub">
          Votre profil énergétique est prêt. Téléchargez le fichier JSON pour l'utiliser avec les agents IA.
        </p>

        {/* Summary stats */}
        <div className="pf-success-stats">
          <div className="pf-stat-card">
            <div className="pf-stat-card__icon">☀️</div>
            <div className="pf-stat-card__val">{data.consommation.heures_soleil_annuelles || "—"}</div>
            <div className="pf-stat-card__label">h soleil/an</div>
          </div>
          <div className="pf-stat-card">
            <div className="pf-stat-card__icon">🌡️</div>
            <div className="pf-stat-card__val">{data.consommation.meteo_avg_celsius || "—"}°</div>
            <div className="pf-stat-card__label">temp. moy.</div>
          </div>
          <div className="pf-stat-card">
            <div className="pf-stat-card__icon">🌿</div>
            <div className="pf-stat-card__val">{data.consommation.taux_co2_kg_par_an || "—"}</div>
            <div className="pf-stat-card__label">kg CO₂/an</div>
          </div>
          <div className="pf-stat-card">
            <div className="pf-stat-card__icon">⚡</div>
            <div className="pf-stat-card__val">{data.consommation.consommation_kwh_mensuelle || "—"}</div>
            <div className="pf-stat-card__label">kWh/mois</div>
          </div>
        </div>

        <pre className="pf-json-preview">{JSON.stringify(data, null, 2)}</pre>

        <div className="pf-success-actions">
          <button className="pf-btn pf-btn--submit" onClick={onLaunch} style={{ padding: "13px 40px", fontSize: "1.05rem" }}>
            🚀 Lancer l'analyse directe
          </button>
          <button className="pf-btn pf-btn--secondary" onClick={onDownload}>
            {downloaded ? "✅ Téléchargé !" : "⬇️ Télécharger JSON"}
          </button>
          <button className="pf-btn pf-btn--secondary" onClick={onBack}>
            ← Retour
          </button>
        </div>
      </div>
    </div>
  );
}

/* ══════════════════ Helper sub-components ════════════════════ */
function Field({ label, children, error }) {
  return (
    <div className="pf-field">
      <label className="pf-label">{label}</label>
      {children}
      {error && <span className="pf-field-error">{error}</span>}
    </div>
  );
}

function ApiField({ label, value, unit, icon, onChange, readonly, hint }) {
  return (
    <div className={`pf-api-field ${readonly ? "pf-api-field--readonly" : ""}`}>
      <div className="pf-api-field__header">
        <span>{icon}</span>
        <span className="pf-api-field__label">{label}</span>
        {!readonly && <span className="pf-api-badge">AUTO</span>}
        {readonly && <span className="pf-api-badge pf-api-badge--calc">CALCULÉ</span>}
      </div>
      <div className="pf-api-field__row">
        <input
          className="pf-input pf-api-field__input"
          type="number"
          value={value}
          onChange={onChange ? (e) => onChange(e.target.value) : undefined}
          readOnly={readonly}
          placeholder="En attente de la carte…"
        />
        <span className="pf-api-field__unit">{unit}</span>
      </div>
      {hint && <span className="pf-api-field__hint">{hint}</span>}
    </div>
  );
}
