'''
PocketPy AI NPC Demo
====================
A text/grid-based demonstration of a Gemini-powered NPC that pursues or
avoids the player on a 2D grid. Ported from the original pygame demo to
a pure terminal rendering system that is compatible with PocketPy.

How to play:
  w / a / s / d  — move the player (P)
  q              — quit

The NPC (@) asks Gemini for its next move every DECISION_INTERVAL turns.
Without an API key it falls back to a simple built-in heuristic.
'''
import os
import sys
import math
import random

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GRID_WIDTH = 20
GRID_HEIGHT = 10
DECISION_INTERVAL = 3    # How many player moves before the NPC asks Gemini
PLAYER_CHAR = 'P'
NPC_CHAR = '@'
EMPTY_CHAR = '.'
WALL_CHAR = '#'

# ---------------------------------------------------------------------------
# API setup
# ---------------------------------------------------------------------------
load_dotenv()
_api_key = os.getenv('GEMINI_API_KEY')
_client = None
_model_name = 'gemini-2.5-flash'

if _api_key:
    try:
        from google import genai as _genai
        _client = _genai.Client(api_key=_api_key)
        print('[NPC Demo] Gemini client initialised.')
    except Exception as _e:
        print(f'[NPC Demo] Warning — could not initialise Gemini client: {_e}')
else:
    print('[NPC Demo] No GEMINI_API_KEY found; using built-in heuristic NPC.')


# ---------------------------------------------------------------------------
# Grid helpers
# ---------------------------------------------------------------------------

def make_grid(width: int, height: int) -> list:
    '''Create a blank grid of EMPTY_CHAR cells surrounded by WALL_CHAR.'''
    grid = []
    for row in range(height):
        if row == 0 or row == height - 1:
            grid.append([WALL_CHAR] * width)
        else:
            grid.append([WALL_CHAR] + [EMPTY_CHAR] * (width - 2) + [WALL_CHAR])
    return grid


def render_grid(grid: list, player_pos: list, npc_pos: list, npc_action: str, turn: int):
    '''Clear the terminal and print the current grid state.'''
    os.system('cls' if sys.platform == 'win32' else 'clear')

    # Draw actors onto a snapshot of the grid
    snapshot = [row[:] for row in grid]
    pr, pc = player_pos
    nr, nc = npc_pos
    snapshot[pr][pc] = PLAYER_CHAR
    snapshot[nr][nc] = NPC_CHAR

    print('╔' + '═' * (GRID_WIDTH * 2) + '╗')
    for row in snapshot:
        print('║ ' + ' '.join(row) + ' ║')
    print('╚' + '═' * (GRID_WIDTH * 2) + '╝')
    print(f'  Turn: {turn}  |  NPC last action: {npc_action}')
    print(f'  Player: {player_pos}  |  NPC: {npc_pos}')
    print()
    print('  Move: w/a/s/d  |  Quit: q')


def is_walkable(grid: list, row: int, col: int) -> bool:
    '''Return True if the given cell can be walked into.'''
    if row < 0 or row >= len(grid) or col < 0 or col >= len(grid[0]):
        return False
    return grid[row][col] != WALL_CHAR


# ---------------------------------------------------------------------------
# NPC decision logic
# ---------------------------------------------------------------------------

def heuristic_npc_decision(player_pos: list, npc_pos: list) -> str:
    '''Simple built-in NPC: move away from the player using Manhattan distance.'''
    pr, pc = player_pos
    nr, nc = npc_pos

    candidates = {
        'UP':    (nr - 1, nc),
        'DOWN':  (nr + 1, nc),
        'LEFT':  (nr, nc - 1),
        'RIGHT': (nr, nc + 1),
    }

    best_action = 'STAY'
    best_dist = abs(pr - nr) + abs(pc - nc)

    for action, (new_r, new_c) in candidates.items():
        dist = abs(pr - new_r) + abs(pc - new_c)
        if dist > best_dist:
            best_dist = dist
            best_action = action

    return best_action


def get_npc_decision(player_pos: list, npc_pos: list) -> str:
    '''Ask Gemini for the NPC's next move; fall back to heuristic on failure.'''
    if _client is None:
        return heuristic_npc_decision(player_pos, npc_pos)

    prompt = (
        f'NPC is at row={npc_pos[0]}, col={npc_pos[1]}. '
        f'Player is at row={player_pos[0]}, col={player_pos[1]}. '
        'You are a primitive AI NPC. Your goal is to keep distance from the player. '
        'Output exactly one of: UP, DOWN, LEFT, RIGHT, STAY. Return only that word.'
    )
    try:
        response = _client.models.generate_content(model=_model_name, contents=prompt)
        decision = response.text.strip().upper().split()[0]
        if decision not in ('UP', 'DOWN', 'LEFT', 'RIGHT', 'STAY'):
            decision = 'STAY'
        return decision
    except Exception as exc:
        print(f'[Gemini] API error: {exc} — using heuristic fallback.')
        return heuristic_npc_decision(player_pos, npc_pos)


def apply_action(grid: list, pos: list, action: str) -> list:
    '''Return a new position after applying the action, if walkable; else same pos.'''
    r, c = pos
    delta = {'UP': (-1, 0), 'DOWN': (1, 0), 'LEFT': (0, -1), 'RIGHT': (0, 1), 'STAY': (0, 0)}
    dr, dc = delta.get(action, (0, 0))
    new_r, new_c = r + dr, c + dc
    if is_walkable(grid, new_r, new_c):
        return [new_r, new_c]
    return pos[:]


# ---------------------------------------------------------------------------
# Input handling
# ---------------------------------------------------------------------------

INPUT_MAP = {
    'w': 'UP',
    'a': 'LEFT',
    's': 'DOWN',
    'd': 'RIGHT',
}


def get_player_action() -> str:
    '''Read one keystroke from stdin and map to an action string.'''
    raw = input('> ').strip().lower()
    if raw == 'q':
        return 'QUIT'
    return INPUT_MAP.get(raw, 'STAY')


# ---------------------------------------------------------------------------
# Game loop
# ---------------------------------------------------------------------------

def run_demo():
    '''Main game loop for the PocketPy AI NPC demo.'''
    grid = make_grid(GRID_WIDTH, GRID_HEIGHT)

    # Spawn player and NPC at sensible starting positions
    player_pos = [GRID_HEIGHT // 2, GRID_WIDTH // 4]
    npc_pos    = [GRID_HEIGHT // 2, (GRID_WIDTH * 3) // 4]
    npc_action = 'STAY'
    turn = 0

    print('Starting PocketPy AI NPC Demo...')
    print('Press Enter to begin.')
    input()

    while True:
        render_grid(grid, player_pos, npc_pos, npc_action, turn)

        player_cmd = get_player_action()
        if player_cmd == 'QUIT':
            print('Thanks for playing!')
            break

        # Move player
        player_pos = apply_action(grid, player_pos, player_cmd)
        turn += 1

        # NPC decision (every DECISION_INTERVAL turns)
        if turn % DECISION_INTERVAL == 0:
            npc_action = get_npc_decision(player_pos, npc_pos)

        # Move NPC
        npc_pos = apply_action(grid, npc_pos, npc_action)

        # Collision detection
        if player_pos == npc_pos:
            render_grid(grid, player_pos, npc_pos, npc_action, turn)
            print('  The NPC caught you! Game over.')
            break


if __name__ == '__main__':
    run_demo()
