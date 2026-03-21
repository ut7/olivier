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
    formate_date,
    nom_technique,
    print_rouge,
)
from olivier.api_grist import (
    recupere_donnees_grist_attachment,
    recupere_grist_attachment,
    recupere_tiers,
    refuse_facture_grist,
    noms_projets,
)
from olivier.tiers import tiers_du_contact, lit_tiers
from olivier.entrees_sorties import (
    affiche_champs,
    verifier_facture_non_recue,
    extrait_extention_piece,
)


CHAMPS_OBLIGATOIRES = [
    "Nom",
    "Facture",
    "Date de facture",
    "Montant HT",
    "Montant TTC",
    "Projet",
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


def demande_champs_manquants(facture,
                             input=lambda prompt: input(prompt),
                             noms_projets=noms_projets):
    for parametre in CHAMPS_OBLIGATOIRES:
        if parametre not in facture:
            facture[parametre] = input(f"Quel {parametre} ? ").strip()
    if facture["Projet"] in noms_projets() and "grist_projet" in facture:
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
    facture["Date de facture"] = extrait_date(facture["Date de facture"])
    facture["Facture"] = format_numero_facture(facture["Facture"])
    facture["Montant TTC"] = extrait_montant(facture["Montant TTC"])
    facture["Montant HT"] = extrait_montant(facture["Montant HT"])
    if "Avoir?" in facture and facture["Avoir?"] == "Oui":
        facture["Montant TTC"] = -abs(facture["Montant TTC"])
        facture["Montant HT"] = -abs(facture["Montant HT"])
    if "Narration" not in facture:
        facture["Narration"] = affiche_mois_facturation(facture["Date de facture"])
        if "Prénom" in facture and len(facture['Prénom']) > 0:
            facture["Narration"] = f'{facture["Prénom"]} {facture["Narration"]}'
    return True


def verifie_existance_tiers(
    facture, recupere_tiers=recupere_tiers, print=lambda message: print(message)
):
    if "Nom" not in facture:
        print("Le Nom est manquant, le contact n'a pas été reconnu")
        return False
    facture["Nom technique"] = nom_technique(facture["Nom"])
    nt = facture["Nom technique"]
    tiers = lit_tiers(recupere_tiers)
    if nt in tiers:
        facture["Nom"] = tiers[nt]["nom"]
        if "Projet" not in facture and len(tiers[nt]["projet"]) == 1:
            facture["Projet"] = tiers[nt]["projet"][0]
        return True
    print(f"Le tiers '{nt}' n'existe pas")
    print("Il faut le créer dans grist")
    print("et lui créer un compte dans accounts.beancount")
    return False


def verifie_les_champs(facture, print_rouge=print_rouge):
    if abs(facture["Montant TTC"]) < abs(facture["Montant HT"]):
        print_rouge("ERREUR, le montant TTC est inférieur au montant HT")
        return False
    return True


def identification_contact(
    facture, tiers_du_contact=tiers_du_contact, print=lambda message: print(message)
):
    if "Contact" not in facture:
        return True

    tiers = tiers_du_contact(facture["Contact"])
    if tiers:
        facture["Nom"] = tiers["nom"]
        if "prenom" in tiers:
            facture["Prénom"] = tiers["prenom"]
        if "Projet" not in facture and len(tiers["projet"]) == 1:
            facture["Projet"] = tiers["projet"][0]
        else:
            print("Ce tiers a plusieurs projets")
            print(f"Projets : {', '.join(tiers['projet'])}")
    return True


def identification_facture_grist(facture):
    if "grist_projet" not in facture:
        return True

    facture["Date de facture"] = formate_date(datetime.fromtimestamp(facture["Date"]))
    facture["Montant HT"] = facture["Nbr_de_jours"] * facture['TJ'] + facture["Frais_HT"]

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
    identification_contact,
    verifie_existance_tiers,
    demande_champs_manquants,
    format_champs,
    verifie_les_champs,
    accepte_facture,
]


FILTRES = FILTRES_FACTURE_RECUE + [verifier_facture_non_recue]
