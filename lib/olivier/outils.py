import math
import re
import unidecode
from rich.console import Console
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import locale
import dateparser

locale.setlocale(category=locale.LC_ALL, locale="fr_FR.UTF-8")

CLAUSE_SOCIALE = "ClauseSociale"
PROJET_UT7 = "Ut7"
PORTAGE = "Portage"
PROVISIONS = "Provisions"
AOF = "Aof"


class color:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def genere_lien_facture(numero_facture):
    return f"^F{unidecode.unidecode(numero_facture)}"


def extrait_montant(montant):
    if isinstance(montant, str):
        montant = "".join((ch if ch in "0123456789.,-" else "") for ch in montant)
        if "," in montant and "." in montant:
            if montant.rindex(",") > montant.rindex("."):
                montant = montant.replace(".", "")
            else:
                montant = montant.replace(",", "")
        if "." not in montant:
            montant = montant.replace(",", ".")
        return float(montant)
    return montant


def extrait_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return datetime.strptime(date_str, "%Y%m%d").date()


def converti_date(datestr, langue):
    if langue == "fr":
        # Corrections des abréviations problématiques
        # bug datepaser https://github.com/scrapinghub/dateparser/issues/819
        corrections = {"sept.": "septembre", "Sept.": "Septembre"}
        for abbreviation, complet in corrections.items():
            datestr = datestr.replace(abbreviation, complet)

    date = dateparser.parse(datestr, languages=[langue])
    return (
        f"date {datestr} non parsable pour la langue {langue}"
        if not date
        else formate_date(date)
    )


def formate_date(date):
    return date.strftime("%Y-%m-%d")


def mois_suivant(date):
    return date.replace(day=28) + timedelta(days=4)


def dernier_jour_du_mois_precedent(date):
    return date.replace(day=1) - timedelta(days=1)


def dernier_jour_du_mois(date):
    return dernier_jour_du_mois_precedent(mois_suivant(date))


def dernier_jour_mois_facturation(date, facturation_ouverte=lambda _: True):
    mois_facturation = date
    if date.day < 10:
        mois_facturation = dernier_jour_du_mois_precedent(date)
    else:
        mois_facturation = dernier_jour_du_mois(date)
    if not facturation_ouverte(mois_facturation):
        mois_facturation = dernier_jour_du_mois(mois_suivant(mois_facturation))
    return mois_facturation


def affiche_mois_facturation(date, format="%m_%Y", facturation_ouverte=lambda _: True):
    mois_facturation = dernier_jour_mois_facturation(date, facturation_ouverte)
    return mois_facturation.strftime(format)


def calcule_date_paiement(date, sous_traitant, projet):
    date_paiement = date + relativedelta(days=10)
    if "delai" in sous_traitant:
        date_paiement = date + relativedelta(days=sous_traitant["delai"])
    elif projet == PROVISIONS:
        date_paiement = date + relativedelta(days=1)
    return date_paiement


def nom_technique(nom):
    return re.sub(
        r"[ .,]", "", re.sub(r"[-'*/&()]", " ", unidecode.unidecode(nom)).title()
    )


def format_numero_facture(numero):
    numero_formate = numero
    numero_formate = re.sub(r"[/∙]", "_", numero_formate)
    numero_formate = re.sub(r"(FACTURE|N°)", "", numero_formate, flags=re.IGNORECASE)
    numero_formate = re.sub(r"[ °]", "", numero_formate)
    return numero_formate


def projet_mois(projet, mois_facturation):
    nom_projet = re.sub(r":Frais$", "", projet)
    nom_projet = re.sub(r".*:", "", nom_projet)
    return f"{nom_projet}_{mois_facturation}"


def calcule_frais_change_qonto(montant):
    cents = montant * 100
    deux_pourcent = math.ceil(cents * 2 / 100)
    return round(deux_pourcent / 100, 2)


def date_pour_le_mois(mois, aujourd_hui=None):
    if aujourd_hui is None:
        aujourd_hui = datetime.today()
    annee = aujourd_hui.year
    if mois > aujourd_hui.month:
        annee -= 1
    return dernier_jour_du_mois(datetime(annee, mois, 1))


def filtre_caracteres_nom_fichier(string):
    return re.sub(r"[', :/;]", "_", string)


def print_rouge(string):
    console = Console()
    console.print(f"[red][bold]{string}")
