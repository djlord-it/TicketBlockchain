from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
import uuid
from typing import Dict, List, Optional, Set
from enum import Enum
import time

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

class TicketStatus(Enum):
    VALID = "valid"
    USED = "used"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING_TRANSFER = "pending_transfer"

class TicketType(Enum):
    REGULAR = "regular"
    VIP = "vip"
    EARLY_BIRD = "early_bird"
    STUDENT = "student"

@dataclass
class Event:
    event_id: str
    name: str
    venue: str
    date: datetime
    total_tickets: Dict[TicketType, int]
    prices: Dict[TicketType, float]
    organizer_address: str
    description: str
    category: str
    max_tickets_per_user: int
    refundable_until: datetime
    available_tickets: Dict[TicketType, int] = field(init=False)
    is_cancelled: bool = False
    waitlist: Set[str] = field(default_factory=set)
    minimum_price: Dict[TicketType, float] = field(default_factory=dict)
    ticket_transfer_cooldown: timedelta = timedelta(minutes=30)

    def __post_init__(self):
        self.available_tickets = self.total_tickets.copy()
        self.minimum_price = {t: self.prices[t] * 0.5 for t in self.prices}

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
    last_transfer: datetime = None
    pending_transfer: Dict = field(default_factory=dict)

    def __post_init__(self):
        self.qr_code = self._generate_qr_code()
        self.last_transfer = self.purchased_at

    def _generate_qr_code(self) -> str:
        data = f"{self.ticket_id}:{self.event_id}:{self.owner_address}:{int(time.time())}"
        return hashlib.sha256(data.encode()).hexdigest()

