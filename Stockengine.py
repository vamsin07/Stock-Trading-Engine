import random
import time
from enum import Enum
import threading
import concurrent.futures
from typing import List, Optional

class OrderType(Enum):
    """Enumeration for order types."""
    BUY = "BUY"
    SELL = "SELL"

class Order:
    def __init__(self, order_id: int, order_type: OrderType, ticker_index: int, 
                 quantity: int, price: float, timestamp: float):
        """
        Initialize an Order.
        
        Args:
            order_id (int): Unique identifier for the order.
            order_type (OrderType): BUY or SELL.
            ticker_index (int): Index of the ticker (0 to max_tickers-1).
            quantity (int): Number of shares.
            price (float): Price per share.
            timestamp (float): Time at which the order was created.
        """
        self.id = order_id
        self.type = order_type
        self.ticker_index = ticker_index
        self.quantity = quantity
        self.price = price
        self.timestamp = timestamp
        self.next = None  # For linked list implementation
        self.is_active = True  # Flag to indicate if order is still active

    def __repr__(self):
        return (f"Order(id={self.id}, type={self.type}, ticker_index={self.ticker_index}, "
                f"quantity={self.quantity}, price={self.price}, timestamp={self.timestamp})")

class OrderBook:
    def __init__(self, ticker_index: int):
        """
        Initialize an OrderBook for a specific ticker.
        
        Args:
            ticker_index (int): Index of the ticker.
        """
        self.ticker_index = ticker_index
        self.buy_head = None   # Head pointer for buy orders (linked list)
        self.sell_head = None  # Head pointer for sell orders (linked list)
        self.version = 0       # Version counter for optimistic concurrency

class Trade:
    def __init__(self, buy_order_id: int, sell_order_id: int, ticker_index: int, 
                 quantity: int, price: float, timestamp: float):
        """
        Initialize a Trade record.
        
        Args:
            buy_order_id (int): ID of the buy order.
            sell_order_id (int): ID of the sell order.
            ticker_index (int): Ticker index.
            quantity (int): Number of shares traded.
            price (float): Execution price.
            timestamp (float): Timestamp of trade execution.
        """
        self.buy_order_id = buy_order_id
        self.sell_order_id = sell_order_id
        self.ticker_index = ticker_index
        self.quantity = quantity
        self.price = price
        self.timestamp = timestamp

    def __repr__(self):
        return (f"Trade(buy_order_id={self.buy_order_id}, sell_order_id={self.sell_order_id}, "
                f"ticker_index={self.ticker_index}, quantity={self.quantity}, "
                f"price={self.price}, timestamp={self.timestamp})")

