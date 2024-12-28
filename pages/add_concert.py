from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QGroupBox, QGridLayout, QDateTimeEdit
)
from PyQt6.QtCore import Qt, QDateTime
from datetime import datetime, timedelta
from blockchain_ticketing import TicketingBlockchain, TicketType


class AddConcertPage(QWidget):
    def __init__(self, blockchain: TicketingBlockchain, update_event_combos_callback=None):
        super().__init__()
        self.blockchain = blockchain
        self.update_event_combos_callback = update_event_combos_callback
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title_label = QLabel("Create a New Concert (Event)")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)

        #Event Information Group
        event_box = QGroupBox("Event Information")
        event_layout = QGridLayout()

        event_layout.addWidget(QLabel("Event Name:"), 0, 0)
        self.concert_name_input = QLineEdit()
        event_layout.addWidget(self.concert_name_input, 0, 1)

        event_layout.addWidget(QLabel("Venue:"), 1, 0)
        self.venue_input = QLineEdit()
        event_layout.addWidget(self.venue_input, 1, 1)

        event_layout.addWidget(QLabel("Event Date & Time:"), 2, 0)
        self.date_input = QDateTimeEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDateTime(QDateTime.currentDateTime().addDays(7))
        event_layout.addWidget(self.date_input, 2, 1)

        event_layout.addWidget(QLabel("Organizer Address:"), 3, 0)
        self.organizer_input = QLineEdit()
        event_layout.addWidget(self.organizer_input, 3, 1)

        event_layout.addWidget(QLabel("Category:"), 4, 0)
        self.category_input = QLineEdit("Music")
        event_layout.addWidget(self.category_input, 4, 1)

        event_layout.addWidget(QLabel("Description:"), 5, 0)
        self.description_input = QLineEdit("A fantastic live event")
        event_layout.addWidget(self.description_input, 5, 1)

        event_box.setLayout(event_layout)
        layout.addWidget(event_box)

        #Ticket Types & Prices Group
        ticket_box = QGroupBox("Ticket Types & Prices")
        ticket_layout = QGridLayout()

        self.ticket_count_inputs = {}
        self.ticket_price_inputs = {}

        row_idx = 0
        for ttype in TicketType:
            label_type = QLabel(f"{ttype.value.capitalize()} Tickets:")

            #QLineEdit for count
            count_input = QLineEdit()
            count_input.setPlaceholderText("Count (e.g. 10)")
            count_input.setText("10" if ttype == TicketType.REGULAR else "5")

            #QLineEdit for price
            price_input = QLineEdit()
            price_input.setPlaceholderText("Price (e.g. 50.0)")
            if ttype == TicketType.REGULAR:
                price_input.setText("50.0")
            else:
                price_input.setText("80.0")

            ticket_layout.addWidget(label_type, row_idx, 0)
            ticket_layout.addWidget(QLabel("Count:"), row_idx, 1)
            ticket_layout.addWidget(count_input, row_idx, 2)
            ticket_layout.addWidget(QLabel("Price:"), row_idx, 3)
            ticket_layout.addWidget(price_input, row_idx, 4)

            self.ticket_count_inputs[ttype] = count_input
            self.ticket_price_inputs[ttype] = price_input
            row_idx += 1

        ticket_box.setLayout(ticket_layout)
        layout.addWidget(ticket_box)

        #Additional Settings Group
        settings_box = QGroupBox("Additional Settings")
        settings_layout = QGridLayout()

        settings_layout.addWidget(QLabel("Max Tickets per User:"), 0, 0)
        self.max_tickets_input = QLineEdit("4")
        settings_layout.addWidget(self.max_tickets_input, 0, 1)

        settings_layout.addWidget(QLabel("Refundable Until:"), 1, 0)
        self.refundable_until_input = QDateTimeEdit()
        self.refundable_until_input.setCalendarPopup(True)
        self.refundable_until_input.setDateTime(QDateTime.currentDateTime().addDays(6))
        settings_layout.addWidget(self.refundable_until_input, 1, 1)

        settings_layout.addWidget(QLabel("Transfer Cooldown (minutes):"), 2, 0)
        self.cooldown_input = QLineEdit("30")
        settings_layout.addWidget(self.cooldown_input, 2, 1)

        self.create_event_btn = QPushButton("Create Event")
        self.create_event_btn.clicked.connect(self.createEvent)
        settings_layout.addWidget(self.create_event_btn, 3, 0, 1, 2)

        settings_box.setLayout(settings_layout)
        layout.addWidget(settings_box)

        layout.addStretch()

    def createEvent(self):
        name = self.concert_name_input.text().strip()
        venue = self.venue_input.text().strip()
        dt = self.date_input.dateTime().toPyDateTime()
        organizer = self.organizer_input.text().strip()
        category = self.category_input.text().strip()
        description = self.description_input.text().strip()
        refundable_dt = self.refundable_until_input.dateTime().toPyDateTime()

        # parse max_tickets_per_user from QLineEdit
        try:
            max_tickets_per_user = int(self.max_tickets_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Error", "Max Tickets per User must be an integer.")
            return

        # parse cooldown minutes
        try:
            cooldown_minutes = int(self.cooldown_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Error", "Transfer Cooldown must be an integer (minutes).")
            return

        if not name or not venue or not organizer:
            QMessageBox.warning(self, "Error", "Please fill in all required fields.")
            return
        if dt <= datetime.now():
            QMessageBox.warning(self, "Error", "Event date must be in the future.")
            return
        if refundable_dt <= datetime.now():
            QMessageBox.warning(self, "Error", "Refundable-until date must be in the future.")
            return

        # parse ticket_types & prices
        ticket_types = {}
        prices = {}
        for ttype in TicketType:
            try:
                cnt_val = int(self.ticket_count_inputs[ttype].text().strip())
                price_val = float(self.ticket_price_inputs[ttype].text().strip())
            except ValueError:
                QMessageBox.warning(self, "Error", f"Invalid count/price for {ttype.value.capitalize()} Tickets.")
                return

            ticket_types[ttype] = cnt_val
            prices[ttype] = price_val

        try:
            event_obj = self.blockchain.create_event(
                name=name,
                venue=venue,
                date=dt,
                ticket_types=ticket_types,
                prices=prices,
                organizer_address=organizer,
                description=description,
                category=category,
                max_tickets_per_user=max_tickets_per_user,
                refundable_until=refundable_dt
            )

            # Overwrite the event's cooldown if we want user-defined
            event_obj.ticket_transfer_cooldown = timedelta(minutes=cooldown_minutes)

            QMessageBox.information(self, "Success", f"Event '{event_obj.name}' created successfully!")
            self.clearForm()

            if self.update_event_combos_callback:
                self.update_event_combos_callback()

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def clearForm(self):
        self.concert_name_input.clear()
        self.venue_input.clear()
        self.date_input.setDateTime(QDateTime.currentDateTime().addDays(7))
        self.organizer_input.clear()
        self.category_input.setText("Music")
        self.description_input.setText("A fantastic live event")
        self.max_tickets_input.setText("4")
        self.refundable_until_input.setDateTime(QDateTime.currentDateTime().addDays(6))
        self.cooldown_input.setText("30")

        for ttype in TicketType:
            if ttype == TicketType.REGULAR:
                self.ticket_count_inputs[ttype].setText("10")
                self.ticket_price_inputs[ttype].setText("50.0")
            else:
                self.ticket_count_inputs[ttype].setText("5")
                self.ticket_price_inputs[ttype].setText("80.0")
