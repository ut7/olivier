from datetime import date, datetime
from olivier.filtres_reception_facture import (
    demande_champs_manquants,
    demande_validation,
    identification_facture_grist,
    verifie_les_champs,
    format_champs,
)


def test_demande_champs_manquants():
    facture = {}

    class Reponses:
        def __init__(self):
            self.i = 0
            self.reponses = [
                ('Quel Nom ? ', 'Nom de ma boite'),
                ('Quel Facture ? ', 'facture1'),
                ('Quel Date de dépôt ? ', 'date'),
                ('Quel Montant HT ? ', 'montant1'),
                ('Quel Montant TTC ? ', 'montantTtc'),
                ('Quel nombre de jours ? ', '1'),
                ('Quel frais HT ([Entrer] pour finir) ? ', ''),
            ]

        def retourne_reponse(self, prompt):
            reponse_courante = self.reponses[self.i]
            self.i += 1
            assert reponse_courante[0] == prompt
            return reponse_courante[1]

    reps = Reponses()
    demande_champs_manquants(facture, lambda prompt: reps.retourne_reponse(prompt))
    assert facture['Nom'] == 'Nom de ma boite'
    assert facture['Facture'] == 'facture1'
    assert facture['Date de dépôt'] == 'date'
    assert facture['Montant HT'] == 'montant1'
    assert facture['Montant TTC'] == 'montantTtc'
    assert facture['Nbr_de_jours'] == 1.0
    assert facture['Frais_HT'] == 0


def test_demande_champs_manquants_grist():
    facture = {
        'Nom': 'nom',
        'Facture': 'numéro',
        'Date de dépôt': 'date',
        'Montant HT': 'montant1',
        'Montant TTC': 'montantTtc',
    }

    class Reponses:
        def __init__(self):
            self.i = 0
            self.reponses = [
                ('Quel nombre de jours ? ', '10,5'),
                ('Quel frais HT ([Entrer] pour finir) ? ', '100,23'),
                ('Quel frais HT ([Entrer] pour finir) ? ', '25.11'),
                ('Quel frais HT ([Entrer] pour finir) ? ', ''),
            ]

        def retourne_reponse(self, prompt):
            reponse_courante = self.reponses[self.i]
            self.i += 1
            assert reponse_courante[0] == prompt
            return reponse_courante[1]

    reps = Reponses()
    demande_champs_manquants(facture, lambda prompt: reps.retourne_reponse(prompt))
    assert facture['Nbr_de_jours'] == 10.5
    assert facture['Frais_HT'] == 125.34


def test_verifie_les_champs_montant_TTC_inferieur_montant_HT():
    facture = {'Montant TTC': 1000.0, 'Montant HT': 1001.0}
    assert verifie_les_champs(facture) == False


def test_verifie_les_champs_montant_TTC_egal_montant_HT():
    facture = {'Montant TTC': 1000.0, 'Montant HT': 1000.0}
    assert verifie_les_champs(facture) == True


def test_verifie_les_champs_montant_TTC_et_montant_HT_negatif():
    facture = {'Montant TTC': -1001.0, 'Montant HT': -1000.0}
    assert verifie_les_champs(facture) == True


def test_demande_validation_accepte():
    facture = {'Nom': 'Etienne'}
    factures_refusees = []

    def refuse_facture(f):
        factures_refusees.append(f)

    resultat = demande_validation(facture, refuse_facture=refuse_facture, input=lambda _: 'o')
    assert resultat is True
    assert factures_refusees == []

    resultat = demande_validation(facture, refuse_facture=refuse_facture, input=lambda _: 'O')
    assert resultat is True
    assert factures_refusees == []

    resultat = demande_validation(facture, refuse_facture=refuse_facture, input=lambda _: 'p')
    assert resultat is False
    assert factures_refusees == []

    resultat = demande_validation(facture, refuse_facture=refuse_facture, input=lambda _: 'n')
    assert resultat is False
    assert factures_refusees == [facture]


def test_format_champs_format_narration_avec_mois_facturation_si_absente():
    facture = {
        'Date de dépôt': '2021-02-02',
        'Facture': 'any',
        'Montant TTC': '1.2',
        'Montant HT': '1.3',
        'Nom': 'nom',
        'Prénom': 'prénom'
    }
    format_champs(facture)
    assert facture['Narration'] == 'prénom 01_2021'


def test_format_champs_format_narration_si_prenom_absente():
    facture = {
        'Date de dépôt': '2021-02-02',
        'Facture': 'any',
        'Montant TTC': '1.2',
        'Montant HT': '1.3',
        'Nom': 'nom',
    }
    format_champs(facture)
    assert facture['Narration'] == '01_2021'


def test_format_champs():
    facture = {
        'Date de dépôt': '2021-02-02',
        'Facture': 'MAA/101466 - 81STEUT7-1',
        'Montant TTC': '1.3',
        'Montant HT': '1.2',
        'Narration': 'narration',
        'Nom': 'nom',
    }
    format_champs(facture)
    assert facture == {
        'Date de dépôt': date(2021, 2, 2),
        'Facture': 'MAA_101466-81STEUT7-1',
        'Montant HT': 1.2,
        'Montant TTC': 1.3,
        'Narration': 'narration',
        'Nom': 'nom',
    }


def test_format_champs_des_avoirs():
    facture = {
        'Date de dépôt': '2021-02-02',
        'Facture': 'MAA/101466 - 81STEUT7-1',
        'Montant TTC': '1.3',
        'Montant HT': '1.2',
        'Narration': 'narration',
        'Avoir?': "Oui"
    }
    format_champs(facture)
    assert facture == {
        'Date de dépôt': date(2021, 2, 2),
        'Facture': 'MAA_101466-81STEUT7-1',
        'Montant HT': -1.2,
        'Montant TTC': -1.3,
        'Narration': 'narration',
        'Avoir?': "Oui"
    }


def test_format_champs_des_avoirs_deja_negatif():
    facture = {
        'Date de dépôt': '2021-02-02',
        'Facture': 'MAA/101466 - 81STEUT7-1',
        'Montant TTC': '-1.3',
        'Montant HT': '-1.2',
        'Narration': 'narration',
        'Avoir?': "Oui"
    }
    format_champs(facture)
    assert facture == {
        'Date de dépôt': date(2021, 2, 2),
        'Facture': 'MAA_101466-81STEUT7-1',
        'Montant HT': -1.2,
        'Montant TTC': -1.3,
        'Narration': 'narration',
        'Avoir?': "Oui"
    }


def test_identification_facture_grist():
    timestamp_depot = 1712880000
    facture = {
        'grist_projet': 'annuaire',
        'Date_de_depot': timestamp_depot,
        'Nbr_de_jours': 10,
        'TJ': 500,
        'Frais_HT': 10,
        'Montant TTC': 6012,
        'Nom': 'Driss Ait Ali',
        'un message': "Et voici ma facture d'avril",
    }
    assert identification_facture_grist(facture) is True
    assert facture['Date de dépôt'] == '2024-04-12'
    assert facture['Montant HT'] == 5010
    assert facture['TVA calculée'] == 0.2
    assert facture['Nom technique'] == 'DrissAitAli'
