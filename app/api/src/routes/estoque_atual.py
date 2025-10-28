from typing import List
from app.api.src.schemas.produto import EstoqueRequest,AtualizarEstoqueRequest,PrecoUnitarioRequest
import requests
from typing import Dict, Any, Optional
import json
from fastapi import APIRouter, HTTPException, status
from fastapi import APIRouter
import os
from dotenv import load_dotenv
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
router = APIRouter()
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

# O router é prefixado com '/produtos' no arquivo principal da API
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

# --- Funções ---

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

def estoque_por_categoria() -> List[Dict[str, Any]]:
    """
    Obtém uma lista com a quantidade em estoque para cada categoria de produto.

    Returns:
        Uma lista de dicionários, onde cada dicionário contém a 'categoria'
        e a 'quantidade' em estoque. Ex: [{'categoria': 'Brownie', 'quantidade': 50}]
    """
    table_name = "Estoque"
    try:
        headers = _get_headers()
        url = f"{SUPABASE_URL}/rest/v1/{table_name}"
        
        # Modificação: Seleciona as colunas 'categoria' e 'quantidade' para todos os registros.
        # Não há filtro por uma categoria específica.
        params = {"select": "categoria,quantidade"}
        
        response = requests.get(url, headers=headers, params=params, timeout=15.0)

        if response.status_code >= 400:
            try:
                detail = response.json()
            except json.JSONDecodeError:
                detail = {"message": response.text}
            raise StandardHTTPException(detail=detail, status_code=response.status_code)
        
        # A API já retorna uma lista de dicionários no formato desejado.
        return response.json()

    except requests.exceptions.RequestException as req_err:
        raise StandardHTTPException(detail={"message": f"Erro de conexão: {req_err}"}, status_code=503)
    except Exception as e:
        if isinstance(e, StandardHTTPException):
            raise
        raise StandardHTTPException(detail={"message": f"Erro inesperado: {e}"}, status_code=500)

def obter_estoque(categoria_produto: str) -> int:
    """Obtém a quantidade em estoque de uma categoria de produto."""
    table_name = "Estoque"
    try:
        headers = _get_headers()
        url = f"{SUPABASE_URL}/rest/v1/{table_name}"
        params = {"categoria": f"eq.{categoria_produto}", "select": "quantidade"}
        
        response = requests.get(url, headers=headers, params=params, timeout=15.0)

        if response.status_code >= 400:
            try:
                detail = response.json()
            except json.JSONDecodeError:
                detail = {"message": response.text}
            raise StandardHTTPException(detail=detail, status_code=response.status_code)
        
        data = response.json()
        if not data:
            raise StandardHTTPException(
                detail={"message": f"A categoria de produto '{categoria_produto}' não foi encontrada."},
                status_code=404
            )
            
        return data[0]['quantidade']

    except requests.exceptions.RequestException as req_err:
        raise StandardHTTPException(detail={"message": f"Erro de conexão: {req_err}"}, status_code=503)
    except Exception as e:
        if isinstance(e, StandardHTTPException):
            raise
        raise StandardHTTPException(detail={"message": f"Erro inesperado: {e}"}, status_code=500)
@router.post(
    "/estoque_atual",
    summary="Obter Estoque Atual de Todos os Produtos",
    description="Retorna uma lista completa de todos os produtos e suas respectivas quantidades em estoque."
)
def obter_estoque_atual(
    req: EstoqueRequest,
    # db: Session = Depends(deps.get_db) (removido)
) -> int:
    """
    Endpoint para buscar o status atual do estoque de todos os produtos.
    """
    return obter_estoque(req.categoria)



def _obter_ultimo_preco_unitario(categoria: str) -> Optional[float]:
    """
    Busca o último 'preco_unitario' conhecido para a categoria no Supabase.
    """
    table_name = "Estoque"
    headers = _get_headers()
    try:
        url = f"{SUPABASE_URL}/rest/v1/{table_name}?categoria=eq.{categoria}&select=preco_unitario"
        response = requests.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        if data:
            return data[0].get("preco_unitario")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Alerta: Falha ao buscar preço unitário no Supabase: {e}")
        return None

