import os
from collections import namedtuple
from datetime import datetime
from cachetools import cached
from grist_api import GristDocAPI

LIGNE_GL = namedtuple(
    "LIGNE_GL", "key Date Flag Tiers Narration Montant_EUR_HT_ Solde_EUR_HT_ Tags"
)
LIGNE_PROJET = namedtuple("LIGNE_PROJET", "Nom Id_document_projet")

SERVER = "https://grist.la.zone"
DOC_ID = {
    "FranceConnect": "nhto1PYFLZLXqrZaiXyMha"
}


@cached(cache={})
def recupere_structure(api):
    constantes = api.fetch_table('Constantes')
    version = getattr(constantes[0], 'Version_structure', 'v1')
    return STRUCTURES_DOCUMENTS_SUIVIS[version]


@cached(cache={})
def recupere_Equipe(api):
    structure = recupere_structure(api)
    return api.fetch_table(structure["table_contacts"])


def recupere_email(api, id_qui):
    equipe = recupere_Equipe(api)
    structure = recupere_structure(api)
    contact_de = structure["contact_de"]
    return [contact_de(membre) for membre in equipe if membre.id == id_qui][0]


def recupere_id_qui(api, facture):
    if "Qui_" in facture:
        return facture["Qui_"]
    if "Prestataire" in facture:
        return facture["Prestataire"]

    email = facture["Contact"]
    equipe = recupere_Equipe(api)

    def contacts(member):
        contacts = getattr(member, "gristHelper_Display", None) or getattr(
            member, "gristHelper_Display2", None
        )
        return [c.strip() for c in contacts]

    ids = [membre.id for membre in equipe if email in contacts(membre)]
    return ids[0] if len(ids) == 1 else None


def recupere_api(nom_projet):
    return GristDocAPI(DOC_ID[nom_projet],
                       server=SERVER,
                       api_key=os.environ.get("GRIST_API_KEY"))


def init_champ(facture, nom, valeur):
    if nom not in facture or facture[nom] is None:
        facture[nom] = valeur


def adaptateur_v1(facture, api, recupere_email=recupere_email):
    facture["Contact"] = recupere_email(api, facture["Qui_"])
    facture['TJ'] = (
        facture["gristHelper_Display"]
        if not isinstance(facture["gristHelper_Display"], str)
        else facture["gristHelper_Display2"]
    )
    facture["Facture"] = facture["Numero_de_facture"]
    init_champ(facture, "Frais_HT", 0)
    facture["Montant TTC"] = (
        facture["Montant_TTC"] if "Montant_TTC" in facture else facture["Total_TTC"]
    )
    facture["un message"] = facture['Un_message_']
    return facture


def adaptateur_v2(facture, _api):
    facture["TJ"] = facture["Tarif_journalier"]
    facture["Contact"] = facture["Email"]
    facture["Facture"] = facture["Numero_de_facture"]
    init_champ(facture, "Frais_HT", 0)
    facture["Montant TTC"] = facture["Total_TTC"]
    facture["un message"] = facture['Un_message_']

    return facture


def adaptateur_v3(facture, _api):
    facture["TJ"] = facture["gristHelper_Display"]
    facture["Contact"] = facture["Email"]
    facture["Nom"] = facture["gristHelper_Display2"]
    facture["Facture"] = facture["Numero_de_facture"]
    init_champ(facture, "Frais_HT", 0)
    facture["Montant TTC"] = facture["Total_TTC"]
    facture["un message"] = facture['Un_message_']

    return facture


STRUCTURES_DOCUMENTS_SUIVIS = {
    "v1": {
        "nom_table_factures_recues": "Factures_soustraitants",
        "filtres": {"Acceptee": False, "Refusee": False},
        "adaptateur": adaptateur_v1,
        "table_contacts": "equipe",
        "contact_de": lambda membre: membre.email,
    },
    "v2": {
        "nom_table_factures_recues": "Factures_Recues",
        "filtres": {"Acceptee": False, "Refusee": False, "Perimetre": 2},
        "adaptateur": adaptateur_v2,
        "table_contacts": "Sous_traitantes"
    },
    "v3": {
        "nom_table_factures_recues": "Factures_soustraitants",
        "filtres": {"Etat": "Déposée"},
        "adaptateur": adaptateur_v3,
        "table_contacts": "Prestataires",
    },
}


def factures_non_traitees(nom_projet):
    api = recupere_api(nom_projet)
    structure = recupere_structure(api)
    adaptateur = structure["adaptateur"]
    factures = api.fetch_table(
        structure['nom_table_factures_recues'],
        structure['filtres']
    )
    return [
        adaptateur(facture._asdict(), api) for facture in factures if facture.PDF_Facture is not None
    ]


def marque_traitee(facture):
    nom_projet = facture["grist_projet"]
    api = recupere_api(nom_projet)
    structure = recupere_structure(api)
    api.update_records(
        structure['nom_table_factures_recues'],
        [
            {
                "id": facture["id"],
                "Acceptee": True,
            }
        ],
    )


def refuse_facture_grist(nom_projet, facture, raison):
    api = recupere_api(nom_projet)
    api.update_records(
        "Factures_soustraitants",
        [
            {
                "id": facture["id"],
                "Refusee": True,
                "Raison_du_refus": raison,
            }
        ],
    )


def recupere_donnees_grist_attachment(nom_projet, id_attachment):
    api = recupere_api(nom_projet)
    return api.call(f"attachments/{id_attachment}", method="GET").json()


def recupere_grist_attachment(nom_projet, id_attachment):
    api = recupere_api(nom_projet)
    return api.call(f"attachments/{id_attachment}/download", method="GET")


def publie_grand_livre_projet(nom_projet, transactions):
    api = recupere_api(nom_projet)
    api.sync_table(
        "Grand_Livre",
        transactions,
        [("key", "key")],
        [
            ("Date", "Date"),
            ("Flag", "Flag"),
            ("Tiers", "Tiers"),
            ("Narration", "Narration"),
            ("Montant_EUR_HT_", "Montant_EUR_HT_"),
            ("Solde_EUR_HT_", "Solde_EUR_HT_"),
            ("Tags", "Tags"),
        ],
    )
    infos = api.fetch_table("Informations_publication_des_comptes")
    if len(infos) == 0:
        api.add_records(
            "Informations_publication_des_comptes",
            [
                {
                    "Date_de_deniere_mise_a_jour": datetime.now(),
                }
            ],
        )
    else:
        api.update_records(
            "Informations_publication_des_comptes",
            [
                {
                    "id": 1,
                    "Date_de_deniere_mise_a_jour": datetime.now(),
                }
            ],
        )


def actualise_budget_grist(nom_projet, facture, mois_facturation):
    api = recupere_api(nom_projet)
    if not api:
        return

    id_qui = recupere_id_qui(api, facture)
    prestations = api.fetch_table(
        "Prestations",
        {"Prestataire": id_qui, "Prevision_": True, "mois_de_facturation": mois_facturation},
    )
    if len(prestations) != 1:
        raise ValueError(
            f"Actualisation budget impossible : {len(prestations)} prévision(s) trouvée(s) "
            f"(attendu : 1) — prestations : {prestations}"
        )

    prestation = prestations[0]
    colonne_nbr_jour = (
        "Jours_factures" if hasattr(prestation, "Jours_factures") else "Nbr_de_jours"
    )
    mise_a_jour = {
        "id": prestation.id,
        "Date": mois_facturation,
        colonne_nbr_jour: facture["Nbr_de_jours"],
        "Frais": facture["Frais_HT"],
        "Prevision_": False,
    }
    api.update_records("Prestations", [mise_a_jour])
