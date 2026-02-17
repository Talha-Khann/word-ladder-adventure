import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
from game_logic import (
    fetch_word_set, validate_word, is_valid_transition,
    neighbours, bfs, dfs, a_star, gbfs, ucs
)

# Try to import optional features
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL not available - graph viewing disabled")

# Try to import visualize_tree - make it optional
try:
    import game_logic
    if hasattr(game_logic, 'visualize_tree'):
        visualize_tree = game_logic.visualize_tree
        GRAPH_AVAILABLE = True
    else:
        GRAPH_AVAILABLE = False
        print("visualize_tree function not found in game_logic.py")
        def visualize_tree(path, alternative_words, user_name, score, output_path='word_ladder_tree'):
            return None
except Exception as e:
    GRAPH_AVAILABLE = False
    print(f"Could not import visualize_tree: {e}")
    def visualize_tree(path, alternative_words, user_name, score, output_path='word_ladder_tree'):
        return None

class WordLadderUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Word Ladder Adventure")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Game state variables
        self.user_name = tk.StringVar()
        self.difficulty = tk.StringVar(value="1")
        self.mode = tk.StringVar(value="AI")
        self.start_word = tk.StringVar()
        self.target_word = tk.StringVar()
        self.algorithm = tk.StringVar(value="1")
        
        self.word_set = set()
        self.current_word = ""
        self.path = []
        self.used_words = set()
        self.moves = 0
        self.move_limit = 10
        self.word_length = 3
        self.restricted_letters = set()
        self.banned_words = set()
        self.child_nodes = {}
        self.ai_path = []
        
        # Configure styles
        self.setup_styles()
        
        # Create UI
        self.create_widgets()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom styles
        style.configure('Title.TLabel', font=('Arial', 24, 'bold'), foreground='#2c3e50')
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'), foreground='#34495e')
        style.configure('Info.TLabel', font=('Arial', 11), foreground='#7f8c8d')
        style.configure('Success.TLabel', font=('Arial', 12, 'bold'), foreground='#27ae60')
        style.configure('Error.TLabel', font=('Arial', 12, 'bold'), foreground='#e74c3c')
        
        style.configure('Primary.TButton', font=('Arial', 11, 'bold'), padding=10)
        style.configure('Secondary.TButton', font=('Arial', 10), padding=8)
        
    def create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Setup Tab
        self.setup_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.setup_frame, text="Setup")
        self.create_setup_tab()
        
        # Game Tab
        self.game_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.game_frame, text="Play Game")
        self.create_game_tab()
        
        # Disable game tab initially
        self.notebook.tab(1, state='disabled')
        
    def create_setup_tab(self):
        # Title
        title = ttk.Label(self.setup_frame, text="🎮 Word Ladder Adventure", 
                         style='Title.TLabel')
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Player Name
        ttk.Label(self.setup_frame, text="Player Name:", style='Header.TLabel').grid(
            row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.setup_frame, textvariable=self.user_name, width=30, 
                 font=('Arial', 11)).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Difficulty Level
        ttk.Label(self.setup_frame, text="Difficulty Level:", style='Header.TLabel').grid(
            row=2, column=0, sticky=tk.W, pady=5)
        
        difficulty_frame = ttk.Frame(self.setup_frame)
        difficulty_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Radiobutton(difficulty_frame, text="Beginner (3-letter, 10 moves)", 
                       variable=self.difficulty, value="1").pack(anchor=tk.W)
        ttk.Radiobutton(difficulty_frame, text="Advanced (4-letter, 15 moves)", 
                       variable=self.difficulty, value="2").pack(anchor=tk.W)
        ttk.Radiobutton(difficulty_frame, text="Challenge (5-letter, 20 moves + restrictions)", 
                       variable=self.difficulty, value="3").pack(anchor=tk.W)
        
        # Game Mode
        ttk.Label(self.setup_frame, text="Game Mode:", style='Header.TLabel').grid(
            row=3, column=0, sticky=tk.W, pady=5)
        
        mode_frame = ttk.Frame(self.setup_frame)
        mode_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Radiobutton(mode_frame, text="AI Mode (Get algorithm hints)", 
                       variable=self.mode, value="AI", 
                       command=self.toggle_algorithm).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Custom Mode (Figure it out yourself)", 
                       variable=self.mode, value="CUSTOM", 
                       command=self.toggle_algorithm).pack(anchor=tk.W)
        
        # Algorithm Selection (for AI mode)
        ttk.Label(self.setup_frame, text="AI Algorithm:", style='Header.TLabel').grid(
            row=4, column=0, sticky=tk.W, pady=5)
        
        self.algo_frame = ttk.Frame(self.setup_frame)
        self.algo_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Radiobutton(self.algo_frame, text="BFS (Breadth-First Search)", 
                       variable=self.algorithm, value="1").pack(anchor=tk.W)
        ttk.Radiobutton(self.algo_frame, text="DFS (Depth-First Search)", 
                       variable=self.algorithm, value="2").pack(anchor=tk.W)
        ttk.Radiobutton(self.algo_frame, text="A* (A-Star)", 
                       variable=self.algorithm, value="3").pack(anchor=tk.W)
        ttk.Radiobutton(self.algo_frame, text="GBFS (Greedy Best-First)", 
                       variable=self.algorithm, value="4").pack(anchor=tk.W)
        ttk.Radiobutton(self.algo_frame, text="UCS (Uniform Cost Search)", 
                       variable=self.algorithm, value="5").pack(anchor=tk.W)
        
        # Start and Target Words
        ttk.Label(self.setup_frame, text="Start Word:", style='Header.TLabel').grid(
            row=5, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.setup_frame, textvariable=self.start_word, width=30, 
                 font=('Arial', 11)).grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(self.setup_frame, text="Target Word:", style='Header.TLabel').grid(
            row=6, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.setup_frame, textvariable=self.target_word, width=30, 
                 font=('Arial', 11)).grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Start Game Button
        ttk.Button(self.setup_frame, text="Start Game", style='Primary.TButton',
                  command=self.start_game).grid(row=7, column=0, columnspan=2, pady=20)
        
        # Configure grid weights
        self.setup_frame.columnconfigure(1, weight=1)
        
    def toggle_algorithm(self):
        if self.mode.get() == "CUSTOM":
            for child in self.algo_frame.winfo_children():
                child.configure(state='disabled')
        else:
            for child in self.algo_frame.winfo_children():
                child.configure(state='normal')
    
    def create_game_tab(self):
        # Game info header
        self.info_frame = ttk.LabelFrame(self.game_frame, text="Game Information", padding="10")
        self.info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.current_word_label = ttk.Label(self.info_frame, text="Current Word: ---", 
                                           style='Header.TLabel')
        self.current_word_label.grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.target_word_label = ttk.Label(self.info_frame, text="Target Word: ---", 
                                          style='Info.TLabel')
        self.target_word_label.grid(row=0, column=1, sticky=tk.W, padx=20)
        
        self.moves_label = ttk.Label(self.info_frame, text="Moves: 0/10", 
                                     style='Info.TLabel')
        self.moves_label.grid(row=0, column=2, sticky=tk.W, padx=20)
        
        # Path display
        path_frame = ttk.LabelFrame(self.game_frame, text="Your Path", padding="10")
        path_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.path_text = scrolledtext.ScrolledText(path_frame, height=6, width=60, 
                                                   font=('Arial', 11), state='disabled',
                                                   wrap=tk.WORD)
        self.path_text.pack(fill=tk.BOTH, expand=True)
        
        # Input frame
        input_frame = ttk.LabelFrame(self.game_frame, text="Make Your Move", padding="10")
        input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(input_frame, text="Next Word:", style='Info.TLabel').grid(
            row=0, column=0, sticky=tk.W, padx=5)
        
        self.next_word_entry = ttk.Entry(input_frame, width=20, font=('Arial', 12))
        self.next_word_entry.grid(row=0, column=1, padx=5)
        self.next_word_entry.bind('<Return>', lambda e: self.submit_word())
        
        ttk.Button(input_frame, text="Submit", style='Primary.TButton',
                  command=self.submit_word).grid(row=0, column=2, padx=5)
        
        self.hint_button = ttk.Button(input_frame, text="Get Hint", 
                                     style='Secondary.TButton',
                                     command=self.get_hint)
        self.hint_button.grid(row=0, column=3, padx=5)
        
        # Message display
        self.message_label = ttk.Label(self.game_frame, text="", style='Info.TLabel')
        self.message_label.grid(row=3, column=0, pady=10)
        
        # Buttons
        button_frame = ttk.Frame(self.game_frame)
        button_frame.grid(row=4, column=0, pady=10)
        
        ttk.Button(button_frame, text="New Game", style='Secondary.TButton',
                  command=self.new_game).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Reset Current", style='Secondary.TButton',
                  command=self.reset_game).pack(side=tk.LEFT, padx=5)
        
        self.graph_button = ttk.Button(button_frame, text="View Graph", 
                                       style='Secondary.TButton',
                                       command=self.show_graph)
        self.graph_button.pack(side=tk.LEFT, padx=5)
        
        # Disable graph button if feature not available
        if not GRAPH_AVAILABLE:
            self.graph_button.config(state='disabled')
        
        # Configure grid weights
        self.game_frame.columnconfigure(0, weight=1)
        self.game_frame.rowconfigure(1, weight=1)
        
    def start_game(self):
        # Validate inputs
        if not self.user_name.get().strip():
            messagebox.showerror("Error", "Please enter your name!")
            return
        
        start = self.start_word.get().strip().upper()
        target = self.target_word.get().strip().upper()
        
        if not start or not target:
            messagebox.showerror("Error", "Please enter both start and target words!")
            return
        
        # Set difficulty parameters
        difficulty = self.difficulty.get()
        if difficulty == "1":
            self.word_length = 3
            self.move_limit = 10
            self.restricted_letters = set()
            self.banned_words = set()
        elif difficulty == "2":
            self.word_length = 4
            self.move_limit = 15
            self.restricted_letters = set()
            self.banned_words = set()
        else:
            self.word_length = 5
            self.move_limit = 20
            self.banned_words = {"CRANE", "PLANE"}
            self.restricted_letters = {'X', 'Z'}
        
        if len(start) != self.word_length or len(target) != self.word_length:
            messagebox.showerror("Error", 
                f"Words must be {self.word_length} letters long for this difficulty!")
            return
        
        # Show loading message
        self.message_label.config(text="Loading word dictionary... Please wait", 
                                 style='Info.TLabel')
        self.root.update()
        
        # Load word set in background
        threading.Thread(target=self.load_game_data, args=(start, target), 
                        daemon=True).start()
    
    def load_game_data(self, start, target):
        try:
            # Fetch word set
            self.word_set = fetch_word_set(self.word_length)
            self.word_set -= self.banned_words
            self.word_set = {word for word in self.word_set 
                           if not any(letter in self.restricted_letters for letter in word)}
            self.word_set.add(start)
            self.word_set.add(target)
            
            # If AI mode, compute path
            if self.mode.get() == "AI":
                algorithms = {
                    "1": bfs, "2": dfs, "3": a_star, "4": gbfs, "5": ucs
                }
                algo_func = algorithms[self.algorithm.get()]
                self.ai_path = algo_func(start, target, self.word_set)
                
                if not self.ai_path:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error", "AI could not find a path between these words!"))
                    return
            
            # Initialize game state
            self.current_word = start
            self.path = [start]
            self.used_words = {start}
            self.moves = 0
            self.child_nodes = {}
            
            # Update UI on main thread
            self.root.after(0, self.initialize_game_ui)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Error", f"Failed to load game: {str(e)}"))
    
    def initialize_game_ui(self):
        # Enable game tab and switch to it
        self.notebook.tab(1, state='normal')
        self.notebook.select(1)
        
        # Update labels
        self.current_word_label.config(text=f"Current Word: {self.current_word}")
        self.target_word_label.config(text=f"Target Word: {self.target_word.get().upper()}")
        self.moves_label.config(text=f"Moves: {self.moves}/{self.move_limit}")
        
        # Update path
        self.update_path_display()
        
        # Show initial message
        if self.mode.get() == "AI":
            algo_names = {"1": "BFS", "2": "DFS", "3": "A*", "4": "GBFS", "5": "UCS"}
            algo_name = algo_names[self.algorithm.get()]
            self.message_label.config(
                text=f"AI found a path using {algo_name}! Try to solve it step by step. Type 'hint' for help.",
                style='Success.TLabel')
            self.hint_button.config(state='normal')
        else:
            self.message_label.config(
                text="Figure out the path yourself - no hints available!",
                style='Info.TLabel')
            self.hint_button.config(state='disabled')
        
        # Focus on input
        self.next_word_entry.focus()
    
    def update_path_display(self):
        self.path_text.config(state='normal')
        self.path_text.delete(1.0, tk.END)
        self.path_text.insert(tk.END, " → ".join(self.path))
        self.path_text.config(state='disabled')
    
    def submit_word(self):
        next_word = self.next_word_entry.get().strip().upper()
        self.next_word_entry.delete(0, tk.END)
        
        if not next_word:
            return
        
        # Validate word
        if next_word not in self.word_set:
            self.message_label.config(
                text="❌ Invalid word! Not in dictionary.", 
                style='Error.TLabel')
            return
        
        if next_word in self.used_words:
            self.message_label.config(
                text="❌ Word already used! Try another.", 
                style='Error.TLabel')
            return
        
        if not is_valid_transition(self.current_word, next_word, 
                                   self.restricted_letters, self.banned_words):
            self.message_label.config(
                text="❌ Invalid transition! Must change exactly one letter.", 
                style='Error.TLabel')
            return
        
        # Valid move
        if self.current_word not in self.child_nodes:
            self.child_nodes[self.current_word] = neighbours(
                self.current_word, self.word_set, self.restricted_letters, self.banned_words)
        
        self.path.append(next_word)
        self.used_words.add(next_word)
        self.current_word = next_word
        self.moves += 1
        
        # Update UI
        self.current_word_label.config(text=f"Current Word: {self.current_word}")
        self.moves_label.config(text=f"Moves: {self.moves}/{self.move_limit}")
        self.update_path_display()
        
        # Check win condition
        if self.current_word == self.target_word.get().upper():
            self.win_game()
            return
        
        # Check move limit
        if self.moves >= self.move_limit:
            self.lose_game()
            return
        
        self.message_label.config(text="✓ Good move! Continue...", style='Success.TLabel')
    
    def get_hint(self):
        if self.mode.get() != "AI" or not self.ai_path:
            return
        
        if self.moves + 1 < len(self.ai_path):
            hint_word = self.ai_path[self.moves + 1]
            self.message_label.config(
                text=f"💡 Hint: Try '{hint_word}'", 
                style='Info.TLabel')
        else:
            self.message_label.config(
                text="No more hints available!", 
                style='Info.TLabel')
    
    def win_game(self):
        score = self.move_limit - self.moves
        message = f"🎉 Congratulations {self.user_name.get()}! You solved it!\n"
        message += f"Path: {' → '.join(self.path)}\n"
        message += f"Score: {score} (Higher is better)"
        
        # Generate graph visualization
        self.generate_graph(score)
        
        messagebox.showinfo("Victory!", message)
        self.next_word_entry.config(state='disabled')
        self.hint_button.config(state='disabled')
    
    def lose_game(self):
        message = f"Game Over! You ran out of moves.\n"
        message += f"Path taken: {' → '.join(self.path)}\n"
        message += f"Target was: {self.target_word.get().upper()}"
        
        messagebox.showinfo("Game Over", message)
        self.next_word_entry.config(state='disabled')
        self.hint_button.config(state='disabled')
    
    def reset_game(self):
        if messagebox.askyesno("Reset", "Reset current game?"):
            start = self.start_word.get().upper()
            self.current_word = start
            self.path = [start]
            self.used_words = {start}
            self.moves = 0
            
            self.current_word_label.config(text=f"Current Word: {self.current_word}")
            self.moves_label.config(text=f"Moves: {self.moves}/{self.move_limit}")
            self.update_path_display()
            self.message_label.config(text="Game reset! Start again.", style='Info.TLabel')
            self.next_word_entry.config(state='normal')
            self.hint_button.config(state='normal' if self.mode.get() == "AI" else 'disabled')
    
    def new_game(self):
        if messagebox.askyesno("New Game", "Start a new game?"):
            self.notebook.tab(1, state='disabled')
            self.notebook.select(0)
            self.next_word_entry.config(state='normal')
            self.message_label.config(text="")
    
    def generate_graph(self, score):
        """Generate the graph visualization"""
        if not GRAPH_AVAILABLE:
            self.message_label.config(
                text="Graph feature not available. Check game_logic.py has visualize_tree function.",
                style='Error.TLabel'
            )
            return
            
        try:
            graph_path = visualize_tree(
                self.path, 
                self.child_nodes, 
                self.user_name.get(), 
                score
            )
            
            if graph_path:
                self.current_graph_path = graph_path
                self.message_label.config(
                    text=f"Graph saved! Click 'View Graph' to see visualization.",
                    style='Success.TLabel'
                )
            else:
                self.message_label.config(
                    text="Could not generate graph. Make sure graphviz is installed.",
                    style='Error.TLabel'
                )
        except Exception as e:
            print(f"Error generating graph: {e}")
            self.message_label.config(
                text=f"Graph error: {e}",
                style='Error.TLabel'
            )
    
    def show_graph(self):
        """Display the graph in a new window with zoom functionality"""
        if not GRAPH_AVAILABLE:
            messagebox.showerror("Feature Unavailable", 
                "Graph visualization is not available.\n\n"
                "Make sure visualize_tree function exists in game_logic.py\n"
                "and graphviz is installed:\n"
                "pip install graphviz")
            return
            
        if not PIL_AVAILABLE:
            messagebox.showerror("PIL Not Installed", 
                "Image viewing requires PIL/Pillow.\n\n"
                "Install with: pip install pillow")
            return
        
        if not hasattr(self, 'current_graph_path') or not self.current_graph_path:
            # Generate graph if not exists
            score = self.move_limit - self.moves
            self.generate_graph(score)
            
            if not hasattr(self, 'current_graph_path') or not self.current_graph_path:
                messagebox.showerror("Error", 
                    "No graph available. Complete a game first!")
                return
        
        if not os.path.exists(self.current_graph_path):
            messagebox.showerror("Error", "Graph file not found!")
            return
        
        # Create new window to display graph
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Word Ladder Graph Visualization - Use Mouse Wheel to Zoom")
        graph_window.geometry("900x700")
        
        # Create top control bar
        control_frame = ttk.Frame(graph_window)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        zoom_label = ttk.Label(control_frame, text="Zoom: 100%", style='Info.TLabel')
        zoom_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(control_frame, text="Zoom In (+)", 
                  command=lambda: self.zoom_graph(graph_window, 1.2)).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Zoom Out (-)", 
                  command=lambda: self.zoom_graph(graph_window, 0.8)).pack(side=tk.LEFT, padx=2)
        
        # Create a frame with scrollbars
        canvas_frame = ttk.Frame(graph_window)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(canvas_frame, bg='white')
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        try:
            # Load original image
            original_img = Image.open(self.current_graph_path)
            
            # Store references in window object
            graph_window.original_img = original_img
            graph_window.canvas = canvas
            graph_window.zoom_label = zoom_label
            graph_window.zoom_level = 1.0
            graph_window.canvas_image = None
            
            # Function to update image display
            def update_image(scale=1.0):
                if scale == 'reset':
                    scale = 1.0
                elif scale == 'fit':
                    # Calculate scale to fit window
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    img_width, img_height = original_img.size
                    scale_w = canvas_width / img_width
                    scale_h = canvas_height / img_height
                    scale = min(scale_w, scale_h) * 0.95
                
                graph_window.zoom_level = scale
                
                # Resize image
                new_width = int(original_img.width * scale)
                new_height = int(original_img.height * scale)
                resized_img = original_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(resized_img)
                
                # Clear canvas and display new image
                canvas.delete("all")
                graph_window.canvas_image = canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                canvas.image = photo  # Keep reference
                canvas.config(scrollregion=(0, 0, new_width, new_height))
                
                # Update zoom label
                zoom_label.config(text=f"Zoom: {int(scale * 100)}%")
            
            # Set up zoom function
            graph_window.update_image = update_image
            
            # Initial display
            update_image(1.0)
            
            # Mouse wheel zoom
            def on_mouse_wheel(event):
                # Get mouse position relative to canvas
                x = canvas.canvasx(event.x)
                y = canvas.canvasy(event.y)
                
                # Determine zoom direction
                if event.delta > 0 or event.num == 4:  # Zoom in
                    scale = graph_window.zoom_level * 1.1
                else:  # Zoom out
                    scale = graph_window.zoom_level * 0.9
                
                # Limit zoom range
                scale = max(0.1, min(scale, 10.0))
                
                update_image(scale)
                
                # Adjust scroll to keep mouse position centered
                canvas.xview_moveto(x / (original_img.width * scale))
                canvas.yview_moveto(y / (original_img.height * scale))
            
            # Bind mouse wheel events
            canvas.bind("<MouseWheel>", on_mouse_wheel)  # Windows
            canvas.bind("<Button-4>", on_mouse_wheel)    # Linux scroll up
            canvas.bind("<Button-5>", on_mouse_wheel)    # Linux scroll down
            
            # Keyboard shortcuts
            def on_key_press(event):
                if event.char == '+' or event.char == '=':
                    self.zoom_graph(graph_window, 1.2)
                elif event.char == '-' or event.char == '_':
                    self.zoom_graph(graph_window, 0.8)
                elif event.char.lower() == 'r':
                    self.zoom_graph(graph_window, 'reset')
                elif event.char.lower() == 'f':
                    self.zoom_graph(graph_window, 'fit')
            
            graph_window.bind('<Key>', on_key_press)
            
            # Pan with middle mouse button or ctrl+drag
            canvas.scan_mark_x = 0
            canvas.scan_mark_y = 0
            
            def on_mouse_press(event):
                canvas.scan_mark_x = event.x
                canvas.scan_mark_y = event.y
            
            def on_mouse_drag(event):
                canvas.scan_dragto(event.x, event.y, gain=1)
            
            canvas.bind("<ButtonPress-2>", on_mouse_press)    # Middle mouse
            canvas.bind("<B2-Motion>", on_mouse_drag)
            canvas.bind("<Control-ButtonPress-1>", on_mouse_press)  # Ctrl+Left
            canvas.bind("<Control-B1-Motion>", on_mouse_drag)
            
            # Add legend
            legend_text = (
                "🎮 Controls: Use Zoom In/Out buttons or Mouse Wheel to zoom\n\n"
                "Legend:\n"
                "🟢 Green = Start Word  |  🟡 Yellow = Target Word\n"
                "━ Blue Solid = Your Path  |  ┄ Red Dashed = Alternative Paths"
            )
            ttk.Label(graph_window, text=legend_text, style='Info.TLabel', 
                     justify=tk.LEFT).pack(pady=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not display graph: {e}")
            graph_window.destroy()
    
    def zoom_graph(self, window, scale):
        """Helper function to zoom the graph"""
        if hasattr(window, 'update_image'):
            if scale == 'reset':
                window.update_image(1.0)
            elif scale == 'fit':
                window.update_image('fit')
            else:
                new_scale = window.zoom_level * scale
                new_scale = max(0.1, min(new_scale, 10.0))  # Limit zoom range
                window.update_image(new_scale)

def main():
    root = tk.Tk()
    app = WordLadderUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()