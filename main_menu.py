#!/usr/bin/env python3

import curses
import time
import random
from typing import Dict, List, Tuple, Any, Optional
import os
import sys

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add parent directory to path
parent_dir = os.path.dirname(SCRIPT_DIR)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import utilities
from save_load import load_settings, save_settings, get_game_progress_overview
from utils.colors import (
    setup_colors, 
    apply_nongame_background, 
    apply_input_background,
    add_colored_text, 
    success_style, 
    info_style, 
    warning_style, 
    error_style,
    standard_style, 
    title_style, 
    dim_style
)

def setup_menu_colors():
    """Set up color pairs for the menu screens"""
    # Initialize all colors
    setup_colors()

def display_menu(stdscr: Any, settings: Dict, games: Dict[str, str], 
                 all_games: List[str], strategy_1_games: List[str], 
                 strategy_2_games: List[str], exiting: List[bool]) -> Tuple[str, Optional[str]]:
    """
    Display the main menu and handle user selection with arrow key navigation
    
    Args:
        stdscr: The curses screen object
        settings: The settings dictionary
        games: Dictionary mapping game names to descriptions
        all_games: List of all game names
        strategy_1_games: List of cognitive psychology games
        strategy_2_games: List of real-world application games
        exiting: Reference to global exiting flag
        
    Returns:
        Tuple of (choice_type, choice_value)
    """
    # Get game progress overview
    game_progress = get_game_progress_overview(all_games)
    
    # Set background to very dark gray for non-game screens
    apply_nongame_background(stdscr)
    
    curses.curs_set(0)  # Hide cursor
    stdscr.clear()
    
    # Get terminal dimensions
    height, width = stdscr.getmaxyx()
    
    # Set up colors
    setup_menu_colors()
    
    # Define menu options
    menu_options = []
    
    # Individual games
    for i, game in enumerate(all_games):
        menu_options.append(("game", game))
    
    # Random game options
    menu_options.append(("random", "strategy1"))  # Random Strategy 1 Game
    menu_options.append(("random", "strategy2"))  # Random Strategy 2 Game
    menu_options.append(("random", "all"))       # Random Game from All
    
    # Other options
    menu_options.append(("settings", None))      # Settings
    menu_options.append(("progress", None))      # View Progress
    menu_options.append(("quit", None))          # Quit
    
    # Current selected option
    current_option = 0
    
    # Menu loop
    while True:
        stdscr.clear()
        
        # Title
        add_colored_text(stdscr, 1, 2, "WORKING MEMORY TRAINING SUITE", title_style())
        add_colored_text(stdscr, 2, 2, "Improve your cognitive abilities with these challenging games", info_style())
        add_colored_text(stdscr, 4, 2, "Select a game to play:", curses.A_UNDERLINE)
        
        # Display menu options
        for i, (option_type, option_value) in enumerate(menu_options):
            y_pos = i + 5
            
            # Skip if not enough space
            if y_pos >= height - 2:
                continue
                
            # Format the option text
            if i < len(all_games):
                # Game option
                game_name = games[option_value].split(" - ")[0]
                progress = game_progress[option_value]
                option_text = f"{i+1}. {game_name}"
                
                # Highlight if selected
                if i == current_option:
                    add_colored_text(stdscr, y_pos, 2, option_text, title_style() | curses.A_REVERSE)
                else:
                    add_colored_text(stdscr, y_pos, 2, option_text, standard_style())
                
                # Always show level info
                level_info = f"[Level: {progress['level']}/10, Progress: {progress['upgrade']}/10]"
                add_colored_text(stdscr, y_pos, 35, level_info, warning_style())
                
            elif i < len(all_games) + 3:
                # Random game options
                if i == len(all_games):
                    option_text = f"{i+1}. Random Strategy 1 Game (Cognitive Psychology Tasks)"
                elif i == len(all_games) + 1:
                    option_text = f"{i+1}. Random Strategy 2 Game (Real-World Applications)"
                else:
                    option_text = f"{i+1}. Random Game from All Categories"
                
                # Highlight if selected
                if i == current_option:
                    add_colored_text(stdscr, y_pos, 2, option_text, success_style() | curses.A_REVERSE)
                else:
                    add_colored_text(stdscr, y_pos, 2, option_text, success_style())
                
            else:
                # Other options (Settings, Progress, Quit)
                if option_type == "settings":
                    option_text = "S. Settings"
                elif option_type == "progress":
                    option_text = "P. View Progress"
                elif option_type == "quit":
                    option_text = "Q. Quit"
                
                # Highlight if selected
                if i == current_option:
                    add_colored_text(stdscr, y_pos, 2, option_text, title_style() | curses.A_REVERSE)
                else:
                    add_colored_text(stdscr, y_pos, 2, option_text, title_style())
        
        # Draw a note about navigation
        add_colored_text(stdscr, height-1, 2, "Use arrow keys to navigate, Enter to select, Ctrl-C to exit", dim_style())
        
        # Refresh the screen
        stdscr.refresh()
        
        # Check for exit request
        if exiting[0]:
            return "quit", None
        
        # Get key input
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            exiting[0] = True
            return "quit", None
        
        # Process key input
        if key == curses.KEY_UP or key == ord('k'):  # Up arrow or k (vim style)
            current_option -= 1
            if current_option < 0:
                current_option = len(menu_options) - 1  # Wrap around to bottom
        elif key == curses.KEY_DOWN or key == ord('j'):  # Down arrow or j (vim style)
            current_option += 1
            if current_option >= len(menu_options):
                current_option = 0  # Wrap around to top
        elif key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key
            return menu_options[current_option]
        elif key == 3:  # Ctrl-C
            exiting[0] = True
            return "quit", None
        elif key in [ord('q'), ord('Q')]:  # Q key
            return "quit", None
        elif key in [ord('s'), ord('S')]:  # S key
            return "settings", None
        elif key in [ord('p'), ord('P')]:  # P key
            return "progress", None
        elif ord('1') <= key <= ord('9'):  # Number keys
            index = key - ord('1')
            if index < len(menu_options):
                return menu_options[index]

