import pytest
from datetime import date
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, DateType, IntegerType
from pyspark.sql.functions import col, row_number, when, lit
from pyspark.sql.window import Window

# ==============================================================================
# 1. FIXTURE DE SPARKSESSION (O ambiente isolado para o CI/CD)
# ==============================================================================
@pytest.fixture(scope="session")
def spark():
    """
    Cria ou recupera uma SparkSession para rodar os testes.
    Ao não forçar o .master(), evitamos conflito de ambiente no Databricks (Spark Connect),
    mas o CI/CD (GitHub Actions) ainda conseguirá instanciar localmente por padrão.
    """
    spark_session = SparkSession.builder \
        .appName("pytest-pyspark-local") \
        .config("spark.sql.shuffle.partitions", "1") \
        .getOrCreate()
        
    yield spark_session


# ==============================================================================
# 2. TESTES UNITÁRIOS DAS REGRAS DE NEGÓCIO DA SILVER
# ==============================================================================

def test_filter_valid_cpf(spark):
    """Garante que CPFs nulos sejam removidos na camada Silver."""
    schema = StructType([
        StructField("id_cliente", StringType(), True),
        StructField("cpf", StringType(), True)
    ])
    data = [("1", "12345678900"), ("2", None), ("3", "98765432100")]
    df = spark.createDataFrame(data, schema)

    # Simula a transformação
    df_filtered = df.filter(col("cpf").isNotNull())
    result = df_filtered.collect()

    assert len(result) == 2
    assert "2" not in [row.id_cliente for row in result]


def test_deduplicate_by_row_number(spark):
    """Garante que o particionamento via ROW_NUMBER mantenha apenas o registro mais recente."""
    schema = StructType([
        StructField("id_transacao", StringType(), True),
        StructField("timestamp_evento", IntegerType(), True),
        StructField("valor", DoubleType(), True)
    ])
    # T1 tem duas versões, queremos manter a de timestamp maior (150)
    data = [
        ("T1", 100, 50.0), 
        ("T1", 150, 55.0), 
        ("T2", 200, 20.0)
    ]
    df = spark.createDataFrame(data, schema)

    # Simula a transformação de dedup
    window_spec = Window.partitionBy("id_transacao").orderBy(col("timestamp_evento").desc())
    df_dedup = df.withColumn("rn", row_number().over(window_spec)) \
                 .filter(col("rn") == 1) \
                 .drop("rn")
    
    result = df_dedup.collect()

    assert len(result) == 2
    t1_rows = [row for row in result if row.id_transacao == "T1"]
    assert t1_rows[0].valor == 55.0 # Manteve o registro atualizado


def test_zeragem_valor_liquido_estornos(spark):
    """Garante que transações do tipo 'estorno' tenham o valor líquido zerado."""
    schema = StructType([
        StructField("id_transacao", StringType(), True),
        StructField("tipo", StringType(), True),
        StructField("valor_bruto", DoubleType(), True)
    ])
    data = [("T1", "compra", 100.0), ("T2", "estorno", 50.0)]
    df = spark.createDataFrame(data, schema)

    # Simula a transformação
    df_transformed = df.withColumn(
        "valor_liquido",
        when(col("tipo") == "estorno", lit(0.0)).otherwise(col("valor_bruto"))
    )
    result = df_transformed.collect()

    t2_row = [row for row in result if row.id_transacao == "T2"][0]
    assert t2_row.valor_liquido == 0.0


def test_point_in_time_join(spark):
    """Valida o join de SCD Tipo 2: transação deve pegar o cartão vigente na data."""
    schema_transacoes = StructType([
        StructField("id_transacao", StringType(), True),
        StructField("id_cartao", StringType(), True),
        StructField("data_transacao", DateType(), True)
    ])
    data_transacoes = [("TX1", "C1", date(2026, 7, 15))]
    df_transacoes = spark.createDataFrame(data_transacoes, schema_transacoes)

    # Cartão com duas vigências
    schema_cartoes = StructType([
        StructField("id_cartao", StringType(), True),
        StructField("limite", DoubleType(), True),
        StructField("data_inicio", DateType(), True),
        StructField("data_fim", DateType(), True)
    ])
    data_cartoes = [
        ("C1", 1000.0, date(2026, 1, 1), date(2026, 6, 30)),  # Expirado
        ("C1", 2000.0, date(2026, 7, 1), date(2099, 12, 31))  # Vigente
    ]
    df_cartoes = spark.createDataFrame(data_cartoes, schema_cartoes)

    # Simula o Join Point-in-Time
    df_join = df_transacoes.join(
        df_cartoes,
        (df_transacoes.id_cartao == df_cartoes.id_cartao) & 
        (df_transacoes.data_transacao >= df_cartoes.data_inicio) & 
        (df_transacoes.data_transacao <= df_cartoes.data_fim),
        "left"
    ).select(df_transacoes["id_transacao"], df_cartoes["limite"])

    result = df_join.collect()
    assert len(result) == 1
    assert result[0].limite == 2000.0 # Pegou o limite da vigência correta


def test_cartao_cancelado_gold_cliente_mes(spark):
    """Garante que cartões cancelados não somem nos totais da camada Gold."""
    schema = StructType([
        StructField("id_cliente", StringType(), True),
        StructField("status_cartao", StringType(), True),
        StructField("valor_transacao", DoubleType(), True)
    ])
    data = [
        ("CLI_1", "ativo", 100.0), 
        ("CLI_1", "cancelado", 500.0), 
        ("CLI_1", "ativo", 50.0)
    ]
    df = spark.createDataFrame(data, schema)

    # Simula a agregação da Gold
    df_gold = df.filter(col("status_cartao") != "cancelado") \
                .groupBy("id_cliente") \
                .sum("valor_transacao") \
                .withColumnRenamed("sum(valor_transacao)", "total_gasto")
    
    result = df_gold.collect()
    assert result[0].total_gasto == 150.0 # Ignorou os 500.0 do cartão cancelado