import os
import json
from google import genai
from dotenv import load_dotenv
from ai.base_provider import BaseProvider
from ai.prompts import SYSTEM_GENERATE, SYSTEM_DEBUG, SYSTEM_IMPROVE
from utils.logger import app_logger

load_dotenv()

class GeminiProvider(BaseProvider):
    '''AI provider for Google Gemini. Generates multi-file PocketPy projects.'''

    def __init__(self, model: str = 'gemini-2.5-flash', api_key: str = None):
        self.model_name = model
        resolved_key = api_key or os.getenv('GEMINI_API_KEY')
        if not resolved_key:
            raise ValueError('GEMINI_API_KEY environment variable is required')
        self.client = genai.Client(api_key=resolved_key)
        app_logger.info(f'Initialized Multi-File GeminiProvider with model {self.model_name}')

    def update_api_key(self, api_key: str):
        if api_key:
            self.client = genai.Client(api_key=api_key)

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config={'system_instruction': system_prompt}
            )
            return response.text
        except Exception as e:
            app_logger.error(f'Gemini API Error: {e}')
            raise e

    def _extract_json(self, text: str) -> dict:
        '''Extract the first JSON block from a markdown-formatted response or raw text.'''
        # Find JSON boundaries
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
        # Fallback empty project structure
        return {"main.py": "print('Failed to parse AI output as JSON')", "src/__init__.py": ""}

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
