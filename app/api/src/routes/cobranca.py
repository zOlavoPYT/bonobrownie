import requests
from datetime import datetime,timezone, date
from fastapi import APIRouter, HTTPException, status
from typing import Optional
import os
from datetime import date, datetime, time, timedelta
from pydantic import BaseModel
from dotenv import load_dotenv
from app.api.src.routes.vender import Venda
from typing import List, Dict, Any
TODAY = date.today() # Data de hoje (apenas a parte da data)
router = APIRouter()
from app.api.src.schemas.cobranca import CobrancaDetalheResponse, CobrancaPagaResponse, FinancialSummaryResponse, PagarCobrancaInput,PagarCobrancaResponse
# --- Configuração do Supabase ---
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Validação das variáveis de ambiente
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar configuradas no .env")

# --- Funções Auxiliares ---
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
class CobrancaInput(BaseModel):
    """
    Define a estrutura e validação dos dados de entrada para criar uma nova cobrança.
    
    Campos da tabela Cobranca no Supabase:
    - id: int8 (auto-gerado, não enviar)
    - created_at: timestamp (auto-gerado, não enviar)
    - status_pagamento: bool (obrigatório)
    - cliente: text (obrigatório)
    - vencimento: timestamp (obrigatório)
    - data_venda: timestamp (opcional)
    - valor: float8 (obrigatório)
    """
    cliente: str
    vencimento: datetime
    valor: float
    status_pagamento: bool  # ✅ Nome correto!
    data_venda: Optional[datetime] = None  # Campo adicional opcional
def criar_cobranca_de_venda(venda: Venda) -> CobrancaInput:
    """
    Cria um objeto CobrancaInput a partir de um objeto Venda,
    mapeando os campos relevantes.
    """
    cobranca = CobrancaInput(
        # Mapeamentos Diretos:
        cliente=venda.cliente,
        status_pagamento=venda.status_pagamento,
        
        # Mapeamento do Valor (valor_total de Venda para valor de CobrancaInput)
        valor=venda.valor_total, 
        
        # Mapeamento da Data de Vencimento
        # (data_vencimento de Venda para vencimento de CobrancaInput)
        vencimento=venda.data_vencimento,
        
        # Mapeamento da Data da Venda (campo opcional em CobrancaInput)
        data_venda=venda.data_venda 
    )
    return cobranca

def adicionar_cobranca(cobranca: CobrancaInput):
    """
    Recebe os dados de uma nova cobrança e os insere na tabela 'Cobranca' do Supabase.
    
    Args:
        cobranca: Um objeto contendo 'cliente', 'vencimento', 'valor' e 'status'.
    
    Returns:
        Uma mensagem de sucesso com os dados da cobrança criada.
    
    Raises:
        HTTPException: Se a requisição ao Supabase falhar.
    """
    table_name = "Cobranca"
    
    # ✅ Converte para dict e serializa datetime para ISO format
    payload = cobranca.model_dump(mode="json")
    
    # Se você quiser enviar como array (para inserção em lote):
    # payload = [cobranca.model_dump(mode="json")]
    
    try:
        headers = _get_headers()
        url = f"{SUPABASE_URL}/rest/v1/{table_name}"
        
        response = requests.post(url, headers=headers, json=payload, timeout=15.0)
        
        # Para debug, você pode descomentar:
        # print(f"Status: {response.status_code}")
        # print(f"Response: {response.text}")
        
        response.raise_for_status()
        
        # Pega os dados retornados pelo Supabase
        data = response.json()
        
    except requests.exceptions.HTTPError as e:
        # Captura erros HTTP específicos (400, 404, 500, etc.)
        error_detail = e.response.text if e.response else str(e)
        # Log para debug
        print(f"Erro HTTP Status: {e.response.status_code if e.response else 'N/A'}")
        print(f"Payload enviado: {payload}")
        print(f"Response do Supabase: {error_detail}")
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
    
    return {
        "message": f"Cobrança para o cliente '{cobranca.cliente}' adicionada com sucesso!",
        "data": data
    }


# Supondo que você tenha este roteador definido e que as variáveis de ambiente
# e a função _get_headers já estejam importadas/disponíveis.



