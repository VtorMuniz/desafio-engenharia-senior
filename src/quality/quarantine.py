from pyspark.sql import DataFrame
import pyspark.sql.functions as F

def aplicar_quarentena(df: DataFrame, regra_invalida, motivo_erro: str):
    """
    Separa um DataFrame em dois com base em uma regra de qualidade:
    - df_validos: registros que passam na regra (vão para a camada Silver).
    - df_quarentena: registros que falharam, enriquecidos com metadados de auditoria.
    """
    df_marcado = df.withColumn(
        "motivo_rejeicao", 
        F.when(regra_invalida, F.lit(motivo_erro)).otherwise(F.lit(None))
    ).withColumn(
        "data_quarentena", 
        F.current_timestamp()
    )
    
    df_quarentena = df_marcado.filter(F.col("motivo_rejeicao").isNotNull())
    df_validos = df_marcado.filter(F.col("motivo_rejeicao").isNull()).drop("motivo_rejeicao", "data_quarentena")
    
    return df_validos, df_quarentena

def aplicar_quarentena_orfao(df_filho: DataFrame, df_pai: DataFrame, coluna_fk: str, motivo_erro: str):
    """
    Identifica registros órfãos usando LEFT ANTI JOIN entre a entidade filha e a entidade pai,
    enviando-os para a quarentena com metadados de auditoria e mantendo os válidos via INNER JOIN.
    """
    # Isola apenas as chaves primárias distintas da tabela pai válida
    ids_pais = df_pai.select(coluna_fk).distinct()
    
    # Left Anti Join captura exatamente os registros filhos que NÃO possuem chave correspondente no pai
    df_quarentena = df_filho.join(
        ids_pais, 
        df_filho[coluna_fk] == ids_pais[coluna_fk], 
        "left_anti"
    ).withColumn(
        "motivo_rejeicao", F.lit(motivo_erro)
    ).withColumn(
        "data_quarentena", 
        F.current_timestamp()
    )
    
    # Inner Join garante que apenas os registros com pai válido sigam adiante para a Silver
    df_validos = df_filho.join(
        ids_pais, 
        df_filho[coluna_fk] == ids_pais[coluna_fk], 
        "inner"
    )
    
    return df_validos, df_quarentena