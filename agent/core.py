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

    Coordinates the AI provider, project container, memory manager, planner,
    and executor to generate, debug, and iteratively improve PocketPy-compatible
    text-based games from natural language prompts.

    The generate loop runs up to max_iterations rounds:
      - Iteration 1: AI generates fresh code from the compiled prompt.
      - Iterations 2-N: AI debugs using the previous error log.
    For "Continue Project" flows the caller pre-loads existing code and passes
    an improvement prompt; the loop calls improve_code on the first step.
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def new_project(self, project_id: str, prompt: str) -> str:
        '''Generate a brand-new PocketPy game from scratch.

        Compiles the user prompt into a structured spec, then runs the
        generate → evaluate → debug loop up to max_iterations times.
        Returns the last generated code string.
        '''
        app_logger.info(f"Starting new project '{project_id}'")
        self.container.create_project(project_id)
        plan = self.planner.plan_project(prompt)
        return self._run_loop(project_id, plan['compiled_prompt'], existing_code=None, mode='new')

    def improve_project(self, project_id: str, instructions: str) -> str:
        '''Improve an existing project using the AI's improve_code pipeline.

        Loads the latest saved code from memory, then runs the
        improve → evaluate → debug loop up to max_iterations times.
        Returns the last generated code string.
        '''
        app_logger.info(f"Improving project '{project_id}'")
        self.container.create_project(project_id)
        existing_code = self.memory.get_latest_code(project_id)
        if not existing_code:
            app_logger.warning(f"No existing code found for '{project_id}' — generating fresh.")
            plan = self.planner.plan_project(instructions)
            return self._run_loop(project_id, plan['compiled_prompt'], existing_code=None, mode='new')

        return self._run_loop(project_id, instructions, existing_code=existing_code, mode='improve')

    # ------------------------------------------------------------------
    # Internal loop
    # ------------------------------------------------------------------

    def _run_loop(self, project_id: str, prompt: str, existing_code: str, mode: str) -> str:
        '''Core generate-evaluate-debug loop shared by new_project and improve_project.

        Args:
            project_id: Unique project identifier.
            prompt:     Compiled prompt (new) or improvement instructions (improve).
            existing_code: Pre-loaded code string for improve mode; None for new.
            mode:       'new' | 'improve'
        '''
        current_code = existing_code or ''
        last_error = ''

        for i in range(self.max_iterations):
            iteration = i + 1
            app_logger.info(f'=== Iteration {iteration}/{self.max_iterations} ===')

            if iteration == 1:
                if mode == 'improve':
                    current_code = self.ai_provider.improve_code({
                        'instructions': prompt,
                        'code': current_code
                    })
                    action_label = 'improved'
                else:
                    current_code = self.ai_provider.generate_code(prompt)
                    action_label = 'generated'
            else:
                # All subsequent iterations are debug passes regardless of mode
                current_code = self.ai_provider.debug_code(last_error, current_code)
                action_label = 'debugged'

            self.container.write_file(project_id, 'main.py', current_code)
            self.memory.save_state(project_id, {
                'iteration': iteration,
                'action': action_label,
                'code': current_code,
                'prompt_used': prompt[:200],  # store a snippet for auditing
            })

            eval_result = self.executor.run_and_evaluate(project_id, 'main.py')
            if eval_result['success']:
                app_logger.info(f'✓ Evaluation passed on iteration {iteration}')
                self._report_success(project_id)
                return current_code

            last_error = eval_result['log']
            app_logger.warning(f'Iteration {iteration} failed — scheduling debug pass')
            self.memory.save_state(project_id, {
                'iteration': iteration,
                'action': 'error',
                'error_log': last_error[:1000],  # cap log size in memory
            })

        app_logger.warning(f'Exhausted {self.max_iterations} iterations without clean execution.')
        self._report_best_effort(project_id)
        return current_code

    # ------------------------------------------------------------------
    # Status reporters (no inline code dump)
    # ------------------------------------------------------------------

    def _report_success(self, project_id: str):
        '''Print a clean success banner — path only, no raw code dump.'''
        workspace_path = os.path.join('workspaces', project_id, 'main.py')
        print(f'\n{"=" * 60}')
        print(f'  ✓  Game ready: {project_id}')
        print(f'  ✎  File      : {workspace_path}')
        print(f'  ▶  Run with  : python {workspace_path}')
        print(f'  📋 Use option 4 from the menu to preview the code.')
        print(f'{"=" * 60}\n')

    def _report_best_effort(self, project_id: str):
        '''Print a best-effort banner when evaluation never fully passed.'''
        workspace_path = os.path.join('workspaces', project_id, 'main.py')
        print(f'\n{"=" * 60}')
        print(f'  ⚠  Best-effort result saved for: {project_id}')
        print(f'  ✎  File      : {workspace_path}')
        print(f'  ℹ  Evaluation did not fully pass — manual review may help.')
        print(f'  📋 Use option 4 from the menu to preview the code.')
        print(f'  🔁 Use option 2 to continue improving this project.')
        print(f'{"=" * 60}\n')
