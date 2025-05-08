#!/usr/bin/env python3

import time
import curses
import random
import json
import os
import sys

# Get the directory where the script is located (digit_span folder)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add parent directory to path so we can import from utils
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

# Import countdown utility
from utils.countdown import present_challenge, present_countdown, present_instruction

# Import LARGE_DIGITS for displaying digits
from utils.LARGE_DIGITS import LARGE_DIGITS

# Change working directory to script directory
os.chdir(SCRIPT_DIR)

# Constants
SETTINGS_FILE = os.path.join(parent_dir, "utils/settings.json")
PROGRESS_FILE = os.path.join(SCRIPT_DIR, "digit_span.json")
HISTORY_FILE = os.path.join(SCRIPT_DIR, "digit_span_history.json")

# Global variable to store the current sequence
current_sequence = []
current_config = {}

def play_digit_span(stdscr, level):
    """
    Full implementation of Digit Span task with progressive difficulty based on level
    Uses parameters from the JSON configuration file
    """
    global current_sequence, current_config
    
    # Set background for the game screen
    apply_game_background(stdscr)
    
    # Setup colors
    setup_colors()
    
    # Get terminal dimensions
    height, width = stdscr.getmaxyx()
    
    # Load challenge configuration
    challenge_config = load_challenge_config(level)
    current_config = challenge_config.copy()  # Store for correct answer display
    
    # Generate sequence of digits
    sequence = generate_sequence(challenge_config)
    current_sequence = sequence.copy()  # Store for correct answer display
    
    # Debug output if WM_DEBUG is set
    if os.environ.get("WM_DEBUG"):
        print(f"Generated sequence: {sequence}")
    
    # Present the sequence
    present_sequence(stdscr, sequence, challenge_config)
    
    # If interference is enabled, show interference task
    if challenge_config.get('interference_task', False):
        show_interference_task(stdscr, challenge_config)
    
    # Get user's response
    success, response_time, user_answer = get_user_response(stdscr, sequence, challenge_config, height, width)
    
    # Debug output if WM_DEBUG is set
    if os.environ.get("WM_DEBUG"):
        print(f"User answer: {user_answer}, Expected: {sequence}, Success: {success}")
    
    # Generate next challenge configuration and update JSON
    next_challenge_config = generate_next_challenge_config(level)
    update_next_challenge(next_challenge_config)
    
    # Return results (only 3 values as expected by the wrapper)
    return success, response_time, user_answer

