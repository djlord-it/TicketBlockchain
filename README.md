# Blockchain Ticketing & AI Chatbot

## Overview
Step into the future of event ticketing with our Blockchain Ticketing System, integrated with a cutting-edge AI Chatbot. Imagine a world where buying tickets is effortless, fraud is a thing of the past, and every transaction is secured by the power of blockchain. This isn't just a system—it's a revolution in how we experience events.

Here's what makes it exceptional:

- **Seamless Event Creation**: Organizers can set up events with multiple ticket types, dynamic pricing, and capped capacities—all stored immutably on a blockchain.
- **Smart Ticket Management**: Buy, transfer, or refund tickets with a click, all while ensuring integrity through decentralized tracking.
- **Fraud Detection Redefined**: Transactions are analyzed in real-time to flag anomalies using both machine learning and rule-based systems.
- **Conversational AI Assistance**: A friendly chatbot guides users through ticket purchases, verifies transactions, and even generates QR codes instantly.

---

## Key Components

### Core Features
- **Blockchain-Powered Ticketing**: Every ticket transaction is recorded as a block, ensuring transparency and security.
- **AI Chatbot**: Your personal event concierge, assisting with ticket purchases and providing fraud alerts.
- **Fraud Detection**: ML-based and rule-driven mechanisms to ensure fair play in the ticketing ecosystem.
- **Wallet Management**: Securely create and handle cryptographic wallets for all ticket transactions.

### Highlights
- **`blockchain_ticketing.py`**: The beating heart of the system, managing events, tickets, and transactions on a blockchain.
- **`fraud_detection.py`**: Your watchdog against suspicious activities, leveraging intelligent detection algorithms.
- **`aiChatbot.py`**: The chatbot that makes ticketing a breeze, integrating fraud detection and QR code generation.
- **`main.py`**: The centralized app where all the magic comes together.
- **Pages**:
  - `add_concert.py`: Create vibrant events effortlessly.
  - `mint.py`: Mint and distribute tickets.
  - `transfer.py`: Seamlessly transfer tickets to new owners.
  - `request_refund.py`: Simplify refund requests for eligible tickets.
  - `stats.py`: Visualize event statistics at a glance.
  - `display_tickets.py`: Showcase all tickets for an event.

---

## Installation

Getting started is as easy as 1-2-3:

1. Clone the repository and set up your environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install the dependencies:
   ```bash
   pip install PyQt6 qrcode pillow scikit-learn joblib
   ```
3. Launch the application:
   ```bash
   python main.py
   ```

(Optional) Train your fraud detection model for even smarter analysis:
```bash
python fraud_detect_model_trainer.py
```

---

## Why It Matters

Imagine a system that combines the transparency of blockchain, the intelligence of AI, and the simplicity of a chatbot interface. That's what we've built. This platform:

- **Empowers Event Organizers**: Create events and manage tickets effortlessly.
- **Protects Ticket Buyers**: Ensures fair transactions and safeguards against fraud.
- **Streamlines Experiences**: With AI-driven interactions, buying a ticket feels like chatting with a friend.

---

## The Vision

We see a world where event ticketing is not just a transaction but an experience—secure, simple, and spectacular. With this system, we're not just solving today's problems; we're shaping tomorrow's possibilities.

Join us in redefining how the world connects and celebrates events.
