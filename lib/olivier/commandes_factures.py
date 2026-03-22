import typer

from olivier import traite_factures_grist

app = typer.Typer()


@app.command()
def importer():
    """
    Importe toutes les factures grist en attente
    """
    print("Traitement des factures Grist")
    traite_factures_grist.main()
