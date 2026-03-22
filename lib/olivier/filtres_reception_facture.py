from datetime import datetime
import os
import subprocess
import tempfile
from rich import print
from olivier.outils import (
    extrait_montant,
    extrait_date,
    format_numero_facture,
    affiche_mois_facturation,
    nom_technique,
    formate_date,
    print_rouge,
)
from olivier.api_grist import (
    recupere_donnees_grist_attachment,
    recupere_grist_attachment,
    refuse_facture_grist,
)
from olivier.entrees_sorties import (
    affiche_champs,
    verifier_facture_non_recue,
    extrait_extention_piece,
)


CHAMPS_OBLIGATOIRES = [
    "Nom",
    "Facture",
    "Date de dépôt",
    "Montant HT",
    "Montant TTC",
]
CHAMPS_IDENTIFICATION = [
    "Nom technique",
    "un message",
    "Prénom",
    "TVA calculée",
    "Narration",
] + CHAMPS_OBLIGATOIRES


def affiche_champs_identification(facture):
    champs = {}

    for nom_champ in CHAMPS_IDENTIFICATION:
        if nom_champ in facture:
            champs[nom_champ] = facture[nom_champ]

    affiche_champs(champs)


def demande_champs_manquants(facture, input=lambda prompt: input(prompt)):
    for parametre in CHAMPS_OBLIGATOIRES:
        if parametre not in facture:
            facture[parametre] = input(f"Quel {parametre} ? ").strip()
    if "Nbr_de_jours" not in facture:
        facture["Nbr_de_jours"] = extrait_montant(input("Quel nombre de jours ? "))
    if "Frais_HT" not in facture:
        total_frais = 0
        while True:
            frais = input("Quel frais HT ([Entrer] pour finir) ? ")
            if frais == "":
                break
            total_frais += extrait_montant(frais)
        facture["Frais_HT"] = total_frais

    return True


def refuse_facture(facture):
    raison = input("Refusée pour quelle raison ? ")
    refuse_facture_grist(facture["grist_projet"], facture, raison)


def demande_validation(facture, refuse_facture=refuse_facture, input=input):
    print("Est-ce que cette facture est acceptée ?")
    print("o : [underline]o[/]ui")
    print("n : [underline]n[/]on")
    print("p : [underline]p[/]lus tard (defaut)")
    validation = input("réponse : ").lower()
    if validation == "n":
        refuse_facture(facture)

    return validation == "o"


def accepte_facture(facture):
    if "fichier_temporaire" not in facture:
        return True

    fp = facture["fichier_temporaire"]
    subprocess.run(["open", fp.name])
    affiche_champs_identification(facture)
    print("✅ Penser à vérifier la période d'activité !")
    print_rouge(":white_check_mark: Penser à vérifier que c'est le bon tier qui est selectionné !")
    if "Erreurs" in facture and len(facture["Erreurs"]) > 0:
        print_rouge(
            f"Attention, le formulaire contient les erreurs suivantes : {facture['Erreurs']}"
        )
    est_validee = demande_validation(facture)
    if not est_validee:
        os.unlink(fp.name)

    return est_validee


def format_champs(facture):
    facture["Date de dépôt"] = extrait_date(facture["Date de dépôt"])
    facture["Facture"] = format_numero_facture(facture["Facture"])
    facture["Montant TTC"] = extrait_montant(facture["Montant TTC"])
    facture["Montant HT"] = extrait_montant(facture["Montant HT"])
    if "Avoir?" in facture and facture["Avoir?"] == "Oui":
        facture["Montant TTC"] = -abs(facture["Montant TTC"])
        facture["Montant HT"] = -abs(facture["Montant HT"])
    if "Narration" not in facture:
        facture["Narration"] = affiche_mois_facturation(facture["Date de dépôt"])
        if "Prénom" in facture and len(facture['Prénom']) > 0:
            facture["Narration"] = f'{facture["Prénom"]} {facture["Narration"]}'
    return True


def verifie_les_champs(facture, print_rouge=print_rouge):
    if abs(facture["Montant TTC"]) < abs(facture["Montant HT"]):
        print_rouge("ERREUR, le montant TTC est inférieur au montant HT")
        return False
    return True


def identification_facture_grist(facture):
    if "grist_projet" not in facture:
        return True

    facture["Date de dépôt"] = formate_date(datetime.fromtimestamp(facture["Date_de_depot"]))
    facture["Montant HT"] = facture["Nbr_de_jours"] * facture['TJ'] + facture["Frais_HT"]
    facture["Nom technique"] = nom_technique(facture["Nom"])

    if facture["Montant HT"] == 0:
        facture["TVA calculée"] = facture["Montant TTC"]
    else:
        facture["TVA calculée"] = (
            facture["Montant TTC"] - facture["Montant HT"]
        ) / facture["Montant HT"]
    return True


def telecharge_piece(facture, nom_fichier, telechargeur):
    extrait_extention_piece(facture, nom_fichier)
    fp = tempfile.NamedTemporaryFile(suffix=facture["extension_fichier"], delete=False)
    facture["fichier_temporaire"] = fp
    print(f"nom fichier facture : {fp.name}")
    fp.write(telechargeur().content)
    fp.close()


def extraction_pdf_facture_grist(facture):
    if "grist_projet" not in facture:
        return True

    facture_id = facture["PDF_Facture"][1]
    info_attachment = recupere_donnees_grist_attachment(
        facture["grist_projet"], facture_id
    )
    telecharge_piece(
        facture,
        info_attachment["fileName"],
        lambda: recupere_grist_attachment(facture["grist_projet"], facture_id),
    )
    return True


FILTRES_FACTURE_RECUE = [
    identification_facture_grist,
    extraction_pdf_facture_grist,
    demande_champs_manquants,
    format_champs,
    verifie_les_champs,
    accepte_facture,
]


FILTRES = FILTRES_FACTURE_RECUE + [verifier_facture_non_recue]
