import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from ai.base_provider import BaseProvider
from ai.prompts import SYSTEM_GENERATE, SYSTEM_DEBUG, SYSTEM_IMPROVE
from utils.logger import app_logger

load_dotenv()


class OpenAIProvider(BaseProvider):
    '''AI provider backed by OpenAI. Generates multi-file PocketPy projects.'''

    def __init__(self, model: str = 'gpt-4o'):
        self.model = model
        self.client = OpenAI()
        app_logger.info(f'Initialized OpenAIProvider with model {self.model}')

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={ "type": "json_object" },
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            app_logger.error(f'OpenAI API Error: {e}')
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
