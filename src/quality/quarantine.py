from pyspark.sql import DataFrame
import pyspark.sql.functions as F

def aplicar_quarentena(df: DataFrame, regra_invalida, motivo_erro: str):
    # Aplica regra de qualidade e separa registros válidos da quarentena
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
    # Isola chaves distintas da entidade pai
    ids_pais = df_pai.select(coluna_fk).distinct()
    
    # Left anti join identifica registros órfãos sem correspondência no pai
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
    
    # Inner join garante a integridade referencial mantendo apenas pais válidos
    df_validos = df_filho.join(
        ids_pais, 
        df_filho[coluna_fk] == ids_pais[coluna_fk], 
        "inner"
    )
    
    return df_validos, df_quarentena