const data = {
  identite: {
    nom: "Ben Ali",
    prenom: "Sami",
    age: 38,
    salaire_tnd_accumulé: 2500,
    marier: "oui",
    nb_enfants: 2,
    age_moyen_enfants: 8,
    // Added for finance agent robustness
    depenses_mensuelles_tnd: 1800,       // monthly spending estimate
    credits_en_cours_tnd: 300,           // monthly loan repayments
    epargne_tnd: 5000,                   // current savings
    revenus_supplementaires_tnd: 200,    // freelance / extra income
    propriete_logement: "locataire",     // "proprietaire" or "locataire"
    budget_renovation_tnd: 3000          // available budget for energy upgrades
  },
  logement: {
    type_maison: "appartement",
    nb_etages: 0,
    surface_m2: 85,                      // living area in m²
    emplacement: "Gabes Ouedref",
    environement: "urbain",
    orientation_solaire: "sud",          // "nord", "sud", "est", "ouest"
    annee_construction: 2005,
    isolation_quality: "moyenne",        // "faible", "moyenne", "bonne"
    // Added for env agent robustness
    type_chauffage: "climatiseur",       // "gaz", "electricite", "climatiseur", "pompe_chaleur"
    type_eau_chaude: "chauffe_eau_electrique",
    equipements_energie: [
      "climatiseur", "lave_linge", "refrigerateur", "television", "ordinateur"
    ],
    panneaux_solaires_existants: false,
    jardin_ou_terrasse: false
  },
  consommation: {
    avg_facture_steg_tnd: 80,            // avg monthly electricity bill
    meteo_avg_celsius: 22,
    // Added for env agent robustness
    consommation_kwh_mensuelle: 320,     // estimated monthly kWh
    heures_soleil_annuelles: 3000,       // solar hours per year (Gabes ~3000)
    taux_co2_kg_par_an: 1840,            // CO2 footprint estimate (320kWh * 12 * 0.48)
    eau_consommation_m3_mois: 8,         // monthly water usage
    transport: {
      type_vehicule: "voiture_essence",  // "voiture_essence", "voiture_diesel", "electrique", "velo", "transport_commun"
      km_par_mois: 600
    }
  }
}

// Export for use in Node/backend context
if (typeof module !== "undefined") {
  module.exports = data;
}