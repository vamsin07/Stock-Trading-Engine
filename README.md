# Stock-Trading-Engine

This repository contains a working solution for a real-time stock trading engine that matches buy orders with sell orders. The solution is implemented in Python using custom data structures and lock-free concepts with optimistic concurrency control to simulate a real-world trading environment—all while avoiding built-in dictionary/map structures.

## Requirements

- **Order Entry:**  
  Implement an `addOrder` function that accepts order type, ticker symbol, quantity, and price. Support up to 1,024 tickers.

- **Order Matching:**  
  Implement a `matchOrder` function that matches orders based on the criterion: if the highest buy price is greater than or equal to the lowest sell price, then execute a trade. The matching process should run in O(n) time per ticker.

- **Concurrency:**  
  Handle race conditions when multiple threads (simulating multiple brokers) modify the order book. The design uses a lock-free approach (conceptually) with custom data structures.

## Design Overview

### Data Structures

- **Fixed-Size Array of OrderBooks:**  
  An array of 1,024 `OrderBook` objects is used—each corresponding to one ticker. This fixed structure avoids high-level map/dictionary constructs.

- **Linked Lists for Orders:**  
  Each `OrderBook` maintains two sorted linked lists:
  - **Buy Orders:** Sorted in descending order by price (and by timestamp for tie-breakers) so that the best buy is at the head.
  - **Sell Orders:** Sorted in ascending order by price (and by timestamp for tie-breakers) so that the best (lowest) sell is at the head.

### Order Matching Logic

- **Price-Time Priority:**  
  Orders are matched based on price first and then by timestamp to ensure fairness. For instance, if two orders have the same price, the earlier order is executed first.

- **Matching Process:**  
  For a given ticker:
  1. **Retrieve the Best Orders:**  
     The highest buy order (head of the buy list) and the lowest sell order (head of the sell list) are compared.
  2. **Check Match Condition:**  
     If the buy price is at least as high as the sell price, a trade is executed.
  3. **Determine Trade Quantity:**  
     The quantity traded is the minimum of the available quantities from the two orders.
  4. **Update or Remove Orders:**  
     Quantities are reduced, and orders that are completely executed (quantity becomes zero) are marked inactive and eventually removed.
  5. **Loop Until No Match Exists:**  
     The matching continues until no further match is possible.

### Concurrency and Lock-Free Techniques

- **Optimistic Concurrency Control:**  
  Each `OrderBook` maintains a version counter. The matching process reads the version and attempts to commit changes by atomically updating it (via a simulated compare-and-swap). If a collision is detected (version mismatch), the process retries.

- **Simulated Atomic Operations:**  
  A custom `_compare_and_swap` method is used to simulate atomic updates for the order counter and the order book’s version. Although Python’s GIL limits true parallelism, this approach demonstrates the lock-free principles that are applicable in lower-level languages.

### Debugging and Error Handling

- **Detailed Docstrings:**  
  Each class and function includes docstrings explaining its purpose, parameters, and return values.
- **Try/Except Blocks:**  
  Critical operations are wrapped in try/except blocks to catch and log errors.
- **Debug Print Statements:**  
  Extensive debug prints trace the flow of order additions, matching events, retries in the optimistic concurrency loop, and final statistics of the simulation.

## How to Run the Solution

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/Stock-Trading-Engine.git
   cd Stock-Trading-Engine