def settings_menu(stdscr: Any, exiting: List[bool]) -> None:
    """
    Display and handle settings menu with arrow key navigation
    
    Args:
        stdscr: The curses screen object
        exiting: Reference to global exiting flag
    """
    # Load current settings
    settings = load_settings()
    
    # Set background to very dark gray for non-game screens
    apply_nongame_background(stdscr)
    
    curses.curs_set(0)
    stdscr.clear()
    
    # Get terminal dimensions
    height, width = stdscr.getmaxyx()
    
    # Define menu options
    menu_options = [
        "challenges_per_session",
        "current_user",
        "back"
    ]
    
    # Current selected option
    current_option = 0
    
    # Menu loop
    while True:
        stdscr.clear()
        
        add_colored_text(stdscr, 1, 2, "SETTINGS", title_style())
        
        # Display menu options
        y_pos = 3
        option_text = f"1. Challenges per session: {settings['user_settings']['challenges_per_session']}"
        if current_option == 0:
            add_colored_text(stdscr, y_pos, 2, option_text, standard_style() | curses.A_REVERSE)
        else:
            add_colored_text(stdscr, y_pos, 2, option_text, standard_style())
        
        y_pos = 4
        option_text = f"2. Current user: {settings['user_settings']['current_user']}"
        if current_option == 1:
            add_colored_text(stdscr, y_pos, 2, option_text, standard_style() | curses.A_REVERSE)
        else:
            add_colored_text(stdscr, y_pos, 2, option_text, standard_style())
        
        y_pos = 6
        option_text = "B. Back to main menu"
        if current_option == 2:
            add_colored_text(stdscr, y_pos, 2, option_text, standard_style() | curses.A_REVERSE)
        else:
            add_colored_text(stdscr, y_pos, 2, option_text, standard_style())
        
        # Draw a note about navigation
        add_colored_text(stdscr, height-1, 2, "Use arrow keys to navigate, Enter to select, Ctrl-C to exit", dim_style())
        
        # Refresh the screen
        stdscr.refresh()
        
        # Check for exit request
        if exiting[0]:
            return
        
        # Get key input
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            exiting[0] = True
            return
        
        # Process key input
        if key == curses.KEY_UP or key == ord('k'):  # Up arrow or k (vim style)
            current_option -= 1
            if current_option < 0:
                current_option = len(menu_options) - 1  # Wrap around to bottom
        elif key == curses.KEY_DOWN or key == ord('j'):  # Down arrow or j (vim style)
            current_option += 1
            if current_option >= len(menu_options):
                current_option = 0  # Wrap around to top
        elif key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key
            # Process selected option
            option = menu_options[current_option]
            
            if option == "back":
                return
            elif option == "challenges_per_session":
                edit_challenges_per_session(stdscr, settings, exiting)
                if exiting[0]:
                    return
            elif option == "current_user":
                edit_current_user(stdscr, settings, exiting)
                if exiting[0]:
                    return
        elif key == 3:  # Ctrl-C
            exiting[0] = True
            return
        elif key in [ord('b'), ord('B')]:  # B key
            return
        elif key == ord('1'):  # 1 key
            edit_challenges_per_session(stdscr, settings, exiting)
            if exiting[0]:
                return
        elif key == ord('2'):  # 2 key
            edit_current_user(stdscr, settings, exiting)
            if exiting[0]:
                return

