# Produto schema
# --- Schemas de Produto ---
from pydantic import BaseModel, Field
# Schema base com os campos comuns
class ProdutoBase(BaseModel):
    nome: str = Field(..., description="Nome do tipo de brownie, ex: Brownie Tradicional")
    valor_unitario: float = Field(..., gt=0, description="Valor de venda por unidade do brownie")
class CategoriaEmEstoque(BaseModel):
    categoria: str = Field(..., description="Categoria do produto")
    quantidade_estoque: int = Field(..., ge=0, description="Quantidade atual em estoque")
# Schema para criação de um novo produto (não inclui estoque inicial)
class ProdutoCreate(ProdutoBase):
    pass

# Schema para atualizar a quantidade em estoque
class ProdutoUpdateEstoque(BaseModel):
    quantidade: int = Field(..., ge=0, description="Nova quantidade total em estoque")
class ProdutoAddEstoque(BaseModel):
    quantidade: int = Field(..., gt=0, description="Quantidade a ser adicionada ao estoque atual")

# Schema completo para leitura (retorno da API), incluindo o ID e o estoque
class Produto(ProdutoBase):
    id: int
    quantidade_estoque: int = Field(..., ge=0, description="Quantidade atual em estoque")

    class Config:
        from_attributes = True
class EstoqueRequest(BaseModel):
    categoria: str = Field(..., description="Categoria do produto")
class AtualizarEstoqueRequest(BaseModel):
    categoria: str = Field(..., description="Categoria do produto")
    quantidade: int  = Field (...,description="Quantidade alvo")

class PrecoUnitarioRequest(BaseModel):
    """Modelo para a requisição do preço unitário de uma categoria."""
    categoria: str
class EstoqueRequest(BaseModel):
    """
    Schema para a requisição de obtenção de estoque de uma categoria.
    """
    categoria: str = Field(..., example="Pizza", description="Nome da categoria do produto.")

class AtualizarEstoqueRequest(BaseModel):
    """
    Schema para a requisição de atualização de estoque de uma categoria.
    """
    categoria: str = Field(..., example="Pizza", description="Nome da categoria do produto a ser atualizada.")
    quantidade: int = Field(..., example=10, description="A nova quantidade total em estoque para a categoria.")

# src/brownie_api/schemas/produto.py



# ... (outras classes de schema de Produto)

class ProdutoUpdateEstoque(BaseModel):
    """Schema para receber a nova quantidade de estoque."""
    quantidade: int = Field(..., ge=0, description="A nova quantidade total em estoque do produto")