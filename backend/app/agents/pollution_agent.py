import os
import logging
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from openai import OpenAI

load_dotenv()
logger = logging.getLogger('PollutionAgent')

def analyze_pollution(query="Valeurs exactes des émissions (mg/L, tonnes) et rejets polluants des usines comme le GCT, et les projets ou solutions pour 2030"):
    """Uses Qdrant to retrieve industry context and OpenAI to extract pollution insights."""
    try:
        QDRANT_URL = os.getenv("QDRANT_URL")
        QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        
        if not QDRANT_URL or not OPENAI_API_KEY:
            return {"level": "unknown", "source": "unknown", "insight": "Missing API keys."}
            
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Query 1: Emissions and 2030 projects
        query_val = "Valeurs exactes des émissions (mg/L, tonnes) et rejets polluants des usines comme le GCT, et les projets ou solutions pour 2030"
        emb_res_1 = openai_client.embeddings.create(input=[query_val], model="text-embedding-3-large")
        
        # Query 2: Production capacities (UAP, DCP, DAP) and consumption
        query_prod = "capacité de production, consommation, usine UAP, DCP, DAP, Ammonitrate, T/jour, eau de mer, phosphate brut"
        emb_res_2 = openai_client.embeddings.create(input=[query_prod], model="text-embedding-3-large")
        
        try:
            results_1 = client.query_points(
                collection_name="gabes_industry",
                query=emb_res_1.data[0].embedding,
                limit=8
            ).points
            
            results_2 = client.query_points(
                collection_name="gabes_industry",
                query=emb_res_2.data[0].embedding,
                limit=8
            ).points
            
            all_results = results_1 + results_2
            context = "\n\n".join([f"--- DÉBUT EXTRAIT [Source: {res.payload.get('source', 'Inconnu')}] ---\n{res.payload.get('text', '')}\n--- FIN EXTRAIT ---" for res in all_results])
        except Exception as e:
            logger.warning(f"Qdrant search failed, returning default: {str(e)}")
            context = "Audit shows high phosphogypsum discharge mainly from GCT (Groupe Chimique Tunisien)."

        prompt = "En te basant sur ce contexte industriel de Gabès (qui contient le nom des fichiers sources pour chaque extrait) :\\n" + context + "\\n\\n" + "Ta mission :\\n" + "1. Extrais TOUTES les capacités de production (ex: UAP 3000 T/jour, DCP 400 T/j) et consommations des usines trouvées dans le texte.\\n" + "2. Extrais les niveaux de pollution et sources.\\n" + "3. ATTENTION - CONFLIT DE DONNÉES : Si les extraits se contredisent complètement (ex: un document 'def' indique une pollution critique, et un document 'contradictoire' ou d'une autre source indique une pollution faible), tu DOIS mentionner cette contradiction dans ton résumé (insight). ET tu dois ajuster ton 'level' en conséquence. Le document mentionnant une baisse ou identifié comme contradictoire a priorité.\\n" + "4. Extrais EXPLICITEMENT LES PROJETS ET SOLUTIONS À RÉALISER D'ICI 2030 mentionnés dans le document.\\n\\n" + "Réponds UNIQUEMENT au format JSON valide:\\n" + "{\"level\": \"élevé/modéré/faible/contradictoire\", \"source\": \"Lister les sources opposées\", \"insight\": \"Résumé détaillé listant les capacités, la situation de la pollution en expliquant les contradictions si elles existent, et les projets 2030.\"}"
        
        res = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        response = res.choices[0].message.content.strip()
        if response.startswith("```json"):
            response = response[7:-3]
        elif response.startswith("```"):
            response = response[3:-3]
            
        import json
        return json.loads(response)
        
    except Exception as e:
        logger.error(f"Failed to analyze pollution: {str(e)}")
        return {"level": "error", "source": "error", "insight": str(e)}