def edit_challenges_per_session(stdscr, settings, exiting):
    """Edit the number of challenges per session"""
    # Clear area for input
    add_colored_text(stdscr, 10, 2, "Enter new number of challenges per session:", standard_style())
    stdscr.refresh()
    
    # Get current value
    current_value = str(settings['user_settings']['challenges_per_session'])
    
    # Create input window
    input_win = curses.newwin(1, 5, 10, 46)
    apply_input_background(input_win)
    
    # Set up the input window
    input_win.keypad(True)  # Enable special keys in the input window
    
    # Show cursor and display current value
    curses.curs_set(1)  # Show cursor
    input_str = current_value
    input_win.addstr(0, 0, input_str)
    input_win.move(0, len(input_str))  # Position cursor at end of input
    input_win.refresh()
    
    # Edit loop - get input from the input window, not stdscr
    while True:
        try:
            key = input_win.getch()  # Get input from input_win, not stdscr
            
            if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key
                if input_str:
                    try:
                        new_value = int(input_str)
                        if new_value > 0:
                            settings['user_settings']['challenges_per_session'] = new_value
                            save_settings(settings)
                            curses.curs_set(0)  # Hide cursor
                            add_colored_text(stdscr, 12, 2, "Setting updated successfully!", title_style())
                            stdscr.refresh()
                            time.sleep(1.5)
                            return
                        else:
                            add_colored_text(stdscr, 12, 2, "Value must be positive!", error_style())
                            stdscr.refresh()
                            time.sleep(1.5)
                            # Restore focus to input window after showing error
                            input_win.move(0, len(input_str))
                            input_win.refresh()
                    except ValueError:
                        add_colored_text(stdscr, 12, 2, "Invalid input!", error_style())
                        stdscr.refresh()
                        time.sleep(1.5)
                        # Restore focus to input window after showing error
                        input_win.move(0, len(input_str))
                        input_win.refresh()
            elif key == 27:  # Escape
                curses.curs_set(0)  # Hide cursor
                return
            elif key == 3:  # Ctrl-C
                exiting[0] = True
                curses.curs_set(0)  # Hide cursor
                return
            elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:  # Backspace
                if input_str:
                    input_str = input_str[:-1]
            elif ord('0') <= key <= ord('9'):  # Numbers only
                if len(input_str) < 3:  # Limit length
                    input_str += chr(key)
                    
            # Redraw input
            input_win.clear()
            input_win.addstr(0, 0, input_str)
            input_win.move(0, len(input_str))  # Position cursor at end of input
            input_win.refresh()
            
        except KeyboardInterrupt:
            exiting[0] = True
            curses.curs_set(0)  # Hide cursor
            return