def load_settings():
    """Load settings from JSON file"""
    default_settings = {
        "user_settings": {
            "challenges_per_session": 10,
            "current_user": "default"
        },
        "game_meta_parameters": {
            "digit_span": {
                "backward_intro_level": 4,
                "interference_intro_level": 7,
                "selective_recall_intro_level": 8,
                "ordering_intro_level": 9,
                "base_display_time": 1.0,
                "display_time_reduction_per_level": 0.1,
                "base_delay_time": 0.5,
                "delay_time_reduction_per_level": 0.05,
                "min_digits_level_1": 3,
                "max_additional_digits_per_level": 1
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
            "sequence_length": 3,
            "display_time": 1.0,
            "inter_digit_delay": 0.5,
            "backward": False,
            "interference_task": False,
            "selective_recall": False,
            "ordering": False,
            "instruction": "Remember the sequence of digits"
        }
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
        # Store the current sequence if it exists
        if 'current_sequence' in progress:
            global current_sequence
            current_sequence = progress.get('current_sequence', [])
            if os.environ.get("WM_DEBUG"):
                print(f"Loaded current sequence from progress file: {current_sequence}")
        
        return progress['next_challenge']
    
    # If no valid configuration, generate a new one
    return generate_next_challenge_config(level)

def update_next_challenge(next_config):
    """Update the next challenge configuration in the progress file"""
    global current_sequence
    progress = load_progress()
    progress['next_challenge'] = next_config
    progress['current_sequence'] = current_sequence
    save_json_file(PROGRESS_FILE, progress)
    
    # Debug output if WM_DEBUG is set
    if os.environ.get("WM_DEBUG"):
        print(f"Updated progress file with new challenge config and sequence: {current_sequence}")

def generate_next_challenge_config(level):
    """Generate the configuration for the next challenge based on meta-parameters"""
    settings = load_settings()
    
    # Get meta-parameters for digit span
    try:
        meta = settings["game_meta_parameters"]["digit_span"]
    except KeyError:
        # Default meta-parameters if not found
        meta = {
            "backward_intro_level": 4,
            "interference_intro_level": 7,
            "selective_recall_intro_level": 8,
            "ordering_intro_level": 9,
            "base_display_time": 1.0,
            "display_time_reduction_per_level": 0.1,
            "base_delay_time": 0.5,
            "delay_time_reduction_per_level": 0.05,
            "min_digits_level_1": 3,
            "max_additional_digits_per_level": 1
        }
    
    # Initialize new challenge config
    config = {
        "sequence_length": 0,
        "display_time": 0,
        "inter_digit_delay": 0,
        "backward": False,
        "interference_task": False,
        "selective_recall": False,
        "ordering": False,
        "instruction": ""
    }
    
    # Calculate sequence length
    config["sequence_length"] = meta["min_digits_level_1"] + int((level - 1) * meta["max_additional_digits_per_level"])
    
    # Calculate display times
    config["display_time"] = max(0.3, meta["base_display_time"] - (level - 1) * meta["display_time_reduction_per_level"])
    config["inter_digit_delay"] = max(0.1, meta["base_delay_time"] - (level - 1) * meta["delay_time_reduction_per_level"])
    
    # Determine if special task types are needed based on level
    if level >= meta["backward_intro_level"]:
        config["backward"] = random.choice([True, False])  # 50% chance once introduced
    
    if level >= meta["interference_intro_level"]:
        config["interference_task"] = random.choice([True, False])  # 50% chance once introduced
    
    if level >= meta["selective_recall_intro_level"]:
        config["selective_recall"] = random.choice([True, False])  # 50% chance once introduced
        # Don't combine backward with selective recall as it's too difficult
        if config["selective_recall"]:
            config["backward"] = False
    
    if level >= meta["ordering_intro_level"]:
        config["ordering"] = random.choice([True, False])  # 50% chance once introduced
        # Don't combine with other complex tasks
        if config["ordering"]:
            config["backward"] = False
            config["selective_recall"] = False
    
    # Set instruction based on configuration
    config["instruction"] = get_instruction_text(config)
    
    # For advanced debugging or logging
    if os.environ.get("WM_DEBUG"):
        print(f"Generated config for level {level}:")
        print(f"  Sequence length: {config['sequence_length']}")
        print(f"  Display time: {config['display_time']}s")
        print(f"  Inter-digit delay: {config['inter_digit_delay']}s")
        print(f"  Backward: {config['backward']}")
        print(f"  Interference: {config['interference_task']}")
        print(f"  Selective recall: {config['selective_recall']}")
        print(f"  Ordering: {config['ordering']}")
    
    return config

def get_instruction_text(config):
    """Generate instruction text based on the challenge configuration"""
    instruction = "Remember the sequence"
    
    if config["backward"]:
        instruction += " and repeat it BACKWARD"
    elif config["selective_recall"]:
        instruction += " but only repeat ODD digits"
    elif config["ordering"]:
        instruction += " and repeat it in ASCENDING order"
    
    if config["interference_task"]:
        instruction += " (with math problem)"
    
    return instruction

def generate_sequence(config):
    """Generate a random sequence of digits based on configuration"""
    length = config["sequence_length"]
    
    # Generate random digits 0-9
    sequence = [random.randint(0, 9) for _ in range(length)]
    
    if config.get("selective_recall"):
        # Ensure there's at least one odd digit for selective recall
        if not any(d % 2 == 1 for d in sequence):
            # Replace a random digit with an odd one
            sequence[random.randint(0, length - 1)] = random.choice([1, 3, 5, 7, 9])
    
    # For debugging or logging
    if os.environ.get("WM_DEBUG"):
        print(f"Generated sequence: {sequence}")
    
    return sequence

def present_sequence(stdscr, sequence, config):
    """Present the digit sequence to the user"""
    # Define a callback function to be used by present_challenge
    def show_sequence(stdscr, config):
        # Get screen dimensions
        height, width = stdscr.getmaxyx()
        
        # Present each digit in white/bright
        for digit in sequence:
            stdscr.clear()
            
            # Display the digit in large font at center
            digit_lines = LARGE_DIGITS[digit]
            for i, line in enumerate(digit_lines):
                y = height//2 - len(digit_lines)//2 + i
                x = width//2 - len(line)//2
                stdscr.addstr(y, x, line, digit_style())
            
            stdscr.refresh()
            time.sleep(config['display_time'])
            
            # Blank screen between digits
            stdscr.clear()
            stdscr.refresh()
            time.sleep(config['inter_digit_delay'])
        
        # Clear screen after sequence
        stdscr.clear()
        stdscr.refresh()
    
    # Use the centralized challenge presentation function
    present_challenge(
        stdscr=stdscr,
        config=config,
        challenge_callback=show_sequence
    )

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
    prompt_x = width//2 - (len(prompt) + 5)//2
    add_colored_text(stdscr, input_row, prompt_x, prompt, standard_style())
    
    input_win = curses.newwin(1, 5, input_row, prompt_x + len(prompt))
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

def get_user_response(stdscr, sequence, config, height, width):
    """Get the user's response to the digit span task"""
    # Determine expected answer based on task type
    expected = get_expected_answer(sequence, config)
    
    # Clear screen and ensure game background is applied
    apply_game_background(stdscr)
    stdscr.clear()
    
    # Show instructions
    task_type = get_task_type_description(config)
    add_colored_text(stdscr, 2, 2, f"Enter the digits you remember {task_type}", title_style())
    
    if config.get("selective_recall"):
        add_colored_text(stdscr, 3, 2, "Only enter the ODD digits (1, 3, 5, 7, 9) in the original order", standard_style())
    elif config.get("ordering"):
        add_colored_text(stdscr, 3, 2, "Enter the digits in ascending order (lowest to highest)", standard_style())
    
    # Draw a note about validation
    add_colored_text(stdscr, height-3, 2, "Press ENTER to validate or M to return to the main menu", dim_style())
    add_colored_text(stdscr, height-2, 2, "Press Ctrl-C to exit the game", dim_style())
    
    # Create input window for digits
    input_y = height // 2
    input_x = width // 2 - 10
    prompt = "Your answer: "
    add_colored_text(stdscr, input_y, input_x - len(prompt), prompt, standard_style())
    
    max_input_len = 20  # Allow for longer sequences
    input_win = curses.newwin(1, max_input_len, input_y, input_x)
    apply_input_background(input_win)
    input_win.keypad(True)  # Enable special keys
    
    stdscr.refresh()
    input_win.refresh()
    
    # Start timing
    start_time = time.time()
    
    # Get user input with validation
    curses.echo()
    user_input = ""
    validation_feedback = ""
    
    while True:
        stdscr.clear()
        apply_game_background(stdscr)
        
        # Re-display the instructions
        add_colored_text(stdscr, 2, 2, f"Enter the digits you remember {task_type}", title_style())
        
        if config.get("selective_recall"):
            add_colored_text(stdscr, 3, 2, "Only enter the ODD digits (1, 3, 5, 7, 9) in the original order", standard_style())
        elif config.get("ordering"):
            add_colored_text(stdscr, 3, 2, "Enter the digits in ascending order (lowest to highest)", standard_style())
        
        # Show validation feedback if any
        if validation_feedback:
            add_colored_text(stdscr, 4, 2, validation_feedback, 
                           success_style() if "Correct" in validation_feedback else warning_style())
        
        # Draw a note about validation
        add_colored_text(stdscr, height-3, 2, "Press ENTER to validate or M to return to the main menu", dim_style())
        add_colored_text(stdscr, height-2, 2, "Press Ctrl-C to exit the game", dim_style())
        
        # Re-display the input prompt
        add_colored_text(stdscr, input_y, input_x - len(prompt), prompt, standard_style())
        
        # Create a new input window
        input_win = curses.newwin(1, max_input_len, input_y, input_x)
        apply_input_background(input_win)
        input_win.keypad(True)
        
        # Show previous input
        if user_input:
            input_win.addstr(0, 0, user_input)
        
        stdscr.refresh()
        input_win.refresh()
        
        try:
            curses.curs_set(1)  # Show cursor
            # Get key input
            key = input_win.getch()
            
            if key == 3:  # Ctrl-C
                os.environ["WM_EXIT"] = "1"  # Set exit flag
                return False, 0, []
            
            elif key in [ord('m'), ord('M')]:  # Return to main menu
                return False, 0, []
            
            elif key in [curses.KEY_ENTER, 10, 13]:  # Enter key - validate
                # Convert user input to list of integers
                try:
                    user_answer = [int(d) for d in user_input]
                except ValueError:
                    user_answer = []
                
                # Check if the answer matches the expected sequence
                success = (user_answer == expected)
                
                # Get validation feedback
                validation_feedback = validate_user_answer(user_answer, expected, config)
                
                # If correct, exit the input loop
                if success:
                    break
                
                # Otherwise, show feedback and continue
                continue
            
            elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace
                if user_input:
                    user_input = user_input[:-1]
            
            elif key >= ord('0') and key <= ord('9'):  # Digit
                if len(user_input) < max_input_len:
                    user_input += chr(key)
            
        except KeyboardInterrupt:
            os.environ["WM_EXIT"] = "1"  # Set exit flag
            return False, 0, []
    
    curses.noecho()
    curses.curs_set(0)  # Hide cursor
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # Convert user input to list of integers (again, to ensure consistency)
    try:
        user_answer = [int(d) for d in user_input]
    except ValueError:
        user_answer = []
    
    return success, response_time, user_answer

def get_expected_answer(sequence, config):
    """Calculate the expected answer based on the task configuration"""
    if config.get("backward"):
        # Reverse the sequence
        return list(reversed(sequence))
    
    elif config.get("selective_recall"):
        # Filter for odd digits
        return [d for d in sequence if d % 2 == 1]
    
    elif config.get("ordering"):
        # Sort the sequence
        return sorted(sequence)
    
    else:
        # Forward recall (default)
        return sequence

def get_task_type_description(config):
    """Generate a description of the task type for instructions"""
    if config.get("backward"):
        return "in REVERSE order"
    elif config.get("selective_recall"):
        return "- ODD digits only"
    elif config.get("ordering"):
        return "in ASCENDING order"
    else:
        return "in order"

def validate_user_answer(user_answer, expected, config):
    """Provide feedback on the user's answer"""
    # Check if the answer is completely correct
    if user_answer == expected:
        return "Correct!"
    
    # If completely wrong length
    if len(user_answer) != len(expected):
        return f"Incorrect length. Expected {len(expected)} digits, got {len(user_answer)}."
    
    # Count correct digits in correct positions
    correct_positions = sum(1 for u, e in zip(user_answer, expected) if u == e)
    
    # Check for special case of correct digits but in wrong order
    if sorted(user_answer) == sorted(expected) and not config.get("ordering"):
        return f"All digits correct but in wrong order. {correct_positions}/{len(expected)} in correct position."
    
    # Generic feedback
    return f"Partially correct. {correct_positions}/{len(expected)} digits in correct position."

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
        info_lines.append(f"Sequence length: {next_challenge['sequence_length']} digits")
        info_lines.append(f"Display time: {next_challenge['display_time']:.1f} seconds per digit")
        
        # Special task info
        task_type = []
        if next_challenge.get('backward'):
            task_type.append("Backward recall")
        if next_challenge.get('selective_recall'):
            task_type.append("Selective recall (odd digits only)")
        if next_challenge.get('ordering'):
            task_type.append("Order the digits (ascending)")
        if next_challenge.get('interference_task'):
            task_type.append("With interference task")
        
        if task_type:
            info_lines.append("Task type: " + ", ".join(task_type))
        else:
            info_lines.append("Task type: Forward recall")
        
        return info_lines
    except Exception as e:
        if os.environ.get("WM_DEBUG"):
            print(f"Error getting next challenge info: {str(e)}")
        return [f"Error getting next challenge info: {str(e)}"]

def get_correct_answer():
    """Return a string representation of the correct sequence"""
    global current_sequence, current_config
    
    if not current_sequence or not current_config:
        return "Not available"
    
    try:
        # Calculate expected answer based on task configuration
        expected = get_expected_answer(current_sequence, current_config)
        
        # Format as string for display
        return "".join(str(digit) for digit in expected)
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
    add_colored_text(stdscr, 2, 2, "DIGIT SPAN TASK", title_style())
    add_colored_text(stdscr, 3, 2, "Test and improve your working memory", info_style())
    
    # Description
    description = [
        "",
        "In this task, you will:",
        f"- See a sequence of {challenge_config['sequence_length']} digits",
        f"- Each digit appears for {challenge_config['display_time']:.1f} seconds",
        "- Try to remember the sequence and reproduce it",
        "",
        "How to play:",
        "- Watch the digits appear one by one",
        "- Type the sequence you remember",
        "- Press ENTER to validate your answer",
        ""
    ]
    
    # Add special instructions based on configuration
    if challenge_config.get('backward'):
        description.append("You'll need to enter the digits in REVERSE order.")
    
    if challenge_config.get('selective_recall'):
        description.append("You'll only need to remember and enter the ODD digits (1,3,5,7,9).")
    
    if challenge_config.get('ordering'):
        description.append("You'll need to enter the digits in ASCENDING order (smallest to largest).")
    
    if challenge_config.get('interference_task'):
        description.append("You'll solve a simple math problem before recalling the digits.")
    
    # Explain difficulty progression
    difficulty_explanation = [
        "",
        "Difficulty progression:",
        "- Sequence length increases with each level",
        "- Display time decreases with each level",
        "- At higher levels, special tasks like backward recall and interference are introduced"
    ]
    
    # Strategy tips based on level
    if level <= 3:
        tips = [
            "",
            "Beginner Tips:",
            "- Try to mentally repeat the digits as you see them",
            "- Group digits into chunks of 2-3 for easier recall",
            "- Visualize the digits as you see them"
        ]
    elif level <= 6:
        tips = [
            "",
            "Intermediate Tips:",
            "- Create a rhythm as you memorize the digits",
            "- Rehearse the sequence multiple times in your mind",
            "- For backward recall, focus on the last few digits first"
        ]
    else:
        tips = [
            "",
            "Advanced Tips:",
            "- Create associations between consecutive digits",
            "- For selective recall, mentally highlight the target digits",
            "- Develop a consistent mental strategy and stick with it"
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
    ready_text = "Press ENTER to begin or M to return to main menu or Q to quit..."
    ready_x = width//2 - len(ready_text)//2
    add_colored_text(stdscr, line + 2, ready_x, ready_text, title_style())
    
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
