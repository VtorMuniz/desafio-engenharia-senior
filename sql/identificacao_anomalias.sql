WITH perfil_cliente AS (
    SELECT 
        c.id_cliente,
        c.nome,
        c.cidade,
        c.segmento,
        SUM(f.valor_liquido) AS total_gasto,
        AVG(f.valor_liquido) AS ticket_medio
    FROM workspace.default.gold_fato_transacao f
    JOIN workspace.default.silver_cartoes cart ON f.id_cartao = cart.id_cartao
    JOIN workspace.default.silver_contas cont ON cart.id_conta = cont.id_conta
    JOIN workspace.default.silver_clientes c ON cont.id_cliente = c.id_cliente
    WHERE f.is_estornada = FALSE
    GROUP BY 1, 2, 3, 4
),

analise_comparativa AS (
    SELECT 
        *,
        -- Compara o ticket médio do cliente com o ticket médio da sua cidade e segmento
        AVG(ticket_medio) OVER (PARTITION BY cidade, segmento) AS ticket_medio_cidade_segmento,
        
        -- Segmentação usando NTILE (Divide os clientes em 4 grupos - Quartis)
        -- Quartil 1 são os que mais gastam, Quartil 4 os que menos gastam na sua região/segmento
        NTILE(4) OVER (PARTITION BY cidade, segmento ORDER BY total_gasto DESC) AS quartil_gasto_regional
    FROM perfil_cliente
)

SELECT 
    id_cliente,
    nome,
    cidade,
    segmento,
    total_gasto,
    ticket_medio,
    ticket_medio_cidade_segmento,
    quartil_gasto_regional,
    
    -- Regra Simples de Anomalia
    CASE 
        WHEN ticket_medio > (ticket_medio_cidade_segmento * 3) THEN 'Anomalia: Gasto 3x acima da média regional'
        ELSE 'Normal' 
    END AS alerta_comportamental
    
FROM analise_comparativa
ORDER BY cidade, quartil_gasto_regional;