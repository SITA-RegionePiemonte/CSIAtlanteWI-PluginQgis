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

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import Qgis, QgsApplication

from .. import configuration


class CsiWebView(QWebView):
    """
        Extends the QWebView and it is used for presenting the AtlanteWI in QGis
    """

    def __init__(self, parent=None, **kwargs):
        super(CsiWebView, self).__init__(parent)
        self.kwargs = kwargs

        # Adding custom action to the widget (right-click activated)
        self.clearCacheAction = QtWidgets.QAction('Pulisci cache e cronologia', self)
        self.clearCacheAction.triggered.connect(self.slot_clear_cache)

    def slot_clear_cache(self):
        """
            Clear the cache.
        """
        cache = self.page().networkAccessManager().cache()
        if cache is None:
            return

        qgs_logger = QgsApplication.messageLog()
        choice = QMessageBox.question(self,
                                      'Pulizia cache',
                                      "Confermi pulizia della cache del browser?",
                                      QMessageBox.Yes | QMessageBox.No)
        if choice == QMessageBox.Yes:
            qgs_logger.logMessage('CsiWebView clear_cache!', tag=configuration.LOGGER_TAG, level=Qgis.Warning)
            cache.clear()

    def contextMenuEvent(self, event):
        """
            Overridden method.
            :param event: The context menu event
            :type event: QContextMenuEvent
        """
        # Getting the menu (right-click activated), which is a QMenu object
        menu = self.page().createStandardContextMenu()
        # Adding the clear-cache action
        menu.addAction(self.clearCacheAction)
        # Show the menu on the specific position
        menu.exec(event.globalPos())
