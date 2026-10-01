# Plano: organizar os assets e introduzir `content.json` no Resume Studio

## Objetivo

Organizar os recursos visuais da skill em uma estrutura explícita e aproximar o fluxo de currículos da arquitetura da Kami: conteúdo estruturado e validado, template HTML único para o layout e PDF renderizado a partir do HTML final.

O formato aprovado do currículo da Trybe permanece como padrão visual imutável. O Markdown continua sendo a fonte editorial e factual; `content.json` será uma representação intermediária normalizada, gerada durante o build.

## Situação atual

- `assets/` contém três HTMLs no mesmo nível: `resume-template-ats.html` (template canônico), `cover-letter-template.html` e `resume-template.html` (layout antigo de duas colunas, sem uso pelo builder canônico).
- `scripts/build-resume.py` interpreta Markdown e monta o HTML diretamente em memória. Não há representação estruturada persistida nem validação de esquema.
- `scripts/render_html_pdf.py` já usa WeasyPrint para imprimir o HTML salvo; HTML e PDF compartilham o layout.
- `scripts/render-cover-letter.py` ainda desenha o PDF da carta diretamente com ReportLab. O template HTML de cover letter é usado por um gerador legado em `output/resume-studio/`.
- `SKILL.md` e alguns builders legados contêm caminhos dos templates atuais.
- Os currículos direcionados ficam em `resumes/targeted/`; essa pasta deve continuar contendo somente Markdown.

## Estrutura proposta

```text
.agents/skills/resume-studio/
  assets/
    templates/
      resume-ats.html
      cover-letter.html
    legacy/
      resume-two-column.html
  references/
    schemas/
      resume-content.schema.json
  scripts/
    build-resume.py
    parse_resume.py
    render_resume_html.py
    render_html_pdf.py
  requirements.txt
```

Não criar diretórios vazios para fontes, imagens ou diagramas. Adicioná-los quando houver recursos ativos que precisem deles. O template de duas colunas fica isolado como legado, nunca como opção padrão.

## Modelo de conteúdo

O parser normaliza o Markdown para um objeto versionado. A estrutura deve incluir:

- `schemaVersion` e `language`;
- identidade: nome, título e contatos;
- resumo;
- experiências ordenadas, com empresa, cargo, período/local, descrição opcional e bullets;
- experiência anterior agrupada, quando presente;
- formação, idiomas e competências.

O esquema deve permitir campos opcionais quando o Markdown não os fornece, preservar links e caracteres acentuados, aceitar os títulos de seção em português e inglês e rejeitar campos essenciais ausentes ou conteúdo de experiência malformado. Nenhum dado factual será inferido pelo parser.

O JSON será um artefato gerado dentro de `output/resume-studio/`, ao lado do HTML e PDF correspondentes. Não será colocado em `resumes/targeted/` nem editado como fonte independente. O Markdown segue sendo a origem das alterações editoriais.

## Fases

### 1. Inventário e migração dos assets — concluída

- Criar `assets/templates/` e mover para lá os templates ATS e de cover letter.
- Mover `resume-template.html` para `assets/legacy/` e documentar que não deve ser usado em novas saídas.
- Atualizar referências em `SKILL.md`, `build-resume.py` e nos geradores legados que ainda apontam para os caminhos antigos.
- Manter os nomes dos arquivos de saída e os Markdown direcionados inalterados.

### 2. Definir e documentar o formato intermediário — concluída

- Criar `references/schemas/resume-content.schema.json` no JSON Schema Draft 2020-12.
- Declarar `jsonschema` junto às dependências Python locais da skill; hoje nenhum validador de esquema está instalado. Manter WeasyPrint declarado ali também, com uma versão compatível com o renderer atual.
- Criar exemplos pequenos em português e inglês derivados de currículos existentes, sem inventar ou copiar novos fatos.
- Documentar o mapeamento entre a sintaxe Markdown atual e cada campo JSON, inclusive links, datas, descrição da empresa e grupo de experiência anterior.

### 3. Separar parsing, validação e apresentação — concluída

