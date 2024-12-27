from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from blockchain_ticketing import TicketType, TicketingBlockchain


class AddConcertPage(QWidget):
    def __init__(self, blockchain: TicketingBlockchain, update_event_combos_callback):
        super().__init__()
        self.blockchain = blockchain
        self.update_event_combos_callback = update_event_combos_callback

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("Add a Concert (Event)")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # Concert Name
        layout.addWidget(QLabel("Concert Name:"))
        self.concert_name_input = QLineEdit()
        self.concert_name_input.setStyleSheet("color: #333333; padding: 8px;")
        layout.addWidget(self.concert_name_input)

        # Venue
        layout.addWidget(QLabel("Venue:"))
        self.venue_input = QLineEdit()
        self.venue_input.setStyleSheet("color: #333333; padding: 8px;")
        layout.addWidget(self.venue_input)

        # Date
        layout.addWidget(QLabel("Date (YYYY-MM-DD HH:MM):"))
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("e.g. 2024-06-15 20:30")
        self.date_input.setStyleSheet("color: #333333; padding: 8px;")
        layout.addWidget(self.date_input)

        # Organizer Wallet Address
        layout.addWidget(QLabel("Organizer Wallet Address:"))
        self.organizer_input = QLineEdit()
        self.organizer_input.setStyleSheet("color: #333333; padding: 8px;")
        layout.addWidget(self.organizer_input)

        # Max Tickets per User
        layout.addWidget(QLabel("Max Tickets per User:"))
        self.max_tickets_input = QLineEdit()
        self.max_tickets_input.setText("5")
        self.max_tickets_input.setStyleSheet("color: #333333; padding: 8px;")
        layout.addWidget(self.max_tickets_input)

        # Refundable Until
        layout.addWidget(QLabel("Refundable Until (YYYY-MM-DD HH:MM):"))
        self.refundable_until_input = QLineEdit()
        self.refundable_until_input.setPlaceholderText("e.g. 2024-06-10 23:59")
        self.refundable_until_input.setStyleSheet("color: #333333; padding: 8px;")
        layout.addWidget(self.refundable_until_input)

        # Number of Tickets (Regular)
        layout.addWidget(QLabel("Number of Tickets (Regular):"))
        self.tix_count_input = QLineEdit()
        self.tix_count_input.setText("100")
        self.tix_count_input.setStyleSheet("color: #333333; padding: 8px;")
        layout.addWidget(self.tix_count_input)

        # Ticket Price (Regular)
        layout.addWidget(QLabel("Ticket Price (Regular):"))
        self.tix_price_input = QLineEdit()
        self.tix_price_input.setText("50.0")
        self.tix_price_input.setStyleSheet("color: #333333; padding: 8px;")
        layout.addWidget(self.tix_price_input)

        # Add Concert button
        add_btn = QPushButton("Add Concert")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
        """)
        add_btn.clicked.connect(self.addConcert)
        layout.addWidget(add_btn)

        layout.addStretch()

    def addConcert(self):
        name = self.concert_name_input.text().strip()
        venue = self.venue_input.text().strip()
        date_str = self.date_input.text().strip()
        organizer = self.organizer_input.text().strip()
        refundable_str = self.refundable_until_input.text().strip()

        # Specific validation messages
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a concert name.")
            return
        if not venue:
            QMessageBox.warning(self, "Error", "Please enter a venue.")
            return
        if not date_str:
            QMessageBox.warning(self, "Error", "Please enter an event date.")
            return
        if not " " in date_str:
            QMessageBox.warning(self, "Error", "Event date must include time (YYYY-MM-DD HH:MM)")
            return
        if not organizer:
            QMessageBox.warning(self, "Error", "Please enter an organizer wallet address.")
            return
        if not refundable_str:
            QMessageBox.warning(self, "Error", "Please enter a refundable until date.")
            return
        if not " " in refundable_str:
            QMessageBox.warning(self, "Error", "Refundable date must include time (YYYY-MM-DD HH:MM)")
            return

        try:
            event_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            refundable_until = datetime.strptime(refundable_str, "%Y-%m-%d %H:%M")

            if event_date < datetime.now():
                QMessageBox.warning(self, "Error", "Event date must be in the future.")
                return

            if refundable_until >= event_date:
                QMessageBox.warning(self, "Error", "Refundable until date must be before event date.")
                return
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid date format. Use YYYY-MM-DD HH:MM")
            return

        try:
            max_tickets = int(self.max_tickets_input.text())
            count_regular = int(self.tix_count_input.text())
            price_regular = float(self.tix_price_input.text())

            if max_tickets <= 0:
                QMessageBox.warning(self, "Error", "Max tickets per user must be greater than 0.")
                return
            if count_regular <= 0:
                QMessageBox.warning(self, "Error", "Number of tickets must be greater than 0.")
                return
            if price_regular <= 0:
                QMessageBox.warning(self, "Error", "Ticket price must be greater than 0.")
                return

            event_obj = self.blockchain.create_event(
                name=name,
                venue=venue,
                date=event_date,
                ticket_types={TicketType.REGULAR: count_regular},
                prices={TicketType.REGULAR: price_regular},
                organizer_address=organizer,
                description="Concert event",
                category="Concert",
                max_tickets_per_user=max_tickets,
                refundable_until=refundable_until
            )
            QMessageBox.information(self, "Success", f"Concert '{event_obj.name}' created successfully!")
            self.update_event_combos_callback()
            self._clear_form()
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter valid numbers for tickets and price.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _clear_form(self):
        self.concert_name_input.clear()
        self.venue_input.clear()
        self.date_input.clear()
        self.organizer_input.clear()
        self.refundable_until_input.clear()
        self.max_tickets_input.setText("5")
        self.tix_count_input.setText("100")
        self.tix_price_input.setText("50.0")