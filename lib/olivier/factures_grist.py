from olivier.outils import (
    dernier_jour_mois_facturation,
    date_pour_le_mois,
    print_rouge
)
from olivier.api_grist import (
    actualise_budget_grist,
    factures_non_traitees,
    factures,
    marque_traitee,
)
from olivier.entrees_sorties import chemin_fichier_facture, range_fichier
from olivier.emailing import email_confirmation_reception

from olivier.filtres_reception_facture import (
    FILTRES,
    FILTRES_TELECHARGEMENT,
)


def traite(projet):
    for facture in factures_non_traitees(projet):
        facture["grist_projet"] = projet
        print(facture)
        if all(filtre(facture) for filtre in FILTRES):
            destination = chemin_fichier_facture(facture)
            range_fichier(facture["fichier_temporaire"].name, destination)

            marque_traitee(facture)

            mois_facturation = dernier_jour_mois_facturation(
                facture["Date de dépôt"]
            )
            try:
                actualise_budget_grist(projet, facture, mois_facturation)
            except ValueError:
                mois_facturation = mois_facturation.replace(day=1)
                try:
                    actualise_budget_grist(projet, facture, mois_facturation)
                except ValueError as e:
                    print_rouge(e)

            email_confirmation_reception(facture)


def telecharge(projet, mois):
    mois_facturation = date_pour_le_mois(mois)
    for facture in factures(projet, mois_facturation):
        facture["grist_projet"] = projet
        if all(filtre(facture) for filtre in FILTRES_TELECHARGEMENT):
            destination = chemin_fichier_facture(facture)
            range_fichier(facture["fichier_temporaire"].name, destination)
