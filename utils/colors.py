#!/usr/bin/env python3

import curses
import os
import json
from typing import Dict, Tuple, Any

"""
Centralized color management for the Working Memory Training Suite.

This module defines all color pairs used throughout the application and provides
utility functions for working with colors in curses.

Color pair assignments:
1: Success color (green on background)
2: Info color (cyan on background)
3: Warning/highlight color (yellow on background)
4: Standard text (white on background)
5: Input field (white on dark gray)
6: Non-game screens background (white on very dark gray)
7: Game screens background (white on black)
8: Error color (red on background)

Special digit span colors:
10: Countdown color (yellow on black)
11: Instruction color (cyan on black)
12: Digit color (bright white on black)
"""

# Color pair assignments
COLOR_SUCCESS = 1
COLOR_INFO = 2
COLOR_WARNING = 3
COLOR_STANDARD = 4
COLOR_INPUT = 5
COLOR_NONGAME_BG = 6
COLOR_GAME_BG = 7
COLOR_ERROR = 8

# Special digit span colors
COLOR_COUNTDOWN = 10
COLOR_INSTRUCTION = 11
COLOR_DIGIT = 12

# Custom color definitions
CUSTOM_DARK_GRAY = 8
CUSTOM_VERY_DARK_GRAY = 9

# Store global background colors
current_bg_color = None
nongame_bg_color = None
game_bg_color = None
input_bg_color = None

