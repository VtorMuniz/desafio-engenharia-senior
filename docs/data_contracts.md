# 📄 Contratos de Dados (Data Contracts)

Este documento define os contratos de dados para todas as fontes ingeridas no pipeline, estabelecendo esquemas esperados, chaves primárias, regras de obrigatoriedade e os critérios de validação que disparam o envio para a **Quarentena**.

---

## 1. Clientes (`clientes_cdc`)
* **Camada Bronze / Silver:** `bronze_clientes` / `silver_clientes` (SCD Tipo 2)
* **Chave Primária / Natural:** `id_cliente`

### Schema Esperado & Regras:
| Campo | Tipo | Nulidade / Obrigatório | Descrição / Regra de Qualidade |
| :--- | :--- | :--- | :--- |
| `id_cliente` | Long / Int | `NOT NULL` | Identificador único do cliente. |
| `cpf` | String | `NOT NULL` | **Regra de Quarentena:** Se `cpf IS NULL`, o registro é rejeitado e enviado para `quarentena_clientes`. |
| `nome` | String | `NULLABLE` | Nome completo do cliente. |
| `renda` | Double | `NULLABLE` | Renda mensal declarada. |
| `segmento` | String | `NULLABLE` | Segmento de atendimento (ex: Mass, VIP, Black). |
| `data_atualizacao`| Timestamp | `NOT NULL` | Data da última alteração cadastral (usada no SCD2). |

---

## 2. Contas (`contas_cdc`)
* **Camada Bronze / Silver:** `bronze_contas` / `silver_contas` (SCD Tipo 2)
* **Chave Primária / Natural:** `id_conta`

### Schema Esperado & Regras:
| Campo | Tipo | Nulidade / Obrigatório | Descrição / Regra de Qualidade |
| :--- | :--- | :--- | :--- |
| `id_conta` | Long / Int | `NOT NULL` | Identificador único da conta. |
| `id_cliente` | Long / Int | `NOT NULL` | **Regra de Quarentena / Órfão:** Se `id_cliente` não existir na tabela válida de clientes, é capturado via `left_anti` e enviado para quarentena de órfãos. |
| `tipo_conta` | String | `NOT NULL` | Tipo da conta (ex: Corrente, Poupança). |
| `status_conta` | String | `NOT NULL` | Status atual (ex: Ativa, Bloqueada, Cancelada). |
| `data_atualizacao`| Timestamp | `NOT NULL` | Data da última atualização de status/tipo. |

---

## 3. Cartões (`cartoes_cdc`)
* **Camada Bronze / Silver:** `bronze_cartoes` / `silver_cartoes` (SCD Tipo 2)
* **Chave Primária / Natural:** `id_cartao`

### Schema Esperado & Regras:
| Campo | Tipo | Nulidade / Obrigatório | Descrição / Regra de Qualidade |
| :--- | :--- | :--- | :--- |
| `id_cartao` | Long / Int | `NOT NULL` | Identificador único do cartão. |
| `id_conta` | Long / Int | `NOT NULL` | **Regra de Quarentena 1:** Se `id_conta IS NULL` ou for órfão de conta ativa, vai para `quarentena_cartoes`. |
| `limite` | Double | `NOT NULL` | **Regra de Quarentena 2:** Se `limite <= 0`, vai para `quarentena_cartoes`. |
| `status_cartao`| String | `NOT NULL` | Status atual do plástico. |
| `data_atualizacao`| Timestamp | `NOT NULL` | Data da última alteração de limite/status. |

---

## 4. Transações (`transacoes`)
* **Camada Bronze / Silver:** `bronze_transacoes` / `silver_transacoes` (Append-only / Fato)
* **Chave Primária / Natural:** `id_transacao`

### Schema Esperado & Regras:
| Campo | Tipo | Nulidade / Obrigatório | Descrição / Regra de Qualidade |
| :--- | :--- | :--- | :--- |
| `id_transacao`| String | `NOT NULL` | Identificador único da transação. |
| `id_cartao` | Long / Int | `NOT NULL` | **Regra de Quarentena 1:** Se `id_cartao IS NULL` ou órfão de cartão válido, vai para quarentena. |
| `valor` | Double | `NOT NULL` | **Regra de Quarentena 2:** Se `valor <= 0`, vai para `quarentena_transacoes`. |
| `estabelecimento`| String | `NULLABLE` | Nome do estabelecimento comercial. |
| `data_transacao`| Timestamp | `NOT NULL` | Momento em que a transação ocorreu. **Tratamento de Dados Atrasados:** Dados retroativos (ex: 150 dias no passado) são mantidos na Silver e processados na Gold respeitando o mês de referência original (`ano_mes_referencia`) via recálculo particionado. |

---

## 5. Eventos de Risco (`eventos_risco`)
* **Camada Bronze / Silver:** `bronze_eventos_risco` / `silver_eventos_risco`
* **Chave Primária / Natural:** `id_evento`

### Schema Esperado & Regras:
| Campo | Tipo | Nulidade / Obrigatório | Descrição / Regra de Qualidade |
| :--- | :--- | :--- | :--- |
| `id_evento` | String | `NOT NULL` | Identificador único do alerta/evento de risco. |
| `id_transacao`| String | `NOT NULL` | **Regra de Quarentena / Órfão:** Se `id_transacao` não existir na base de transações válidas (`left_anti`), é direcionado para quarentena. |
| `tipo_risco` | String | `NOT NULL` | Classificação da suspeita de fraude. |
| `score_risco` | Double | `NULLABLE` | Pontuação de criticidade atribuída pelo motor. |

---

## 6. Estornos (`estornos`)
* **Camada Bronze / Silver:** `bronze_estornos` / `silver_estornos`
* **Chave Primária / Natural:** `id_estorno`

### Schema Esperado & Regras:
| Campo | Tipo | Nulidade / Obrigatório | Descrição / Regra de Qualidade |
| :--- | :--- | :--- | :--- |
| `id_estorno` | String | `NOT NULL` | Identificador único do estorno. |
| `id_transacao`| String | `NOT NULL` | **Regra de Quarentena / Órfão:** Se `id_transacao IS NULL` ou transação pai ausente (validado via `aplicar_quarentena_orfao`), vai para `quarentena_estornos`. |
| `valor_estorno`| Double | `NOT NULL` | Valor financeiro devolvido ao cliente. |
| `motivo` | String | `NULLABLE` | Justificativa operacional para o estorno. |

---

## 7. Políticas de Integridade Referencial e Dados Atrasados (Late-Arriving Data)
* **Integridade Referencial por Órfãos:** Utilização de `left_anti` joins centralizados no módulo de quarentena (`quarantine.py`) para isolar registros filhos que chegam sem a respectiva chave pai válida, impedindo nulos silenciosos nas camadas analíticas.
* **Reprocessamento Histórico:** Na camada Gold, as agregações mensais (`gold_cliente_mes`) utilizam o `DATE_TRUNC` baseado no campo `data_transacao` em vez da data de ingestão. Isso garante que a chegada de dados atrasados atualize de forma estável e correta a competência de origem.