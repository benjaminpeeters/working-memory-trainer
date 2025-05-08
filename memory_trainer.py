#!/usr/bin/env python3

import os
import sys
import curses
import argparse

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Change the working directory to the script directory
os.chdir(SCRIPT_DIR)

def main():
    """
    Main entry point for the Working Memory Training Suite
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Working Memory Training Suite")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with verbose output")
    parser.add_argument("--config", type=str, help="Path to custom config file")
    args = parser.parse_args()
    
    # Set debug flag for other modules
    if args.debug:
        os.environ["WM_DEBUG"] = "1"
    
    # Set custom config file if specified
    if args.config:
        os.environ["WM_CONFIG"] = args.config

    # Add script directory to Python path to ensure modules can be found
    sys.path.insert(0, SCRIPT_DIR)
    
    # Import wrapper without polluting namespace
    try:
        # Import the main function from wrapper
        from wrapper import main as wrapper_main
        
        # Run the main function with curses wrapper
        curses.wrapper(wrapper_main)
    except KeyboardInterrupt:
        # Gracefully handle keyboard interrupts
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
        if args.debug:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
