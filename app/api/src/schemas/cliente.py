# Cliente schema
from pydantic import Field,BaseModel
class ClienteBase(BaseModel):
    nome: str = Field(..., description="Nome do cliente, ex: Padaria Central")
    # Outros campos como CNPJ, contato, etc., poderiam ser adicionados aqui

# Schema para criação de um novo cliente
class ClienteCreate(ClienteBase):
    pass

# Schema completo para leitura (retorno da API), incluindo o ID
class Cliente(ClienteBase):
    id: int

    class Config:
        from_attributes = True