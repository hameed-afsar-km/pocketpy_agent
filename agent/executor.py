import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import app_logger


class Executor:
    '''Orchestrates code execution and evaluates whether generated games are valid.

    Uses VirtualContainer.execute_code() which runs code via exec() — no subprocess,
    fully PocketPy-runtime-compatible.
    '''

    def __init__(self, container, max_iterations: int = 5, timeout: int = 5):
        self.container = container
        self.max_iterations = max_iterations
        self.timeout = timeout

    def run_and_evaluate(self, project_id: str, main_file: str = 'main.py') -> dict:
        '''Execute the game file and return a structured evaluation result.

        Returns:
            dict with keys:
                success (bool): True if the code ran without errors.
                log (str): Human-readable summary of stdout and stderr for debugging.
        '''
        result = self.container.execute_code(project_id, filename=main_file, timeout=self.timeout)

        if result.get('success'):
            stdout = result.get('stdout', '')
            app_logger.info(f'Evaluation passed for {project_id}/{main_file}')
            return {'success': True, 'log': f'OK\nSTDOUT:\n{stdout}'}

        stderr = result.get('error') or result.get('stderr', '')
        stdout = result.get('stdout', '')
        log = f'STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}'
        app_logger.warning(f'Evaluation failed for {project_id}/{main_file}')
        return {'success': False, 'log': log}
