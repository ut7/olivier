from datetime import datetime
from olivier.api_grist import adaptateur_v1, adaptateur_v2, adaptateur_v3


def test_adaptateur_facture_v1():
    facture = {
        'Qui_': 3,
        'Date': 1712880000,
        'Numero_de_facture': 'numero_facture',
        'Nbr_de_jours': 10,
        'gristHelper_Display': 500,
        'Frais_HT': None,
        'Montant_TTC': 6000,
        'Un_message_': "Et voici ma facture d'avril",
    }
    email = {
        "api#3": "nom@consultant.fr"
    }
    facture = adaptateur_v1(facture, "api", lambda api, id_tier: email[f"{api}#{id_tier}"])
    assert facture == {
        'Qui_': 3,
        'Contact': 'nom@consultant.fr',
        'Date': 1712880000,
        'Numero_de_facture': 'numero_facture',
        'Nbr_de_jours': 10,
        'gristHelper_Display': 500,
        'TJ': 500,
        'Frais_HT': 0,
        'Montant_TTC': 6000,
        'Un_message_': "Et voici ma facture d'avril",
        'Facture': 'numero_facture',
        'Montant TTC': 6000,
        'un message': "Et voici ma facture d'avril"
    }


def test_adaptateur_v1_gristHelper_Display2():
    facture = {
        'Qui_': 3,
        'Date': 1712880000,
        'Numero_de_facture': 'numero_facture',
        'Nbr_de_jours': 10,
        'gristHelper_Display': 'Anne Faubry',
        'Tarif': 2,
        'gristHelper_Display2': 500,
        'Frais_HT': 0,
        'Montant_TTC': 6000,
        'Un_message_': "Et voici ma facture d'avril",
    }
    facture = adaptateur_v1(facture, "api", lambda api, id_tier: "")
    assert facture['TJ'] == 500


def test_adaptateur_v1_avec_Total_TTC():
    facture = {
        'Qui_': 3,
        'Date': 1712880000,
        'Numero_de_facture': 'numero_facture',
        'Nbr_de_jours': 10,
        'gristHelper_Display': 'Anne Faubry',
        'Tarif': 2,
        'gristHelper_Display2': 500,
        'Frais_HT': 0,
        'Total_TTC': 6000,
        'Un_message_': "Et voici ma facture d'avril",
    }
    facture = adaptateur_v1(facture, "api", lambda api, id_tier: "")
    assert facture['Montant TTC'] == 6000


def test_adaptateur_facture_v2():
    facture = {
        'Prestataire': 3,
        'Email': 'nom@consultant.fr',
        'Date': 1712880000,
        'Numero_de_facture': 'numero_facture',
        'Nbr_de_jours': 10,
        'Tarif_journalier': 500,
        'Frais_HT': None,
        'Total_TTC': 6000,
        'Un_message_': "Et voici ma facture d'avril",
    }
    facture = adaptateur_v2(facture, "api")
    assert facture == {
        'Prestataire': 3,
        'Email': 'nom@consultant.fr',
        'Contact': 'nom@consultant.fr',
        'Date': 1712880000,
        'Numero_de_facture': 'numero_facture',
        'Nbr_de_jours': 10,
        'Tarif_journalier': 500,
        'TJ': 500,
        'Frais_HT': 0,
        'Total_TTC': 6000,
        'Un_message_': "Et voici ma facture d'avril",
        'Facture': 'numero_facture',
        'Montant TTC': 6000,
        'un message': "Et voici ma facture d'avril"
    }


def test_adaptateur_facture_v2_sans_message():
    facture = {
        'Prestataire': 3,
        'Email': 'nom@consultant.fr',
        'Date': 1712880000,
        'Numero_de_facture': 'numero_facture',
        'Nbr_de_jours': 10,
        'Tarif_journalier': 500,
        'Frais_HT': None,
        'Total_TTC': 6000,
        'Un_message_': "",
    }
    facture = adaptateur_v2(facture, "api")
    assert facture == {
        'Prestataire': 3,
        'Email': 'nom@consultant.fr',
        'Contact': 'nom@consultant.fr',
        'Date': 1712880000,
        'Numero_de_facture': 'numero_facture',
        'Nbr_de_jours': 10,
        'Tarif_journalier': 500,
        'TJ': 500,
        'Frais_HT': 0,
        'Total_TTC': 6000,
        'Facture': 'numero_facture',
        'Montant TTC': 6000,
        'Un_message_': "",
        'un message': "",
    }


def test_adaptateur_facture_v3():
    facture = {
        'Prestataire': 3,
        'Email': 'nom@consultant.fr',
        'gristHelper_Display': 759,
        'gristHelper_Display2': 'Driss Ait Ali',
        'Date': 1712880000,
        'Mois_de_facturation': 1774915200,
        'Numero_de_facture': 'numero_facture',
        'Nbr_de_jours': 10,
        'Frais_HT': None,
        'Total_TTC': 6000,
        'Un_message_': "Et voici ma facture d'avril",
    }
    facture = adaptateur_v3(facture, "api")
    assert facture == {
        'Prestataire': 3,
        'Email': 'nom@consultant.fr',
        'Contact': 'nom@consultant.fr',
        'Nom': 'Driss Ait Ali',
        'gristHelper_Display': 759,
        'gristHelper_Display2': 'Driss Ait Ali',
        'TJ': 759,
        'Date': 1712880000,
        'Mois_de_facturation': 1774915200,
        'Mois de facturation': datetime(2026, 3, 31, 2, 0),
        'Numero_de_facture': 'numero_facture',
        'Nbr_de_jours': 10,
        'Frais_HT': 0,
        'Total_TTC': 6000,
        'Facture': 'numero_facture',
        'Montant TTC': 6000,
        'Un_message_': "Et voici ma facture d'avril",
        'un message': "Et voici ma facture d'avril",
    }
