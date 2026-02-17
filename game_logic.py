"""
Word Ladder Adventure - Core Game Logic
This file contains all the game algorithms and word validation functions
"""

import requests
import heapq
from collections import deque

# ================================
# API Functions
# ================================

def fetch_word_set(length):
    """Fetch words of specified length from Datamuse API"""
    try:
        response = requests.get(f"https://api.datamuse.com/words?sp={'?' * length}&max=1000")
        if response.status_code == 200:
            return {word['word'].upper() for word in response.json()}
        return set()
    except:
        return set()

def validate_word(word):
    """Validate if word exists in dictionary"""
    try:
        response = requests.get(f"https://api.datamuse.com/words?sp={word}&max=1")
        if response.status_code == 200:
            data = response.json()
            return bool(data) and data[0]['word'].upper() == word.upper()
        return False
    except:
        return False

# ================================
# Transition Validation
# ================================

def is_valid_transition(current, next_word, restricted_letters=None, banned_words=None):
    """Check if transition from current to next_word is valid"""
    if len(current) != len(next_word):
        return False

    diff = sum(1 for c1, c2 in zip(current, next_word) if c1 != c2)
    if diff != 1:
        return False

    if restricted_letters:
        for letter in next_word:
            if letter in restricted_letters:
                return False

    if banned_words and next_word in banned_words:
        return False

    return True

# ================================
# Neighbor Finding
# ================================

def neighbours(word, word_set, restricted_letters=None, banned_words=None):
    """Find all valid neighbor words"""
    neighbors = []
    for w in range(len(word)):
        for let in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            junior = word[:w] + let + word[w+1:]
            if (
                junior in word_set and junior != word and
                is_valid_transition(word, junior, restricted_letters, banned_words)
            ):
                neighbors.append(junior)
    return neighbors

# ================================
# Search Algorithms
# ================================

def bfs(start, target, word_set, restricted_letters=None, banned_words=None):
    """Breadth-First Search algorithm"""
    queue = deque([[start]])
    visited = set()

    while queue:
        path = queue.popleft()
        current = path[-1]

        if current == target:
            return path

        for neighbor in neighbours(current, word_set, restricted_letters, banned_words):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])
    return None

def dfs(start, target, word_set, visited=None, path=None):
    """Depth-First Search algorithm"""
    if visited is None:
        visited = set()
    if path is None:
        path = [start]

    if start == target:
        return path

    visited.add(start)

    for neighbor in neighbours(start, word_set):
        if neighbor not in visited:
            new_path = dfs(neighbor, target, word_set, visited, path + [neighbor])
            if new_path:
                return new_path

    return None

def gbfs(start, target, word_set):
    """Greedy Best-First Search algorithm"""
    def heuristic(word):
        return sum(c1 != c2 for c1, c2 in zip(word, target))

    heap = []
    heapq.heappush(heap, (heuristic(start), start, [start]))
    visited = set()

    while heap:
        h_cost, current, path = heapq.heappop(heap)
        if current == target:
            return path
        if current in visited:
            continue
        visited.add(current)
        for neighbor in neighbours(current, word_set):
            if neighbor not in visited:
                new_h = heuristic(neighbor)
                heapq.heappush(heap, (new_h, neighbor, path + [neighbor]))
    return None

def ucs(start, target, word_set):
    """Uniform Cost Search algorithm"""
    heap = []
    heapq.heappush(heap, (0, start, [start]))
    visited = set()

    while heap:
        cost, current, path = heapq.heappop(heap)
        if current == target:
            return path
        if current in visited:
            continue
        visited.add(current)
        for neighbor in neighbours(current, word_set):
            if neighbor not in visited:
                heapq.heappush(heap, (cost + 1, neighbor, path + [neighbor]))
    return None

def a_star(start, target, word_set):
    """A* Search algorithm"""
    def heuristic(word):
        return sum(c1 != c2 for c1, c2 in zip(word, target)) + 0.5 * len(neighbours(word, word_set))

    heap = []
    heapq.heappush(heap, (heuristic(start), 0, start, [start]))
    g_costs = {start: 0}
    visited = set()

    while heap:
        f_cost, g_cost, current, path = heapq.heappop(heap)

        if current == target:
            return path

        if current in visited and g_cost >= g_costs.get(current, float('inf')):
            continue

        visited.add(current)
        g_costs[current] = g_cost

        for neighbor in neighbours(current, word_set):
            new_g = g_cost + 1
            if neighbor not in g_costs or new_g < g_costs[neighbor]:
                g_costs[neighbor] = new_g
                new_f = new_g + heuristic(neighbor)
                heapq.heappush(heap, (new_f, new_g, neighbor, path + [neighbor]))

    return None

# ================================
# Graph Visualization
# ================================

def visualize_tree(path, alternative_words, user_name, score, output_path='word_ladder_tree'):
    """
    Visualize the word ladder path as a graph
    
    Args:
        path: List of words in the solution path
        alternative_words: Dict of word -> list of alternative neighbors
        user_name: Player's name
        score: Game score
        output_path: Where to save the graph (default: 'word_ladder_tree')
    
    Returns:
        Path to the generated PNG file
    """
    try:
        import graphviz
        
        dot = graphviz.Digraph(comment='Word Ladder Tree', format='png')
        dot.attr(rankdir='TB')
        dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')

        # Draw the main path with blue solid edges
        for i in range(len(path) - 1):
            dot.edge(path[i], path[i + 1], color='blue', style='solid', 
                    label=str(i + 1), penwidth='2.0')
        
        # Highlight start and end nodes
        dot.node(path[0], path[0], fillcolor='lightgreen', style='rounded,filled')
        dot.node(path[-1], path[-1], fillcolor='gold', style='rounded,filled')
        
        # Draw alternative paths with red dashed edges
        for word in alternative_words:
            for neighbor in alternative_words[word]:
                # Only draw if it's not part of the main path
                if not (word in path and neighbor in path and 
                       abs(path.index(word) - path.index(neighbor)) == 1):
                    dot.edge(word, neighbor, color='red', style='dashed')
        
        # Add game info as a label
        dot.attr(label=f"Player: {user_name}\\nScore: {score}", 
                fontsize='14', fontname='Arial Bold')

        # Render the graph
        dot.render(output_path, view=False, cleanup=True)
        
        return f"{output_path}.png"
    
    except ImportError:
        print("Warning: graphviz not installed. Install with: pip install graphviz")
        return None
    except Exception as e:
        print(f"Error creating visualization: {e}")
        return None