class Block:
    def __init__(self, timestamp: datetime, transactions: List[Dict], previous_hash: str):
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        data = json.dumps({
            "timestamp": self.timestamp.isoformat(),
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def mine_block(self, difficulty: int):
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

class SmartContract:
    def __init__(self):
        self.refund_policy = {"7_days": 1.0, "3_days": 0.75, "1_day": 0.5}
        self.max_markup_percentage = 0.5

    def calculate_refund_amount(self, ticket: 'Ticket', event: 'Event') -> Optional[float]:
        if datetime.now() > event.refundable_until:
            return None
        d = (event.date - datetime.now()).days
        if d >= 7: return ticket.price * self.refund_policy["7_days"]
        elif d >= 3: return ticket.price * self.refund_policy["3_days"]
        elif d >= 1: return ticket.price * self.refund_policy["1_day"]
        return None

class TicketingBlockchain:
    def __init__(self, difficulty: int = 2):
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict] = []
        self.difficulty = difficulty
        self.events: Dict[str, Event] = {}
        self.tickets: Dict[str, Ticket] = {}
        self.smart_contract = SmartContract()
        self.user_tickets: Dict[str, Set[str]] = {}
        self.suspicious_patterns: Dict[str, List[datetime]] = {}
        self.chain.append(Block(datetime.now(), [], "0"))

    def create_event(self, name: str, venue: str, date: datetime,
                     ticket_types: Dict[TicketType, int],
                     prices: Dict[TicketType, float],
                     organizer_address: str, description: str,
                     category: str, max_tickets_per_user: int,
                     refundable_until: datetime) -> Event:
        e_id = str(uuid.uuid4())
        e = Event(
            event_id=e_id,
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
        self.events[e_id] = e
        self.pending_transactions.append({
            "type": "create_event",
            "id": e_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "name": name,
                "venue": venue,
                "date": date.isoformat(),
                "ticket_types": {t.value: c for t, c in ticket_types.items()},
                "prices": {t.value: p for t, p in prices.items()},
                "organizer_address": organizer_address,
                "description": description,
                "category": category,
                "max_tickets_per_user": max_tickets_per_user,
                "refundable_until": refundable_until.isoformat()
            }
        })
        return e

    def _verify_signature(self, payload: bytes, signature: bytes, pubkey_bytes: bytes) -> bool:
        try:
            pub = serialization.load_der_public_key(pubkey_bytes)
            pub.verify(signature, payload, ec.ECDSA(hashes.SHA256()))
            return True
        except InvalidSignature:
            return False
        except Exception:
            return False

    def mint_ticket(self, event_id: str, buyer_address: str, ticket_type: TicketType,
                    signature: bytes = None, public_key_bytes: bytes = None) -> Ticket:
        if event_id not in self.events:
            raise ValueError("Event not found")
        e = self.events[event_id]
        if datetime.now() > e.date:
            raise ValueError("Event has passed")
        if e.is_cancelled:
            e.waitlist.add(buyer_address)
            raise ValueError("Event cancelled, added to waitlist")
        if e.available_tickets[ticket_type] <= 0:
            e.waitlist.add(buyer_address)
            raise ValueError("No tickets left, added to waitlist")

        recent = [
            t for t in self.get_user_tickets(buyer_address)
            if (datetime.now() - t.purchased_at).days < 1
        ]
        if len(recent) >= 10:
            raise ValueError("Too many buys in 24h")

        if signature and public_key_bytes:
            pl = f"mint:{event_id}:{buyer_address}:{ticket_type.value}".encode()
            if not self._verify_signature(pl, signature, public_key_bytes):
                raise ValueError("Invalid signature")

        user_tix = [
            t for t in self.get_user_tickets(buyer_address)
            if t.event_id == event_id
        ]
        if len(user_tix) >= e.max_tickets_per_user:
            raise ValueError("Max tickets per user reached")

        tid = str(uuid.uuid4())
        tk = Ticket(
            ticket_id=tid,
            event_id=event_id,
            ticket_type=ticket_type,
            price=e.prices[ticket_type],
            owner_address=buyer_address,
            metadata={}
        )
        tk.transfer_history.append({
            "timestamp": datetime.now().isoformat(),
            "from": "mint",
            "to": buyer_address,
            "price": e.prices[ticket_type]
        })
        self.tickets[tid] = tk
        e.available_tickets[ticket_type] -= 1
        if buyer_address not in self.user_tickets:
            self.user_tickets[buyer_address] = set()
        self.user_tickets[buyer_address].add(tid)
        self._add_transaction("mint_ticket", tid, {
            "event_id": event_id, "buyer": buyer_address,
            "ticket_type": ticket_type.value
        })
        return tk

    def transfer_ticket(self, ticket_id: str, from_addr: str, to_addr: str, price: float,
                        signature: bytes = None, public_key_bytes: bytes = None) -> bool:
        if ticket_id not in self.tickets:
            raise ValueError("Ticket not found")
        tk = self.tickets[ticket_id]
        if tk.owner_address != from_addr:
            raise ValueError("You do not own this ticket")
        if tk.status != TicketStatus.VALID:
            raise ValueError(f"Ticket is {tk.status.value}")
        e = self.events[tk.event_id]
        if datetime.now() > e.date:
            raise ValueError("Event passed")

        if signature and public_key_bytes:
            pl = f"transfer:{ticket_id}:{from_addr}:{to_addr}:{price}".encode()
            if not self._verify_signature(pl, signature, public_key_bytes):
                raise ValueError("Invalid signature")

        if price < e.minimum_price[tk.ticket_type]:
            raise ValueError(f"Price below minimum {e.minimum_price[tk.ticket_type]}")

        now = datetime.now()
        if tk.last_transfer and now - tk.last_transfer < e.ticket_transfer_cooldown:
            raise ValueError("Transfer cooldown active")

        if from_addr not in self.suspicious_patterns:
            self.suspicious_patterns[from_addr] = []
        daily = [dt for dt in self.suspicious_patterns[from_addr] if (now - dt).days < 1]
        if len(daily) >= 5:
            raise ValueError("Suspicious pattern, wait 24h")

        tk.status = TicketStatus.PENDING_TRANSFER
        tk.pending_transfer = {"to": to_addr, "price": price, "expires": now + timedelta(hours=24)}

        self.suspicious_patterns[from_addr].append(now)
        self._add_transaction("init_transfer", ticket_id, {
            "from": from_addr, "to": to_addr, "price": price
        })
        return True

    def confirm_transfer(self, ticket_id: str, to_addr: str) -> bool:
        if ticket_id not in self.tickets:
            raise ValueError("Ticket not found")
        tk = self.tickets[ticket_id]
        if tk.status != TicketStatus.PENDING_TRANSFER:
            raise ValueError("No pending transfer")

        if tk.pending_transfer.get("to") != to_addr:
            raise ValueError("Invalid confirm address")

        if datetime.now() > tk.pending_transfer["expires"]:
            tk.status = TicketStatus.VALID
            tk.pending_transfer = {}
            raise ValueError("Transfer expired")

        old = tk.owner_address
        tk.owner_address = to_addr
        tk.status = TicketStatus.VALID
        tk.last_transfer = datetime.now()
        tk.transfer_history.append({
            "timestamp": datetime.now().isoformat(),
            "from": old, "to": to_addr,
            "price": tk.pending_transfer["price"]
        })
        self.user_tickets[old].remove(ticket_id)
        if to_addr not in self.user_tickets:
            self.user_tickets[to_addr] = set()
        self.user_tickets[to_addr].add(ticket_id)
        tk.pending_transfer = {}
        self._add_transaction("confirm_transfer", ticket_id, {
            "from": old, "to": to_addr, "price": tk.price
        })
        return True

    def get_user_tickets(self, addr: str) -> List[Ticket]:
        if addr not in self.user_tickets:
            return []
        return [self.tickets[tid] for tid in self.user_tickets[addr]]

    def get_event_tickets(self, event_id: str) -> List[Ticket]:
        return [tk for tk in self.tickets.values() if tk.event_id == event_id]

    def request_refund(self, ticket_id: str, owner_addr: str) -> float:
        if ticket_id not in self.tickets:
            raise ValueError("Ticket not found")
        tk = self.tickets[ticket_id]
        if tk.owner_address != owner_addr:
            raise ValueError("Not owner")
        if tk.status != TicketStatus.VALID:
            raise ValueError("Ticket not valid for refund")

        e = self.events[tk.event_id]
        amt = self.smart_contract.calculate_refund_amount(tk, e)
        if amt is None:
            raise ValueError("Not eligible for refund")

        tk.status = TicketStatus.CANCELLED
        self._add_transaction("refund_ticket", ticket_id, {"owner": owner_addr, "amt": amt})
        return amt

    def cancel_event(self, event_id: str, organizer_addr: str) -> bool:
        if event_id not in self.events:
            raise ValueError("No such event")
        e = self.events[event_id]
        if e.organizer_address != organizer_addr:
            raise ValueError("Not organizer")
        e.is_cancelled = True
        for t in self.get_event_tickets(event_id):
            if t.status == TicketStatus.VALID:
                t.status = TicketStatus.CANCELLED
                self._add_transaction("refund_ticket", t.ticket_id, {
                    "owner": t.owner_address, "amt": t.price
                })
        return True

    def get_event_stats(self, event_id: str) -> Dict:
        if event_id not in self.events:
            raise ValueError("Event not found")
        e = self.events[event_id]
        tix = self.get_event_tickets(event_id)
        return {
            "total_tickets": sum(e.total_tickets.values()),
            "available_tickets": sum(e.available_tickets.values()),
            "sold_tickets": sum(e.total_tickets.values()) - sum(e.available_tickets.values()),
            "waitlist_size": len(e.waitlist),
            "tickets_by_type": {
                t: len([x for x in tix if x.ticket_type == t])
                for t in e.total_tickets
            },
            "used_tickets": len([x for x in tix if x.status == TicketStatus.USED]),
            "cancelled_tickets": len([x for x in tix if x.status == TicketStatus.CANCELLED])
        }

    def mine_pending_transactions(self, miner_address: str):
        if not self.pending_transactions:
            print("No pending tx to mine.")
            return
        reward = {"type": "reward", "id": str(uuid.uuid4()),
                  "timestamp": datetime.now().isoformat(),
                  "data": {"miner": miner_address, "reward": 10}}
        self.pending_transactions.append(reward)
        b = Block(datetime.now(), self.pending_transactions.copy(), self.chain[-1].hash)
        b.mine_block(self.difficulty)
        self.chain.append(b)
        self.pending_transactions.clear()
        print(f"Mined a block. Reward for {miner_address}.")

    def _add_transaction(self, type_: str, id_: str, data: Dict):
        self.pending_transactions.append({
            "type": type_,
            "id": id_,
            "timestamp": datetime.now().isoformat(),
            "data": data
        })
