#!/usr/bin/env python3

import curses
import time
import random
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Change working directory to script directory to ensure all relative paths are correct
os.chdir(SCRIPT_DIR)

# Import from our modules
from save_load import (
    load_json_file, 
    save_json_file, 
    load_game_progress,
    save_game_progress,
    add_history_entry
)
from progress import show_progress

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
    dim_style
)

# Game names and descriptions
GAMES = {
    "digit_span": "Digit Span Task - Remember and recall sequences of numbers",
    "n_back": "N-Back Challenge - Identify when the current item matches one from N steps earlier",
    "spatial_pattern": "Spatial Pattern Recall - Memorize and reproduce grid patterns",
    "shopping_list": "Shopping List Challenge - Remember increasing lists of items",
    "mental_math": "Mental Math Workout - Perform calculations while holding information in memory",
    "story_details": "Story Details Recall - Read passages and recall specific details"
}

def select_random_game(game_category):
    """Select a random game from the specified category"""
    return random.choice(game_category)

def update_progress(game, success, response_time, user_answer=None):
    """Update game progress based on success/failure"""
    # Load game progress
    game_progress = load_game_progress(game)
    
    # Update basic stats
    game_progress["total_challenges"] += 1
    if success:
        game_progress["successful_challenges"] += 1
        game_progress["current_streak"] += 1
        game_progress["upgrade"] += 1
    else:
        game_progress["current_streak"] = 0
        game_progress["upgrade"] -= 1
    
    # Update longest streak
    if game_progress["current_streak"] > game_progress["longest_streak"]:
        game_progress["longest_streak"] = game_progress["current_streak"]
    
    # Update response time average
    old_avg = game_progress["avg_response_time"]
    old_total = game_progress["total_challenges"] - 1
    if old_total == 0:
        game_progress["avg_response_time"] = response_time
    else:
        game_progress["avg_response_time"] = (old_avg * old_total + response_time) / game_progress["total_challenges"]
    
    # Check for level up/down
    level_before = game_progress["level"]
    if game_progress["upgrade"] >= 10 and game_progress["level"] < 10:
        game_progress["level"] += 1
        game_progress["upgrade"] = 0
        if game_progress["level"] > game_progress["highest_level_reached"]:
            game_progress["highest_level_reached"] = game_progress["level"]
    elif game_progress["upgrade"] <= -5 and game_progress["level"] > 1:
        game_progress["level"] -= 1
        game_progress["upgrade"] = 0
    
    # Save updated progress
    save_game_progress(game, game_progress)
    
    # Add history entry
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "game": game,
        "level": level_before,
        "success": success,
        "response_time": response_time,
        "upgrade_progress": game_progress["upgrade"]
    }
    
    # Add user's answer if provided
    if user_answer:
        entry["user_answer"] = user_answer
        
    add_history_entry(game, entry)
    
    return game_progress["level"], game_progress["upgrade"]

