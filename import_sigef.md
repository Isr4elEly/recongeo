# Definições de metodo para importação de dados do sigef

- a função python deve abir uma janela de diálogo para importar um arquivo .csv;
- as seguintes colunas devem ser mapeadas: 
    - DO_VERTICE;
    - AO_VERTICE;
    - CONFRONTANTE_DESC;
    - GEOMETRIA_WKT;
- os dados contidos na coluna "GEOMETRIA_WKT" possui dois pares de coordendas formando WKT formando um seguimento de reta conforme o exemplo: `LINESTRING (-59.1105202722520815 -3.9039623803234602, -59.1064075024132123 -3.9118177033262942)` sendo `este` e `norte` da coluna "DO_VERTICE"  e o par seguinte  é `este` e `norte` da coluna "AO_VERTICE". A função deve separar os dados este e norte de cada coluna;
- a função deve montar a tabela "tbl_coordenada" com os dados coletados no arquivo csv;
- a função deve seguir as seguintes correlações entre as colunas do CSV e as colunas da "tbl_coordenada":
    - "DO_VERTICE"    ->    Vértice
    - o `este` da coluna "DO_VERTICE"    -> Este
    - o `norte` da coluna "DO_VERTICE"    -> Norte
    - "CONFRONTANTE_DESC"   -> Confrontante
- todo o procedimento deve ser chamado pelo botão "btn_sigef_import";