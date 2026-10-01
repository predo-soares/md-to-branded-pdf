# Plano: benchmark de extração de uma vaga com agentes

## Objetivo

Comparar, usando exatamente a mesma vaga e o mesmo contrato de dados, a qualidade da extração produzida por:

1. busca padrão do Codex (`web__run`);
2. HTTP direto + HTML/JSON-LD;
3. Puppeteer;
4. Crawlee;
5. agent-browser;
6. Firecrawl;
7. Apify Actor/Crawlee.

O resultado deve mostrar qual abordagem é mais eficaz para o uso pessoal atual e qual oferece a melhor base para escalar depois.

## Escopo

O experimento parte de uma única URL pública de vaga fornecida pelo usuário. Cada alternativa deverá produzir:

- um registro normalizado em JSON;
- um arquivo Markdown legível;
- um arquivo XML equivalente;
- evidência suficiente para verificar de onde cada campo veio;
- métricas de tempo, custo aproximado, completude e necessidade de intervenção.

O JSON será o formato canônico. Markdown e XML serão renderizações do mesmo registro, para evitar comparar diferenças causadas apenas por templates.

## Contrato de dados

Todos os métodos tentarão preencher os mesmos campos:

```json
{
  "title": null,
  "company": null,
  "location": [],
  "employmentType": null,
  "workplaceType": null,
  "salary": null,
  "postedAt": null,
  "description": null,
  "responsibilities": [],
  "requirements": [],
  "niceToHave": [],
  "benefits": [],
  "applicationUrl": null,
  "sourceUrl": null,
  "sourceDomain": null,
  "retrievedAt": null,
  "extractionMethod": null,
  "confidence": null,
  "evidence": []
}
```

Campos ausentes devem permanecer `null` ou `[]`; nenhum método deve inventar informação. Quando houver ambiguidade, o resultado deve preservar o texto original e registrar uma observação em `evidence`.

## Protocolo experimental

### Fase 0 — Fixar o caso de teste

- Receber uma URL pública de vaga.
- Registrar data/hora, URL final após redirecionamentos e estado de autenticação.
- Confirmar que não serão usados dados privados, credenciais ou ações de candidatura.
- Salvar uma cópia do HTML ou Markdown bruto sempre que a ferramenta permitir.
- Definir uma pequena lista de campos esperados manualmente, que funcionará como referência de avaliação.

### Fase 1 — Busca padrão do Codex

- Fazer uma chamada de busca padrão com a URL e, se necessário, o nome da empresa/vaga.
- Avaliar se a busca encontra a página correta, apenas um snippet, uma versão indexada ou informações de terceiros.
- Extrair somente fatos sustentados pelo resultado retornado.
- Registrar limitações: cobertura parcial, conteúdo desatualizado, ausência de descrição completa e dependência de indexação.

Esta alternativa será avaliada como **descoberta e síntese**, não como substituta garantida de uma captura integral da página.

### Fase 2 — HTTP direto + JSON-LD

- Fazer `GET` da URL.
- Inspecionar status, redirecionamento, `robots.txt` e conteúdo recebido.
- Priorizar `application/ld+json` com tipo `JobPosting`.
- Complementar campos usando meta tags e seletores HTML estáveis.
- Salvar HTML bruto, JSON-LD encontrado e JSON normalizado.

Critério principal: verificar quanto da vaga já está disponível sem executar JavaScript.

### Fase 3 — Puppeteer

- Abrir a URL em um navegador controlado.
- Aguardar carregamento e estabilidade mínima do conteúdo.
- Capturar URL final, título, texto visível e HTML renderizado.
- Reutilizar a mesma lógica de JSON-LD/seletores da fase anterior.
- Não clicar em candidatura nem executar ações externas.

Critério principal: medir o ganho sobre HTTP puro em páginas dinâmicas e o custo adicional de execução.

### Fase 4 — Crawlee

- Implementar um crawler de uma única requisição usando o modo mais leve que funcionar.
- Começar por HTTP/Cheerio e trocar para PuppeteerCrawler apenas se necessário.
- Registrar retries, tempo, requests adicionais e erros.
- Produzir o mesmo JSON canônico e os mesmos arquivos de saída.

Critério principal: avaliar se Crawlee adiciona valor real para uma vaga isolada e quais capacidades já deixam o caminho pronto para múltiplas vagas.

### Fase 5 — agent-browser

- Pedir ao agente para abrir a URL, localizar os dados da vaga e retornar o contrato de dados.
- Registrar as ações realizadas, seletores ou referências usadas e qualquer decisão interpretativa.
- Repetir uma segunda vez, se possível, para observar variação do resultado.
- Separar claramente campos extraídos da página de inferências feitas pelo agente.

