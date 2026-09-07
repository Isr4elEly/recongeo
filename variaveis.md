# Informações sobre o formulário do QT


## Botões (QPushButton)

- btn_abrir
- btn_abrir_pdf
- btn_dados_finais
- btn_salvar
- btn_vetor_temp
- btn_az_down_ln
- btn_az_recal_tabela
- btn_az_up_ln
- btn_add_vert_ini_az
- btn_remove_vert_ini_az
- btn_add_ln_az
- btn_remove_ln_az
- btn_add_ln_cor
- btn_remove_ln_cor
- btn_limp_form

## label (QLabel)

- lbl_area
- lbl_data_titulo
- lbl_data_analise
- lbl_obs
- lbl_municipio
- lbl_num_lote
- lbl_num_titulo
- lbl_nome_lote
- lbl_titulado
- lbl_uf
- lbl_arquivo
- lbl_processo
- lbl_gleba

## campos linha (QLineEdit)

- processo
- gleba
- num_titulo
- num_lote
- nome_lote
- titulado
- area
- uf
- municipio
- coord_este_ini
- coord_norte_ini
- vertice_ini
- graus
- minutos
- segundos
- distancia
- vertice_az
- confrontante_az
- num_lote_az
- vertice_cor
- este_cor
- norte_cor
- confrontante_cor
- lote_vizinho_cor

## Data (QDateEdit)

- data_titulo
- data_analise

## Check box (QCheckBox)

- chkbox_sigef

## campo de texto (QTextEdit)

- obs

## combobox (QComboBox)

- planilha_status

## abas (QTabWidget) (QWidget)

- azimute
- coordenadas

## tabelas (QTableWidget)

- tbl_azimute
- tbl_coordenada

crie as funções:

"""
def calc_azimute_decimal(self, graus, minutos, segundos):
    azimute_decimal = graus + (minutos / 60.0) + (segundos / 3600.0)
    return azimute_decimal

def calc_delta_este(self, azimute_decimal, distancia):
    delta_este = math.sin(math.radians(azimute_decimal)) * distancia
    return delta_este
    
def calc_delta_norte(self, azimute_decimal, distancia):
    delta_norte = math.cos(math.radians(azimute_decimal)) * distancia
    return delta_norte

def calcula_coodenada_seguinte(este_ini, norte_inicial, delta_este, delta_norte):
    este_pos = este_ini + delta_este
    norte_pos = norte_ini + delta_norte
    return este_pos, norte_pos
"""
o método disparado pelo "btn_add_ln_az" deve pegar as informações dos campos [graus, minutos, segundos, distancia, vertice_az, confrontante_az, num_lote_az] e calcular os campos azimute_decimal, delta_este, delta_norte utilizando as funções acima descritas e calcular as coordenadas com base na linha anterior da tabela e a função "calcula_coodenada_seguinte".

inclua na função do btn_add_ln_az a limpesa dos campos [graus, minutos, segundos, distancia, vertice_az, confrontante_az, num_lote_az] após o clique e mova o cursor para o campo graus para uma nova inclusão.

modifique o botão "btn_remove_ln_az" para iniciar desabilitado, ficando habilitado quando uma linha da "tbl_azimute" for selecionada, voltando a ficar desabilitado se a seleção for removida. Ao ser clicado, o "btn_remove_ln_az" deve apagar a linha selecionada e recalcular a linhas abaixo conforme descrito para os cálculos do "btn_add_ln_az" sem haver adição de nova linha na tabela.

seguindo a mesma lógica, o "btn_az_recal_tabela" deve ficar desabilitado, sendo habilitado com a seleção de uma linha da tabela, e aplicar o recalculo a linhas abaixo conforme descrito para os cálculos do "btn_add_ln_az" sem haver adição de nova linha na tabela.

com base na função que gera os arquivos temporários de ponto, linha e polígono, modifique para que possa gerar também com as informações da tabela "tbl_azimute" sendo que não poderá ser preenchido as duas tabelas ao mesmo tempo. Quando uma começar a ser alimentada a outra aba deve ser desabilitada.
