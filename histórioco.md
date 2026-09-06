o campo "data_Analise" por padrão recebe a data atual do sistema, caso seja aberto um txt com dados salvos, o campo assume o valor salvo no arquivo, caso haja um novo clique no botão "btn_salvar", o campo DEVE se atualizado para a data atual.
4:33


O comportamento solicitado para o campo data_analise foi implementado em 
recongeo_dialog.py
:

Regras Aplicadas:
Padrão na Abertura:

No construtor (__init__), o campo data_analise é preenchido automaticamente com a data corrente do sistema:
python

if hasattr(self, 'data_analise'):
    self.data_analise.setDate(QDate.currentDate())
Na Importação de Arquivo (btn_abrir):

Ao importar um arquivo .txt gerado anteriormente, o campo assume exatamente o valor salvo no arquivo sob data_analise.
A Cada Novo Salvamento (btn_salvar):

A cada clique no botão btn_salvar, o campo data_analise é obrigatoriamente atualizado para a data atual do sistema antes de coletar as informações e salvar o arquivo:
python

# Em salvar_dados():
if hasattr(self, 'data_analise'):
    self.data_analise.setDate(QDate.currentDate())
Isso garante que tanto a interface visual quanto o novo .txt registrado reflitam com precisão a data do momento do salvamento.
As modificações foram validadas e já estão integradas ao plugin.

Walkthrough
4:33
crie uma função para salvar uma cópia do arquivo PDF anlisado no mesmo local de salvamento do arquivo txt usando o mesmo nome padrão. altere a função de criação do arquivo txt para guardar o nome do arquivo pdf original e o nome do pdf copiado. na seção [TITULO]
4:42


A função salvar_copia_pdf foi criada e a rotina salvar_dados foi atualizada em 
recongeo_dialog.py
.

O que foi implementado:
Função salvar_copia_pdf:

Salva uma cópia do arquivo PDF selecionado/analisado na mesma pasta escolhida pelo operador para o arquivo .txt.
Utiliza exatamente o mesmo nome padrão com a extensão .pdf (ex: Gleba_Sul-4567-15-20260906_044300.pdf).
Usa shutil.copy2 para manter a integridade e metadados do documento.
Registro dos Nomes na Seção [TITULO] do .txt:

O arquivo .txt gerado agora inclui os nomes de referência dos arquivos PDF:
pdf_original: Nome do arquivo PDF selecionado no computador do operador (ex: processo_original.pdf).
pdf_copiado: Nome do PDF copiado junto ao arquivo de dados (ex: Gleba_Sul-4567-15-20260906_044300.pdf).
Exemplo de saída no arquivo gerado:

text

[TITULO]
processo = 001/2024
gleba = Gleba Sul
num_titulo = 4567
num_lote = 15
nome_lote = Lote Primavera
data_titulo = 12/04/2022
titulado = Maria Oliveira
area = 85.5000
uf = PA
municipio = Marabá
data_analise = 06/09/2026
chkbox_sigef = True
planilha_status = Planilha Conforme
obs = Nenhuma ressalva encontrada.
pdf_original = processo_original.pdf
pdf_copiado = Gleba_Sul-4567-15-20260906_044300.pdf
Revinculação na Importação (importar_dados):

Ao importar o .txt pelo botão btn_abrir, o plugin verifica se o PDF copiado está presente na pasta do .txt e já reconecta automaticamente o arquivo e o QLabel lbl_arquivo, permitindo abrir o PDF copiado diretamente pelo botão Abrir PDF.
Código implementado em 
recongeo_dialog.py
:
python

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
E em salvar_dados():

python

        # Salva uma cópia do PDF analisado no mesmo diretório usando o mesmo nome padrão
        pdf_orig, pdf_cop, caminho_pdf_copiado = self.salvar_copia_pdf(caminho_arquivo, nome_padrao)
        dados_titulo = [
            # ... demais campos ...
            ("pdf_original", pdf_orig),
            ("pdf_copiado", pdf_cop),
        ]
As alterações foram validadas e testadas com sucesso no arquivo do plugin.

Walkthrough
4:42
crie uma função que colete as informações dos campos [vertice_cor, este_cor, norte_cor, confrontante_cor, lote_vizinho_cor] e adicione na tabela "tbl_coordenada". A fução é chamada pelo botão "btn_add_ln_cor" retornado o cursor para o campo "vertice_cor" após o clique. A ordem dos campos está na listagem fornecida.
4:55


4:55
This chat is archived.