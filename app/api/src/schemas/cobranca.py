# models.py (ou no mesmo arquivo da rota)

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime,date

# Modelo para os detalhes de cada categoria (pendentes/vencidas)
class CobrancaStatusDetalhes(BaseModel):
    quantidade: int = Field(default=0, description="Número de cobranças nesta categoria.")
    valor_total: float = Field(default=0.0, description="Soma dos valores das cobranças nesta categoria.")

# Modelo principal para a resposta da rota /pendentes
class RelatorioCobrancas(BaseModel):
    pendentes: CobrancaStatusDetalhes
    vencidas: CobrancaStatusDetalhes
    total_a_receber: float = Field(description="Valor total a receber (soma de pendentes e vencidas).")

# Modelo de entrada (reutilizado do seu exemplo, para referência)
class CobrancaSummaryInput(BaseModel):
    cliente: str
    vencimento: datetime
    valor: float
    status_pagamento: bool = False

from pydantic import BaseModel, Field
from typing import List

# --- Response Model para a Rota: GET /pendentes ---

class TotaisPorStatus(BaseModel):
    """
    Define a estrutura para o total e a quantidade de um status específico.
    """
    total: float = Field(..., description="O valor monetário total das cobranças neste status.")
    quantidade: int = Field(..., description="O número de cobranças neste status.")

class TotaisCobrancasResponse(BaseModel):
    """
    Define a estrutura de resposta completa para a rota de totais de cobranças.
    """
    pendentes: TotaisPorStatus
    vencidas: TotaisPorStatus
    total_a_receber: TotaisPorStatus


# --- Response Model para a Rota: GET /lista_cobrancas ---

class CobrancaDetalheResponse(BaseModel):
    """
    Define a estrutura de um item individual na lista de cobranças ativas.
    """
    cliente: str = Field(..., description="Nome do cliente/empresa.")
    vencimento: str = Field(..., description="Data de vencimento no formato string ISO (YYYY-MM-DD).")
    valor: float = Field(..., description="Valor da cobrança.")
    status: str = Field(..., description="Status calculado: 'Pendente' (a vencer) ou 'Vencido'.")
class CobrancaPagaResponse(BaseModel):
    """
    Define a estrutura de um item individual na lista de cobranças pagas.
    """
    cliente: str = Field(..., description="Nome do cliente/empresa.")
    vencimento: str = Field(..., description="Data em que a cobrança venceu (formato YYYY-MM-DD).")
    valor: float = Field(..., description="Valor da cobrança.")
    status: str = Field(default="Pago", description="Status fixo da cobrança.")

class StatusSummary(BaseModel):
    """
    Model for the 'pendentes' and 'vencidas' objects.
    """
    quantidade: int
    valor_total: float

class NonPaidBill(BaseModel):
    """
    Model for an item in the 'cobrancas_nao_pagas' list.
    """
    id: int
    created_at: Optional[datetime] = None  # Using Optional since the example shows 'null'
    status_pagamento: bool
    cliente: str
    vencimento: datetime
    data_venda: datetime
    valor: float

## --- Main Response Model --- ##

class FinancialSummaryResponse(BaseModel):
    """
    The main Pydantic model for the entire JSON response.
    """
    pendentes: StatusSummary
    vencidas: StatusSummary
    total_a_receber: float
    cobrancas_nao_pagas: List[NonPaidBill]
class PagarCobrancaInput(BaseModel):
    """Schema para os dados de entrada da rota de pagamento."""
    cliente: str = Field(..., description="Nome do cliente para identificar a cobrança.")
    vencimento: date = Field(..., description="Data de vencimento da cobrança (YYYY-MM-DD).")
    valor: float = Field(..., description="Valor exato da cobrança a ser paga.")

class CobrancaData(BaseModel):
    """Schema para representar uma linha da tabela 'Cobranca' retornada pela API."""
    id: int
    created_at: Optional[datetime] = None
    status_pagamento: bool
    cliente: str
    vencimento: datetime
    data_venda: Optional[datetime] = None
    valor: float

class PagarCobrancaResponse(BaseModel):
    """Schema para a resposta de sucesso da rota."""
    message: str
    data: List[CobrancaData]