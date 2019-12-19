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


from qgis.core import Qgis, QgsApplication

from .. import configuration


class CsiClassHelper(object):
    """
        General purpose helper class
    """

    def __init__(self, instance):
        self.instance = instance
        self.class_name = self.instance.__class__.__name__

        qgs_logger = QgsApplication.messageLog()
        qgs_logger.logMessage("__________________ Class Name: {} __________________".format(self.class_name),
                              tag=configuration.LOGGER_TAG, level=Qgis.Info)

    def log_properties(self):
        """
            Log 'info' messages inherently the properties of the wrapped object
        """
        qgs_logger = QgsApplication.messageLog()

        if self.class_name == "QNetworkAccessManager":
            return

        if self.class_name == "QNetworkDiskCache":
            qgs_logger.logMessage("cacheDirectory() : {}".format(
                self.instance.cacheDirectory()), tag=configuration.LOGGER_TAG, level=Qgis.Info)
            qgs_logger.logMessage("maximumCacheSize(): {}".format(
                self.instance.maximumCacheSize()), tag=configuration.LOGGER_TAG, level=Qgis.Info)
            qgs_logger.logMessage("cacheSize(): {}".format(
                self.instance.cacheSize()), tag=configuration.LOGGER_TAG, level=Qgis.Info)
        else:
            qgs_logger.logMessage("Unknown class name!", tag=configuration.LOGGER_TAG, level=Qgis.Info)
