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
from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

# Import the Qt resources from file 'resources.py' (required for successfully show the icon)
from . import resources
from .modules.csi_atlante_wi_dockwidget import CSIAtlanteWIDockWidget


class CSIAtlanteWI(object):
    """
        The main class representing the plugin QGIS for the Atlante Suite
    """

    def __init__(self, iface):
        """
            Constructor.
            :param iface: The interface instance for manipulating the QGIS application at run time.
            :type iface: QgsInterface
        """
        # Save QGis interface reference
        self.iface = iface

        # Initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # Initialize locale
        locale = QSettings().value("locale" + os.sep + "userLocale")
        if locale:
            locale = locale[0:2]

        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'CSIAtlanteWI_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.translate(u'&CSI Atlante WI')
        self.toolbar = self.iface.addToolBar(u'CSIAtlanteWI')
        self.toolbar.setObjectName(u'CSIAtlanteWI')

        self.pluginIsActive = False
        self.dockwidget = None
        self.windowPosition = None
        self.load_configs()

    def translate(self, message):
        """
            Get the translation for a string using Qt translation API.
            :param message: String for translation.
            :type message: str, QString
            :returns: Translated version of message.
            :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('CSIAtlanteWI', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """
            Add a toolbar icon to the toolbar.
            :param icon_path: Path to the icon for this action. Can be a resource path (e.g. ':/plugins/foo/bar.png')
                or a normal file system path.
            :type icon_path: str
            :param text: Text that should be shown in menu items for this action.
            :type text: str
            :param callback: Function to be called when the action is triggered.
            :type callback: function
            :param enabled_flag: A flag indicating if the action should be enabled by default. Defaults to True.
            :type enabled_flag: bool
            :param add_to_menu: Flag indicating whether the action should also be added to the menu. Defaults to True.
            :type add_to_menu: bool
            :param add_to_toolbar: Flag indicating whether the action should also be added to the toolbar. Defaults
                to True.
            :type add_to_toolbar: bool
            :param status_tip: Optional text to show in a popup when mouse pointer hovers over the action.
            :type status_tip: str
            :param parent: Parent widget for the new action. Defaults None.
            :type parent: QWidget
            :param whats_this: Optional text to show in the status bar when the mouse pointer hovers over the action.
            :returns: The action that was created. Note that the action is also added to self.actions list.
            :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """
            Create the menu entries and toolbar icons inside the QGIS GUI.
            The method named is required as 'initGui', for proper loading the QGis plugin.
        """

        icon_path = ':' + os.sep + 'plugins' + os.sep + 'CSIAtlanteWI' + os.sep + 'icon.png'
        self.add_action(
            icon_path,
            text=self.translate(u'CSI Atlante WI'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """
            Removes the plugin menu item and icon from QGIS GUI.
        """
        self.save_configs()

        for action in self.actions:
            self.iface.removePluginMenu(
                self.translate(u'&CSI Atlante WI'),
                action)
            self.iface.removeToolBarIcon(action)

        del self.toolbar

    def run(self):
        """
            Run method that loads and starts the plugin
        """
        self.windowPosition = Qt.LeftDockWidgetArea
        if self.dockwidget is None:
            self.dockwidget = CSIAtlanteWIDockWidget()
            self.iface.addDockWidget(self.windowPosition, self.dockwidget)
            self.dockwidget.show()
        else:
            if self.dockwidget.isVisible():
                self.iface.removeDockWidget(self.dockwidget)
            else:
                self.iface.addDockWidget(self.windowPosition, self.dockwidget)
                self.dockwidget.show()

    def save_configs(self):
        """
            Save the plugin settings
        """
        # A reference for future approach
        pass

    def load_configs(self):
        """
            Load the plugin settings
        """
        # A reference for future approach
        pass