# Store color configuration
color_config = {}

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color (#RRGGBB) to RGB tuple (0-1000 range for curses)"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    # Convert from 0-255 to 0-1000 range
    return (r * 1000 // 255, g * 1000 // 255, b * 1000 // 255)

def load_color_config() -> Dict:
    """Load color configuration from JSON file"""
    global color_config
    
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "colors_config.json")
    
    try:
        with open(config_path, 'r') as f:
            color_config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback to default colors if file doesn't exist or is invalid
        color_config = {
            "background": {
                "game": "#000000",
                "nongame": "#262626",
                "input": "#4D4D4D"
            },
            "foreground": {
                "success": "#00FF00",
                "info": "#00FFFF",
                "warning": "#FFFF00",
                "error": "#FF0000",
                "standard": "#FFFFFF",
                "dim": "#AAAAAA"
            },
            "special": {
                "countdown": "#FFFF00",
                "instruction": "#00FFFF",
                "digit": "#FFFFFF"
            }
        }
        
        # Create the config file with defaults
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(color_config, f, indent=2)
        except:
            if os.environ.get("WM_DEBUG"):
                print(f"Failed to create default color config at {config_path}")
                
    return color_config

def setup_colors():
    """
    Initialize all color pairs used in the application.
    
    This function should be called once at the start of the application
    before using any colors.
    """
    global current_bg_color, nongame_bg_color, game_bg_color, input_bg_color
    
    # Make sure we can use colors
    curses.start_color()
    curses.use_default_colors()  # Use terminal's default colors
    
    # Load color configuration
    config = load_color_config()
    
    # Debug output if WM_DEBUG is set
    if os.environ.get("WM_DEBUG"):
        print(f"Terminal supports {curses.COLORS} colors and {curses.COLOR_PAIRS} color pairs")
        print(f"Terminal can change colors: {curses.can_change_color()}")
    
    # Define custom colors for backgrounds if possible
    try:
        if curses.can_change_color():
            # Define the background colors
            r, g, b = hex_to_rgb(config["background"]["nongame"])
            curses.init_color(CUSTOM_VERY_DARK_GRAY, r, g, b)
            nongame_bg_color = CUSTOM_VERY_DARK_GRAY
            
            r, g, b = hex_to_rgb(config["background"]["input"])
            curses.init_color(CUSTOM_DARK_GRAY, r, g, b)
            input_bg_color = CUSTOM_DARK_GRAY
            
            # Game background is always black
            game_bg_color = curses.COLOR_BLACK
        else:
            # Fallback to standard colors if custom colors aren't supported
            nongame_bg_color = curses.COLOR_BLACK
            input_bg_color = curses.COLOR_BLACK
            game_bg_color = curses.COLOR_BLACK
    except:
        # Fallback in case of any errors
        nongame_bg_color = curses.COLOR_BLACK
        input_bg_color = curses.COLOR_BLACK
        game_bg_color = curses.COLOR_BLACK
    
    # Set up main UI colors with the nongame background
    _initialize_color_pairs(nongame_bg_color)
    
    # Set up input field color
    curses.init_pair(COLOR_INPUT, curses.COLOR_WHITE, input_bg_color)
    
    # Background colors
    curses.init_pair(COLOR_NONGAME_BG, curses.COLOR_WHITE, nongame_bg_color)
    curses.init_pair(COLOR_GAME_BG, curses.COLOR_WHITE, game_bg_color)
    
    # Set current background
    current_bg_color = nongame_bg_color

def _initialize_color_pairs(bg_color):
    """Initialize the standard color pairs with the specified background color"""
    # Load color configuration
    config = load_color_config()
    
    # Map color names to curses constants
    color_mapping = {
        "success": curses.COLOR_GREEN,
        "info": curses.COLOR_CYAN,
        "warning": curses.COLOR_YELLOW,
        "error": curses.COLOR_RED,
        "standard": curses.COLOR_WHITE
    }
    
    # Set up foreground colors
    for color_name, curses_color in color_mapping.items():
        # Initialize the foreground color if terminal supports it
        if curses.can_change_color() and color_name in config["foreground"]:
            # Each foreground color gets its own color number, starting from 20
            color_number = 20 + list(color_mapping.keys()).index(color_name)
            r, g, b = hex_to_rgb(config["foreground"][color_name])
            try:
                curses.init_color(color_number, r, g, b)
                if color_name == "success":
                    curses.init_pair(COLOR_SUCCESS, color_number, bg_color)
                elif color_name == "info":
                    curses.init_pair(COLOR_INFO, color_number, bg_color)
                elif color_name == "warning":
                    curses.init_pair(COLOR_WARNING, color_number, bg_color)
                elif color_name == "error":
                    curses.init_pair(COLOR_ERROR, color_number, bg_color)
                elif color_name == "standard":
                    curses.init_pair(COLOR_STANDARD, color_number, bg_color)
            except:
                # Fallback to standard curses colors if custom color fails
                if color_name == "success":
                    curses.init_pair(COLOR_SUCCESS, curses_color, bg_color)
                elif color_name == "info":
                    curses.init_pair(COLOR_INFO, curses_color, bg_color)
                elif color_name == "warning":
                    curses.init_pair(COLOR_WARNING, curses_color, bg_color)
                elif color_name == "error":
                    curses.init_pair(COLOR_ERROR, curses_color, bg_color)
                elif color_name == "standard":
                    curses.init_pair(COLOR_STANDARD, curses_color, bg_color)
        else:
            # Use standard curses colors
            if color_name == "success":
                curses.init_pair(COLOR_SUCCESS, curses_color, bg_color)
            elif color_name == "info":
                curses.init_pair(COLOR_INFO, curses_color, bg_color)
            elif color_name == "warning":
                curses.init_pair(COLOR_WARNING, curses_color, bg_color)
            elif color_name == "error":
                curses.init_pair(COLOR_ERROR, curses_color, bg_color)
            elif color_name == "standard":
                curses.init_pair(COLOR_STANDARD, curses_color, bg_color)
    
    # Set up special digit span colors (always with black background)
    curses.init_pair(COLOR_COUNTDOWN, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(COLOR_INSTRUCTION, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(COLOR_DIGIT, curses.COLOR_WHITE, curses.COLOR_BLACK)

def _update_color_pairs(bg_color):
    """
    Update color pairs to use the specified background color
    
    This is called automatically when applying backgrounds to ensure
    text colors remain consistent with the current background.
    """
    global current_bg_color
    
    # Only update if the background has changed
    if bg_color == current_bg_color:
        return
    
    current_bg_color = bg_color
    
    # Update standard color pairs with the new background
    _initialize_color_pairs(bg_color)

def apply_nongame_background(win):
    """Apply the non-game screen background to the given curses window"""
    global current_bg_color
    
    # First update the color pairs to match the new background
    _update_color_pairs(nongame_bg_color)
    
    # Now apply the background
    win.bkgd(' ', curses.color_pair(COLOR_NONGAME_BG))

def apply_game_background(win):
    """Apply the game screen background to the given curses window"""
    global current_bg_color
    
    # First update the color pairs to match the new background
    _update_color_pairs(game_bg_color)
    
    # Now apply the background
    win.bkgd(' ', curses.color_pair(COLOR_GAME_BG))

def apply_input_background(input_win):
    """Apply the input field background to the given curses window"""
    input_win.bkgd(' ', curses.color_pair(COLOR_INPUT))

def success_style():
    """Return the success text style attribute"""
    return curses.color_pair(COLOR_SUCCESS) | curses.A_BOLD

def info_style():
    """Return the info text style attribute"""
    return curses.color_pair(COLOR_INFO)

def warning_style():
    """Return the warning text style attribute"""
    return curses.color_pair(COLOR_WARNING)

def error_style():
    """Return the error text style attribute"""
    return curses.color_pair(COLOR_ERROR) | curses.A_BOLD

def standard_style():
    """Return the standard text style attribute"""
    return curses.color_pair(COLOR_STANDARD)

def title_style():
    """Return the title text style attribute"""
    return curses.color_pair(COLOR_STANDARD) | curses.A_BOLD

def dim_style():
    """Return the dim text style attribute"""
    return curses.color_pair(COLOR_STANDARD) | curses.A_DIM

def countdown_style():
    """Return the countdown style attribute for digit span"""
    return curses.color_pair(COLOR_COUNTDOWN) | curses.A_BOLD

def instruction_style():
    """Return the instruction style attribute for digit span"""
    return curses.color_pair(COLOR_INSTRUCTION) | curses.A_BOLD

def digit_style():
    """Return the digit style attribute for digit span"""
    return curses.color_pair(COLOR_DIGIT) | curses.A_BOLD

def add_colored_text(win, y, x, text, style):
    """
    Add colored text to a window with specified style
    
    This function helps ensure consistent color application by using a single
    function for all text drawing operations.
    
    Args:
        win: The curses window to draw on
        y: The y coordinate
        x: The x coordinate
        text: The text to display
        style: The style attribute from one of the style functions
    """
    win.addstr(y, x, text, style)
