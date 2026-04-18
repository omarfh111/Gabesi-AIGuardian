import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import json
from werkzeug.utils import secure_filename
import subprocess
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.analysis_pipeline import run_pipeline
from scripts.fetch_marine_data import fetch_and_process

load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER_INDUSTRY = 'data_an/raw/industry'
UPLOAD_FOLDER_FISHING = 'data_an/raw/fishing'
os.makedirs(UPLOAD_FOLDER_INDUSTRY, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_FISHING, exist_ok=True)

@app.route('/api/chat', methods=['POST'])
def chat():
    """RAG Agentic Chat Layer - Memory & Expert Persona"""
    # Grab the conversation history array if it exists, else fallback to just message
    messages_history = request.json.get('messages', [])
    user_input = request.json.get('message', '')
    
    if not messages_history and not user_input:
        return jsonify({"error": "Message is required"}), 400
        
    try:
        analysis_path = "data_an/processed/analysis_results.json"
        
        if "aujourd" in str(messages_history).lower() or "today" in str(messages_history).lower() or "aujourd" in user_input.lower():
             fetch_and_process()
             run_pipeline()
             
        if not os.path.exists(analysis_path):
            latest_analysis = run_pipeline()
        else:
            with open(analysis_path, "r", encoding="utf-8") as f:
                latest_analysis = json.load(f)
                
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            return jsonify({"error": "Missing API Key"}), 500
            
        client = OpenAI(api_key=OPENAI_API_KEY)
        context = json.dumps(latest_analysis, indent=2)
        
        # Inject exact fishing excel data if exists
        fishing_context = "Aucune donnée de pêche exacte disponible."
        if os.path.exists("data_an/processed/fishing.json"):
            with open("data_an/processed/fishing.json", "r", encoding="utf-8") as f:
                fishing_context = f.read()

        system_prompt = f"""
        Tu es "Gabesi", l'expert IA environnemental et stratégique du golfe de Gabès.
        Tu es amical, extrêmement compétent, et très investi pour aider l'utilisateur.
        
        Tu as accès à l'analyse multi-agents fraîche et aux bases de données :
        {context}
        
        Voici les DONNÉES BRUTES Excel Pêche :
        {fishing_context}
        
        RÈGLES ABSOLUES :
        1. Tu dois répondre SEULEMENT en FRANÇAIS, avec un ton expert et bienveillant.
        2. TU PEUX ET DOIS UTILISER LE MARKDOWN. Fais de beaux tableaux Markdown si on te demande les "détails des usines" (UAP, DCP, capacités, émissions).
        3. SI l'utilisateur demande explicitement "les détails" ou "les usines", tu as l'OBLIGATION de lister les données CHIFFRÉES (tonnage, mg/Nm3) exactes contenues dans l'analyse sans les vulgariser hors de vue.
        4. OBLIGATOIRE : Si la question concerne la pêche, OU la pollution, OU demande une courbe/prédiction, tu DOIS retourner "chart_data" avec les valeurs exactes récupérées ou déduites, et projeter jusqu'n 2030. Fournis un "chart_title" descriptif. 
        IMPORTANT : Tu DOIS lire les valeurs réelles dans les données brutes (exemple: additionne les valeurs de chaque excel pour trouver le total 2024 réel). Ne recopie surtout pas les valeurs `X, Y, Z` de mon exemple, remplace les par les VRAIES mathématiques issues du contexte. Exemple ciblé: [{{"name": "2024", "value": "valeur mathématique calculée"}}, {{"name": "2026", "value": "prediction"}}, {{"name": "2030", "value": "projection"}}]. C'EST INDISPENSABLE.
        5. Inclus exactement les sources en bas de réponse.
        
        Format JSON de retour stricte:
        {{
            "response": "Texte markdown expert, amical, avec des tableaux si pertinent...",
            "sources": ["Nom complet source 1", "Nom complet doc 2"],
            "chart_title": "Titre explicite de la Courbe (Pêche ou Émissions)",
            "chart_data": [{{"name": "2024", "value": "valeur mathématique calculée"}}, {{"name": "2026", "value": "prediction"}}, {{"name": "2030", "value": "projection"}}]
        }}
        """
        
        formatted_messages = [{"role": "system", "content": system_prompt}]
        
        # Hydrate memory history
        if messages_history:
            for msg in messages_history:
                formatted_messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        else:
            formatted_messages.append({"role": "user", "content": user_input})
        
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=formatted_messages,
            response_format={ "type": "json_object" }
        )
        
        response_json = json.loads(res.choices[0].message.content)
        
        return jsonify({
            "response": response_json.get("response", ""),
            "sources": response_json.get("sources", []),
            "chart_title": response_json.get("chart_title", "📉 Évolution des Données"),
            "chart_data": response_json.get("chart_data", []),
            "analysis_id": latest_analysis.get("analysis_id", "live")
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/upload', methods=['POST'])
def upload_data():
    """Upload new Raw Data and trigger the pipeline re-analysis."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    files = request.files.getlist('file')
    if not files or len(files) == 0:
        return jsonify({"error": "No selected file"}), 400
        
    industry_uploaded = False
    fishing_uploaded = False
    
    for file in files:
        if file.filename == '':
            continue
            
        filename = secure_filename(file.filename)
        if filename.endswith('.pdf'):
            path = os.path.join(UPLOAD_FOLDER_INDUSTRY, filename)
            file.save(path)
            industry_uploaded = True
            
        elif filename.endswith('.xlsx') or filename.endswith('.csv'):
            path = os.path.join(UPLOAD_FOLDER_FISHING, filename)
            file.save(path)
            fishing_uploaded = True

    try:
        if industry_uploaded:
            subprocess.run([sys.executable, "backend/scripts/ingest_industry.py"], check=True)
            
        if fishing_uploaded:
            subprocess.run([sys.executable, "backend/scripts/process_fishing.py"], check=True)
            
        if industry_uploaded or fishing_uploaded:
            run_pipeline()
            return jsonify({"message": f"{len(files)} fichier(s) intégré(s) et ré-analyse effectuée !"})
        else:
            return jsonify({"error": "Extensions non supportées. Uniquement PDF ou XLSX/CSV."}), 400
    except Exception as e:
        return jsonify({"error": f"Erreur lors de l\'intégration: {str(e)}"}), 500

@app.route('/api/analysis', methods=['GET'])
def get_analysis_results():
    """Returns the latest analysis results for the dashboard."""
    try:
        with open("data_an/processed/analysis_results.json", "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": "No analysis found, run pipeline first"}), 404

@app.route('/api/files', methods=['GET'])
def get_saved_files():
    """Returns the list of active local raw files."""
    try:
        industry_files = os.listdir(UPLOAD_FOLDER_INDUSTRY) if os.path.exists(UPLOAD_FOLDER_INDUSTRY) else []
        fishing_files = os.listdir(UPLOAD_FOLDER_FISHING) if os.path.exists(UPLOAD_FOLDER_FISHING) else []
        return jsonify({
            "industry": industry_files,
            "fishing": fishing_files
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/files/<file_type>/<filename>', methods=['DELETE'])
def delete_file(file_type, filename):
    """Deletes a file and purges its RAG/JSON data representation."""
    filename = secure_filename(filename)
    try:
        if file_type == 'industry':
            path = os.path.join(UPLOAD_FOLDER_INDUSTRY, filename)
            if os.path.exists(path):
                os.remove(path)
            # Wipe Qdrant Vectors
            QDRANT_URL = os.getenv("QDRANT_URL")
            QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
            if QDRANT_URL and QDRANT_API_KEY:
                qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
                try:
                    qdrant.delete(
                        collection_name="gabes_industry",
                        points_selector=qdrant_models.Filter(
                            must=[
                                qdrant_models.FieldCondition(
                                    key="source",
                                    match=qdrant_models.MatchValue(value=filename)
                                )
                            ]
                        )
                    )
                except Exception as ex:
                    print(f"Qdrant delete failed: {ex}")
            run_pipeline()
            return jsonify({"message": "Document pdf supprimé avec succès."})

        elif file_type == 'fishing':
            path = os.path.join(UPLOAD_FOLDER_FISHING, filename)
            if os.path.exists(path):
                os.remove(path)
            # Recompile JSON without this file
            subprocess.run([sys.executable, "backend/scripts/process_fishing.py"], check=True)
            run_pipeline()
            return jsonify({"message": "Fichier Excel/CSV de pêche supprimé avec succès."})
            
        else:
            return jsonify({"error": "Type invalide."}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=3000, debug=True)