# --- Rota para o Relatório de Pendências ---
@router.get("/pendentes",response_model=FinancialSummaryResponse)
def obter_relatorio_pendentes():
    """
    Consulta a tabela 'Cobranca' e retorna um relatório com o total de
    cobranças pendentes, vencidas e o valor total a receber.
    """
    table_name = "Cobranca"
    
    # 1. Busca apenas as cobranças que não foram pagas
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?status_pagamento=eq.false"
    
    try:
        headers = _get_headers()
        response = requests.get(url, headers=headers, timeout=15.0)
        response.raise_for_status()
        cobrancas_nao_pagas = response.json()
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if e.response else str(e)
        raise HTTPException(
            status_code=e.response.status_code if e.response else 500,
            detail=f"Erro do Supabase: {error_detail}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro de comunicação com o Supabase: {e}"
        )

    # 2. Processa os dados para classificar e somar
    agora_utc = datetime.now(timezone.utc)
    
    relatorio = {
        "pendentes": {"quantidade": 0, "valor_total": 0.0},
        "vencidas": {"quantidade": 0, "valor_total": 0.0}
    }

    for cobranca in cobrancas_nao_pagas:
        # Converte a data de vencimento string para um objeto datetime com timezone
        vencimento = datetime.fromisoformat(cobranca["vencimento"])
        valor = float(cobranca["valor"])

        if vencimento > agora_utc:
            # Se a data de vencimento for no futuro, está pendente.
            relatorio["pendentes"]["quantidade"] += 1
            relatorio["pendentes"]["valor_total"] += valor
        else:
            # Se a data de vencimento for no passado ou hoje, está vencida.
            relatorio["vencidas"]["quantidade"] += 1
            relatorio["vencidas"]["valor_total"] += valor

    # 3. Calcula o total a receber
    total_a_receber = relatorio["pendentes"]["valor_total"] + relatorio["vencidas"]["valor_total"]

    # 4. Retorna o resultado no formato do response_model
    return {
        "pendentes": relatorio["pendentes"],
        "vencidas": relatorio["vencidas"],
        "total_a_receber": total_a_receber,
        "cobrancas_nao_pagas":cobrancas_nao_pagas
    }


@router.get(
    "/cobrancas_ativas",
    response_model=List[CobrancaDetalheResponse],
    summary="Lista todas as cobranças com pagamento pendente"
)
def listar_cobrancas_ativas():
    """
    Consulta a tabela 'Cobrancas' no Supabase e retorna uma lista com todas as
    cobranças que ainda não foram pagas (`status_pagamento` = FALSE).

    O status de cada cobrança é calculado dinamicamente:
    - **Pendente**: Se a data de vencimento for hoje ou no futuro.
    - **Vencido**: Se a data de vencimento já passou.

    Returns:
        Uma lista de objetos, cada um representando uma cobrança ativa.

    Raises:
        HTTPException: Se ocorrer um erro na comunicação com o Supabase.
    """
    table_name = "Cobrancas"
    hoje = date.today()
    cobrancas_formatadas = []

    table_name = "Cobranca"
    
    # 1. Busca apenas as cobranças que não foram pagas
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?status_pagamento=eq.false"
    try:
        headers = _get_headers()
        response = requests.get(url, headers=headers, timeout=15.0)
        response.raise_for_status()

        cobrancas_ativas = response.json()

        # ✅ Itera sobre os resultados para formatar a resposta
        for cobranca in cobrancas_ativas:
            # Converte a string de data/hora do Supabase para um objeto de data Python
            vencimento_dt = datetime.fromisoformat(cobranca['vencimento']).date()

            # Calcula o status da cobrança
            status_calculado = "Vencido" if vencimento_dt < hoje else "Pendente"

            item_formatado = CobrancaDetalheResponse(
                cliente=cobranca.get('cliente', 'N/A'),
                vencimento=str(vencimento_dt),
                valor=cobranca.get('valor', 0.0),
                status=status_calculado
            )
            cobrancas_formatadas.append(item_formatado)

    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if e.response else str(e)
        raise HTTPException(
            status_code=e.response.status_code if e.response else 500,
            detail=f"Erro ao buscar cobranças no Supabase: {error_detail}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro de comunicação com o Supabase: {e}"
        )
    except (KeyError, TypeError) as e:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar os dados recebidos do Supabase. Campo faltando ou tipo inválido: {e}"
        )

    return cobrancas_formatadas



# --- Assumindo que o restante do seu setup (router, variáveis, _get_headers) já existe ---

