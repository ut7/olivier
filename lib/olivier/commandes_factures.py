import typer

from olivier import factures_grist

app = typer.Typer()


@app.command()
def telecharger(mois: int):
    """
    Télécharge les factures grist pour un mois donné
    """
    factures_grist.telecharge("FranceConnect", mois)


@app.command()
def importer():
    """
    Importe toutes les factures grist en attente
    """
    print("Traitement des factures Grist")
    projet = "FranceConnect"
    factures_grist.traite(projet)
