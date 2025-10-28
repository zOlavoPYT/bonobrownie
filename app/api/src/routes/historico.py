from fastapi import APIRouter, Path
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import requests, json
from app.api.src.schemas.venda import Venda,CategoriaSchema
from datetime import datetime
router = APIRouter()

# --- Constante para definir o tamanho da página ---
ITENS_POR_PAGINA = 20
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
# ... (rota POST "/" existente) ...
        )
import os
from dotenv import load_dotenv
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

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

def obter_historico(categoria: str) -> List[Venda]:
    """Retorna o histórico de vendas para uma categoria de produto específica."""
    table_name = "Venda"
    try:
        headers = _get_headers()
        url = f"{SUPABASE_URL}/rest/v1/{table_name}"
        params = {"categoria_produto": f"eq.{categoria}", "select": "*"}

        response = requests.get(url, headers=headers, params=params, timeout=15.0)

        if response.status_code >= 400:
            try:
                detail = response.json()
            except json.JSONDecodeError:
                detail = {"message": response.text}
            raise StandardHTTPException(detail=detail, status_code=response.status_code)
        
        data = response.json()
        
        # Converte cada item do dicionário JSON em um objeto Venda
        return [Venda(**item) for item in data]

    except requests.exceptions.RequestException as req_err:
        raise StandardHTTPException(detail={"message": f"Erro de conexão: {req_err}"}, status_code=503)
    except Exception as e:
        if isinstance(e, StandardHTTPException):
            raise
        raise StandardHTTPException(detail={"message": f"Erro inesperado: {e}"}, status_code=500)




@router.post(
    "/historico/{pagina}",
    response_model=List[Venda],
    summary="Obter Histórico de Vendas Paginado"
)
def obter_historico_de_vendas(
    *,
    categoria_dto: CategoriaSchema, # DTO vem no corpo da requisição
    pagina: int = Path(..., gt=0, description="O número da página para retornar")
)-> List[Venda]:
    """
    Endpoint para obter o histórico de vendas de forma paginada,
    filtrado por uma categoria enviada no corpo da requisição.
    """
    historico_completo = obter_historico(categoria_dto.categoria)
    
    # Lógica de paginação
    inicio = (pagina - 1) * ITENS_POR_PAGINA
    fim = pagina * ITENS_POR_PAGINA
    
    return historico_completo[inicio:fim]