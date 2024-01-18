import streamlit as st
import pandas as pd
import plotly.express as px
import warnings

# Titres et configuration de la page
import hmac
import streamlit as st


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.

st.set_page_config(layout="wide",
                   page_title="Garanties d'origine",
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
    "<h1 style='text-align: center;'>Garanties d'Origine</h1>",
    unsafe_allow_html=True
    )
st.sidebar.write("Données à upload :")
chemin_go_list = st.sidebar.file_uploader(
            "go_list.csv qui contient les données extraites du registre",
            type=["csv"])
chemin_pp_list = st.sidebar.file_uploader(
            "pp-list.csv qui contient le nom des centrales PP par année",
            type=["csv"])
st.sidebar.write(":bulb: Appuyer sur la croix en haut à droite de la colonne pour la réduire")

@st.cache_data()
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
    
    #rajout colonne type de centrale
    df_data["Type de centrale"]=pd.Series()
    df_data["Type de centrale"].loc[df_data["Type d'installation "].str.contains("Solaire")==True]="Solaire"
    df_data["Type de centrale"].loc[df_data["Type d'installation "].str.contains("hydro")==True]="Hydroélectrique"
    df_data["Type de centrale"].loc[df_data["Type d'installation "].str.contains("Vent")==True]="Éolien"
    df_data["Type de centrale"].loc[df_data["Type d'installation "].str.contains("Marine")==True]="Marémotrice"
    df_data["Type de centrale"].loc[df_data["Type d'installation "].str.contains("Thermique")==True]="Thermique"
    df_data["Type de centrale"].loc[df_data["Type de centrale"].isnull()]="Inconnu/Autre"

    return df_data

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

warnings.filterwarnings("ignore")
if chemin_go_list is not None and chemin_pp_list is not None :

    if "go-list" not in chemin_go_list.name or "pp-list" not in chemin_pp_list.name:
        st.write(""":no_entry: Êtes vous sûr d'avoir correctement choisi les fichiers ? Assurez vous que les
                 noms des fichiers contiennent bien les caratères "go-list" et "pp-list" """)
    
    df_data_go=recup_et_mise_en_forme(chemin_go_list,
                                    chemin_pp_list)

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

    liste_offres_selectionnees,liste_statuts_selectionnes=liste_selections(liste_offres,liste_statut)

    #Récupération du dataframe des données réduites aux sélections
    df_data_go_checked=selection_donnees(df_data_go,annees,
                                        liste_offres_selectionnees,
                                        liste_statuts_selectionnes)

    #tracé de deux graphiques sur la même ligne
    tab_an_1, tab_an_2 = st.tabs(["Volume par année", "Nombre par année"])
    with tab_an_1:
        fig=px.bar(df_data_go_checked,x="Année",y="Quantité certifiée (MWh) ",
                    color="Type de centrale",
                    title="Volume valorisé par année de production et par type de centrale",
                    color_discrete_sequence=px.colors.qualitative.Set1
                    )
        st.plotly_chart(fig,use_container_width=True)

    with tab_an_2:
        fig=px.bar(df_data_go_checked,x="Année",y='Nombre de centrales',
                color="Type de centrale",
                title="Nombre de centrales par année de production et par type",
                color_discrete_sequence=px.colors.qualitative.Set1
                )
        st.plotly_chart(fig,use_container_width=True)
        
    #tracé de deux autres graphiques sur la même ligne
    col_ligne_2_1,col_ligne_2_2=st.columns(2)
    with col_ligne_2_2:
        sum_df=df_data_go_checked.groupby('Année', as_index=False).agg({'Quantité certifiée (MWh) ': 'sum'})
        sum_df=sum_df.rename(columns={'Quantité certifiée (MWh) ':"Volume certifié total (MWh)"})
        count_df=df_data_go_checked.groupby('Année', as_index=False).agg({"Nombre de centrales": 'sum'})
        df_chiffres=pd.merge(sum_df,count_df,on="Année")
        sum_df_power=df_data_go_checked.groupby('Année', as_index=False).agg({'Puissance (MW) ': 'sum'})
        df_chiffres=pd.merge(df_chiffres,sum_df_power,on="Année")

        sum_df_par_type=df_data_go_checked.groupby('Type de centrale', as_index=False).agg({'Quantité certifiée (MWh) ': 'sum'})
        sum_df_par_type=sum_df_par_type.rename(columns={'Quantité certifiée (MWh) ':"Volume (MWh)"})
        sum_df_par_type["Pourcentage (%)"]=(sum_df_par_type["Volume (MWh)"]*100/sum_df_par_type["Volume (MWh)"].sum()).round(1)
        
        st.markdown("**Tableau du volume valorisé, du nombre et de la puissance installée des centrales par année**")
        st.dataframe(df_chiffres,use_container_width=True,hide_index=True)

        st.markdown("**Tableau du volume valorisé par type de centrale**")
        st.dataframe(sum_df_par_type,use_container_width=True,hide_index=True)
        
    with col_ligne_2_1:
        fig=px.bar(df_data_go_checked,x="Année",y="Puissance (MW) ",
                color="Type de centrale",
                title="Puissance installée des centrales par année de production et par type",
                color_discrete_sequence=px.colors.qualitative.Set1
                )
        st.plotly_chart(fig,use_container_width=True)

    #tracé des deux derniers graphiques sur la même ligne
    tab_pays_1, tab_pays_2 = st.tabs(["Volume par pays", "Nombre par pays"])
    with tab_pays_1:
        
        fig=px.bar(df_data_go_checked,y="Pays ",x="Quantité certifiée (MWh) ",
                color="Type de centrale",
                title="Volume valorisé par pays et par type de centrale",
                orientation='h',
                color_discrete_sequence=px.colors.qualitative.Set1
                )
        st.plotly_chart(fig,use_container_width=True)
        
    with tab_pays_2:
        
        # Création du graphique à barres avec px.bar
        fig=px.bar(df_data_go_checked,y="Pays ",x='Nombre de centrales',
                color="Type de centrale",
                title="Nombre de centrales par pays et par type de centrale",
                orientation='h',
                color_discrete_sequence=px.colors.qualitative.Set1
                )
        st.plotly_chart(fig,use_container_width=True)

    st.markdown("**Données sélectionnées :**")
    st.dataframe(df_data_go_checked[['Installation ','Puissance (MW) ','Adresse ', 'Code postal ', 'Pays ',
                                'Région Française', 'Aide(s) nationale(s) ', "Type d'installation ",
                                'Quantité certifiée (MWh) ','Statut ','Année',
                                "Type d'offre", "Type de centrale"]],
                                hide_index=True)
else :
    st.write(":warning: Veuillez upload les données")

st.write("---")
st.caption("Développé par Alexandre Castanié - 2023")
