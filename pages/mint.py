import qrcode
import io
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QDialog, QMessageBox, QProgressBar,
    QHBoxLayout, QGridLayout, QGroupBox
)

from datetime import datetime
from blockchain_ticketing import TicketType, TicketingBlockchain


class MintPage(QWidget):
    def __init__(self, blockchain: TicketingBlockchain):
        super().__init__()
        self.blockchain = blockchain
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        title_box = QGroupBox("Mint New Tickets")
        title_layout = QVBoxLayout()

        event_layout = QGridLayout()
        event_layout.addWidget(QLabel("Select Event:"), 0, 0)
        self.mint_event_combo = QComboBox()
        self.mint_event_combo.currentIndexChanged.connect(self.update_event_details)
        event_layout.addWidget(self.mint_event_combo, 0, 1)

        self.event_date_label = QLabel("Date: ")
        self.event_venue_label = QLabel("Venue: ")
        self.available_tickets_label = QLabel("Available: ")

        event_layout.addWidget(self.event_date_label, 1, 0)
        event_layout.addWidget(self.event_venue_label, 1, 1)
        event_layout.addWidget(self.available_tickets_label, 2, 0)

        title_layout.addLayout(event_layout)
        title_box.setLayout(title_layout)
        layout.addWidget(title_box)

        ticket_box = QGroupBox("Ticket Details")
        ticket_layout = QGridLayout()

        ticket_layout.addWidget(QLabel("Ticket Type:"), 0, 0)
        self.ticket_type_combo = QComboBox()
        for ttype in TicketType:
            self.ticket_type_combo.addItem(ttype.value.capitalize(), ttype)
        self.ticket_type_combo.currentIndexChanged.connect(self.update_price_display)
        ticket_layout.addWidget(self.ticket_type_combo, 0, 1)

        self.price_label = QLabel("Price: ")
        ticket_layout.addWidget(self.price_label, 1, 0, 1, 2)

        ticket_layout.addWidget(QLabel("Buyer Wallet Address:"), 2, 0)
        self.mint_wallet_input = QLineEdit()
        ticket_layout.addWidget(self.mint_wallet_input, 2, 1)

        self.student_id_label = QLabel("Student ID:")
        self.student_id_input = QLineEdit()
        self.student_id_label.setVisible(False)
        self.student_id_input.setVisible(False)
        ticket_layout.addWidget(self.student_id_label, 3, 0)
        ticket_layout.addWidget(self.student_id_input, 3, 1)

        ticket_box.setLayout(ticket_layout)
        layout.addWidget(ticket_box)

        button_layout = QHBoxLayout()
        self.mint_btn = QPushButton("Mint Ticket")
        self.mint_btn.clicked.connect(self.mintTicket)
        button_layout.addWidget(self.mint_btn)

        self.waitlist_btn = QPushButton("Join Waitlist")
        self.waitlist_btn.clicked.connect(self.joinWaitlist)
        button_layout.addWidget(self.waitlist_btn)

        layout.addLayout(button_layout)

        self.status_bar = QProgressBar()
        self.status_bar.setTextVisible(False)
        self.status_bar.setVisible(False)
        layout.addWidget(self.status_bar)
        layout.addStretch()

        self.ticket_type_combo.currentIndexChanged.connect(self.handle_ticket_type_change)

    def handle_ticket_type_change(self):
        ticket_type = self.ticket_type_combo.currentData()
        if ticket_type == TicketType.STUDENT:
            self.student_id_label.setVisible(True)
            self.student_id_input.setVisible(True)
        else:
            self.student_id_label.setVisible(False)
            self.student_id_input.setVisible(False)

    def update_event_details(self):
        event_id = self.mint_event_combo.currentData()
        if event_id in self.blockchain.events:
            event = self.blockchain.events[event_id]
            self.event_date_label.setText(f"Date: {event.date.strftime('%Y-%m-%d %H:%M')}")
            self.event_venue_label.setText(f"Venue: {event.venue}")

            available = sum(event.available_tickets.values())
            self.available_tickets_label.setText(f"Available Tickets: {available}")

            self.mint_btn.setEnabled(available > 0)
            self.waitlist_btn.setEnabled(available == 0)
            self.update_price_display()

    def update_price_display(self):
        event_id = self.mint_event_combo.currentData()
        ticket_type = self.ticket_type_combo.currentData()
        if event_id in self.blockchain.events and ticket_type:
            event = self.blockchain.events[event_id]
            price = event.prices.get(ticket_type, 0)
            self.price_label.setText(f"Price: ${price:.2f}")
            if event.available_tickets.get(ticket_type, 0) == 0:
                self.price_label.setText(f"Price: ${price:.2f} (SOLD OUT)")

    @staticmethod
    def generate_qr_pixmap(data: str) -> QPixmap:
        qr = qrcode.QRCode(version=1, box_size=4, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        qimage = QImage.fromData(buffer.getvalue(), "PNG")
        pixmap = QPixmap.fromImage(qimage)
        return pixmap

    def mintTicket(self):
        self.status_bar.setVisible(True)
        self.status_bar.setRange(0, 0)

        event_id = self.mint_event_combo.currentData()
        ticket_type = self.ticket_type_combo.currentData()
        wallet = self.mint_wallet_input.text().strip()
        if not event_id or not wallet:
            QMessageBox.warning(self, "Error", "Select event and enter wallet address.")
            self.status_bar.setVisible(False)
            return

        if ticket_type == TicketType.STUDENT and not self.student_id_input.text().strip():
            QMessageBox.warning(self, "Error", "Please enter a valid student ID.")
            self.status_bar.setVisible(False)
            return

        try:
            ticket = self.blockchain.mint_ticket(event_id, wallet, ticket_type)

            qr_pixmap = self.generate_qr_pixmap(ticket.qr_code)

            msg = QMessageBox(self)
            msg.setWindowTitle("Ticket Minted")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(
                f"Ticket ID: {ticket.ticket_id}\n\n"
                f"Below is your QR code image. Keep it safe!"
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()

            dialog = QDialog(self)
            dialog.setWindowTitle("Your QR Code")
            dialog_layout = QVBoxLayout(dialog)

            qr_label = QLabel()
            qr_label.setPixmap(qr_pixmap)
            dialog_layout.addWidget(qr_label)

            dialog.exec()

            self.mint_wallet_input.clear()
            self.student_id_input.clear()
            self.update_event_details()

        except ValueError as e:
            self.status_bar.setVisible(False)
            QMessageBox.warning(self, "Error", str(e))

    def joinWaitlist(self):
        event_id = self.mint_event_combo.currentData()
        wallet = self.mint_wallet_input.text().strip()
        if not event_id or not wallet:
            QMessageBox.warning(self, "Error", "Select event and enter wallet address.")
            return
        try:
            event = self.blockchain.events[event_id]
            event.waitlist.add(wallet)
            QMessageBox.information(self, "Waitlist", "You have been added to the waitlist.")
            self.mint_wallet_input.clear()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def updateEventList(self):
        self.mint_event_combo.clear()
        sorted_events = sorted(
            self.blockchain.events.items(),
            key=lambda x: x[1].date
        )
        for eid, ev in sorted_events:
            if ev.date > datetime.now() and not ev.is_cancelled:
                self.mint_event_combo.addItem(
                    f"{ev.name} ({ev.date.strftime('%Y-%m-%d')})", eid
                )
