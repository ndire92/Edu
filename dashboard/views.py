import requests
import pandas as pd
import plotly.express as px
from django.shortcuts import render
from django.core.paginator import Paginator

API_TOKEN = "f585e3b36fa1739f8b0a27ba559f0992d2bf1d6f"

# --- CONFIGURATION DE TES FORMULAIRES ---
FORMS_CONFIG = [
    {'uid': 'aJtfPktL7aZKg2t7qZdp7v', 'title': 'Formulaire Principal'},
]

def home(request):
    all_tables_data = []
    
    # Récupération des filtres (GET parameters)
    search_query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    
    filter_month = request.GET.get('filter_month', '')
    filter_teacher = request.GET.get('filter_teacher', '')
    filter_type = request.GET.get('filter_type', '')

    # Colonnes techniques à supprimer
    colonnes_a_supprimer = [
        '_id', '_uuid', '_validation_status',
        'meta/instanceID', 'meta/rootUuid', '_xform_id_string',
        '_bamboo_dataset_id', '_tags', '__version__', '_status',
        '_submitted_by', '_geolocation', 'formhub/uuid'
    ]

    # --- BOUCLE SUR CHAQUE FORMULAIRE ---
    for form in FORMS_CONFIG:
        form_uid = form['uid']
        form_title = form['title']

        # 1. Récupération
        url = f"https://kf.kobotoolbox.org/api/v2/assets/{form_uid}/data/"
        headers = {"Authorization": f"Token {API_TOKEN}"}
        all_records = []
        
        while url and len(all_records) < 1000:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                all_records.extend(data['results'])
                url = data.get('next')
            else:
                break

        df = pd.DataFrame(all_records)
        
        # Contexte initial
        table_context = {
            'title': form_title,
            'headers': [],
            'page_obj': None,
            'chart_bar': None,
            'chart_line': None,
            'chart_pie': None,
            'total': len(all_records),
            # Listes pour les filtres (Dropdowns)
            'available_months': [],
            'available_teachers': []
        }

        if not df.empty:
            # --- 2. NETTOYAGE & IMAGES ---
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

            df.drop(columns=colonnes_a_supprimer, inplace=True, errors='ignore')

            # --- 3. DÉTECTION DES COLONNES ---
            cols_pertinentes = [col for col in df.columns if not (df[col].astype(str).str.startswith('http', na=False).any())]
            
            # A. Date
            col_date = None
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower() or 'jour' in col.lower() or 'start' in col.lower():
                    col_date = col
                    break
            if not col_date and 'start' in df.columns: col_date = 'start'
            if not col_date and '_submission_time' in df.columns: col_date = '_submission_time'

            if col_date:
                df[col_date] = pd.to_datetime(df[col_date], errors='coerce')
                df.sort_values(col_date, inplace=True)
                # Création d'une colonne formatée "YYYY-MM" pour le filtre
                df['MonthStr'] = df[col_date].dt.strftime('%Y-%m')
                table_context['available_months'] = sorted(df['MonthStr'].unique())

            # B. Nom (Barres)
            col_nom = None
            for col in cols_pertinentes:
                if 'nom' in col.lower() or 'eleve' in col.lower() or 'student' in col.lower() or 'name' in col.lower():
                    col_nom = col
                    break
            if not col_nom: col_nom = cols_pertinentes[0] if cols_pertinentes else None

            # C. OBSERVATIONS
            col_obs = None
            for col in df.columns:
                if col.lower() in ['observation', 'observations', 'statut', 'statuts']:
                    col_obs = col
                    break
            if not col_obs:
                for col in df.columns:
                    if 'obs' in col.lower() or 'statut' in col.lower() or 'presence' in col.lower():
                        col_obs = col
                        break
            
            # D. ENSEIGNANT (NOUVEAU)
            col_teacher = None
            for col in cols_pertinentes:
                if 'ens' in col.lower() or 'prof' in col.lower() or 'teacher' in col.lower() or 'classe' in col.lower() or 'maître' in col.lower():
                    col_teacher = col
                    break
            
            # Remplir la liste des enseignants pour le dropdown
            if col_teacher:
                table_context['available_teachers'] = sorted(df[col_teacher].dropna().unique())

            # --- 4. APPLICATION DES FILTRES (CORE LOGIC) ---
            
            # Filtre par Mois
            if filter_month and col_date:
                df = df[df['MonthStr'] == filter_month]
            
            # Filtre par Enseignant
            if filter_teacher and col_teacher:
                df = df[df[col_teacher] == filter_teacher]

            # Filtre par Type d'observation (Sur la lettre A, R, P brute)
            if filter_type and col_obs:
                # On normalise les deux côtés en majuscule pour la comparaison
                df = df[df[col_obs].astype(str).str.upper() == filter_type.upper()]

            # --- 5. GRAPHIQUE 1 : BARRES ---
            if col_nom:
                count_abs = df[col_nom].value_counts().reset_index()
                count_abs.columns = [col_nom, 'Nb_Absences']
                count_abs['Nb_Absences'] = pd.to_numeric(count_abs['Nb_Absences'])
                
                fig_bar = px.bar(
                    count_abs, x='Nb_Absences', y=col_nom, orientation='h',
                    title=f"Top Absences par {col_nom}",
                    text='Nb_Absences', color='Nb_Absences',
                    color_continuous_scale='Viridis'
                )
                fig_bar.update_yaxes(autorange="reversed")
                fig_bar.update_traces(textposition='outside')
                table_context['chart_bar'] = fig_bar.to_html(full_html=False, include_plotlyjs=False)

            # --- 6. GRAPHIQUE 2 : COURBE ---
            if col_date:
                df_line = df.dropna(subset=[col_date]).copy()
                if not df_line.empty:
                    df_evolution = df_line.groupby(col_date).size().reset_index(name='Total')
                    fig_line = px.line(df_evolution, x=col_date, y='Total', title="Évolution des absences", markers=True)
                    table_context['chart_line'] = fig_line.to_html(full_html=False, include_plotlyjs=False)

            # --- 7. GRAPHIQUE 3 : CAMEMBERT (Logique A, R, P) ---
            if col_obs:
                df_pie = df.copy()

                def normalize_status(x):
                    val = str(x).lower()
                    if val == 'p' or 'present' in val: return 'Présent'
                    if val == 'a' or 'abs' in val: return 'Absent'
                    if val == 'r' or 'retard' in val or 'late' in val: return 'Retard'
                    return None

                df_pie['Categorie'] = df_pie[col_obs].apply(normalize_status)
                df_pie = df_pie[df_pie['Categorie'].notna()]

                if not df_pie.empty:
                    count_obs = df_pie['Categorie'].value_counts().reset_index()
                    count_obs.columns = ['Type', 'Nombre']
                    count_obs['Type'] = pd.Categorical(count_obs['Type'], ['Présent', 'Absent', 'Retard'])
                    count_obs.sort_values('Type', inplace=True)

                    color_map = {'Présent': '#2ecc71', 'Absent': '#e74c3c', 'Retard': '#f1c40f'}
                    fig_pie = px.pie(
                        count_obs, values='Nombre', names='Type',
                        title=f"Répartition : {col_obs}", hole=0.3,
                        color='Type', color_discrete_map=color_map
                    )
                    table_context['chart_pie'] = fig_pie.to_html(full_html=False, include_plotlyjs=False)

            # --- 8. RECHERCHE & PAGINATION ---
            df = df.astype(str) 
            if search_query:
                mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
                df = df[mask]

            if not df.empty:
                records = df.to_dict('records')
                paginator = Paginator(records, 20)
                table_context['page_obj'] = paginator.get_page(page_number)
                table_context['headers'] = df.columns.tolist()
                table_context['total'] = paginator.count

        all_tables_data.append(table_context)

    context = {
        'all_tables': all_tables_data,
        'query': search_query,
        # Conserver les filtres pour les remettre dans les inputs
        'current_month': filter_month,
        'current_teacher': filter_teacher,
        'current_type': filter_type
    }
    
    return render(request, 'dashboard/home.html', context)