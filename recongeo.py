# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ReconGeo
                                 A QGIS plugin
 Plugin ReconGeo para QGIS com interface Qt5 editável via Qt Designer
 ***************************************************************************/
"""

import os
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import Qgis, QgsMessageLog

from .recongeo_dialog import ReconGeoDialog


class ReconGeoPlugin:
    """Classe principal do plugin ReconGeo para o QGIS."""

    def __init__(self, iface):
        """Construtor.

        :param iface: Interface do QGIS fornecida pelo runtime.
        :type iface: QgsInterface
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = "&ReconGeo"
        self.toolbar = self.iface.addToolBar("ReconGeo")
        self.toolbar.setObjectName("ReconGeo")
        self.dlg = None

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
        parent=None,
    ):
        """Cria e registra uma ação (QAction) no QGIS."""
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent or self.iface.mainWindow())
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip:
            action.setStatusTip(status_tip)
        if whats_this:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        """Inicializa a interface gráfica do plugin no QGIS (menu e barra de ferramentas)."""
        icon_path = os.path.join(self.plugin_dir, "icon.png")

        self.add_action(
            icon_path=icon_path,
            text="Abrir ReconGeo",
            callback=self.run,
            parent=self.iface.mainWindow(),
            status_tip="Abre a janela principal do plugin ReconGeo",
        )

    def unload(self):
        """Descarrega o plugin, removendo menus e barras de ferramentas do QGIS."""
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

        del self.toolbar

    def run(self):
        """Executa a lógica principal e abre a janela de diálogo."""
        # Instancia o diálogo. Como o recongeo_dialog.py usa uic.loadUiType,
        # cada nova instância recarregará eventuais alterações feitas no Qt Designer.
        self.dlg = ReconGeoDialog(self.iface.mainWindow())

        # Exibe a janela de forma modal
        result = self.dlg.exec_()

        # Se o usuário clicou em OK / Aceitar
        if result:
            dados = self.dlg.get_valores()
            lote = dados.get("nome_lote") or "N/A"
            processo = dados.get("processo") or "N/A"
            mensagem = (
                f"ReconGeo executado com sucesso!\n"
                f"Lote: {lote}\n"
                f"Processo: {processo}"
            )
            self.iface.messageBar().pushMessage(
                "ReconGeo",
                mensagem,
                level=Qgis.Info,
                duration=5,
            )
            QgsMessageLog.logMessage(mensagem, "ReconGeo", level=Qgis.Info)
