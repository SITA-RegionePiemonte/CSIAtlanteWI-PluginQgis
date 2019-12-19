# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QByteArray


class CsiCertificate(object):
    """
        The CSI certificates for SSL encryption
    """

    @classmethod
    def get_certificate(cls):
        # Set a value in case of use
        s = ""
        qba = QByteArray(s)
        return qba

    @classmethod
    def get_key(cls):
        # Set a value in case of use
        s = ""
        qba = QByteArray(s)
        return qba

