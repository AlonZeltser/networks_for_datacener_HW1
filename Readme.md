# Fat-Tree Network Simulator

## 🧩 Overview

This project is the submission for HW in the course <bold>Networks for Data Centers and AI </bold>.

The project is aimed to visualize and simulate the behavior of a Fat-Tree network topology under various scenarios.
For this purpose, I implemented a fully functional network-flow simulator.
The simulator is based on the design pattern DES (discrete even simulator) 
The goal architecture implemented is of "Fat Tree Network Topology" by *Al-Fares et al., SIGCOMM 2008*.
The simulator models packet transmission, routing, and failure scenarios in a scalable data-center topology.

<div style="text-align:center">
<span style="font-size:20px">
Note

This is a temporal submission, not all functionality is implemented, fully tested or documented in this file.
</span>
</div>

**Objectives:**
- Understand and implement a hierarchical Fat-Tree topology.
- Simulate packet delivery between hosts across pods.
- Evaluate network behavior under **normal** and **disruptive** conditions
- Observe routing, load balancing (ECMP), and fault recovery.

## ⚙️ Implementation Approach
**Language:** Python 3.9  
**Framework:** My own event-driven simulator  
**Alternatives:** Using external simulation libraries such as mininet. Eventually I choose to implement my own for the learning process.  
**Other Considerations**: I chose to use an Object-Oriented modeling for the system, where each object acts similarly to its real-world behavior.  

## AI Usage
**I developed and coded the project by myself, yet was assisted by Gen AI tools as follows:**  
- Choosing DSE Design Pattern (over usage of mininet), pattern exploration: ChatGPT5    
- Python ongoing hints features exploration: ChatGPT5  
- Typo corrections finding: Github Copilot (GPT-5 mini)  
- Readme.md: hyper-text syntax, common readme structuring: ChatGPT5, Copilot  (GPT-5 mini)
- Visualizations: pakages selection, implementation hints and examples: github Copilot (GPT-5 mini, Claude Sonnet 3.5)

ChatGPT doumentation will be published as part of final submission.

### Architecture Summary
| Real life Component  | Responsibility                                                                |
|----------------------|-------------------------------------------------------------------------------|
| `Host`               | Generates and receives packets; interacts via ARP and routing logic (TBD)|
| `Switch`             | Maintains forwarding tables; handles packet forwarding and ECMP|
| `Link`               | Connects two nodes; simulates latency, bandwidth, and (TBD) randomal failures |

| Pure SW Component     | Responsibility                                                                                                     |
|-----------------------|--------------------------------------------------------------------------------------------------------------------|
| `Node`                | Base class for an actor that may receive and handle events                                                         |
| `NetworkNode`         | A Node that can receive netwok packets (Host, Switch..)                                                            |
| `Scheduler`           | Alias for the discrete event manager. Handles scheduled-tasks and execute them on the right time                   |
| `Message` / `Packet`  | Data unit that is sent between components                                                                          |
| `SimulatorCreator`    | BAse class for creating instances of simulation (e.g. Fat Tree). A concrete creator should inheret from this class |

### Design Highlights
- Packages split over functionalities
- Object-oriented, real-time simulating implementation.
- Event queue ensures deterministic simulation order.
- Fat Tree: Configurable `k` parameter (controls pods, switch count, and hosts).
- Forwarding tables auto-generated per Al-Fares conventions (TBD)
- Failure injection for testing robustness (TBD)

## ▶️ How to Run

### 1. Clone the repository
```bash
    git clone https://github.com/AlonZeltser/networks_for_datacener_HW1.git
```

### 2. Install dependencies

### TBD update requirements.txt before final commit

```bash
pip install -r requirements.txt
```

### 3. Run baseline scenario
### TBD add command line for Far-Tree k, and other parameters
```bash
python main.py 
```

### 4. Run with disruptive events
### TBD add command line options for Fat-Tree k, and other parameters
```bash
TBD 
```

### 5. Optional arguments
###TBD

| Flag | Description |
|------|--------------|


## 🧪 Tests and Scenarios


### TBD 


## 📊 Results Summary
### TBD

## 🗂️ Project Structure
### update before final commit

```
networks_for_datacener_HW1/
├── README.md
├── main.py
├── requirements.txt (TBD)
├── des/
│   ├── __init__.py
│   ├── des.py
│   ├── priority_queue.py
├── netowrk_simulation/
│   ├── __init__.py
│   ├── Host
│   ├── ip
│   ├── link
│   ├── message
│   ├── netowrk_node
│   ├── node
│   ├── switch
├── scenarios/
│   ├── fat_tree_topo_creator.py
│   ├── hsh_creator.py
│   ├── simulator_creator.py
├── statistics/
│   ├── tbd
├── unit_tests/
│   ├── tbd
```

## 📚 References
- M. Al-Fares, A. Loukissas, A. Vahdat,  
  *A Scalable, Commodity Data Center Network Architecture*, SIGCOMM 2008.  
- [Wikipedia: Fat Tree network topology](https://en.wikipedia.org/wiki/Fat_tree)

## ✍️ Author
**Alon Zeltser**  
Date: 5.11.2025
