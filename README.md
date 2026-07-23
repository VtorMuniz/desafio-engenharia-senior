# Data Product Lakehouse - Cooperativa NovaRota

Este repositório contém a solução do desafio técnico para Engenharia de Dados (Nível Sênior), focado em construir um produto de dados transacional e analítico utilizando Databricks, Delta Lake e arquitetura Medallion.

## 🚀 Como Executar o Projeto

A execução foi desenhada para ser modular e reproduzível. Para testar o pipeline ponta a ponta no workspace:

1. **Setup Inicial (Massa de Dados):**
   - Execute o notebook `src/config/generate_mock_data` para gerar os arquivos brutos (`clientes_cdc.csv`, `transacoes.csv`, etc.). Os dados gerados já contêm simulações de problemas reais (dados atrasados, duplicidade, SCD2 e CPFs nulos).

2. **Camada Bronze (Ingestão Incremental e Governança):**
   - Execute os notebooks da pasta `src/ingestion/`. Eles lerão os arquivos do volume e farão o *append* nas tabelas Delta Bronze, inferindo o schema (`mergeSchema=true`) e adicionando os metadados de rastreabilidade exigidos (ex: `hash_linha`, `_metadata.file_path`, `batch_id`).

3. **Camada Prata (SCD Tipo 2, MERGE e Qualidade):**
   - Execute os notebooks da pasta `src/silver/`. Aqui as regras de qualidade são aplicadas (registros inválidos vão para quarentena) e a dimensão histórica (SCD Tipo 2) é construída utilizando `MERGE` idempotente. A deduplicação é feita via `ROW_NUMBER`.

4. **Camada Ouro (Modelagem Analítica):**
   - Execute os notebooks da pasta `src/gold/`. Serão construídas a Fato de Transações (zerando o valor líquido de estornos) e as tabelas agregadas usando SQL Avançado (`LAG`, `NTILE`, CTEs) para consumo do negócio e modelos de Data Science.

## 📁 Estrutura do Repositório

- `src/`: Códigos PySpark modulares divididos pelas camadas (config, ingestion, silver, gold).
- `sql/`: Consultas de SQL Avançado exigidas no desafio (identificação de anomalias, segmentação).
- `docs/`: Documentações complementares, incluindo o **ADR (Decisões de Arquitetura)** detalhando estratégias de performance, Unity Catalog e Auto Loader.

## 🛠️ Tecnologias e Padrões Adotados
- **PySpark & Spark SQL:** Processamento distribuído e Window Functions.
- **Delta Lake:** Versionamento (Time Travel), idempotência e evolução de schema.
- **Unity Catalog:** Governança e controle de acesso.
- **Git Flow & Conventional Commits:** Controle de versão estruturado.

## 📸 Evidências de Execução

As evidências de execução e validação das regras de qualidade (testes unitários em PySpark bloqueando CPFs nulos na camada Silver) foram registradas e estão disponíveis no repositório.
* **Teste de Transformação (Silver):** `docs/evidencia_teste_silver.png` *(ou ajuste o caminho da pasta onde você salvou a imagem)*

---

## ⚖️ Trade-offs e Decisões de Arquitetura

Neste desafio, o foco foi demonstrar domínio sobre a arquitetura Medallion e engenharia de software aplicada a dados (Git Flow, versionamento e testes). Algumas escolhas foram feitas para balancear a entrega técnica em um ambiente de demonstração versus um cenário real de produção em larga escala:

**1. O que foi implementado (Escopo do Desafio):**
* **Carga Batch Simulada:** A ingestão de dados foi construída utilizando leitura estática para validar a lógica de transformação na camada Silver e as agregações analíticas na Gold de forma reprodutível.
* **Qualidade de Dados Local:** Implementação de testes baseados em PySpark (asserts nativos) simulando um ambiente de CI para validação de regras (ex: bloqueio de registros com CPF nulo).
* **Governança via Código:** Aplicação de regras de qualidade de dados de forma programática (PySpark) na camada Silver.

**2. O que ficou como Desenho/Conceito:**
* **Orquestração e Triggers:** O fluxo de dependência entre Bronze, Silver e Gold está modularizado logicamente, mas a orquestração oficial (via Databricks Workflows/Jobs ou Apache Airflow) foi documentada arquiteturalmente, sem agendamento ativo.

**3. O que seria feito em um Ambiente de Produção (Cenário Real):**
* **Ingestão Contínua (Databricks Auto Loader):** Em um ambiente produtivo, a camada Bronze utilizaria o Auto Loader (`cloudFiles`) para detectar novos arquivos no data lake de forma contínua e incremental, otimizando custos e latência em comparação ao batch tradicional.
* **Delta Live Tables (DLT):** A governança da camada Silver seria migrada para as *Expectations* do DLT (`@dlt.expect_or_drop`), permitindo monitoramento visual da qualidade, quarentena automática de dados ruins e linhagem nativa no Unity Catalog.
* **CI/CD Automatizado:** A esteira contaria com GitHub Actions ou Azure DevOps rodando os testes automatizados a cada *Pull Request* para a branch `develop`, além de realizar o *deploy* dos notebooks nos *workspaces* (Dev, QA, Prod).