def handle_session_continuation(stdscr, line, height, games_queue, challenges_completed, 
                                current_game, ALL_GAMES, STRATEGY_1_GAMES, STRATEGY_2_GAMES):
    """Handle the logic for continuing or ending a session"""
    # Store session type information
    session_games = []
    session_type = ""
    
    # Determine the current session type
    if current_game in ALL_GAMES:
        # Single game session - just the current game
        session_games = [current_game]
        session_type = "single"
    elif current_game in STRATEGY_1_GAMES:
        session_type = "strategy1"
    elif current_game in STRATEGY_2_GAMES:
        session_type = "strategy2"
    else:
        session_type = "random_all"
        
    if not games_queue and challenges_completed % 10 == 0:
        # Add 4 more challenges of the same type if session is complete
        add_colored_text(stdscr, line, 2, "Session complete! Would you like to continue for 4 more challenges?", standard_style())
        add_colored_text(stdscr, line + 1, 2, "Y: Yes, 4 more challenges  N: No, return to menu  P: Show progress", standard_style())
        add_colored_text(stdscr, height-1, 2, "Press Y to continue, N to end, M for main menu, P for progress, Q to quit", dim_style())
        stdscr.refresh()
        
        while True:
            try:
                choice = stdscr.getch()
                if choice == 3 or choice in [ord('q'), ord('Q')]:  # Ctrl-C or Q
                    os.environ["WM_EXIT"] = "1"  # Set exit flag
                    return False, games_queue
                elif choice in [ord('m'), ord('M')]:  # Return to main menu
                    return False, games_queue
                elif choice in [ord('y'), ord('Y')]:
                    if session_type == "single":
                        # For single game sessions, add 4 more of the same game
                        games_queue.extend([current_game] * 4)
                    elif session_type == "strategy1":
                        # For Strategy 1 sessions, add 4 more Strategy 1 games
                        games_queue.extend([select_random_game(STRATEGY_1_GAMES) for _ in range(4)])
                    elif session_type == "strategy2":
                        # For Strategy 2 sessions, add 4 more Strategy 2 games
                        games_queue.extend([select_random_game(STRATEGY_2_GAMES) for _ in range(4)])
                    else:
                        # For random sessions from all games, add 4 more random games
                        games_queue.extend([select_random_game(ALL_GAMES) for _ in range(4)])
                    return True, games_queue
                elif choice in [ord('n'), ord('N')]:
                    return False, games_queue
                elif choice in [ord('p'), ord('P')]:
                    # Show progress and then return to main menu
                    from progress import show_progress
                    show_progress(stdscr, dict([(game, GAMES[game]) for game in ALL_GAMES]), [False], {})
                    return False, games_queue
            except KeyboardInterrupt:
                os.environ["WM_EXIT"] = "1"  # Set exit flag
                return False, games_queue
    elif not games_queue:
        # End of regular queue but not a multiple of 10
        add_colored_text(stdscr, line, 2, "Continue playing?", standard_style())
        add_colored_text(stdscr, line + 1, 2, "Y: Yes, 4 more challenges  N: No, return to menu  P: Show progress", standard_style())
        add_colored_text(stdscr, height-1, 2, "Press Y to continue, N to end, M for main menu, P for progress, Q to quit", dim_style())
        stdscr.refresh()
        
        while True:
            try:
                choice = stdscr.getch()
                if choice == 3 or choice in [ord('q'), ord('Q')]:  # Ctrl-C or Q
                    os.environ["WM_EXIT"] = "1"  # Set exit flag
                    return False, games_queue
                elif choice in [ord('m'), ord('M')]:  # Return to main menu
                    return False, games_queue
                elif choice in [ord('y'), ord('Y')]:
                    # Add more challenges of the same type
                    if session_type == "single":
                        # For single game sessions, add 4 more of the same game
                        games_queue.extend([current_game] * 4)
                    elif session_type == "strategy1":
                        # For Strategy 1 sessions, add 4 more Strategy 1 games
                        games_queue.extend([select_random_game(STRATEGY_1_GAMES) for _ in range(4)])
                    elif session_type == "strategy2":
                        # For Strategy 2 sessions, add 4 more Strategy 2 games
                        games_queue.extend([select_random_game(STRATEGY_2_GAMES) for _ in range(4)])
                    else:
                        # For random sessions from all games, add 4 more random games
                        games_queue.extend([select_random_game(ALL_GAMES) for _ in range(4)])
                    return True, games_queue
                elif choice in [ord('n'), ord('N')]:
                    return False, games_queue
                elif choice in [ord('p'), ord('P')]:
                    # Show progress and then return to main menu
                    from progress import show_progress
                    show_progress(stdscr, dict([(game, GAMES[game]) for game in ALL_GAMES]), [False], {})
                    return False, games_queue
            except KeyboardInterrupt:
                os.environ["WM_EXIT"] = "1"  # Set exit flag
                return False, games_queue
    else:
        # More games in queue, just continue
        add_colored_text(stdscr, line, 2, "Press any key to continue, M for main menu, Q to quit...", standard_style())
        stdscr.refresh()
        
        try:
            choice = stdscr.getch()
            if choice == 3 or choice in [ord('q'), ord('Q')]:  # Ctrl-C or Q
                os.environ["WM_EXIT"] = "1"  # Set exit flag
                return False, games_queue
            elif choice in [ord('m'), ord('M')]:  # Return to main menu
                return False, games_queue
            return True, games_queue
        except KeyboardInterrupt:
            os.environ["WM_EXIT"] = "1"  # Set exit flag
            return False, games_queue

