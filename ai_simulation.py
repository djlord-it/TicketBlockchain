import random
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from blockchain_ticketing import TicketingBlockchain, TicketType, Event
from fraud_detection import FraudDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_simulation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AISimulation')


@dataclass
class PurchaseAttempt:
    """Tracks a single purchase attempt with timestamp"""
    timestamp: datetime
    ticket_id: Optional[str] = None
    success: bool = False


@dataclass
class PurchaseResult:
    """Represents the result of a purchase attempt"""
    success: bool
    message: str
    ticket_id: Optional[str] = None
    fraud_status: Optional[str] = None


class AIUser:
    """
    Represents a single simulated 'user' (agent) with certain behavior patterns.
    """

    def __init__(self, wallet_address: str, behavior_profile: Dict):
        """
        Initialize an AI user with specific behavioral characteristics.

        Args:
            wallet_address: The user's unique wallet address
            behavior_profile: Dict containing user behavior parameters
        """
        self.wallet = wallet_address
        self.behavior_profile = behavior_profile
        self.purchase_attempts: List[PurchaseAttempt] = []
        logger.debug(f"Created new AI user with wallet {wallet_address}")

    def record_purchase_attempt(self, result: PurchaseResult):
        """Record a purchase attempt with timestamp"""
        attempt = PurchaseAttempt(
            timestamp=datetime.now(),
            ticket_id=result.ticket_id,
            success=result.success
        )
        self.purchase_attempts.append(attempt)

    def get_recent_successful_purchases(self, hours: int = 24) -> int:
        """Count successful purchases within the last n hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return sum(1 for attempt in self.purchase_attempts
                   if attempt.success and attempt.timestamp > cutoff)


class AISimulation:
    def __init__(self, blockchain: TicketingBlockchain, fraud_detector: FraudDetector):
        self.blockchain = blockchain
        self.fraud_detector = fraud_detector
        self.users: List[AIUser] = []
        logger.info("Initialized AI Simulation")

    def create_users(self, n_users: int = 100) -> None:
        """
        Create n_users with varied behavior profiles.

        Args:
            n_users: Number of AI users to create
        """
        try:
            # Get available ticket types from the blockchain
            event_types = set()
            for event in self.blockchain.events.values():
                event_types.update(event.total_tickets.keys())

            if not event_types:
                raise ValueError("No ticket types available in any events")

            for i in range(n_users):
                wallet = f"AISimUser_{i:03d}"
                # Create more varied behavior profiles
                behavior = {
                    "preferred_types": random.sample(list(event_types),
                                                     k=min(2, len(event_types))),
                    "max_tickets_each_time": random.randint(1, 3),
                    "fraud_prone": random.random() < 0.2,  # 20% chance of being fraud-prone
                    "purchase_frequency": random.uniform(0.3, 0.9),  # Likelihood to attempt purchase
                    "price_sensitivity": random.uniform(0.5, 1.5),  # Multiplier for acceptable price
                    "retry_attempts": random.randint(1, 3)  # How many times they'll retry on failure
                }
                self.users.append(AIUser(wallet, behavior))

            logger.info(f"Successfully created {n_users} AI users")

        except Exception as e:
            logger.error(f"Error creating users: {str(e)}", exc_info=True)
            raise

    def get_available_ticket_types(self, event_id: str) -> List[TicketType]:
        """Get available ticket types for an event"""
        try:
            event = self.blockchain.events[event_id]
            return [
                t_type for t_type, count in event.available_tickets.items()
                if count > 0
            ]
        except KeyError:
            logger.error(f"Event {event_id} not found")
            return []
        except Exception as e:
            logger.error(f"Error getting available ticket types: {str(e)}")
            return []

    def simulate_purchases(self, event_id: str, steps: int = 50) -> None:
        """
        Simulate a series of purchase attempts.

        Args:
            event_id: Target event ID
            steps: Number of simulation steps
        """
        if not self.users:
            logger.error("No users available for simulation")
            return

        logger.info(f"Starting purchase simulation for event {event_id} with {steps} steps")

        try:
            event = self.blockchain.events[event_id]
        except KeyError:
            logger.error(f"Event {event_id} not found")
            return

        successful_purchases = 0
        failed_purchases = 0

        for step in range(steps):
            user = random.choice(self.users)

            # Check if user wants to attempt purchase based on their frequency
            if random.random() > user.behavior_profile["purchase_frequency"]:
                logger.debug(f"User {user.wallet} skipped purchase attempt")
                continue

            # Get available ticket types for this event
            available_types = self.get_available_ticket_types(event_id)
            if not available_types:
                logger.warning(f"No available tickets for event {event_id}")
                break

            # Filter for user's preferred types that are available
            preferred_available = [
                t for t in user.behavior_profile["preferred_types"]
                if t in available_types
            ]

            if not preferred_available:
                logger.debug(f"No preferred ticket types available for user {user.wallet}")
                continue

            ticket_type = random.choice(preferred_available)
            quantity = random.randint(1, user.behavior_profile["max_tickets_each_time"])

            logger.info(
                f"Step {step + 1}/{steps}: User {user.wallet} attempting to purchase "
                f"{quantity} {ticket_type.value} ticket(s)"
            )

            for _ in range(quantity):
                result = self.attempt_purchase(user, event_id, ticket_type)
                user.record_purchase_attempt(result)

                if result.success:
                    successful_purchases += 1
                    logger.info(f"Successfully purchased ticket {result.ticket_id}")
                else:
                    failed_purchases += 1
                    logger.warning(f"Purchase failed: {result.message}")

                time.sleep(0.1)  # Simulate realistic timing

            # Log progress every 10 steps
            if (step + 1) % 10 == 0:
                logger.info(f"Progress: {step + 1}/{steps} steps completed")
                logger.info(
                    f"Success rate: {successful_purchases / (successful_purchases + failed_purchases) * 100:.2f}%")

    def attempt_purchase(self, user: AIUser, event_id: str, ticket_type: TicketType) -> PurchaseResult:
        transaction_data = {
            "wallet": user.wallet,
            "event_id": event_id,
            "ticket_type": ticket_type.value,
            "timestamp": datetime.now().isoformat(),
            "fraud_prone": user.behavior_profile["fraud_prone"],
            "recent_purchases": user.get_recent_successful_purchases(hours=24)
        }
        try:
            fraud_status = self.fraud_detector.judge_transaction(transaction_data)
            if fraud_status == "fraud":
                logger.error(f"[FRAUD BLOCKED] {user.wallet} tried {ticket_type.value}, blocked by FraudDetector.")
                return PurchaseResult(
                    success=False,
                    message="Transaction blocked: Fraud detection triggered",
                    fraud_status=fraud_status
                )
            elif fraud_status == "suspect":
                logger.warning(f"[SUSPECT] {user.wallet} buying {ticket_type.value}")

        except Exception as e:
            logger.error(f"Fraud detection error: {str(e)}")
            return PurchaseResult(success=False, message=f"Fraud detection error: {str(e)}")

        # Attempt the mint
        try:
            ticket = self.blockchain.mint_ticket(event_id, user.wallet, ticket_type)
            logger.info(f"[OK] {user.wallet} -> {ticket_type.value} ticket {ticket.ticket_id} purchased")
            return PurchaseResult(
                success=True,
                message="Purchase successful",
                ticket_id=ticket.ticket_id,
                fraud_status=fraud_status
            )
        except ValueError as e:
            # e.g. "No tickets available," "Max tickets exceeded," ...
            logger.warning(f"[FAILED] {user.wallet}: {str(e)}")
            return PurchaseResult(success=False, message=str(e), fraud_status=fraud_status)
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error for {user.wallet}: {str(e)}", exc_info=True)
            return PurchaseResult(success=False, message=f"Unexpected error: {str(e)}", fraud_status=fraud_status)


def main():
    try:
        # Initialize blockchain
        bc = TicketingBlockchain(difficulty=2)

        # Create test event with larger capacity for 100 customers
        event = bc.create_event(
            name="AI Sim Concert",
            venue="Virtual Stadium",
            date=datetime.now() + timedelta(days=5),
            ticket_types={
                TicketType.REGULAR: 200,  # Increased capacity
                TicketType.VIP: 50,  # Increased capacity
            },
            prices={
                TicketType.REGULAR: 40.0,
                TicketType.VIP: 100.0,
            },
            organizer_address="OrganizerXYZ",
            description="An event for AI Simulation",
            category="Music",
            max_tickets_per_user=5,
            refundable_until=datetime.now() + timedelta(days=4)
        )

        # Initialize components
        fd = FraudDetector()
        sim = AISimulation(blockchain=bc, fraud_detector=fd)

        # Run simulation with more users and steps
        logger.info("Starting simulation")
        sim.create_users(n_users=100)  # Increased to 100 users
        sim.simulate_purchases(event_id=event.event_id, steps=200)  # More steps for more users
        logger.info("Simulation complete")

    except Exception as e:
        logger.error(f"Fatal error in simulation: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()