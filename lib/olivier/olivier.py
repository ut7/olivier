import typer

from olivier import commandes_factures

app = typer.Typer()


@app.callback()
def callback():
    """
    Olivier l'outil
    """


app.add_typer(commandes_factures.app, name="factures", help="réception et paiement des factures")
