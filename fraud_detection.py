import random
import joblib

class FraudDetector:
    """
    Very simple placeholder for an ML-based or rules-based fraud detection system.
    Could be replaced with a real trained model.
    """
    def __init__(self):
        # If you had a saved model, you might load it here:
        self.model = joblib.load("fraud_model.pkl")
        pass

    def judge_transaction(self, tx_data: dict) -> str:
        """
        Return "normal", "suspect", or "fraud".
        :param tx_data: {
            'wallet': str,
            'event_id': str,
            'ticket_type': str,
            'timestamp': str,
            'fraud_prone': bool,
            ... more features ...
        }
        """
        # If tx_data['fraud_prone'] is True, let's raise suspicion/fraud more often
        base_suspicion = 0.1  # 10% suspicion for normal
        if tx_data.get("fraud_prone"):
            base_suspicion += 0.3  # 40% total suspicion

        rand_val = random.random()
        if rand_val < base_suspicion:
            # 50% chance "suspect" vs "fraud"
            if random.random() < 0.5:
                return "suspect"
            else:
                return "fraud"

        # Otherwise normal
        return "normal"

    def train_model(self, transaction_logs):
        """
        If you had a dataset of transaction logs labeled with fraud=1/0,
        you could do real ML training here. For now, it's a stub.
        """
        pass
