# 🧩 Word Ladder Adventure

A Python-based word puzzle game where players transform one word into another by changing one letter at a time — powered by real dictionary lookups and multiple AI search algorithms.

---

## 🎮 What is Word Ladder?

Word Ladder is a classic puzzle invented by Lewis Carroll. The goal is to go from a **start word** to a **target word** by changing **one letter at a time**, where every step must be a valid English word.

**Example:**
```
CAT → COT → DOT → DOG
```

---

## ✨ Features

- 🔤 **Real dictionary validation** — words are checked live using the [Datamuse API](https://www.datamuse.com/api/)
- 🤖 **5 built-in AI search algorithms** to find the optimal path:
  - BFS (Breadth-First Search)
  - DFS (Depth-First Search)
  - GBFS (Greedy Best-First Search)
  - UCS (Uniform Cost Search)
  - A\* (A-Star Search)
- 🚫 **Challenge modes** — restrict certain letters or ban specific words
- 🌳 **Graph visualization** — generates a visual tree of the solution path using Graphviz
- 🖥️ **Game UI** — interactive interface for playing the game

---

## 📁 Project Structure

```
word-ladder-adventure/
│
├── game_logic.py          # Core algorithms, word validation, graph visualization
├── game_ui.py             # Game interface and user interaction
├── WordLadderGame.spec    # PyInstaller build configuration
└── word_ladder_tree.png   # Sample visualization output
```

---

## 🚀 Getting Started

### Prerequisites

```bash
pip install requests graphviz
```

> Also install the [Graphviz system package](https://graphviz.org/download/) for tree visualization.

### Run the Game

```bash
python game_ui.py
```

---

## 🧠 How the Algorithms Work

| Algorithm | Strategy | Finds Shortest Path? |
|-----------|----------|----------------------|
| BFS | Explores all neighbors level by level | ✅ Yes |
| DFS | Dives deep before backtracking | ❌ Not guaranteed |
| GBFS | Picks the word closest to the target | ❌ Not guaranteed |
| UCS | Picks the lowest-cost path so far | ✅ Yes |
| A\* | Combines cost + heuristic (smartest) | ✅ Yes |

---

## 🌳 Visualization Example

After solving a puzzle, the game generates a graph showing the solution path (blue) and alternative word branches (red dashed):

<img width="4615" height="465" alt="word_ladder_tree" src="https://github.com/user-attachments/assets/32d2ccbd-ff22-4743-8c2b-9b81f980043a" />


---

## 🛠️ Built With

- **Python 3**
- [Datamuse API](https://www.datamuse.com/api/) — for word lookups
- [Graphviz](https://graphviz.org/) — for graph rendering
- `heapq`, `collections.deque` — for search algorithm implementation

---

## 👤 Author

Made with ❤️ by **Talha Khan**
