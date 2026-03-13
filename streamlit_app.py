"""Streamlit webapp

Run: $ streamlit run streamlit_app.py

"""
# Standard imports
from datetime import date, datetime

# Custom imports
import streamlit as st

# Local imports
from comp_pel_a_av import simulate, make_graphs, make_plotly, get_cagr_df


def web_interface():
    """Setup streamlit sidebar"""
    st.set_page_config(layout="wide")

    st.title("Simulation d'épargne")

    st.sidebar.header("Paramètres")

    capital_initial = st.sidebar.number_input(
        "Capital initial (€)", value=23000, step=1000
    )

    years_duration = st.sidebar.slider("Durée (années)", 1, 40, 26)

    start_date = st.sidebar.date_input(
        "Date de début",
        # No inflation rate available before
        min_value=date(1999, 1, 1),
        max_value=date.today(),
        value=date(2000, 1, 1),
    )

    st.sidebar.subheader("Taux")

    pel_rate = st.sidebar.number_input("Taux PEL (%) (auto si 0)", value=0.0)
    pel_rate = None if pel_rate == 0 else pel_rate / 100

    av_fees_rate = st.sidebar.slider("Frais gestion AV (%)", 0.0, 2.0, 0.0) / 100

    st.sidebar.subheader("Fiscalité (PEL)")

    # use_pfu checkbox must enable/disable the ir_tmi slider
    if "use_pfu" not in st.session_state:
        st.session_state.use_pfu = True

    pfu_enabled = st.sidebar.checkbox("Utiliser PFU 30% (31.4% en 2026)", key="use_pfu")

    ps = 0.172
    ir_tmi = (
        st.sidebar.select_slider(
            "TMI (%)",
            value=30,
            options=(0, 11, 30, 41, 45),
            disabled=st.session_state.use_pfu,
        )
        / 100
    )

    pfu = 0.30 if pfu_enabled else None

    st.sidebar.subheader("Inflation")

    ipc_tooltip_text = """
    # IPCH :
    Conçu pour évaluer la stabilité des prix et n'a pas vocation à être un indice du coût de la vie.
    Couvre toutes les dépenses sur le territoire : résidents, touristes, étrangers.
    Conforme à la logique économique européenne, utilisé pour comparer l’inflation entre pays européens.
    Cohérence avec publications financières

    # IPC :
    Cohérence avec le pouvoir d’achat réel d’un ménage français.

    Note : Aucun indice ne couvre l'évolution des prix des logements à l'achat.

    # Jeux de données :
    - Type de ménage : Ensemble des ménages
    - Produits : Ensemble hors tabac
    - Nature : Glissement annuel
    - Zone : France
    - Périodicité : Mensuelle
    """

    ipch = st.sidebar.toggle(
        "Utiliser indice IPCH (sinon IPC)",
        value=False,
        help=ipc_tooltip_text,
    )

    st.sidebar.subheader("Graphe")
    show_av_withdrawal_sold = st.sidebar.checkbox("Montrer le solde net AV")
    show_pea_withdrawal_sold = st.sidebar.checkbox("Montrer le solde net PEA")

    return {
        "capital_initial": capital_initial,
        "start_date": start_date,
        "years_duration": years_duration,
        "ipch": ipch,
        "pel_rate": pel_rate,
        "av_fees_rate": av_fees_rate,
        "pfu_enabled": pfu_enabled,
        "ir_tmi": ir_tmi,
        "show_av_withdrawal_sold": show_av_withdrawal_sold,
        "show_pea_withdrawal_sold": show_pea_withdrawal_sold,
    }


