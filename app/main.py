from fastapi import APIRouter, FastAPI # Import FastAPI
# NOTE: Adjust the import path for your endpoints based on your actual file structure
from app.api.src.routes.atualizar_estoque import router as atualizar_estoque_router
from app.api.src.routes.estoque_atual import router as produtos_router
from app.api.src.routes.vender import router as vendas_router
from app.api.src.routes.historico import router as historico_router
from app.api.src.routes.estoque_atual import router as estoque_atual_router
from app.api.src.routes.cobranca import router as cobranca_router
from app.api.src.routes.clientes import router as clientes_router
# 1. Create the top-level API router for v1
api_router = APIRouter()

# 2. Include the endpoint routers
api_router.include_router(atualizar_estoque_router, prefix="/estoque", tags=["Estoque"])
api_router.include_router(produtos_router, prefix="/produtos", tags=["Produtos"])
api_router.include_router(vendas_router, prefix="/vendas", tags=["Vendas"])
api_router.include_router(historico_router, prefix="/historico", tags=["Histórico de Vendas"])
api_router.include_router(estoque_atual_router, prefix="/estoque", tags=["Estoque"])
api_router.include_router(cobranca_router,prefix='/cobranca',tags=['Cobrança'])
api_router.include_router(clientes_router,prefix='/clientes',tags=['Clientes'])
# 3. Create the main FastAPI application instance
app = FastAPI(
    title="Brownie API",
    version="1.0.0",
    description="API for managing Bonobrownie sales and inventory."
)

# 4. Include the v1 router into the main application, usually with a prefix
app.include_router(api_router, prefix="/api/v1") 

# Optional: Add a root endpoint for health check/discovery
@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API do Bonobrownie! Um projeto pró-bono por luismaiasombra@gmail.com."}