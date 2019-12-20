# CSI AtlanteWI - Accesso organizzato a dati e geoservizi

CSI AtlanteWI è un plugin del software GIS 
[QGIS](https://qgis.org "QGIS - A Free and Open Source Geographic Information System") 
ed è l'evoluzione del plugin CSI Atlante ( https://github.com/SITA-RegionePiemonte/CSIAtlante ) sviluppato per la versione di QGIS 3.x

Pensato per un'organizzazione (enti pubblici, singoli dipartimenti/direzioni,...) 
dove gli amministratori del Sistema Informativo Territoriale (SIT)
guidano, attraverso un catalogo strutturato, gli utilizzatori finali di QGIS all'accesso 
ai dati vettoriali (PostGIS) e ai geoservizi (WMS) di riferimento.

Questa è la componente client per la gestione delle 
alberature di dati e servizi (Plugin Qgis 3.4)


Le differenze principali rispetto alla versione precedente sono le seguenti :

- interfaccia gestita in una Webview
- accesso tramite login personale
- integrazione con Drupal8 (Modulo Drupal)
- registrazione e cambio password autonoma
- gestione profilazione e privilegi
- gestione di progetti personali e di gruppo
- editing dati postgis


## Features:
* Presentazione di dati geografici
* Ricerca di dati geografici
* Tematizzazione dati geografici
* Profilazione per utenti e gruppi di utenti


# Getting Started
Per utilizzare correttamente quanto presente nel repository, è necessario impostare alcuni parametri:
- impostare correttamente la variabile *base_path* del **pb_tool-deploy.bat** alla cartella *bin* dell'installazione QGis 3.4 (e.g. *C:\Program Files\QGIS 3.4\bin*).
- impostare correttamente le variabili nel file **configuration.py** in funzione del proprio caso d'uso.
- in caso il server del componente Drupal utilizzi una connessione sicura, è necessario impostare le opportune variabili nei metodi del *modules/csi_certificate.py*,  richiesti per instaurare la socket SSL. I valori sono stringhe in *base64*:
    - nel metodo *get_certificate* impostare il certificato locale
	- nel metodo *get_key* impostare la private key

Per la compilazione ed installazione in locale viene utilizzato [pb_tool](http://g-sherman.github.io/plugin_build_tool/) configurato tramite il file *pb_tool.cfg*. Per comodità di sviluppo viene utilizzato lo script batch **pb_tool-deploy.bat** che prepara l'esecuzione per **pb_tool** e lo esegue, fornendo in caso un parametro in input. Di seguito alcuni esempi di comandi utilizzati.

Per compilare il plugin (i.e. i file di interfaccia grafica e le risorse):
> pb_tool-deploy.bat compile

Per compilare ed installare in locale il plugin:
> pb_tool-deploy.bat deploy

Per compilare ed installare in locale il plugin, sovrascrivendo in automatico il pre-esistente:
> pb_tool-deploy.bat deploy -y

Per modificare i files di interfaccia grafica *\*.ui* è necessario utilizzare ***QtCreator*** in quanto gli omonimi files *\*.py* verranno sovrascritti dalla compilazione.

# Prerequisites
Installing [QGIS 3.4](https://docs.qgis.org/3.4/en/docs/)

# Installing
[QGIS Lesson: Installing and Managing Plugins](docs.qgis.org/3.4/en/docs/training_manual/qgis_plugins/index.html#"QGIS Lesson: Installing and Managing Plugins")

# Contributing
Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests to us.

# Versioning
We use Semantic Versioning for versioning. (http://semver.org)

# Authors
See the list of contributors who participated inthis project in file Author.md 

# Copyrights
© Copyright: Regione Piemonte 2019