def edit_current_user(stdscr, settings, exiting):
    """Edit the current username"""
    # Clear area for input
    add_colored_text(stdscr, 10, 2, "Enter new username:", standard_style())
    stdscr.refresh()
    
    # Get current value
    current_value = settings['user_settings']['current_user']
    
    # Create input window
    input_win = curses.newwin(1, 30, 10, 22)
    apply_input_background(input_win)
    
    # Set up the input window
    input_win.keypad(True)  # Enable special keys in the input window
    
    # Show cursor and display current value
    curses.curs_set(1)  # Show cursor
    input_str = current_value
    input_win.addstr(0, 0, input_str)
    input_win.move(0, len(input_str))  # Position cursor at end of input
    input_win.refresh()
    
    # Edit loop - get input from the input window, not stdscr
    while True:
        try:
            key = input_win.getch()  # Get input from input_win, not stdscr
            
            if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key
                if input_str:
                    settings['user_settings']['current_user'] = input_str
                    save_settings(settings)
                    curses.curs_set(0)  # Hide cursor
                    add_colored_text(stdscr, 12, 2, "Username updated successfully!", title_style())
                    stdscr.refresh()
                    time.sleep(1.5)
                    return
            elif key == 27:  # Escape
                curses.curs_set(0)  # Hide cursor
                return
            elif key == 3:  # Ctrl-C
                exiting[0] = True
                curses.curs_set(0)  # Hide cursor
                return
            elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:  # Backspace
                if input_str:
                    input_str = input_str[:-1]
            elif 32 <= key <= 126:  # Printable ASCII characters
                if len(input_str) < 28:  # Limit length
                    input_str += chr(key)
                    
            # Redraw input
            input_win.clear()
            input_win.addstr(0, 0, input_str)
            input_win.move(0, len(input_str))  # Position cursor at end of input
            input_win.refresh()
            
        except KeyboardInterrupt:
            exiting[0] = True
            curses.curs_set(0)  # Hide cursor
            return

def get_game_for_session(choice_type: str, choice_value: str, 
                         all_games: List[str], 
                         strategy_1_games: List[str], 
                         strategy_2_games: List[str]) -> List[str]:
    """
    Determine which game(s) to play based on menu selection
    
    Args:
        choice_type: Type of choice made ("game" or "random")
        choice_value: Value of choice made (game name or category)
        all_games: List of all game names
        strategy_1_games: List of cognitive psychology games
        strategy_2_games: List of real-world application games
        
    Returns:
        List of games to play in the session
    """
    # Load settings
    settings = load_settings()
    games_per_session = settings['user_settings']['challenges_per_session']
    
    if choice_type == "game":
        # Single specific game
        return [choice_value] * games_per_session
    
    elif choice_type == "random":
        # Random game selection
        session_games = []
        
        for _ in range(games_per_session):
            if choice_value == "strategy1":
                session_games.append(random.choice(strategy_1_games))
            elif choice_value == "strategy2":
                session_games.append(random.choice(strategy_2_games))
            else:  # "all"
                session_games.append(random.choice(all_games))
        
        return session_games
    
    return []

def show_invalid_choice(stdscr: Any) -> None:
    """Display invalid choice message"""
    # Set background to very dark gray for non-game screens
    apply_nongame_background(stdscr)
    stdscr.clear()
    add_colored_text(stdscr, 1, 2, "Invalid choice! Please try again.", error_style())
    stdscr.refresh()
    time.sleep(1.5)