@router.post(
    "/atualizar_estoque",
    status_code=status.HTTP_200_OK,  # Melhor que 201 para UPSERT
    summary="Atualiza o estoque de uma categoria de produto (UPSERT)",
    description="Cria um novo registro de estoque ou atualiza um existente com base na categoria."
)
def atualizar_estoque_por_categoria(req: AtualizarEstoqueRequest):
    """
    Endpoint para atualizar o estoque de uma categoria de produto no Supabase.
    Esta função realiza um 'UPSERT'.
    """
    table_name = "Estoque"

    preco_unitario_existente = _obter_ultimo_preco_unitario(req.categoria)
    preco_para_uso = preco_unitario_existente if preco_unitario_existente is not None else 0.0

    payload = {
        "categoria": req.categoria,
        "quantidade": req.quantidade,
        "preco_unitario": preco_para_uso,
        "observacao": "Atualizacao de estoque"
    }

    try:
        headers = _get_headers()
        headers["Prefer"] = "resolution=merge-duplicates"

        # ✅ Adiciona on_conflict na URL
        url = f"{SUPABASE_URL}/rest/v1/{table_name}?on_conflict=categoria"

        response = requests.post(url, headers=headers, json=payload, timeout=15.0)
        response.raise_for_status()

        try:
            data = response.json() if response.content else None
        except ValueError:
            data = None

        return {
            "message": f"Estoque da categoria '{req.categoria}' atualizado com sucesso.",
            "data": data
}


    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if e.response else str(e)
        raise HTTPException(
            status_code=e.response.status_code if e.response else 500,
            detail=f"Erro do Supabase ao atualizar estoque: {error_detail}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro de comunicação: {e}"
        )
@router.post(
    "/adicionar_ao_estoque",
    status_code=status.HTTP_200_OK,
    summary="Adiciona uma quantidade ao estoque de uma categoria (UPSERT)",
    description="Adiciona a quantidade fornecida ao estoque existente ou cria um novo registro se ele não existir."
)
def adicionar_ao_estoque(req: AtualizarEstoqueRequest):
    """
    Endpoint para ADICIONAR uma quantidade ao estoque de uma categoria no Supabase.
    """
    table_name = "Estoque"
    try:
        # Tenta obter o estoque atual. Se não encontrar (404), considera como 0.
        try:
            estoque_atual = obter_estoque(req.categoria)
        except StandardHTTPException as e:
            if e.status_code == 404:
                estoque_atual = 0
            else:
                raise  # Propaga outros erros

        nova_quantidade = estoque_atual + req.quantidade
        preco_unitario_existente = _obter_ultimo_preco_unitario(req.categoria)
        preco_para_uso = preco_unitario_existente if preco_unitario_existente is not None else 0.0

        payload = {
            "categoria": req.categoria,
            "quantidade": nova_quantidade,
            "preco_unitario": preco_para_uso,
            "observacao": f"Adicao de {req.quantidade} unidade(s) ao estoque"
        }

        headers = _get_headers()
        headers["Prefer"] = "resolution=merge-duplicates"

        # ✅ Adiciona on_conflict na URL
        url = f"{SUPABASE_URL}/rest/v1/{table_name}?on_conflict=categoria"

        response = requests.post(url, headers=headers, json=payload, timeout=15.0)
        

        
        response.raise_for_status()
        data = None
        if response.status_code != 204 and response.text:
            try:
                data = response.json()
            except json.JSONDecodeError:
                # ✅ TRATA RESPOSTA INVÁLIDA DE FORMA MAIS CLARA
                raise HTTPException(
                    status_code=500,
                    detail=f"A API externa respondeu com um corpo não-JSON. Conteúdo: {response.text}"
                )
        
        return {"message": f"Estoque da categoria '{req.categoria}' incrementado com sucesso.", "data": data}
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if e.response else str(e)
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=f"Erro do Supabase ao adicionar ao estoque: {error_detail}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Erro de comunicação: {e}")

