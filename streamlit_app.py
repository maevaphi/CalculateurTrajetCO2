# -*- coding: utf-8 -*-
"""
Created on Tu Dec 09  2025

@author: MaevaLavignePhilippot
"""


import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from PIL import Image


# -------------------------------
# Créer la table si elle n'existe pas
# -------------------------------
#with engine.begin() as conn:
#    conn.execute(text("""
#        CREATE TABLE IF NOT EXISTS participations (
#            id INT AUTO_INCREMENT PRIMARY KEY,
#            mode VARCHAR(100) NOT NULL,
#            distance FLOAT NOT NULL,
#            nbpassager INT NOT NULL,
#            impact FLOAT NOT NULL,
#            raison TEXT NULL,
#            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#        )
#    """))




# ---------------------------
# Facteurs ADEME par km par passager
# Source https://agirpourlatransition.ademe.fr/particuliers/evaluer-son-impact/calculer-empreinte-carbone/calculer-emissions-carbone-trajets
# ---------------------------
FACTEURS = {
    "Marche": 0,
    "Vélo mécanique": 0.00017,
    "Tramway": 0.00428,
    "Vélo à assistance électrique": 0.011,
    "Trottinette à assistance électrique": 0.0249,
    "Scooter ou moto légère thermique": 0.076,
    "Voiture électrique": 0.103,
    "Bus GNV ou thermique": 0.122,
    "Moto thermique": 0.217,
    "Train (TER)": 0.277,
    "Voiture thermique": 0.218,
}

# ---------------------------
#Interface
# ---------------------------

st.title("🌿 Calculateur CO₂ — Événement")
img = Image.open("logoLong_lesAmiesDesSheds_colvert.png")
st.image(img)
st.header("➤ Je renseigne mon déplacement")

#et si plusieurs modes de transport?
with st.form("impact_presonnel"):
    mode = st.selectbox("Mode de transport", list(FACTEURS.keys()))
    distance = st.number_input("Distance parcourue (en km)", min_value=0.0, step=0.1)
    if mode == "Voiture thermique" or mode == "Moto thermique" or mode == "Voiture électrique" or mode == "Vélo à assistance électrique" or mode  == "Vélo mécanique":
        nbpassager = st.number_input("Nombre de passagers **(en plus du conducteur)**", min_value=0.0, step=1.0)
    else:
        nbpassager = 0

    if mode == "Voiture thermique" or mode == "Moto thermique" or mode == "Voiture électrique" or mode == "Scooter ou moto légère thermique":
        if nbpassager > 0 :
            st.write("Bravo pour le covoiturage !")
        raison = st.text_input("Qu'est ce qui vous aiderait à adopter une mobilité douce ?")
    else :
        raison = ""
        #manque calcul et affiche impact évité par rapport à une personne seule dans une voiture thermique


    if st.form_submit_button("Valider ma participation"):
        if distance <= 0:
            st.error("Merci de rentrer la distance parcourue en km.")
        else:
            impact = distance * FACTEURS[mode] / (nbpassager + 1)
            # -------------------------------
            # Connexion MySQL via SQLAlchemy
            # -------------------------------
            engine = create_engine(
                f"mysql+mysqlconnector://"
                f"{st.secrets['DB_USER']}:{st.secrets['DB_PASSWORD']}"
                f"@{st.secrets['DB_HOST']}:{st.secrets['DB_PORT']}"
                f"/{st.secrets['DB_NAME']}",
                pool_pre_ping=True
            )
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO participations
                        (mode, distance, nbpassager, impact, raison)
                        VALUES (:mode, :distance, :nbpassager, :impact, :raison)
                    """),
                    {
                        "mode": mode,
                        "distance": distance,
                        "nbpassager": nbpassager,
                        "impact": impact,
                        "raison": raison
                    }
                )
            st.success(f"Merci ! Votre impact : **{impact:.2f} kg CO₂e/personne**")
            if mode == "Marche" or mode == "Vélo mécanique" or mode == "Tramway" or mode == "Vélo à assistance électrique" or mode =="Trottinette à assistance électrique":
                st.balloons ()
                st.success("Bravo pour votre choix de mobilité douce !")
    

# ---------------------------
#calcule et affiche l'impact de l'évènemnet par personne
# ---------------------------
st.header("📘 Impact global de l'événement")

with st.form("impact_global"):
    if st.form_submit_button("Afficher l'impact global de l'événement"):
        engine = create_engine(
                f"mysql+mysqlconnector://"
                f"{st.secrets['DB_USER']}:{st.secrets['DB_PASSWORD']}"
                f"@{st.secrets['DB_HOST']}:{st.secrets['DB_PORT']}"
                f"/{st.secrets['DB_NAME']}",
                pool_pre_ping=True
            )
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT impact, nbpassager FROM participations")
            ).fetchall()

        if not rows:
            st.info("Aucune participation enregistrée.")
        else:
            total_impact = 0
            total_personnes = 0

            for impact, nbpassager in rows:
                total_impact += impact
                total_personnes += (1 + nbpassager)
        
            impact_moyen = total_impact / total_personnes

            st.subheader(f"🌍 Impact total : **{total_impact:.2f} kg CO₂e**")
            st.subheader(f"👥 Nombre de participants : **{total_personnes}**")
            st.subheader(f"📊 Impact moyen : **{impact_moyen:.2f} kg CO₂e/personne**")  


if st.checkbox("📊 Afficher la base de données"):
    df = pd.read_sql(
        "SELECT * FROM participations ORDER BY created_at DESC",
        engine
    )
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Export CSV",
        csv,
        "participations.csv",
        "text/csv"
    )





with st.expander("Plus d'info sur le calcul"):
    st.write ("Les transports émettent 1/3 des gaz à effet de serre de la France.")

    st.write ("La bonne nouvelle, c’est que de nouvelles mobilités se dessinent, notamment avec le développement des pistes cyclables, du covoiturage, de l’autopartage..." \
    " Bouger davantage n’est pas seulement bon pour la santé mais cela permet aussi de réduire les émissions de gaz à effet de serre et les pollutions générées par les transports. ")
    st.write("La source des données à l'ADEME.")
    st.write("Les facteurs d'émissions par km et par passager sont les suivants :")
    FACTEURS
    st.link_button("Calculateur trajets de l'ADEME","https://agirpourlatransition.ademe.fr/particuliers/evaluer-son-impact/calculer-empreinte-carbone/calculer-emissions-carbone-trajets")
    st.write("Sont pris en compte : la fabrication, la maintenance, l'usage et la fin de vie des modes de transport." \
    "La construction des infrastructures (routes, rails, aéroports...) n'est pas incluse." \
    "Les facteurs d’émission utilisées pour calculer l’impact carbone des différents modes de transport référencés sont issues de la Base Empreinte de l’ADEME." \
    "La méthodologie de calcul est open source et accessible sur le repo GitHub")
    st.link_button("Repo Github","https://github.com/incubateur-ademe/impactco2")
    st.write("Les hypothèses de calcul de l'ADEME :" \
    "1 seul passager pour une voiture (thermique ou électrique)." \
    "Une moyenne des taux d’occupation des différents modes de transport (Bus : 10 personnes)." \
    "Pour le vélo mécanique, similaire au vélo à assistance électrique, une hypothèse de durée de vie de 12 ans et une distance parcourue de 30 000 km.")


    



