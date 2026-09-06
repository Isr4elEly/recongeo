# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ReconGeoDialog
                                 A QGIS plugin
 Plugin ReconGeo para QGIS com interface Qt5 editável via Qt Designer
 ***************************************************************************/
"""

import os
import shutil
from datetime import datetime
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QDate, QLocale, QUrl, Qt
from qgis.PyQt.QtGui import QDesktopServices, QDoubleValidator, QIntValidator, QValidator
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis import gui

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
    def __init__(self, parent=None):
        """Construtor da janela de diálogo.

        :param parent: Widget pai (normalmente a janela principal do QGIS iface.mainWindow()).
        """
        super(ReconGeoDialog, self).__init__(parent)
        # Configura e inicializa os componentes definidos no Qt Designer (.ui)
        self.setupUi(self)

        # Variável para armazenar o caminho completo do PDF selecionado
        self.caminho_pdf = None

        # Variável para armazenar o nome padrão formatado do arquivo
        self.nome_padrao_do_arquivo = None

        # Conecta o botão btn_abrir_pdf à função que seleciona e abre o PDF
        if hasattr(self, 'btn_abrir_pdf'):
            self.btn_abrir_pdf.clicked.connect(self.abrir_pdf)

        # Conecta o botão btn_salvar à função de salvar dados e btn_dados_finais ao nome padrão
        if hasattr(self, 'btn_salvar'):
            self.btn_salvar.clicked.connect(self.salvar_dados)

        if hasattr(self, 'btn_dados_finais'):
            self.btn_dados_finais.clicked.connect(self.formatar_nome_padrao_do_arquivo)

        # Conecta o botão btn_abrir à função de importar dados
        if hasattr(self, 'btn_abrir'):
            self.btn_abrir.clicked.connect(self.importar_dados)

        # Define a data atual do sistema como padrão para o campo data_analise
        if hasattr(self, 'data_analise'):
            self.data_analise.setDate(QDate.currentDate())

        # Configura os validadores float e int nos QLineEdit especificados
        self.configurar_validadores()

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

        # Salva o arquivo no formato .txt com a seção [TITULO]
        try:
            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                f.write("[TITULO]\n")
                for chave, valor in dados_titulo:
                    f.write(f"{chave} = {valor}\n")

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
                        chave_atual = None
                        continue

                    if secao_atual == "TITULO":
                        if "=" in linha:
                            chave, valor = linha.split("=", 1)
                            chave_atual = chave.strip()
                            dados_titulo[chave_atual] = valor.strip()
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

        # Atualiza a vinculação do PDF analisado se constar no arquivo importado
        pdf_orig = dados_titulo.get("pdf_original", "")
        pdf_cop = dados_titulo.get("pdf_copiado", "")
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

