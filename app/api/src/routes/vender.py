# src/brownie_api/api/v1/endpoints/vendas.py

from fastapi import APIRouter, status
router = APIRouter()
import requests
from typing import Dict, Any
import json
from app.api.src.schemas.produto import AtualizarEstoqueRequest
from app.api.src.routes.estoque_atual import adicionar_ao_estoque
from app.api.src.schemas.venda import Venda
from app.api.src.routes.cobranca import criar_cobranca_de_venda,adicionar_cobranca
from app.api.src.routes.estoque_atual import _obter_ultimo_preco_unitario
import os
from dotenv import load_dotenv
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


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

def registrar_nova_venda(venda: Venda) -> Dict[str, Any]:
    """
    Registra uma nova venda na tabela 'Venda' do Supabase.

    A função recebe um objeto (presumivelmente um modelo Pydantic 'Venda') 
    e o insere como uma nova linha na tabela.

    Args:
        venda (Venda): O objeto contendo os dados da venda a serem inseridos.
                       Assume-se que este objeto já tem todos os campos necessários
                       preenchidos, conforme a regra de negócio.

    Returns:
        Dict[str, Any]: Um dicionário representando a linha recém-criada no banco de dados,
                        conforme retornado pela API do Supabase.

    Raises:
        StandardHTTPException: Lançada em caso de erro na requisição HTTP (status >= 400),
                               erro de conexão ou outro erro inesperado.
    """
    table_name = "Venda"
    if not venda.valor_unitario:
        venda.valor_unitario = _obter_ultimo_preco_unitario(venda.categoria_produto)
    try:
        # 1. Reutiliza a função para obter os cabeçalhos de autenticação
        headers = _get_headers()
        url = f"{SUPABASE_URL}/rest/v1/{table_name}"

        # 2. Converte o objeto 'venda' em um dicionário para o payload JSON.
        #    A API do Supabase espera uma lista de registros para inserção.
        payload = [venda.model_dump(mode="json")]

        
        response = requests.post(url, headers=headers, json=payload, timeout=15.0)
        cobranca = criar_cobranca_de_venda(venda)
        adicionar_cobranca(cobranca)

        # 4. Reutiliza o padrão de tratamento de erros HTTP
        if response.status_code >= 400:
            try:
                detail = response.json()
            except json.JSONDecodeError:
                detail = {"message": response.text}
            raise StandardHTTPException(detail=detail, status_code=response.status_code)

        # 5. A API, com o header "Prefer: return=representation", retorna uma lista
        #    contendo os registros que foram criados.
        created_data = response.json()
        
        # Retorna o primeiro (e único) registro do resultado
        return created_data[0]

    except requests.exceptions.RequestException as req_err:
        # Reutiliza o padrão de tratamento de erro de conexão
        raise StandardHTTPException(detail={"message": f"Erro de conexão ao registrar venda: {req_err}"}, status_code=503)
    except Exception as e:
        # Reutiliza o padrão de tratamento de erro genérico
        if isinstance(e, StandardHTTPException):
            raise
        raise StandardHTTPException(detail={"message": f"Erro inesperado ao registrar venda: {e}"}, status_code=500)
@router.post(
    "/vender",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar uma Nova Venda",
    description="Cria um novo registro de venda e atualiza o estoque do produto correspondente."
)
def registrar_venda(
    venda_in: Venda
):
    """
    Endpoint para registrar uma nova venda.

    - **cliente_id**: ID do cliente.
    - **produto_id**: ID do produto.
    - **unidades**: Quantidade vendida (deve ser maior que 0).
    - **prazo_dias**: Prazo em dias para o pagamento.
    - **valor_unitario**: Preço do produto no momento da venda.
    """
    print(venda_in)
    registrar_nova_venda(venda_in)
    req = AtualizarEstoqueRequest(categoria=venda_in.categoria_produto,quantidade=-venda_in.qtd_unidades)
    adicionar_ao_estoque(req)

