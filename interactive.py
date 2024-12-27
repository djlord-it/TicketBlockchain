import argparse
from blockchain_ticketing import TicketingBlockchain, TicketType
from datetime import datetime

# Initialize blockchain
def initialize_blockchain():
    return TicketingBlockchain(difficulty=2)

# Add a concert event
def add_concert(blockchain):
    print("\n--- Add a New Concert ---")
    name = input("Enter concert name: ")
    venue = input("Enter concert venue: ")
    date_str = input("Enter concert date (YYYY-MM-DD HH:MM): ")
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD HH:MM.")
        return

    description = input("Enter event description: ")
    category = input("Enter event category: ")
    max_tickets_per_user = int(input("Enter maximum tickets per user: "))
    refundable_until_str = input("Enter refund deadline (YYYY-MM-DD HH:MM): ")
    try:
        refundable_until = datetime.strptime(refundable_until_str, "%Y-%m-%d %H:%M")
    except ValueError:
        print("Invalid date format for refund deadline. Please use YYYY-MM-DD HH:MM.")
        return

    ticket_types = {}
    prices = {}
    for t_type in TicketType:
        count = int(input(f"Enter total {t_type.value} tickets: "))
        price = float(input(f"Enter price for {t_type.value} tickets: "))
        ticket_types[t_type] = count
        prices[t_type] = price

    organizer_address = input("Enter organizer wallet address: ")

    event = blockchain.create_event(
        name=name,
        venue=venue,
        date=date,
        ticket_types=ticket_types,
        prices=prices,
        organizer_address=organizer_address,
        description=description,
        category=category,
        max_tickets_per_user=max_tickets_per_user,
        refundable_until=refundable_until
    )
    print(f"\nConcert '{event.name}' created successfully with Event ID: {event.event_id}")

# Mint tickets for a buyer
def mint_tickets(blockchain):
    print("\n--- Mint Tickets ---")
    event_id = input("Enter Event ID: ")
    buyer_address = input("Enter buyer wallet address: ")
    ticket_type_str = input("Enter ticket type (regular, vip, early_bird): ")
    try:
        ticket_type = TicketType[ticket_type_str.upper()]
    except KeyError:
        print("Invalid ticket type. Use one of: regular, vip, early_bird.")
        return

    try:
        ticket = blockchain.mint_ticket(event_id, buyer_address, ticket_type)
        print(f"Ticket {ticket.ticket_id} minted successfully for buyer {buyer_address}")
    except ValueError as e:
        print(f"Error: {e}")

# Transfer tickets between users
def transfer_tickets(blockchain):
    print("\n--- Transfer Tickets ---")
    ticket_id = input("Enter Ticket ID: ")
    from_address = input("Enter current owner wallet address: ")
    to_address = input("Enter new owner wallet address: ")
    price = float(input("Enter transfer price: "))

    try:
        success = blockchain.transfer_ticket(ticket_id, from_address, to_address, price)
        if success:
            print(f"Ticket {ticket_id} successfully transferred from {from_address} to {to_address}")
    except ValueError as e:
        print(f"Error: {e}")

# Display all tickets for an event
def display_event_tickets(blockchain):
    print("\n--- Display Event Tickets ---")
    event_id = input("Enter Event ID: ")

    tickets = blockchain.get_event_tickets(event_id)
    if not tickets:
        print("No tickets found for this event.")
        return

    print(f"\nTickets for Event ID {event_id}:")
    for ticket in tickets:
        print(f"- Ticket ID: {ticket.ticket_id}, Owner: {ticket.owner_address}, Price: {ticket.price}, Type: {ticket.ticket_type.value}")

# Request a refund
def request_refund(blockchain):
    print("\n--- Request a Refund ---")
    ticket_id = input("Enter Ticket ID: ")
    owner_address = input("Enter your wallet address: ")

    try:
        refund_amount = blockchain.request_refund(ticket_id, owner_address)
        print(f"Refund processed successfully. Amount: {refund_amount:.2f}")
    except ValueError as e:
        print(f"Error: {e}")

# Display event statistics
def display_event_stats(blockchain):
    print("\n--- Event Statistics ---")
    event_id = input("Enter Event ID: ")

    try:
        stats = blockchain.get_event_stats(event_id)
        print(f"\nStatistics for Event ID {event_id}:")
        for key, value in stats.items():
            print(f"{key}: {value}")
    except ValueError as e:
        print(f"Error: {e}")

# Interactive menu
def interactive_menu(blockchain):
    while True:
        print("\n--- Ticketing Blockchain System ---")
        print("1. Add a Concert")
        print("2. Mint Tickets")
        print("3. Transfer Tickets")
        print("4. Display Event Tickets")
        print("5. Request Refund")
        print("6. Display Event Statistics")
        print("7. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            add_concert(blockchain)
        elif choice == "2":
            mint_tickets(blockchain)
        elif choice == "3":
            transfer_tickets(blockchain)
        elif choice == "4":
            display_event_tickets(blockchain)
        elif choice == "5":
            request_refund(blockchain)
        elif choice == "6":
            display_event_stats(blockchain)
        elif choice == "7":
            print("Exiting... Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

# Main interactive function
def main():
    blockchain = initialize_blockchain()

    parser = argparse.ArgumentParser(description="Blockchain-Based Ticketing System")
    parser.add_argument("--add", action="store_true", help="Add a new concert")
    parser.add_argument("--mint", action="store_true", help="Mint tickets for an event")
    parser.add_argument("--transfer", action="store_true", help="Transfer a ticket between users")
    parser.add_argument("--display", action="store_true", help="Display all tickets for an event")
    parser.add_argument("--refund", action="store_true", help="Request a refund for a ticket")
    parser.add_argument("--stats", action="store_true", help="Display statistics for an event")

    args = parser.parse_args()

    if args.add:
        add_concert(blockchain)
    elif args.mint:
        mint_tickets(blockchain)
    elif args.transfer:
        transfer_tickets(blockchain)
    elif args.display:
        display_event_tickets(blockchain)
    elif args.refund:
        request_refund(blockchain)
    elif args.stats:
        display_event_stats(blockchain)
    else:
        interactive_menu(blockchain)

if __name__ == "__main__":
    main()
