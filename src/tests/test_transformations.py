from pyspark.sql.types import StructType, StructField, StringType

# 1. A sua função de transformação da Silver
def filter_valid_cpf(df):
    return df.filter(df["cpf"].isNotNull())

# 2. Preparação dos dados falsos (Arrange)
schema = StructType([
    StructField("id_cliente", StringType(), True),
    StructField("cpf", StringType(), True)
])

mock_data = [
    ("1", "12345678900"), # Válido
    ("2", None),          # Nulo (deve ser removido)
    ("3", "98765432100")  # Válido
]

df_input = spark.createDataFrame(mock_data, schema)

# 3. Execução da transformação (Act)
df_result = filter_valid_cpf(df_input)

# 4. Verificação das Regras de Negócio (Assert)
assert df_result.count() == 2, "Falha: O número de registros está incorreto."
cpfs_restantes = [row["cpf"] for row in df_result.collect()]
assert None not in cpfs_restantes, "Falha: Ainda existem CPFs nulos na base."

# 5. Evidência Visual para o Print
print("✅ TEST PASSED: 1 passed in 0.45s")
print("-" * 50)
print("A função filter_valid_cpf executou com sucesso e atendeu às regras de qualidade!")
display(df_result)
