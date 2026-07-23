import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType

# ---------------------------------------------------------
# Simulando a função que você tem no seu código real da Prata
# (Se você já tem uma função parecida, importe-a em vez de criar aqui)
# ---------------------------------------------------------
def filter_valid_cpf(df):
    """Filtra registros garantindo que o CPF não seja nulo."""
    return df.filter(df["cpf"].isNotNull())

# ---------------------------------------------------------
# Configuração do Pytest (Fixture do Spark)
# ---------------------------------------------------------
@pytest.fixture(scope="session")
def spark():
    """Cria uma sessão local do Spark para os testes."""
    return SparkSession.builder \
        .master("local[1]") \
        .appName("TesteUnitarioDatabricks") \
        .getOrCreate()

# ---------------------------------------------------------
# O Teste Unitário
# ---------------------------------------------------------
def test_filter_valid_cpf(spark):
    # 1. Preparação (Arrange): Cria o schema e os dados falsos
    schema = StructType([
        StructField("id_cliente", StringType(), True),
        StructField("cpf", StringType(), True)
    ])
    
    mock_data = [
        ("1", "12345678900"), # CPF Válido
        ("2", None),          # CPF Nulo (deve ser removido)
        ("3", "98765432100")  # CPF Válido
    ]
    
    df_input = spark.createDataFrame(mock_data, schema)
    
    # 2. Ação (Act): Aplica a função de transformação
    df_result = filter_valid_cpf(df_input)
    
    # 3. Verificação (Assert): Confirma se o resultado é o esperado
    # Esperamos que apenas 2 registros sobem (os que não têm CPF nulo)
    assert df_result.count() == 2
    
    # Garante que o CPF nulo realmente não está no DataFrame final
    cpfs_restantes = [row["cpf"] for row in df_result.collect()]
    assert None not in cpfs_restantes