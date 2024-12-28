import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget
)

from blockchain_ticketing import TicketingBlockchain
from pages.add_concert import AddConcertPage
from pages.mint import MintPage
from pages.transfer import TransferPage
from pages.display_tickets import DisplayTicketsPage
from pages.request_refund import RequestRefundPage
from pages.stats import StatsPage
from pages.aiChatbot import ChatWindow


class ConcertTicketingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Concert Ticketing System")
        self.resize(1200, 800)

        # Load the TicketingBlockchain instance
        self.blockchain = TicketingBlockchain(difficulty=2)

        # Define the sidebar button actions; 7 pages
        self.buttons_actions = [
            lambda: self.stack.setCurrentIndex(0),  # Add a Concert
            lambda: self.stack.setCurrentIndex(1),  # Mint Tickets
            lambda: self.stack.setCurrentIndex(2),  # Transfer Tickets
            lambda: self.stack.setCurrentIndex(3),  # Display Event Tickets
            lambda: self.stack.setCurrentIndex(4),  # Request Refund
            lambda: self.stack.setCurrentIndex(5),  # Display Event Statistics
            lambda: self.stack.setCurrentIndex(6),  # AI Chatbot
        ]

        # 3) Main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 4) Sidebar
        self.sidebar = self.createSidebar()
        main_layout.addWidget(self.sidebar)

        # 5) QStackedWidget
        self.stack = QStackedWidget()

        # 6) Create the pages
        self.add_concert_page = AddConcertPage(
            self.blockchain,
            update_event_combos_callback=self.updateAllPages
        )
        self.mint_page = MintPage(self.blockchain)
        self.transfer_page = TransferPage(self.blockchain)
        self.display_tix_page = DisplayTicketsPage(self.blockchain)
        self.refund_page = RequestRefundPage(self.blockchain)
        self.stats_page = StatsPage(self.blockchain)

        # Create an instance of the AI Chatbot page
        self.ai_chatbot_page = ChatWindow(self.blockchain)

        # 7) Add all pages to the stack
        self.stack.addWidget(self.add_concert_page)  # index 0
        self.stack.addWidget(self.mint_page)  # index 1
        self.stack.addWidget(self.transfer_page)  # index 2
        self.stack.addWidget(self.display_tix_page)  # index 3
        self.stack.addWidget(self.refund_page)  # index 4
        self.stack.addWidget(self.stats_page)  # index 5
        self.stack.addWidget(self.ai_chatbot_page)  # index 6

        main_layout.addWidget(self.stack)

        # 8) Apply style
        self.setStyleSheet('''
            QMainWindow {
                background-color: #f5f5f7;
            }
            QMessageBox {
                background-color: #ffffff;
            }
            QMessageBox QLabel {
                color: #000000;
                font-size: 15px;
            }
            QMessageBox QPushButton {
                background-color: #0071e3;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px 15px;
                margin: 5px;
                font-size: 14px;
            }
            QMessageBox QPushButton:hover {
                background-color: #005bb5;
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
                color: #333333;
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

        # 9) Update combos if needed
        self.updateAllPages()

    def createSidebar(self):
        sidebar = QWidget(objectName="sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Concert Ticketing", objectName="sidebarTitle")
        layout.addWidget(title)

        # 7 button labels
        button_texts = [
            "1. Add a Concert",
            "2. Mint Tickets",
            "3. Transfer Tickets",
            "4. Display Event Tickets",
            "5. Request Refund",
            "6. Display Event Statistics",
            "7. AI Chatbot"
        ]

        for i, text in enumerate(button_texts):
            btn = QPushButton(text, objectName="sidebarButton")
            btn.clicked.connect(self.buttons_actions[i])
            layout.addWidget(btn)

        layout.addStretch()
        return sidebar

    def updateAllPages(self):
        self.mint_page.updateEventList()
        self.display_tix_page.updateEventList()
        self.stats_page.updateEventList()


def main():
    app = QApplication(sys.argv)
    window = ConcertTicketingApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
