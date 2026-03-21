from cachetools import cached
from olivier.api_grist import recupere_tiers, recupere_tiers_du_contact


@cached(cache={})
def lit_tiers(recupere_tiers = recupere_tiers):
    resultat = {}
    for tiers in recupere_tiers():
        nomTechnique = tiers.Identifiant
        resultat[nomTechnique] = {}
        for field in tiers._fields:
            val = getattr(tiers, field)
            if len(str(val)) > 0:
                resultat[nomTechnique][field] = val
        resultat[nomTechnique]['projet'] = tiers.gristHelper_Display[1:]
        resultat[nomTechnique]['Emails'] = tiers.gristHelper_Display2[1:]
    return resultat


def tiers_du_contact(contact, recupere_tiers_du_contact = recupere_tiers_du_contact):
    dbTiers = recupere_tiers_du_contact(contact)
    if dbTiers:
        tiers = {}
        tiers['nom'] = dbTiers.nom
        if len(dbTiers.prenom) > 0:
            tiers['prenom'] = dbTiers.prenom
        tiers['projet'] = dbTiers.gristHelper_Display[1:]
        return tiers