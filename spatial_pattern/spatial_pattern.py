#!/usr/bin/env python3

import time
import curses
import random
import json
import os
import sys

# Get the directory where the script is located (spatial_pattern folder)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add parent directory to path so we can import from save_load
parent_dir = os.path.dirname(SCRIPT_DIR)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import utilities for file handling
from save_load import load_json_file, save_json_file

# Import color utilities
from utils.colors import (
    setup_colors,
    apply_game_background,
    apply_nongame_background,
    apply_input_background,
    add_colored_text,
    success_style,
    info_style,
    warning_style,
    error_style,
    standard_style,
    title_style,
    dim_style,
    countdown_style,
    instruction_style,
    digit_style
)

# Import countdown utilities
from utils.countdown import present_challenge

# Change working directory to script directory
os.chdir(SCRIPT_DIR)

# Constants
SETTINGS_FILE = os.path.join(parent_dir, "utils/settings.json")
PROGRESS_FILE = os.path.join(SCRIPT_DIR, "spatial_pattern.json")
HISTORY_FILE = os.path.join(SCRIPT_DIR, "spatial_pattern_history.json")

# Global variable to store the current pattern
current_pattern = []
current_highlights = {}
current_config = {}

# Grid cell representations
EMPTY_CELL = "  "
CURSOR_CELL = "><"
SELECTED_CELL = "▒▒"

# Different highlight patterns
HIGHLIGHT_PATTERNS = [
    "██",  # Solid fill
    "▓▓",  # Dense shade
    "▒▒",  # Medium shade
    "░░",  # Light shade
    "◼◼",  # Black square
    "◆◆",  # Diamond
    "●●",  # Circle
    "★★"   # Star
]

def play_spatial_pattern(stdscr, level):
    """
    Full implementation of Spatial Pattern task with progressive difficulty based on level
    Uses parameters from the JSON configuration file
    """
    global current_pattern, current_highlights, current_config
    
    # Set background for the game screen
    apply_game_background(stdscr)
    
    # Setup colors
    setup_colors()
    
    # Get terminal dimensions
    height, width = stdscr.getmaxyx()
    
    # Load challenge configuration
    challenge_config = load_challenge_config(level)
    current_config = challenge_config.copy()  # Store for correct answer display
    
    # Generate the pattern
    pattern, highlights = generate_pattern(challenge_config)
    current_pattern = pattern.copy()  # Store for correct answer display
    current_highlights = highlights.copy()  # Store the highlight styles
    
    # Debug output if WM_DEBUG is set
    if os.environ.get("WM_DEBUG"):
        print(f"Generated pattern: {pattern}")
        print(f"Highlights: {highlights}")
    
    # Present the pattern
    present_pattern(stdscr, pattern, highlights, challenge_config)
    
    # If interference is enabled, show interference task
    if challenge_config.get('interference', False):
        show_interference_task(stdscr, challenge_config)
    
    # Get user response
    success, response_time, user_answer = get_user_response(stdscr, pattern, challenge_config, height, width)
    
    # Debug output if WM_DEBUG is set
    if os.environ.get("WM_DEBUG"):
        print(f"User answer: {user_answer}, Expected: {pattern}, Success: {success}")
    
    # Generate next challenge configuration and update JSON
    next_challenge_config = generate_next_challenge_config(level)
    update_next_challenge(next_challenge_config)
    
    # Return results
    return success, response_time, user_answer

def load_settings():
    """Load settings from JSON file"""
    default_settings = {
        "user_settings": {
            "challenges_per_session": 10,
            "current_user": "default"
        },
        "game_meta_parameters": {
            "spatial_pattern": {
                "grid_size_base": 3,
                "grid_size_increase_every_n_levels": 2,
                "max_grid_size": 7,
                "min_cells_level_1": 3,
                "max_additional_cells_per_level": 2,
                "display_time_base": 1.5,
                "display_time_reduction_per_level": 0.1,
                "multiple_highlights_intro_level": 5,
                "interference_intro_level": 7
            }
        }
    }
    return load_json_file(SETTINGS_FILE, default_settings)

