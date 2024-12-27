import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget, QLineEdit, QComboBox,
                             QScrollArea, QGridLayout, QSpinBox, QDoubleSpinBox, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime
from blockchain_ticketing import TicketingBlockchain, TicketType, Event, Ticket


class TicketingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.blockchain = TicketingBlockchain(difficulty=2)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Blockchain Ticketing System')
        # You can adjust this size or use showMaximized() for full screen
        self.resize(1280, 800)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Sidebar
        sidebar = self.createSidebar()
        main_layout.addWidget(sidebar)

        # Main content area
        self.stack = QStackedWidget()
        self.stack.addWidget(self.createEventsPage())
        self.stack.addWidget(self.createTicketsPage())
        self.stack.addWidget(self.createTransferPage())
        self.stack.addWidget(self.createStatsPage())
        main_layout.addWidget(self.stack)

        # Stretch factors: left column (sidebar) is narrower, right column is wider
        main_layout.setStretch(0, 1)  # Sidebar
        main_layout.setStretch(1, 4)  # Main content

        # A modern, minimalistic Apple-inspired style sheet
        self.setStyleSheet('''
            QMainWindow {
                background-color: #f5f5f7;
            }

            /* Sidebar styles */
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
                margin: 5px 0;
                font-size: 15px;
                text-align: center;
            }
            QPushButton#sidebarButton:hover {
                background-color: #005bb5;
            }

            /* Shared button style */
            QPushButton {
                background-color: #0071e3;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 8px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }

            QLabel {
                font-size: 16px;
                color: #333333;
            }

            /* Inputs */
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 8px;
                border: 1px solid #d1d1d6;
                border-radius: 6px;
                background: white;
                font-size: 15px;
            }

            /* Event cards */
            QWidget#eventCard {
                background-color: #ffffff;
                border: 1px solid #d1d1d6;
                border-radius: 10px;
                padding: 15px;
            }

            QScrollArea {
                border: none;
            }
        ''')

    def createSidebar(self):
        sidebar = QWidget(objectName='sidebar')
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel("Ticketing System", objectName="sidebarTitle")
        layout.addWidget(title)

        buttons = [
            ("Events", lambda: self.stack.setCurrentIndex(0)),
            ("My Tickets", lambda: self.stack.setCurrentIndex(1)),
            ("Transfer", lambda: self.stack.setCurrentIndex(2)),
            ("Statistics", lambda: self.stack.setCurrentIndex(3))
        ]

        for text, callback in buttons:
            btn = QPushButton(text, objectName="sidebarButton")
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        layout.addStretch()
        return sidebar

    def createEventsPage(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QHBoxLayout()
        header.setSpacing(10)
        title = QLabel("Events")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        header.addWidget(title)

        add_event_btn = QPushButton("Add Event")
        add_event_btn.clicked.connect(self.showAddEventDialog)
        header.addStretch()
        header.addWidget(add_event_btn)
        layout.addLayout(header)

        # Events grid inside a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        events_widget = QWidget()
        self.events_grid = QGridLayout(events_widget)
        self.events_grid.setSpacing(20)
        self.events_grid.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(events_widget)
        layout.addWidget(scroll)

        self.updateEventsGrid()
        return page

    def createEventCard(self, event: Event):
        card = QWidget(objectName="eventCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)
        card_layout.setContentsMargins(10, 10, 10, 10)

        # Event details
        title = QLabel(event.name)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        card_layout.addWidget(title)

        card_layout.addWidget(QLabel(f"Venue: {event.venue}"))
        card_layout.addWidget(QLabel(f"Date: {event.date.strftime('%Y-%m-%d %H:%M')}"))
        card_layout.addWidget(QLabel(f"Category: {event.category}"))

        # Tickets section
        tickets_label = QLabel("Available Tickets:")
        tickets_label.setStyleSheet("font-weight: 500; margin-top: 10px;")
        card_layout.addWidget(tickets_label)

        for ticket_type, count in event.available_tickets.items():
            price = event.prices[ticket_type]
            card_layout.addWidget(QLabel(f"{ticket_type.value}: {count} (${price:.2f})"))

        # Buy button
        buy_btn = QPushButton("Purchase Tickets")
        buy_btn.clicked.connect(lambda: self.showPurchaseDialog(event))
        card_layout.addWidget(buy_btn)

        return card

    def showAddEventDialog(self):
        dialog = QWidget(self)
        dialog.setWindowTitle("Add New Event")
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Event details inputs
        layout.addWidget(QLabel("Event Name:"))
        name_input = QLineEdit()
        layout.addWidget(name_input)

        layout.addWidget(QLabel("Venue:"))
        venue_input = QLineEdit()
        layout.addWidget(venue_input)

        layout.addWidget(QLabel("Date: (YYYY-MM-DD HH:MM)"))
        date_input = QLineEdit()
        date_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        layout.addWidget(date_input)

        # Ticket types
        self.ticket_type_inputs = []
        for t_type in TicketType:
            layout.addWidget(QLabel(f"{t_type.value} Tickets:"))
            count_input = QSpinBox()
            count_input.setMaximum(10000)
            layout.addWidget(count_input)

            layout.addWidget(QLabel(f"{t_type.value} Price:"))
            price_input = QDoubleSpinBox()
            price_input.setMaximum(10000)
            price_input.setDecimals(2)
            price_input.setValue(0.00)
            layout.addWidget(price_input)

            self.ticket_type_inputs.append((t_type, count_input, price_input))

        save_btn = QPushButton("Create Event")
        save_btn.clicked.connect(lambda: self.saveEvent(
            dialog,
            name_input.text(),
            venue_input.text(),
            date_input.text()
        ))
        layout.addWidget(save_btn)

        dialog.show()

    def saveEvent(self, dialog, name):
        # Example logic to save the event
        # Retrieve inputs from self.ticket_type_inputs
        # For your use-case, parse date, etc.
        # This function would call self.blockchain.create_event(...)
        # Make sure to validate inputs and show messages if needed

        # Basic example of usage:
        # name_input, venue_input, date_input are from your widgets
        # self.ticket_type_inputs is a list of tuples: (TicketType, QSpinBox, QDoubleSpinBox)
        # Then you can do something like:
        #   for (t_type, count_input, price_input) in self.ticket_type_inputs:
        #       count = count_input.value()
        #       price = price_input.value()
        #       # Use count and price as needed
        #
        # Implementation is up to your existing code logic

        dialog.close()
        self.updateEventsGrid()

    def showPurchaseDialog(self, event: Event):
        dialog = QWidget(self)
        dialog.setWindowTitle("Purchase Tickets")
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel(f"Event: {event.name}"))

        layout.addWidget(QLabel("Ticket Type:"))
        type_combo = QComboBox()
        for t_type in TicketType:
            if event.available_tickets[t_type] > 0:
                type_combo.addItem(t_type.value)
        layout.addWidget(type_combo)

        layout.addWidget(QLabel("Wallet Address:"))
        wallet_input = QLineEdit()
        layout.addWidget(wallet_input)

        buy_btn = QPushButton("Confirm Purchase")
        buy_btn.clicked.connect(lambda: self.purchaseTicket(
            event,
            TicketType[type_combo.currentText().upper()],
            wallet_input.text(),
            dialog
        ))
        layout.addWidget(buy_btn)

        dialog.show()

    def purchaseTicket(self, event: Event, ticket_type: TicketType, wallet: str, dialog):
        try:
            ticket = self.blockchain.mint_ticket(event.event_id, wallet, ticket_type)
            QMessageBox.information(self, "Success",
                                    f"Ticket purchased successfully!\nTicket ID: {ticket.ticket_id}")
            dialog.close()
            self.updateEventsGrid()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def createTicketsPage(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("My Tickets")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Add wallet search
        wallet_layout = QHBoxLayout()
        wallet_layout.setSpacing(10)
        wallet_layout.addWidget(QLabel("Wallet Address:"))
        wallet_input = QLineEdit()
        wallet_layout.addWidget(wallet_input)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(lambda: self.searchTickets(wallet_input.text()))
        wallet_layout.addWidget(search_btn)

        layout.addLayout(wallet_layout)

        # Tickets list will be added here
        self.tickets_layout = QVBoxLayout()
        layout.addLayout(self.tickets_layout)

        layout.addStretch()
        return page

    def searchTickets(self, wallet: str):
        # Example logic to search for tickets in the blockchain
        # Clear layout first
        for i in reversed(range(self.tickets_layout.count())):
            widget = self.tickets_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Suppose you query self.blockchain for tickets belonging to wallet
        # and then display them
        # Example:
        # tickets = self.blockchain.get_tickets_by_owner(wallet)
        # for ticket in tickets:
        #     label = QLabel(f"Ticket ID: {ticket.ticket_id} - Event: {ticket.event_id}")
        #     self.tickets_layout.addWidget(label)
        pass

    def createTransferPage(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Transfer Ticket")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        form = QVBoxLayout()
        form.setSpacing(10)

        form.addWidget(QLabel("Ticket ID:"))
        ticket_input = QLineEdit()
        form.addWidget(ticket_input)

        form.addWidget(QLabel("From Address:"))
        from_input = QLineEdit()
        form.addWidget(from_input)

        form.addWidget(QLabel("To Address:"))
        to_input = QLineEdit()
        form.addWidget(to_input)

        form.addWidget(QLabel("Price:"))
        price_input = QDoubleSpinBox()
        price_input.setMaximum(10000)
        form.addWidget(price_input)

        transfer_btn = QPushButton("Transfer")
        transfer_btn.clicked.connect(lambda: self.transferTicket(
            ticket_input.text(),
            from_input.text(),
            to_input.text(),
            price_input.value()
        ))
        form.addWidget(transfer_btn)

        layout.addLayout(form)
        layout.addStretch()
        return page

    def transferTicket(self, ticket_id, from_addr, to_addr, price):
        # Example logic for transferring a ticket
        try:
            self.blockchain.transfer_ticket(ticket_id, from_addr, to_addr, price)
            QMessageBox.information(self, "Success", "Ticket transferred successfully!")
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def createStatsPage(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Statistics")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Event selection
        event_layout = QHBoxLayout()
        event_layout.setSpacing(10)
        event_layout.addWidget(QLabel("Select Event:"))
        self.event_combo = QComboBox()
        event_layout.addWidget(self.event_combo)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.updateStats)
        event_layout.addWidget(refresh_btn)

        layout.addLayout(event_layout)

        # Stats will be displayed here
        self.stats_layout = QVBoxLayout()
        layout.addLayout(self.stats_layout)

        layout.addStretch()
        return page

    def updateEventsGrid(self):
        # Clear existing events
        for i in reversed(range(self.events_grid.count())):
            widget = self.events_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Add events to grid
        row, col = 0, 0
        for event in self.blockchain.events.values():
            card = self.createEventCard(event)
            self.events_grid.addWidget(card, row, col)
            col += 1
            if col > 1:  # 2 columns of event cards
                col = 0
                row += 1

    def updateStats(self):
        event_id = self.event_combo.currentData()
        if not event_id:
            return

        try:
            stats = self.blockchain.get_event_stats(event_id)

            # Clear existing stats
            for i in reversed(range(self.stats_layout.count())):
                widget = self.stats_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            # Display stats
            for key, value in stats.items():
                self.stats_layout.addWidget(QLabel(f"{key}: {value}"))

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))


def main():
    app = QApplication(sys.argv)
    window = TicketingApp()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
