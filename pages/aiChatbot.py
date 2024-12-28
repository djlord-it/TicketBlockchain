import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QLineEdit, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from datetime import datetime
import qrcode
from PIL import Image
from PIL.ImageQt import ImageQt

from blockchain_ticketing import TicketingBlockchain, TicketType
from fraud_detection import FraudDetector

class ChatBubble(QWidget):
    def __init__(self, text, isUser=False, parent=None, has_qr=False, ticket_data=None):
        super().__init__(parent)
        self.isUser = isUser
        self.text = text
        self.has_qr = has_qr
        self.ticket_data = ticket_data
        self.setupUI()

    def setupUI(self):
        layout = QHBoxLayout(self)
        container = QWidget()
        container_layout = QVBoxLayout(container)

        label = QLabel(self.text)
        label.setWordWrap(True)
        label.setStyleSheet(self.bubbleStyle())
        container_layout.addWidget(label)

        if self.has_qr and self.ticket_data:
            qr = qrcode.QRCode(version=1, box_size=8, border=3)
            qr.add_data(str(self.ticket_data))
            qr.make(fit=True)
            qr_image = qr.make_image(fill_color="black", back_color="white")
            if not isinstance(qr_image, Image.Image):
                qr_image = qr_image.convert("RGB")
            pixmap = QPixmap.fromImage(ImageQt(qr_image))
            qr_label = QLabel()
            qr_label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
            container_layout.addWidget(qr_label)

        if self.isUser:
            layout.addStretch()
            layout.addWidget(container)
        else:
            layout.addWidget(container)
            layout.addStretch()

        self.setLayout(layout)

    def bubbleStyle(self):
        if self.isUser:
            return """
                QLabel {
                    background-color: #ffffff;
                    color: #333333;
                    border-radius: 10px;
                    padding: 8px;
                    margin: 5px;
                    font-size: 14px;
                }
            """
        else:
            return """
                QLabel {
                    background-color: #0071e3;
                    color: #ffffff;
                    border-radius: 10px;
                    padding: 8px;
                    margin: 5px;
                    font-size: 14px;
                }
            """