def load_progress():
    """Load progress from JSON file"""
    default_progress = {
        "level": 1,
        "upgrade": 0,
        "highest_level_reached": 1,
        "total_challenges": 0,
        "successful_challenges": 0,
        "current_streak": 0,
        "longest_streak": 0,
        "avg_response_time": 0,
        "next_challenge": {
            "grid_size": 3,
            "pattern_size": 3,
            "display_time": 1.5,
            "interference": False,
            "use_multiple_highlights": False,
            "instruction": "Remember the pattern of highlighted cells"
        },
        "current_pattern": [],
        "current_highlights": {}
    }
    return load_json_file(PROGRESS_FILE, default_progress)

def load_history():
    """Load history from JSON file"""
    return load_json_file(HISTORY_FILE, [])

def load_challenge_config(level):
    """Load the challenge configuration based on level"""
    progress = load_progress()
    
    # Check if next_challenge exists and is valid
    if 'next_challenge' in progress and progress['next_challenge']:
        # Store the current pattern if it exists
        if 'current_pattern' in progress:
            global current_pattern, current_highlights
            current_pattern = progress.get('current_pattern', [])
            
            # Convert string keys back to tuples for current_highlights
            highlights_dict = progress.get('current_highlights', {})
            current_highlights = {}
            for key, value in highlights_dict.items():
                if key.startswith('(') and key.endswith(')'):
                    # Parse tuple from string like "(0, 1)"
                    coords = key.strip('()').split(',')
                    tuple_key = (int(coords[0]), int(coords[1]))
                    current_highlights[tuple_key] = value
                else:
                    current_highlights[key] = value
            
            if os.environ.get("WM_DEBUG"):
                print(f"Loaded current pattern from progress file: {current_pattern}")
                print(f"Loaded highlights from progress file: {current_highlights}")
        
        return progress['next_challenge']
    
    # If no valid configuration, generate a new one
    return generate_next_challenge_config(level)

def update_next_challenge(next_config):
    """Update the next challenge configuration in the progress file"""
    global current_pattern, current_highlights
    progress = load_progress()
    progress['next_challenge'] = next_config
    progress['current_pattern'] = current_pattern
    
    # Convert highlights dict to a serializable format
    serializable_highlights = {}
    for pos, highlight in current_highlights.items():
        serializable_highlights[str(pos)] = highlight
    
    progress['current_highlights'] = serializable_highlights
    save_json_file(PROGRESS_FILE, progress)
    
    # Debug output if WM_DEBUG is set
    if os.environ.get("WM_DEBUG"):
        print(f"Updated progress file with new challenge config and pattern: {current_pattern}")
        print(f"Updated highlights: {serializable_highlights}")

def generate_next_challenge_config(level):
    """Generate the configuration for the next challenge based on meta-parameters"""
    settings = load_settings()
    
    # Get meta-parameters for spatial pattern
    try:
        meta = settings["game_meta_parameters"]["spatial_pattern"]
    except KeyError:
        # Default meta-parameters if not found
        meta = {
            "grid_size_base": 3,
            "grid_size_increase_every_n_levels": 2,
            "max_grid_size": 7,
            "min_cells_level_1": 3,
            "max_additional_cells_per_level": 2,
            "display_time_base": 1.5,
            "display_time_reduction_per_level": 0.1,
            "multiple_highlights_intro_level": 5,
            "interference_intro_level": 7
        }
    
    # Initialize new challenge config
    config = {
        "grid_size": 0,
        "pattern_size": 0,
        "display_time": 0,
        "interference": False,
        "use_multiple_highlights": False,
        "instruction": ""
    }
    
    # Calculate grid size - increase by 1 every N levels
    grid_size_increase_every_n = meta.get("grid_size_increase_every_n_levels", 2)
    grid_size_increase = min((level - 1) // grid_size_increase_every_n, 
                             meta["max_grid_size"] - meta["grid_size_base"])
    config["grid_size"] = meta["grid_size_base"] + grid_size_increase
    
    # Calculate pattern size (number of cells to remember)
    min_cells = meta["min_cells_level_1"] + (level - 1) * meta["max_additional_cells_per_level"]
    max_cells = min(min_cells + meta["max_additional_cells_per_level"], 
                   (config["grid_size"] * config["grid_size"]) - 1)
    config["pattern_size"] = random.randint(min_cells, max_cells)
    
    # Calculate display time
    config["display_time"] = max(0.5, meta["display_time_base"] - 
                                (level - 1) * meta["display_time_reduction_per_level"])
    
    # Determine if interference is needed (add at higher levels)
    interference_level = meta.get("interference_intro_level", 7)
    if level >= interference_level:
        config["interference"] = random.choice([True, False])  # 50% chance once introduced
    
    # Determine if multiple highlights should be used
    multiple_highlights_level = meta.get("multiple_highlights_intro_level", 5)
    if level >= multiple_highlights_level:
        config["use_multiple_highlights"] = random.choice([True, False])  # 50% chance once introduced
    
    # Set instruction based on configuration
    config["instruction"] = get_instruction_text(config)
    
    # For debugging or logging
    if os.environ.get("WM_DEBUG"):
        print(f"Generated config for level {level}:")
        print(f"  Grid size: {config['grid_size']}x{config['grid_size']}")
        print(f"  Pattern size: {config['pattern_size']}")
        print(f"  Display time: {config['display_time']}s")
        print(f"  Interference: {config['interference']}")
        print(f"  Multiple highlights: {config['use_multiple_highlights']}")
    
    return config

