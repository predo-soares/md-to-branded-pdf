# Career Tools

Um espaço para guardar e evoluir skills e ferramentas próprias que ajudam na busca de vagas, pesquisa de empresas, avaliação de aderência e preparação de candidaturas.

## O que entra no repositório

- Skills autorais do Codex em `.agents/skills/`.
- Ferramentas reutilizáveis em `tools/`, organizadas por finalidade quando forem criadas.
- Esquemas, documentação e benchmarks reutilizáveis em `docs/`.
- Exemplos e fixtures sintéticos, sem informações pessoais ou dados de candidaturas reais.

## O que fica local

Currículos mestre, versões adaptadas a vagas, cartas específicas, PDFs, HTMLs de preview, capturas brutas de páginas e experimentos com dados de vagas ficam no checkout local e são ignorados pelo Git. Assim, o repositório guarda o processo e as ferramentas sem virar um arquivo de candidaturas pessoais.

A cópia local da skill Kami também é ignorada. Ela foi usada como referência durante a criação da skill própria `resume-studio`; este repositório usa e mantém apenas a implementação própria.

## Estrutura atual

```text
.agents/skills/resume-studio/  Skill autoral para currículos e cartas
docs/                         Planos e documentação reutilizável
tools/                        Reservado para ferramentas próprias
```

Os diretórios de ferramentas serão criados quando houver conteúdo para eles. Não há licença definida ainda.

## Resume Studio

A skill `.agents/skills/resume-studio/SKILL.md` documenta o fluxo Markdown → JSON validado → HTML canônico → PDF. Os documentos pessoais usados como entrada e as saídas geradas não são versionados. Para executar o builder, consulte a skill e instale as dependências listadas em `.agents/skills/resume-studio/requirements.txt`.
