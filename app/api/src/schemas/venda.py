# Venda schema
from pydantic import BaseModel, Field, computed_field
from datetime import datetime
from .msg import StatusPagamento
from typing import Optional 
# --- Schemas de Venda ---

# Schema base com os campos que vêm do request de criação
class VendaBase(BaseModel):
    cliente_id: int = Field(..., description="ID do cliente que fez a compra")
    produto_id: int = Field(..., description="ID do produto vendido")
    unidades: int = Field(..., gt=0, description="Quantidade de unidades vendidas")
    prazo_dias: int = Field(..., ge=0, description="Prazo em dias para o pagamento")

# Schema para registrar uma nova venda
class VendaCreate(VendaBase):
    # O valor unitário no momento da venda é registrado para garantir consistência,
    # mesmo que o preço do produto mude no futuro.
    valor_unitario: float = Field(..., gt=0, description="Valor unitário do produto no momento da venda")

# Schema para atualizar o status de uma cobrança
class VendaUpdateStatus(BaseModel):
    status_pagamento: StatusPagamento = Field(..., description="Novo status do pagamento")
class CategoriaSchema(BaseModel):
    categoria: str = Field(..., description="Categoria do produto para filtrar o histórico")
class Venda(BaseModel):
    cliente: str
    categoria_produto: str
    qtd_unidades: int
    # 1. Use Optional[float] para permitir None
    # 2. Defina um valor padrão, como None, para torná-lo opcional
    valor_unitario: Optional[float] = None # OU: valor_unitario: float | None = None
    status_pagamento: bool
    data_venda: datetime
    data_vencimento: datetime
    valor_total: float
    # Corrigido para datetime para ser compatível com timestamptz
    
    
    
    
    
    
    # Adicionado o campo que estava faltando
    
    
    # Corrigido para ser um campo normal, lido do banco
    
    
    
    
    # Corrigido para ser um campo normal, lido do banco
    

    # Configuração para permitir a criação do modelo a partir de um objeto de banco de dados
    class Config:
        from_attributes = True