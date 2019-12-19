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

from PyQt5.QtCore import QUrl, QMetaObject
from qgis.PyQt import QtCore, QtWebKit
from qgis.PyQt.QtWidgets import QDialog
from qgis._core import QgsApplication, Qgis

from .. import configuration
from . import csi_utils
from ..csi_atlante_wi_metadata_base import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class DialogMetadata(QDialog):
    """
        Charged to present the metadata elements
    """

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.dlg = Ui_Dialog()
        self.dlg.setupUi(self)
        self.debug = csi_utils.get_qgs_settings_value_or_default("CSIAtlanteWI/debug", default=False, value_type=bool)

        if hasattr(self.dlg, 'webview'):
            self.dlg.gridLayout.removeWidget(self.dlg.webview)
            del self.dlg.webview

        # Defining the dialog webview
        self.dlg.webview = QtWebKit.QWebView()

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

        # Adding the webview widget in the grid layout
        self.dlg.gridLayout.addWidget(self.dlg.webview, 1, 0, 1, 1)

        QMetaObject.connectSlotsByName(self)
        self.dlg.btn_chiudi.clicked.connect(self.slot_close)

    def set_title(self, title):
        """
            Set the txt_layer title
            :param title: The txt_layer title
            :type title: str
        """
        self.dlg.txt_layer.setText(title)

    def set_url(self, url):
        """
            Set the target URL for the metadata dialog webview
            :param url: The target URL
            :type url: str
        """
        qgs_logger = QgsApplication.messageLog()
        qgs_logger.logMessage('DialogMetadata: url {}'.format(url), tag=configuration.LOGGER_TAG, level=Qgis.Info)
        self.dlg.webview.load(QUrl(url))
        self.dlg.webview.show()

    def slot_close(self):
        """
            Close the dialog
        """
        self.close()