class StockTradingEngine:
    def __init__(self, max_tickers: int = 1024):
        """
        Initialize the trading engine.
        
        Args:
            max_tickers (int): Maximum number of tickers to support.
        """
        self.max_tickers = max_tickers
        self.order_books = [OrderBook(i) for i in range(max_tickers)]
        self.ticker_symbols = [""] * max_tickers  # Array mapping index -> ticker symbol
        # Pre-populate ticker symbols (e.g., STOCK0000, STOCK0001, ...)
        for i in range(max_tickers):
            self.ticker_symbols[i] = f"STOCK{i:04d}"
        self.order_counter = 0
        self.executed_trades = []  # List to store executed Trade objects
        self.local = threading.local()  # Thread-local storage (if needed)

    def _get_ticker_index(self, ticker: str) -> int:
        """
        Convert a ticker symbol to its index.
        
        Args:
            ticker (str): Ticker symbol.
        
        Returns:
            int: Corresponding index.
        """
        try:
            for i in range(self.max_tickers):
                if self.ticker_symbols[i] == ticker:
                    return i
            # If not found, find first empty slot and assign the ticker.
            for i in range(self.max_tickers):
                if self.ticker_symbols[i] == "":
                    self.ticker_symbols[i] = ticker
                    return i
            raise ValueError(f"No space for new ticker: {ticker}")
        except Exception as e:
            print(f"[ERROR] _get_ticker_index: {e}")
            raise

    def _insert_order_sorted(self, head: Optional[Order], new_order: Order) -> Order:
        """
        Insert a new order into the linked list in sorted order.
        
        For BUY orders, higher price comes first; for SELL orders, lower price comes first.
        If prices are equal, earlier timestamp gets priority.
        
        Args:
            head (Optional[Order]): Current head of the list.
            new_order (Order): Order to insert.
        
        Returns:
            Order: New head of the list.
        """
        try:
            if not head:
                return new_order

            # Check if new order should become the new head.
            if ((new_order.type == OrderType.BUY and new_order.price > head.price) or
                (new_order.type == OrderType.SELL and new_order.price < head.price) or
                (new_order.price == head.price and new_order.timestamp < head.timestamp)):
                new_order.next = head
                return new_order

            current = head
            prev = None
            while current:
                if new_order.type == OrderType.BUY:
                    if new_order.price > current.price or (new_order.price == current.price and new_order.timestamp < current.timestamp):
                        break
                else:
                    if new_order.price < current.price or (new_order.price == current.price and new_order.timestamp < current.timestamp):
                        break
                prev = current
                current = current.next

            if prev:
                new_order.next = prev.next
                prev.next = new_order
                return head
            else:
                new_order.next = head
                return new_order
        except Exception as e:
            print(f"[ERROR] _insert_order_sorted: {e}")
            raise

    def _add_order_to_book(self, order_book: OrderBook, order: Order) -> None:
        """
        Add an order to the appropriate linked list in the given order book.
        
        Args:
            order_book (OrderBook): The order book for a ticker.
            order (Order): The order to add.
        """
        try:
            if order.type == OrderType.BUY:
                order_book.buy_head = self._insert_order_sorted(order_book.buy_head, order)
            else:
                order_book.sell_head = self._insert_order_sorted(order_book.sell_head, order)
            print(f"[DEBUG] Order added to book for ticker index {order_book.ticker_index}")
        except Exception as e:
            print(f"[ERROR] _add_order_to_book: {e}")
            raise

    def addOrder(self, order_type: OrderType, ticker: str, quantity: int, price: float) -> int:
        """
        Public method to add a new order to the engine.
        
        Args:
            order_type (OrderType): Order type (BUY or SELL).
            ticker (str): Ticker symbol.
            quantity (int): Number of shares.
            price (float): Price per share.
        
        Returns:
            int: The unique order ID.
        """
        try:
            if not isinstance(order_type, OrderType):
                raise ValueError("order_type must be an OrderType enum")
            if not isinstance(ticker, str) or len(ticker) == 0:
                raise ValueError("ticker must be a non-empty string")
            if not isinstance(quantity, int) or quantity <= 0:
                raise ValueError("quantity must be a positive integer")
            if not isinstance(price, float) or price <= 0:
                raise ValueError("price must be a positive float")
            
            ticker_index = self._get_ticker_index(ticker)
            order_id = self._get_next_order_id()
            new_order = Order(
                order_id=order_id,
                order_type=order_type,
                ticker_index=ticker_index,
                quantity=quantity,
                price=price,
                timestamp=time.time()
            )
            order_book = self.order_books[ticker_index]
            self._add_order_to_book(order_book, new_order)
            
            # Attempt to match orders immediately after adding
            self.matchOrder(ticker_index)
            
            return order_id
        except Exception as e:
            print(f"[ERROR] addOrder: {e}")
            raise

    def _get_next_order_id(self) -> int:
        """
        Atomically generate and return the next order ID.
        
        Returns:
            int: Next order ID.
        """
        try:
            while True:
                current = self.order_counter
                new_value = current + 1
                if self._compare_and_swap(self, "order_counter", current, new_value):
                    return current
        except Exception as e:
            print(f"[ERROR] _get_next_order_id: {e}")
            raise

    def _compare_and_swap(self, obj, attr, old_value, new_value) -> bool:
        """
        Simulate an atomic compare-and-swap operation.
        
        Args:
            obj: Object containing the attribute.
            attr (str): Attribute name.
            old_value: Expected current value.
            new_value: New value to set.
        
        Returns:
            bool: True if the swap was successful, else False.
        """
        try:
            current = getattr(obj, attr)
            if current != old_value:
                return False
            setattr(obj, attr, new_value)
            return True
        except Exception as e:
            print(f"[ERROR] _compare_and_swap: {e}")
            raise

    def matchOrder(self, ticker_index: int) -> List[Trade]:
        """
        Match buy and sell orders for a given ticker using an optimistic,
        lock-free approach with a time complexity of O(n) for that ticker.
        
        Args:
            ticker_index (int): Index of the ticker.
        
        Returns:
            List[Trade]: List of trades executed.
        """
        trades = []
        retry_count = 0
        max_retries = 10
        try:
            while retry_count < max_retries:
                order_book = self.order_books[ticker_index]
                buy_head = order_book.buy_head
                sell_head = order_book.sell_head
                current_version = order_book.version

                if not buy_head or not sell_head:
                    # No matching possible if either list is empty.
                    return trades

                # Work on local copies of the linked lists
                local_buy_head = buy_head
                local_sell_head = sell_head
                local_trades = []
                
                while local_buy_head and local_sell_head:
                    if not local_buy_head.is_active:
                        local_buy_head = local_buy_head.next
                        continue
                    if not local_sell_head.is_active:
                        local_sell_head = local_sell_head.next
                        continue
                    if local_buy_head.price >= local_sell_head.price:
                        trade_quantity = min(local_buy_head.quantity, local_sell_head.quantity)
                        trade_price = local_sell_head.price
                        trade = Trade(
                            buy_order_id=local_buy_head.id,
                            sell_order_id=local_sell_head.id,
                            ticker_index=ticker_index,
                            quantity=trade_quantity,
                            price=trade_price,
                            timestamp=time.time()
                        )
                        local_trades.append(trade)
                        local_buy_head.quantity -= trade_quantity
                        local_sell_head.quantity -= trade_quantity
                        if local_buy_head.quantity == 0:
                            local_buy_head.is_active = False
                            local_buy_head = local_buy_head.next
                        if local_sell_head.quantity == 0:
                            local_sell_head.is_active = False
                            local_sell_head = local_sell_head.next
                    else:
                        break

                # Try to commit the changes by updating the version
                if self._compare_and_swap(order_book, "version", current_version, current_version + 1):
                    for trade in local_trades:
                        self._mark_order_inactive(buy_head, trade.buy_order_id)
                        self._mark_order_inactive(sell_head, trade.sell_order_id)
                    self._cleanup_inactive_orders(order_book)
                    trades.extend(local_trades)
                    self.executed_trades.extend(local_trades)
                    for trade in local_trades:
                        ticker_sym = self.ticker_symbols[trade.ticker_index]
                        print(f"[DEBUG] Executed trade: {trade.quantity} shares of {ticker_sym} at ${trade.price:.2f}")
                    return trades
                else:
                    retry_count += 1
                    print(f"[DEBUG] matchOrder retry count: {retry_count}")
            return trades
        except Exception as e:
            print(f"[ERROR] matchOrder: {e}")
            raise

    def _mark_order_inactive(self, head: Optional[Order], order_id: int) -> None:
        """
        Mark a specific order (by ID) as inactive in the linked list.
        
        Args:
            head (Optional[Order]): Head of the linked list.
            order_id (int): ID of the order to mark inactive.
        """
        try:
            current = head
            while current:
                if current.id == order_id and current.is_active:
                    current.is_active = False
                    return
                current = current.next
        except Exception as e:
            print(f"[ERROR] _mark_order_inactive: {e}")
            raise

    def _cleanup_inactive_orders(self, order_book: OrderBook) -> None:
        """
        Remove all inactive orders from both the buy and sell linked lists.
        
        Args:
            order_book (OrderBook): The order book to clean up.
        """
        try:
            # Clean up buy orders
            if order_book.buy_head:
                while order_book.buy_head and not order_book.buy_head.is_active:
                    order_book.buy_head = order_book.buy_head.next
                current = order_book.buy_head
                while current and current.next:
                    if not current.next.is_active:
                        current.next = current.next.next
                    else:
                        current = current.next
            # Clean up sell orders
            if order_book.sell_head:
                while order_book.sell_head and not order_book.sell_head.is_active:
                    order_book.sell_head = order_book.sell_head.next
                current = order_book.sell_head
                while current and current.next:
                    if not current.next.is_active:
                        current.next = current.next.next
                    else:
                        current = current.next
        except Exception as e:
            print(f"[ERROR] _cleanup_inactive_orders: {e}")
            raise


