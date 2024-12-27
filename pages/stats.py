# pages/stats.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit, QMessageBox
from PyQt6.QtCore import Qt
from blockchain_ticketing import TicketingBlockchain


class StatsPage(QWidget):
    def __init__(self, blockchain: TicketingBlockchain):
        super().__init__()
        self.blockchain = blockchain

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

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

    def showEventStats(self):
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
                # tickets_by_type is likely a dict
                sub_lines = []
                for ttype, count in value.items():
                    sub_lines.append(f"   {ttype.value.capitalize()}: {count}")
                sub_str = "\n".join(sub_lines)
                lines.append(f"{key}:\n{sub_str}")
            else:
                lines.append(f"{key}: {value}")

        self.stats_display_area.setText("\n".join(lines))

    def updateEventList(self):
        """Refresh the event combo with current events."""
        self.stats_event_combo.clear()
        for event_id, event_obj in self.blockchain.events.items():
            self.stats_event_combo.addItem(event_obj.name, event_id)
