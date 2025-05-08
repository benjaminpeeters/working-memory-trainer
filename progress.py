#!/usr/bin/env python3

import curses
import time
import subprocess
import os
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt

# Import utilities
from save_load import load_game_progress, load_settings

def setup_progress_colors():
    """Set up color pairs for the progress screens"""
    curses.start_color()
    curses.use_default_colors()  # Use terminal's default colors
    
    # Main UI colors
    curses.init_pair(1, curses.COLOR_GREEN, -1)  # Success color
    curses.init_pair(2, curses.COLOR_CYAN, -1)   # Info color
    curses.init_pair(3, curses.COLOR_YELLOW, -1) # Warning/highlight color
    curses.init_pair(4, curses.COLOR_WHITE, -1)  # Standard text
    
    # Very dark gray background for non-game screens
    try:
        if curses.can_change_color():
            curses.init_color(9, 150, 150, 150)  # Very dark gray (RGB: 150/1000)
            curses.init_pair(6, curses.COLOR_WHITE, 9)  # White on very dark gray
        else:
            curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)
    except:
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)
    
    # Error color
    curses.init_pair(8, curses.COLOR_RED, -1)

def create_visualization(games: Dict[str, str], output_path: str = "working_memory_progress.png") -> str:
    """
    Create matplotlib visualization and save to file
    
    Args:
        games: Dictionary mapping game names to descriptions
        output_path: Path to save the visualization to
        
    Returns:
        Path to the saved visualization
    """
    # Extract data for visualization
    game_names = list(games.keys())
    levels = []
    success_rates = []
    avg_times = []
    highest_levels = []
    
    for game in game_names:
        progress = load_game_progress(game)
        
        # Get level
        levels.append(progress.get("level", 1))
        
        # Calculate success rate
        total = progress.get("total_challenges", 0)
        successful = progress.get("successful_challenges", 0)
        if total > 0:
            rate = (successful / total) * 100
        else:
            rate = 0
        success_rates.append(rate)
        
        # Get average response time
        avg_times.append(progress.get("avg_response_time", 0))
        
        # Get highest level reached
        highest_levels.append(progress.get("highest_level_reached", 1))
    
    # Create figure with multiple subplots
    fig = plt.figure(figsize=(12, 10))
    
    # Current level by game
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.bar(game_names, levels, color='skyblue')
    ax1.set_title('Current Level by Game')
    ax1.set_ylabel('Level')
    ax1.set_ylim(0, 10)
    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # Success rate by game
    ax2 = fig.add_subplot(2, 2, 2)
    ax2.bar(game_names, success_rates, color='lightgreen')
    ax2.set_title('Success Rate by Game (%)')
    ax2.set_ylabel('Success Rate')
    ax2.set_ylim(0, 100)
    plt.setp(ax2.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # Average response time
    ax3 = fig.add_subplot(2, 2, 3)
    ax3.bar(game_names, avg_times, color='salmon')
    ax3.set_title('Average Response Time (seconds)')
    ax3.set_ylabel('Time (s)')
    plt.setp(ax3.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # Highest level reached
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.bar(game_names, highest_levels, color='gold')
    ax4.set_title('Highest Level Reached')
    ax4.set_ylabel('Level')
    ax4.set_ylim(0, 10)
    plt.setp(ax4.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    plt.tight_layout()
    
    # Get the full path for the output file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    viz_path = os.path.join(script_dir, output_path)
    
    # Save figure to file
    plt.savefig(viz_path)
    
    # Return the figure path
    return viz_path

def show_progress(stdscr: Any, games: Dict[str, str], exiting: List[bool], config: Optional[Dict] = None) -> None:
    """
    Display progress tracking and visualization
    
    Args:
        stdscr: The curses screen object
        games: Dictionary mapping game names to descriptions
        exiting: Reference to global exiting flag
        config: Optional compatibility config
    """
    # Set background to very dark gray for non-game screens
    stdscr.bkgd(' ', curses.color_pair(6))
    
    # Set up colors
    setup_progress_colors()
    
    # First, create the visualization
    try:
        # Generate the visualization
        visualization_path = create_visualization(games)
        visualization_error = None
    except Exception as e:
        visualization_error = str(e)
    
    # Now show the terminal stats
    stdscr.clear()
    stdscr.addstr(1, 2, "PROGRESS VISUALIZATION", curses.A_BOLD)
    stdscr.addstr(3, 2, "Game Statistics:", curses.A_UNDERLINE)
    
    line = 5
    for game in games:
        progress = load_game_progress(game)
        
        total = progress.get("total_challenges", 0)
        successful = progress.get("successful_challenges", 0)
        success_rate = 0 if total == 0 else (successful / total) * 100
            
        stdscr.addstr(line, 2, f"{games[game]}")
        stdscr.addstr(line + 1, 4, f"Level: {progress.get('level', 1)}/10")
        stdscr.addstr(line + 2, 4, f"Total Challenges: {total}")
        stdscr.addstr(line + 3, 4, f"Success Rate: {success_rate:.1f}%")
        stdscr.addstr(line + 4, 4, f"Longest Streak: {progress.get('longest_streak', 0)}")
        stdscr.addstr(line + 5, 4, f"Avg Response Time: {progress.get('avg_response_time', 0):.2f}s")
        
        line += 7
    
    # Try to open the visualization after generating it
    if visualization_error:
        stdscr.addstr(line, 2, f"Error creating visualization: {visualization_error}", curses.color_pair(8))
        line += 2
    else:
        stdscr.addstr(line, 2, "Visualization saved as: working_memory_progress.png")
        line += 2
        
        # Try to open the image
        try:
            # For Linux
            subprocess.Popen(["xdg-open", visualization_path], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            try:
                # For macOS
                subprocess.Popen(["open", visualization_path],
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                try:
                    # For Windows
                    subprocess.Popen(["start", visualization_path], shell=True,
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.DEVNULL)
                except:
                    stdscr.addstr(line, 2, "Could not automatically open visualization")
                    line += 2
    
    # Get terminal dimensions
    height, width = stdscr.getmaxyx()
    stdscr.addstr(height-1, 2, "Press Ctrl-C to exit at any time", curses.A_DIM)
    
    stdscr.addstr(line, 2, "Press any key to return to the main menu...")
    stdscr.refresh()
    
    # Check for exit request with proper Ctrl+C handling
    if exiting[0]:
        return
    
    try:
        # Set timeout for checking Ctrl+C
        stdscr.timeout(100)
        
        while True:
            try:
                key = stdscr.getch()
                if key == -1:  # No key pressed yet
                    continue
                elif key == 3:  # Ctrl+C
                    exiting[0] = True
                    return
                else:
                    break  # Any other key
            except KeyboardInterrupt:
                exiting[0] = True
                return
        
        # Reset timeout
        stdscr.timeout(-1)
    except:
        pass
