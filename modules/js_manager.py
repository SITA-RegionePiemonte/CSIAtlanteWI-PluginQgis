# -*- coding: utf-8 -*-


"""
/*******************************************
Copyright: Regione Piemonte 2012-2019
SPDX-Licene-Identifier: GPL-2.0-or-later
*******************************************/

/***************************************************************************
CSIAtlanteWI
Accesso organizzato a dati e geoservizi
A QGIS plugin, designed for an organization where the Administrators of the
Geographic Information System want to guide end users
in organized access to the data and geo-services of their interest.
Date : 2019-11-16
copyright : (C) 2012-2019 by Regione Piemonte
author : Enzo Ciarmoli(CSI Piemonte), Luca Guida(Genegis), Matteo Tranquillini(Trilogis), Stefano Giorgi (CSI Piemonte) 
email : supporto.gis@csi.it
Note:
The content of this file is based on
- DB Manager by Giuseppe Sucameli <brush.tyler@gmail.com> (GPLv2 license)
- PG_Manager by Martin Dobias <wonder.sk@gmail.com> (GPLv2 license)
***************************************************************************/

/***************************************************************************
* *
* This program is free software; you can redistribute it and/or modify *
* it under the terms of the GNU General Public License as published by *
* the Free Software Foundation; either version 2 of the License, or *
* (at your option) any later version. *
* *
***************************************************************************/
"""

import os
import codecs
from PyQt5.QtCore import QFileInfo
from qgis.PyQt import QtCore
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import qApp, QMessageBox, QFileDialog
from qgis.PyQt.QtCore import QUrl, QEventLoop
from qgis.PyQt import QtNetwork
from qgis.core import Qgis, QgsDataSourceUri, QgsRasterLayer, QgsProject, QgsVectorLayer, QgsApplication

from . import csi_utils
from .. import configuration
from .csi_web_view import CsiWebView
from .csi_atlante_wi_metadata import DialogMetadata


