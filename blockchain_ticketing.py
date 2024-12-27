# blockchain_ticketing.py
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
import uuid
from typing import Dict, List, Optional, Set
from enum import Enum
import time


class TicketStatus(Enum):
    VALID = "valid"
    USED = "used"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TicketType(Enum):
    REGULAR = "regular"
    VIP = "vip"
    EARLY_BIRD = "early_bird"


@dataclass
class Event:
    event_id: str
    name: str
    venue: str
    date: datetime
    total_tickets: Dict[TicketType, int]  # Tickets per type
    prices: Dict[TicketType, float]  # Prices per type
    organizer_address: str
    description: str
    category: str
    max_tickets_per_user: int
    refundable_until: datetime
    available_tickets: Dict[TicketType, int] = field(init=False)
    is_cancelled: bool = False
    waitlist: Set[str] = field(default_factory=set)

    def __post_init__(self):
        self.available_tickets = self.total_tickets.copy()


@dataclass
class Ticket:
    ticket_id: str
    event_id: str
    ticket_type: TicketType
    price: float
    owner_address: str
    metadata: Dict
    transfer_history: List[Dict] = field(default_factory=list)
    status: TicketStatus = TicketStatus.VALID
    qr_code: str = field(init=False)
    purchased_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.qr_code = self._generate_qr_code()

    def _generate_qr_code(self) -> str:
        # Generate a unique QR code based on ticket details
        data = f"{self.ticket_id}:{self.event_id}:{self.owner_address}:{int(time.time())}"
        return hashlib.sha256(data.encode()).hexdigest()


class SmartContract:
    def __init__(self):
        self.refund_policy: Dict[str, float] = {
            "7_days": 1.0,  # 100% refund if more than 7 days before event
            "3_days": 0.75,  # 75% refund if 3-7 days before event
            "1_day": 0.5  # 50% refund if 1-3 days before event
        }
        self.max_markup_percentage: float = 0.5  # 50% maximum markup for resale

    def calculate_refund_amount(self, ticket: Ticket, event: Event) -> Optional[float]:
        if not event.refundable_until or datetime.now() > event.refundable_until:
            return None

        days_until_event = (event.date - datetime.now()).days

        if days_until_event >= 7:
            return ticket.price * self.refund_policy["7_days"]
        elif days_until_event >= 3:
            return ticket.price * self.refund_policy["3_days"]
        elif days_until_event >= 1:
            return ticket.price * self.refund_policy["1_day"]
        return None


