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

## 🧪 Execução dos Testes Automatizados (CI/CD Ready)

Os testes unitários e de transformação foram refatorados para **não dependerem do contexto interativo do notebook** (variáveis globais `spark` ou `display`). A suíte agora utiliza `pytest` e fixtures de `SparkSession` isoladas, garantindo que possam ser executados localmente ou coletados por runners em esteiras de CI/CD.

A cobertura inclui as principais regras de negócio da camada Silver e Gold:
*   Filtro de CPFs inválidos.
*   Deduplicação via `ROW_NUMBER`.
*   Zeragem de valor líquido para estornos.
*   Point-in-time join para controle de vigência de cartões (SCD Tipo 2).
*   Exclusão de cartões cancelados nas agregações mensais.

**Como executar localmente ou via pipeline CI:**
```bash
pip install pytest
python -m pytest src/tests/ -v
Nota para execução via Notebook no Databricks:
Devido a restrições do sistema de arquivos virtualizado do Workspace (que impede a criação de pastas de cache __pycache__), caso deseje validar a suíte interativamente via notebook, utilize os parâmetros de inibição de disco:

Python
import pytest
import sys
sys.dont_write_bytecode = True
pytest.main(["src/tests/test_transformations.py", "-v", "-p", "no:cacheprovider", "--assert=plain"])
📁 Estrutura do Repositório
src/: Códigos PySpark modulares divididos pelas camadas (config, ingestion, silver, gold, tests).

sql/: Consultas de SQL Avançado exigidas no desafio (identificação de anomalias, segmentação).

docs/: Documentações complementares, incluindo o ADR (Decisões de Arquitetura) e evidências de execução.

🛠️ Tecnologias e Padrões Adotados
PySpark & Spark SQL: Processamento distribuído e Window Functions.

Delta Lake: Versionamento (Time Travel), idempotência e evolução de schema.

Unity Catalog: Governança e controle de acesso.

Git Flow & Conventional Commits: Controle de versão estruturado e semântico.

📸 Evidências de Execução
As evidências de execução da suíte completa de testes de qualidade rodando de forma isolada na memória, além de outras validações estruturais, foram salvas no repositório:

Execução Pytest (100% Passed): docs/evidencias/testes_pytest_passando.png

⚖️ Trade-offs e Decisões de Arquitetura
Neste desafio, o foco foi demonstrar domínio sobre a arquitetura Medallion e engenharia de software aplicada a dados (Git Flow, versionamento estruturado e testes unitários independentes). Algumas escolhas foram feitas para balancear a entrega técnica em um ambiente de demonstração versus um cenário real de produção em larga escala:

1. O que foi implementado (Escopo do Desafio):

Carga Batch Simulada: A ingestão de dados foi construída utilizando leitura estática para validar a lógica de transformação na camada Silver e as agregações analíticas na Gold de forma reprodutível.

Governança e Testes: Aplicação de regras de qualidade de dados de forma programática na camada Silver, validadas por uma suíte de testes em pytest pronta para CI/CD.

2. O que ficou como Desenho/Conceito:

Orquestração e Triggers: O fluxo de dependência entre Bronze, Silver e Gold está modularizado logicamente, mas a orquestração oficial (via Databricks Workflows/Jobs ou Apache Airflow) foi documentada arquiteturalmente, sem agendamento ativo.

3. O que seria feito em um Ambiente de Produção (Cenário Real):

Ingestão Contínua (Databricks Auto Loader): Em um ambiente produtivo, a camada Bronze utilizaria o Auto Loader (cloudFiles) para detectar novos arquivos no data lake de forma contínua e incremental, otimizando custos e latência em comparação ao batch tradicional.

Delta Live Tables (DLT): A governança da camada Silver poderia ser expandida para as Expectations do DLT (@dlt.expect_or_drop), permitindo monitoramento visual da qualidade, quarentena automática de dados ruins e linhagem nativa no Unity Catalog.