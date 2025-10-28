import os
import requests
import json
from typing import Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter
from app.api.src.schemas.produto import Produto, ProdutoUpdateEstoque,ProdutoAddEstoque

router = APIRouter()

# --- Modelos e Exceção Aprimorada ---

class StandardHTTPException(Exception):
    """
    Exceção aprimorada para encapsular erros de requisição HTTP,
    mostrando a resposta completa da API.
    """
    def __init__(self, detail: Dict[str, Any], status_code: int):
        self.detail = detail
        self.status_code = status_code
        # A mensagem base (super) continua simples, para logs concisos se necessário
        super().__init__(f"HTTP {status_code}: {self.detail.get('message', 'Erro desconhecido')}")

    def __str__(self):
        """
        Retorna uma representação em string detalhada e formatada do erro,
        incluindo a resposta completa da API.
        """
        # Formata o dicionário de detalhes em uma string JSON legível
        detailed_response = json.dumps(self.detail, indent=2, ensure_ascii=False)
        
        return (
            f"[ERRO HTTP {self.status_code}] {self.detail.get('message', 'Ocorreu um erro na requisição.')}\n"
            f"--- Resposta completa da API ---\n"
            f"{detailed_response}"
        )

# Adicionando o modelo Pydantic para o código ser executável
class Produto(BaseModel):
    id: int
    created_at: str = Field(..., alias="created_at")
    categoria: str
    quantidade: int

# --- Funções ---

# Coloquei suas credenciais hardcoded aqui para o exemplo funcionar,
# mas o ideal é manter como variáveis de ambiente.
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ0ZXBpeWpreHNhb3d3eW1vdHR3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTI2ODI4MCwiZXhwIjoyMDc0ODQ0MjgwfQ.NHrBblEdWdf1eiw_wN8TViYb6Ycj4lmVLUjRbMu7Ggo'
SUPABASE_URL = 'https://rtepiyjkxsaowwymottw.supabase.co'

def _get_headers() -> dict:
    """Cria os cabeçalhos padrão para a autenticação na API do Supabase."""
    if not SUPABASE_KEY:
        raise ValueError("A chave do Supabase não foi definida.")
    
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }

def atualizar_estoque(categoria_produto: str, nova_quantidade: int) -> int:
    """
    Atualiza (define) a quantidade em estoque para uma categoria de produto.
    
    RETORNA:
        A nova quantidade de estoque para a categoria.
    """
    table_name = "Estoque"
    try:
        headers = _get_headers()
        url = f"{SUPABASE_URL}/rest/v1/{table_name}"
        params = {"categoria": f"eq.{categoria_produto}"}
        payload = {"quantidade": nova_quantidade}

        response = requests.patch(url, headers=headers, params=params, json=payload, timeout=15.0)

        if response.status_code >= 400:
            try:
                detail = response.json()
            except json.JSONDecodeError:
                detail = {"message": response.text}
            raise StandardHTTPException(detail=detail, status_code=response.status_code)

        rows = response.json()
        if not rows:
            raise StandardHTTPException(
                detail={"message": f"Operação PATCH bem-sucedida, mas nenhum registro foi retornado. A categoria '{categoria_produto}' pode não existir."},
                status_code=404
            )
        
        # ALTERADO: Retorna diretamente o valor da nova quantidade do primeiro registro atualizado.
        return rows[0]['quantidade']

    except requests.exceptions.RequestException as req_err:
        raise StandardHTTPException(detail={"message": f"Erro de conexão: {req_err}"}, status_code=503)
    except Exception as e:
        if isinstance(e, StandardHTTPException):
            raise
        raise StandardHTTPException(detail={"message": f"Erro inesperado: {e}"}, status_code=500)

def add_to_stock(categoria_produto: str, quantidade_a_adicionar: int) -> int:
    """
    Adiciona uma quantidade ao estoque existente de uma categoria de produto.

    RETORNA:
        A nova quantidade total de estoque para a categoria.
    """
    table_name = "Estoque"
    try:
        headers = _get_headers()
        get_url = f"{SUPABASE_URL}/rest/v1/{table_name}"
        get_params = {"categoria": f"eq.{categoria_produto}", "select": "quantidade"}
        
        get_response = requests.get(get_url, headers=headers, params=get_params, timeout=15.0)

        if get_response.status_code >= 400:
            raise StandardHTTPException(detail=get_response.json(), status_code=get_response.status_code)
        
        data = get_response.json()
        if not data:
            raise StandardHTTPException(
                detail={"message": f"A categoria de produto '{categoria_produto}' não foi encontrada na base de dados."},
                status_code=404
            )
            
        quantidade_atual = data[0]['quantidade']
        nova_quantidade_total = quantidade_atual + quantidade_a_adicionar

        # ALTERADO: Chama a função 'atualizar_estoque' e retorna diretamente seu resultado (a nova quantidade).
        return atualizar_estoque(categoria_produto, nova_quantidade_total)

    except requests.exceptions.RequestException as req_err:
        raise StandardHTTPException(detail={"message": f"Erro de conexão: {req_err}"}, status_code=503)
    except Exception as e:
        if isinstance(e, StandardHTTPException):
            raise
        raise StandardHTTPException(detail={"message": f"Erro inesperado: {e}"}, status_code=500)


# --- Endpoints da API ---

@router.patch(
    "/{categoria_produto}/estoque",
    response_model=int,
    summary="Atualizar Estoque de um Produto Específico",
    description="Define uma nova quantidade total para o estoque de um produto e retorna o novo valor."
)
def atualizar_estoque_produto(
    *,
    categoria_produto: str,
    estoque_in: ProdutoUpdateEstoque
) -> int:
    """Endpoint para definir a quantidade de estoque de um produto."""
    # ALTERADO: Retorna diretamente o resultado da função de serviço.
    return atualizar_estoque(categoria_produto, estoque_in.quantidade)

@router.post(
    "/{categoria_produto}/add_to_estoque",
    response_model=int,
    summary="Adicionar ao Estoque de um Produto Específico",
    description="Adiciona uma quantidade ao estoque atual de um produto e retorna o novo total."
)
def adicionar_estoque_produto(
    *,
    categoria_produto: str,
    estoque_in: ProdutoAddEstoque
) -> int:
    """Endpoint para adicionar itens ao estoque de um produto."""
    # O retorno já estava correto, apenas adicionamos o tipo de retorno e o response_model.
    return add_to_stock(categoria_produto, estoque_in.quantidade)
