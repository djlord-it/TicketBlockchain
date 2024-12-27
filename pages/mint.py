# pages/mint.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox, QMessageBox
from PyQt6.QtCore import Qt
from blockchain_ticketing import TicketType, TicketingBlockchain


class MintPage(QWidget):
    def __init__(self, blockchain: TicketingBlockchain):
        super().__init__()
        self.blockchain = blockchain

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("Mint Tickets")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Select Event:"))
        self.mint_event_combo = QComboBox()
        layout.addWidget(self.mint_event_combo)

        layout.addWidget(QLabel("Ticket Type:"))
        self.ticket_type_combo = QComboBox()
        for ttype in TicketType:
            self.ticket_type_combo.addItem(ttype.value.capitalize(), ttype)
        layout.addWidget(self.ticket_type_combo)

        layout.addWidget(QLabel("Wallet Address (Buyer):"))
        self.mint_wallet_input = QLineEdit()
        layout.addWidget(self.mint_wallet_input)

        mint_btn = QPushButton("Mint Ticket")
        mint_btn.clicked.connect(self.mintTicket)
        layout.addWidget(mint_btn)

        layout.addStretch()

    def mintTicket(self):
        event_id = self.mint_event_combo.currentData()
        ticket_type = self.ticket_type_combo.currentData()
        wallet = self.mint_wallet_input.text().strip()

        if not event_id or not wallet:
            QMessageBox.warning(self, "Error", "Please select an event and enter a wallet address.")
            return

        try:
            ticket = self.blockchain.mint_ticket(event_id, wallet, ticket_type)
            QMessageBox.information(
                self,
                "Success",
                f"Ticket minted successfully!\nTicket ID: {ticket.ticket_id}"
            )
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def updateEventList(self):
        """Called by main to refresh the event combo with current events."""
        self.mint_event_combo.clear()
        for event_id, event_obj in self.blockchain.events.items():
            self.mint_event_combo.addItem(event_obj.name, event_id)
