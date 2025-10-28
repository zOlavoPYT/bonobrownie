Feature: Testes da API de Estoque

Background:
  * url baseUrl

# --------------------------
# Teste 1: Listar categorias (sucesso)
# --------------------------
Scenario: GET /categorias_estoque
  Given path 'categorias_estoque'
  When method get
  Then status 200
  And match response contains any ["Legume", "Pizza"]

# --------------------------
# Teste 2: Endpoint inexistente (fracasso esperado)
# --------------------------
Scenario: GET /categoria_inexistente
  Given path 'categoria_inexistente'
  When method get
  Then status 200
