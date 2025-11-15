import csv
from typing import Annotated
from semantic_kernel.functions import kernel_function
from config.logging_config import get_logger

logger = get_logger("plugins.search")

class TicketSearchPlugin:
    """Plugin para buscar informações de tickets"""

    def __init__(self, csv_path: str = "data/tickets.csv"):
        self.csv_path = csv_path
        logger.info(f"TicketSearchPlugin inicializado com CSV: {csv_path}")

    @kernel_function(
        name="search_ticket",
        description="Busca um ticket pelo número e retorna todas as informações incluindo status, descrição e responsável"
    )
    def search_ticket(
            self,
            ticket_number: Annotated[str, "O número do ticket a ser buscado (ex: TKT-001)"]
    ) -> str:
        """Busca um ticket específico no CSV"""
        logger.info(f"🔍 Buscando ticket: {ticket_number}")

        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['ticket_number'].lower() == ticket_number.lower():
                        logger.info(f"✅ Ticket {ticket_number} encontrado - Status: {row['status']}")
                        result = f"""
🎫 **Ticket Encontrado**
━━━━━━━━━━━━━━━━━━━━
📌 Número: {row['ticket_number']}
📊 Status: {row['status']}
👤 Responsável: {row['owner']}
📝 Descrição: {row['body']}
"""
                        return result

                logger.warning(f"❌ Ticket {ticket_number} não encontrado")
                return f"❌ Ticket {ticket_number} não encontrado no sistema."

        except FileNotFoundError:
            logger.error(f"❌ Arquivo CSV não encontrado: {self.csv_path}")
            return f"❌ Erro: Arquivo de tickets não encontrado."
        except Exception as e:
            logger.error(f"❌ Erro ao buscar ticket {ticket_number}: {str(e)}", exc_info=True)
            return f"❌ Erro ao buscar ticket: {str(e)}"

    @kernel_function(
        name="list_all_tickets",
        description="Lista todos os tickets disponíveis no sistema"
    )
    def list_all_tickets(self) -> str:
        """Lista todos os tickets"""
        logger.info("📋 Listando todos os tickets")

        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                tickets = list(reader)

                if not tickets:
                    logger.warning("Nenhum ticket encontrado no CSV")
                    return "📋 Nenhum ticket encontrado."

                logger.info(f"✅ {len(tickets)} tickets encontrados")

                result = "📋 **Lista de Tickets**\n━━━━━━━━━━━━━━━━━━━━\n\n"
                for ticket in tickets:
                    result += f"🎫 {ticket['ticket_number']} - Status: {ticket['status']} - Owner: {ticket['owner']}\n"

                return result

        except Exception as e:
            logger.error(f"❌ Erro ao listar tickets: {str(e)}", exc_info=True)
            return f"❌ Erro ao listar tickets: {str(e)}"