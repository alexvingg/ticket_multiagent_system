import csv
from typing import Annotated
from semantic_kernel.functions import kernel_function
from config.logging_config import get_logger
from datetime import datetime

logger = get_logger("plugins.processor")

class TicketProcessorPlugin:
    """Plugin para processar tickets pendentes"""

    def __init__(self, csv_path: str = "data/tickets.csv"):
        self.csv_path = csv_path
        logger.info(f"TicketProcessorPlugin inicializado com CSV: {csv_path}")

    @kernel_function(
        name="process_pending_ticket",
        description="Processa um ticket que está com status 'pending' e altera para 'solved', gerando um novo CSV"
    )
    def process_pending_ticket(
            self,
            ticket_number: Annotated[str, "O número do ticket pendente a ser processado"]
    ) -> str:
        """Processa um ticket pendente e marca como solved"""
        logger.info(f"⚙️ Processando ticket: {ticket_number}")

        try:
            tickets = []
            ticket_found = False
            ticket_was_pending = False
            original_status = None

            # Ler todos os tickets
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                tickets = list(reader)

            logger.debug(f"📖 {len(tickets)} tickets lidos do CSV")

            # Processar o ticket específico
            for ticket in tickets:
                if ticket['ticket_number'].lower() == ticket_number.lower():
                    ticket_found = True
                    original_status = ticket['status']

                    if ticket['status'].lower() == 'pending':
                        ticket['status'] = 'solved'
                        ticket_was_pending = True
                        logger.info(f"✅ Status do ticket {ticket_number} alterado: pending → solved")
                    else:
                        logger.warning(f"⚠️ Ticket {ticket_number} não está pending. Status atual: {original_status}")
                        return f"⚠️ Ticket {ticket_number} não pode ser processado. Status atual: {ticket['status']}. Apenas tickets 'pending' podem ser processados."

            if not ticket_found:
                logger.warning(f"❌ Ticket {ticket_number} não encontrado")
                return f"❌ Ticket {ticket_number} não encontrado."

            if ticket_was_pending:
                # Backup do arquivo original
                backup_path = f"{self.csv_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                with open(self.csv_path, 'r', encoding='utf-8') as original:
                    with open(backup_path, 'w', encoding='utf-8') as backup:
                        backup.write(original.read())
                logger.debug(f"💾 Backup criado: {backup_path}")

                # Salvar novo CSV
                with open(self.csv_path, 'w', encoding='utf-8', newline='') as file:
                    fieldnames = ['ticket_number', 'status', 'body', 'owner']
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(tickets)

                logger.info(f"✅ Ticket {ticket_number} processado e CSV atualizado com sucesso")
                return f"✅ Ticket {ticket_number} processado com sucesso! Status alterado para 'solved'."

        except Exception as e:
            logger.error(f"❌ Erro ao processar ticket {ticket_number}: {str(e)}", exc_info=True)
            return f"❌ Erro ao processar ticket: {str(e)}"

    @kernel_function(
        name="list_pending_tickets",
        description="Lista todos os tickets com status 'pending' que podem ser processados"
    )
    def list_pending_tickets(self) -> str:
        """Lista apenas tickets pendentes"""
        logger.info("📋 Listando tickets pendentes")

        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                pending_tickets = [row for row in reader if row['status'].lower() == 'pending']

                if not pending_tickets:
                    logger.info("Nenhum ticket pendente encontrado")
                    return "📋 Nenhum ticket pendente encontrado."

                logger.info(f"✅ {len(pending_tickets)} tickets pendentes encontrados")

                result = "📋 **Tickets Pendentes**\n━━━━━━━━━━━━━━━━━━━━\n\n"
                for ticket in pending_tickets:
                    result += f"🎫 {ticket['ticket_number']} - Owner: {ticket['owner']} - {ticket['body']}\n"

                return result

        except Exception as e:
            logger.error(f"❌ Erro ao listar tickets pendentes: {str(e)}", exc_info=True)
            return f"❌ Erro ao listar tickets pendentes: {str(e)}"