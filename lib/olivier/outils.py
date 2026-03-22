import math
import os
import re
from subprocess import run
import unidecode
from rich.console import Console
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from jinja2 import FileSystemLoader, Environment
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


def compte_depenses(nom_technique, sous_traitant):
    if "compte" in sous_traitant:
        return sous_traitant["compte"]
    else:
        return f"Expenses:SousTraitants:{nom_technique}"


def compte_credit(projet):
    if projet == CLAUSE_SOCIALE:
        return "Assets:Qonto:Provisions:ClauseSociale"
    if projet == PROVISIONS:
        return "Assets:Qonto:Provisions:DepensesRecurentes"
    if projet == PORTAGE:
        return "Assets:Qonto:ADisposition:Portage:Dinum"
    if projet == PROJET_UT7:
        return "Assets:Qonto:ADisposition"
    if projet.startswith(AOF):
        return f"Assets:Qonto:{projet}"
    return f"Assets:Qonto:Projets:{projet}"


def projet_mois(projet, mois_facturation):
    nom_projet = re.sub(r":Frais$", "", projet)
    nom_projet = re.sub(r".*:", "", nom_projet)
    return f"{nom_projet}_{mois_facturation}"


def facturation_ouverte(projet, date_mois_facturation):
    mois_facturation = date_mois_facturation.strftime("%m_%Y")
    lien = projet_mois(projet, mois_facturation)
    resultat = run(
        args=["grep", f'cloture_facturation: "{lien}', "transactions.beancount"],
        capture_output=True,
        text=True,
    )
    cloture_trouvee = str(resultat.stdout)
    return len(cloture_trouvee) == 0


def calcule_frais_change_qonto(montant):
    cents = montant * 100
    deux_pourcent = math.ceil(cents * 2 / 100)
    return round(deux_pourcent / 100, 2)


def transaction_salaire(date, personne, net_a_payer, pas, net_a_payer_avec_pas):
    assert abs(net_a_payer + pas - net_a_payer_avec_pas) < 0.001
    return transactions({
        "date": formate_date(date),
        "personne": personne,
        "nom_technique": nom_technique(personne),
        "mois_paye": affiche_mois_facturation(date),
        "net_a_payer": net_a_payer,
        "pas": pas,
        "net_a_payer_avec_pas": -net_a_payer_avec_pas
    }, "transaction_salaire.beancount")


def transaction_balance(balance, date):
    date = formate_date(date)
    return f"{date} balance Assets:Qonto                     {balance:10.2f} EUR"


def transactions(entrees, nom_template):
    project_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    template_loader = FileSystemLoader(
        searchpath=f"{project_path}/olivier/templates"
    )
    template_env = Environment(loader=template_loader)
    template = template_env.get_template(nom_template)
    return template.render(entrees)


def met_en_retard_transaction(virement):
    date = virement["date"]
    date_str = formate_date(date)
    nouvelle_date = formate_date(date + relativedelta(months=1))
    nom = re.sub("/", "\/", re.escape(virement["personne"]))
    numero_facture = virement["numero_facture"]
    compte_depart = "EnAttenteDePaiement"
    compte_arrive = "EnRetard1A30Jours"
    return f"\
perl -i -w -0pe 's/({date_str}) ! (\"{nom}[^\n]*{numero_facture} :[^\n]*)\n([^\n]*){compte_depart}([^\n]*)\n/\
$1 * $2\n\
$3{compte_depart}$4\n\
$3{compte_arrive}\n\
\n\
{nouvelle_date} ! $2\n\
$3{compte_arrive}$4\n/sg' transactions.beancount"


def coche_transaction(date, virement):
    lien = ""
    nom = virement["personne"].replace("/", "\\/").replace("'", ".")
    debut_narration = ""
    if "numero_facture" in virement:
        lien = f".*\\{genere_lien_facture(virement['numero_facture'])}"
    elif "debut_narration" in virement:
        debut_narration = f".*{virement['debut_narration']}"

    if "lien" in virement:
        lien = f".*\\^{virement['lien']}"

    date_str = formate_date(date)
    return f"perl -i -pe 's/....-..-.. ! (\"{nom}{debut_narration}{lien})/{date_str} * $1/sg' transactions.beancount"


def filtre_caracteres_nom_fichier(string):
    return re.sub(r"[', :/;]", "_", string)


def print_rouge(string):
    console = Console()
    console.print(f"[red][bold]{string}")
