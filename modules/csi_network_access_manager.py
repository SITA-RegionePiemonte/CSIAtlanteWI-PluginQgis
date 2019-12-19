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


from PyQt5.QtWidgets import QMessageBox
from qgis.PyQt import QtNetwork
from qgis.core import Qgis, QgsApplication

from .. import configuration
from .csi_certificate import CsiCertificate


class CsiNetworkAccessManager(QtNetwork.QNetworkAccessManager):
    """
        Customized NetworkAccessManager.
        The methods override are for debug purposes.
    """

    def __init__(self, old_manager, debug=False):
        """
            Wrap the NetworkAccessManager given in the 'old_manager'
            :param old_manager: The NetworkAccessManager to wrap
            :type old_manager: QNetworkAccessManager
            :param debug: True for processing debug information
            :type debug: bool
        """
        super().__init__()
        self.debug = debug
        self.experiment = False

        # Setting the same objects of the given 'old_manager'
        self.setCache(old_manager.cache())
        self.setCookieJar(old_manager.cookieJar())
        self.setProxy(old_manager.proxy())
        self.setProxyFactory(old_manager.proxyFactory())

        # Connecting slots
        self.finished.connect(self.slot_on_finished_handler)
        self.sslErrors.connect(self.slot_ssl_errors_handler)

    def createRequest(self, operation, original_request, outgoing_data):
        """
            Overridden method. See https://doc.qt.io/qt-5/qnetworkaccessmanager.html#createRequest
            :param operation: The operation
            :type operation: QNetworkAccessManager.Operation
            :param original_request: The request
            :type original_request: QNetworkRequest
            :param outgoing_data: The outgoing data
            :type outgoing_data: QIODevice
            :return: The reply in the open state
            :rtype: QNetworkReply
        """
        # Invoking the original method
        if not self.experiment:
            reply = super().createRequest(operation, original_request, outgoing_data)
            return reply

        qgs_logger = QgsApplication.messageLog()
        qgs_logger.logMessage('createRequest: overrided', tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)

        # 28 March 2019
        certificate = CsiCertificate()
        qba_cert = certificate.get_certificate()
        qba_key = certificate.get_key()
        qgs_logger.logMessage('_createRequest: csi cert {}'.format(qba_cert.__class__.__name__),
                              tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Warning)
        ssl_conf = original_request.sslConfiguration()
        ca_cert_list = ssl_conf.caCertificates()
        qgs_logger.logMessage('_createRequest: ca_cert_list {}'.format(ca_cert_list.__class__.__name__),
                              tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Warning)
        for ca in ca_cert_list:
            qgs_logger.logMessage('_createRequest: ca {}'.format(ca.__class__.__name__),
                                  tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Warning)

        ca_cert = QtNetwork.QSslCertificate.fromData(qba_cert, QtNetwork.QSsl.Pem)
        ca_cert_list.append(ca_cert)

        ssl_key = QtNetwork.QSslKey(qba_key, QtNetwork.QSsl.Rsa)
        ssl_cert = QtNetwork.QSslCertificate(qba_cert)
        ssl_conf.setLocalCertificate(ssl_cert)
        ssl_conf.setPrivateKey(ssl_key)
        ssl_conf.setProtocol(QtNetwork.QSsl.AnyProtocol)
        original_request.setSslConfiguration(ssl_conf)

        # Following is useful for testing issues on HTTPS and WMS Basic auth:
        if self.debug:
            qgs_logger.logMessage('createRequest: operation {}'.format(str(operation)),
                                  tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)
            qgs_logger.logMessage('createRequest: request {}'.format(original_request),
                                  tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)
            if outgoing_data is not None:
                qgs_logger.logMessage('createRequest: data {}'.format(str(outgoing_data)),
                                      tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)
            if outgoing_data and hasattr(outgoing_data, 'bytesAvailable'):
                qgs_logger.logMessage('createRequest: data size {}'.format(str(outgoing_data.bytesAvailable())),
                                      tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)

            # Logging URL data
            url = original_request.url()
            qgs_logger.logMessage('createRequest: url {}'.format(url),
                                  configuration=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)
            if hasattr(url, 'encodedPath'):
                qgs_logger.logMessage('createRequest: encoded query items {}'.format(url.encodedPath()),
                                      tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)
            if hasattr(url, 'encodedQuery'):
                qgs_logger.logMessage('_createRequest: encoded query items {}'.format(url.encodedQuery()),
                                      tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)
            if hasattr(url, 'encodedQueryItems'):
                qgs_logger.logMessage('_createRequest: encoded query items {}'.format(url.encodedQueryItems()),
                                      tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)
            if hasattr(url, 'queryItems'):
                qgs_logger.logMessage('_createRequest: queryItems? {}'.format(url.queryItems()),
                                      tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)
            qgs_logger.logMessage('_createRequest: headers {}'.format(original_request.rawHeaderList()),
                                  tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)

        # Generating the request
        reply = super().createRequest(operation, original_request, outgoing_data)
        return reply

    def slot_ssl_errors_handler(self, reply, errors):
        """
            Handler for the arisen SSL errors, usually encountered during set-up.
            See: https://doc.qt.io/qt-5/qnetworkaccessmanager.html#sslErrors
            :param reply: The request sent through the QNetworkAccessManager
            :type reply: QNetworkReply
            :param errors: The list of errors
            :type errors: QList of QSslError
        """
        qgs_logger = QgsApplication.messageLog()
        qgs_logger.logMessage('slot_ssl_errors_handler: connected', tag=configuration.NETWORK_LOGGER_TAG,
                              level=Qgis.Info)
        url = reply.url().toString()
        qgs_logger.logMessage('slot_ssl_errors_handler: ignoreSslErrors() {}'.format(url),
                              tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Warning)

        # The list of the fields identifiers to print (i.e. from 0 to 5 included)
        certificate_fields_list = range(0, 6)

        # Processing the errors
        errors_messages = []
        for e in errors:
            # Logging the error data
            qgs_logger.logMessage('slot_ssl_errors_handler: e {}'.format(e.__class__.__name__),
                                  tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Critical)
            qgs_logger.logMessage('slot_ssl_errors_handler: errorString {}'.format(e.errorString()),
                                  tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Critical)
            if len(errors_messages) > 0:
                errors_messages.append("\n")

            errors_messages.append(e.errorString())

            # In case the debug flag is enabled, log additional details
            if self.debug:
                # Logging the certificate
                certificate = e.certificate()
                qgs_logger.logMessage('slot_ssl_errors_handler: certificate {}'.format(certificate),
                                      tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Warning)

                # Printing the certificate 'data' for subjectInfo and issuerInfo fields
                for i in certificate_fields_list:
                    qgs_logger.logMessage('slot_ssl_errors_handler: subjectInfo[{}] {}'
                                          .format(i, certificate.subjectInfo(i)), tag=configuration.NETWORK_LOGGER_TAG,
                                          level=Qgis.Warning)
                    qgs_logger.logMessage('slot_ssl_errors_handler: issuerInfo[{}] {}'
                                          .format(i, certificate.issuerInfo(i)), tag=configuration.NETWORK_LOGGER_TAG,
                                          level=Qgis.Warning)

                # Printing other certificate 'data'
                qgs_logger.logMessage('slot_ssl_errors_handler: version {}'.format(certificate.version()),
                                      tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Warning)
                qgs_logger.logMessage('slot_ssl_errors_handler: effectiveDate {}'
                                      .format(certificate.effectiveDate().toString("dd.MM.yyyy hh:mm:ss.zzz")),
                                      tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Warning)
                expiration_date = certificate.expiryDate().toString("dd.MM.yyyy hh:mm:ss.zzz")
                qgs_logger.logMessage('slot_ssl_errors_handler: expiryDate {}'.format(expiration_date),
                                      tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Warning)
                public_key = certificate.publicKey()
                qgs_logger.logMessage('slot_ssl_errors_handler: publicKey {}'.format(public_key),
                                      tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Warning)

        # Letting the user decide to proceed
        message = "Si sta cercando di connettersi ad un indirizzo in HTTPs, ma sono sorti dei problemi. "
        if len(errors_messages) > 0:
            message += "Riscontrati i seguenti errori:\n\n"
            message += "".join(errors_messages)
        else:
            message += "Probabilmente problema di certificato SSL."
        message += "\n\nProcedere comunque?"
        user_answer = QMessageBox.question(None, 'Attenzione', message, QMessageBox.Yes, QMessageBox.No)
        if user_answer == QMessageBox.No:
            return

        reply.ignoreSslErrors()

    def slot_on_finished_handler(self, reply):
        """
            QNetworkAccessManager has an asynchronous API.
            When the replyFinished slot is called, the parameter it takes is the QNetworkReply object
            containing the downloaded data as well as meta-data.
            :param reply: The request sent through the QNetworkAccessManager
            :type reply: QNetworkReply
        """
        qgs_logger = QgsApplication.messageLog()

        # In case there is some error
        if reply.error() != QtNetwork.QNetworkReply.NoError:
            # SSL handshake error
            if reply.error() == QtNetwork.QNetworkReply.SslHandshakeFailedError:
                qgs_logger.logMessage('replyFinished: SslHandshakeFailedError {0}'.format(reply.errorString()),
                                      tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Critical)
                return

            # In case of other error
            qgs_logger.logMessage('replyFinished: Error {0}'.format(reply.errorString()),
                                  tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Critical)
            return

        # In case the reply doesn't have any error
        if self.debug:
            from_cache = reply.attribute(QtNetwork.QNetworkRequest.SourceIsFromCacheAttribute)
            qgs_logger.logMessage('replyFinished: page from cache? {} -> {}'.format(from_cache, reply.url().toString()),
                                  tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)

            # Log just the index.php
            url = reply.url().toString()
            if "index.php" in url:
                request = reply.request()
                known_headers_list = ["Accept", "Accept-Encoding", "Accept-Language", "Authorization", "Cache-Control",
                                      "Connection", "Cookie", "DNT", "Host", "Referer", "Upgrade-Insecure-Requests",
                                      "User-Agent"]
                qgs_logger.logMessage("url: {}".format(url), tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)

                # The request headers
                for i in range(len(known_headers_list)):
                    header = known_headers_list[i]
                    if request.hasRawHeader(bytearray(header, encoding='utf8')):
                        header_content = str(request.rawHeader(bytearray(header, encoding='utf8')))
                        qgs_logger.logMessage("Request header: {0}: {1}".format(header, header_content),
                                              tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Info)

                # The response headers
                raw_headers = reply.rawHeaderPairs()
                response_headers = {str(k): str(v) for k, v in raw_headers}
                for key, value in response_headers.items():
                    qgs_logger.logMessage("Response Header: {0} : {1}".format(key, value),
                                          tag=configuration.NETWORK_LOGGER_TAG, level=Qgis.Warning)
