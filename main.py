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
║   Professional Multi-File Project Mode                   ║
╚══════════════════════════════════════════════════════════╝
'''

MENU = '''
  ┌─────────────────────────────────────────────────────┐
  │  1. New Project      Generate a game from a prompt  │
  │  2. Continue Project Improve an existing project    │
  │  3. Run Project      Run any project                │
  │  4. List Projects    Browse all projects            │
  │  5. Project History  Iteration log for a project    │
  │  6. View Code        Preview latest generated code  │
  │  7. Update API Key   Hot-swap Gemini API key        │
  │  8. Exit                                            │
  └─────────────────────────────────────────────────────┘
'''

SEP = '─' * 58

def display_menu():
    print(MENU)

def _list_projects(memory: MemoryManager):
    projects = memory.list_projects()
    if not projects:
        print('\n  No projects found yet. Create one with option 1.\n')
        return []
    
    print(f'\n  {"ID":<4} {"Project ID":<28} {"Status":<12} {"Last Updated"}')
    print('  ' + '─' * 58)
    for idx, pid in enumerate(projects):
        summary = memory.get_project_summary(pid)
        status = summary['status']
        ts = summary['last_updated'][:19] if summary['last_updated'] != 'never' else 'never'
        print(f'  {idx+1:<4} {pid:<28} {status:<12} {ts}')
    print('\n')
    return projects

def _show_project_history(memory: MemoryManager, project_id: str):
    history = memory.retrieve_history(project_id)
    entries = history.get('history', [])
    if not entries:
        print(f'\n  No history for "{project_id}".\n')
        return

    print(f'\n  Project Activity Log: {project_id}')
    print('  ' + '─' * 58)
    for idx, entry in enumerate(entries):
        ts = entry.get('timestamp', 'unknown')[:19]
        action = entry.get('action', 'unknown')
        iteration = entry.get('iteration', '?')
        print(f'  [{idx:02d}] iter={iteration:<2} | {action:<10} | {ts}')
    print('\n  Enter code view (option 6) to see the source.\n')

def main():
    print(BANNER)
    custom_gemini_key = input('  Optional Gemini API Key (Enter to skip): ').strip()
    agent = CoreAgent(gemini_api_key=custom_gemini_key if custom_gemini_key else None)
    memory = MemoryManager()

    while True:
        display_menu()
        choice = input('  Select [1-8]: ').strip()

        if choice == '1':
            project_id = input('  Project name: ').strip()
            prompt = input('  Describe your game (professional multi-file): ').strip()
            if project_id and prompt:
                print(f'\n  Agent starting Multi-File workflow for "{project_id}"...\n')
                agent.new_project(project_id, prompt)
            else:
                print('  Name and prompt required.\n')

        elif choice == '2':
            projects = _list_projects(memory)
            if projects:
                idx = input('  Select Project # to improve (or Enter for manually typed ID): ').strip()
                if idx.isdigit() and 1 <= int(idx) <= len(projects):
                    project_id = projects[int(idx)-1]
                else:
                    project_id = input('  Project name/ID: ').strip()
                instructions = input('  Describe improvement: ').strip()
                if project_id and instructions:
                    print(f'\n  Agent starting Multi-File improvement for "{project_id}"...\n')
                    agent.improve_project(project_id, instructions)

        elif choice == '3':
            projects = _list_projects(memory)
            if projects:
                idx = input('  Enter Project # to run (or Enter to cancel): ').strip()
                if idx.isdigit() and 1 <= int(idx) <= len(projects):
                    project_id = projects[int(idx)-1]
                    workspace_path = os.path.join('workspaces', project_id, 'main.py')
                    if os.path.exists(workspace_path):
                        print(f'\n  ▶ Launching {project_id}...\n')
                        # Use subprocess to run it interactively in the current terminal 
                        import subprocess
                        subprocess.run([sys.executable, workspace_path])
                        print(f'\n  ■ Game closed.\n')
                    else:
                        print(f'\n  Cannot find entry point at: {workspace_path}\n')

        elif choice == '4':
            _list_projects(memory)

        elif choice == '5':
            projects = _list_projects(memory)
            if projects:
                idx = input('  Enter Project # to view detailed history (or Enter to go back): ').strip()
                if idx.isdigit() and 1 <= int(idx) <= len(projects):
                    _show_project_history(memory, projects[int(idx)-1])

        elif choice == '6':
            projects = _list_projects(memory)
            if projects:
                idx = input('  Enter Project # to view code: ').strip()
                if idx.isdigit() and 1 <= int(idx) <= len(projects):
                    project_id = projects[int(idx)-1]
                    print(f'\n  Previewing entry point for {project_id}:')
                    print('  ' + '─' * 58)
                    print(f'  Full project is at: workspaces/{project_id}/')
                    print(f'  Check src/engine.py for game logic.')
                    print('  ' + '─' * 58 + '\n')

        elif choice == '7':
            new_key = input('  New Gemini API Key: ').strip()
            if new_key and hasattr(agent.ai_provider, 'update_api_key'):
                agent.ai_provider.update_api_key(new_key)
                print('  ✓ Updated Key.\n')

        elif choice == '8':
            print('\n  Goodbye! Happy Coding.\n')
            break

        else:
            print('  Invalid option.\n')

if __name__ == '__main__':
    main()
