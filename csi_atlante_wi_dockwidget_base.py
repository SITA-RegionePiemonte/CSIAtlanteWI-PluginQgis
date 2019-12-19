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


# Form implementation generated from reading ui file 'csi_atlante_wi_dockwidget_base.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DockWidget(object):
    def setupUi(self, DockWidget):
        DockWidget.setObjectName("DockWidget")
        DockWidget.resize(350, 500)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DockWidget.sizePolicy().hasHeightForWidth())
        DockWidget.setSizePolicy(sizePolicy)
        DockWidget.setMinimumSize(QtCore.QSize(350, 500))
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.gridLayout = QtWidgets.QGridLayout(self.dockWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        DockWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(DockWidget)
        QtCore.QMetaObject.connectSlotsByName(DockWidget)

    def retranslateUi(self, DockWidget):
        _translate = QtCore.QCoreApplication.translate
        DockWidget.setWindowTitle(_translate("DockWidget", "CSI Atlante WI"))

