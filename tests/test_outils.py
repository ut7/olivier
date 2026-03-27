from datetime import datetime, date
from olivier.outils import (
    converti_date,
    extrait_montant,
    extrait_date,
    format_numero_facture,
    affiche_mois_facturation,
    print_rouge,
)
from olivier.outils import nom_technique, filtre_caracteres_nom_fichier
from olivier.outils import date_pour_le_mois, timestamp_utc


def test_extrait_montant():
    assert extrait_montant("1 000,23") == 1000.23
    assert extrait_montant("1 000,23 euro") == 1000.23
    assert extrait_montant("1,000.23 euro") == 1000.23
    assert extrait_montant("1.000,23 euro") == 1000.23
    assert extrait_montant("1000.23 euro") == 1000.23
    assert extrait_montant(1000.23) == 1000.23


def test_extrait_montant_negatif():
    assert extrait_montant("-1 000,23") == -1000.23


def test_extrait_date():
    assert extrait_date("2021-01-02") == date(2021, 1, 2)
    assert extrait_date("20210102") == date(2021, 1, 2)


def test_converti_date():
    assert converti_date("01/08/2023", "fr") == "2023-08-01"
    assert converti_date("31 juil. 2023", "fr") == "2023-07-31"
    assert converti_date("01 sept. 2025", "fr") == "2025-09-01"
    assert converti_date("11 August, 2023", "en") == "2023-08-11"
    assert (
        converti_date("2024-07-19", "fr")
        == "date 2024-07-19 non parsable pour la langue fr"
    )


def test_affiche_mois_facturation():
    assert (
        affiche_mois_facturation(
            datetime(2020, 2, 29), facturation_ouverte=lambda _: True
        )
        == "02_2020"
    )
    assert (
        affiche_mois_facturation(
            datetime(2020, 3, 3), facturation_ouverte=lambda _: True
        )
        == "02_2020"
    )
    assert (
        affiche_mois_facturation(
            datetime(2020, 3, 9), facturation_ouverte=lambda _: True
        )
        == "02_2020"
    )
    assert (
        affiche_mois_facturation(
            datetime(2020, 3, 10), facturation_ouverte=lambda _: True
        )
        == "03_2020"
    )
    assert (
        affiche_mois_facturation(
            datetime(2021, 1, 1), facturation_ouverte=lambda _: True
        )
        == "12_2020"
    )
    assert (
        affiche_mois_facturation(
            datetime(2021, 1, 1), facturation_ouverte=lambda _: False
        )
        == "01_2021"
    )
    assert (
        affiche_mois_facturation(
            datetime(2020, 2, 29), facturation_ouverte=lambda _: False
        )
        == "03_2020"
    )


def test_nom_technique():
    assert nom_technique("Ad-Hoc Lab") == "AdHocLab"
    assert nom_technique("scopyleft") == "Scopyleft"
    assert nom_technique("Mélodie Dahi") == "MelodieDahi"
    assert nom_technique("L'échappée Belle") == "LEchappeeBelle"
    assert nom_technique("Toto S.à.r.l.") == "TotoSARL"
    assert nom_technique("IT-era") == "ItEra"
    assert nom_technique("Ppg*Ecoperl France") == "PpgEcoperlFrance"
    assert nom_technique("Whimsical, Inc.") == "WhimsicalInc"
    assert nom_technique("Front/Side") == "FrontSide"
    assert nom_technique("Mettler V&Saveu") == "MettlerVSaveu"
    assert nom_technique("VI(E)NS") == "ViENs"


def test_format_numero_facture():
    assert format_numero_facture("MAA/101466 - 81STEUT7-1") == "MAA_101466-81STEUT7-1"
    assert format_numero_facture("23°-03-4") == "23-03-4"
    assert format_numero_facture("FACTURE N° 23-03-4") == "23-03-4"
    assert format_numero_facture("facture n° 23-03-4") == "23-03-4"
    assert format_numero_facture("n° 23-03-4") == "23-03-4"
    assert format_numero_facture("facture 23-03-4") == "23-03-4"
    assert format_numero_facture("FA0010086∙UT7-PAVIE") == "FA0010086_UT7-PAVIE"


def test_filtre_caracteres_nom_fichier():
    assert filtre_caracteres_nom_fichier("mot") == "mot"
    assert (
        filtre_caracteres_nom_fichier("une phrase de plusieurs mots")
        == "une_phrase_de_plusieurs_mots"
    )
    assert filtre_caracteres_nom_fichier("Drum:Covidoudou") == "Drum_Covidoudou"
    assert filtre_caracteres_nom_fichier("12/09") == "12_09"
    assert (
        filtre_caracteres_nom_fichier("Septembre, changement de forfait")
        == "Septembre__changement_de_forfait"
    )
    assert (
        filtre_caracteres_nom_fichier("Licence d'un Page Builder")
        == "Licence_d_un_Page_Builder"
    )
    assert filtre_caracteres_nom_fichier("billet 1 ; billet 2") == "billet_1___billet_2"


def test_date_pour_le_mois():
    aujourd_hui = datetime(2026, 3, 27)
    assert date_pour_le_mois(3, aujourd_hui) == datetime(2026, 3, 31)  # mois en cours
    assert date_pour_le_mois(2, aujourd_hui) == datetime(2026, 2, 28)  # mois passé même année
    assert date_pour_le_mois(12, aujourd_hui) == datetime(2025, 12, 31)  # mois futur → année précédente
    assert date_pour_le_mois(1, aujourd_hui) == datetime(2026, 1, 31)  # janvier même année


def test_timestamp_utc():
    assert timestamp_utc(datetime(2026, 3, 31)) == 1774915200
    assert timestamp_utc(datetime(2026, 2, 28)) == 1772236800


def test_print_rouge():
    print_rouge("message rouge")
    print("message non rouge")
