-- =====================================================================
-- ANÁLISE COM FIRST_VALUE E LAST_VALUE
-- =====================================================================

WITH transacoes_com_cliente AS (
    SELECT 
        c.id_cliente,
        t.id_transacao,
        t.data_transacao,
        t.estabelecimento,
        t.valor
    FROM workspace.default.silver_transacoes t
    INNER JOIN workspace.default.silver_cartoes cart ON t.id_cartao = cart.id_cartao
    INNER JOIN workspace.default.silver_contas conta ON cart.id_conta = conta.id_conta
    INNER JOIN workspace.default.silver_clientes c ON conta.id_cliente = c.id_cliente
    WHERE c.is_active = true
),
transacoes_ordenadas AS (
    SELECT 
        id_cliente,
        id_transacao,
        data_transacao,
        estabelecimento,
        valor,
        -- Identifica a primeira transação do cliente no histórico global
        FIRST_VALUE(id_transacao) OVER (
            PARTITION BY id_cliente 
            ORDER BY data_transacao ASC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS primeira_transacao_id,
        
        FIRST_VALUE(data_transacao) OVER (
            PARTITION BY id_cliente 
            ORDER BY data_transacao ASC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS data_primeira_transacao,

        -- Identifica o último estabelecimento visitado pelo cliente
        LAST_VALUE(estabelecimento) OVER (
            PARTITION BY id_cliente 
            ORDER BY data_transacao ASC 
            ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
        ) AS ultimo_estabelecimento_visitado
    FROM transacoes_com_cliente
)
SELECT DISTINCT
    id_cliente,
    primeira_transacao_id,
    data_primeira_transacao,
    ultimo_estabelecimento_visitado
FROM transacoes_ordenadas
ORDER BY id_cliente;