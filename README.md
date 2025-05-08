# Working Memory Trainer

A terminal-based cognitive training application with multiple memory games.

## Overview

Working Memory Trainer is a curses-based terminal application that provides various cognitive training exercises to improve working memory and mental processing. The application includes multiple game types with adjustable difficulty levels and progress tracking.

## Game Types

- **Digit Span**: Remember and recall sequences of digits of increasing length
- **N-Back**: Identify matches in a sequence based on items shown n steps earlier
- **Mental Math**: Solve arithmetic problems with increasing complexity
- **Shopping List**: Memorize and recall lists of items
- **Spatial Pattern**: Remember and reproduce spatial patterns
- **Story Details**: Read short stories and recall specific details

## Installation

### Prerequisites

- Python 3.x
- Curses library (included with most Python installations)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/username/working-memory-trainer.git
   cd working-memory-trainer
   ```

2. Run the main program:
   ```bash
   python memory_trainer.py
   ```

## Usage

Navigate the menu using arrow keys and select options with Enter. Each game has its own instructions that will be displayed before starting.

The application saves your progress automatically and will adjust difficulty based on your performance.

## Configuration

Game settings can be modified in the corresponding JSON files for each game type:

- `digit_span/digit_span.json`
- `n_back/n_back.json`
- `mental_math/mental_math.json`
- `shopping_list/shopping_list.json`
- `spatial_pattern/spatial_pattern.json`
- `story_details/story_details.json`

## License

AGPL-3.0