class JsManager(QtCore.QObject):
    """
        Interested to manage the interactions with the AtlanteWI Javascript functions.
    """

    def __init__(self, web_view, background_color):
        """
            Initialize the Javascript manager with the webview widget.
            :param web_view: The webview instance
            :type web_view: CsiWebView
            :param background_color: The color to use for the background
            :type background_color: str
        """
        super(JsManager, self).__init__()
        self.web_view = web_view
        self.download_folder_path = ""
        self.session_password = ""
        self.session_user = ""
        self.load_configuration()
        self.dialog_metadata = None
        self.background_color = background_color

    def show_message(self, title, message):
        """
            Showing a message box.
            :param title: The message box title
            :type title: str
            :param message: The message box message
            :type message: str
        """
        QMessageBox.information(None, title, message)

    @QtCore.pyqtSlot(str, str)
    def showMessageJS(self, title, message):
        """
            # Slot for exposing the same-name function to Javascript. #
            Wrap to function for showing the message box.
            :param title: The message box title
            :type title: str
            :param message: The message box message
            :type message: str
        """
        self.show_message(title, message)

    @QtCore.pyqtSlot(result=str)
    def getColorBG(self):
        """
            # Slot for exposing the same-name function to Javascript. #
            Return the background color.
            :return: The background color
            :rtype: str
        """
        return self.background_color

    @QtCore.pyqtSlot(str, result=str)
    def askConfirm(self, message):
        """
            # Slot for exposing the same-name function to Javascript. #
            Return the user choice: "OK" for positive, "KO" for negative response.
            :return: The user choice
            :rtype: str
        """
        reply = QMessageBox.question(None, 'Attenzione',
                                     message,
                                     QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            return "OK"
        else:
            return "NO"

    @QtCore.pyqtSlot(str, str)
    def download_and_open_qgis_project(self, project_file_str, nome_file):
        """
            # Slot for exposing the same-name function to Javascript. #
            Save the given project to the filesystem and open it in QGis.
            The recognition of *.qgs and *.qgz is carried out checking the string content.
            :param project_file_str: The project file which could be either a *.qgs or *.qgz UTF-8 encoded string
            :type project_file_str: str
            :param nome_file: The file name
            :type nome_file: str
        """

        if not self.check_download_folder():
            return False

        destination_path = os.path.join(self.download_folder_path, nome_file)

        # In case the file is a *.qgs (which is a XML file) is expected to start with either "DOCTYPE" (which should
        # have been removed during the upload, though) or "<QGIS"
        lowered = project_file_str.lower()
        if lowered.startswith("<!doctype") or lowered.startswith("<qgis"):
            destination_path = destination_path + ".qgs"
            try:
                with codecs.open(destination_path, "w", "utf-8") as f:
                    f.write(project_file_str)
            except Exception as e:
                QMessageBox.critical(None,
                                     "Errore scaricamento",
                                     "Non e' stato possibile salvare in locale il file di progetto " + nome_file +
                                     ".qgs")
                raise
        # In case it is a zip file, it is expected to start with "PK"
        elif lowered.startswith("pk"):
            destination_path = destination_path + ".qgz"
            try:
                # Generating the byte array (explicitly using the default utf-8 anyway)
                tmp_encoded = codecs.encode(project_file_str, encoding="utf-8")
                # Decoding from "UTF-8" to a byte array
                project_file_str = codecs.decode(tmp_encoded, encoding="utf-8")
                # The user base is using Windows OS. The *.zip archive are ANSI encoded by empirical observation
                project_file_bytes = codecs.encode(project_file_str, encoding="ansi")
                with codecs.open(destination_path, 'wb') as f:
                    f.write(project_file_bytes)
            except Exception as e:
                QMessageBox.critical(None,
                                     "Errore scaricamento",
                                     "Non e' stato possibile salvare in locale il file di progetto " + nome_file +
                                     ".qgz")
                raise
        else:
            QMessageBox.critical(None,
                                 "Errore scaricamento",
                                 "Non e' stato possibile salvare in locale il file di progetto " + nome_file +
                                 "\n\nNon e' stato possibile individuare il tipo di file dal suo contenuto")
            raise Exception("Non e' stato possibile individuare il tipo di file dal suo contenuto")

        print("chiude progetto corrente")
        QgsProject.instance().clear()
        qApp.processEvents() #Wait untill  GUI Update

        print("apre progetto " + destination_path)
        QgsProject.instance().read(destination_path)

    @QtCore.pyqtSlot(str)
    def erroreApriQgsFile(self, error_message):
        """
            # Slot for exposing the same-name function to Javascript. #
            Show error message to the user.
            :param error_message: The error message to show to the user
            :type error_message: str
        """
        print(error_message)
        self.show_message("Attenzione!", "Impossibile aprire il progetto\n" + error_message)

    @QtCore.pyqtSlot(str, str)
    def setCredenzialiUtente(self, user, password):
        """
            # Slot for exposing the same-name function to Javascript. #
            Set the user credentials to the QGis settings, if changed.
            Then execute the Javascript submit.
            :param user: The user name
            :type user: str
            :param password: The password
            :type password: str
        """
        self.session_password = password
        self.session_user = user

        # Prompt the user for storing the credential in case they differs from the previous configured
        old_password = csi_utils.get_qgs_settings_value_or_default("CSIAtlanteWI/password", default="", value_type=str)
        old_user = csi_utils.get_qgs_settings_value_or_default("CSIAtlanteWI/user", default="", value_type=str)
        if password != old_password or user != old_user:
            user_reply = QMessageBox.question(None, 'Salvare la password?',
                                              'Si desidera salvare la password per accedere in automatico al plugin?',
                                              QMessageBox.Yes, QMessageBox.No)
            if user_reply == QMessageBox.Yes:
                csi_utils.set_qgs_settings_value("CSIAtlanteWI/password", password)
                csi_utils.set_qgs_settings_value("CSIAtlanteWI/user", user)

        # Invoke
        js_script = "submitUser('', false, 'INFO');"
        self.web_view.page().mainFrame().evaluateJavaScript(js_script)

    @QtCore.pyqtSlot(str)
    def setPasswordSessioneUtente(self, password):
        """
            # Slot for exposing the same-name function to Javascript. #
            Set the session user password.
            :param password: The password
            :type password: str
        """
        self.session_password = password

    @QtCore.pyqtSlot(str)
    def setUserSessioneUtente(self, user):
        """
            # Slot for exposing the same-name function to Javascript. #
            Set the session user.
            :param user: The user
            :type user: str
        """
        # csi_utils.set_qgs_settings_value("CSIAtlanteWI/user", user)
        self.session_user = user

    @QtCore.pyqtSlot()
    def getPassword(self):
        """
            # Slot for exposing the same-name function to Javascript. #
            Retrieve the password from settings and execut Javascript code to set in that scope.
        """
        password = csi_utils.get_qgs_settings_value_or_default("CSIAtlanteWI/password", default="", value_type=str)
        # Executing Javascript for storing the password
        js_script = "setPassword('{0}', false, 'INFO');".format(password)
        self.web_view.page().mainFrame().evaluateJavaScript(js_script)

    @QtCore.pyqtSlot()
    def getUser(self):
        """
            # Slot for exposing the same-name function to Javascript. #
            Retrieve the user from settings and execute Javascript code to set in that scope.
        """
        user = csi_utils.get_qgs_settings_value_or_default("CSIAtlanteWI/user", default="", value_type=str)
        # Executing Javascript for storing the user
        js_script = "setUser('{0}', false, 'INFO');".format(user)
        self.web_view.page().mainFrame().evaluateJavaScript(js_script)

    @QtCore.pyqtSlot(str)
    def openUrlInBrowser(self, url):
        """
            # Slot for exposing the same-name function to Javascript. #
            Open the given URL in a browser.
        """
        import webbrowser
        webbrowser.open(url)

    @QtCore.pyqtSlot(str, str)
    def showMetadataDialog(self, layer_name, url_metadata):
        """
            # Slot for exposing the same-name function to Javascript. #
            Show the metadata dialog with the given parameters.
            :param layer_name: The layer name
            :type layer_name: str
            :param url_metadata: The URL for the metadata to show
            :type url_metadata: str
        """
        if self.dialog_metadata is None:
            self.dialog_metadata = DialogMetadata()

        self.dialog_metadata.set_title(layer_name)
        self.dialog_metadata.set_url(url_metadata)

        qgs_logger = QgsApplication.messageLog()
        qgs_logger.logMessage('showMetadataDialog: {} {}'.format(layer_name, url_metadata),
                              tag=configuration.LOGGER_TAG, level=Qgis.Info)
        self.dialog_metadata.exec()

    @QtCore.pyqtSlot(str, str)
    def showMetadata(self, layer_name, url_metadata):
        """
            # Slot for exposing the same-name function to Javascript. #
            Open the given URL in a browser.
            :param layer_name: The layer name
            :type layer_name: str
            :param url_metadata: The URL for the metadata to show
            :type url_metadata: str
        """
        qgs_logger = QgsApplication.messageLog()
        qgs_logger.logMessage('showMetadata: {} {}'.format(layer_name, url_metadata),
                              tag=configuration.LOGGER_TAG, level=Qgis.Info)
        QDesktopServices.openUrl(QUrl(url_metadata))

    @QtCore.pyqtSlot(result=str)
    def getCartellaScaricoPacchetti(self):
        """
            # Slot for exposing the same-name function to Javascript. #
            Retrieve the download folder name.
            :return: The download folder name
            :rtype: str
        """
        if self.download_folder_path is None or self.download_folder_path == "":
            return "-- non selezionata --"

        return self.download_folder_path

    @QtCore.pyqtSlot()
    def selezionaCartellaScarico(self):
        """
            # Slot for exposing the same-name function to Javascript. #
            Activate the chooser for the download folder name.
        """
        # If already defined, prompt the user for the change
        if self.download_folder_path != "":
            reply = QMessageBox.question(None,
                                         'Cartella di scarico',
                                         'Cartella di scarico attuale: ' + self.download_folder_path +
                                         '\nSi desidera modificarla?',
                                         QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        # Prompt the file chooser
        self.download_folder_path = QFileDialog.getExistingDirectory(None)
        self.set_download_folder()
        self.save_configuration()

    @QtCore.pyqtSlot(str, str, str, str, str, str)
    def addWms(self, wms_name, url, layers, mime_type, epsg_code, protocol):
        """
            # Slot for exposing the same-name function to Javascript. #
            Adding the WMS to the QGis TOC.
            :param wms_name: The WMS name to add in TOC as group
            :type wms_name: str
            :param url: The WMS URL
            :type url: str
            :param layers: The list of the WMS layers to add
            :type layers: list of str
            :param mime_type: The image MIME TYPE (e.g. image/png)
            :type mime_type: str
            :param epsg_code: The EPSG code (e.g. the number 32632)
            :type epsg_code: int
            :param protocol: The protocol (i.e. should be 'ba' for applying basic authentication). Not yet managed.
            :type protocol: str
        """
        qgs_logger = QgsApplication.messageLog()
        qgs_logger.logMessage('addWms: wms_name = {}'.format(wms_name), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: url = {}'.format(url), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: layers = {}'.format(layers), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: mime_type = {}'.format(mime_type), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: epsg_code = {}'.format(epsg_code), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: protocol = {}'.format(protocol), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)

        # For storing the URI data
        uri = QgsDataSourceUri()

        # Split the host with the request data
        pieces = url.split("?")
        if len(pieces) == 1:
            qgs_logger.logMessage('len(pieces) == 1', tag=configuration.LOGGER_TAG, level=Qgis.Info)
        elif len(pieces) == 2:
            qgs_logger.logMessage('len(pieces) == 2', tag=configuration.LOGGER_TAG, level=Qgis.Info)
            # Overriding the URL
            url = "{}{}".format(pieces[0], "?")
            parameters_values = pieces[1].split("=")
            if len(parameters_values) == 2:
                qgs_logger.logMessage('len(parameters) == 2', tag=configuration.LOGGER_TAG, level=Qgis.Info)
                uri.setParam(parameters_values[0], parameters_values[1])
                qgs_logger.logMessage('uri.param({}): {}'.format(parameters_values[0], uri.param(parameters_values[0])),
                                      tag=configuration.LOGGER_TAG, level=Qgis.Info)
            else:
                qgs_logger.logMessage('len(p) != 2', tag=configuration.LOGGER_TAG, level=Qgis.Info)
        else:
            qgs_logger.logMessage('len(pieces) > 2 Not yet managed!', tag=configuration.LOGGER_TAG, level=Qgis.Warning)

        # Setting the URL to the URI
        uri.setParam("url", url)

        # Process the layers accordingly if just an element or a list of elements
        layers_list = []
        if "," in layers:
            layers_list = layers.split(",")
        else:
            layers_list.append(layers)

        # Setting the parameter 'layers' in the URI
        for val in layers_list:
            uri.setParam("layers", val)

        # Setting the other parameters
        # Styles seems required: https://gis.stackexchange.com/questions/183485/load-wms-with-pyqgis
        uri.setParam("styles", "")
        uri.setParam("format", mime_type)
        uri.setParam("crs", "EPSG:{}".format(epsg_code))

        # https://docs.qgis.org/3.4/en/docs/pyqgis_developer_cookbook/loadlayer.html#raster-layers
        # Ignore GetCoverage URL advertised by GetCapabilities. May be necessary if a server is not configured properly.
        uri.setParam("IgnoreGetMapUrl", "1")

        # Adding the parameters for the basic authentication
        qgs_logger.logMessage('Applying Basic-Authentication', tag=configuration.LOGGER_TAG, level=Qgis.Info)
        uri.setParam("username", self.session_user)
        uri.setParam("password", self.session_password)

        # Logging the parameters for debugging
        qgs_logger.logMessage('uri.param(url): {}'.format(uri.param("url")), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('uri.param(layers): {}'.format(uri.param("layers")), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('uri.param(format): {}'.format(uri.param("format")), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('uri.param(crs): {}'.format(uri.param("crs")), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('uri.service(): {}'.format(uri.service()), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('encodedUri: {}'.format(str(uri.encodedUri())), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('uri.uri(): {}'.format(uri.uri()), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)

        # Generating the WMS layer
        wms_layer = QgsRasterLayer(str(uri.encodedUri()), wms_name, 'wms')

        # If the WMS is correctly generated, add to the QGis TOC
        if wms_layer.isValid():
            QgsProject.instance().addMapLayer(wms_layer)
        else:
            qgs_logger.logMessage('Impossibile aggiungere il WMS: {}'.format(wms_name), tag=configuration.LOGGER_TAG,
                                  level=Qgis.Warning)
            self.show_message("Attenzione!", "Impossibile aggiungere il WMS " + wms_name + " al progetto")

    @QtCore.pyqtSlot(str, str, str, str)
    def addWfsQML(self, name, url, data, qml_url):
        """
            # Slot for exposing the same-name function to Javascript. #
            Add the WFS with its *.qml to the QGis TOC.
            :param name: The name
            :type name: str
            :param url: The WFS URL
            :type url: str
            :param data: Present an aggregate data separated by a "|". The first element is the layer, the second the
            EPSG code.
            :type data: str
            :param qml_url: The URL for the *.qml file
            :type qml_url: str
        """
        data = data.split("|")
        epsg_code = data[1]
        layer = data[0]

        # Check the download folder
        if not self.check_download_folder():
            return False

        qml_file_name = self.get_qml_file_name(qml_url)
        qml_file_path = self.download_qml(qml_url, qml_file_name)
        self.addWfs(name, url, layer, epsg_code, qml_file_path)

    @QtCore.pyqtSlot(str, str, str, str, str)
    def addWfs(self, name, url, layer, epsg_code, qml_file_path):
        """
            # Slot for exposing the same-name function to Javascript. #
            Add the WFS to the QGis TOC.
            :param name: The name
            :type name: str
            :param url: The WFS URL
            :type url: str
            :param layer: The layer
            :type layer: str
            :param epsg_code: The EPSG code (number)
            :type epsg_code: int
            :param qml_file_path: The *.qml file path
            :type qml_file_path: str
        """
        qgs_logger = QgsApplication.messageLog()
        qgs_logger.logMessage('addWms: {} {} {} {} {}'.format(name, url, layer, epsg_code, qml_file_path),
                              tag=configuration.LOGGER_TAG, level=Qgis.Info)

        # Preparing the URI
        uri = QgsDataSourceUri()
        uri.setParam("url", url)
        uri.setParam("typename", layer)
        uri.setParam('srsname', "EPSG:" + str(epsg_code))
        uri.setParam('version', "auto")

        # Instantiate
        wfs_layer = QgsVectorLayer(uri.uri(), name, "WFS", QgsVectorLayer.LayerOptions(False))

        # Add to map in case it is valid
        if wfs_layer.isValid():
            QgsProject.instance().addMapLayer(wfs_layer)
            wfs_layer.loadNamedStyle(qml_file_path)
        else:
            self.show_message("Attenzione!", "Impossibile aggiungere il WFS " + name + " al progetto")

    @QtCore.pyqtSlot(str, str)
    def apriFileLocale(self, name, local_file_path):
        """
            # Slot for exposing the same-name function to Javascript. #
            Open the local file.
            :param name: The name
            :type name: str
            :param local_file_path: The local file path
            :type local_file_path: str
        """
        # Get the file extension
        file_extension = os.path.splitext(local_file_path)[1][1:].upper()
        if file_extension == "ZIP":
            local_layer = QgsVectorLayer(local_file_path, name, "ogr")
        else:
            local_layer = QgsRasterLayer(local_file_path, name, )

        # In case the layer is valid, add to the map
        if local_layer.isValid():
            QgsProject.instance().addMapLayer(local_layer)
        else:
            self.show_message("Attenzione!", "Impossibile aprire il file " + local_file_path)

    @QtCore.pyqtSlot(str, str)
    def apriFileRemoto(self, name, url):
        """
            # Slot for exposing the same-name function to Javascript. #
            Open the remote file.
            :param name: The name
            :type name: str
            :param url: The URL for accessing the remote file
            :type url: str
        """

        # Check the existence of the folder
        if not self.check_download_folder():
            return False

        # Retrieving the file name from the URL
        file_name = url.split("://")
        file_name = file_name[len(file_name) - 1]
        file_name = file_name.replace("/", "_")

        # The local path
        local_file_path = os.path.join(self.download_folder_path, file_name)

        # Check if already exists the file
        to_download = True
        if os.path.exists(local_file_path) and os.path.isfile(local_file_path):
            reply = QMessageBox.question(None,
                                         'Attenzione',
                                         'file gia\' presente nella cartella di scarico. \nSovrascrivere?',
                                         QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                to_download = False
                reply = QMessageBox.question(None,
                                             'Scarico del dato annullato',
                                             'Caricare il dato presente in locale?',
                                             QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    return

        # Download the file if marked to do so
        if to_download:
            request = QtNetwork.QNetworkRequest(QUrl(url))
            reply = self.web_view.page().networkAccessManager().get(request)
            evloop = QEventLoop()
            reply.finished.connect(evloop.quit)
            evloop.exec_()
            response = bytearray(reply.readAll())
            with open(local_file_path, "wb") as f:
                f.write(response)

        # Instantiate
        vector_layer = QgsVectorLayer(local_file_path, name, "ogr")

        # In case the layer is valid, add to the QGis TOC
        if vector_layer.isValid():
            QgsProject.instance().addMapLayer(vector_layer)
        else:
            self.show_message("Attenzione!", "Impossibile aggiungere il pacchetto " + name + " al progetto")

    @QtCore.pyqtSlot(str, str, str, str, str, str, str, str, str, str)
    def addTabellaQML(self, name, host, port, database_name, username, schema, table, geom_col, id_col, qml_url):
        """
            # Slot for exposing the same-name function to Javascript. #
            Add the database table in the QGis TOC and apply its associated QML.
            :param name: The name
            :type name: str
            :param host: The hostname
            :type host: str
            :param port: Aggregated data separated by "|". The first element is the port, the second is the ssl request
            specification (e.g. require, allow, disable, prefer)
            :type port: str
            :param database_name: The database name
            :type database_name: str
            :param username: The username for connecting to the database
            :type username: str
            :param schema: The database schema
            :type schema: str
            :param table: Aggregated data separated by "|". The first is the table name, the second is the sql filter
            :type table: str
            :param geom_col: The geometry column name
            :type geom_col: str
            :param id_col: The identifier column name
            :type id_col: str
            :param qml_url: The *.qml file URL
            :type qml_url: str
        """
        port = port.split("|")
        ssl = port[1]
        port = port[0]

        table = table.split("|")
        sql_filter = table[1]
        table = table[0]

        # Check the download folder
        if not self.check_download_folder():
            return False

        # Delegate
        file_name = self.get_qml_file_name(qml_url)
        qml_file_path = self.download_qml(qml_url, file_name)
        self.add_postgres_layer(name, host, port, database_name, username, schema, table, geom_col, id_col, ssl,
                                qml_file_path, sql_filter)

    def add_postgres_layer(self, name, host, port, database_name, username, schema, table, geom_col, id_col, ssl,
                           qml_file_path, sql_filter):
        """
            Add the database table in the QGis TOC and apply its associated QML.
            :param name: The name
            :type name: str
            :param host: The hostname
            :type host: str
            :param port: Aggregated data separated by "|". The first element is the port, the second is the ssl request
            specification (e.g. require, allow, disable, prefer)
            :type port: str
            :param database_name: The database name
            :type database_name: str
            :param username: The username for connecting to the database
            :type username: str
            :param schema: The database schema
            :type schema: str
            :param table: Aggregated data separated by "|". The first is the table name, the second is the sql filter
            :type table: str
            :param geom_col: The geometry column name
            :type geom_col: str
            :param id_col: The identifier column name
            :type id_col: str
            :param ssl: The SSL type request. Expected one of: require, allow, disable or prefer.
            :type ssl: str
            :param qml_file_path: The *.qml file path
            :type qml_file_path: str
            :param sql_filter: The SQL where condition
            :type sql_filter: str
        """
        qgs_logger = QgsApplication.messageLog()
        qgs_logger.logMessage('addWms: name = {}'.format(name), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: host = {}'.format(host), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: port = {}'.format(port), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: database_name = {}'.format(database_name), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: username = {}'.format(username), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: schema = {}'.format(schema), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: table = {}'.format(table), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: geom_col = {}'.format(geom_col), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: id_col = {}'.format(id_col), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: ssl = {}'.format(ssl), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: self.session_user = {}'.format(str(self.session_user)),
                              tag=configuration.LOGGER_TAG, level=Qgis.Info)
        qgs_logger.logMessage('addWms: qml_file_path = {}'.format(qml_file_path), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)
        qgs_logger.logMessage('addWms: sql_filter = {}'.format(sql_filter), tag=configuration.LOGGER_TAG,
                              level=Qgis.Info)

        uri = QgsDataSourceUri()
        ssl_mode = QgsDataSourceUri.SslAllow

        if ssl == "require":
            ssl_mode = QgsDataSourceUri.SslRequire
        if ssl == "allow":
            ssl_mode = QgsDataSourceUri.SslAllow
        if ssl == "disable":
            ssl_mode = QgsDataSourceUri.SslDisable
        if ssl == "prefer":
            ssl_mode = QgsDataSourceUri.SslPrefer

        # Set the connection
        uri.setConnection(str(host), str(port), str(database_name), str(self.session_user), str(self.session_password),
                          ssl_mode)

        # In case the geometry column is not defined ignore as parameter, otherwise set it
        if str(geom_col) == "":
            uri.setDataSource(str(schema), str(table), None, sql_filter, str(id_col))
        else:
            uri.setDataSource(str(schema), str(table), str(geom_col), sql_filter, str(id_col))

        # Instantiate
        postgres_layer = QgsVectorLayer(uri.uri(), str(name), 'postgres')

        # In case the layer is valid, add to the QGis TOC
        if postgres_layer.isValid():
            QgsProject.instance().addMapLayer(postgres_layer)
            postgres_layer.loadNamedStyle(qml_file_path)
        else:
            par = "\nhost: " + str(host)\
                + "\nport: " + str(port)\
                + "\ndbname: " + str(database_name)\
                + "\nuser: " + str(self.session_user)\
                + "\nssl: " + str(ssl)\
                + "\nschema: " + str(schema)\
                + "\ntable: " + str(table) \
                + "\ngeom_col: " + str(geom_col) \
                + "\nid_col: " + str(id_col) \
                + "\npathQMLFile: " + str(qml_file_path) \
                + "\nsqlFilter: " + str(sql_filter)
            self.show_message("Attenzione!", "Impossibile aggiungere la tabella " + name + " al progetto.\n" + par)

    def check_download_folder(self):
        """
            Check the existence of the download folder or prompt the user for the selection of a new one.
            :return: True in case it exists
            :rtype: bool
        """
        # Check the download folder
        if os.path.exists(self.download_folder_path):
            return True

        # Prompt the user to choose one.
        title = "Attenzione!"
        message = "La cartella di scarico dei dati in locale non e' stata definita:" \
                  " prima di procedere e' necessario selezionarla."
        QMessageBox.information(None, title, message)
        self.selezionaCartellaScarico()

        # Check the download folder
        if os.path.exists(self.download_folder_path):
            return True

        # Arise error message to the user
        title = "Attenzione!"
        message = "La cartella di scarico selezionata non esiste o non e' valida."
        QMessageBox.information(None, title, message)
        return False

    def download_qml(self, qml_url, qml_file_name):
        """
            Download the *.qml file.
            :param qml_url: The URL for retrieving the *.qml file
            :type qml_url: str
            :param qml_file_name: The *.qml file name
            :type qml_file_name: str
        """
        local_file_path = os.path.join(self.download_folder_path, qml_file_name)

        qgs_logger = QgsApplication.messageLog()
        qgs_logger.logMessage('scaricaQML: {}'.format(qml_url), tag=configuration.LOGGER_TAG, level=Qgis.Info)

        # Download the file
        request = QtNetwork.QNetworkRequest(QUrl(qml_url))
        reply = self.web_view.page().networkAccessManager().get(request)
        evloop = QEventLoop()
        reply.finished.connect(evloop.quit)
        evloop.exec_()
        response = bytearray(reply.readAll())
        with open(local_file_path, "wb") as f:
            f.write(response)

        return local_file_path

    def get_qml_file_name(self, qml_url):
        """
            Retrieve the *.qml file name from the URL.
            :param qml_url: The *.qml  URL
            :type qml_url: str
            :return: The file name
            :rtype: str
        """
        return qml_url.split("/")[-1] + ".qml"

    def load_configuration(self):
        """
            Load the configuration for:
                - download folder path
                - the user in the session
                - the user password in the session
        """
        self.download_folder_path = csi_utils.get_qgs_settings_value_or_default(
            "CSIAtlanteWI/cartellaScaricoPacchetti", default="", value_type=str)
        self.session_user = csi_utils.get_qgs_settings_value_or_default(
            "CSIAtlanteWI/user", default="", value_type=str)
        self.session_password = csi_utils.get_qgs_settings_value_or_default(
            "CSIAtlanteWI/password", default="", value_type=str)

    def save_configuration(self):
        """
            Save the configuration for:
                - download folder path
                - the user in the session
                - the user password in the session
        """
        csi_utils.set_qgs_settings_value("CSIAtlanteWI/cartellaScaricoPacchetti", self.download_folder_path)
        csi_utils.set_qgs_settings_value("CSIAtlanteWI/user", self.session_user)
        csi_utils.set_qgs_settings_value("CSIAtlanteWI/password", self.session_password)

    @QtCore.pyqtSlot(str)
    def open_href(self, url):
        """
            # Slot for exposing the same-name function to Javascript. #
            Open the given URL in the browser.
            :param url: The URL to open
            :type url: str
        """
        QDesktopServices.openUrl(QUrl(url))

    @QtCore.pyqtSlot(result=str)
    def get_nome_progetto(self):
        """
            # Slot for exposing the same-name function to Javascript. #
            Retrieve the project name having the whitespaces replaced with underscores.
        """
        project_file_name = QFileInfo(QgsProject.instance().fileName())
        project_name = project_file_name.baseName()

        # Replacement for the whitespaces with underscore
        project_name = project_name.replace(" ", "_")
        return project_name

    @QtCore.pyqtSlot(result=str)
    def get_progetto_utf8_string(self):
        """
            # Slot for exposing the same-name function to Javascript. #
            Retrieve the current project as a UTF-8 string (both in case of a *.qgs and *.qgz)
            :return: The QGis project file as a UTF-8 string
            :rtype: str
        """
        project_title = QgsProject.instance().title()
        project_path = QgsProject.instance().fileName()

        # Controlli bloccanti
        if project_path == u'' or project_path == u'.qgs':
            QMessageBox.critical(None,
                                 "Progetto non salvato",
                                 "Il progetto non e' stato salvato in locale \ne non puo' essere salvato in remoto!\n "
                                 "prjpath == ###>" + project_path + "<###")
            return

        if QgsProject.instance().isDirty():
            # the dirty flag is true if the project has been modified since the last write()
            QMessageBox.critical(None,
                                 "Progetto in stato modificato",
                                 "E' necessario salvare su disco locale il progetto prima di procedere")
            return

        if project_title == u'':
            QMessageBox.critical(None,
                                 "Progetto in stato iniziale",
                                 "E' necessario inserire un titolo nelle proprieta' del progetto prima di procedere")
            return

        # Setting the loading cursor
        csi_utils.set_qgs_hourglass_cursor()

        try:
            # In case the project is a "qgz" proceed differently
            if QgsProject.instance().isZipped():
                project_file = None
                with codecs.open(project_path, 'rb') as f:
                    project_file = f.read()

                # The user base is using Windows OS. The *.zip archive are ANSI encoded by empirical observation
                project_file_os_decoded = codecs.decode(project_file, encoding="ansi")
                # Encoding to UTF-8 since all the stack is expecting it (AtlanteWI works on string, AtlanteBackOffice is
                # saving it on database and returning as a UTF-8 string)
                progetto_utf8_bytes = codecs.encode(project_file_os_decoded, encoding="utf-8")
                progetto_utf8_string = progetto_utf8_bytes.decode()
            else:
                progetto_utf8_string = csi_utils.get_compact_xml_string_from_qgs_file(project_path)
        except Exception as e:
            QMessageBox.critical(None,
                                 "Errore durante il recupero del progetto",
                                 str(e))
        finally:
            csi_utils.restore_qgs_cursor()

        return progetto_utf8_string

    def set_download_folder(self):
        """
            # Slot for exposing the same-name function to Javascript. #
            Execute Javascript code to set the download folder in that scope.
        """
        tmp = self.download_folder_path
        tmp = tmp.replace('\\', '\\\\')

        # Executing Javascript for storing the user
        js_script = "setCartellaScarico('{0}', false, 'INFO');".format(tmp.replace('"', '\\"'))
        self.web_view.page().mainFrame().evaluateJavaScript(js_script)
