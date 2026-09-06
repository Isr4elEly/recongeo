# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ReconGeo
                                 A QGIS plugin
 Plugin ReconGeo para QGIS com interface Qt5 editável via Qt Designer
 ***************************************************************************/
"""


def classFactory(iface):
    """Carrega e instancia a classe principal do plugin ReconGeo.

    :param iface: Instância da interface do QGIS (QgsInterface).
    :type iface: QgsInterface
    """
    from .recongeo import ReconGeoPlugin
    return ReconGeoPlugin(iface)