def get_instruction_text(config):
    """Generate instruction text based on the challenge configuration"""
    if config.get("interference", False):
        return "Remember the pattern - You'll solve a math problem before recalling"
    elif config.get("use_multiple_highlights", False):
        return f"Remember the pattern with {config['pattern_size']} cells AND their highlight style"
    else:
        return f"Remember the pattern with {config['pattern_size']} highlighted cells"

def generate_pattern(config):
    """Generate a random pattern of cells based on configuration"""
    grid_size = config["grid_size"]
    pattern_size = config["pattern_size"]
    
    # Generate all possible grid positions
    all_positions = [(row, col) for row in range(grid_size) for col in range(grid_size)]
    
    # Randomly select positions for the pattern
    pattern = random.sample(all_positions, pattern_size)
    
    # Sort the pattern for consistent representation
    pattern.sort()
    
    # For higher levels, assign different highlight styles to cells
    highlights = {}
    if config.get('use_multiple_highlights', False):
        # Decide how many different highlights to use (between 2-3)
        num_highlight_types = min(3, len(HIGHLIGHT_PATTERNS))
        highlight_types = random.sample(HIGHLIGHT_PATTERNS, num_highlight_types)
        
        for pos in pattern:
            # Convert to tuple for dictionary key
            position = tuple(pos) if isinstance(pos, list) else pos
            highlights[position] = random.choice(highlight_types)
    else:
        # Use default highlight for all cells
        for pos in pattern:
            # Convert to tuple for dictionary key
            position = tuple(pos) if isinstance(pos, list) else pos
            highlights[position] = HIGHLIGHT_PATTERNS[0]
    
    return pattern, highlights

def show_pattern_content(stdscr, config):
    """Callback function to display the pattern itself"""
    global current_pattern, current_highlights
    
    # Get terminal dimensions
    height, width = stdscr.getmaxyx()
    
    # Clear screen for the pattern
    stdscr.clear()
    
    # Display the grid with the pattern
    draw_grid(stdscr, config["grid_size"], current_pattern, current_highlights, [], height, width)
    stdscr.refresh()
    time.sleep(config["display_time"])
    
    # Clear screen after showing pattern
    stdscr.clear()
    stdscr.refresh()

def present_pattern(stdscr, pattern, highlights, config):
    """Present the spatial pattern to the user"""
    present_challenge(
        stdscr=stdscr,
        config=config,
        challenge_callback=show_pattern_content
    )

