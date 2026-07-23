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