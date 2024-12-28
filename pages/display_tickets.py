from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit
from blockchain_ticketing import TicketingBlockchain


class DisplayTicketsPage(QWidget):
    def __init__(self, blockchain: TicketingBlockchain):
        super().__init__()
        self.blockchain = blockchain

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("Display Event Tickets")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Select Event:"))
        self.display_event_combo = QComboBox()
        layout.addWidget(self.display_event_combo)

        show_btn = QPushButton("Show Tickets")
        show_btn.clicked.connect(self.showEventTickets)
        layout.addWidget(show_btn)

        self.tickets_display_area = QTextEdit()
        self.tickets_display_area.setReadOnly(True)
        layout.addWidget(self.tickets_display_area)

        layout.addStretch()

    def showEventTickets(self):
        self.tickets_display_area.clear()
        event_id = self.display_event_combo.currentData()
        if not event_id:
            self.tickets_display_area.setText("No event selected.")
            return

        tickets = self.blockchain.get_event_tickets(event_id)
        if not tickets:
            self.tickets_display_area.setText("No tickets found for this event.")
            return

        lines = []
        for t in tickets:
            lines.append(
                f"Ticket ID: {t.ticket_id}\n"
                f"Type: {t.ticket_type.value.capitalize()}\n"
                f"Owner: {t.owner_address}\n"
                f"Status: {t.status.value.capitalize()}\n"
                f"Price: ${t.price:.2f}\n"
                f"Purchased At: {t.purchased_at}\n"
                "----------------------------------------"
            )
        self.tickets_display_area.setText("\n".join(lines))

    def updateEventList(self):
        """Refresh the event combo with current events."""
        self.display_event_combo.clear()
        for event_id, event_obj in self.blockchain.events.items():
            self.display_event_combo.addItem(event_obj.name, event_id)
