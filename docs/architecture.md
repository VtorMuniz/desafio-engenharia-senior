# Arquitetura e Decisões Técnicas (ADR)

Este documento detalha as decisões arquiteturais, estratégias de performance e governança adotadas para o Data Product Lakehouse da Cooperativa NovaRota.

## 1. Estratégia de Performance e Armazenamento
- **Evolução de Particionamento e Clustering:** Para otimizar a leitura na Camada Ouro (especialmente na `gold_fato_transacao` e `gold_cliente_mes`), a estratégia recomendada em produção é a utilização do **Liquid Clustering** do Databricks, substituindo o particionamento estático tradicional e o ZORDER. O Liquid Clustering adapta dinamicamente o layout dos dados à medida que o volume cresce, evitando distorções (data skew).
- **Prevenção de Small Files:** Para evitar o problema de arquivos pequenos gerados pela ingestão contínua, ativamos o conceito das propriedades `delta.autoOptimize.optimizeWrite = true` e `delta.autoOptimize.autoCompact = true`. Adicionalmente, um job de manutenção executará o comando `OPTIMIZE` seguido de `VACUUM` (retendo 7 dias de histórico) para desfragmentação física.

## 2. Ingestão e Lógica Incremental
- **Auto Loader vs Lotes Temporais:** O pipeline simula cargas incrementais de forma idempotente via parâmetro `batch_id`. Em um ambiente produtivo definitivo, a Camada Bronze seria orquestrada utilizando **Databricks Auto Loader (cloudFiles)**. O Auto Loader gerencia nativamente a descoberta de novos arquivos no bucket via serviços de notificação e RocksDB, eliminando a necessidade de listar o storage inteiro a cada execução, garantindo escala barata.
- **Evolução de Schema:** A Bronze utiliza a flag `mergeSchema = true`. Caso a origem insira colunas não mapeadas nos arquivos, o Delta Lake fará a evolução segura do schema sem quebrar o pipeline.

## 3. Governança e Unity Catalog
A governança de dados utiliza o Unity Catalog com controle de acesso baseado em funções (RBAC) e separação lógica em 3-tier namespaces:
- **Catálogo:** Criação de um catálogo dedicado para o domínio.
- **Schemas:** Segregação clara das camadas `bronze`, `silver` e `gold`.
- **Permissões:** O uso de funções legadas (como `input_file_name()`) foi substituído por `_metadata.file_path` para garantir compatibilidade nativa e segura com o Unity Catalog.

## 4. Operação e Observabilidade
- **Orquestração:** O pipeline será agendado através do **Databricks Workflows** utilizando Job Clusters dinâmicos (para redução de custos em relação ao uso de clusters interativos).
- **Qualidade de Dados:** A qualidade é garantida programaticamente na Camada Prata. Registros que ferem contratos fortes (ex: `cpf` nulo) são bloqueados e direcionados para tabelas de quarentena. Em uma evolução futura, as expectativas do **Delta Live Tables (DLT)** poderiam ser introduzidas para barrar, alertar ou dropar registros com base em regras de negócio em tempo real.