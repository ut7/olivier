## Installation

Installation python (3.11, peut-être plus) :
    > python3 -m venv venv
    > . ./venv/bin/activate
    > pip install -r requirements.txt

Initialisation du fichier d'environment pour les scripts :
Créer un fichier `.env` à la racine du projet avec un contenu adapté avec vos info personnelles :
(Permet aux plugins `direnv` ou `dotenv` de setter automatiquement un environnement quand on entre dans le répertoire)

    export REPERTOIRE_DOCUMENTS=<chemin vers le répertoire des documents>
    export GRIST_API_KEY=<Clé d'API GRIST récupérée sur le Grist>

    # commande permettant d'ouvrir un lien mailto avec l'application associée dans l'OS, 
    # par exemple `open` qui fonctionne sous mac et sous certaines distributions Linux
    export CMD_OUVERTURE_EMAIL=open
    # export WITH_DOCKER=no

    export VENV_DIR=venv

### Dépendences

/!\ Déprécié - mettre à jour la procédure (passe par un conteneur docker)

les scripts qui analysent les PDFs sont dépendants d'un outil système qui s'appelle `pdftohtml`. On utilise la version installée avec `poppler`.

> brew install poppler

### Tests

Pour lancer les tests unitaires des outils :

    > ptw

ou, pour lancer en mode watch les "webtest"
    > ptw -- -m webtest

## Toutes les commandes

Anita
    factures
        importer