def simulate_trading(engine: StockTradingEngine, num_orders: int = 1000, num_threads: int = 4):
    """
    Simulate trading by concurrently adding orders using multiple threads.
    
    Args:
        engine (StockTradingEngine): Instance of the trading engine.
        num_orders (int): Total number of orders to generate.
        num_threads (int): Number of concurrent threads.
    """
    def worker(thread_id, orders_per_thread):
        for _ in range(orders_per_thread):
            order_type = random.choice([OrderType.BUY, OrderType.SELL])
            ticker_index = random.randint(0, engine.max_tickers - 1)
            ticker = engine.ticker_symbols[ticker_index]
            quantity = random.randint(1, 1000)
            price = round(random.uniform(10.0, 1000.0), 2)
            try:
                engine.addOrder(order_type, ticker, quantity, price)
            except ValueError as e:
                print(f"[ERROR] Thread {thread_id} - Error adding order: {e}")
            time.sleep(random.uniform(0.001, 0.005))
    try:
        orders_per_thread = num_orders // num_threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=worker, args=(i, orders_per_thread))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
    except Exception as e:
        print(f"[ERROR] simulate_trading: {e}")
        raise


def main():
    """
    Main function to initialize the trading engine, simulate trading,
    and print summary statistics.
    """
    try:
        engine = StockTradingEngine()
        print("[DEBUG] Starting trading simulation with concurrent threads...")
        start_time = time.time()
        simulate_trading(engine, num_orders=10000, num_threads=8)
        end_time = time.time()
        total_trades = len(engine.executed_trades)
        print(f"\n[DEBUG] Simulation complete. Total trades executed: {total_trades}")
        print(f"[DEBUG] Time taken: {end_time - start_time:.2f} seconds")
        if total_trades > 0:
            avg_price = sum(trade.price for trade in engine.executed_trades) / total_trades
            print(f"[DEBUG] Average trade price: ${avg_price:.2f}")
            ticker_counts = [0] * engine.max_tickers
            for trade in engine.executed_trades:
                ticker_counts[trade.ticker_index] += trade.quantity
            max_count = 0
            max_index = 0
            for i, count in enumerate(ticker_counts):
                if count > max_count:
                    max_count = count
                    max_index = i
            if max_count > 0:
                print(f"[DEBUG] Most active ticker: {engine.ticker_symbols[max_index]} with {max_count} shares traded")
    except Exception as e:
        print(f"[ERROR] main: {e}")
        raise


if __name__ == "__main__":
    main()