def main():
    ret = web_interface()
    # Convert to datetime: We do not need hours, but values in dataframe are in datetime format
    dt_pel_start = ret["start_date"]
    dt_pel_start = datetime(dt_pel_start.year, dt_pel_start.month, dt_pel_start.day)
    ret["dt_pel_start"] = dt_pel_start

    # fig = make_graphs(*simulate(**ret), dt_pel_start=dt_pel_start, interactive=False)
    # st.pyplot(fig)

    # Workaround for https://github.com/plotly/plotly.py/issues/4052
    # See https://stackoverflow.com/questions/52095414/how-to-change-the-language-locale-in-dash-plotly-or-the-label-of-the-plotly
    locales={
        'fr-FR':{
            'dictionary': {
                'Autoscale': 'Échelle automatique',
                'Box Select': 'Sélection rectangulaire',
                'Click to enter Colorscale title': 'Ajouter un titre à l\'échelle de couleurs',
                'Click to enter Component A title': 'Ajouter un titre à la composante A',
                'Click to enter Component B title': 'Ajouter un titre à la composante B',
                'Click to enter Component C title': 'Ajouter un titre à la composante C',
                'Click to enter Plot title': 'Ajouter un titre au graphique',
                'Click to enter Plot subtitle': 'Ajouter un sous-titre au graphique',
                'Click to enter X axis title': 'Ajouter un titre à l\'axe des x',
                'Click to enter Y axis title': 'Ajouter un titre à l\'axe des y',
                'Click to enter radial axis title': 'Ajouter un titre à l\'axe radial',
                'Compare data on hover': 'Comparaison entre données en survol',
                'Double-click on legend to isolate one trace': 'Double-cliquer sur la légende pour isoler une série',
                'Double-click to zoom back out': 'Double-cliquer pour dézoomer',
                'Download plot as a PNG': 'Télécharger le graphique en fichier PNG',
                'Download plot': 'Télécharger le graphique',
                'Edit in Chart Studio': 'Éditer le graphique sur Chart Studio',
                'IE only supports svg.  Changing format to svg.': 'IE ne permet que les conversions en SVG. Conversion en SVG en cours.',
                'Lasso Select': 'Sélection lasso',
                'Orbital rotation': 'Rotation orbitale',
                'Pan': 'Translation',
                'Produced with Plotly.js': 'Généré avec Plotly.js',
                'Reset': 'Réinitialiser',
                'Reset axes': 'Réinitialiser les axes',
                'Reset camera to default': 'Régler la caméra à sa valeur défaut',
                'Reset camera to last save': 'Régler la caméra à sa valeur sauvegardée',
                'Reset view': 'Réinitialiser',
                'Reset views': 'Réinitialiser',
                'Show closest data on hover': 'Données les plus proches en survol',
                'Snapshot succeeded': 'Conversion réussie',
                'Sorry, there was a problem downloading your snapshot!': 'Désolé, un problème est survenu lors du téléchargement de votre graphique',
                'Taking snapshot - this may take a few seconds': 'Conversion en cours, ceci peut prendre quelques secondes',
                'Zoom': 'Zoom',
                'Zoom in': 'Zoom intérieur',
                'Zoom out': 'Zoom extérieur',
                'close:': 'fermeture :',
                'trace': 'série',
                'lat:': 'lat. :',
                'lon:': 'lon. :',
                'q1:': 'q1 :',
                'q3:': 'q3 :',
                'source:': 'source :',
                'target:': 'embouchure :',
                'lower fence:': 'clôture inférieure :',
                'upper fence:': 'clôture supérieure :',
                'max:': 'max. :',
                'mean ± σ:': 'moyenne ± σ :',
                'mean:': 'moyenne :',
                'median:': 'médiane :',
                'min:': 'min. :',
                'new text': 'nouveau texte',
                'Turntable rotation': 'Rotation planaire',
                'Toggle Spike Lines': 'Activer/désactiver les pics',
                'open:': 'ouverture :',
                'high:': 'haut :',
                'low:': 'bas :',
                'Toggle show closest data on hover': 'Activer/désactiver le survol',
                'incoming flow count:': 'flux entrant :',
                'outgoing flow count:': 'flux sortant :',
                'kde:': 'est. par noyau :'
            },
            'format': {
                'days': ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'],
                'shortDays': ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'],
                'months': [
                    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
                ],
                'shortMonths': [
                    'Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun',
                    'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'
                ],
                'date': '%d/%m/%Y',
                'decimal': ',',
                'thousands': ' ',
                'year': '%Y',
                'month': '%b %Y',
                'dayMonth': '%-d %b',
                'dayMonthYear': '%-d %b %Y'
            }
        }
    }

    config = {
        'locale': 'fr-FR',
        'locales':locales,
    }
    dates, data = simulate(**ret)
    fig = make_plotly(dates, data, **ret)
    st.plotly_chart(fig, width='stretch', config=config)

    st.markdown("""
    ⚠️ *Les performances passées ne préjugent pas des performances futures et ne
    constituent pas une garantie de rendement.*

    *L’illustration graphique présentée ne constitue pas un indicateur fiable quant
    aux performances futures de vos investissements. Elle a uniquement pour objectif
    d’illustrer les mécanismes de votre investissement sur la durée de placement.
    La valeur de votre investissement peut évoluer à la hausse comme à la baisse et
    s’écarter des résultats affichés.*
    """, width="stretch")

    # Add CAGR table
    st.subheader("Rendement annuel composé réel")
    df_returns = get_cagr_df(dates, data, years_duration=ret["years_duration"])

    st.data_editor(
        df_returns,
        width="stretch",
        column_config={
            "Placement": st.column_config.Column(
                pinned=True,  # stay visible on the left side
                disabled=True,  # disable editing
            ),
            "Capital final (€)": st.column_config.NumberColumn(
                help="Capital final brut en euros (hors fiscalité en sortie)",
                format="euro",  # Monetary values
                step=1,  # Remove decimals
                disabled=True,
            ),
            "Gains (€)": st.column_config.NumberColumn(
                help="Gains finaux en euros (hors fiscalité en sortie)",
                format="euro",
                step=1,
                disabled=True,
            ),
            "CAGR réel (%)": st.column_config.NumberColumn(
                help="Rendement annuel composé réel (hors fiscalité en sortie)",
                format="percent",
                step=0.0001,
                disabled=True,
            ),
        },
    )
    print(df_returns)


if __name__ == "__main__":
    main()
