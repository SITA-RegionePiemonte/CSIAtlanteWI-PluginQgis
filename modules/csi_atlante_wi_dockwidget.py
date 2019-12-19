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


from qgis.PyQt import QtCore, QtNetwork, QtWebKit, QtWidgets
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QPalette
from qgis.core import QgsNetworkAccessManager, Qgis, QgsApplication

from . import csi_utils
from .. import configuration
from .csi_class_helper import CsiClassHelper
from .csi_network_access_manager import CsiNetworkAccessManager
from .csi_web_view import CsiWebView
from ..csi_atlante_wi_dockwidget_base import Ui_DockWidget
from .js_manager import JsManager

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class CSIAtlanteWIDockWidget(QtWidgets.QDockWidget, Ui_DockWidget):
    """
        Represents the CSIAtlanteWI QGIS plugin dock widget, which is the main element in the plugin.
    """

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.dlg = Ui_DockWidget()
        self.dlg.setupUi(self)

        # Getting the logger
        qgs_logger = QgsApplication.messageLog()

        # Retrieving configurations
        qgs_logger.logMessage(message="Settings retrieved from the default file: " + QtCore.QSettings().fileName(),
                              tag=configuration.LOGGER_TAG, level=Qgis.Info)
        self.debug = csi_utils.get_qgs_settings_value_or_default("CSIAtlanteWI/debug",
                                                                 default=configuration.DEBUG, value_type=bool)
        qgs_logger.logMessage('debug: {}'.format(str(self.debug)), tag=configuration.LOGGER_TAG, level=Qgis.Info)
        self.debug_log = csi_utils.get_qgs_settings_value_or_default(
            "CSIAtlanteWI/debug_log", default=configuration.DEBUG_ON_FILE, value_type=bool)
        qgs_logger.logMessage('debug_log: {}'.format(str(self.debug)), tag=configuration.LOGGER_TAG, level=Qgis.Info)
        
        # Getting the log file path from configuration
        self.log_file_path = csi_utils.get_qgs_settings_value_or_default(
            "CSIAtlanteWI/logfile", default=configuration.CSI_LOG_FILE_PATH, value_type=str)
        qgs_logger.logMessage(
            'logfilename: {}'.format(self.log_file_path), tag=configuration.LOGGER_TAG, level=Qgis.Info)

        # In case the 'debug' flag is set, write the message to the logfile
        if self.debug_log:
            qgs_logger.messageReceived.connect(csi_utils.write_log_message)

        # Setting the proxy
        proxy_enabled = csi_utils.get_qgs_settings_value_or_default("proxy/proxyEnabled", default=False, value_type=bool)
        qgs_logger.logMessage(
            'proxy_enabled: {}'.format(str(proxy_enabled)), tag=configuration.LOGGER_TAG, level=Qgis.Info)

        # In case the proxy is required, set it
        if proxy_enabled:
            proxy_host = csi_utils.get_qgs_settings_value_or_default(
                "proxy/proxyHost", default=configuration.CSI_PROXY, value_type=str)
            qgs_logger.logMessage('proxy_host: {}'.format(proxy_host), tag=configuration.LOGGER_TAG, level=Qgis.Info)
            proxy_port = csi_utils.get_qgs_settings_value_or_default(
                "proxy/proxyPort", default=configuration.CSI_PROXY_PORT, value_type=int)
            qgs_logger.logMessage(
                'proxy_port: {}'.format(str(proxy_port)), tag=configuration.LOGGER_TAG, level=Qgis.Info)
            proxy_type = csi_utils.get_qgs_settings_value_or_default(
                "proxy/proxyType", default=configuration.CSI_PROXY_TYPE, value_type=str)
            qgs_logger.logMessage('proxy_type: {}'.format(proxy_type), tag=configuration.LOGGER_TAG, level=Qgis.Info)

            # Preparing the proxy
            self.proxy = QtNetwork.QNetworkProxy()
            self.proxy.setType(QtNetwork.QNetworkProxy.HttpProxy)
            self.proxy.setHostName(proxy_host)
            self.proxy.setPort(proxy_port)
            # Setting the proxy application level
            QtNetwork.QNetworkProxy.setApplicationProxy(self.proxy)
        
        # In case the element is already associated, remove it
        if hasattr(self.dlg, 'webview'):
            self.dlg.gridLayout.removeWidget(self.dlg.webview)
            del self.dlg.webview

        # Instantiating the 'webview' (extending the QWebView)
        self.dlg.webview = CsiWebView(self.dlg.dockWidgetContents)

        # Defining the size policy
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.dlg.webview.sizePolicy().hasHeightForWidth())
        self.dlg.webview.setSizePolicy(size_policy)

        # Additional settings for the webview
        self.dlg.webview.setStyleSheet(_fromUtf8("background-color:#ffffff;"))
        self.dlg.webview.setProperty("url", QtCore.QUrl(_fromUtf8("about:blank")))
        self.dlg.webview.setObjectName(_fromUtf8("webview"))

        # Adding the webview widget in the grid layout filling the whole column and row
        self.dlg.gridLayout.addWidget(self.dlg.webview, 0, 0, 1, 1)

        # Getting the configuration for which NetworkAccessManager to use
        self.use_qgs_networkaccessmanager = csi_utils.get_qgs_settings_value_or_default(
            "CSIAtlanteWI/use_qgs_networkaccessmanager", default=True, value_type=bool)
        qgs_logger.logMessage('use_qgs_networkaccessmanager: {}'
                              .format(self.use_qgs_networkaccessmanager), tag=configuration.LOGGER_TAG, level=Qgis.Info)

        # Setting the proper NetworAccessManager
        if self.use_qgs_networkaccessmanager:
            # Getting the current NetworkAccessManager in use
            self.network_access_manager = QgsNetworkAccessManager.instance()
            # Wrap on the CsiNetworkAccessManager
            self.network_access_manager = CsiNetworkAccessManager(self.network_access_manager, self.debug)
        else:
            # Getting the NetworkAccessManager used by the view
            self.network_access_manager = self.dlg.webview.page().networkAccessManager()
            # Wrap on the CsiNetworkAccessManager
            self.network_access_manager = CsiNetworkAccessManager(self.network_access_manager, self.debug)

        # Logging the NetworAccessManager
        if self.debug:
            proxy = self.network_access_manager.proxy()
            qgs_logger.logMessage('networkaccessmanager.proxy: {} {}'.format(proxy.hostName(), str(proxy.port())),
                                  tag=configuration.LOGGER_TAG, level=Qgis.Info)
        
        # Setting the CsiNetworkAccessManager to the webview
        self.dlg.webview.page().setNetworkAccessManager(self.network_access_manager)
        # Updating the reference
        self.network_access_manager = self.dlg.webview.page().networkAccessManager()

        # Log the cache element
        if self.debug:
            helper = CsiClassHelper(self.network_access_manager.cache())
            helper.log_properties()
            helper = None

        # Getting the background color from the palette
        color = self.palette().color(QPalette.Background).name()
        # Instantiate the JsManager on the webview with the color palette
        self.jsManager = JsManager(self.dlg.webview, color)

        # Connect slots to signals
        self.dlg.webview.loadFinished.connect(self.slot_log_cookies)
        self.dlg.webview.loadFinished.connect(self.slot_enable_developer_extra_tools)
        self.dlg.webview.loadFinished.connect(self.slot_engage_javascript)

        # Retrieve the AtlanteWI URL
        self.url_plugin = csi_utils.get_qgs_settings_value_or_default(
            "CSIAtlanteWI/url_plugin", default=configuration.ATLANTEWI_URL, value_type=str)

        # Load the AtlanteWI in the WebView
        self.dlg.webview.load(QUrl(self.url_plugin))

        # Log
        qgs_logger.logMessage(
            "--------------------------------------------", tag=configuration.LOGGER_TAG, level=Qgis.Info)
        qgs_logger.logMessage(
            "url_plugin: {}".format(self.url_plugin), tag=configuration.LOGGER_TAG, level=Qgis.Info)
        qgs_logger.logMessage(
            "--------------------------------------------", tag=configuration.LOGGER_TAG, level=Qgis.Info)

    def slot_enable_developer_extra_tools(self):
        """
            Enable the additional settings for developers
        """
        # Enabling the tools for 'Web developers' like the 'Inspect' tool
        self.dlg.webview.settings().setAttribute(QtWebKit.QWebSettings.DeveloperExtrasEnabled, True)
        # Enabling the browser plugins
        self.dlg.webview.settings().setAttribute(QtWebKit.QWebSettings.PluginsEnabled, True)

    def slot_engage_javascript(self):
        """
            Enabling the 'qgis' element JavaScript side, referring to the jsManager module
        """
        self.dlg.webview.settings().setAttribute(QtWebKit.QWebSettings.JavascriptEnabled, True)
        # Enabling the JavaScript object 'qgis' and relating it to the module jsManager
        self.dlg.webview.page().mainFrame().addToJavaScriptWindowObject('qgis', self.jsManager)
        # Activate the javascript interested in the HTML page creation
        self.dlg.webview.page().mainFrame().evaluateJavaScript("start();")

    def slot_log_cookies(self):
        """
            Log of the cookies
        """
        qgs_logger = QgsApplication.messageLog()
        qgs_logger.logMessage(
            "__________________ cookies __________________", tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)
        network_access_manager = self.dlg.webview.page().networkAccessManager()
        cookie_jar = network_access_manager.cookieJar()
        cookies = cookie_jar.cookiesForUrl(QUrl(self.url_plugin))
        for cookie in cookies:
            if not self.debug:
                qgs_logger.logMessage(
                    "{0} = {1}".format(cookie.name(), cookie.value().data()), tag=configuration.NETWORK_LOGGER_TAG,
                    level=Qgis.Info)
                continue

            # Finer logger
            qgs_logger.logMessage(
                "cookie name()            : " + str(cookie.name()), tag=configuration.LOGGER_TAG, level=Qgis.Warning)
            qgs_logger.logMessage(
                "cookie value()           : " + str(cookie.value()), tag=configuration.LOGGER_TAG, level=Qgis.Warning)
            qgs_logger.logMessage(
                "cookie isSessionCookie() : " + str(cookie.isSessionCookie()), tag=configuration.LOGGER_TAG,
                level=Qgis.Warning)
            if not cookie.isSessionCookie():
                # If this cookie is a session cookie, the QDateTime returned will not be valid, so add the following
                qgs_logger.logMessage(
                    "cookie expirationDate(): " + cookie.expirationDate().toString(), tag=configuration.LOGGER_TAG,
                    level=Qgis.Warning)

            qgs_logger.logMessage(
                "cookie isSecure()        : " + str(cookie.isSecure()), tag=configuration.LOGGER_TAG,
                level=Qgis.Warning)
            qgs_logger.logMessage(
                "cookie isHttpOnly()      : " + str(cookie.isHttpOnly()), tag=configuration.LOGGER_TAG,
                level=Qgis.Warning)
