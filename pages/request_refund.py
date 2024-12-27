# pages/request_refund.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from blockchain_ticketing import TicketingBlockchain


class RequestRefundPage(QWidget):
    def __init__(self, blockchain: TicketingBlockchain):
        super().__init__()
        self.blockchain = blockchain

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("Request Refund")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Ticket ID:"))
        self.refund_ticket_id = QLineEdit()
        layout.addWidget(self.refund_ticket_id)

        layout.addWidget(QLabel("Owner Address:"))
        self.refund_owner_address = QLineEdit()
        layout.addWidget(self.refund_owner_address)

        refund_btn = QPushButton("Request Refund")
        refund_btn.clicked.connect(self.requestRefund)
        layout.addWidget(refund_btn)

        layout.addStretch()

    def requestRefund(self):
        ticket_id = self.refund_ticket_id.text().strip()
        owner = self.refund_owner_address.text().strip()

        if not ticket_id or not owner:
            QMessageBox.warning(self, "Error", "Please fill in ticket ID and owner address.")
            return

        try:
            amount = self.blockchain.request_refund(ticket_id, owner)
            QMessageBox.information(self, "Success", f"Refund issued: ${amount:.2f}")
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
