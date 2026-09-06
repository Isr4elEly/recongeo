# ReconGeo - Plugin para QGIS com Interface Qt5

Plugin base desenvolvido para o **QGIS 3**, projetado para permitir edição visual e manual de janelas diretamente no **Qt Designer** sem necessidade de compilação intermediária com `pyuic5`.

---

## 📁 Estrutura de Arquivos

```text
recongeo/
├── __init__.py                # Ponto de entrada do QGIS (função classFactory)
├── icon.png                   # Ícone do plugin na barra de ferramentas e menu
├── metadata.txt               # Metadados do plugin lidos pelo QGIS
├── recongeo.py                # Lógica principal do plugin (ciclo de vida e ações)
├── recongeo_dialog.py         # Classe Python do diálogo (carrega dinamicamente o .ui)
├── recongeo_dialog_base.ui    # Arquivo de interface XML editável no Qt Designer
└── README.md                  # Este guia
```

---

## 🎨 Como Editar a Janela no Qt Designer

O arquivo [recongeo_dialog_base.ui](recongeo_dialog_base.ui) é um arquivo nativo do Qt Designer.

1. Abra o **Qt Designer** no seu sistema:
   ```bash
   designer recongeo_dialog_base.ui
   ```
   *(Ou abra o Qt Designer pelo menu de aplicativos e vá em `Arquivo -> Abrir`)*

2. No Qt Designer você pode:
   - Adicionar novos botões (`QPushButton`), caixas de seleção (`QComboBox`, `QCheckBox`), campos de texto (`QLineEdit`, `QSpinBox`), etc.
   - Definir o `objectName` de cada elemento (ex: `meuBotao`, `comboCamadas`).
   - Salvar as alterações (`Ctrl + S`).

3. **Acesso aos novos widgets no Python**:
   - Graças ao uso de `uic.loadUiType` no [recongeo_dialog.py](recongeo_dialog.py), qualquer widget adicionado com um `objectName` estará imediatamente disponível em `self.<objectName>`.
   - Por exemplo, se você adicionar um botão com `objectName="btnProcessar"`, no método `__init__` do `ReconGeoDialog` você pode simplesmente fazer:
     ```python
     self.btnProcessar.clicked.connect(self.sua_funcao)
     ```

---

## 🚀 Como Instalar e Testar no QGIS

### 1. Criar Link Simbólico para a pasta de plugins do QGIS

Para não precisar copiar os arquivos toda vez que fizer uma alteração, crie um link simbólico apontando para a pasta de plugins do seu perfil no QGIS:

```bash
# Para Linux:
mkdir -p ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
ln -s "/home/isr/Documentos/arquivos/recongeo" ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/recongeo
```

### 2. Ativar o Plugin no QGIS

1. Abra o **QGIS**.
2. Vá no menu superior: **Complementos (Plugins) -> Gerenciar e Instalar Complementos...**
3. Na aba **Instalados**, marque a caixa de seleção ao lado de **ReconGeo**.
4. O ícone do plugin aparecerá na barra de ferramentas e também no menu **Complementos -> ReconGeo -> Abrir ReconGeo**.

---

## ⚡ Dica de Produtividade: Plugin Reloader

Durante o desenvolvimento, instale o complemento **Plugin Reloader** diretamente pelo Gerenciador de Complementos do QGIS:
- Com ele, ao alterar o código Python ou salvar o `.ui` no Qt Designer, basta pressionar a tecla de atalho configurada (ou clicar no ícone do Plugin Reloader) para recarregar o plugin instantaneamente, sem precisar fechar e reabrir o QGIS!