- Extrair a leitura do Markdown para `parse_resume.py`, que escreve o `content.json` normalizado.
- Validar o JSON com a biblioteca `jsonschema` contra o esquema antes de gerar qualquer HTML. Falhas devem apontar o campo e a origem Markdown que precisam de correção.
- Fazer `render_resume_html.py` consumir apenas o JSON validado e o template canônico; ele será responsável por escapar conteúdo, preencher placeholders e gerar as seções.
- Manter `build-resume.py` como orquestrador e preservar a interface atual `INPUT.md OUTPUT.html OUTPUT.pdf`.
- O orquestrador grava o JSON intermediário em `OUTPUT.content.json`, o HTML em `OUTPUT.html` e, por fim, renderiza esse HTML em `OUTPUT.pdf` com WeasyPrint.

### 4. Atualizar o contrato da skill — concluída

- Documentar a cadeia Markdown → JSON validado → HTML canônico → PDF do HTML.
- Explicar que o Markdown é a fonte factual, o JSON é intermediário gerado, o template controla o visual e WeasyPrint imprime o HTML final.
- Registrar a organização de `assets/templates`, `assets/legacy` e `references/schemas`.
- Manter explícita a proibição de usar Kami como ferramenta, dependência ou fonte de templates/estilos.
- Preservar o fluxo de cover letter atual nesta mudança, apenas atualizando o caminho do template. A eventual migração da carta para HTML → PDF será uma decisão separada.

### 5. Migrar e validar os currículos existentes — concluída

- Gerar novamente os currículos direcionados em inglês e português com o novo pipeline.
- Comparar a saída do iFood e da Trybe com os PDFs aprovados: duas páginas A4, hierarquia, tipografia, alinhamentos, cabeçalhos de experiência em uma linha e skills no final.
- Conferir texto extraído para confirmar empresas, cargos, períodos, contatos e bullets, sem placeholders.
- Confirmar que a edição do HTML final altera o PDF renderizado, demonstrando que não existe um segundo layout de PDF.
- Atualizar ou retirar imagens antigas de prévia que possam representar PDFs anteriores.

## Critérios de aceite

- Todos os templates ativos ficam em `assets/templates/`; o template antigo está claramente isolado como legado.
- `resumes/targeted/` continua contendo somente Markdown.
- O build produz um `content.json` válido, um HTML sem placeholders e um PDF a partir desse HTML.
- Currículos em português e inglês passam pelo mesmo pipeline e mantêm o conteúdo suportado.
- O PDF do iFood preserva o formato aprovado e continua com duas páginas A4.
- A documentação não descreve ReportLab como renderer de currículo.

## Verificação automatizada

- Executar o builder com um currículo em português e outro em inglês.
- Validar ambos os sidecars com o JSON Schema.
- Conferir número de páginas e tamanho A4 com `pdfinfo`.
- Extrair o texto com `pdftotext` e verificar nomes das seções, empresas, cargos, períodos e ausência de placeholders.
- Executar compilação/sintaxe dos scripts Python.

Resultado: os exemplos pt-BR/en e os sidecars iFood/Trybe passaram no validador Draft 2020-12. Ambos os PDFs foram gerados novamente com duas páginas A4; texto extraído e inspeção visual confirmaram conteúdo e hierarquia. `py_compile` passou nos três scripts do pipeline. A prévia via navegador Codex não foi aberta neste ambiente; o próprio PDF produzido a partir do HTML foi inspecionado página a página.

## Verificação manual

- Renderizar e inspecionar todas as páginas dos currículos Trybe e iFood.
- Comparar o iFood com o PDF aprovado em margens, cabeçalho, resumo, experiência, quebras de página e seção final de competências.
- Conferir o HTML no navegador para garantir que a prévia e o PDF têm o mesmo layout.

## Fora de escopo

- Alterar o design aprovado ou a hierarquia das seções do currículo.
- Reescrever os currículos mestre ou inventar novos fatos.
- Migrar o PDF da cover letter de ReportLab para HTML → PDF.
- Replicar o conjunto amplo de ferramentas, fontes, diagramas e verificadores da Kami; adotar apenas a organização e a separação de responsabilidades que atendem a esta skill.
- Introduzir uma framework geral de documentos; as dependências ficam limitadas a WeasyPrint e validação JSON Schema.
