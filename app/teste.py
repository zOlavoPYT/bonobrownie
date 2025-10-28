import requests
import json
from datetime import datetime
import datetime as dt
from typing import Dict, Any

# --- Configurações do Teste ---
# URL base da sua aplicação FastAPI (ajuste a porta se necessário)
BASE_URL = "http://127.0.0.1:8000"
# Endpoint que estamos testando
ENDPOINT = "/api/v1/cobranca/adicionar_cobranca"
FULL_URL = f"{BASE_URL}{ENDPOINT}"

def build_test_payload() -> Dict[str, Any]:
    """
    Cria um payload de teste válido para a rota CobrancaInput.
    """
    # A data de vencimento deve estar no formato ISO 8601,
    # que é o que a Pydantic espera para o tipo 'datetime'.
    vencimento_exemplo = (datetime.now().date() + dt.timedelta(days=30)).isoformat()
    
    # Criamos os dados que a API FastAPI espera receber no corpo da requisição
    payload = {
        "cliente": "Fulano de Tal",
        # O FastAPI converte a string ISO para o objeto datetime
        "vencimento": f"{vencimento_exemplo}T10:00:00", 
        "valor": 99.99,
        "status": False  # Cobrança inicialmente não paga
    }
    return payload

def run_test_request():
    """
    Executa a requisição POST de teste para o endpoint de adicionar cobrança.
    """
    test_data = build_test_payload()
    
    print(f"--- Iniciando Teste POST para {FULL_URL} ---")
    print(f"Dados a serem enviados (Payload):\n{json.dumps(test_data, indent=4)}\n")

    try:
        # Envia a requisição POST
        response = requests.post(
            FULL_URL,
            json=test_data,
            timeout=10
        )
        
        # Exibe o status da resposta
        print(f"Status Code da Resposta: {response.status_code}")
        
        # Tenta obter o corpo da resposta (JSON)
        try:
            response_json = response.json()
            print(f"Corpo da Resposta:\n{json.dumps(response_json, indent=4)}")
        except requests.exceptions.JSONDecodeError:
            print("Corpo da Resposta (não-JSON):")
            print(response.text)

        # Verifica se o status code indica sucesso (201 Created)
        if response.status_code == 201:
            print("\n✅ Teste Concluído com SUCESSO! A cobrança foi enviada (e deve ter sido criada no Supabase).")
        else:
            print(f"\n❌ Teste Falhou! Status Code inesperado: {response.status_code}")
            print("Verifique se a sua API está rodando e se as variáveis do Supabase estão corretas.")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO: Falha ao conectar. Verifique se a sua API FastAPI está rodando em 'http://127.0.0.1:8000'.")
    except requests.exceptions.Timeout:
        print("\n❌ ERRO: A requisição expirou (Timeout).")
    except Exception as e:
        print(f"\n❌ Ocorreu um erro inesperado durante o teste: {e}")

# --- Ponto de Entrada do Script ---
if __name__ == '__main__':
    run_test_request()