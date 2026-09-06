# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ReconGeoDialog
                                 A QGIS plugin
 Plugin ReconGeo para QGIS com interface Qt5 editável via Qt Designer
 ***************************************************************************/
"""

import os
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis import gui

# Carrega a classe base da interface dinamicamente do arquivo .ui.
# Dessa forma, qualquer edição feita no Qt Designer é reconhecida automaticamente!
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'recongeo_dialog_base.ui'))


class ReconGeoDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Construtor da janela de diálogo.

        :param parent: Widget pai (normalmente a janela principal do QGIS iface.mainWindow()).
        """
        super(ReconGeoDialog, self).__init__(parent)
        # Configura e inicializa os componentes definidos no Qt Designer (.ui)
        self.setupUi(self)

        # Variável para armazenar o caminho completo do PDF selecionado
        self.caminho_pdf = None

        # Conecta o botão btn_abrir_pdf à função que seleciona e abre o PDF
        if hasattr(self, 'btn_abrir_pdf'):
            self.btn_abrir_pdf.clicked.connect(self.abrir_pdf)

    def abrir_pdf(self):
        """Abre uma caixa de diálogo para seleção de um arquivo PDF.
        Atualiza o QLabel 'lbl_arquivo' com o nome do arquivo selecionado
        e abre o arquivo no visualizador padrão do sistema operacional.
        """
        caminho_arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo PDF",
            "",
            "Arquivos PDF (*.pdf);;Todos os Arquivos (*)"
        )

        if not caminho_arquivo:
            return

        # Armazena o caminho do arquivo selecionado
        self.caminho_pdf = caminho_arquivo

        # Obtém o nome do arquivo selecionado (ex: 'processo_123.pdf')
        nome_arquivo = os.path.basename(caminho_arquivo)

        # Altera o QLabel 'lbl_arquivo' com o nome do arquivo selecionado
        if hasattr(self, 'lbl_arquivo'):
            self.lbl_arquivo.setText(nome_arquivo)
            self.lbl_arquivo.setToolTip(caminho_arquivo)

        # Abre o arquivo no visualizador padrão do sistema operacional
        url = QUrl.fromLocalFile(caminho_arquivo)
        sucesso = QDesktopServices.openUrl(url)
        if not sucesso:
            QMessageBox.warning(
                self,
                "Aviso",
                f"Não foi possível abrir o arquivo no visualizador do sistema:\n{caminho_arquivo}"
            )

    def get_valores(self):
        """Método auxiliar para coletar os dados do formulário."""
        return {
            "processo": self.processo.text().strip() if hasattr(self, 'processo') else "",
            "gleba": self.gleba.text().strip() if hasattr(self, 'gleba') else "",
            "nome_lote": self.nome_lote.text().strip() if hasattr(self, 'nome_lote') else "",
            "titulado": self.titulado.text().strip() if hasattr(self, 'titulado') else "",
            "area": self.area.text().strip() if hasattr(self, 'area') else "",
            "uf": self.uf.text().strip() if hasattr(self, 'uf') else "",
            "municipio": self.municipio.text().strip() if hasattr(self, 'municipio') else "",
            "caminho_pdf": self.caminho_pdf,
        }

