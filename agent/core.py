import json
import os
import sys

# Add project root to path for sibling package discovery
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from .planner import Planner
from .executor import Executor
from ai.openai_provider import OpenAIProvider
from ai.ollama_provider import OllamaProvider
from ai.gemini_provider import GeminiProvider
from container.virtual_container import VirtualContainer
from memory.memory_manager import MemoryManager
from utils.logger import app_logger
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class CoreAgent:
    '''Top-level orchestrator for the PocketPy Vibe Coding Agent.
    Now supports multi-file project generation and evaluation.
    '''

    def __init__(self, config_path: str = 'config.json', gemini_api_key: str = None):
        # Resolve config path relative to project root when not absolute
        if not os.path.exists(config_path):
            config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', config_path))

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.provider_name = self.config.get('provider', 'gemini')
        self.max_iterations = self.config.get('max_iterations', 5)
        self.timeout = self.config.get('execution_timeout', 5)

        if self.provider_name == 'openai':
            self.ai_provider = OpenAIProvider(model=self.config.get('openai_model', 'gpt-4o'))
        elif self.provider_name == 'gemini':
            self.ai_provider = GeminiProvider(
                model=self.config.get('gemini_model', 'gemini-2.5-flash'),
                api_key=gemini_api_key
            )
        else:
            self.ai_provider = OllamaProvider(model=self.config.get('ollama_model', 'llama3'))

        self.container = VirtualContainer()
        self.memory = MemoryManager()
        self.planner = Planner(self.ai_provider)
        self.executor = Executor(
            self.container,
            max_iterations=self.max_iterations,
            timeout=self.timeout
        )

    def new_project(self, project_id: str, prompt: str) -> dict:
        app_logger.info(f"Starting multi-file project '{project_id}'")
        self.container.create_project(project_id)
        plan = self.planner.plan_project(prompt)
        return self._run_loop(project_id, plan['compiled_prompt'], existing_project=None, mode='new')

    def improve_project(self, project_id: str, instructions: str) -> dict:
        app_logger.info(f"Improving multi-file project '{project_id}'")
        self.container.create_project(project_id)
        existing_project = {} # Logic to build a proper project files dict from memory needed here
        return self._run_loop(project_id, instructions, existing_project=existing_project, mode='improve')

    def _run_loop(self, project_id: str, prompt: str, existing_project: dict, mode: str) -> dict:
        current_project_files = existing_project or {}
        last_error = ''

        for i in range(self.max_iterations):
            iteration = i + 1
            app_logger.info(f'=== Iteration {iteration}/{self.max_iterations} ===')

            if iteration == 1:
                if mode == 'improve':
                    current_project_files = self.ai_provider.improve_code({
                        'instructions': prompt,
                        'project_files': current_project_files
                    })
                    action_label = 'improved'
                else:
                    current_project_files = self.ai_provider.generate_code(prompt)
                    action_label = 'generated'
            else:
                current_project_files = self.ai_provider.debug_code(last_error, current_project_files)
                action_label = 'debugged'

            # Write multi-file structure
            self.container.write_project_files(project_id, current_project_files)
            
            # Save state
            self.memory.save_state(project_id, {
                'iteration': iteration,
                'action': action_label,
                'files': list(current_project_files.keys()),
                'status': 'validating'
            })

            eval_result = self.executor.run_and_evaluate(project_id, 'main.py')
            if eval_result['success']:
                app_logger.info(f'Success on iteration {iteration}!')
                self._report_success(project_id)
                return current_project_files

            last_error = eval_result['log']
            self.memory.save_state(project_id, {
                'iteration': iteration,
                'action': 'error',
                'error_log': last_error[:1000]
            })

        app_logger.warning(f'Exhausted {self.max_iterations} iterations without clean execution.')
        self._report_best_effort(project_id)
        return current_project_files

    def _report_success(self, project_id: str):
        workspace_path = os.path.join('workspaces', project_id)
        print(f'\n{"=" * 60}')
        print(f'  ✓ Multi-file project ready: {project_id}')
        print(f'  ✎ Location   : {workspace_path}')
        print(f'  ▶ Entry Point : python {workspace_path}/main.py')
        print(f'{"=" * 60}\n')

    def _report_best_effort(self, project_id: str):
        workspace_path = os.path.join('workspaces', project_id)
        print(f'\n{"=" * 60}')
        print(f'  ⚠ Best-effort project saved for: {project_id}')
        print(f'  ✎ Location   : {workspace_path}')
        print(f'  ℹ Review src/engine.py for logic improvements.')
        print(f'{"=" * 60}\n')
