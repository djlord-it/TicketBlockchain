from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QGridLayout, QHBoxLayout,
    QProgressBar, QFrame
    )
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime, timedelta
from blockchain_ticketing import TicketingBlockchain, TicketStatus, TicketType

class TransferPage(QWidget):
    def __init__(self, blockchain: TicketingBlockchain):
        super().__init__()
        self.blockchain = blockchain
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Title
        ticket_box = QGroupBox("Ticket Information")
        ticket_layout = QGridLayout()

        ticket_layout.addWidget(QLabel("Ticket ID:"), 0, 0)
        self.transfer_ticket_id = QLineEdit()
        self.transfer_ticket_id.textChanged.connect(self.load_ticket_details)
        ticket_layout.addWidget(self.transfer_ticket_id, 0, 1)

        self.ticket_details = QLabel()
        ticket_layout.addWidget(self.ticket_details, 1, 0, 1, 2)

        self.cooldown_frame = QFrame()
        cooldown_layout = QHBoxLayout(self.cooldown_frame)
        self.cooldown_label = QLabel()
        cooldown_layout.addWidget(self.cooldown_label)
        self.cooldown_frame.setVisible(False)
        ticket_layout.addWidget(self.cooldown_frame, 2, 0, 1, 2)

        ticket_box.setLayout(ticket_layout)
        layout.addWidget(ticket_box)

        # Transfer Details
        transfer_box = QGroupBox("Transfer Details")
        transfer_layout = QGridLayout()

        transfer_layout.addWidget(QLabel("Current Owner:"), 0, 0)
        self.transfer_from_input = QLineEdit()
        self.transfer_from_input.setReadOnly(True)
        transfer_layout.addWidget(self.transfer_from_input, 0, 1)

        transfer_layout.addWidget(QLabel("New Owner:"), 1, 0)
        self.transfer_to_input = QLineEdit()
        transfer_layout.addWidget(self.transfer_to_input, 1, 1)

        transfer_layout.addWidget(QLabel("Price:"), 2, 0)
        self.transfer_price_input = QLineEdit("0.0")  # replaced QDoubleSpinBox
        transfer_layout.addWidget(self.transfer_price_input, 2, 1)

        self.price_recommendation = QLabel()
        transfer_layout.addWidget(self.price_recommendation, 3, 0, 1, 2)

        transfer_box.setLayout(transfer_layout)
        layout.addWidget(transfer_box)

        # Action Buttons
        button_layout = QHBoxLayout()
        self.initiate_transfer_btn = QPushButton("Initiate Transfer")
        self.initiate_transfer_btn.clicked.connect(self.initiateTransfer)
        button_layout.addWidget(self.initiate_transfer_btn)

        self.confirm_transfer_btn = QPushButton("Confirm Transfer")
        self.confirm_transfer_btn.clicked.connect(self.confirmTransfer)
        self.confirm_transfer_btn.setVisible(False)
        button_layout.addWidget(self.confirm_transfer_btn)

        layout.addLayout(button_layout)

        # Status Bar
        self.status_bar = QProgressBar()
        self.status_bar.setTextVisible(False)
        self.status_bar.setVisible(False)
        layout.addWidget(self.status_bar)

        # cooldown timer
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_cooldown)

        layout.addStretch()

    def load_ticket_details(self):
        ticket_id = self.transfer_ticket_id.text().strip()
        if not ticket_id:
            self.clear_details()
            return

        if ticket_id not in self.blockchain.tickets:
            self.clear_details()
            return

        ticket = self.blockchain.tickets[ticket_id]
        event = self.blockchain.events[ticket.event_id]
        details = (
            f"Event: {event.name}\n"
            f"Date: {event.date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Type: {ticket.ticket_type.value.capitalize()}\n"
            f"Status: {ticket.status.value.capitalize()}\n"
            f"Original Price: ${ticket.price:.2f}"
        )
        self.ticket_details.setText(details)
        self.transfer_from_input.setText(ticket.owner_address)

        min_price = event.minimum_price.get(ticket.ticket_type, 0.0)
        rec_text = f"Minimum: ${min_price:.2f} | No strict max"
        self.price_recommendation.setText(rec_text)

        if ticket.status == TicketStatus.PENDING_TRANSFER:
            self.initiate_transfer_btn.setVisible(False)
            self.confirm_transfer_btn.setVisible(True)
        else:
            self.initiate_transfer_btn.setVisible(True)
            self.confirm_transfer_btn.setVisible(False)

        self.update_cooldown_frame(ticket)

    def update_cooldown_frame(self, ticket):
        now = datetime.now()
        event = self.blockchain.events[ticket.event_id]
        cooldown_needed = event.ticket_transfer_cooldown

        if ticket.last_transfer and ticket.status == TicketStatus.VALID:
            elapsed = now - ticket.last_transfer
            if elapsed < cooldown_needed:
                remaining = cooldown_needed - elapsed
                mins = remaining.seconds // 60
                self.cooldown_label.setText(f"Transfer cooldown active. Wait ~{mins} minutes.")
                self.cooldown_frame.setVisible(True)
                self.countdown_timer.start(60000)  # update every minute
            else:
                self.cooldown_frame.setVisible(False)
                self.countdown_timer.stop()
        else:
            self.cooldown_frame.setVisible(False)
            self.countdown_timer.stop()

    def update_cooldown(self):
        ticket_id = self.transfer_ticket_id.text().strip()
        if ticket_id in self.blockchain.tickets:
            ticket = self.blockchain.tickets[ticket_id]
            self.update_cooldown_frame(ticket)

    def clear_details(self):
        self.ticket_details.setText("")
        self.transfer_from_input.setText("")
        self.price_recommendation.setText("")
        self.cooldown_frame.setVisible(False)
        self.initiate_transfer_btn.setVisible(True)
        self.confirm_transfer_btn.setVisible(False)

    def initiateTransfer(self):
        self.status_bar.setVisible(True)
        self.status_bar.setRange(0, 0)

        ticket_id = self.transfer_ticket_id.text().strip()
        if ticket_id not in self.blockchain.tickets:
            QMessageBox.warning(self, "Error", "Invalid Ticket ID.")
            self.status_bar.setVisible(False)
            return

        ticket = self.blockchain.tickets[ticket_id]
        from_addr = ticket.owner_address
        to_addr = self.transfer_to_input.text().strip()

        try:
            price_val = float(self.transfer_price_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Error", "Price must be a number.")
            self.status_bar.setVisible(False)
            return

        if not to_addr:
            QMessageBox.warning(self, "Error", "Please enter the new owner's address.")
            self.status_bar.setVisible(False)
            return

        try:
            self.blockchain.transfer_ticket(ticket_id, from_addr, to_addr, price_val)
            self.status_bar.setRange(0, 100)
            self.status_bar.setValue(100)
            QTimer.singleShot(1000, lambda: self.status_bar.setVisible(False))

            QMessageBox.information(
                self,
                "Transfer Initiated",
                "Ticket transfer initiated. The new owner must confirm within 24 hours."
            )
            self.load_ticket_details()

        except ValueError as e:
            self.status_bar.setVisible(False)
            QMessageBox.warning(self, "Error", str(e))

    def confirmTransfer(self):
        self.status_bar.setVisible(True)
        self.status_bar.setRange(0, 0)

        ticket_id = self.transfer_ticket_id.text().strip()
        if ticket_id not in self.blockchain.tickets:
            QMessageBox.warning(self, "Error", "Invalid Ticket ID.")
            self.status_bar.setVisible(False)
            return

        ticket = self.blockchain.tickets[ticket_id]
        to_addr = self.transfer_to_input.text().strip()
        if not to_addr:
            QMessageBox.warning(self, "Error", "No target address to confirm.")
            self.status_bar.setVisible(False)
            return

        try:
            self.blockchain.confirm_transfer(ticket_id, to_addr)
            self.status_bar.setRange(0, 100)
            self.status_bar.setValue(100)
            QTimer.singleShot(1000, lambda: self.status_bar.setVisible(False))

            QMessageBox.information(
                self,
                "Transfer Confirmed",
                "Ticket ownership has been successfully updated!"
            )
            self.load_ticket_details()

        except ValueError as e:
            self.status_bar.setVisible(False)
            QMessageBox.warning(self, "Error", str(e))
