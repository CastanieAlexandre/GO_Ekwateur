import streamlit as st
import pandas as pd
import plotly.express as px
import warnings

# Titres et configuration de la page

st.set_page_config(layout="wide",
                   page_title="GO Ekwateur",
                   page_icon=":bar_chart:")

HIDE_FORMAT = """
       <style>
       footer {visibility: hidden;}
       </style>
       """
st.markdown(HIDE_FORMAT, unsafe_allow_html=True)
st.markdown(
        f"""
            <style>
                .main{{
                    background-image: url(https://cdn.hellowatt.fr/media/logos/nouveau-logo-ekwateur_1.webp);
                    background-repeat: no-repeat;
                    padding-top: 10px;
                    background-position: 50% 7%;
                }}
            </style>
            """,
        unsafe_allow_html=True
    )

st.markdown(
    "<h1 style='text-align: center;'>Garanties d'Origines Ekwateur</h1>",
    unsafe_allow_html=True
    )

#st.caption("Cette page permet d'agréger les résultats de l'outil de prévision C4 développé par Irex en pernant en compte les dates du parc")
#st.write("---")
st.cache_data()
def recup_et_mise_en_forme(chemin_csv,chemin_pp):
    """Récupération et mise en forme des données issues du registre"""
    #récupération des données de l'exctract du registre
    df_data=pd.read_csv(chemin_csv,
                        sep=";",
                        parse_dates=True)
    df_data["Installation "].loc[df_data["Installation "].isnull()]="Inconnu"
    df_data["Date de fin "]=pd.to_datetime(df_data["Date de fin "],dayfirst=True)#.dt.strftime('%d-%m-%Y')
    df_data["Date de début "]=pd.to_datetime(df_data["Date de début "],dayfirst=True)
    df_data["Année"]=df_data["Date de début "].dt.year

    #récupération de la liste des petits producteurs
    df_liste_pp=pd.read_csv(chemin_pp,
                            sep=";",
                            dtype=str,
                            encoding="latin_1")
    
    #rajout et complétion d'une colonne type d'offre
    df_data["Type d'offre"]=pd.Series()
    for an in df_data["Année"].drop_duplicates().values:
        for _,nom_pp in df_liste_pp[str(an)].dropna().items():
            df_data["Type d'offre"].loc[(df_data["Installation "].str.contains(nom_pp)==True)&
                                        (df_data["Date de début "].dt.year==an)]=f"PP_{an}"
        df_data["Type d'offre"].loc[df_data["Type d'offre"].isnull()]="Classique"

    return df_data

warnings.filterwarnings("ignore")
df_data_go=recup_et_mise_en_forme(r".\go-list.csv",
                                  r".\liste_pp_tot.csv")

#Création des paramètres
liste_offres=["Classique","PP"]
liste_annees=df_data_go["Année"].drop_duplicates().sort_values().values
liste_statut=df_data_go["Statut "].drop_duplicates().values

tuple_col=(1,)
for i in range(len(liste_offres)):
    tuple_col+=(1,)
tuple_col=tuple_col+(2,)
for i in range(len(liste_statut)):
    tuple_col+=(1,)
tuple_col=tuple_col+(2,)

conteneur_parametres = st.columns(tuple_col)
for i,offre in enumerate(liste_offres):
    conteneur_parametres[i+1].checkbox(offre,value=True,key=offre)

annees = conteneur_parametres[i+2].slider(label='Années',
                   min_value=min(liste_annees),
                   max_value=max(liste_annees),
                   value=(min(liste_annees)+1,max(liste_annees)-1),
                   key="annees",
                   label_visibility="collapsed")

for k,statut in enumerate(liste_statut):
    conteneur_parametres[i+3+k+1].checkbox(statut,value=True,key=statut)

def liste_selections(l_offr,l_stat):

    l_offres_selectionnees,l_statuts_selectionnes=[],[]

    for offer in l_offr:
        if st.session_state[offer]:
            l_offres_selectionnees.append(offer)
    for stat in l_stat:
        if st.session_state[stat]:
            l_statuts_selectionnes.append(stat)

    return l_offres_selectionnees,l_statuts_selectionnes

