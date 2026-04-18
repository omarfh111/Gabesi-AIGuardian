import pandas as pd
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('FishingProcessor')

INPUT_DIR = "data_an/raw/fishing"
OUTPUT_FILE = "data_an/processed/fishing.json"

def process_fishing_data():
    if not os.path.exists(INPUT_DIR):
        logger.error(f"Directory not found: {INPUT_DIR}")
        return

    all_records = []

    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith(".xlsx"):
            continue
            
        input_file = os.path.join(INPUT_DIR, filename)
        try:
            logger.info(f"Loading data from {input_file}")
            df = pd.read_excel(input_file)
        
        # Clean: remove empty columns or obvious nulls
        df.dropna(how='all', axis=1, inplace=True)
        df.dropna(how='all', axis=0, inplace=True)
        
        # We assume columns: 'Annee', 'Delegation', 'Peche_cotiere', ...
        # Melt the dataframe to get format: year, fish_type, production_tons, zone
        
        id_vars = ['Annee']
        if 'Delegation' in df.columns:
            id_vars.append('Delegation')
            
        value_vars = [col for col in df.columns if col not in id_vars and col != 'Total']
        
        melted_df = df.melt(id_vars=id_vars, value_vars=value_vars, var_name='fish_type', value_name='production_tons')
        
        # Drop rows where production is null
        melted_df.dropna(subset=['production_tons'], inplace=True)
        
        # Ensure production is numeric, fill non-numeric with 0
        melted_df['production_tons'] = pd.to_numeric(melted_df['production_tons'], errors='coerce').fillna(0)
        
        records = []
            for _, row in melted_df.iterrows():
                if row['production_tons'] > 0:
                    zone = row.get('Delegation', 'gabes')
                    if pd.isna(zone) or str(zone).lower() == 'nan':
                        zone = 'gabes'
                        
                    all_records.append({
                        "year": int(row['Annee']),
                        "fish_type": row['fish_type'],
                        "production_tons": float(row['production_tons']),
                        "zone": str(zone).lower(),
                        "source_file": filename
                    })
                    
        except Exception as e:
            logger.error(f"Error processing fishing data from {filename}: {str(e)}")

    if all_records:
        # Sort by year
        all_records = sorted(all_records, key=lambda x: x['year'])
                
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_records, f, indent=2)
            
        logger.info(f"Successfully processed {len(all_records)} records total and saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_fishing_data()
