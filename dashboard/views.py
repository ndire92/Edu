import requests
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from django.shortcuts import render
from django.core.paginator import Paginator  # <--- IMPORT IMPORTANT

API_TOKEN = "f585e3b36fa1739f8b0a27ba559f0992d2bf1d6f"

# --- CONFIGURATION DE TES FORMULAIRES ---
FORMS_CONFIG = [
    {'uid': 'aJtfPktL7aZKg2t7qZdp7v', 'title': 'Formulaire Principal'},
    # {'uid': 'ID_DU_DEUXIEME_FORMULAIRE', 'title': 'Deuxième Formulaire'},
]

def home(request):
    all_tables_data = []
    
    # On récupère la recherche et le numéro de page
    search_query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1) # <--- RÉCUPÉRATION PAGE

    # Liste des colonnes techniques à supprimer
    colonnes_a_supprimer = [
        '_id', '_uuid', '_submission_time', '_validation_status',
        'meta/instanceID', 'meta/rootUuid', '_xform_id_string',
        '_bamboo_dataset_id', '_tags', '_notes'
    ]

    # --- BOUCLE SUR CHAQUE FORMULAIRE ---
    for form in FORMS_CONFIG:
        form_uid = form['uid']
        form_title = form['title']

        # 1. Récupération des données
        url = f"https://kf.kobotoolbox.org/api/v2/assets/{form_uid}/data/"
        headers = {"Authorization": f"Token {API_TOKEN}"}
        all_records = []
        
        # Limitation à 1000 records
        while url and len(all_records) < 1000:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                all_records.extend(data['results'])
                url = data.get('next')
            else:
                break

        df = pd.DataFrame(all_records)
        
        # Préparation du contexte pour ce tableau
        table_context = {
            'title': form_title,
            'headers': [],
            'page_obj': None, # <--- On utilisera page_obj au lieu de rows
            'graph': None,
            'graph_title': 'Aucune donnée',
            'total': len(all_records)
        }

        if not df.empty:
            # --- 2. GESTION INTELLIGENTE DES IMAGES ---
            if '_attachments' in df.columns:
                for index, row in df.iterrows():
                    attachments = row['_attachments']
                    if isinstance(attachments, list):
                        for att in attachments:
                            question_name = att.get('question_xpath')
                            url_img = att.get('download_medium_url')

                            if url_img:
                                url_img += f"?token={API_TOKEN}"
                            
                            if question_name and url_img and question_name in df.columns:
                                df.at[index, question_name] = url_img
                
                df.drop(columns=['_attachments'], inplace=True)

            # --- 3. NETTOYAGE DES COLONNES TECHNIQUES ---
            df.drop(columns=colonnes_a_supprimer, inplace=True, errors='ignore')

            # --- 4. RECHERCHE & FILTRE ---
            df = df.astype(str) 
            
            if search_query:
                mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
                df = df[mask]

            # --- 5. GRAPHIQUE (Basé sur les données filtrées) ---
            if not df.empty:
                colonnes_pertinentes = [col for col in df.columns if not (df[col].str.startswith('http', na=False).any())]
                
                if colonnes_pertinentes:
                    ma_colonne = colonnes_pertinentes[0]
                    table_context['graph_title'] = f"Répartition : {ma_colonne}"
                    
                    compte = df[ma_colonne].value_counts()
                    
                    plt.figure(figsize=(8, 3))
                    compte.plot(kind='bar', color='teal')
                    plt.title(table_context['graph_title'], fontsize=10)
                    plt.tight_layout()

                    buf = io.BytesIO()
                    plt.savefig(buf, format='png')
                    buf.seek(0)
                    table_context['graph'] = base64.b64encode(buf.read()).decode('utf-8')
                    plt.close()

                # --- 6. PAGINATION (NOUVEAU) ---
                records = df.to_dict('records')
                paginator = Paginator(records, 2) # 15 lignes par page
                
                # On applique le numéro de page demandé
                table_context['page_obj'] = paginator.get_page(page_number)
                
                table_context['headers'] = df.columns.tolist()
                # On met à jour le total après filtrage pour affichage
                table_context['total'] = paginator.count

        all_tables_data.append(table_context)

    # Envoi au template
    context = {
        'all_tables': all_tables_data,
        'query': search_query
    }
    
    return render(request, 'dashboard/home.html', context)

