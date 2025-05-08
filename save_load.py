#!/usr/bin/env python3

import json
import os
from typing import Any, Dict, List, Optional, Union

# Get the directory where the root script is located
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def ensure_directory_exists(file_path: str) -> None:
    """Ensure the directory for a file exists"""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def get_absolute_path(relative_path: str) -> str:
    """Convert a relative path to an absolute path based on root location"""
    if os.path.isabs(relative_path):
        return relative_path
    return os.path.join(ROOT_DIR, relative_path)

def load_json_file(file_path: str, default: Optional[Any] = None) -> Any:
    """
    Load JSON from file with error handling using absolute path
    
    Args:
        file_path: Relative or absolute path to the JSON file
        default: Default value to return if file doesn't exist or is invalid
        
    Returns:
        Loaded JSON data, or default value if specified
    """
    abs_path = get_absolute_path(file_path)
    try:
        if os.path.exists(abs_path):
            with open(abs_path, 'r') as f:
                return json.load(f)
        elif default is not None:
            # Create directory if it doesn't exist
            ensure_directory_exists(abs_path)
            # Save default to file
            with open(abs_path, 'w') as f:
                json.dump(default, f, indent=2)
            return default
        else:
            raise FileNotFoundError(f"File not found: {abs_path}")
    except json.JSONDecodeError:
        if default is not None:
            # File exists but is corrupt, overwrite with default
            with open(abs_path, 'w') as f:
                json.dump(default, f, indent=2)
            return default
        else:
            raise
    except Exception as e:
        if os.environ.get("WM_DEBUG"):
            print(f"Error loading {abs_path}: {e}")
        if default is not None:
            return default
        raise

def save_json_file(file_path: str, data: Any) -> bool:
    """
    Save JSON to file with error handling using absolute path
    
    Args:
        file_path: Relative or absolute path to save the JSON file
        data: Data to save as JSON
        
    Returns:
        True if successful, False otherwise
    """
    abs_path = get_absolute_path(file_path)
    try:
        # Create directory if it doesn't exist
        ensure_directory_exists(abs_path)
        # Save to file with proper flushing
        with open(abs_path, 'w') as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
        return True
    except Exception as e:
        if os.environ.get("WM_DEBUG"):
            print(f"Error saving to {abs_path}: {e}")
        return False

# Game file paths
def get_game_progress_path(game: str) -> str:
    """Get the path to a game's progress file"""
    return os.path.join(game, f"{game}.json")

def get_game_history_path(game: str) -> str:
    """Get the path to a game's history file"""
    return os.path.join(game, f"{game}_history.json")

# Settings paths
def get_settings_path() -> str:
    """Get the path to the settings file"""
    return os.path.join("utils", "settings.json")

# Game data functions
def load_settings(default: Optional[Dict] = None) -> Dict:
    """Load settings from the settings file"""
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
            },
            "n_back": {
                "base_n_value": 1,
                "items_per_level": 20,
                "max_n_value": 5,
                "display_time_base": 2.0,
                "display_time_reduction_per_level": 0.15,
                "chance_of_match": 0.3
            },
            "spatial_pattern": {
                "grid_size_base": 3,
                "max_grid_size": 7,
                "min_cells_level_1": 3,
                "max_additional_cells_per_level": 2,
                "display_time_base": 1.5,
                "display_time_reduction_per_level": 0.1
            },
            "shopping_list": {
                "min_items_level_1": 3,
                "max_additional_items_per_level": 2,
                "display_time_per_item": 1.2,
                "category_grouping_intro_level": 4,
                "distraction_intro_level": 7
            },
            "mental_math": {
                "operations_level_1": 2,
                "max_operations": 8,
                "max_value_level_1": 10,
                "max_value_increment_per_level": 5,
                "intermediate_result_frequency": 0.3
            },
            "story_details": {
                "word_count_base": 50,
                "word_count_increment_per_level": 25,
                "questions_level_1": 3,
                "max_questions": 8,
                "detail_specificity_increase_per_level": 0.2
            }
        }
    }
    if default is not None:
        default_settings.update(default)
    return load_json_file(get_settings_path(), default_settings)

def save_settings(settings: Dict) -> bool:
    """Save settings to the settings file"""
    return save_json_file(get_settings_path(), settings)

def load_game_progress(game: str, default: Optional[Dict] = None) -> Dict:
    """Load progress for a specific game"""
    default_progress = {
        "level": 1,
        "upgrade": 0,
        "highest_level_reached": 1,
        "total_challenges": 0,
        "successful_challenges": 0,
        "current_streak": 0,
        "longest_streak": 0,
        "avg_response_time": 0
    }
    
    # For digit span, add next_challenge
    if game == "digit_span":
        default_progress.update({
            "next_challenge": {
                "sequence_length": 3,
                "display_time": 1.0,
                "inter_digit_delay": 0.5,
                "backward": False,
                "interference": False,
                "manipulation": None,
                "instruction": "Remember the digits in order"
            },
            "current_sequence": []
        })
    
    if default is not None:
        default_progress.update(default)
        
    return load_json_file(get_game_progress_path(game), default_progress)

def save_game_progress(game: str, progress: Dict) -> bool:
    """Save progress for a specific game"""
    return save_json_file(get_game_progress_path(game), progress)

def load_game_history(game: str) -> List:
    """Load history for a specific game"""
    return load_json_file(get_game_history_path(game), [])

def save_game_history(game: str, history: List) -> bool:
    """Save history for a specific game"""
    return save_json_file(get_game_history_path(game), history)

def add_history_entry(game: str, entry: Dict) -> bool:
    """Add an entry to a game's history"""
    history = load_game_history(game)
    history.append(entry)
    return save_game_history(game, history)

def get_game_progress_overview(games: List[str]) -> Dict[str, Dict]:
    """Get an overview of all game progress for display"""
    game_progress = {}
    
    for game in games:
        progress = load_game_progress(game)
        game_progress[game] = progress
        
    return game_progress

def create_config_for_compatibility(games: List[str]) -> Dict:
    """Create a compatibility config object for functions that expect the old format"""
    config = {
        "user_settings": {},
        "game_meta_parameters": {},
        "game_progress": {},
        "game_history": []
    }
    
    # Load settings
    settings = load_settings()
    config["user_settings"] = settings.get("user_settings", {})
    config["game_meta_parameters"] = settings.get("game_meta_parameters", {})
    
    # Load game progress
    for game in games:
        progress = load_game_progress(game)
        config["game_progress"][game] = progress
    
    return config

def initialize_all_files(games):
    """Initialize all necessary files if they don't exist"""
    # Ensure utils directory exists
    utils_dir = os.path.join(ROOT_DIR, "utils")
    if not os.path.exists(utils_dir):
        os.makedirs(utils_dir, exist_ok=True)
    
    # Initialize settings file
    settings = load_settings()
    
    # Initialize game progress files and history files
    for game in games:
        # Initialize progress file
        progress = load_game_progress(game)
        
        # Initialize history file
        history = load_game_history(game)
    
    return settings
