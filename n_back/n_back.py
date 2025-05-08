#!/usr/bin/env python3

import time
import curses

def play_n_back(stdscr, level):
    """
    Simple N-Back game - just type A to succeed
    """
    stdscr.clear()
    stdscr.addstr(1, 2, "N-BACK CHALLENGE", curses.A_BOLD)
    stdscr.addstr(3, 2, f"Level {level} Challenge")
    stdscr.addstr(5, 2, "This is a simplified test version.")
    stdscr.addstr(7, 2, "Type 'A' to succeed, any other key to fail:")
    stdscr.refresh()
    
    # Start timing
    start_time = time.time()
    
    # Get user input
    key = stdscr.getstr(1).decode('utf-8').upper()
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # Check answer
    success = (key == 'A')
    
    return success, response_time