Critério principal: medir flexibilidade para páginas desconhecidas contra determinismo, repetibilidade e custo.

### Fase 6 — Firecrawl

- Executar scrape da URL em Markdown e, se disponível, em JSON baseado no schema.
- Comparar o Markdown retornado com o HTML bruto e com o JSON canônico.
- Usar interação somente se o scrape inicial não revelar o conteúdo.
- Registrar dependência de serviço, latência, créditos/custo e qualidade do conteúdo limpo.

Critério principal: medir a velocidade para chegar a um resultado útil com pouco código.

### Fase 7 — Apify Actor/Crawlee

- Empacotar a implementação Crawlee em um Actor mínimo.
- Passar a URL pelo input do Actor.
- Salvar o JSON no Dataset e os artefatos brutos no Key-value Store.
- Recuperar os resultados pela API.
- Registrar tempo de inicialização, duração, memória, custo e facilidade de agendamento.

Critério principal: avaliar a transição de execução local para execução recorrente e escalável.

## Métricas

Cada alternativa receberá uma avaliação de 0 a 5 para:

- completude dos campos;
- precisão em relação à página;
- preservação do texto original;
- repetibilidade;
- tempo total;
- custo direto;
- quantidade de código/configuração;
- necessidade de intervenção manual;
- tolerância a conteúdo dinâmico;
- facilidade de armazenar evidências.

Também serão registrados fatos objetivos:

- status HTTP;
- número de requests;
- duração;
- tamanho dos artefatos;
- erros e retries;
- se browser foi necessário;
- se houve conteúdo não acessível.

## Avaliação de qualidade

O resultado será comparado contra uma referência manual criada antes de analisar as saídas dos métodos. A comparação deve distinguir:

- campo correto;
- campo correto, mas incompleto;
- campo incorreto;
- campo não encontrado;
- inferência não sustentada.

Será dada atenção especial a descrição, requisitos, localização, modalidade de trabalho, salário e URL de candidatura, pois esses campos frequentemente aparecem em lugares diferentes da página.

## Artefatos esperados

Para cada método:

```text
docs/experiments/<slug-da-vaga>/<metodo>/raw.html
docs/experiments/<slug-da-vaga>/<metodo>/raw.json
docs/experiments/<slug-da-vaga>/<metodo>/job.json
docs/experiments/<slug-da-vaga>/<metodo>/job.md
docs/experiments/<slug-da-vaga>/<metodo>/job.xml
docs/experiments/<slug-da-vaga>/<metodo>/evidence.md
```

Também haverá um relatório final:

```text
docs/experiments/<slug-da-vaga>/comparison.md
```

## Hipótese inicial

Para uma vaga isolada, a melhor ordem provável é:

1. HTTP + JSON-LD;
2. Firecrawl, se for necessário obter rapidamente Markdown limpo;
3. Puppeteer como fallback controlado;
4. Crawlee como base quando houver mais de uma URL;
5. agent-browser para casos exploratórios ou difíceis;
6. Apify quando houver execução recorrente, fila, agendamento ou volume.

A hipótese não será tratada como conclusão: o benchmark deve permitir que a evidência altere essa ordem.

## Limites e cuidados

- Não fazer login ou candidatura.
- Não contornar controles de acesso, CAPTCHA ou bloqueios técnicos.
- Respeitar termos de uso, limites de requisição e `robots.txt` quando aplicável.
- Não considerar uma página de terceiros como fonte equivalente à página original.
- Não chamar uma alternativa de “mais precisa” sem conservar evidência verificável.

## Verificação

### Automatizada

- Validar cada `job.json` contra o schema.
- Verificar que Markdown e XML representam os mesmos valores do JSON.
- Comparar campos extraídos com a referência manual.
- Calcular métricas de completude e precisão.
- Registrar duração, erros e tamanho dos artefatos.

### Manual

- Conferir visualmente a página original e cada campo crítico.
- Verificar se a descrição não foi truncada ou misturada com navegação.
- Conferir se salário e modalidade não foram inferidos incorretamente.
- Avaliar legibilidade do Markdown e validade prática do XML.
- Revisar se as evidências permitem reproduzir a decisão.

## Próximo passo

Fornecer a URL da vaga. A execução começará pela captura da referência manual e pelas alternativas mais leves: busca padrão do Codex, HTTP/JSON-LD e Firecrawl; depois serão executados os fallbacks de navegador e as variantes Crawlee/Apify.
