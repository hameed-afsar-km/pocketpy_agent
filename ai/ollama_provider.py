import requests
import json
from ai.base_provider import BaseProvider
from ai.prompts import SYSTEM_GENERATE, SYSTEM_DEBUG, SYSTEM_IMPROVE
from utils.logger import app_logger


class OllamaProvider(BaseProvider):
    '''AI provider backed by a local Ollama server, generating multi-file PocketPy projects.'''

    def __init__(self, model: str = 'llama3', base_url: str = 'http://localhost:11434'):
        self.model = model
        self.base_url = base_url
        app_logger.info(f'Initialized OllamaProvider with model {self.model} at {self.base_url}')

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        try:
            payload = {
                'model': self.model,
                'format': 'json',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'stream': False
            }
            response = requests.post(f'{self.base_url}/api/chat', json=payload)
            response.raise_for_status()
            return response.json()['message']['content']
        except Exception as e:
            app_logger.error(f'Ollama API Error: {e}')
            raise e

    def generate_code(self, prompt: str) -> dict:
        response = self._call_api(SYSTEM_GENERATE, f"Generate a project: {prompt}")
        return self._extract_json(response)

    def debug_code(self, error_log: str, project_files: dict) -> dict:
        user = f'Project Files JSON:\n{json.dumps(project_files)}\n\nError Log:\n{error_log}'
        response = self._call_api(SYSTEM_DEBUG, user)
        return self._extract_json(response)

    def improve_code(self, context: dict) -> dict:
        user = f'Improvement instruction: {context.get("instructions", "")}\n\nExisting Files JSON: {json.dumps(context.get("project_files", {}))}'
        response = self._call_api(SYSTEM_IMPROVE, user)
        return self._extract_json(response)
