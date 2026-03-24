## Installation

Initialisation du fichier d'environnement pour les scripts :
Créer un fichier `.env` à la racine du projet avec un contenu adapté avec vos info personnelles :
(Permet aux plugins `direnv` ou `dotenv` de setter automatiquement un environnement quand on entre dans le répertoire)

    export REPERTOIRE_DOCUMENTS=<chemin vers le répertoire des documents>
    export GRIST_API_KEY=<Clé d'API GRIST récupérée sur le Grist>

    # commande permettant d'ouvrir un lien mailto avec l'application associée dans l'OS, 
    # par exemple `open` qui fonctionne sous mac et sous certaines distributions Linux
    export CMD_OUVERTURE_EMAIL=open

## Exécution

    $> . ./.env
    $> . ./venv/bin/activate
    $> olivier factures importer


## Toutes les commandes

olivier
    factures
        importer

## Aides

    $> olivier --help
    $> olivier factures --help
    $> olivier factures importer --help
