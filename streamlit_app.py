import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.express as px

# Configuration de la page Streamlit
st.set_page_config(page_title="Tableau de bord des laboratoires", layout="wide")

# Fonction pour charger les données
@st.cache_data
def load_data():
    data = pd.read_csv(r'C:\Users\hmkada\Documents\GRAPH EEL\IDF.csv', delimiter=';', encoding='latin1')
    numeric_columns = ['Latitude', 'Longitude', 'NOMBRE DE DOSSIERS EEL S-1', 
                       'NOMBRE MOYEN DE DOSSIERS EEL/J    SEMAINE-1', 
                       'NOMBRE DE DOSSIERS EEL EN 2024', 
                       'NOMBRE DE DOSSIERS EEL S-1', 
                       'NOMBRE DE DOSSIERS EEL S-2', 
                       'NOMBRE DE DOSSIERS EEL S-3', 'PMD']
    for col in numeric_columns:
        data[col] = pd.to_numeric(data[col], errors='coerce')
    return data.dropna(subset=['Latitude', 'Longitude'])

# Charger les données
data = load_data()

# Créer un menu pour naviguer entre les pages
page = st.sidebar.radio("Choisissez une page", ["Carte des laboratoires", "TOP labo EEL S-1", "Top 15 PMD"])

if page == "Carte des laboratoires":
    st.title('Carte des laboratoires')

    # Sidebar pour les filtres
    st.sidebar.header('Filtres')
    idf_options = ['IDFS', 'IDFE', 'IDFO']
    selected_idf = st.sidebar.multiselect('Choisissez IDF', idf_options, default=idf_options)
    
    # Nouveau filtre pour EEL et CLINICAL
    deployment_status = st.sidebar.multiselect('Statut de déploiement', ['EEL', 'CLINICAL', 'NON DEPLOYES'], default=['EEL', 'CLINICAL', 'NON DEPLOYES'])
    
    selected_lab = st.sidebar.selectbox('Choisissez un laboratoire', ['Tous'] + list(data['NOM'].unique()))

    # Filtrer les données selon les sélections
    filtered_data = data[data['IDF'].isin(selected_idf)]

    # Appliquer le nouveau filtre de déploiement
    if deployment_status:
        mask = pd.Series(False, index=filtered_data.index)
        if 'EEL' in deployment_status:
            mask |= filtered_data['EEL'].str.lower() == 'oui'
        if 'CLINICAL' in deployment_status:
            mask |= filtered_data['CLINICAL'].str.lower() == 'oui'
        if 'NON DEPLOYES' in deployment_status:
            mask |= (filtered_data['EEL'].str.lower() != 'oui') & (filtered_data['CLINICAL'].str.lower() != 'oui')
        filtered_data = filtered_data[mask]

    if selected_lab != 'Tous':
        filtered_data = filtered_data[filtered_data['NOM'] == selected_lab]

    # Créer la carte
    m = folium.Map(location=[filtered_data['Latitude'].mean(), filtered_data['Longitude'].mean()], zoom_start=10)

    # Fonction pour déterminer la couleur du marqueur
    def get_marker_color(row):
        if row['EEL'].lower() == 'oui' and row['CLINICAL'].lower() == 'oui':
            return 'green'
        elif row['EEL'].lower() == 'non' and row['CLINICAL'].lower() == 'oui':
            return 'purple'
        else:
            return 'red'

    # Fonction pour calculer le rayon du cercle
    def get_circle_radius(value):
        min_radius = 8
        max_radius = 25
        scale_factor = 1.2
        return min(max(min_radius, value * scale_factor), max_radius)

    # Ajouter des marqueurs pour tous les laboratoires filtrés
    for idx, row in filtered_data.iterrows():
        tooltip_content = f"""
        <strong>{row['NOM']}</strong><br>
        PMD: {row['PMD']}<br>
        CLINICAL: {row['CLINICAL']}<br>
        EEL: {row['EEL']}<br>
        NOMBRE MOYEN DE DOSSIERS EEL/J SEMAINE-1: {row['NOMBRE MOYEN DE DOSSIERS EEL/J    SEMAINE-1']:.2f}<br>
        NOMBRE DE DOSSIERS EEL S-1: {row['NOMBRE DE DOSSIERS EEL S-1']}
        """
        
        radius = get_circle_radius(row['NOMBRE DE DOSSIERS EEL S-1'])
        
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=radius,
            popup=row['NOM'],
            tooltip=folium.Tooltip(tooltip_content),
            color=get_marker_color(row),
            fill=True,
            fillColor=get_marker_color(row),
            fillOpacity=0.7
        ).add_to(m)

    # Créer une mise en page avec deux colonnes
    col1, col2 = st.columns([3, 1])

    with col1:
        # Afficher la carte dans Streamlit
        folium_static(m)

    with col2:
        # Ajouter la légende
        st.subheader("Légende")
        st.markdown("""
        <style>
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
        }
        </style>
        
        <div class="legend-item">
            <div class="legend-color" style="background-color: purple;"></div>
            <div>CLINICAL</div>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: green;"></div>
            <div>EEL</div>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: red;"></div>
            <div>NON DEPLOYES</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("La taille de la bulle est proportionnelle au nombre de dossiers EEL en semaine S-1.")

    # Afficher les statistiques générales
    st.subheader('Statistiques générales')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nombre total de laboratoires", len(filtered_data))
    with col2:
        st.metric("Laboratoires EEL", len(filtered_data[filtered_data['EEL'].str.lower() == 'oui']))
    with col3:
        st.metric("Laboratoires CLINICAL", len(filtered_data[filtered_data['CLINICAL'].str.lower() == 'oui']))

    # Afficher les informations détaillées si un laboratoire spécifique est sélectionné
    if selected_lab != 'Tous':
        st.subheader(f'Informations détaillées pour {selected_lab}')
        lab_data = filtered_data.iloc[0]
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"PMD: {lab_data['PMD']}")
            st.write(f"EEL: {lab_data['EEL']}")
            st.write(f"CLINICAL: {lab_data['CLINICAL']}")
        with col2:
            st.write(f"DATE ACTIVATION EEL: {lab_data['DATE ACTIVATION EEL']}")
            st.write(f"NOMBRE MOYEN DE DOSSIERS EEL/J SEMAINE-1: {lab_data['NOMBRE MOYEN DE DOSSIERS EEL/J    SEMAINE-1']:.2f}")
            st.write(f"NOMBRE DE DOSSIERS EEL EN 2024: {lab_data['NOMBRE DE DOSSIERS EEL EN 2024']}")
        st.write(f"NOMBRE DE DOSSIERS EEL S-1: {lab_data['NOMBRE DE DOSSIERS EEL S-1']}")

        # Graphique des dossiers EEL par semaine
        st.subheader('Nombre de dossiers EEL par semaine')
        weeks_data = lab_data[['NOMBRE DE DOSSIERS EEL S-1', 'NOMBRE DE DOSSIERS EEL S-2', 'NOMBRE DE DOSSIERS EEL S-3']]
        st.bar_chart(weeks_data)

    # Afficher un tableau de toutes les données filtrées
    st.subheader('Tableau des données')
    st.dataframe(filtered_data)

elif page == "TOP labo EEL S-1":
    st.title('TOP labo EEL S-1')
    
    # Trier les données par NOMBRE DE DOSSIERS EEL S-1 en ordre décroissant
    top_labs = data.sort_values('NOMBRE DE DOSSIERS EEL S-1', ascending=False).head(20)
    
    # Créer un graphique à barres horizontal avec Plotly
    fig = px.bar(top_labs, 
                 x='NOMBRE DE DOSSIERS EEL S-1', 
                 y='NOM', 
                 orientation='h',
                 title='Top 20 des laboratoires par nombre de dossiers EEL S-1',
                 labels={'NOMBRE DE DOSSIERS EEL S-1': 'Nombre de dossiers', 'NOM': 'Laboratoire'},
                 color='NOMBRE DE DOSSIERS EEL S-1',
                 color_continuous_scale='Viridis')
    
    # Personnaliser la mise en page
    fig.update_layout(yaxis={'categoryorder':'total ascending'},
                      height=600,
                      margin=dict(l=0, r=0, t=50, b=0))
    
    # Afficher le graphique
    st.plotly_chart(fig, use_container_width=True)
    
    # Afficher un tableau avec les données détaillées
    st.subheader("Données détaillées")
    st.dataframe(top_labs[['NOM', 'NOMBRE DE DOSSIERS EEL S-1', 'IDF']])

elif page == "Top 15 PMD":
    st.title('Top 15 des laboratoires par PMD')
    
    # Trier les données par PMD en ordre décroissant
    top_pmd = data.sort_values('PMD', ascending=False).head(15)
    
    # Créer un graphique à barres horizontal avec Plotly
    fig = px.bar(top_pmd, 
                 x='PMD', 
                 y='NOM', 
                 orientation='h',
                 title='Top 15 des laboratoires par PMD',
                 labels={'PMD': 'PMD', 'NOM': 'Laboratoire'},
                 color='PMD',
                 color_continuous_scale='Viridis')
    
    # Personnaliser la mise en page
    fig.update_layout(yaxis={'categoryorder':'total ascending'},
                      height=600,
                      margin=dict(l=0, r=0, t=50, b=0))
    
    # Afficher le graphique
    st.plotly_chart(fig, use_container_width=True)
    
    # Afficher un tableau avec les données détaillées
    st.subheader("Données détaillées")
    st.dataframe(top_pmd[['NOM', 'PMD', 'IDF']])