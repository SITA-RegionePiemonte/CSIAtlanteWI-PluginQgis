# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CSIAtlanteWI
                                 A QGIS plugin
 CSI Atlante Web Interfaces
                             -------------------
        begin                : 2018-03-05
        copyright            : (C) 2018 by CSI Piemonte
        email                : stefano.giorgi@csi.it
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """
        Load CSIAtlanteWI class from file CSIAtlanteWI.

        :param iface: A QGIS interface instance.
        :type iface: QgsInterface
    """
    from .csi_atlante_wi import CSIAtlanteWI
    return CSIAtlanteWI(iface)