@st.cache_data(show_spinner=True)
def selection_donnees(df,years:tuple,list_checked_offers:list,list_checked_status:list):
    df_data=df.copy()
    #tronquage sur les années sélectionnées
    df_data=df_data.loc[(df_data["Date de début "].dt.year>=years[0])&
                        (df_data["Date de fin "].dt.year<=years[1])]
    
    list_checked_offers_tot=[]
    if "PP" in list_checked_offers:
        for annee in list(range(years[0],years[1]+1)):
            list_checked_offers_tot.append(f"PP_{annee}")

    if "Classique" in list_checked_offers:
        list_checked_offers_tot.append("Classique")

    #tronquage sur les check box types d'offre
    for annee in list(range(years[0],years[1]+1)):
        df_data=df_data.loc[df_data["Type d'offre"].isin(list_checked_offers_tot)]

    #tronquage sur les check box statut
    df_data=df_data.loc[df_data["Statut "].isin(list_checked_status)]

    #Comptage centrales
    df_data["Nombre de centrales"]=1

    return df_data

liste_offres_selectionnees,liste_statuts_selectionnes=liste_selections(liste_offres,liste_statut)

#Récupération du dataframe des données réduites aux sélections
df_data_go_checked=selection_donnees(df_data_go,annees,
                                     liste_offres_selectionnees,
                                     liste_statuts_selectionnes)

#tracé de deux graphiques sur la même ligne
col_ligne_1_1,col_ligne_1_2=st.columns((4,2))
with col_ligne_1_1:
    fig=px.bar(df_data_go_checked,x="Année",y="Quantité certifiée (MWh) ",
                color="Type d'installation ",
                title="Volume valorisé par année et par type",
                color_discrete_sequence=px.colors.qualitative.Light24
                )
    col_ligne_1_1.plotly_chart(fig,use_container_width=True)

with col_ligne_1_2:
    sum_df=df_data_go_checked.groupby('Année', as_index=False).agg({'Quantité certifiée (MWh) ': 'sum'})
    sum_df=sum_df.rename(columns={'Quantité certifiée (MWh) ':"Volume certifié total (MWh)"})
    count_df=df_data_go_checked.groupby('Année', as_index=False).agg({"Nombre de centrales": 'sum'})
    df_chiffres=pd.merge(sum_df,count_df,on="Année")
    sum_df_power=df_data_go_checked.groupby('Année', as_index=False).agg({'Puissance (MW) ': 'sum'})
    df_chiffres=pd.merge(df_chiffres,sum_df_power,on="Année")
    
    st.dataframe(df_chiffres,use_container_width=True,hide_index=True)

#tracé de deux autres graphiques sur la même ligne
col_ligne_2_1,col_ligne_2_2=st.columns(2)
with col_ligne_2_1:
    # Création du graphique à barres avec px.bar
    fig=px.bar(df_data_go_checked,x="Année",y='Nombre de centrales',
            color="Type d'installation ",
            title="Nombre de centrales par année et par type",
            color_discrete_sequence=px.colors.qualitative.Light24
            )
    st.plotly_chart(fig,use_container_width=True)
with col_ligne_2_2:
    fig=px.bar(df_data_go_checked,x="Année",y="Puissance (MW) ",
               color="Type d'installation ",
               title="Puissance installée des centrales par année et par type",
               color_discrete_sequence=px.colors.qualitative.Light24
               )
    st.plotly_chart(fig,use_container_width=True)

#tracé des deux derniers graphiques sur la même ligne
col_ligne_3_1,col_ligne_3_2=st.columns(2)
with col_ligne_3_1:
    
    fig=px.bar(df_data_go_checked,y="Pays ",x="Quantité certifiée (MWh) ",
               color="Type d'installation ",
               title="Volume valorisé par pays et par type",
               orientation='h',
               color_discrete_sequence=px.colors.qualitative.Light24
               )
    st.plotly_chart(fig,use_container_width=True)
    
with col_ligne_3_2:
    
    # Création du graphique à barres avec px.bar
    fig=px.bar(df_data_go_checked,y="Pays ",x='Nombre de centrales',
               color="Type d'installation ",
               title="Nombre de centrales par pays et par type",
               orientation='h',
               color_discrete_sequence=px.colors.qualitative.Light24
               )
    st.plotly_chart(fig,use_container_width=True)
st.markdown("**Données sélectionnées :**")
st.dataframe(df_data_go_checked[['Installation ','Puissance (MW) ','Adresse ', 'Code postal ', 'Pays ',
                             'Région Française', 'Aide(s) nationale(s) ', "Type d'installation ",
                             'Quantité certifiée (MWh) ','Statut ','Année',
                             "Type d'offre"]],
                             hide_index=True)
st.write("---")
st.caption("Développé par Alexandre Castanié")