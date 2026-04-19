"""
data.py - Python mirror of data.js
User profile data for the agents to consume.
"""

USER_DATA = {
    "identite": {
        "nom": "Ben Ali",
        "prenom": "Sami",
        "age": 38,
        "salaire_tnd_accumule": 2500,
        "marier": "oui",
        "nb_enfants": 2,
        "age_moyen_enfants": 8,
        "depenses_mensuelles_tnd": 1800,
        "credits_en_cours_tnd": 300,
        "epargne_tnd": 5000,
        "revenus_supplementaires_tnd": 200,
        "propriete_logement": "locataire",
        "budget_renovation_tnd": 3000,
    },
    "logement": {
        "type_maison": "appartement",
        "nb_etages": 0,
        "surface_m2": 85,
        "emplacement": "Gabes Ouedref",
        "environement": "urbain",
        "orientation_solaire": "sud",
        "annee_construction": 2005,
        "isolation_quality": "moyenne",
        "type_chauffage": "climatiseur",
        "type_eau_chaude": "chauffe_eau_electrique",
        "equipements_energie": [
            "climatiseur", "lave_linge", "refrigerateur", "television", "ordinateur"
        ],
        "panneaux_solaires_existants": False,
        "jardin_ou_terrasse": False,
    },
    "consommation": {
        "avg_facture_steg_tnd": 80,
        "meteo_avg_celsius": 22,
        "consommation_kwh_mensuelle": 320,
        "heures_soleil_annuelles": 3000,
        "taux_co2_kg_par_an": 1840,
        "eau_consommation_m3_mois": 8,
        "transport": {
            "type_vehicule": "voiture_essence",
            "km_par_mois": 600,
        },
    },
}
