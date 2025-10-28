Feature: Testes da API de Estoque

Background:
  * url baseUrl

# --------------------------
# Teste 1: Listar categorias
# --------------------------
Scenario: GET /categorias_estoque
  Given path 'categorias_estoque'
  When method get
  Then status 200
  And match response contains any  ["Legume","Pizza"]