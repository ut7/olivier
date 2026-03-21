import os
import glob
from rich.console import Console
from rich.table import Table
from olivier.outils import (
    extrait_date,
    filtre_caracteres_nom_fichier,
    affiche_mois_facturation
)


def format_montant(v):
    if isinstance(v, str):
        v = float(v.replace(",", "."))
    formatted = f"{v:,.2f} €".replace(",", " ")
    entier, decimales = formatted.split(".", 1)
    return f"{entier.rjust(6)},{decimales}"


def gras(v):
    return f"[bold]{v}"


FORMATEURS = {
    "Nom": gras,
    "Date de facture": str,
    "Montant HT": format_montant,
    "Montant TTC": lambda v: gras(format_montant(v)),
    "un message": gras,
    "TVA calculée": lambda v: f"[bold]{v:.1%}".replace(".", ","),
}


def extrait_extention_piece(facture, nom_fichier):
    _, extension = os.path.splitext(nom_fichier)
    facture['extension_fichier'] = extension


def affiche_champs(champs):
    table = Table(title="✅ Attributs de la facture ✅")
    table.add_column("Nom", style="cyan", no_wrap=True)
    table.add_column("Valeur", style="green")

    for nom, valeur in champs.items():
        table.add_row(nom, FORMATEURS.get(nom, str)(valeur))

    console = Console()
    console.print(table)


def document_archives():
    return f'{os.environ["PARTAGE_UT7"]}/documents_archives'


def chemin_fichier_facture(facture):
    repertoire = document_archives()
    date = facture['Date de facture'].strftime("%Y%m%d")
    nom = facture['Nom technique']
    extension = facture['extension_fichier'] if 'extension_fichier' in facture else ''
    numero_facture = facture['Facture']
    montant_ttc = facture['Montant TTC']
    narration = filtre_caracteres_nom_fichier(facture['Narration'])[:110]
    projet = filtre_caracteres_nom_fichier(facture['Projet'])
    return f'{repertoire}/{date}-{nom}-facture_{numero_facture}-{projet}_{narration}-{montant_ttc}{extension}'


def range_fichier(src, dest):
    print(f'déplace le fichier\n{src}\nvers\n{dest}')
    os.rename(src, dest)


def verifier_facture_non_recue(facture, input=lambda prompt: input(prompt)):
    fichier_existe = os.path.exists(chemin_fichier_facture(facture))
    reponse = 'n'
    if fichier_existe:
        reponse = input('Cette facture a déjà été importée. Continuer ? (o/N)')
    return reponse == 'o' or not fichier_existe


def cherche_piece_archivee(facture, input=lambda prompt: input(prompt)):
    facture['extension_fichier'] = '.pdf'
    while True:
        repertoire = document_archives()
        nom=facture['Nom technique']
        numero_facture=facture['Facture']
        montant_ttc=int(facture['Montant TTC'])
        masque_fichier = f'{repertoire}/*-{nom}-facture_{numero_facture}-*-{montant_ttc}*'
        files=glob.glob(masque_fichier)
        if len(files) == 1:
            return files[0]
        elif len(files) > 1:
            print("J'ai trouvé plusieurs factures")
            print(files)
            exit(1)
        print(f'Aucun fichier trouvé pour le masque {masque_fichier}')
        reponse = input(f'Ré-essayer ? o/N')
        if reponse.lower() != 'o':
            return