class TicketingBlockchain:
    def __init__(self, difficulty: int = 2):
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict] = []
        self.difficulty = difficulty
        self.events: Dict[str, Event] = {}
        self.tickets: Dict[str, Ticket] = {}
        self.smart_contract = SmartContract()
        self.user_tickets: Dict[str, Set[str]] = {}  # address -> ticket_ids

        # Create genesis block
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(datetime.now(), [], "0")
        self.chain.append(genesis_block)

    def create_event(self, name: str, venue: str, date: datetime,
                     ticket_types: Dict[TicketType, int],
                     prices: Dict[TicketType, float],
                     organizer_address: str, description: str,
                     category: str, max_tickets_per_user: int,
                     refundable_until: datetime) -> Event:
        """Create a new event with multiple ticket types."""
        event_id = str(uuid.uuid4())
        event = Event(
            event_id=event_id,
            name=name,
            venue=venue,
            date=date,
            total_tickets=ticket_types,
            prices=prices,
            organizer_address=organizer_address,
            description=description,
            category=category,
            max_tickets_per_user=max_tickets_per_user,
            refundable_until=refundable_until
        )
        self.events[event_id] = event

        self._add_transaction("create_event", event_id, {
            "name": name,
            "venue": venue,
            "date": date.isoformat(),
            "ticket_types": {t.value: count for t, count in ticket_types.items()},
            "prices": {t.value: price for t, price in prices.items()},
            "organizer_address": organizer_address,
            "description": description,
            "category": category
        })

        return event

    def join_waitlist(self, event_id: str, user_address: str) -> bool:
        """Add user to event waitlist."""
        if event_id not in self.events:
            raise ValueError("Event not found")

        event = self.events[event_id]
        event.waitlist.add(user_address)
        return True

    def mint_ticket(self, event_id: str, buyer_address: str,
                    ticket_type: TicketType) -> Optional[Ticket]:
        """Mint a new ticket for an event."""
        if event_id not in self.events:
            raise ValueError("Event not found")

        event = self.events[event_id]
        if event.is_cancelled:
            raise ValueError("Event is cancelled")

        if event.available_tickets[ticket_type] <= 0:
            raise ValueError("No tickets available for this type")

        # Check max tickets per user
        user_event_tickets = len([
            t for t in self.get_user_tickets(buyer_address)
            if t.event_id == event_id
        ])
        if user_event_tickets >= event.max_tickets_per_user:
            raise ValueError("Maximum tickets per user exceeded")

        ticket_id = str(uuid.uuid4())
        ticket = Ticket(
            ticket_id=ticket_id,
            event_id=event_id,
            ticket_type=ticket_type,
            price=event.prices[ticket_type],
            owner_address=buyer_address,
            metadata={
                "event_name": event.name,
                "venue": event.venue,
                "date": event.date.isoformat(),
                "ticket_type": ticket_type.value
            }
        )

        # Record initial transfer
        ticket.transfer_history.append({
            "timestamp": datetime.now().isoformat(),
            "from": "mint",
            "to": buyer_address,
            "price": event.prices[ticket_type]
        })

        self.tickets[ticket_id] = ticket
        event.available_tickets[ticket_type] -= 1

        # Update user tickets mapping
        if buyer_address not in self.user_tickets:
            self.user_tickets[buyer_address] = set()
        self.user_tickets[buyer_address].add(ticket_id)

        self._add_transaction("mint_ticket", ticket_id, {
            "event_id": event_id,
            "buyer_address": buyer_address,
            "ticket_type": ticket_type.value,
            "price": event.prices[ticket_type]
        })

        return ticket

    def cancel_event(self, event_id: str, organizer_address: str) -> bool:
        """Cancel an event and process refunds."""
        if event_id not in self.events:
            raise ValueError("Event not found")

        event = self.events[event_id]
        if event.organizer_address != organizer_address:
            raise ValueError("Not event organizer")

        event.is_cancelled = True

        # Process refunds for all tickets
        for ticket in self.get_event_tickets(event_id):
            if ticket.status == TicketStatus.VALID:
                ticket.status = TicketStatus.CANCELLED
                # In a real implementation, process refund transaction here
                self._add_transaction("refund_ticket", ticket.ticket_id, {
                    "event_id": event_id,
                    "owner_address": ticket.owner_address,
                    "refund_amount": ticket.price
                })

        return True

    def request_refund(self, ticket_id: str, owner_address: str) -> Optional[float]:
        """Request a refund for a ticket."""
        if ticket_id not in self.tickets:
            raise ValueError("Ticket not found")

        ticket = self.tickets[ticket_id]
        if ticket.owner_address != owner_address:
            raise ValueError("Not ticket owner")

        if ticket.status != TicketStatus.VALID:
            raise ValueError("Ticket is not valid for refund")

        event = self.events[ticket.event_id]
        refund_amount = self.smart_contract.calculate_refund_amount(ticket, event)

        if refund_amount is None:
            raise ValueError("Ticket is not eligible for refund")

        ticket.status = TicketStatus.CANCELLED
        self._add_transaction("refund_ticket", ticket_id, {
            "owner_address": owner_address,
            "refund_amount": refund_amount
        })

        return refund_amount

    def use_ticket(self, ticket_id: str, presented_by_address: str) -> bool:
        """Mark a ticket as used."""
        if not self.verify_ticket(ticket_id, presented_by_address):
            return False

        ticket = self.tickets[ticket_id]
        if ticket.status == TicketStatus.VALID:
            ticket.status = TicketStatus.USED
            self._add_transaction("use_ticket", ticket_id, {
                "presented_by": presented_by_address,
                "used_at": datetime.now().isoformat()
            })
            return True
        return False

    def verify_ticket(self, ticket_id: str, presented_by_address: str) -> bool:
        """Verify ticket validity and ownership."""
        if ticket_id not in self.tickets:
            return False

        ticket = self.tickets[ticket_id]
        if ticket.event_id not in self.events:
            return False

        event = self.events[ticket.event_id]

        return (
                ticket.status == TicketStatus.VALID and
                ticket.owner_address == presented_by_address and
                event.date > datetime.now() and
                not event.is_cancelled
        )

    def _add_transaction(self, type_: str, id_: str, data: Dict):
        """Add a transaction to pending transactions."""
        self.pending_transactions.append({
            "type": type_,
            "id": id_,
            "timestamp": datetime.now().isoformat(),
            "data": data
        })

    def get_event_stats(self, event_id: str) -> Dict:
        """Get detailed statistics for an event."""
        if event_id not in self.events:
            raise ValueError("Event not found")

        event = self.events[event_id]
        tickets = self.get_event_tickets(event_id)

        stats = {
            "total_tickets": sum(event.total_tickets.values()),
            "available_tickets": sum(event.available_tickets.values()),
            "sold_tickets": sum(event.total_tickets.values()) - sum(event.available_tickets.values()),
            "waitlist_size": len(event.waitlist),
            "revenue": sum(t.price for t in tickets),
            "tickets_by_type": {
                ticket_type: len([t for t in tickets if t.ticket_type == ticket_type])
                for ticket_type in TicketType
            },
            "used_tickets": len([t for t in tickets if t.status == TicketStatus.USED]),
            "cancelled_tickets": len([t for t in tickets if t.status == TicketStatus.CANCELLED])
        }

        return stats

    # ... (keeping existing methods like transfer_ticket, mine_pending_transactions, etc.)
    def transfer_ticket(self, ticket_id: str, from_address: str, to_address: str, price: float) -> bool:
        """Transfer ownership of a ticket."""
        if ticket_id not in self.tickets:
            raise ValueError("Ticket not found")

        ticket = self.tickets[ticket_id]

        if ticket.owner_address != from_address:
            raise ValueError("Transfer failed: Sender does not own the ticket")

        if ticket.status != TicketStatus.VALID:
            raise ValueError("Transfer failed: Ticket is not valid")

        # Validate resale price
        original_price = ticket.price
        max_resale_price = original_price * (1 + self.smart_contract.max_markup_percentage)
        if price > max_resale_price:
            raise ValueError(
                f"Transfer failed: Price exceeds maximum allowed markup of {self.smart_contract.max_markup_percentage * 100}%")

        # Update ownership
        ticket.transfer_history.append({
            "timestamp": datetime.now().isoformat(),
            "from": from_address,
            "to": to_address,
            "price": price
        })
        ticket.owner_address = to_address

        # Update user tickets mapping
        self.user_tickets[from_address].remove(ticket_id)
        if to_address not in self.user_tickets:
            self.user_tickets[to_address] = set()
        self.user_tickets[to_address].add(ticket_id)

        # Record transaction
        self._add_transaction("transfer_ticket", ticket_id, {
            "from": from_address,
            "to": to_address,
            "price": price
        })

        return True

    def get_user_tickets(self, user_address: str) -> List[Ticket]:
        """Retrieve all tickets owned by a user."""
        if user_address not in self.user_tickets:
            return []

        return [self.tickets[t_id] for t_id in self.user_tickets[user_address]]

    def get_event_tickets(self, event_id: str) -> List[Ticket]:
        """Retrieve all tickets for a specific event."""
        return [ticket for ticket in self.tickets.values() if ticket.event_id == event_id]

    def mine_pending_transactions(self, miner_address: str):
        """Simulate mining of pending transactions."""
        if not self.pending_transactions:
            print("No pending transactions to mine.")
            return

        # Create a reward transaction
        reward_transaction = {
            "type": "reward",
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "data": {
                "miner": miner_address,
                "reward": 10  # Mining reward (can be configurable)
            }
        }

        self.pending_transactions.append(reward_transaction)

        # Create a new block
        block = Block(datetime.now(), self.pending_transactions.copy(), self.chain[-1].hash)
        block.mine_block(self.difficulty)

        # Add block to chain
        self.chain.append(block)
        self.pending_transactions.clear()

        print(f"Block mined successfully by {miner_address}, reward added.")

    def display_blockchain(self):
        """Display the entire blockchain."""
        for i, block in enumerate(self.chain):
            print(f"Block {i}:")
            print(json.dumps(block.__dict__, default=str, indent=4))
            print("-" * 50)
class Block:
    def __init__(self, timestamp: datetime, transactions: List[Dict], previous_hash: str):
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """Calculate block hash."""
        block_data = json.dumps({
            "timestamp": self.timestamp.isoformat(),
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_data.encode()).hexdigest()

    def mine_block(self, difficulty: int):
        """Mine the block by finding a hash with the required number of leading zeros."""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

        print(f"Block mined with nonce {self.nonce}: {self.hash}")