def draw_grid(stdscr, grid_size, pattern, highlights, selected_cells, height, width, cursor_pos=None):
    """
    Draw the grid with highlighted and selected cells
    
    Args:
        stdscr: The curses window
        grid_size: Size of the grid (e.g., 3 for 3x3)
        pattern: List of (row, col) tuples for cells in the pattern
        highlights: Dictionary mapping (row, col) positions to highlight patterns
        selected_cells: List of (row, col) tuples for cells the user has selected
        height: Screen height
        width: Screen width
        cursor_pos: (row, col) tuple for cursor position during selection phase
    """
    # Calculate center of screen
    center_y = height // 2
    center_x = width // 2
    
    # Calculate grid dimensions
    cell_width = 4  # Width of each cell in characters
    cell_height = 2  # Height of each cell in lines
    
    # Calculate grid offset
    grid_width = grid_size * cell_width
    grid_height = grid_size * cell_height
    start_y = center_y - (grid_height // 2)
    start_x = center_x - (grid_width // 2)
    
    # Draw grid background and border
    for row in range(grid_size):
        for col in range(grid_size):
            # Calculate cell position
            cell_y = start_y + (row * cell_height)
            cell_x = start_x + (col * cell_width)
            
            # Determine cell content
            pos = (row, col)
            is_highlighted = pos in pattern
            is_selected = pos in selected_cells
            is_cursor = cursor_pos and cursor_pos == pos
            
            # Set cell style based on state
            if is_highlighted:
                cell_style = digit_style()
                # Get the specific highlight pattern for this cell
                cell_content = highlights.get(pos, HIGHLIGHT_PATTERNS[0])
            elif is_selected:
                cell_style = warning_style()
                cell_content = SELECTED_CELL
            elif is_cursor:
                cell_style = standard_style() | curses.A_REVERSE
                cell_content = CURSOR_CELL
            else:
                cell_style = standard_style()
                cell_content = EMPTY_CELL
            
            # Draw cell
            stdscr.addstr(cell_y, cell_x, cell_content, cell_style)
    
    # Draw grid lines
    for i in range(grid_size + 1):
        # Horizontal lines
        h_y = start_y + (i * cell_height)
        if h_y < height:
            h_line = "+" + "---+" * grid_size
            stdscr.addstr(h_y - 1, start_x - 1, h_line, standard_style())
        
        # Vertical lines
        v_x = start_x + (i * cell_width) - 1
        if v_x < width:
            for j in range(grid_size):
                v_y = start_y + (j * cell_height)
                if v_y < height:
                    stdscr.addstr(v_y, v_x, "|", standard_style())
                    stdscr.addstr(v_y + 1, v_x, "|", standard_style())
    
    return start_y, start_x, grid_height, grid_width

def show_interference_task(stdscr, config):
    """Show a simple math interference task"""
    height, width = stdscr.getmaxyx()
    
    # Generate a simple math problem
    num1 = random.randint(1, 20)
    num2 = random.randint(1, 20)
    operation = random.choice(['+', '-'])
    
    if operation == '+':
        problem = f"{num1} + {num2} = ?"
        answer = num1 + num2
    else:
        # Ensure positive result for subtraction
        if num1 < num2:
            num1, num2 = num2, num1
        problem = f"{num1} - {num2} = ?"
        answer = num1 - num2
    
    # Display the problem
    stdscr.clear()
    add_colored_text(stdscr, height//2 - 2, width//2 - len("SOLVE THIS PROBLEM")//2, 
                    "SOLVE THIS PROBLEM", instruction_style())
    add_colored_text(stdscr, height//2, width//2 - len(problem)//2, 
                    problem, digit_style())
    
    # Create input window for answer
    input_row = height//2 + 2
    prompt = "Your answer: "
    add_colored_text(stdscr, input_row, width//2 - len(prompt)//2 - 5, prompt, standard_style())
    
    input_win = curses.newwin(1, 10, input_row, width//2 - len(prompt)//2 + len(prompt) - 5)
    apply_input_background(input_win)
    input_win.keypad(True)  # Enable special keys
    
    stdscr.refresh()
    input_win.refresh()
    
    # Get user's answer to math problem
    curses.echo()
    try:
        curses.curs_set(1)  # Show cursor
        user_math = input_win.getstr(0, 0, 5).decode('utf-8')
        curses.noecho()
        curses.curs_set(0)  # Hide cursor
    except:
        user_math = ""
        curses.noecho()
        curses.curs_set(0)  # Hide cursor
    
    # Check if correct (not critical, just for engagement)
    try:
        user_answer_val = int(user_math)
        correct = (user_answer_val == answer)
    except:
        correct = False
    
    # Show brief feedback
    stdscr.clear()
    if correct:
        add_colored_text(stdscr, height//2, width//2 - len("Correct!")//2, 
                        "Correct!", success_style())
    else:
        feedback = f"The answer was {answer}"
        add_colored_text(stdscr, height//2, width//2 - len(feedback)//2, 
                        feedback, warning_style())
    
    stdscr.refresh()
    time.sleep(1.0)
    
    # Clear screen
    stdscr.clear()
    stdscr.refresh()

def get_user_response(stdscr, pattern, config, height, width):
    """Get the user's response by letting them select cells on the grid"""
    grid_size = config["grid_size"]
    
    # Clear screen and ensure game background is applied
    apply_game_background(stdscr)
    stdscr.clear()
    
    # Show instructions
    add_colored_text(stdscr, 2, 2, "Reproduce the pattern you just saw", title_style())
    add_colored_text(stdscr, 3, 2, "Use arrow keys or hjkl (vim) to move, Space to select/deselect, Enter to submit", standard_style())
    
    # Draw a note about navigation
    add_colored_text(stdscr, height-1, 2, "Press Ctrl-C to exit or M to return to main menu", dim_style())
    
    # Initialize cursor position and selected cells
    cursor_pos = (0, 0)  # Start at top-left
    selected_cells = []
    
    # Start timing
    start_time = time.time()
    
    # Input loop
    curses.curs_set(0)  # Hide cursor
    stdscr.keypad(True)  # Enable special keys
    
    while True:
        # Draw the grid
        grid_start_y, grid_start_x, grid_height, grid_width = draw_grid(
            stdscr, grid_size, [], {}, selected_cells, height, width, cursor_pos
        )
        
        # Show selected count
        status_text = f"Selected: {len(selected_cells)}/{config['pattern_size']}"
        add_colored_text(stdscr, grid_start_y + grid_height + 2, width//2 - len(status_text)//2,
                        status_text, info_style())
        
        stdscr.refresh()
        
        # Get user input
        try:
            key = stdscr.getch()
            
            if key == 3:  # Ctrl-C
                os.environ["WM_EXIT"] = "1"  # Set exit flag
                return False, 0, []
            elif key in [ord('m'), ord('M')]:  # Return to main menu
                return False, 0, []
            elif key in [ord('s'), ord('S'), curses.KEY_ENTER, 10, 13]:  # Submit answer
                # Calculate response time
                response_time = time.time() - start_time
                
                # Check if answer is correct - just care about positions, not highlight styles
                success = sorted(selected_cells) == sorted(pattern)
                
                return success, response_time, selected_cells
            elif key == ord(' '):  # Toggle cell selection
                if cursor_pos in selected_cells:
                    selected_cells.remove(cursor_pos)
                else:
                    # Only add if not already at maximum
                    if len(selected_cells) < config['pattern_size']:
                        selected_cells.append(cursor_pos)
            # Support both arrow keys and vim navigation (hjkl)
            elif key in [ord('k'), curses.KEY_UP] and cursor_pos[0] > 0:
                cursor_pos = (cursor_pos[0] - 1, cursor_pos[1])
            elif key in [ord('j'), curses.KEY_DOWN] and cursor_pos[0] < grid_size - 1:
                cursor_pos = (cursor_pos[0] + 1, cursor_pos[1])
            elif key in [ord('h'), curses.KEY_LEFT] and cursor_pos[1] > 0:
                cursor_pos = (cursor_pos[0], cursor_pos[1] - 1)
            elif key in [ord('l'), curses.KEY_RIGHT] and cursor_pos[1] < grid_size - 1:
                cursor_pos = (cursor_pos[0], cursor_pos[1] + 1)
        except KeyboardInterrupt:
            os.environ["WM_EXIT"] = "1"  # Set exit flag
            return False, 0, []

def get_next_challenge_info():
    """Get information about the next challenge for display on results screen"""
    try:
        # Load progress file
        progress = load_progress()
        next_challenge = progress.get('next_challenge', {})
        
        if not next_challenge:
            return ["No information available for next challenge"]
        
        info_lines = []
        
        # Basic challenge info
        info_lines.append(f"Grid size: {next_challenge['grid_size']}x{next_challenge['grid_size']}")
        info_lines.append(f"Cells to remember: {next_challenge['pattern_size']}")
        info_lines.append(f"Display time: {next_challenge['display_time']:.1f} seconds")
        
        # Special task info
        if next_challenge.get('use_multiple_highlights'):
            info_lines.append("Cells will have different highlight patterns")
        
        if next_challenge.get('interference'):
            info_lines.append("You'll solve a math problem before recalling")
        
        return info_lines
    except Exception as e:
        if os.environ.get("WM_DEBUG"):
            print(f"Error getting next challenge info: {str(e)}")
        return [f"Error getting next challenge info: {str(e)}"]

def get_correct_answer():
    """Return a string representation of the correct pattern"""
    global current_pattern
    
    if not current_pattern:
        return "Not available"
    
    try:
        # Format the pattern as a string
        return ", ".join([f"({r},{c})" for r, c in current_pattern])
    except Exception as e:
        if os.environ.get("WM_DEBUG"):
            print(f"Error getting correct answer: {str(e)}")
        return f"Error: {str(e)}"

def display_challenge_explanation(stdscr, level, first_in_session=False):
    """Display explanation screen for the first challenge in a session"""
    if not first_in_session:
        return True
        
    # Set background to very dark gray
    apply_nongame_background(stdscr)
    
    # Set up colors
    setup_colors()
    
    # Get terminal dimensions
    height, width = stdscr.getmaxyx()
    
    # Clear screen
    stdscr.clear()
    
    # Try to get the challenge config
    try:
        challenge_config = load_challenge_config(level)
    except:
        challenge_config = generate_next_challenge_config(level)
    
    # Title
    add_colored_text(stdscr, 2, 2, "SPATIAL PATTERN RECALL", title_style())
    add_colored_text(stdscr, 3, 2, "Test and improve your visual-spatial working memory", info_style())
    
    # Description
    description = [
        "",
        "In this task, you will:",
        f"- See a {challenge_config['grid_size']}x{challenge_config['grid_size']} grid with {challenge_config['pattern_size']} highlighted cells",
        f"- The pattern will appear for {challenge_config['display_time']:.1f} seconds",
        "- Try to remember the pattern and reproduce it exactly",
        "",
        "How to play:",
        "- Use ARROW KEYS or HJKL (vim-style) to navigate the grid",
        "- SPACE to select/deselect a cell",
        "- ENTER to submit your answer",
        ""
    ]
    
    # Add special instructions based on configuration
    if challenge_config.get('use_multiple_highlights'):
        description.append("Some cells may have different highlight patterns to remember.")
    
    if challenge_config.get('interference'):
        description.append("You'll solve a simple math problem before recalling the pattern.")
    
    # Explain difficulty progression
    difficulty_explanation = [
        "",
        "Difficulty progression:",
        f"- Grid size increases every {challenge_config.get('grid_size_increase_every_n_levels', 2)} levels",
        "- Number of cells to remember increases with each level",
        "- Display time decreases with each level",
        "- At higher levels, interference tasks and different highlight styles are introduced"
    ]
    
    # Strategy tips based on level
    if level <= 3:
        tips = [
            "",
            "Beginner Tips:",
            "- Try to see shapes or patterns in the highlighted cells",
            "- Count the number of cells in each row and column",
            "- Visualize the overall arrangement"
        ]
    elif level <= 6:
        tips = [
            "",
            "Intermediate Tips:",
            "- Look for symmetry or asymmetry in the pattern",
            "- Group cells into meaningful clusters",
            "- Mentally trace a path through the highlighted cells"
        ]
    else:
        tips = [
            "",
            "Advanced Tips:",
            "- Use relative positioning (e.g., 'one in each corner except top-right')",
            "- Remember the negative space (non-highlighted areas)",
            "- For multiple highlights, associate each pattern with a verbal label"
        ]
    
    # Display description and tips
    line = 5
    for text in description:
        add_colored_text(stdscr, line, 4, text, standard_style())
        line += 1
    
    for text in difficulty_explanation:
        add_colored_text(stdscr, line, 4, text, info_style())
        line += 1
    
    for text in tips:
        add_colored_text(stdscr, line, 4, text, warning_style())
        line += 1
    
    # Ready instruction
    add_colored_text(stdscr, line + 2, width//2 - 35, "Press ENTER to begin or M to return to main menu or Q to quit...", title_style())
    
    # Draw a note about keyboard shortcuts
    add_colored_text(stdscr, height-1, 2, "Press Ctrl-C to exit or M to return to main menu or Q to quit", dim_style())
    
    stdscr.refresh()
    
    # Wait for key press with specific handling for M and Q
    while True:
        try:
            key = stdscr.getch()
            if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key - start game
                return True
            elif key in [ord('m'), ord('M')]:  # Return to main menu
                return False
            elif key in [ord('q'), ord('Q')] or key == 3:  # Quit or Ctrl-C
                # Set the global exit flag
                os.environ["WM_EXIT"] = "1"
                return False
        except KeyboardInterrupt:
            os.environ["WM_EXIT"] = "1"
            return False

# Export functions for the wrapper to use
get_next_challenge_info_for_wrapper = get_next_challenge_info
get_correct_answer_for_wrapper = get_correct_answer
display_challenge_explanation_for_wrapper = display_challenge_explanation