@router.get(
    "/categorias_estoque",
    summary="Obter todas as categorias do estoque",
    description="Retorna uma lista com os nomes de todas as categorias de produtos existentes no estoque.",
    response_model=List[str]
)
def get_categorias_estoque():
    """
    Endpoint para buscar todas as categorias de produtos no estoque.
    """
    table_name = "Estoque"
    try:
        headers = _get_headers()
        url = f"{SUPABASE_URL}/rest/v1/{table_name}"
        params = {"select": "categoria"}
        
        response = requests.get(url, headers=headers, params=params, timeout=15.0)
        response.raise_for_status()
        
        data = response.json()
        categorias = [item['categoria'] for item in data]
        
        return categorias

    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if e.response else str(e)
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=f"Erro do Supabase: {error_detail}")
    except requests.exceptions.RequestException as req_err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Erro de comunicação: {req_err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {e}")
@router.get('/estoque')
def estoque_por_categoria() -> List[Dict[str, Any]]:
    """
    Obtém uma lista com a quantidade em estoque para cada categoria de produto.

    Returns:
        Uma lista de dicionários, onde cada dicionário contém a 'categoria'
        e a 'quantidade' em estoque. Ex: [{'categoria': 'Brownie', 'quantidade': 50}]
    """
    table_name = "Estoque"
    try:
        headers = _get_headers()
        url = f"{SUPABASE_URL}/rest/v1/{table_name}"
        
        # Modificação: Seleciona as colunas 'categoria' e 'quantidade' para todos os registros.
        # Não há filtro por uma categoria específica.
        params = {"select": "categoria,quantidade"}
        
        response = requests.get(url, headers=headers, params=params, timeout=15.0)

        if response.status_code >= 400:
            try:
                detail = response.json()
            except json.JSONDecodeError:
                detail = {"message": response.text}
            raise StandardHTTPException(detail=detail, status_code=response.status_code)
        
        # A API já retorna uma lista de dicionários no formato desejado.
        return response.json()

    except requests.exceptions.RequestException as req_err:
        raise StandardHTTPException(detail={"message": f"Erro de conexão: {req_err}"}, status_code=503)
    except Exception as e:
        if isinstance(e, StandardHTTPException):
            raise
        raise StandardHTTPException(detail={"message": f"Erro inesperado: {e}"}, status_code=500)

@router.post(
    "/preco_unitario",
    response_model=float,
    status_code=status.HTTP_200_OK,
    summary="Obtém o preço unitário de uma categoria",
    description="Busca e retorna o último preço unitário registrado para a categoria fornecida."
)
def obter_preco_unitario(req: PrecoUnitarioRequest):
    """
    Endpoint para obter o último preço unitário de uma categoria no Supabase.
    """
    try:
        # Utiliza a função auxiliar para buscar o preço
        preco_unitario = _obter_ultimo_preco_unitario(req.categoria)

        # Se a função retornar None, significa que a categoria não foi encontrada
        if preco_unitario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"A categoria '{req.categoria}' não foi encontrada no estoque."
            )
        
        return preco_unitario

    except HTTPException as e:
        # Re-propaga a exceção HTTP já tratada (como o 404 acima)
        raise e
    except Exception as e:
        # Captura qualquer outro erro inesperado durante a execução
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro interno ao buscar o preço unitário: {str(e)}"
        )
# --- Bloco de Teste ---
if __name__ == "__main__":

    print("\n\n--- Iniciando teste para ADICIONAR ao estoque ---")
    dados_adicao = {"categoria": "Pizza", "quantidade": 5}
    dados_adicao = AtualizarEstoqueRequest(**dados_adicao)
    adicionar_ao_estoque(dados_adicao)
   