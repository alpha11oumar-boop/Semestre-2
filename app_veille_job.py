import streamlit as st
import pandas as pd
import pdfplumber
import sqlite3
import re
import plotly.express as px
from plyer import notification

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="DBR Job Intelligence Pro", layout="wide")

if 'data_jobs' not in st.session_state:
    st.session_state.data_jobs = None

# --- 2. BASE DE DONNEES ET ALERTE ---
def init_db():
    with sqlite3.connect('dbr_historique.sqlite') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS historique (lien TEXT PRIMARY KEY)''')

def check_and_save_new_job(lien_offre):
    with sqlite3.connect('dbr_historique.sqlite') as conn:
        c = conn.cursor()
        existe = c.execute("SELECT 1 FROM historique WHERE lien = ?", (lien_offre,)).fetchone()
        if not existe:
            c.execute("INSERT INTO historique (lien) VALUES (?)", (lien_offre,))
            return True
        return False

def envoyer_alerte_bureau(entreprise, poste, score):
    try:
        notification.notify(
            title=f"Nouvelle Offre : {entreprise}",
            message=f"Match : {score}% pour {poste}",
            app_name="DBR Job Scraper",
            timeout=5
        )
    except: pass

# --- 3. SCANNER DE CV ---
def extraire_texte_cv(file):
    if not file: return ""
    try:
        file.seek(0)
        with pdfplumber.open(file) as pdf:
            text = " ".join([page.extract_text() or "" for page in pdf.pages])
        return re.sub(r'\s+', ' ', text).strip()
    except Exception:
        return ""

def extraire_profil(texte):
    # Liste des outils incluant r
    outils = ["python", "sql", "pandas", "numpy", "powerbi", "tableau", "excel", "alteryx", "gcp", "dataiku", "aws", "azure", "git", "c#", "java", "r"]
    competences = ["machine learning", "scikit-learn", "statistiques", "analyse de données", "nlp", "modèles prédictifs", "datamarts", "reporting", "gestion de projet", "agile"]
    
    texte_lower = texte.lower()
    outils_trouves = [o for o in outils if re.search(r'\b' + re.escape(o) + r'\b', texte_lower)]
    comps_trouvees = [c for c in competences if re.search(r'\b' + re.escape(c) + r'\b', texte_lower)]
    
    return outils_trouves, comps_trouvees

# --- 4. MOTEUR DE SCRAPING CIBLE ---
def moteur_scraping(job, city, contrats, cv_outils, cv_comps):
    results = []
    init_db() 
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)
    
    query = f"{job} {city} {' '.join(contrats)}"
    url = f"https://candidat.francetravail.fr/offres/recherche?motsCles={quote(query)}"
    
    try:
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-id-offre] a.media")))
        offres = driver.find_elements(By.CSS_SELECTOR, "li[data-id-offre] a.media")[:10]
        liens = [o.get_attribute("href") for o in offres]
        
        for lien in liens:
            driver.get(lien)
            
            # Extraction precise du nom de l'entreprise via h3 class="t4 title"
            try:
                ent_nom = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h3.t4.title"))).text.strip()
            except:
                try:
                    ent_nom = driver.find_element(By.CSS_SELECTOR, "span[itemprop='name']").text
                except:
                    ent_nom = "Entreprise Inconnue"

            # Extraction du descriptif via itemprop="description"
            texte_annonce = ""
            try: 
                texte_annonce += driver.find_element(By.CSS_SELECTOR, "div[itemprop='description']").text + " "
            except: pass
            
            if not texte_annonce.strip():
                texte_annonce = driver.find_element(By.TAG_NAME, "body").text

            # Logique de match
            offre_outils, offre_comps = extraire_profil(texte_annonce)
            out_ok = [o for o in offre_outils if o in cv_outils]
            out_ko = [o for o in offre_outils if o not in cv_outils]
            comp_ok = [c for c in offre_comps if c in cv_comps]
            comp_ko = [c for c in offre_comps if c not in cv_comps]
            
            total = len(offre_outils) + len(offre_comps)
            score = round((len(out_ok) + len(comp_ok)) / total * 100, 1) if total > 0 else 0.0
            
            if check_and_save_new_job(lien) and score >= 50:
                envoyer_alerte_bureau(ent_nom, job, score)
                
            results.append({
                "Entreprise": ent_nom,
                "Match (%)": score,
                "Points Forts": ", ".join(out_ok + comp_ok).title() or "-",
                "Skills Manquants": ", ".join(out_ko + comp_ko).title() or "-",
                "Lien": lien
            })
    except Exception as e:
        st.error(f"Erreur : {e}")
    finally:
        driver.quit()
    return results

# --- 5. INTERFACE UI ---
st.title("DBR Job Analyzer - Liste Complete et Alertes")

with st.sidebar:
    st.header("1. Dossier Candidat")
    cv_file = st.file_uploader("Charger le CV (PDF)", type="pdf")
    cv_outils, cv_comps = [], []
    if cv_file:
        cv_text = extraire_texte_cv(cv_file)
        cv_outils, cv_comps = extraire_profil(cv_text)
        st.success("CV analyse avec succes !")
        with st.expander("Voir le profil extrait", expanded=True):
            st.markdown("**Outils Informatiques :**")
            st.write(", ".join(cv_outils).upper() if cv_outils else "Aucun detecte")
            st.markdown("**Competences Metier :**")
            st.write(", ".join(cv_comps).title() if cv_comps else "Aucune detectee")

    st.header("2. Parametres")
    job_in = st.text_input("Poste", "Data Scientist")
    city_in = st.text_input("Ville", "Strasbourg")
    contrats_in = st.multiselect("Contrats", ["CDI", "Alternance", "CDD"], default=["Alternance"])
    
    if st.button("Lancer la recherche", use_container_width=True):
        if cv_file:
            st.session_state.data_jobs = moteur_scraping(job_in, city_in, contrats_in, cv_outils, cv_comps)
        else:
            st.warning("Veuillez charger un CV.")

if st.session_state.data_jobs:
    df = pd.DataFrame(st.session_state.data_jobs).sort_values(by="Match (%)", ascending=False).reset_index(drop=True)
    df.index += 1
    
    st.subheader("Offres disponibles")
    st.dataframe(
        df[["Entreprise", "Match (%)", "Points Forts", "Skills Manquants", "Lien"]],
        column_config={
            "Match (%)": st.column_config.ProgressColumn("Match (%)", format="%f %%", min_value=0, max_value=100),
            "Lien": st.column_config.LinkColumn("Lien", display_text="Voir l'annonce")
        },
        use_container_width=True
    )
    
    st.markdown("---")
    
    st.subheader("Analyse detaillee")
    selection = st.selectbox("Selectionnez une entreprise :", df["Entreprise"].tolist())
    ligne = df[df["Entreprise"] == selection].iloc[0]
    score_match = ligne["Match (%)"]
    
    col_text, col_chart = st.columns([2, 1])
    with col_text:
        st.header(f"Entreprise : {ligne['Entreprise']}")
        st.write(f"**Points Forts detectes :** {ligne['Points Forts']}")
        st.write(f"**Elements Manquants :** {ligne['Skills Manquants']}")
        st.write(f"[Lien direct vers l'annonce]({ligne['Lien']})")
    
    with col_chart:
        fig = px.pie(values=[score_match, 100 - score_match] if score_match > 0 else [0, 100], 
                     names=["Match", "Manque"], color_discrete_sequence=["#27ae60", "#e74c3c"], hole=0.5)
        st.plotly_chart(fig, use_container_width=True)