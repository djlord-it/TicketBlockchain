import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QScrollArea, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Make sure blockchain_ticketing.py is in the same directory or accessible in PYTHONPATH
from blockchain_ticketing import TicketingBlockchain, TicketType, TicketStatus


class ConcertTicketingApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.blockchain = TicketingBlockchain(difficulty=2)
        self.setWindowTitle("Concert Ticketing System")
        self.resize(1200, 800)

        # ---------------------------------------------------------------------
        # 1) Define the button actions FIRST
        # ---------------------------------------------------------------------
        self.buttons_actions = [
            lambda: self.stack.setCurrentIndex(0),  # (1) Add a Concert
            lambda: self.stack.setCurrentIndex(1),  # (2) Mint Tickets
            lambda: self.stack.setCurrentIndex(2),  # (3) Transfer Tickets
            lambda: self.stack.setCurrentIndex(3),  # (4) Display Event Tickets
            lambda: self.stack.setCurrentIndex(4),  # (5) Request Refund
            lambda: self.stack.setCurrentIndex(5),  # (6) Display Event Statistics
        ]

        # ---------------------------------------------------------------------
        # 2) Create the main layout
        # ---------------------------------------------------------------------
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        self.setCentralWidget(main_widget)

        # 3) Create sidebar (uses self.buttons_actions)
        self.sidebar = self.createSidebar()
        main_layout.addWidget(self.sidebar)

        # 4) Create the stacked widget
        self.stack = QStackedWidget()

        # 5) Add pages to the stack
        self.stack.addWidget(self.createAddConcertPage())      # index 0
        self.stack.addWidget(self.createMintPage())            # index 1
        self.stack.addWidget(self.createTransferPage())        # index 2
        self.stack.addWidget(self.createDisplayTicketsPage())  # index 3
        self.stack.addWidget(self.createRefundPage())          # index 4
        self.stack.addWidget(self.createStatsPage())           # index 5

        main_layout.addWidget(self.stack)

        # 6) Apply style sheet
        self.setStyleSheet('''
            QMainWindow {
                background-color: #f5f5f7;
            }
            QWidget#sidebar {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #d1d1d6;
            }
            QLabel#sidebarTitle {
                font-size: 22px; 
                font-weight: 600; 
                color: #333333;
                margin-bottom: 20px;
            }
            QPushButton#sidebarButton {
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                margin: 6px 0;
                font-size: 15px;
                text-align: center;
            }
            QPushButton#sidebarButton:hover {
                background-color: #005bb5;
            }
            QLabel {
                font-size: 15px;
                color: #333333;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
                padding: 8px;
                border: 1px solid #d1d1d6;
                border-radius: 6px;
                background: white;
                font-size: 15px;
            }
            QPushButton {
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
        ''')

        # Populate event combos (if events exist) at startup
        self.updateEventCombos()

    def createSidebar(self):
        """Create the vertical sidebar with six labeled buttons."""
        sidebar = QWidget(objectName="sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Concert Ticketing", objectName="sidebarTitle")
        layout.addWidget(title)

        # Button labels
        button_texts = [
            "1. Add a Concert",
            "2. Mint Tickets",
            "3. Transfer Tickets",
            "4. Display Event Tickets",
            "5. Request Refund",
            "6. Display Event Statistics"
        ]

        # Create the buttons, link them to self.buttons_actions
        for i, text in enumerate(button_texts):
            btn = QPushButton(text, objectName="sidebarButton")
            btn.clicked.connect(self.buttons_actions[i])
            layout.addWidget(btn)

        layout.addStretch()
        return sidebar

    # -------------------------------------------------------------------------
    # (1) ADD A CONCERT PAGE
    # -------------------------------------------------------------------------
    def createAddConcertPage(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Add a Concert (Event)")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # Concert Name
        layout.addWidget(QLabel("Concert Name:"))
        self.concert_name_input = QLineEdit()
        layout.addWidget(self.concert_name_input)

        # Venue
        layout.addWidget(QLabel("Venue:"))
        self.venue_input = QLineEdit()
        layout.addWidget(self.venue_input)

        # Date
        layout.addWidget(QLabel("Date (YYYY-MM-DD HH:MM):"))
        self.date_input = QLineEdit()
        layout.addWidget(self.date_input)

        # Organizer address
        layout.addWidget(QLabel("Organizer Wallet Address:"))
        self.organizer_input = QLineEdit()
        layout.addWidget(self.organizer_input)

        # Max tickets per user
        layout.addWidget(QLabel("Max Tickets per User:"))
        self.max_tickets_input = QSpinBox()
        self.max_tickets_input.setValue(5)
        layout.addWidget(self.max_tickets_input)

        # Refundable until
        layout.addWidget(QLabel("Refundable Until (YYYY-MM-DD HH:MM):"))
        self.refundable_until_input = QLineEdit()
        layout.addWidget(self.refundable_until_input)

        # # of Tickets (Regular)
        layout.addWidget(QLabel("Number of Tickets (Regular):"))
        self.tix_count_input = QSpinBox()
        self.tix_count_input.setValue(100)
        layout.addWidget(self.tix_count_input)

        # Ticket Price (Regular)
        layout.addWidget(QLabel("Ticket Price (Regular):"))
        self.tix_price_input = QDoubleSpinBox()
        self.tix_price_input.setDecimals(2)
        self.tix_price_input.setValue(50.0)
        layout.addWidget(self.tix_price_input)

        # "Add Concert" button
        add_btn = QPushButton("Add Concert")
        add_btn.clicked.connect(self.addConcert)
        layout.addWidget(add_btn)

        layout.addStretch()
        return page

    def addConcert(self):
        """Create an event on the blockchain using the input fields."""
        name = self.concert_name_input.text().strip()
        venue = self.venue_input.text().strip()
        date_str = self.date_input.text().strip()
        organizer = self.organizer_input.text().strip()
        max_tix_per_user = self.max_tickets_input.value()
        refundable_str = self.refundable_until_input.text().strip()

        if not name or not venue or not date_str or not organizer:
            QMessageBox.warning(self, "Error", "Please fill all required fields.")
            return

        # Parse date
        try:
            event_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid event date format.")
            return

        # Parse refundable until
        try:
            refundable_until = datetime.strptime(refundable_str, "%Y-%m-%d %H:%M")
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid refundable-until format.")
            return

        # Collect ticket info
        count_regular = self.tix_count_input.value()
        price_regular = self.tix_price_input.value()

        ticket_types = {TicketType.REGULAR: count_regular}
        prices = {TicketType.REGULAR: price_regular}

        # Create the event (category can be "Concert"; description optional)
        try:
            event_obj = self.blockchain.create_event(
                name=name,
                venue=venue,
                date=event_date,
                ticket_types=ticket_types,
                prices=prices,
                organizer_address=organizer,
                description="Concert event",
                category="Concert",
                max_tickets_per_user=max_tix_per_user,
                refundable_until=refundable_until
            )
            QMessageBox.information(self, "Success", f"Concert '{event_obj.name}' created!")
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

        # Update combos after adding
        self.updateEventCombos()

    # -------------------------------------------------------------------------
    # (2) MINT TICKETS PAGE
    # -------------------------------------------------------------------------
    def createMintPage(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Mint Tickets")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # Choose event
        layout.addWidget(QLabel("Select Event:"))
        self.mint_event_combo = QComboBox()
        layout.addWidget(self.mint_event_combo)

        # Ticket Type
        layout.addWidget(QLabel("Ticket Type: (Regular, VIP, Early_bird, etc.)"))
        self.ticket_type_combo = QComboBox()
        for ttype in TicketType:
            self.ticket_type_combo.addItem(ttype.value.capitalize(), ttype)
        layout.addWidget(self.ticket_type_combo)

        # Wallet address
        layout.addWidget(QLabel("Wallet Address (Buyer):"))
        self.mint_wallet_input = QLineEdit()
        layout.addWidget(self.mint_wallet_input)

        # Mint button
        mint_btn = QPushButton("Mint Ticket")
        mint_btn.clicked.connect(self.mintTicket)
        layout.addWidget(mint_btn)

        layout.addStretch()
        return page

    def mintTicket(self):
        """Call blockchain.mint_ticket to create a new ticket."""
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

    # -------------------------------------------------------------------------
    # (3) TRANSFER TICKETS PAGE
    # -------------------------------------------------------------------------
    def createTransferPage(self):
        page = QWidget()
        layout = QVBoxLayout(page)

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
        return page

    def transferTicket(self):
        """Use blockchain.transfer_ticket with user-provided data."""
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

    # -------------------------------------------------------------------------
    # (4) DISPLAY EVENT TICKETS PAGE
    # -------------------------------------------------------------------------
    def createDisplayTicketsPage(self):
        """Page to display all tickets for a selected event."""
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Display Event Tickets")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Select Event:"))
        self.display_event_combo = QComboBox()
        layout.addWidget(self.display_event_combo)

        show_btn = QPushButton("Show Tickets")
        show_btn.clicked.connect(self.showEventTickets)
        layout.addWidget(show_btn)

        # Scrollable text area for ticket listings
        self.tickets_display_area = QTextEdit()
        self.tickets_display_area.setReadOnly(True)
        layout.addWidget(self.tickets_display_area)

        layout.addStretch()
        return page

    def showEventTickets(self):
        """Query blockchain for tickets of the selected event, then display."""
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

    # -------------------------------------------------------------------------
    # (5) REQUEST REFUND PAGE
    # -------------------------------------------------------------------------
    def createRefundPage(self):
        """Page to request a refund for a ticket."""
        page = QWidget()
        layout = QVBoxLayout(page)

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
        return page

    def requestRefund(self):
        """Call blockchain.request_refund with user-provided data."""
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

    # -------------------------------------------------------------------------
    # (6) DISPLAY EVENT STATISTICS PAGE
    # -------------------------------------------------------------------------
    def createStatsPage(self):
        """Page to display event statistics."""
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Display Event Statistics")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Select Event:"))
        self.stats_event_combo = QComboBox()
        layout.addWidget(self.stats_event_combo)

        stats_btn = QPushButton("Show Statistics")
        stats_btn.clicked.connect(self.showEventStats)
        layout.addWidget(stats_btn)

        self.stats_display_area = QTextEdit()
        self.stats_display_area.setReadOnly(True)
        layout.addWidget(self.stats_display_area)

        layout.addStretch()
        return page

    def showEventStats(self):
        """Retrieve statistics for the selected event from the blockchain."""
        self.stats_display_area.clear()
        event_id = self.stats_event_combo.currentData()
        if not event_id:
            self.stats_display_area.setText("No event selected.")
            return

        try:
            stats = self.blockchain.get_event_stats(event_id)
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        lines = []
        for key, value in stats.items():
            if isinstance(value, dict):
                # For nested stats like tickets_by_type
                sub_lines = [f"   {t_type.value.capitalize()}: {cnt}"
                             for t_type, cnt in value.items()]
                sub_str = "\n".join(sub_lines)
                lines.append(f"{key}:\n{sub_str}")
            else:
                lines.append(f"{key}: {value}")

        self.stats_display_area.setText("\n".join(lines))

    # -------------------------------------------------------------------------
    # HELPER: UPDATE EVENT COMBOS
    # -------------------------------------------------------------------------
    def updateEventCombos(self):
        """Populate all event-related combo boxes with the current blockchain events."""
        combos = []
        # Only add combos if they've been created:
        if hasattr(self, "mint_event_combo"):
            combos.append(self.mint_event_combo)
        if hasattr(self, "display_event_combo"):
            combos.append(self.display_event_combo)
        if hasattr(self, "stats_event_combo"):
            combos.append(self.stats_event_combo)

        for combo in combos:
            combo.clear()
            for event_id, event_obj in self.blockchain.events.items():
                combo.addItem(event_obj.name, event_id)


def main():
    app = QApplication(sys.argv)
    window = ConcertTicketingApp()
    window.show()
    # Populate combos on startup, in case there are existing events
    window.updateEventCombos()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
