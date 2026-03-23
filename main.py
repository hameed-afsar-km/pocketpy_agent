import sys
import os

# Set up project root in path for top-level module discovery
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from agent.core import CoreAgent
from memory.memory_manager import MemoryManager

BANNER = r'''
╔══════════════════════════════════════════════════════════╗
║   ____           _        _   ____        _              ║
║  |  _ \ ___  ___| | _____| |_|  _ \ _  _| |             ║
║  | |_) / _ \/ __| |/ / _ \ __| |_) | | | | |             ║
║  |  __/ (_) \__ \   <  __/ |_|  __/| |_| |_|             ║
║  |_|   \___/|___/_|\_\___|\__|_|    \__, (_)             ║
║                                     |___/                ║
║   PocketPy Vibe Coding Agent  🐍                         ║
║   GSoC 2026 · Python Software Foundation · PocketPy      ║
║   Generates text/grid games for the PocketPy runtime     ║
╚══════════════════════════════════════════════════════════╝
'''

MENU = '''
  ┌─────────────────────────────────────────────────────┐
  │  1. New Project      Generate a game from a prompt  │
  │  2. Continue Project Improve an existing project    │
  │  3. List Projects    Browse all projects            │
  │  4. Project History  Iteration log for a project   │
  │  5. View Code        Preview latest generated code  │
  │  6. Update API Key   Hot-swap Gemini API key        │
  │  7. Exit                                            │
  └─────────────────────────────────────────────────────┘
'''

SEP = '─' * 58


def _sep():
    print(SEP)


def display_menu():
    '''Print the main navigation menu.'''
    print(MENU)


def _list_projects(memory: MemoryManager):
    '''Display a table of all known projects with status and timestamps.'''
    projects = memory.list_projects()
    if not projects:
        print('\n  No projects found yet. Create one with option 1.\n')
        return

    print(f'\n  {"ID":<28} {"Status":<16} {"Last Updated"}')
    _sep()
    for pid in projects:
        summary = memory.get_project_summary(pid)
        pid_display = pid[:26] + '..' if len(pid) > 28 else pid
        status = summary['status']
        ts = summary['last_updated'][:19] if summary['last_updated'] != 'never' else 'never'
        print(f'  {pid_display:<28} {status:<16} {ts}')
    print(f'\n  Total: {len(projects)} project(s)\n')


def _show_history(memory: MemoryManager, project_id: str):
    '''Print the full iteration history for a single project.'''
    history = memory.retrieve_history(project_id)
    entries = history.get('history', [])
    if not entries:
        print(f'\n  No history found for "{project_id}".\n')
        return

    summary = memory.get_project_summary(project_id)
    print(f'\n  Project  : {project_id}')
    print(f'  Status   : {summary["status"]}')
    print(f'  Entries  : {len(entries)}')
    _sep()
    for idx, entry in enumerate(entries):
        ts = entry.get('timestamp', 'unknown')[:19]
        action = entry.get('action', 'unknown')
        iteration = entry.get('iteration', '?')
        snippet = ''
        if 'prompt_used' in entry:
            snippet = f'  prompt: {entry["prompt_used"][:40]}…'
        if 'error_log' in entry:
            first_line = entry['error_log'].split('\n')[0][:50]
            snippet = f'  err: {first_line}'
        print(f'  [{idx:02d}] iter={iteration:<3} | {action:<12} | {ts}{snippet}')
    print()


def _preview_code(memory: MemoryManager, project_id: str):
    '''Display the latest code for a project in a readable bordered block.'''
    code = memory.get_latest_code(project_id)
    if not code:
        print(f'\n  No code saved for "{project_id}" yet.\n')
        return
    lines = code.splitlines()
    print(f'\n  Code for "{project_id}"  ({len(lines)} lines)\n')
    _sep()
    # Show first 60 lines to avoid flooding the terminal
    MAX_LINES = 60
    for line in lines[:MAX_LINES]:
        print(f'  {line}')
    if len(lines) > MAX_LINES:
        print(f'\n  … and {len(lines) - MAX_LINES} more lines.')
        workspace_path = os.path.join('workspaces', project_id, 'main.py')
        print(f'  Open the full file at: {workspace_path}')
    _sep()
    print()


def main():
    '''Entry point for the PocketPy Vibe Coding Agent CLI.'''
    print(BANNER)

    custom_gemini_key = input('  Gemini API Key (press Enter to use .env value): ').strip()
    if not custom_gemini_key:
        custom_gemini_key = None

    print('\n  Initialising agent…')
    agent = CoreAgent(gemini_api_key=custom_gemini_key)
    memory = MemoryManager()
    print('  Agent ready.\n')

    while True:
        display_menu()
        choice = input('  Select [1-7]: ').strip()

        if choice == '1':
            project_id = input('  Project name/ID: ').strip()
            prompt = input('  Describe your game: ').strip()
            if project_id and prompt:
                print(f'\n  Generating "{project_id}" — this may take a moment…\n')
                agent.new_project(project_id, prompt)
            else:
                print('  Project name and prompt are both required.\n')

        elif choice == '2':
            projects = memory.list_projects()
            if projects:
                _list_projects(memory)
            project_id = input('  Project name/ID to improve: ').strip()
            instructions = input('  Describe the improvement: ').strip()
            if project_id and instructions:
                print(f'\n  Improving "{project_id}" — this may take a moment…\n')
                agent.improve_project(project_id, instructions)
            else:
                print('  Project name and improvement instructions are both required.\n')

        elif choice == '3':
            _list_projects(memory)

        elif choice == '4':
            projects = memory.list_projects()
            if projects:
                _list_projects(memory)
            project_id = input('  Project name/ID: ').strip()
            if project_id:
                _show_history(memory, project_id)

        elif choice == '5':
            projects = memory.list_projects()
            if projects:
                _list_projects(memory)
            project_id = input('  Project name/ID: ').strip()
            if project_id:
                _preview_code(memory, project_id)

        elif choice == '6':
            new_key = input('  New Gemini API Key: ').strip()
            if new_key:
                if hasattr(agent.ai_provider, 'update_api_key'):
                    agent.ai_provider.update_api_key(new_key)
                    print('  ✓ API key updated.\n')
                else:
                    print('  Current provider does not support dynamic key updates.\n')
            else:
                print('  No key entered — unchanged.\n')

        elif choice == '7':
            print('\n  Goodbye! Happy hacking with PocketPy 🐍\n')
            break

        else:
            print('  Invalid option — enter a number 1–7.\n')


if __name__ == '__main__':
    main()
