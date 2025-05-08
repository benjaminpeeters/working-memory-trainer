#!/usr/bin/env python3

import curses
import os
import signal
import sys
from typing import Dict, List, Any, Optional

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Change working directory to script directory to ensure all relative paths are correct
os.chdir(SCRIPT_DIR)

# Import our modules
from save_load import (
    load_settings,
    create_config_for_compatibility,
    initialize_all_files
)
from main_menu import (
    display_menu,
    settings_menu,
    get_game_for_session,
    show_invalid_choice
)
from progress import show_progress
from game_session import start_game_session


# Constants for games
GAMES = {
    "digit_span": "Digit Span Task - Remember and recall sequences of numbers",
    "n_back": "N-Back Challenge - Identify when the current item matches one from N steps earlier",
    "spatial_pattern": "Spatial Pattern Recall - Memorize and reproduce grid patterns",
    "shopping_list": "Shopping List Challenge - Remember increasing lists of items",
    "mental_math": "Mental Math Workout - Perform calculations while holding information in memory",
    "story_details": "Story Details Recall - Read passages and recall specific details"
}

# Game categories
STRATEGY_1_GAMES = ["digit_span", "n_back", "spatial_pattern"]
STRATEGY_2_GAMES = ["shopping_list", "mental_math", "story_details"]
ALL_GAMES = STRATEGY_1_GAMES + STRATEGY_2_GAMES

# Game functions mapping - import only when needed to reduce startup errors
GAME_FUNCTIONS = {}

# Global variables for program state - use a list to make it mutable for passing to game_session
exiting = [False]

def load_game_functions():
    """Dynamically load game functions to prevent import errors on startup"""
    # Import and initialize colors module
    try:
        from utils.colors import setup_colors
        # Set up colors early
        setup_colors()
        if os.environ.get("WM_DEBUG"):
            print("Successfully initialized colors module")
    except ImportError:
        print("Warning: colors module not found")
    
    try:
        from digit_span.digit_span import play_digit_span
        if os.environ.get("WM_DEBUG"):
            print("Successfully imported play_digit_span")
        GAME_FUNCTIONS["digit_span"] = play_digit_span
    except ImportError:
        print("Warning: digit_span module not found")
    
    try:
        from n_back.n_back import play_n_back
        GAME_FUNCTIONS["n_back"] = play_n_back
    except ImportError:
        print("Warning: n_back module not found")
    
    try:
        from spatial_pattern.spatial_pattern import play_spatial_pattern
        GAME_FUNCTIONS["spatial_pattern"] = play_spatial_pattern
    except ImportError:
        print("Warning: spatial_pattern module not found")
    
    try:
        from shopping_list.shopping_list import play_shopping_list
        GAME_FUNCTIONS["shopping_list"] = play_shopping_list
    except ImportError:
        print("Warning: shopping_list module not found")
    
    try:
        from mental_math.mental_math import play_mental_math
        GAME_FUNCTIONS["mental_math"] = play_mental_math
    except ImportError:
        print("Warning: mental_math module not found")
    
    try:
        from story_details.story_details import play_story_details
        GAME_FUNCTIONS["story_details"] = play_story_details
    except ImportError:
        print("Warning: story_details module not found")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global exiting
    exiting[0] = True
    # Try to restore terminal state
    try:
        curses.endwin()
    except:
        pass
    print("Program terminated by user.")
    sys.exit(0)

def main(stdscr):
    """Main function for the working memory training suite"""
    global exiting
    
    # Clear any exit flags from environment
    if "WM_EXIT" in os.environ:
        os.environ.pop("WM_EXIT")
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize curses settings
    curses.curs_set(0)  # Hide cursor
    stdscr.keypad(True)  # Enable special keys
    
    # Load game functions dynamically to prevent import errors
    load_game_functions()
    
    # Load settings
    settings = load_settings()
    
    # Main application loop
    while not exiting[0]:
        # Check for exit request via environment variable
        if os.environ.get("WM_EXIT") == "1":
            os.environ.pop("WM_EXIT")  # Clear the flag
            exiting[0] = True
            break
            
        # Display main menu and get choice
        choice_type, choice_value = display_menu(
            stdscr, settings, GAMES, ALL_GAMES, STRATEGY_1_GAMES, STRATEGY_2_GAMES, exiting
        )
        
        # Handle exit request
        if exiting[0]:
            break
        
        # Process choice
        if choice_type == "quit":
            break
        elif choice_type == "settings":
            settings_menu(stdscr, exiting)
        elif choice_type == "progress":
            show_progress(stdscr, GAMES, exiting, settings)
        elif choice_type == "game" or choice_type == "random":
            # Get list of games for this session
            games_queue = get_game_for_session(
                choice_type, choice_value, ALL_GAMES, STRATEGY_1_GAMES, STRATEGY_2_GAMES
            )
            # Start game session
            start_game_session(
                stdscr, settings, games_queue, exiting,
                GAME_FUNCTIONS, ALL_GAMES, STRATEGY_1_GAMES, STRATEGY_2_GAMES
            )
        else:
            show_invalid_choice(stdscr)
        
        # Check for exit again
        if exiting[0] or os.environ.get("WM_EXIT") == "1":
            if os.environ.get("WM_EXIT") == "1":
                os.environ.pop("WM_EXIT")
            break
    
    # Clean exit - restore terminal
    curses.endwin()
    print("Thank you for using the Working Memory Training Suite!")

if __name__ == "__main__":
    # Override SIGINT handler before curses initializes
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Initialize curses
        curses.wrapper(main)
    except KeyboardInterrupt:
        # Catch keyboard interrupt that might happen during startup
        try:
            curses.endwin()
        except:
            pass
        print("Program terminated by user.")
    except Exception as e:
        # Handle other exceptions and clean up terminal
        try:
            curses.endwin()
        except:
            pass
        print(f"An error occurred: {e}")
