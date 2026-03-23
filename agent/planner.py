import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import app_logger


class Planner:
    '''Decomposes a user game prompt into a structured, detail-rich prompt for AI generation.

    The compiled prompt instructs the AI provider to produce a fully PocketPy-compatible,
    text/grid-based Python game — enforcing all runtime constraints before code is generated.
    '''

    def __init__(self, ai_provider):
        self.ai_provider = ai_provider

    def plan_project(self, prompt: str) -> dict:
        '''Build a structured game specification from a raw user prompt.

        Returns:
            dict with key 'compiled_prompt' — the enriched prompt string sent to the AI.
        '''
        app_logger.info(f'Planning project for: {prompt}')
        compiled_prompt = (
            f"Build a PocketPy-compatible terminal game: '{prompt}'.\n\n"
            "Requirements (ALL mandatory):\n"
            "  - Pure Python, no external libraries except: math, random, sys, time, collections\n"
            "  - Text/ASCII rendering using print() — NO pygame, NO tkinter, NO GUI\n"
            "  - Interactive game loop driven by input() (w/a/s/d or menu commands)\n"
            "  - Proper win/loss/game-over detection with clear terminal messages\n"
            "  - Score tracking displayed after each move\n"
            "  - Grid or board state represented as a list-of-lists\n"
            "  - Clean code: snake_case functions, CapsCaseWords classes, constants in UPPER_CASE\n"
            "  - A single entry point: if __name__ == '__main__': main()\n"
            "Output ONLY the Python code block — no explanation text outside the block."
        )
        return {'compiled_prompt': compiled_prompt}
