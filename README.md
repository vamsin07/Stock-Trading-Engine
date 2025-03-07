# Stock Trading Engine

This repository contains a working solution for a real-time stock trading engine that matches buy orders with sell orders. The solution is implemented in Python using custom data structures and optimistic lock-free techniques to simulate concurrent order matching as it might occur in a live trading system. The design avoids using high-level dictionaries or maps by leveraging fixed-size arrays and custom linked lists.

## Requirements

- **Order Entry:**  
  Implement an `addOrder` function that accepts order type, ticker symbol, quantity, and price. Support up to 1,024 tickers.
  
- **Order Matching:**  
  Implement a `matchOrder` function that matches orders based on the criterion: if the highest buy price is greater than or equal to the lowest sell price, then execute a trade. This function should run in O(n) time where n is the number of orders in the order book.

- **Concurrency:**  
  Handle race conditions when multiple threads (simulating multiple brokers) modify the stock order book. Use a lock-free design that avoids high-level data structures like dictionaries or maps.

## Design Overview

### Data Structures

- **Fixed-Size Array of OrderBooks:**  
  An array of 1,024 `OrderBook` objects is used—one per ticker. This ensures a fixed, predictable memory footprint and meets the constraint of not using dictionaries or maps.

- **Linked Lists for Orders:**  
  Each `OrderBook` maintains two sorted linked lists:
  - **Buy Orders:** Sorted in descending order by price (and by timestamp for tie-breakers) so that the best buy is always at the head.
  - **Sell Orders:** Sorted in ascending order by price (and by timestamp for tie-breakers) so that the best (lowest) sell is always at the head.

### Order Matching Logic

- **Price-Time Priority:**  
  Orders are matched first by price and then by the order in which they were received (timestamp). This ensures fairness—if two orders have the same price, the earlier one gets executed first.

- **Matching Process:**  
  For a given ticker:
  1. **Retrieve the Best Orders:**  
     The highest buy order (from the buy list) and the lowest sell order (from the sell list) are selected.
  2. **Check Match Condition:**  
     If the highest buy price is greater than or equal to the lowest sell price, a trade is executed.
  3. **Determine Trade Quantity:**  
     The trade quantity is the minimum of the quantities available in the two orders.
  4. **Update or Remove Orders:**  
     Quantities are reduced by the trade amount, and fully executed orders (quantity becomes zero) are removed from the list.
  5. **Loop:**  
     The process continues until no further matching is possible.

### Concurrency and Lock-Free Techniques

- **Optimistic Concurrency Control:**  
  Each `OrderBook` has a version counter. During the matching process, the current version is read; after processing local copies of the order lists, the solution attempts to commit changes by atomically updating the version. If the version has changed (indicating another thread modified the book), the matching process is retried.

- **Simulated Atomic Operations:**  
  The solution uses a custom `_compare_and_swap` function to simulate atomic updates. Although Python's Global Interpreter Lock (GIL) limits true parallelism, this technique demonstrates the lock-free approach that could be implemented in lower-level languages like C++.

### Debugging and Error Handling

- **Try/Except Blocks:**  
  Functions include try/except blocks to catch and log errors during execution.
- **Debug Print Statements:**  
  Extensive debug prints are added throughout the code to trace:
  - Order additions and their positions in the linked lists.
  - Matching events and trade executions.
  - Retrying during optimistic concurrency control.
  - Overall simulation progress and summary statistics.

## How to Run the Solution

1. **Clone the Repository:**  
   ```bash
   git clone https://github.com/yourusername/stock-trading-engine.git
   cd stock-trading-engine
