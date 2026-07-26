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