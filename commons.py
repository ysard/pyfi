"""Common configuration settings, global constants, dataset files used by the simulations"""
# Standard imports
from pathlib import Path
import locale


ASSETS_DIR = Path("./assets/")


# --- Historical data ---
# https://webstat.banque-france.fr/fr/catalogue/mir1/MIR1.M.FR.B.L22FRSP.H.R.A.2250U6.EUR.N
PEL_RATES_FILEPATH = ASSETS_DIR / "Webstat_Export_fr_MIR1.M.FR.B.L22FRSP.H.R.A.2250U6.EUR.N.csv"
# https://webstat.banque-france.fr/fr/catalogue/mir1/MIR1.M.FR.B.L23FRLA.D.R.A.2230U6.EUR.O
LIVRETA_RATES_FILEPATH = ASSETS_DIR / "Webstat_Export_fr_MIR1.M.FR.B.L23FRLA.D.R.A.2230U6.EUR.O.csv"
# IPCH: https://webstat.banque-france.fr/fr/catalogue/icp/ICP.M.FR.N.000000.4.ANR
INFLATION_IPCH_RATES_FILEPATH = ASSETS_DIR / "Webstat_Export_fr_ICP.M.FR.N.000000.4.ANR.csv"
# IPC: https://www.insee.fr/fr/statistiques/serie/001768580
# indice brut: https://www.insee.fr/fr/statistiques/serie/000641194
# Jeux de données :
# - Type de ménage : Ensemble des ménages
# - Produits : Ensemble hors tabac
# - Nature : Glissement annuel
# - Zone : France
# - Périodicité : Mensuelle
INFLATION_IPC_RATES_FILEPATH = ASSETS_DIR / "valeurs_mensuelles.csv"
# ^SP500: https://fr.finance.yahoo.com/quote/%5ESPX/history/?frequency=1mo&filter=history&period1=-1325583000&period2=1772667522
# SP500_RATES_FILEPATH = ASSETS_DIR / "^SPX.csv"
# ^SP500TR (Total Return / dividendes réinvestis): https://finance.yahoo.com/quote/%5ESP500TR/
SP500TR_RATES_FILEPATH = ASSETS_DIR / "^SP500TR.csv"

ASSURANCE_VIE_RATES = {
    # https://leparticulier.lefigaro.fr/upload/internet_files/abonne/media/attribut/pdf/6335.pdf
    1999: 0.0635,
    # https://www.lexpress.fr/economie/le-palmares-des-contrats-d-assurance-vie-en-2000_1351821.html
    2000: 0.0635,
    # https://www.argusdelassurance.com/dossier/assurance-vie-avec-des-performances-moyennes-d-environ-5-en-2002-la-gestion-en-euros-a-atteint-un-point-bas-mais-les-ecarts-sur-le-marche-ne-cessent-de-s-accentuer-les-rendements-vont-du-simpl.14089
    2001: 0.0625,
    2002: 0.0528,
    # 2003 ?? https://fr.scribd.com/document/957437139/assurancevie-euros-2000-2003
    2003: 0.0515,
    # https://www.lesechos.fr/2005/02/ou-vont-les-contrats-dassurance-vie-1064738
    # https://www.argusdelassurance.com/marches/produits-services/la-retraite-de-la-macsf-est-au-point.29981
    # https://leparticulier.lefigaro.fr/upload/internet_files/abonne/media/attribut/pdf/6829.pdf
    2004: 0.0505,  # 5.03% ?
    2005: 0.0477,
    # https://www.lequotidiendumedecin.fr/archives/465-pour-le-contrat-res-de-la-macsf
    2006: 0.0465,
    2007: 0.0465,
    # https://www.lexpress.fr/argent/fiscalite/assurance-vie-tous-les-rendements-2008_1606656.html?cmp_redirect=true
    2008: 0.0465,
    # Official source
    2009: 0.0455,
    2010: 0.0405,
    2011: 0.0365,
    2012: 0.035,
    2013: 0.034,
    2014: 0.031,
    2015: 0.0285,
    2016: 0.024,
    2017: 0.024,
    2018: 0.022,
    2019: 0.017,
    2020: 0.0155,
    2021: 0.021,
    2022: 0.025,
    2023: 0.031,
    2024: 0.031,
    2025: 0.0315,
}

try:
    # Try to load French locale if available
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
except locale.Error:
    pass

def eur_fmt(value, fmt="%.2f", currency="€"):
    """Format the given value to a monetary localized amount in euros"""
    return locale.format_string(fmt, value, grouping=True, monetary=True) + f" {currency}"