def start_game_session(stdscr, config, games_queue, exiting, GAME_FUNCTIONS, ALL_GAMES, STRATEGY_1_GAMES, STRATEGY_2_GAMES):
    """
    Start a gaming session with the specified games queue
    
    Parameters:
    - stdscr: curses screen object
    - config: game configuration dictionary
    - games_queue: list of games to play
    - exiting: reference to global exiting flag
    - GAME_FUNCTIONS: dictionary mapping game names to functions
    - ALL_GAMES: list of all game names
    - STRATEGY_1_GAMES: list of cognitive psychology games
    - STRATEGY_2_GAMES: list of real-world application games
    
    This function handles:
    - Playing each game in the queue
    - Showing results after each game
    - Updating progress
    - Displaying next challenge information
    - Handling session continuation/termination
    """
    # Initialize colors
    setup_colors()
    
    challenges_completed = 0
    continue_session = True
    
    while games_queue and continue_session and not exiting[0] and not os.environ.get("WM_EXIT"):
        current_game = games_queue.pop(0)
        challenges_completed += 1
        
        # Get current level for the game
        try:
            game_progress = load_game_progress(current_game)
            current_level = game_progress["level"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # Fallback if file doesn't exist or is invalid
            current_level = 1
        
        # Set background to deep black for game screens
        apply_game_background(stdscr)
        stdscr.clear()
        
        # For the first game in a session, show explanation screen for digit span
        first_in_session = (challenges_completed == 1)
        if first_in_session and current_game == "digit_span":
            try:
                from digit_span.digit_span import display_challenge_explanation_for_wrapper
                continue_game = display_challenge_explanation_for_wrapper(stdscr, current_level, first_in_session)
                
                # Check if user wants to exit
                if os.environ.get("WM_EXIT") == "1":
                    return
                    
                # Check if user wants to return to menu
                if not continue_game:
                    continue_session = False
                    continue  # Skip to next iteration, which will check continue_session
            except (ImportError, AttributeError) as e:
                if os.environ.get("WM_DEBUG"):
                    print(f"Error in display_challenge_explanation: {e}")
        
        # Check for exit request again
        if exiting[0] or os.environ.get("WM_EXIT") == "1":
            return
            
        # Call the specific game function based on the current game
        game_function = GAME_FUNCTIONS.get(current_game)
        if game_function:
            try:
                success, response_time, user_answer = game_function(stdscr, current_level)
            except Exception as e:
                apply_nongame_background(stdscr)
                stdscr.clear()
                add_colored_text(stdscr, 1, 2, f"Error in game {current_game}: {str(e)}", error_style())
                add_colored_text(stdscr, 3, 2, "Press any key to continue...", standard_style())
                stdscr.refresh()
                stdscr.getch()
                continue_session = False
                continue
        else:
            # Fallback to simulation if game function not found
            apply_nongame_background(stdscr)
            stdscr.clear()
            add_colored_text(stdscr, 1, 2, f"Game '{current_game}' not implemented yet.", warning_style())
            add_colored_text(stdscr, 3, 2, "Select: S for success, F for failure, Q to quit, M for menu", standard_style())
            stdscr.refresh()
            
            try:
                key = stdscr.getch()
                if key in [ord('q'), ord('Q')] or key == 3:  # Q or Ctrl+C
                    os.environ["WM_EXIT"] = "1"  # Set exit flag
                    return
                elif key in [ord('m'), ord('M')]:  # M for menu
                    continue_session = False
                    continue
                    
                success = (key in [ord('s'), ord('S')])
                response_time = 1.0  # Default response time
                user_answer = chr(key)
            except KeyboardInterrupt:
                os.environ["WM_EXIT"] = "1"  # Set exit flag
                return
        
        # Check for exit request again
        if exiting[0] or os.environ.get("WM_EXIT") == "1":
            return
        
        # Update progress
        try:
            new_level, upgrade_progress = update_progress(current_game, success, response_time, user_answer)
        except Exception as e:
            apply_nongame_background(stdscr)
            stdscr.clear()
            add_colored_text(stdscr, 1, 2, f"Error in update_progress: {str(e)}", error_style())
            add_colored_text(stdscr, 3, 2, "Press any key to continue...", standard_style())
            stdscr.refresh()
            stdscr.getch()
            continue_session = False
            continue
        
        # Get the next challenge's details from JSON file
        next_challenge_info = None
        if games_queue:
            next_game = games_queue[0]
            # Get information about the next challenge
            if next_game == "digit_span":
                try:
                    # Import function to get next challenge info from digit_span module
                    from digit_span.digit_span import get_next_challenge_info_for_wrapper
                    next_challenge_info = get_next_challenge_info_for_wrapper()
                except (ImportError, AttributeError):
                    # Fallback if function not available
                    next_challenge_info = ["Next: Digit Span Task"]
        
        # Show results - set background to very dark gray for non-game screens
        apply_nongame_background(stdscr)
        stdscr.clear()
        
        # Get terminal dimensions
        height, width = stdscr.getmaxyx()
        
        if success:
            add_colored_text(stdscr, 1, 2, "SUCCESS!", success_style())
        else:
            add_colored_text(stdscr, 1, 2, "INCORRECT", warning_style())
            if user_answer:
                add_colored_text(stdscr, 2, 2, f"Your answer: {user_answer}", standard_style())
            
        # For digit span, get correct answer
        if current_game == "digit_span":
            try:
                # Try to import the function to get the correct answer
                from digit_span.digit_span import get_correct_answer_for_wrapper
                correct_answer = get_correct_answer_for_wrapper()
                add_colored_text(stdscr, 3, 2, f"Correct answer: {correct_answer}", standard_style())
            except (ImportError, AttributeError):
                add_colored_text(stdscr, 3, 2, "Correct answer: Not available", standard_style())
        
        add_colored_text(stdscr, 5, 2, f"Current level: {new_level}/10", standard_style())
        
        level_progress = ""
        if upgrade_progress > 0:
            level_progress = f"{upgrade_progress}/10 towards level up"
        elif upgrade_progress < 0:
            level_progress = f"{abs(upgrade_progress)}/5 towards level down"
        else:
            level_progress = "just changed levels"
            
        add_colored_text(stdscr, 6, 2, f"Progress: {level_progress}", standard_style())
        add_colored_text(stdscr, 7, 2, f"Response time: {response_time:.2f} seconds", standard_style())
        
        # Display next challenge info if available
        line = 9
        if next_challenge_info:
            add_colored_text(stdscr, line, 2, "NEXT CHALLENGE:", info_style())
            line += 1
            for info in next_challenge_info:
                add_colored_text(stdscr, line, 4, info, info_style())
                line += 1
            line += 1
        
        # Handle session continuation
        continue_session, games_queue = handle_session_continuation(
            stdscr, line, height, games_queue, challenges_completed,
            current_game, ALL_GAMES, STRATEGY_1_GAMES, STRATEGY_2_GAMES
        )
        
        # Check for exit request again
        if exiting[0] or os.environ.get("WM_EXIT") == "1":
            if os.environ.get("WM_EXIT") == "1":
                os.environ.pop("WM_EXIT")
            return