class ChatWindow(QMainWindow):
    """
    Chatbot that:
    - Lists events from shared blockchain
    - Asks user for wallet address before confirm
    - Uses FraudDetector
    - Mints tickets on confirm
    """

    def __init__(self, blockchain):
        super().__init__()
        self.blockchain = blockchain
        self.fraud_detector = FraudDetector()

        self.selected_event = None
        self.selected_ticket_type = None
        self.ticket_quantity = None
        self.buyer_wallet = None

        # possible states:
        # 'greeting', 'select_event', 'select_type', 'select_quantity',
        # 'ask_wallet', 'confirm'
        self.current_state = 'greeting'

        self.setupUI()
        self.initializeConversation()

    def setupUI(self):
        self.setWindowTitle("AI Ticket Chatbot")
        self.resize(400, 600)
        self.setStyleSheet("background-color: #F0F2F5;")

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        headerFrame = QFrame()
        headerFrame.setStyleSheet("""
            QFrame {
                background-color: #075E54;
                color: white;
                padding: 10px;
            }
        """)
        headerLayout = QHBoxLayout(headerFrame)
        titleLabel = QLabel("AI Ticket Chatbot")
        titleLabel.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        headerLayout.addWidget(titleLabel)
        main_layout.addWidget(headerFrame)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("QScrollArea { border: none; background-color: #F0F2F5; }")
        self.chatContainer = QWidget()
        self.chatLayout = QVBoxLayout(self.chatContainer)
        self.chatLayout.addStretch()
        self.chatContainer.setLayout(self.chatLayout)
        self.scrollArea.setWidget(self.chatContainer)
        main_layout.addWidget(self.scrollArea)

        inputFrame = QFrame()
        inputFrame.setStyleSheet("QFrame { background-color: white; border-top: 1px solid #E0E0E0; }")
        inputLayout = QHBoxLayout(inputFrame)

        self.inputField = QLineEdit()
        self.inputField.setPlaceholderText("Type a message...")
        self.inputField.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E0E0E0;
                border-radius: 20px;
                padding: 8px 15px;
                font-size: 14px;
            }
        """)
        self.inputField.returnPressed.connect(self.onSendClicked)

        self.sendBtn = QPushButton("Send")
        self.sendBtn.setStyleSheet("""
            QPushButton {
                background-color: #075E54;
                color: white;
                border-radius: 15px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
        """)
        self.sendBtn.clicked.connect(self.onSendClicked)

        inputLayout.addWidget(self.inputField)
        inputLayout.addWidget(self.sendBtn)
        main_layout.addWidget(inputFrame)

    def initializeConversation(self):
        self.addChatBubble("Hello! Type 'buy' to purchase tickets or 'hi' to begin.", isUser=False)

    def addChatBubble(self, text, isUser=False, has_qr=False, ticket_data=None):
        bubble = ChatBubble(text, isUser=isUser, has_qr=has_qr, ticket_data=ticket_data)
        self.chatLayout.takeAt(self.chatLayout.count() - 1)
        self.chatLayout.addWidget(bubble)
        self.chatLayout.addStretch()
        QTimer.singleShot(100, self.scrollToBottom)

    def scrollToBottom(self):
        self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())

    def handleUserMessage(self, msg: str):
        self.addChatBubble(msg, isUser=True)

        # Basic fraud check on every message
        tx_data = {
            "wallet": "temporary",
            "timestamp": datetime.now().isoformat(),
            "message": msg,
            "fraud_prone": False
        }
        fd_result = self.fraud_detector.judge_transaction(tx_data)
        if fd_result == "fraud":
            self.addChatBubble("⚠️ Suspicious request. Please try again later.", isUser=False)
            return
        elif fd_result == "suspect":
            self.addChatBubble("This seems unusual; proceed with caution...", isUser=False)

        # State machine
        if self.current_state == 'greeting':
            if "buy" in msg.lower() or "hi" in msg.lower():
                self.showEventList()
            else:
                self.addChatBubble("You can type 'buy' to start buying tickets.", isUser=False)

        elif self.current_state == "select_event":
            try:
                choice = int(msg)
                if 1 <= choice <= len(self.events_list):
                    self.selected_event = self.events_list[choice - 1]
                    self.showTicketTypes()
                else:
                    self.addChatBubble("Please enter a valid event number.", isUser=False)
            except ValueError:
                self.addChatBubble("Please enter a valid event number.", isUser=False)

        elif self.current_state == "select_type":
            try:
                choice = int(msg)
                if choice in self.ticket_type_map:
                    self.selected_ticket_type = self.ticket_type_map[choice]
                    self.current_state = "select_quantity"
                    max_tix = self.selected_event.max_tickets_per_user
                    self.addChatBubble(f"How many {self.selected_ticket_type.value} tickets?\n"
                                       f"(Max {max_tix} per user)", isUser=False)
                else:
                    self.addChatBubble("Invalid type choice. Try again.", isUser=False)
            except ValueError:
                self.addChatBubble("Enter a valid number for ticket type.", isUser=False)

        elif self.current_state == "select_quantity":
            try:
                qty = int(msg)
                if qty < 1 or qty > self.selected_event.max_tickets_per_user:
                    self.addChatBubble(f"Pick 1 - {self.selected_event.max_tickets_per_user}.", isUser=False)
                    return
                available = self.selected_event.available_tickets[self.selected_ticket_type]
                if qty > available:
                    self.addChatBubble(f"Only {available} left for {self.selected_ticket_type.value}.", isUser=False)
                    return
                self.ticket_quantity = qty
                # Now we ask for the buyer wallet
                self.current_state = "ask_wallet"
                self.addChatBubble("Please enter your buyer wallet address:", isUser=False)
            except ValueError:
                self.addChatBubble("Please enter a valid integer for quantity.", isUser=False)

        elif self.current_state == "ask_wallet":
            # The user is typing the wallet address
            self.buyer_wallet = msg.strip()
            if not self.buyer_wallet:
                self.addChatBubble("No wallet address detected. Try again or type 'default' to use a placeholder address.", isUser=False)
                return
            if self.buyer_wallet.lower() == "default":
                self.buyer_wallet = "userXYZ"
                self.addChatBubble("Using default wallet address: userXYZ", isUser=False)
            self.current_state = "confirm"
            price_each = self.selected_event.prices[self.selected_ticket_type]
            total = self.ticket_quantity * price_each
            event_name = self.selected_event.name
            self.addChatBubble(
                f"Event: {event_name}\n"
                f"Type: {self.selected_ticket_type.value}\n"
                f"Quantity: {self.ticket_quantity}\n"
                f"Wallet: {self.buyer_wallet}\n"
                f"Total: ${total:.2f}\n"
                "Type 'confirm' to finalize or 'cancel' to abort.",
                isUser=False
            )

        elif self.current_state == "confirm":
            if msg.lower() == "confirm":
                self.doPurchase()
            elif msg.lower() == "cancel":
                self.addChatBubble("Purchase canceled. Type 'buy' to start again.", isUser=False)
                self.current_state = "greeting"
            else:
                self.addChatBubble("Type 'confirm' or 'cancel'.", isUser=False)

        else:
            self.addChatBubble("Not sure what you mean. Type 'buy' to begin.", isUser=False)

    def showEventList(self):
        self.events_list = list(self.blockchain.events.values())
        if not self.events_list:
            self.addChatBubble("No events available. Please add a concert first.", isUser=False)
            self.current_state = 'greeting'
            return

        self.current_state = "select_event"
        msg = "Select an event by number:\n"
        for i, ev in enumerate(self.events_list, start=1):
            msg += f"{i}. {ev.name} - {ev.date.strftime('%Y-%m-%d %H:%M')}\n"
        self.addChatBubble(msg, isUser=False)

    def showTicketTypes(self):
        self.current_state = "select_type"
        e = self.selected_event
        self.ticket_type_map = {}
        msg = f"Event: {e.name}\nTicket Types:\n"
        idx = 1
        for ttype, price in e.prices.items():
            available = e.available_tickets[ttype]
            msg += f"{idx}. {ttype.value.capitalize()} - ${price} (Remaining: {available})\n"
            self.ticket_type_map[idx] = ttype
            idx += 1

        msg += "\nPick the type number you want."
        self.addChatBubble(msg, isUser=False)

    def doPurchase(self):
        e = self.selected_event
        ttype = self.selected_ticket_type
        qty = self.ticket_quantity
        wallet = self.buyer_wallet if self.buyer_wallet else "userXYZ"

        for i in range(qty):
            try:
                new_ticket = self.blockchain.mint_ticket(e.event_id, wallet, ttype)
                ticket_data = {
                    "event": e.name,
                    "ticket_id": new_ticket.ticket_id,
                    "type": ttype.value,
                    "price": new_ticket.price,
                    "wallet": wallet,
                    "minted_at": datetime.now().isoformat()
                }
                msg = (f"Ticket minted: {new_ticket.ticket_id}\n"
                       f"Type: {ttype.value}\n"
                       f"Price: ${new_ticket.price:.2f}\n"
                       f"Wallet: {wallet}")
                self.addChatBubble(msg, isUser=False, has_qr=True, ticket_data=ticket_data)

            except ValueError as ve:
                self.addChatBubble(f"Purchase failed: {str(ve)}", isUser=False)
                break

        self.current_state = "greeting"
        QTimer.singleShot(1000, lambda: self.addChatBubble("Type 'buy' to purchase more tickets.", isUser=False))

    def onSendClicked(self):
        text = self.inputField.text().strip()
        if text:
            self.inputField.clear()
            self.handleUserMessage(text)

def main():
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    bc = TicketingBlockchain()
    window = ChatWindow(bc)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
