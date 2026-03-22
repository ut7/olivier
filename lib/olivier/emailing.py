import os
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlunparse, ParseResult, urlencode, quote

from olivier.outils import affiche_mois_facturation


PORT = 465  # For SSL
SMTP_SERVER = "smtp.gmail.com"
GERANCE_EMAIL = "gerance@ut7.fr"


def construit_message(facture):
    contact = facture['Contact']
    prenom = facture['Nom']
    numero_facture = facture['Facture']
    mois = affiche_mois_facturation(facture['Date de dépôt'], '%B')
    message = f"""Bonjour {prenom},

Nous avons bien reçu ta facture {numero_facture} pour {mois} et nous l'avons inscrite dans nos comptes.

Merci beaucoup,
/ut7
"""
    msg = EmailMessage()
    msg.set_content(message)
    msg['Subject'] = f'La facture No {numero_facture}, pour {mois}, a été reçue et traitée par /ut7'
    msg['To'] = ', '.join([contact, GERANCE_EMAIL])
    msg['From'] = GERANCE_EMAIL  # le champ est ignoré mais exigé par l'API
    return msg


def email_confirmation_reception(facture):
    if 'Contact' not in facture:
        return

    message = construit_message(facture)
    url_mailto = construire_url_mailto(message)
    print(url_mailto)
    if 'CMD_OUVERTURE_EMAIL' in os.environ:
        os.system(f"{os.environ['CMD_OUVERTURE_EMAIL']} \"{url_mailto}\"")


def construire_url_mailto(message):
    return urlunparse(ParseResult(
        scheme='mailto',
        netloc='',
        path=quote(message['To']),
        params='',
        query=urlencode({
            'subject': message['Subject'],
            'body': message.get_content(),
        }, quote_via=quote),
        fragment=''))
