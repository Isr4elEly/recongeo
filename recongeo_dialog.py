# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ReconGeoDialog
                                 A QGIS plugin
 Plugin ReconGeo para QGIS com interface Qt5 editável via Qt Designer
 ***************************************************************************/
"""

import os
import json
import math
import shutil
from datetime import datetime
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QDate, QLocale, QUrl, Qt, QVariant
from qgis.PyQt.QtGui import QDesktopServices, QDoubleValidator, QIntValidator, QValidator
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis import gui
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
    QgsVectorFileWriter,
)

# Carrega a classe base da interface dinamicamente do arquivo .ui.
# Dessa forma, qualquer edição feita no Qt Designer é reconhecida automaticamente!
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'recongeo_dialog_base.ui'))


class FloatValidator(QDoubleValidator):
    """Validador numérico de ponto flutuante (float) que:
    - Aceita tanto ponto (.) quanto vírgula (,) como separador decimal.
    - Limita estritamente o número de casas decimais ao valor configurado.
    - Suporta valores positivos e negativos.
    """

    def __init__(self, decimals=2, bottom=-1e15, top=1e15, parent=None):
        super(FloatValidator, self).__init__(bottom, top, decimals, parent)
        self.setNotation(QDoubleValidator.StandardNotation)
        self.setLocale(QLocale(QLocale.C))

    def validate(self, input_str, pos):
        normalized = input_str.replace(',', '.')
        state, _, pos = super(FloatValidator, self).validate(normalized, pos)
        return state, input_str, pos


class IntegerValidator(QIntValidator):
    """Validador numérico para números inteiros (int) que:
    - Aceita apenas dígitos inteiros (sem separador decimal, letras ou símbolos).
    - Valida o intervalo [bottom, top] em tempo real.
    - Permite campo vazio durante a digitação/edição.
    """

    def __init__(self, bottom=0, top=999999, parent=None):
        super(IntegerValidator, self).__init__(bottom, top, parent)

    def validate(self, input_str, pos):
        if not input_str:
            return QValidator.Intermediate, input_str, pos
        if not input_str.isdigit():
            return QValidator.Invalid, input_str, pos
        val = int(input_str)
        if self.bottom() <= val <= self.top():
            return QValidator.Acceptable, input_str, pos
        if val < self.bottom():
            return QValidator.Intermediate, input_str, pos
        return QValidator.Invalid, input_str, pos


class ReconGeoDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, iface=None):
        """Construtor da janela de diálogo.

        :param parent: Widget pai (normalmente a janela principal do QGIS iface.mainWindow()).
        """
        super(ReconGeoDialog, self).__init__(parent)
        self.iface = iface
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        # Configura e inicializa os componentes definidos no Qt Designer (.ui)
        self.setupUi(self)

        # Define SIRGAS 2000 como sistema de coordenadas padrão
        if hasattr(self, 'mQgsProjectionSelectionWidget'):
            self.mQgsProjectionSelectionWidget.setCrs(
                QgsCoordinateReferenceSystem('EPSG:4674')
            )

        # Variável para armazenar o caminho completo do PDF selecionado
        self.caminho_pdf = None
        self.pdf_copiado = ''

        # Variável para armazenar o nome padrão formatado do arquivo
        self.nome_padrao_do_arquivo = None

        # Valores do vértice inicial da tabela de azimute
        self.vertice_ini_valor = None
        self.coord_este_ini_valor = None
        self.coord_norte_ini_valor = None

        # Conecta o botão btn_abrir_pdf à função que seleciona e abre o PDF
        if hasattr(self, 'btn_abrir_pdf'):
            self.btn_abrir_pdf.clicked.connect(self.abrir_pdf)

        # Conecta o botão btn_salvar à função de salvar dados e btn_dados_finais ao nome padrão
        if hasattr(self, 'btn_salvar'):
            self.btn_salvar.clicked.connect(self.salvar_dados)

        if hasattr(self, 'btn_dados_finais'):
            self.btn_dados_finais.clicked.connect(
                lambda checked=False: self.arquivos_finais()
            )

        # Confirma a limpeza antes de abrir um novo arquivo
        if hasattr(self, 'btn_abrir'):
            self.btn_abrir.clicked.connect(
                lambda checked=False: self.confirmar_novo_arquivo()
            )

        # Conecta o botão à limpeza completa do formulário
        if hasattr(self, 'btn_limp_form'):
            self.btn_limp_form.clicked.connect(self.limpar_formulario)

        if hasattr(self, 'btn_add_vert_ini_az'):
            self.btn_add_vert_ini_az.clicked.connect(
                lambda checked=False: self.adicionar_vertice_inicial_az()
            )

        if hasattr(self, 'btn_remove_vert_ini_az'):
            self.btn_remove_vert_ini_az.setEnabled(False)
            self.btn_remove_vert_ini_az.clicked.connect(
                lambda checked=False: self.remover_vertice_inicial_az()
            )

        if hasattr(self, 'btn_remove_ln_az'):
            self.btn_remove_ln_az.setEnabled(False)
            self.btn_remove_ln_az.clicked.connect(
                lambda checked=False: self.remover_linha_azimute()
            )

        if hasattr(self, 'btn_az_recal_tabela'):
            self.btn_az_recal_tabela.setEnabled(False)
            self.btn_az_recal_tabela.clicked.connect(
                lambda checked=False: self.recalcular_tabela_azimute()
            )

        self.configurar_campos_azimute(False)

        # Conecta o botão à criação das camadas temporárias
        if hasattr(self, 'btn_vetor_temp'):
            self.btn_vetor_temp.clicked.connect(
                lambda checked=False: self.criar_camadas_coordenadas()
            )

        # Conecta o botão btn_add_ln_cor à função de adicionar linha
        if hasattr(self, 'btn_add_ln_cor'):
            self.btn_add_ln_cor.clicked.connect(self.adicionar_linha_coordenada)

        if hasattr(self, 'btn_add_ln_az'):
            self.btn_add_ln_az.clicked.connect(
                lambda checked=False: self.adicionar_linha_azimute()
            )

        # Define a data atual do sistema como padrão para o campo data_analise
        if hasattr(self, 'data_analise'):
            self.data_analise.setDate(QDate.currentDate())

        # Habilita a remoção somente quando houver uma linha selecionada
        if hasattr(self, 'btn_remove_ln_cor'):
            self.btn_remove_ln_cor.setEnabled(False)
            self.btn_remove_ln_cor.clicked.connect(
                self.remover_linha_coordenada
            )

        if hasattr(self, 'tbl_coordenanda'):
            self.tbl_coordenanda.setSelectionBehavior(
                QtWidgets.QAbstractItemView.SelectRows
            )
            self.tbl_coordenanda.itemSelectionChanged.connect(
                self.atualizar_estado_btn_remove_ln_cor
            )

        if hasattr(self, 'tbl_azimute'):
            self.tbl_azimute.setSelectionBehavior(
                QtWidgets.QAbstractItemView.SelectRows
            )
            self.tbl_azimute.itemSelectionChanged.connect(
                self.atualizar_estado_botoes_azimute
            )

        self.atualizar_estado_abas_tabelas()

        # Configura os validadores float e int nos QLineEdit especificados
        self.configurar_validadores()

    def atualizar_estado_btn_remove_ln_cor(self):
        """Atualiza o botão conforme a seleção da tabela de coordenadas."""
        if (hasattr(self, 'btn_remove_ln_cor')
            and hasattr(self, 'tbl_coordenanda')):
            linha_selecionada = bool(
                self.tbl_coordenanda.selectionModel().selectedRows()
            )
            self.btn_remove_ln_cor.setEnabled(linha_selecionada)

    def atualizar_estado_abas_tabelas(self):
        """Desabilita a aba oposta à tabela que já possui dados."""
        if not hasattr(self, 'tabWidget'):
            return

        coordenadas_preenchidas = (
            hasattr(self, 'tbl_coordenanda')
            and self.tbl_coordenanda.rowCount() > 0
        )
        azimute_preenchido = (
            hasattr(self, 'tbl_azimute')
            and self.tbl_azimute.rowCount() > 0
        )
        indice_azimute = self.tabWidget.indexOf(self.azimute)
        indice_coordenada = self.tabWidget.indexOf(self.coordenada)

        if coordenadas_preenchidas:
            self.tabWidget.setTabEnabled(indice_azimute, False)
        elif azimute_preenchido:
            self.tabWidget.setTabEnabled(indice_coordenada, False)
        else:
            self.tabWidget.setTabEnabled(indice_azimute, True)
            self.tabWidget.setTabEnabled(indice_coordenada, True)

    def remover_linha_coordenada(self):
        """Remove da tabela de coordenadas a linha selecionada."""
        if not hasattr(self, 'tbl_coordenanda'):
            return
        if (hasattr(self, 'tbl_azimute')
                and self.tbl_azimute.rowCount() > 0):
            return

        tabela = self.tbl_coordenanda
        linha = tabela.currentRow()
        if linha < 0:
            return

        tabela.removeRow(linha)
        self.atualizar_estado_btn_remove_ln_cor()
        self.atualizar_estado_abas_tabelas()

    def atualizar_estado_botoes_azimute(self):
        """Atualiza os botões conforme a seleção de segmentos."""
        if not hasattr(self, 'tbl_azimute'):
            return

        linhas_selecionadas = self.tbl_azimute.selectionModel().selectedRows()
        linha_selecionada = bool(linhas_selecionadas)
        if hasattr(self, 'btn_remove_ln_az'):
            self.btn_remove_ln_az.setEnabled(linha_selecionada)
        if hasattr(self, 'btn_az_recal_tabela'):
            self.btn_az_recal_tabela.setEnabled(linha_selecionada)

    def configurar_campos_azimute(self, habilitado):
        """Habilita ou desabilita os campos dependentes do vértice inicial."""
        campos = [
            'confrontante_az',
            'graus',
            'minutos',
            'segundos',
            'vertice_az',
        ]
        for nome_campo in campos:
            if hasattr(self, nome_campo):
                getattr(self, nome_campo).setEnabled(habilitado)

    def adicionar_vertice_inicial_az(self):
        """Insere o vértice inicial como primeira linha da tabela de azimute."""
        if self.vertice_ini_valor is not None:
            return
        if (hasattr(self, 'tbl_coordenanda')
                and self.tbl_coordenanda.rowCount() > 0):
            return

        campos = ['vertice_ini', 'coord_este_ini', 'coord_norte_ini']
        valores = {}
        for nome_campo in campos:
            if not hasattr(self, nome_campo):
                return
            valores[nome_campo] = getattr(self, nome_campo).text().strip()

        if not all(valores.values()):
            QMessageBox.warning(
                self,
                'Dados incompletos',
                'Preencha o vértice inicial e as coordenadas Este e Norte.'
            )
            return

        try:
            float(valores['coord_este_ini'].replace(',', '.'))
            float(valores['coord_norte_ini'].replace(',', '.'))
        except ValueError:
            QMessageBox.warning(
                self,
                'Coordenadas inválidas',
                'As coordenadas Este e Norte devem ser numéricas.'
            )
            return

        self.vertice_ini_valor = valores['vertice_ini']
        self.coord_este_ini_valor = valores['coord_este_ini']
        self.coord_norte_ini_valor = valores['coord_norte_ini']

        if hasattr(self, 'tbl_azimute'):
            from qgis.PyQt.QtWidgets import QTableWidgetItem

            self.tbl_azimute.insertRow(0)
            valores_linha = [
                self.vertice_ini_valor,
                self.coord_este_ini_valor,
                self.coord_norte_ini_valor,
            ]
            for coluna, valor in enumerate(valores_linha):
                self.tbl_azimute.setItem(
                    0,
                    coluna,
                    QTableWidgetItem(valor),
                )

        if hasattr(self, 'btn_add_vert_ini_az'):
            self.btn_add_vert_ini_az.setEnabled(False)
        if hasattr(self, 'btn_remove_vert_ini_az'):
            self.btn_remove_vert_ini_az.setEnabled(True)
        self.configurar_campos_azimute(True)
        self.atualizar_estado_abas_tabelas()

    def calc_azimute_decimal(self, graus, minutos, segundos):
        """Converte graus, minutos e segundos para graus decimais."""
        return graus + (minutos / 60.0) + (segundos / 3600.0)

    def calc_delta_este(self, azimute_decimal, distancia):
        """Calcula a variação Este a partir do azimute e distância."""
        return math.sin(math.radians(azimute_decimal)) * distancia

    def calc_delta_norte(self, azimute_decimal, distancia):
        """Calcula a variação Norte a partir do azimute e distância."""
        return math.cos(math.radians(azimute_decimal)) * distancia

    def calcula_coodenada_seguinte(
            self, este_ini, norte_ini, delta_este, delta_norte):
        """Calcula a coordenada seguinte a partir da coordenada anterior."""
        este_pos = este_ini + delta_este
        norte_pos = norte_ini + delta_norte
        return este_pos, norte_pos

    def adicionar_linha_azimute(self):
        """Calcula e adiciona a próxima linha na tabela de azimute."""
        if not hasattr(self, 'tbl_azimute'):
            return
        if (hasattr(self, 'tbl_coordenanda')
                and self.tbl_coordenanda.rowCount() > 0):
            return

        campos = [
            'graus',
            'minutos',
            'segundos',
            'distancia',
            'vertice_az',
            'confrontante_az',
        ]
        valores = {}
        for nome_campo in campos:
            if not hasattr(self, nome_campo):
                return
            valores[nome_campo] = getattr(self, nome_campo).text().strip()

        if not all(valores.values()):
            QMessageBox.warning(
                self,
                'Dados incompletos',
                'Preencha todos os campos do novo segmento de azimute.'
            )
            return

        try:
            graus = float(valores['graus'].replace(',', '.'))
            minutos = float(valores['minutos'].replace(',', '.'))
            segundos = float(valores['segundos'].replace(',', '.'))
            distancia = float(valores['distancia'].replace(',', '.'))
        except ValueError:
            QMessageBox.warning(
                self,
                'Valores inválidos',
                'Graus, minutos, segundos e distância devem ser numéricos.'
            )
            return

        tabela = self.tbl_azimute
        if tabela.rowCount() == 0:
            QMessageBox.warning(
                self,
                'Vértice inicial ausente',
                'Adicione o vértice inicial antes de inserir um segmento.'
            )
            return

        linha_anterior = tabela.rowCount() - 1
        item_este = tabela.item(linha_anterior, 1)
        item_norte = tabela.item(linha_anterior, 2)
        try:
            este_ini = float(item_este.text().replace(',', '.'))
            norte_ini = float(item_norte.text().replace(',', '.'))
        except (AttributeError, ValueError):
            QMessageBox.warning(
                self,
                'Coordenada anterior inválida',
                'A linha anterior não possui coordenadas Este e Norte válidas.'
            )
            return

        azimute_decimal = self.calc_azimute_decimal(
            graus, minutos, segundos
        )
        delta_este = self.calc_delta_este(azimute_decimal, distancia)
        delta_norte = self.calc_delta_norte(azimute_decimal, distancia)
        este_pos, norte_pos = self.calcula_coodenada_seguinte(
            este_ini,
            norte_ini,
            delta_este,
            delta_norte,
        )

        from qgis.PyQt.QtWidgets import QTableWidgetItem

        nova_linha = tabela.rowCount()
        tabela.insertRow(nova_linha)
        valores_linha = [
            valores['vertice_az'],
            f'{este_pos:.6f}',
            f'{norte_pos:.6f}',
            valores['graus'],
            valores['minutos'],
            valores['segundos'],
            valores['distancia'],
            f'{azimute_decimal:.6f}',
            f'{delta_este:.6f}',
            f'{delta_norte:.6f}',
            valores['confrontante_az'],
        ]
        for coluna, valor in enumerate(valores_linha):
            tabela.setItem(
                nova_linha,
                coluna,
                QTableWidgetItem(valor),
            )

        for nome_campo in campos:
            getattr(self, nome_campo).clear()
        self.graus.setFocus()
        self.atualizar_estado_abas_tabelas()

    def recalcular_linhas_azimute(self, linha_inicial):
        """Recalcula uma linha e todas as linhas seguintes da tabela."""
        tabela = self.tbl_azimute
        if linha_inicial <= 0 or linha_inicial >= tabela.rowCount():
            return False

        for numero_linha in range(linha_inicial, tabela.rowCount()):
            item_este = tabela.item(numero_linha - 1, 1)
            item_norte = tabela.item(numero_linha - 1, 2)
            try:
                este_ini = float(item_este.text().replace(',', '.'))
                norte_ini = float(item_norte.text().replace(',', '.'))
                graus = float(tabela.item(numero_linha, 3).text().replace(',', '.'))
                minutos = float(tabela.item(numero_linha, 4).text().replace(',', '.'))
                segundos = float(tabela.item(numero_linha, 5).text().replace(',', '.'))
                distancia = float(tabela.item(numero_linha, 6).text().replace(',', '.'))
            except (AttributeError, ValueError):
                return False

            azimute_decimal = self.calc_azimute_decimal(
                graus, minutos, segundos
            )
            delta_este = self.calc_delta_este(azimute_decimal, distancia)
            delta_norte = self.calc_delta_norte(azimute_decimal, distancia)
            este_pos, norte_pos = self.calcula_coodenada_seguinte(
                este_ini,
                norte_ini,
                delta_este,
                delta_norte,
            )
            tabela.item(numero_linha, 1).setText(f'{este_pos:.6f}')
            tabela.item(numero_linha, 2).setText(f'{norte_pos:.6f}')
            tabela.item(numero_linha, 7).setText(f'{azimute_decimal:.6f}')
            tabela.item(numero_linha, 8).setText(f'{delta_este:.6f}')
            tabela.item(numero_linha, 9).setText(f'{delta_norte:.6f}')

        return True

    def remover_linha_azimute(self):
        """Remove o segmento selecionado e recalcula os segmentos abaixo."""
        if not hasattr(self, 'tbl_azimute'):
            return

        tabela = self.tbl_azimute
        linha = tabela.currentRow()
        if linha < 0:
            return

        if linha == 0:
            self.remover_vertice_inicial_az()
            return

        tabela.removeRow(linha)
        if tabela.rowCount() > linha:
            self.recalcular_linhas_azimute(linha)
        self.atualizar_estado_botoes_azimute()
        self.atualizar_estado_abas_tabelas()

    def recalcular_tabela_azimute(self):
        """Recalcula a linha selecionada e todas as linhas abaixo."""
        if not hasattr(self, 'tbl_azimute'):
            return

        linha = self.tbl_azimute.currentRow()
        if linha == 0:
            linha = 1
        if linha < self.tbl_azimute.rowCount():
            self.recalcular_linhas_azimute(linha)

    def remover_vertice_inicial_az(self):
        """Remove a primeira linha da tabela e libera uma nova inserção."""
        if not hasattr(self, 'tbl_azimute'):
            return

        if self.vertice_ini_valor is None or self.tbl_azimute.rowCount() == 0:
            return

        self.tbl_azimute.removeRow(0)
        self.vertice_ini_valor = None
        self.coord_este_ini_valor = None
        self.coord_norte_ini_valor = None

        if hasattr(self, 'btn_add_vert_ini_az'):
            self.btn_add_vert_ini_az.setEnabled(True)
        if hasattr(self, 'btn_remove_vert_ini_az'):
            self.btn_remove_vert_ini_az.setEnabled(False)
        self.configurar_campos_azimute(False)
        self.atualizar_estado_botoes_azimute()
        self.atualizar_estado_abas_tabelas()

    def confirmar_novo_arquivo(self):
        """Confirma a limpeza e inicia a importação de um novo arquivo."""
        resposta = QMessageBox.question(
            self,
            'Abrir novo arquivo',
            'Ao abrir um novo arquivo, as informações digitadas no '
            'formulário serão apagadas. Deseja continuar?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resposta == QMessageBox.Yes:
            self.limpar_formulario(confirmar=False)
            self.importar_dados()

    def limpar_formulario(self, confirmar=True):
        """Confirma e limpa campos, tabelas e arquivos selecionados."""
        if confirmar:
            resposta = QMessageBox.question(
                self,
                'Confirmar limpeza',
                'Deseja realmente limpar todos os campos e tabelas '
                'do formulário?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if resposta != QMessageBox.Yes:
                return

        for campo in self.findChildren(QtWidgets.QLineEdit):
            campo.clear()

        for campo in self.findChildren(QtWidgets.QTextEdit):
            campo.clear()

        for campo in self.findChildren(QtWidgets.QPlainTextEdit):
            campo.clear()

        for campo in self.findChildren(QtWidgets.QComboBox):
            campo.setCurrentIndex(-1)

        for campo in self.findChildren(QtWidgets.QCheckBox):
            campo.setChecked(False)

        for campo in self.findChildren(QtWidgets.QDateEdit):
            campo.lineEdit().clear()

        for tabela in self.findChildren(QtWidgets.QTableWidget):
            tabela.clearContents()
            tabela.setRowCount(0)

        if hasattr(self, 'mQgsProjectionSelectionWidget'):
            self.mQgsProjectionSelectionWidget.setCrs(
                QgsCoordinateReferenceSystem('EPSG:4674')
            )

        self.caminho_pdf = None
        self.pdf_copiado = ''
        self.nome_padrao_do_arquivo = None
        self.vertice_ini_valor = None
        self.coord_este_ini_valor = None
        self.coord_norte_ini_valor = None

        for nome_label in ['lbl_arquivo', 'lbl_arquivo_padrao']:
            if hasattr(self, nome_label):
                label = getattr(self, nome_label)
                label.clear()
                label.setToolTip('')

        self.atualizar_estado_btn_remove_ln_cor()
        if hasattr(self, 'btn_remove_ln_az'):
            self.btn_remove_ln_az.setEnabled(False)
        if hasattr(self, 'btn_az_recal_tabela'):
            self.btn_az_recal_tabela.setEnabled(False)
        self.configurar_campos_azimute(False)
        if hasattr(self, 'btn_add_vert_ini_az'):
            self.btn_add_vert_ini_az.setEnabled(True)
        if hasattr(self, 'btn_remove_vert_ini_az'):
            self.btn_remove_vert_ini_az.setEnabled(False)
        self.atualizar_estado_abas_tabelas()

    def configurar_validadores(self):
        """Aplica validação float e int com restrições apropriadas aos QLineEdit."""
        # 'area': 4 casas decimais
        if hasattr(self, 'area'):
            self.area.setValidator(FloatValidator(decimals=4, parent=self))

        # 'distancia': 2 casas decimais
        if hasattr(self, 'distancia'):
            self.distancia.setValidator(FloatValidator(decimals=2, parent=self))

        # 'coord_este_ini', 'coord_norte_ini', 'este_cor', 'norte_cor': 6 casas decimais
        campos_6_decimais = [
            'coord_este_ini',
            'coord_norte_ini',
            'este_cor',
            'norte_cor',
        ]
        for nome_campo in campos_6_decimais:
            if hasattr(self, nome_campo):
                getattr(self, nome_campo).setValidator(FloatValidator(decimals=6, parent=self))

        # 'graus': inteiro (0 a 360 graus para azimutes)
        if hasattr(self, 'graus'):
            self.graus.setValidator(IntegerValidator(bottom=0, top=360, parent=self))

        # 'minutos': inteiro (0 a 59 minutos)
        if hasattr(self, 'minutos'):
            self.minutos.setValidator(IntegerValidator(bottom=0, top=59, parent=self))

        # 'segundos': inteiro (0 a 59 segundos)
        if hasattr(self, 'segundos'):
            self.segundos.setValidator(IntegerValidator(bottom=0, top=59, parent=self))

    def adicionar_linha_coordenada(self):
        """Coleta os valores dos campos de coordenada do painel de entrada
        [vertice_cor, este_cor, norte_cor, confrontante_cor],
        insere uma nova linha na tabela 'tbl_coordenanda' com os dados na ordem fornecida,
        limpa os campos de entrada e retorna o foco para o campo 'vertice_cor'.

        Colunas da tabela (0-indexed):
            0 → Vértice      → vertice_cor
            1 → Este         → este_cor
            2 → Norte        → norte_cor
            3 → Confrontante → confrontante_cor
        """
        from qgis.PyQt.QtWidgets import QTableWidgetItem

        # Coleta os valores dos campos na ordem especificada
        vertice = self.vertice_cor.text().strip() if hasattr(self, 'vertice_cor') else ""
        este = self.este_cor.text().strip() if hasattr(self, 'este_cor') else ""
        norte = self.norte_cor.text().strip() if hasattr(self, 'norte_cor') else ""
        confrontante = self.confrontante_cor.text().strip() if hasattr(self, 'confrontante_cor') else ""

        if not hasattr(self, 'tbl_coordenanda'):
            return
        if (hasattr(self, 'tbl_azimute')
                and self.tbl_azimute.rowCount() > 0):
            return

        # Adiciona nova linha ao final da tabela
        tabela = self.tbl_coordenanda
        nova_linha = tabela.rowCount()
        tabela.insertRow(nova_linha)

        # Preenche cada célula na ordem: vértice, este, norte, confrontante, lote vizinho
        tabela.setItem(nova_linha, 0, QTableWidgetItem(vertice))
        tabela.setItem(nova_linha, 1, QTableWidgetItem(este))
        tabela.setItem(nova_linha, 2, QTableWidgetItem(norte))
        tabela.setItem(nova_linha, 3, QTableWidgetItem(confrontante))

        # Rola a tabela até a linha recém-adicionada
        tabela.scrollToItem(tabela.item(nova_linha, 0))

        # Limpa os campos de entrada
        for campo in ['vertice_cor', 'este_cor', 'norte_cor', 'confrontante_cor']:
            if hasattr(self, campo):
                getattr(self, campo).clear()

        # Retorna o foco para o campo 'vertice_cor'
        if hasattr(self, 'vertice_cor'):
            self.vertice_cor.setFocus()
        self.atualizar_estado_abas_tabelas()

    def criar_camadas_coordenadas(self, adicionar_projeto=True):
        """Cria pontos, linhas e polígono com a tabela preenchida."""
        usa_azimute = (
            hasattr(self, 'tbl_azimute')
            and self.tbl_azimute.rowCount() > 0
        )
        if usa_azimute:
            tabela = self.tbl_azimute
            numero_colunas = 11
            confrontante_coluna = 10
        elif hasattr(self, 'tbl_coordenanda'):
            tabela = self.tbl_coordenanda
            numero_colunas = 5
            confrontante_coluna = 3
        else:
            return None

        sistema_coordenadas = QgsCoordinateReferenceSystem('EPSG:4674')
        if hasattr(self, 'mQgsProjectionSelectionWidget'):
            sistema_selecionado = self.mQgsProjectionSelectionWidget.crs()
            if sistema_selecionado.isValid():
                sistema_coordenadas = sistema_selecionado

        pontos = []
        atributos = []
        linhas_invalidas = []
        for numero_linha in range(tabela.rowCount()):
            item_este = tabela.item(numero_linha, 1)
            item_norte = tabela.item(numero_linha, 2)
            valor_este = item_este.text().strip() if item_este else ''
            valor_norte = item_norte.text().strip() if item_norte else ''

            try:
                coordenada_este = float(valor_este.replace(',', '.'))
                coordenada_norte = float(valor_norte.replace(',', '.'))
            except (TypeError, ValueError):
                linhas_invalidas.append(numero_linha + 1)
                continue

            pontos.append(QgsPointXY(coordenada_este, coordenada_norte))
            atributos.append([
                tabela.item(numero_linha, coluna).text().strip()
                if tabela.item(numero_linha, coluna) else ''
                for coluna in range(numero_colunas)
            ])

        if len(pontos) < 3:
            QMessageBox.warning(
                self,
                'Coordenadas insuficientes',
                'Informe pelo menos três linhas com coordenadas '
                'Este e Norte válidas.'
            )
            return None

        texto_crs = sistema_coordenadas.authid() or 'EPSG:4674'
        nome_base = self.nome_padrao_do_arquivo or 'ReconGeo'
        camada_pontos = QgsVectorLayer(
            f'Point?crs={texto_crs}',
            f'{nome_base}_pto',
            'memory'
        )
        if usa_azimute:
            campos_pontos = [
                ('vertice', QVariant.String),
                ('este', QVariant.Double),
                ('norte', QVariant.Double),
                ('graus', QVariant.Double),
                ('minutos', QVariant.Double),
                ('segundos', QVariant.Double),
                ('distancia', QVariant.Double),
                ('azimute_decimal', QVariant.Double),
                ('delta_este', QVariant.Double),
                ('delta_norte', QVariant.Double),
                ('confrontante', QVariant.String),
            ]
        else:
            campos_pontos = [
                ('vertice', QVariant.String),
                ('este', QVariant.Double),
                ('norte', QVariant.Double),
                ('confrontante', QVariant.String),
            ]
        camada_pontos.dataProvider().addAttributes([
            QgsField(nome, tipo) for nome, tipo in campos_pontos
        ])
        camada_pontos.updateFields()

        feicoes_pontos = []
        for ponto, valores in zip(pontos, atributos):
            feicao_ponto = QgsFeature(camada_pontos.fields())
            feicao_ponto.setGeometry(QgsGeometry.fromPointXY(ponto))
            atributos_ponto = [
                valores[0],
                float(valores[1].replace(',', '.')),
                float(valores[2].replace(',', '.')),
            ]
            if usa_azimute:
                atributos_ponto.extend([
                    float(valores[coluna].replace(',', '.'))
                    if valores[coluna] else None
                    for coluna in range(3, 10)
                ])
                atributos_ponto.append(valores[10])
            else:
                atributos_ponto.append(valores[3])
            feicao_ponto.setAttributes(atributos_ponto)
            feicoes_pontos.append(feicao_ponto)
        camada_pontos.dataProvider().addFeatures(feicoes_pontos)

        camada_poligono = QgsVectorLayer(
            f'Polygon?crs={texto_crs}',
            f'{nome_base}_pol',
            'memory'
        )

        dados_titulo_poligono = [
            ('processo', self.processo.text().strip()
             if hasattr(self, 'processo') else ''),
            ('gleba', self.gleba.text().strip()
             if hasattr(self, 'gleba') else ''),
            ('num_titulo', self.num_titulo.text().strip()
             if hasattr(self, 'num_titulo') else ''),
            ('num_lote', self.num_lote.text().strip()
             if hasattr(self, 'num_lote') else ''),
            ('nome_lote', self.nome_lote.text().strip()
             if hasattr(self, 'nome_lote') else ''),
            ('data_titulo', self.data_titulo.date().toString('dd/MM/yyyy')
             if hasattr(self, 'data_titulo') else ''),
            ('titulado', self.titulado.text().strip()
             if hasattr(self, 'titulado') else ''),
            ('area', self.area.text().strip()
             if hasattr(self, 'area') else ''),
            ('uf', self.uf.text().strip() if hasattr(self, 'uf') else ''),
            ('municipio', self.municipio.text().strip()
             if hasattr(self, 'municipio') else ''),
            ('data_analise', self.data_analise.date().toString('dd/MM/yyyy')
             if hasattr(self, 'data_analise') else ''),
            ('chkbox_sigef', str(self.chkbox_sigef.isChecked())
             if hasattr(self, 'chkbox_sigef') else 'False'),
            ('planilha_status', self.planilha_status.currentText()
             if hasattr(self, 'planilha_status') else ''),
            ('obs', self.obs.toPlainText().strip()
             if hasattr(self, 'obs') else ''),
            ('pdf_original', os.path.basename(self.caminho_pdf)
             if self.caminho_pdf else ''),
            ('pdf_copiado', self.pdf_copiado),
        ]
        camada_poligono.dataProvider().addAttributes([
            QgsField('num_pontos', QVariant.Int),
            *[QgsField(chave, QVariant.String)
              for chave, _ in dados_titulo_poligono],
        ])
        camada_poligono.updateFields()

        feicao_poligono = QgsFeature(camada_poligono.fields())
        anel_poligono = pontos + [pontos[0]]
        feicao_poligono.setGeometry(QgsGeometry.fromPolygonXY([anel_poligono]))
        feicao_poligono.setAttributes([
            len(pontos),
            *[valor for _, valor in dados_titulo_poligono],
        ])
        camada_poligono.dataProvider().addFeature(feicao_poligono)

        camada_linhas = QgsVectorLayer(
            f'LineString?crs={texto_crs}',
            f'{nome_base}_lna',
            'memory'
        )
        camada_linhas.dataProvider().addAttributes([
            QgsField('ordem', QVariant.Int),
            QgsField('vertice_inicial', QVariant.String),
            QgsField('vertice_final', QVariant.String),
            QgsField('confrontante', QVariant.String),
        ])
        camada_linhas.updateFields()

        feicoes_linhas = []
        for indice, valores_iniciais in enumerate(atributos):
            indice_final = (indice + 1) % len(atributos)
            valores_finais = atributos[indice_final]
            feicao_linha = QgsFeature(camada_linhas.fields())
            feicao_linha.setGeometry(QgsGeometry.fromPolylineXY([
                pontos[indice],
                pontos[indice_final],
            ]))
            feicao_linha.setAttributes([
                indice + 1,
                valores_iniciais[0],
                valores_finais[0],
                valores_finais[confrontante_coluna],
            ])
            feicoes_linhas.append(feicao_linha)
        camada_linhas.dataProvider().addFeatures(feicoes_linhas)

        if adicionar_projeto:
            QgsProject.instance().addMapLayers([
                camada_pontos,
                camada_poligono,
                camada_linhas,
            ])
        if adicionar_projeto and self.iface is not None:
            canvas = self.iface.mapCanvas()
            canvas.setExtent(camada_poligono.extent())
            canvas.refresh()

        if linhas_invalidas:
            QMessageBox.warning(
                self,
                'Linhas ignoradas',
                'As seguintes linhas não possuem coordenadas válidas: '
                + ', '.join(map(str, linhas_invalidas))
            )

        return camada_pontos, camada_poligono, camada_linhas

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

    def formatar_nome_padrao_do_arquivo(self, *args, **kwargs):
        """Formata o 'nome_padrao_do_arquivo' utilizando os campos obrigatórios:
        'gleba', 'num_titulo', 'num_lote' seguidos do datetime da geração (separados por '-').

        Caso algum dos campos esteja vazio, exibe mensagem de erro e retorna None.
        Atualiza o QLabel 'lbl_arquivo_padrao' com o nome formatado.
        """
        gleba = self.gleba.text().strip() if hasattr(self, 'gleba') else ""
        num_titulo = self.num_titulo.text().strip() if hasattr(self, 'num_titulo') else ""
        num_lote = self.num_lote.text().strip() if hasattr(self, 'num_lote') else ""

        # Verificação dos campos obrigatórios
        campos_vazios = []
        if not gleba:
            campos_vazios.append("Nome da Gleba ('gleba')")
        if not num_titulo:
            campos_vazios.append("Nº do Título ('num_titulo')")
        if not num_lote:
            campos_vazios.append("Nº do Lote ('num_lote')")

        if campos_vazios:
            lista_campos = "\n".join(f"• {campo}" for campo in campos_vazios)
            mensagem_erro = (
                f"Não é possível continuar. Os seguintes campos são obrigatórios e não podem estar vazios:\n\n"
                f"{lista_campos}\n\n"
                f"Por favor, preencha todos os campos obrigatórios antes de prosseguir."
            )
            QMessageBox.critical(self, "Campos Obrigatórios Vazios", mensagem_erro)

            # Define o foco no primeiro campo com pendência
            if not gleba and hasattr(self, 'gleba'):
                self.gleba.setFocus()
            elif not num_titulo and hasattr(self, 'num_titulo'):
                self.num_titulo.setFocus()
            elif not num_lote and hasattr(self, 'num_lote'):
                self.num_lote.setFocus()

            return None

        # Formata o timestamp com a data e hora atuais da geração
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_formatado = f"{gleba}-{num_titulo}-{num_lote}-{timestamp}"

        # Armazena o resultado na instância
        self.nome_padrao_do_arquivo = nome_formatado

        # Atualiza o QLabel 'lbl_arquivo_padrao' na interface
        if hasattr(self, 'lbl_arquivo_padrao'):
            self.lbl_arquivo_padrao.setText(nome_formatado)
            self.lbl_arquivo_padrao.setToolTip(nome_formatado)

        return nome_formatado

    def salvar_copia_pdf(self, caminho_txt, nome_padrao=None):
        """Salva uma cópia do arquivo PDF analisado no mesmo local de salvamento
        do arquivo .txt, utilizando o mesmo nome padrão ({nome_padrao}.pdf).

        Retorna a tupla (nome_pdf_original, nome_pdf_copiado, caminho_destino_pdf).
        """
        if not self.caminho_pdf or not os.path.isfile(self.caminho_pdf):
            return ("", "", None)

        nome_original = os.path.basename(self.caminho_pdf)

        pasta_destino = os.path.dirname(caminho_txt)
        if not nome_padrao:
            nome_padrao = os.path.splitext(os.path.basename(caminho_txt))[0]

        nome_copiado = f"{nome_padrao}.pdf"
        caminho_destino = os.path.join(pasta_destino, nome_copiado)

        try:
            # Efetua a cópia caso o arquivo original e o destino sejam caminhos distintos
            if os.path.abspath(self.caminho_pdf) != os.path.abspath(caminho_destino):
                shutil.copy2(self.caminho_pdf, caminho_destino)
            return (nome_original, nome_copiado, caminho_destino)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Aviso ao Copiar PDF",
                f"Ocorreu um erro ao tentar salvar uma cópia do PDF analisado:\n{str(e)}"
            )
            return (nome_original, "", None)

    def arquivos_finais(self):
        """Gera a pasta final com TXT, PDF e GPKG das camadas vetoriais."""
        nome_padrao = self.formatar_nome_padrao_do_arquivo()
        if not nome_padrao:
            return

        pasta_base = QFileDialog.getExistingDirectory(
            self,
            'Selecionar local dos arquivos finais',
            '',
        )
        if not pasta_base:
            return

        pasta_final = os.path.join(pasta_base, nome_padrao)
        os.makedirs(pasta_final, exist_ok=True)
        caminho_txt = os.path.join(pasta_final, f'{nome_padrao}.txt')
        caminho_gpkg = os.path.join(pasta_final, f'{nome_padrao}.gpkg')

        pdf_orig, pdf_cop, caminho_pdf_copiado = self.salvar_copia_pdf(
            caminho_txt,
            nome_padrao,
        )
        self.pdf_copiado = pdf_cop

        dados_titulo = [
            ('processo', self.processo.text().strip()
             if hasattr(self, 'processo') else ''),
            ('gleba', self.gleba.text().strip()
             if hasattr(self, 'gleba') else ''),
            ('num_titulo', self.num_titulo.text().strip()
             if hasattr(self, 'num_titulo') else ''),
            ('num_lote', self.num_lote.text().strip()
             if hasattr(self, 'num_lote') else ''),
            ('nome_lote', self.nome_lote.text().strip()
             if hasattr(self, 'nome_lote') else ''),
            ('data_titulo', self.data_titulo.date().toString('dd/MM/yyyy')
             if hasattr(self, 'data_titulo') else ''),
            ('titulado', self.titulado.text().strip()
             if hasattr(self, 'titulado') else ''),
            ('area', self.area.text().strip()
             if hasattr(self, 'area') else ''),
            ('uf', self.uf.text().strip() if hasattr(self, 'uf') else ''),
            ('municipio', self.municipio.text().strip()
             if hasattr(self, 'municipio') else ''),
            ('data_analise', self.data_analise.date().toString('dd/MM/yyyy')
             if hasattr(self, 'data_analise') else ''),
            ('chkbox_sigef', str(self.chkbox_sigef.isChecked())
             if hasattr(self, 'chkbox_sigef') else 'False'),
            ('planilha_status', self.planilha_status.currentText()
             if hasattr(self, 'planilha_status') else ''),
            ('obs', self.obs.toPlainText().strip()
             if hasattr(self, 'obs') else ''),
            ('pdf_original', pdf_orig),
            ('pdf_copiado', pdf_cop),
        ]
        crs_authid = 'EPSG:4674'
        if hasattr(self, 'mQgsProjectionSelectionWidget'):
            crs = self.mQgsProjectionSelectionWidget.crs()
            if crs.isValid() and crs.authid():
                crs_authid = crs.authid()

        try:
            with open(caminho_txt, 'w', encoding='utf-8') as arquivo:
                arquivo.write('[TITULO]\n')
                for chave, valor in dados_titulo:
                    arquivo.write(f'{chave} = {valor}\n')
                arquivo.write(f'\n[SRC]\ncrs_authid = {crs_authid}\n')
                for nome_secao, tabela_nome in [
                    ('TABELA_COORDENADAS', 'tbl_coordenanda'),
                    ('TABELA_AZIMUTE', 'tbl_azimute'),
                ]:
                    tabela = getattr(self, tabela_nome, None)
                    if tabela is None:
                        continue
                    arquivo.write(f'\n[{nome_secao}]\n')
                    for numero_linha in range(tabela.rowCount()):
                        valores = [
                            tabela.item(numero_linha, coluna).text()
                            if tabela.item(numero_linha, coluna) else ''
                            for coluna in range(tabela.columnCount())
                        ]
                        registro = json.dumps(valores, ensure_ascii=False)
                        arquivo.write(
                            f'linha_{numero_linha + 1} = {registro}\n'
                        )

            camadas = self.criar_camadas_coordenadas(adicionar_projeto=False)
            if not camadas:
                return

            transform_context = QgsProject.instance().transformContext()
            opcoes = QgsVectorFileWriter.SaveVectorOptions()
            opcoes.driverName = 'GPKG'
            opcoes.layerName = camadas[0].name()
            opcoes.actionOnExistingFile = (
                QgsVectorFileWriter.CreateOrOverwriteFile
            )
            resultado = QgsVectorFileWriter.writeAsVectorFormatV3(
                camadas[0], caminho_gpkg, transform_context, opcoes
            )
            erro = resultado[0]
            mensagem = resultado[1] if len(resultado) > 1 else ''
            if erro != QgsVectorFileWriter.NoError:
                raise RuntimeError(mensagem)

            for camada in camadas[1:]:
                opcoes.layerName = camada.name()
                opcoes.actionOnExistingFile = (
                    QgsVectorFileWriter.CreateOrOverwriteLayer
                )
                resultado = QgsVectorFileWriter.writeAsVectorFormatV3(
                    camada, caminho_gpkg, transform_context, opcoes
                )
                erro = resultado[0]
                mensagem = resultado[1] if len(resultado) > 1 else ''
                if erro != QgsVectorFileWriter.NoError:
                    raise RuntimeError(mensagem)

            camadas_finais = []
            estilos = {
                '_pto': os.path.join(
                    os.path.dirname(__file__),
                    'estilos',
                    'pto_estilo.qml',
                ),
                '_pol': os.path.join(
                    os.path.dirname(__file__),
                    'estilos',
                    'pol_estilo.qml',
                ),
                '_lna': os.path.join(
                    os.path.dirname(__file__),
                    'estilos',
                    'lna_estilo.qml',
                ),
            }
            for camada in camadas:
                caminho_camada = (
                    f'{caminho_gpkg}|layername={camada.name()}'
                )
                camada_final = QgsVectorLayer(
                    caminho_camada,
                    camada.name(),
                    'ogr',
                )
                if not camada_final.isValid():
                    raise RuntimeError(
                        f'Não foi possível carregar a camada {camada.name()}.'
                    )

                caminho_estilo = next(
                    (caminho for sufixo, caminho in estilos.items()
                     if camada.name().endswith(sufixo)),
                    None,
                )
                if caminho_estilo is None or not os.path.isfile(caminho_estilo):
                    raise RuntimeError(
                        f'Estilo QML não encontrado para {camada.name()}.'
                    )
                resultado_estilo = camada_final.loadNamedStyle(caminho_estilo)
                if isinstance(resultado_estilo, tuple):
                    indicadores = [
                        valor for valor in resultado_estilo
                        if isinstance(valor, bool)
                    ]
                    estilo_carregado = (
                        indicadores[-1] if indicadores else True
                    )
                else:
                    estilo_carregado = (
                        resultado_estilo is None
                        or resultado_estilo is True
                    )
                if not estilo_carregado:
                    raise RuntimeError(
                        f'Não foi possível aplicar o estilo a {camada.name()}.'
                    )
                camada_final.triggerRepaint()
                camadas_finais.append(camada_final)

            QgsProject.instance().addMapLayers(camadas_finais)
            if self.iface is not None:
                canvas = self.iface.mapCanvas()
                canvas.setExtent(camadas_finais[1].extent())
                canvas.refresh()

            QMessageBox.information(
                self,
                'Arquivos finais',
                f'Arquivos finais gerados em:\n{pasta_final}',
            )
        except Exception as erro:
            QMessageBox.critical(
                self,
                'Erro ao gerar arquivos finais',
                f'Não foi possível gerar os arquivos finais:\n{erro}',
            )

    def salvar_dados(self):
        """Coleta as informações dos campos do título, valida os campos obrigatórios,
        abre o diálogo de seleção de local com o 'nome_padrao_do_arquivo',
        salva uma cópia do PDF analisado no mesmo diretório
        e salva as informações em formato .txt na seção [TITULO].
        """
        # Atualiza obrigatoriamente o campo data_analise para a data atual do sistema a cada clique em salvar
        if hasattr(self, 'data_analise'):
            self.data_analise.setDate(QDate.currentDate())

        # Formata e valida o nome padrão do arquivo (garante gleba, num_titulo e num_lote preenchidos)
        nome_padrao = self.formatar_nome_padrao_do_arquivo()
        if not nome_padrao:
            return

        # Abre caixa de diálogo para seleção do local de salvamento
        nome_sugerido = f"{nome_padrao}.txt"
        caminho_arquivo, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Dados do Título",
            nome_sugerido,
            "Arquivos de Texto (*.txt);;Todos os Arquivos (*)"
        )

        if not caminho_arquivo:
            return

        # Garante a extensão .txt
        if not caminho_arquivo.lower().endswith(".txt"):
            caminho_arquivo += ".txt"

        # Salva uma cópia do PDF analisado no mesmo diretório usando o mesmo nome padrão
        pdf_orig, pdf_cop, caminho_pdf_copiado = self.salvar_copia_pdf(caminho_arquivo, nome_padrao)
        self.pdf_copiado = pdf_cop

        # Coleta os valores de todos os campos listados
        dados_titulo = [
            ("processo", self.processo.text().strip() if hasattr(self, "processo") else ""),
            ("gleba", self.gleba.text().strip() if hasattr(self, "gleba") else ""),
            ("num_titulo", self.num_titulo.text().strip() if hasattr(self, "num_titulo") else ""),
            ("num_lote", self.num_lote.text().strip() if hasattr(self, "num_lote") else ""),
            ("nome_lote", self.nome_lote.text().strip() if hasattr(self, "nome_lote") else ""),
            ("data_titulo", self.data_titulo.date().toString("dd/MM/yyyy") if hasattr(self, "data_titulo") else ""),
            ("titulado", self.titulado.text().strip() if hasattr(self, "titulado") else ""),
            ("area", self.area.text().strip() if hasattr(self, "area") else ""),
            ("uf", self.uf.text().strip() if hasattr(self, "uf") else ""),
            ("municipio", self.municipio.text().strip() if hasattr(self, "municipio") else ""),
            ("data_analise", self.data_analise.date().toString("dd/MM/yyyy") if hasattr(self, "data_analise") else ""),
            ("chkbox_sigef", str(self.chkbox_sigef.isChecked()) if hasattr(self, "chkbox_sigef") else "False"),
            ("planilha_status", self.planilha_status.currentText() if hasattr(self, "planilha_status") else ""),
            ("obs", self.obs.toPlainText().strip() if hasattr(self, "obs") else ""),
            ("pdf_original", pdf_orig),
            ("pdf_copiado", pdf_cop),
        ]

        crs_authid = "EPSG:4674"
        if hasattr(self, "mQgsProjectionSelectionWidget"):
            crs = self.mQgsProjectionSelectionWidget.crs()
            if crs.isValid() and crs.authid():
                crs_authid = crs.authid()

        # Salva o arquivo no formato .txt com as seções [TITULO] e [SRC]
        try:
            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                f.write("[TITULO]\n")
                for chave, valor in dados_titulo:
                    f.write(f"{chave} = {valor}\n")
                f.write("\n[SRC]\n")
                f.write(f"crs_authid = {crs_authid}\n")

                if hasattr(self, "tbl_coordenanda"):
                    f.write("\n[TABELA_COORDENADAS]\n")
                    tabela = self.tbl_coordenanda
                    for numero_linha in range(tabela.rowCount()):
                        valores_linha = [
                            tabela.item(numero_linha, coluna).text()
                            if tabela.item(numero_linha, coluna) else ""
                            for coluna in range(tabela.columnCount())
                        ]
                        registro = json.dumps(
                            valores_linha,
                            ensure_ascii=False,
                        )
                        f.write(f"linha_{numero_linha + 1} = {registro}\n")

                if hasattr(self, "tbl_azimute"):
                    f.write("\n[TABELA_AZIMUTE]\n")
                    tabela = self.tbl_azimute
                    for numero_linha in range(tabela.rowCount()):
                        valores_linha = [
                            tabela.item(numero_linha, coluna).text()
                            if tabela.item(numero_linha, coluna) else ""
                            for coluna in range(tabela.columnCount())
                        ]
                        registro = json.dumps(
                            valores_linha,
                            ensure_ascii=False,
                        )
                        f.write(f"linha_{numero_linha + 1} = {registro}\n")

            mensagem_sucesso = f"Dados salvos com sucesso!\n\nArquivo TXT: {caminho_arquivo}"
            if pdf_cop and caminho_pdf_copiado:
                mensagem_sucesso += f"\nCópia do PDF: {caminho_pdf_copiado}"

            QMessageBox.information(
                self,
                "Sucesso",
                mensagem_sucesso
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao Salvar",
                f"Ocorreu um erro ao tentar salvar o arquivo:\n{str(e)}"
            )

    def importar_dados(self):
        """Abre uma caixa de diálogo para selecionar um arquivo .txt gerado pelo plugin,
        lê as informações sob a seção [TITULO] e preenche os campos correspondentes do formulário.
        """
        caminho_arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Importar Dados do Título",
            "",
            "Arquivos de Texto (*.txt);;Todos os Arquivos (*)"
        )

        if not caminho_arquivo:
            return

        dados_titulo = {}
        dados_src = {}
        dados_coordenadas = []
        dados_azimute = []
        tem_secao_coordenadas = False
        tem_secao_azimute = False
        aba_importada = None
        secao_atual = None
        chave_atual = None

        try:
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                for line in f:
                    linha = line.rstrip("\r\n")
                    linha_strip = linha.strip()

                    # Identifica cabeçalho de seção (ex: [TITULO])
                    if linha_strip.startswith("[") and linha_strip.endswith("]"):
                        secao_atual = linha_strip[1:-1].strip().upper()
                        if secao_atual == "TABELA_COORDENADAS":
                            tem_secao_coordenadas = True
                            aba_importada = "coordenada"
                        elif secao_atual == "TABELA_AZIMUTE":
                            tem_secao_azimute = True
                            aba_importada = "azimute"
                        chave_atual = None
                        continue

                    if secao_atual in [
                        "TITULO",
                        "SRC",
                        "TABELA_COORDENADAS",
                        "TABELA_AZIMUTE",
                    ]:
                        if "=" in linha:
                            chave, valor = linha.split("=", 1)
                            chave_atual = chave.strip()
                            if secao_atual == "TITULO":
                                dados_titulo[chave_atual] = valor.strip()
                            elif secao_atual == "SRC":
                                dados_src[chave_atual] = valor.strip()
                            elif secao_atual == "TABELA_AZIMUTE":
                                dados_azimute.append(valor.strip())
                            else:
                                dados_coordenadas.append(valor.strip())
                        elif chave_atual == "obs":
                            # Continuação de observações com múltiplas linhas
                            dados_titulo["obs"] += "\n" + linha
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro de Leitura",
                f"Não foi possível ler o arquivo selecionado:\n{str(e)}"
            )
            return

        if not dados_titulo:
            QMessageBox.warning(
                self,
                "Aviso",
                "O arquivo selecionado não contém a seção [TITULO] ou está vazio."
            )
            return

        # Preenche campos de texto simples (QLineEdit)
        campos_texto = [
            "processo",
            "gleba",
            "num_titulo",
            "num_lote",
            "nome_lote",
            "titulado",
            "area",
            "uf",
            "municipio",
        ]
        for campo in campos_texto:
            if campo in dados_titulo and hasattr(self, campo):
                getattr(self, campo).setText(dados_titulo[campo])

        # Preenche campos de data (QDateEdit)
        for campo_data in ["data_titulo", "data_analise"]:
            if campo_data in dados_titulo and hasattr(self, campo_data):
                val_data = dados_titulo[campo_data]
                if val_data:
                    qdate = QDate.fromString(val_data, "dd/MM/yyyy")
                    if not qdate.isValid():
                        qdate = QDate.fromString(val_data, Qt.ISODate)
                    if qdate.isValid():
                        getattr(self, campo_data).setDate(qdate)

        # Preenche o checkbox do SIGEF (QCheckBox)
        if "chkbox_sigef" in dados_titulo and hasattr(self, "chkbox_sigef"):
            val_sigef = dados_titulo["chkbox_sigef"].strip().lower()
            self.chkbox_sigef.setChecked(val_sigef in ["true", "1", "sim", "yes"])

        # Preenche o status da planilha (QComboBox)
        if "planilha_status" in dados_titulo and hasattr(self, "planilha_status"):
            val_status = dados_titulo["planilha_status"]
            idx = self.planilha_status.findText(val_status)
            if idx >= 0:
                self.planilha_status.setCurrentIndex(idx)
            else:
                self.planilha_status.setCurrentText(val_status)

        # Preenche observações (QTextEdit)
        if "obs" in dados_titulo and hasattr(self, "obs"):
            self.obs.setPlainText(dados_titulo["obs"])

        # Reconstrói a tabela de coordenadas importada
        if tem_secao_coordenadas and hasattr(self, "tbl_coordenanda"):
            tabela = self.tbl_coordenanda
            tabela.setRowCount(0)
            for registro in dados_coordenadas:
                try:
                    valores_linha = json.loads(registro)
                except json.JSONDecodeError:
                    continue

                if not isinstance(valores_linha, list):
                    continue

                numero_linha = tabela.rowCount()
                tabela.insertRow(numero_linha)
                for coluna in range(tabela.columnCount()):
                    valor = (
                        valores_linha[coluna]
                        if coluna < len(valores_linha)
                        else ""
                    )
                    tabela.setItem(
                        numero_linha,
                        coluna,
                        QtWidgets.QTableWidgetItem(str(valor)),
                    )

        # Reconstrói a tabela de azimute importada
        if tem_secao_azimute and hasattr(self, "tbl_azimute"):
            tabela = self.tbl_azimute
            tabela.setRowCount(0)
            for registro in dados_azimute:
                try:
                    valores_linha = json.loads(registro)
                except json.JSONDecodeError:
                    continue

                if not isinstance(valores_linha, list):
                    continue

                numero_linha = tabela.rowCount()
                tabela.insertRow(numero_linha)
                for coluna in range(tabela.columnCount()):
                    valor = (
                        valores_linha[coluna]
                        if coluna < len(valores_linha)
                        else ""
                    )
                    tabela.setItem(
                        numero_linha,
                        coluna,
                        QtWidgets.QTableWidgetItem(str(valor)),
                    )

            if tabela.rowCount() > 0:
                item_vertice = tabela.item(0, 0)
                item_este = tabela.item(0, 1)
                item_norte = tabela.item(0, 2)
                self.vertice_ini_valor = (
                    item_vertice.text() if item_vertice else ""
                )
                self.coord_este_ini_valor = (
                    item_este.text() if item_este else ""
                )
                self.coord_norte_ini_valor = (
                    item_norte.text() if item_norte else ""
                )
                self.configurar_campos_azimute(True)
                if hasattr(self, "btn_add_vert_ini_az"):
                    self.btn_add_vert_ini_az.setEnabled(False)
                if hasattr(self, "btn_remove_vert_ini_az"):
                    self.btn_remove_vert_ini_az.setEnabled(True)

        self.atualizar_estado_abas_tabelas()

        # Atualiza o sistema de coordenadas salvo no arquivo
        crs_authid = dados_src.get("crs_authid", "EPSG:4674")
        if hasattr(self, "mQgsProjectionSelectionWidget"):
            crs = QgsCoordinateReferenceSystem(crs_authid)
            if crs.isValid():
                self.mQgsProjectionSelectionWidget.setCrs(crs)

        # Seleciona a aba correspondente à seção importada
        if aba_importada and hasattr(self, "tabWidget"):
            nome_aba = getattr(self, aba_importada, None)
            if nome_aba is not None:
                self.tabWidget.setCurrentWidget(nome_aba)

        # Atualiza a vinculação do PDF analisado se constar no arquivo importado
        pdf_orig = dados_titulo.get("pdf_original", "")
        pdf_cop = dados_titulo.get("pdf_copiado", "")
        self.pdf_copiado = pdf_cop
        if pdf_cop:
            pasta_txt = os.path.dirname(caminho_arquivo)
            caminho_pdf_junto = os.path.join(pasta_txt, pdf_cop)
            if os.path.isfile(caminho_pdf_junto):
                self.caminho_pdf = caminho_pdf_junto
                if hasattr(self, "lbl_arquivo"):
                    self.lbl_arquivo.setText(pdf_cop)
                    self.lbl_arquivo.setToolTip(caminho_pdf_junto)
            elif pdf_orig and hasattr(self, "lbl_arquivo"):
                self.lbl_arquivo.setText(pdf_orig)
        elif pdf_orig and hasattr(self, "lbl_arquivo"):
            self.lbl_arquivo.setText(pdf_orig)

        # Atualiza o identificador padrão do arquivo com base no arquivo importado
        nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
        self.nome_padrao_do_arquivo = nome_base
        if hasattr(self, "lbl_arquivo_padrao"):
            self.lbl_arquivo_padrao.setText(nome_base)
            self.lbl_arquivo_padrao.setToolTip(caminho_arquivo)

        QMessageBox.information(
            self,
            "Sucesso",
            f"Dados importados com sucesso!\n\nArquivo: {os.path.basename(caminho_arquivo)}"
        )

    def get_valores(self):
        """Método auxiliar para coletar os dados do formulário."""
        return {
            "processo": self.processo.text().strip() if hasattr(self, 'processo') else "",
            "gleba": self.gleba.text().strip() if hasattr(self, 'gleba') else "",
            "num_titulo": self.num_titulo.text().strip() if hasattr(self, 'num_titulo') else "",
            "num_lote": self.num_lote.text().strip() if hasattr(self, 'num_lote') else "",
            "nome_lote": self.nome_lote.text().strip() if hasattr(self, 'nome_lote') else "",
            "titulado": self.titulado.text().strip() if hasattr(self, 'titulado') else "",
            "area": self.area.text().strip() if hasattr(self, 'area') else "",
            "uf": self.uf.text().strip() if hasattr(self, 'uf') else "",
            "municipio": self.municipio.text().strip() if hasattr(self, 'municipio') else "",
            "caminho_pdf": self.caminho_pdf,
            "nome_padrao_do_arquivo": self.nome_padrao_do_arquivo,
            "pdf_original": os.path.basename(self.caminho_pdf) if self.caminho_pdf else "",
        }

