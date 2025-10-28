# Message schema
import enum


# Enum para o status de pagamento da cobrança
class StatusPagamento(str, enum.Enum):
    PENDENTE = "Pendente"
    PAGO = "Pago"