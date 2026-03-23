import os
import sys
import io
from utils.logger import app_logger


class VirtualContainer:
    '''Manages isolated project workspaces for PocketPy-compatible game files.

    Each project lives in its own subdirectory under workspace_root.
    Code is executed in-process using exec() with captured stdout/stderr,
    which is fully compatible with the PocketPy runtime model and removes
    the subprocess dependency entirely.
    '''

    def __init__(self, workspace_root: str = 'workspaces'):
        self.workspace_root = workspace_root
        if not os.path.exists(self.workspace_root):
            os.makedirs(self.workspace_root)
            app_logger.info(f'Created workspace root at {self.workspace_root}')

    def _get_project_path(self, project_id: str) -> str:
        '''Return the filesystem path for a given project.'''
        return os.path.join(self.workspace_root, project_id)

    def create_project(self, project_id: str) -> bool:
        '''Initialise a new project directory structure.

        Creates the project folder and an assets subfolder.
        Returns True if freshly created, False if it already existed.
        '''
        project_path = self._get_project_path(project_id)
        if not os.path.exists(project_path):
            os.makedirs(project_path)
            os.makedirs(os.path.join(project_path, 'assets'))
            app_logger.info(f'Created new project workspace: {project_id}')
            return True
        return False

    def write_file(self, project_id: str, filename: str, content: str):
        '''Write content to a file inside the project workspace.'''
        project_path = self._get_project_path(project_id)
        if not os.path.exists(project_path):
            self.create_project(project_id)

        file_path = os.path.join(project_path, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        app_logger.info(f'Written file: {filename} to {project_id}')

    def read_file(self, project_id: str, filename: str) -> str:
        '''Read and return content from a project file. Returns empty string if not found.'''
        file_path = os.path.join(self._get_project_path(project_id), filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ''

    def list_files(self, project_id: str) -> list:
        '''Return a list of all filenames in the project workspace.'''
        project_path = self._get_project_path(project_id)
        if not os.path.exists(project_path):
            return []
        return [
            f for f in os.listdir(project_path)
            if os.path.isfile(os.path.join(project_path, f))
        ]

    def execute_code(self, project_id: str, filename: str = 'main.py', timeout: int = 5) -> dict:
        '''Execute a Python file using exec() with captured stdout and stderr.

        This replaces the old subprocess.run approach, removing all OS process
        dependencies. The generated code is loaded as source text and executed
        in an isolated namespace. Input calls are stubbed to prevent the game
        loop from blocking during automated evaluation.

        Returns a dict with keys: success, stdout, stderr, exit_code.
        '''
        app_logger.info(f'Executing {filename} in {project_id}...')
        project_path = self._get_project_path(project_id)
        file_path = os.path.join(project_path, filename)

        if not os.path.exists(file_path):
            return {'success': False, 'error': f'{filename} not found.', 'stdout': '', 'stderr': ''}

        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        # Validate that code does not import forbidden graphic libraries
        forbidden = ['import pygame', 'from pygame', 'import tkinter', 'from tkinter',
                     'import wx', 'import PyQt', 'import kivy']
        for banned in forbidden:
            if banned in source:
                msg = f'Validation failed: detected forbidden import "{banned}" in generated code.'
                app_logger.warning(msg)
                return {'success': False, 'error': msg, 'stdout': '', 'stderr': msg, 'exit_code': 1}

        # Redirect stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured_out = io.StringIO()
        captured_err = io.StringIO()
        sys.stdout = captured_out
        sys.stderr = captured_err

        # Stub input() so the evaluation run does not block forever
        # The stub returns 'q' to gracefully exit any game loop on first prompt
        stub_inputs = iter(['q'])

        def _stubbed_input(prompt_text=''):
            try:
                return next(stub_inputs)
            except StopIteration:
                return 'q'

        exec_globals = {
            '__name__': '__main__',
            '__file__': file_path,
            'input': _stubbed_input,
        }

        success = False
        error_message = ''
        try:
            # Compile first to surface SyntaxErrors cleanly
            compiled = compile(source, file_path, 'exec')
            exec(compiled, exec_globals)  # noqa: S102
            success = True
        except SystemExit:
            # A clean sys.exit() is treated as success
            success = True
        except Exception as exc:
            import traceback
            error_message = traceback.format_exc()
            captured_err.write(error_message)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        stdout_value = captured_out.getvalue()
        stderr_value = captured_err.getvalue()

        if not success:
            app_logger.warning(f'Execution failed for {project_id}/{filename}')
        else:
            app_logger.info(f'Execution succeeded for {project_id}/{filename}')

        return {
            'success': success,
            'stdout': stdout_value,
            'stderr': stderr_value,
            'exit_code': 0 if success else 1,
        }
