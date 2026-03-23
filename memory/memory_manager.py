import os
import json
from datetime import datetime
from utils.logger import app_logger


class MemoryManager:
    '''Persistent JSON-based storage for project history, code versions, and iteration logs.

    Each project gets its own JSON file in the data_dir. History entries are
    appended chronologically, making it easy to replay or inspect any iteration.
    '''

    def __init__(self, data_dir: str = 'memory_data'):
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            app_logger.info(f'Created memory directory at {self.data_dir}')

    def _get_project_file(self, project_id: str) -> str:
        '''Return the JSON file path for a given project.'''
        return os.path.join(self.data_dir, f'{project_id}.json')

    def list_projects(self) -> list:
        '''Return a list of all project IDs that have a history file.'''
        if not os.path.exists(self.data_dir):
            return []
        projects = []
        for fname in sorted(os.listdir(self.data_dir)):
            if fname.endswith('.json'):
                projects.append(fname[:-5])  # strip .json
        return projects

    def retrieve_history(self, project_id: str) -> dict:
        '''Return the full history dict for a project, or an empty skeleton if not found.'''
        file_path = self._get_project_file(project_id)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'project_id': project_id, 'history': []}

    def save_state(self, project_id: str, state_data: dict):
        '''Append a new state entry to the project history.

        Automatically stamps each entry with an ISO timestamp.
        '''
        file_path = self._get_project_file(project_id)
        current_data = self.retrieve_history(project_id)
        state_data['timestamp'] = datetime.now().isoformat()
        current_data['history'].append(state_data)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, indent=4)
        app_logger.info(f'Saved state for project: {project_id}')

    def get_latest_code(self, project_id: str) -> str:
        '''Return the most recently saved code string for a project.'''
        history = self.retrieve_history(project_id).get('history', [])
        for entry in reversed(history):
            if 'code' in entry and entry['code'].strip():
                return entry['code']
        return ''

    def get_project_summary(self, project_id: str) -> dict:
        '''Return a compact summary of a project suitable for listing.

        Returns a dict with: project_id, total_iterations, last_action, last_updated, status.
        '''
        history = self.retrieve_history(project_id).get('history', [])
        if not history:
            return {'project_id': project_id, 'total_iterations': 0,
                    'last_action': 'none', 'last_updated': 'never', 'status': 'empty'}

        last = history[-1]
        # Determine overall status
        actions = [e.get('action', '') for e in history]
        if 'generated' in actions and 'error' not in actions[-1]:
            status = '✓ success'
        elif any(a in actions for a in ('generated', 'debugged')):
            status = '⚠ in progress'
        else:
            status = '✗ failed'

        return {
            'project_id': project_id,
            'total_iterations': len([e for e in history if e.get('iteration')]),
            'last_action': last.get('action', 'unknown'),
            'last_updated': last.get('timestamp', 'unknown'),
            'status': status,
        }
