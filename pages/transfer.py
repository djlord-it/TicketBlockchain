# pages/transfer.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QDoubleSpinBox, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from blockchain_ticketing import TicketingBlockchain


class TransferPage(QWidget):
    def __init__(self, blockchain: TicketingBlockchain):
        super().__init__()
        self.blockchain = blockchain

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("Transfer Tickets")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Ticket ID:"))
        self.transfer_ticket_id = QLineEdit()
        layout.addWidget(self.transfer_ticket_id)

        layout.addWidget(QLabel("From (Current Owner):"))
        self.transfer_from_input = QLineEdit()
        layout.addWidget(self.transfer_from_input)

        layout.addWidget(QLabel("To (New Owner):"))
        self.transfer_to_input = QLineEdit()
        layout.addWidget(self.transfer_to_input)

        layout.addWidget(QLabel("Price:"))
        self.transfer_price_input = QDoubleSpinBox()
        self.transfer_price_input.setDecimals(2)
        self.transfer_price_input.setValue(0.0)
        layout.addWidget(self.transfer_price_input)

        btn = QPushButton("Transfer")
        btn.clicked.connect(self.transferTicket)
        layout.addWidget(btn)

        layout.addStretch()

    def transferTicket(self):
        ticket_id = self.transfer_ticket_id.text().strip()
        from_addr = self.transfer_from_input.text().strip()
        to_addr = self.transfer_to_input.text().strip()
        price = self.transfer_price_input.value()

        if not ticket_id or not from_addr or not to_addr:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return

        try:
            self.blockchain.transfer_ticket(ticket_id, from_addr, to_addr, price)
            QMessageBox.information(self, "Success", "Ticket transferred successfully.")
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
