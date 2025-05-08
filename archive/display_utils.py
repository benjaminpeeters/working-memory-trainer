#!/usr/bin/env python3

import time
import curses
import os
import sys
import importlib.util

# Try to import LARGE_DIGITS
try:
    # Get the script directory and parent directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # Add the utils directory to the path if not already present
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Import LARGE_DIGITS
    from LARGE_DIGITS import LARGE_DIGITS
except ImportError:
    # Fallback definition if import fails
    print("Could not import LARGE_DIGITS, using fallback definition")
    LARGE_DIGITS = [
        [" __ ", "/  \\", "\\__/", "    "],  # 0
        ["    ", "   |", "   |", "    "],    # 1
        [" __ ", " __|", "|__ ", "    "],    # 2
        [" __ ", " __|", " __|", "    "],    # 3
        ["    ", "|__|", "   |", "    "],    # 4
        [" __ ", "|__ ", " __|", "    "],    # 5
        [" __ ", "|__ ", "|__|", "    "],    # 6
        [" __ ", "   |", "   |", "    "],    # 7
        [" __ ", "|__|", "|__|", "    "],    # 8
        [" __ ", "|__|", " __|", "    "]     # 9
    ]

def display_big_number(stdscr, number, y, x, attr):
    """Display a big ASCII art number at the specified position"""
    number_str = str(number)
    
    for i, digit in enumerate(number_str):
        digit_int = int(digit)
        for line_idx, line in enumerate(LARGE_DIGITS[digit_int]):
            stdscr.addstr(y + line_idx, x + (i * 6), line, attr)

def display_countdown(stdscr, height, width, countdown_style, start_count=3, delay=0.7):
    """
    Display a centralized countdown using large digits
    
    Args:
        stdscr: The curses window
        height: Screen height
        width: Screen width
        countdown_style: The style to use for the countdown
        start_count: The number to start counting down from (default 3)
        delay: Time in seconds between each count (default 0.7)
    """
    for count in range(start_count, 0, -1):
        stdscr.clear()
        # Display large centered countdown
        display_big_number(stdscr, count, height//2 - 2, width//2 - 3, countdown_style())
        stdscr.refresh()
        time.sleep(delay)

def display_instruction(stdscr, height, width, instruction, instruction_style, display_time=1.5):
    """
    Display a centered instruction text
    
    Args:
        stdscr: The curses window
        height: Screen height
        width: Screen width
        instruction: The instruction text to display
        instruction_style: The style to use for the instruction
        display_time: How long to display the instruction (default 1.5s)
    """
    from utils.colors import add_colored_text
    
    stdscr.clear()
    add_colored_text(stdscr, height//2, width//2 - len(instruction)//2, 
                    instruction, instruction_style())
    stdscr.refresh()
    time.sleep(display_time)
