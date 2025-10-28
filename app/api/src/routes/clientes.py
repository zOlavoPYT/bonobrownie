# Continuação do seu arquivo principal da API (ex: main.py ou routers/clientes.py)
import requests
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, status

import os
from dotenv import load_dotenv

router = APIRouter()

# --- Configuração do Supabase ---
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

from typing import List, Dict, Any
def _get_headers() -> dict:
    """
    Cria os cabeçalhos de autenticação para as requisições ao Supabase.
    """
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"  # ✅ Header importante!
    }

# --- Modelo de Dados de Entrada ---
# --- Modelo de Dados de Saída ---
# Define como os dados do cliente virão do Supabase
class ClienteOutput(BaseModel):
    """
    Define a estrutura dos dados de saída (resposta da API) para um cliente.
    O nome 'name' no Supabase é mapeado para 'nome' na resposta, se desejado,
    mas usaremos 'name' para simplicidade.
    """
    id: int
    name: str  # Corresponde à coluna 'name' na sua tabela
    status: bool # Corresponde à coluna 'status' na sua tabela

# --- Nova Rota: Listar Clientes ---
@router.get(
    "/listar_clientes",
    response_model=List[ClienteOutput],  # Informa ao FastAPI que a resposta é uma lista de ClienteOutput
    status_code=status.HTTP_200_OK,
    summary="Lista todos os clientes",
    description="Busca todos os registros da tabela 'Cliente' no Supabase."
)
def listar_clientes():
    """
    Busca e retorna todos os clientes da tabela 'Cliente' no Supabase.

    Returns:
        Uma lista de objetos ClienteOutput.

    Raises:
        HTTPException: Se a requisição ao Supabase falhar.
    """
    table_name = "Cliente"
    
    try:
        headers = _get_headers()
        
        # URL para buscar todos os dados da tabela 'Cliente'
        # O parâmetro 'select=*' (opcional, mas recomendado) garante que todas as colunas sejam retornadas
        url = f"{SUPABASE_URL}/rest/v1/{table_name}?select=*"
        
        # O método HTTP para leitura de dados é GET
        response = requests.get(url, headers=headers, timeout=15.0)
        
        # Lança exceção se a resposta não for 2xx
        response.raise_for_status()
        
        # O Supabase retorna uma lista de dicionários
        clientes_data: List[Dict[str, Any]] = response.json()
        
    except requests.exceptions.HTTPError as e:
        # Captura erros HTTP (400, 404, 500, etc.)
        error_detail = e.response.text if e.response else str(e)
        raise HTTPException(
            status_code=e.response.status_code if e.response else 500,
            detail=f"Erro do Supabase: {error_detail}"
        )
    except requests.exceptions.RequestException as e:
        # Captura erros de conexão, timeout, etc.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro de comunicação com o Supabase: {e}"
        )
    
    # O Pydantic (usado por FastAPI) irá validar a lista de dicionários
    # com base no modelo ClienteOutput antes de retornar a resposta.
    return clientes_data