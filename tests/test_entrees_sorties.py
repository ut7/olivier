import os
import unittest
import pathlib
import shutil
from datetime import datetime
from olivier.entrees_sorties import (
    FORMATEURS,
    format_montant,
    chemin_fichier_facture,
    cherche_piece_archivee,
    extrait_extention_piece,
    verifier_facture_non_recue,
)

ROOT_PATH = pathlib.Path(__file__).resolve().parent.parent


class TestEntreesSorties(unittest.TestCase):
    def setUp(self):
        os.environ["REPERTOIRE_DOCUMENTS"] = f'{ROOT_PATH}/test/documents_archives'
        shutil.rmtree(f'{ROOT_PATH}/test/documents_archives', True)
        os.makedirs(f'{ROOT_PATH}/test/documents_archives')

    def test_format_montant(self):
        assert format_montant(1.5) == "     1,50 €"
        assert format_montant(2345.67) == " 2 345,67 €"
        assert format_montant(12345.67) == "12 345,67 €"
        assert format_montant("1.5") == "     1,50 €"
        assert format_montant("1 000.5") == " 1 000,50 €"
        assert format_montant("1,5") == "     1,50 €"
        assert format_montant("1") == "     1,00 €"

    def test_format_champs_identification(self):
        assert FORMATEURS["Montant HT"](2345.67) == " 2 345,67 €"
        assert FORMATEURS["Montant TTC"](12345.67) == "[bold]12 345,67 €"
        assert FORMATEURS["TVA calculée"](0.1919) == "[bold]19,2%"

    def test_chemin_fichier_facture(self):
        facture = {
            'Mois de facturation': datetime(2021, 2, 28, 0, 0),
            'Facture': 'MAA_101466-81STEUT7-1',
            'Montant TTC': 1.2,
            'extension_fichier': '.pdf',
            'Narration': 'x' * 111,
            'Nom technique': 'Nom',
            'grist_projet': 'ProjetX',
        }
        assert chemin_fichier_facture(facture) == \
            f"{ROOT_PATH}/test/documents_archives/20210228-Nom-facture_MAA_101466-81STEUT7-1-ProjetX_{'x' * 110}-1.2.pdf"

    def test_chemin_fichier_facture_jpg(self):
        facture = {
            'Mois de facturation': datetime(2021, 2, 28, 0, 0),
            'Facture': 'MAA_101466-81STEUT7-1',
            'extension_fichier': '.jpg',
            'Montant TTC': 1.2,
            'Narration': 'narration',
            'Nom technique': 'Nom',
            'grist_projet': 'ProjetX',
        }
        assert chemin_fichier_facture(facture) == \
            f"{ROOT_PATH}/test/documents_archives/20210228-Nom-facture_MAA_101466-81STEUT7-1-ProjetX_narration-1.2.jpg"

    def test_verifier_facture_non_recue_non_recue(self):
        facture = {
            'Mois de facturation': datetime(2021, 2, 2, 0, 0),
            'Facture': 'MAA_101466-81STEUT7-1',
            'extension_fichier': '.pdf',
            'Montant TTC': 1.2,
            'Narration': 'narration',
            'Nom technique': 'Nom',
            'grist_projet': 'ProjetX',
        }
        assert verifier_facture_non_recue(facture) == True

    def test_verifier_facture_non_recue_deja_recue(self):
        facture = {
            'Mois de facturation': datetime(2021, 2, 28, 0, 0),
            'Facture': 'MAA_101466-81STEUT7-1',
            'extension_fichier': '.pdf',
            'Montant TTC': 1.2,
            'Narration': 'narration',
            'Nom technique': 'Nom',
            'grist_projet': 'ProjetX',
        }
        nom_fichier = chemin_fichier_facture(facture)
        with open(nom_fichier, 'w') as db:
            db.write('contenu quelconque')

        reponses = {'Cette facture a déjà été importée. Continuer ? (o/N)': 'n'}
        assert verifier_facture_non_recue(facture, lambda prompt: reponses[prompt]) == False

        reponses = {'Cette facture a déjà été importée. Continuer ? (o/N)': 'o'}
        assert verifier_facture_non_recue(facture, lambda prompt: reponses[prompt]) == True

    def test_cherche_piece_archivee(self):
        facture = {
            'Mois de facturation': datetime(2021, 2, 28, 0, 0),
            'Facture': 'MAA_101466-81STEUT7-1',
            'extension_fichier': '.pdf',
            'Montant TTC': 1.2,
            'Narration': 'narration',
            'Nom technique': 'Nom',
            'grist_projet': 'ProjetX',
        }
        nom_fichier = chemin_fichier_facture(facture)
        with open(nom_fichier, 'w') as db:
            db.write('contenu quelconque')
        assert cherche_piece_archivee({
            'Nom technique': facture['Nom technique'],
            'Montant TTC': facture['Montant TTC'],
            'Facture': facture['Facture'],
        }) == nom_fichier

    def test_cherche_piece_archivee_sans_tenir_compte_des_centimes(self):
        facture = {
            'Mois de facturation': datetime(2021, 2, 28, 0, 0),
            'Facture': 'MAA_101466-81STEUT7-1',
            'extension_fichier': '.pdf',
            'Montant TTC': 1,
            'Narration': 'narration',
            'Nom technique': 'Nom',
            'grist_projet': 'ProjetX',
        }
        nom_fichier = chemin_fichier_facture(facture)
        with open(nom_fichier, 'w') as db:
            db.write('contenu quelconque')
        assert cherche_piece_archivee({
            'Nom technique': facture['Nom technique'],
            'Montant TTC': 1.0,
            'Facture': facture['Facture'],
        }, lambda prompt: {}[prompt]) == nom_fichier

    def test_extrait_extention_piece(self):
        facture = {}
        extrait_extention_piece(facture, "fichier.extension")
        assert facture['extension_fichier'] == '.extension'