# ... seu código anterior ...





@router.get(
    "/cobrancas_pagas",
    response_model=List[CobrancaPagaResponse],
    summary="Lista todas as cobranças que já foram pagas"
)
def listar_cobrancas_pagas():
    """
    Consulta a tabela 'Cobranca' no Supabase e retorna uma lista com todas as
    cobranças que já foram pagas (`status_pagamento` = TRUE).

    Returns:
        Uma lista de objetos, cada um representando uma cobrança paga.

    Raises:
        HTTPException: Se ocorrer um erro na comunicação com o Supabase.
    """
    cobrancas_formatadas = []
    table_name = "Cobranca"
    
    # ✅ Altera o filtro para buscar cobranças com status_pagamento igual a TRUE
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?status_pagamento=eq.true"
    
    try:
        headers = _get_headers()
        response = requests.get(url, headers=headers, timeout=15.0)
        response.raise_for_status()

        cobrancas_pagas = response.json()

        # Itera sobre os resultados para formatar a resposta
        for cobranca in cobrancas_pagas:
            # Converte a string de data/hora para um objeto de data Python
            vencimento_dt = datetime.fromisoformat(cobranca['vencimento']).date()

            # ✅ Utiliza o novo modelo de resposta
            item_formatado = CobrancaPagaResponse(
                cliente=cobranca.get('cliente', 'N/A'),
                vencimento=str(vencimento_dt),
                valor=cobranca.get('valor', 0.0)
                # O status "Pago" é definido pelo modelo Pydantic
            )
            cobrancas_formatadas.append(item_formatado)

    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if e.response else str(e)
        raise HTTPException(
            status_code=e.response.status_code if e.response else 500,
            detail=f"Erro ao buscar cobranças no Supabase: {error_detail}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro de comunicação com o Supabase: {e}"
        )
    except (KeyError, TypeError) as e:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar os dados recebidos do Supabase. Campo faltando ou tipo inválido: {e}"
        )

    return cobrancas_formatadas

@router.post("/pagar_cobranca", response_model=PagarCobrancaResponse)
def pagar_cobranca(cobranca_info: PagarCobrancaInput):
    """
    Recebe os dados de uma cobrança (cliente, vencimento e valor), localiza o
    registro correspondente no Supabase e atualiza seu 'status_pagamento' para TRUE.

    A busca pelo 'vencimento' considera apenas a data, ignorando a hora.
    
    Args:
        cobranca_info: Um objeto contendo 'cliente', 'vencimento' e 'valor'.
        
    Returns:
        Uma mensagem de sucesso com os dados da cobrança atualizada.
        
    Raises:
        HTTPException: Se a cobrança não for encontrada ou se a requisição ao Supabase falhar.
    """
    table_name = "Cobranca"
    
    # 1. Define o payload da atualização (o que vamos mudar)
    payload = {"status_pagamento": True}
    
    # 2. Constrói os filtros para a busca (query params)
    # Para buscar pela data de vencimento ignorando a hora, criamos um intervalo
    # que vai do início ao fim do dia informado.
    start_of_day = datetime.combine(cobranca_info.vencimento, time.min)
    end_of_day = start_of_day + timedelta(days=1)
    
    params = {
        "cliente": f"eq.{cobranca_info.cliente}",
        "valor": f"eq.{cobranca_info.valor}",
        "vencimento": f"gte.{start_of_day.isoformat()}", # gte = Greater Than or Equal
        "vencimento": f"lt.{end_of_day.isoformat()}",   # lt = Less Than
    }

    try:
        headers = _get_headers()
        url = f"{SUPABASE_URL}/rest/v1/{table_name}"
        
        # Usamos o método PATCH para atualizar dados existentes
        response = requests.patch(url, headers=headers, params=params, json=payload, timeout=15.0)
        
        response.raise_for_status()
        
        data = response.json()
        
        # Se a resposta for uma lista vazia, nenhum registro foi encontrado/atualizado
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhuma cobrança encontrada com os critérios especificados."
            )
            
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if e.response else str(e)
        raise HTTPException(
            status_code=e.response.status_code if e.response else 500,
            detail=f"Erro do Supabase: {error_detail}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro de comunicação com o Supabase: {e}"
        )
        
    return {
        "message": f"Pagamento da cobrança para '{cobranca_info.cliente}' registrado com sucesso!",
        "data": data
    }






















