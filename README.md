# Projeto bonobrownie

## Visão Geral

Este projeto consiste em uma aplicação de API desenvolvida em Python e um conjunto de testes de API automatizados utilizando o framework Karate. A aplicação Python é construída para ser executada com `uvicorn`, enquanto os testes são executados diretamente através do arquivo `karate-1.5.1.jar`.

## 1\. Como a Aplicação Funciona

A aplicação principal reside no diretório `app/` e é gerenciada usando [Poetry](https://python-poetry.org/) para dependências.

  * **Tecnologia:** A API é desenvolvida em Python com FastAPI.
  * **Execução:** A aplicação é servida localmente usando o servidor ASGI `uvicorn`, que é iniciado através do Poetry para garantir que o ambiente virtual correto e as dependências sejam carregados.

## 2\. Implementação e Uso do `karate-1.5.1.jar`

Neste projeto, o Karate é implementado como um executável "standalone" (autônomo), o `karate-1.5.1.jar`. Ele não é uma dependência de compilação do código Python; em vez disso, é uma ferramenta de teste independente que interage com a API "por fora".

  * **O que é:** O `karate-1.5.1.jar` é um arquivo Java executável que contém toda a biblioteca Karate. Ele permite a execução de testes de API sem a necessidade de configurar um projeto Java complexo (como Maven ou Gradle).
  * **Como é usado:**
    1.  A API Python é iniciada (conforme as instruções abaixo).
    2.  O `karate-1.5.1.jar` é invocado pela linha de comando para executar os testes.
    3.  O Karate lê o arquivo de definição de teste `test_api.feature`. Este arquivo, escrito em sintaxe Gherkin (Dado/Quando/Então), define os cenários de teste, como quais *endpoints* da API chamar, quais dados enviar (JSON) e quais respostas (códigos de status, corpos JSON) são esperadas.
    4.  O arquivo `karate-config.js` é usado para definir configurações globais para os testes, como a URL base da API (ex: `http://localhost:8000`).

## 3\. Pré-requisitos

Para executar a aplicação e os testes, os seguintes componentes devem estar instalados no sistema:

  * **Java (JDK ou JRE):** Necessário para executar o arquivo `karate-1.5.1.jar`. É recomendada a versão 8 ou superior.
      * *Verificação:* `java -version`
  * **Python:** Versão 3.8 ou superior.
      * *Verificação:* `python --version`
  * **Poetry:** O gerenciador de dependências e pacotes Python usado no projeto.
      * *Instalação (se necessário):* Siga as instruções em [python-poetry.org](https://www.google.com/search?q=https://python-poetry.org/docs/%23installation).

## 4\. Como Executar o Projeto

Siga estes passos para configurar e executar a aplicação e os testes.

### Passo 1: Instalar Dependências do Python

Clone o repositório e, dentro do diretório raiz do projeto, instale as dependências da API usando Poetry:

```bash
# Instala as dependências definidas no pyproject.toml
poetry install
```

### Passo 2: Executar a API Python

Após a instalação das dependências, inicie a API com o comando fornecido:

```bash
# O --reload monitora mudanças nos arquivos e reinicia o servidor
poetry run uvicorn app.main:app --reload
```

A API estará em execução (em `http://127.0.0.1:8000`).

### Passo 3: Executar os Testes do Karate

Com a API em execução, abra um **novo terminal** no mesmo diretório raiz e execute os testes do Karate usando o arquivo `.jar`:

```bash
# Comando para executar o arquivo .feature
java -jar karate-1.5.1.jar test_api.feature
```

O Karate executará as requisições HTTP contra a API (conforme definido em `test_api.feature`) e exibirá um relatório dos resultados no terminal.
