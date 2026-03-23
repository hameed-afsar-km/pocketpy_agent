import os
import io
import sys
import shutil
from utils.logger import app_logger

class VirtualContainer:
    '''Professional Multi-File Workspace Manager for PocketPy projects.

    Each project is structured as a proper Python package:
    - workspaces/project_id/
        - main.py (Entry point)
        - src/ (Package logic)
            - __init__.py
            - engine.py
            - renderer.py
            - ...
        - assets/ (Data files)

    Execution is handled by dynamically importing the entry point into a
    sandboxed namespace.
    '''

    def __init__(self, workspace_root: str = 'workspaces'):
        self.workspace_root = workspace_root
        if not os.path.exists(self.workspace_root):
            os.makedirs(self.workspace_root)

    def _get_project_path(self, project_id: str) -> str:
        return os.path.join(self.workspace_root, project_id)

    def create_project(self, project_id: str) -> bool:
        project_path = self._get_project_path(project_id)
        if not os.path.exists(project_path):
            os.makedirs(project_path)
            os.makedirs(os.path.join(project_path, 'src'))
            os.makedirs(os.path.join(project_path, 'assets'))
            # Create empty __init__.py to make src/ a package
            with open(os.path.join(project_path, 'src', '__init__.py'), 'w') as f:
                f.write('')
            app_logger.info(f'Created multi-file project workspace: {project_id}')
            return True
        return False

    def write_project_files(self, project_id: str, files_dict: dict):
        '''Writes multiple files to the project directory.
        files_dict example: {"main.py": "...", "src/engine.py": "..."}
        '''
        project_path = self._get_project_path(project_id)
        if not os.path.exists(project_path):
            self.create_project(project_id)

        for filename, content in files_dict.items():
            file_path = os.path.join(project_path, filename)
            # Ensure subdirectories exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        app_logger.info(f'Synchronized {len(files_dict)} files for {project_id}')

    def read_file(self, project_id: str, filename: str) -> str:
        file_path = os.path.join(self._get_project_path(project_id), filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ''

    def execute_code(self, project_id: str, filename: str = 'main.py', timeout: int = 5) -> dict:
        '''Multi-file aware execution using subprocess.
        Safely evaluates untrusted code with a strict timeout to prevent infinite loops.
        '''
        app_logger.info(f'Executing multi-file project {project_id}...')
        project_path = os.path.abspath(self._get_project_path(project_id))
        file_path = os.path.join(project_path, filename)

        if not os.path.exists(file_path):
            return {'success': False, 'error': f'{filename} not found.'}

        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        # Input guard (PocketPy constraints)
        forbidden = ['pygame', 'tkinter', 'wx', 'PyQt', 'kivy', 'threading', 'multiprocessing', 'subprocess']
        for banned in forbidden:
            if f'import {banned}' in source or f'from {banned}' in source:
                return {'success': False, 'error': f'Banned library detected: {banned}'}

        import subprocess
        # Pre-seed the input stream with 'q' to naturally exit game loops
        mock_input = b'q\n' * 50

        try:
            # Inject project path so relative imports work inside the subprocess context
            env = dict(os.environ)
            env['PYTHONPATH'] = project_path + os.pathsep + env.get('PYTHONPATH', '')

            result = subprocess.run(
                [sys.executable, file_path],
                input=mock_input,
                capture_output=True,
                timeout=timeout,
                env=env
            )
            success = result.returncode == 0
            return {
                'success': success,
                'stdout': result.stdout.decode('utf-8', errors='replace'),
                'stderr': result.stderr.decode('utf-8', errors='replace')
            }
        except subprocess.TimeoutExpired as e:
            return {
                'success': False,
                'stdout': e.stdout.decode('utf-8', errors='replace') if e.stdout else '',
                'stderr': f'Execution timed out after {timeout} seconds. The game loop might be infinite or missing a quit condition.'
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Execution failed: {e}'
            }
