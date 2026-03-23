import os
from openai import OpenAI
from dotenv import load_dotenv
from ai.base_provider import BaseProvider
from ai.prompts import SYSTEM_GENERATE, SYSTEM_DEBUG, SYSTEM_IMPROVE
from utils.logger import app_logger

load_dotenv()


class OpenAIProvider(BaseProvider):
    '''AI provider backed by OpenAI, generating PocketPy-compatible text games.'''

    def __init__(self, model: str = 'gpt-4o'):
        self.model = model
        self.client = OpenAI()
        app_logger.info(f'Initialized OpenAIProvider with model {self.model}')

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        '''Call the OpenAI chat completions API.'''
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            app_logger.error(f'OpenAI API Error: {e}')
            raise e

    def _extract_code(self, text: str) -> str:
        '''Extract the first Python code block from a markdown-formatted response.'''
        if '```python' in text:
            parts = text.split('```python')
            if len(parts) > 1:
                return parts[1].split('```')[0].strip()
        elif '```' in text:
            parts = text.split('```')
            if len(parts) > 1:
                return parts[1].strip()
        return text.strip()

    def generate_code(self, prompt: str) -> str:
        '''Generate a complete PocketPy-compatible text game from a natural language prompt.'''
        response = self._call_api(SYSTEM_GENERATE, prompt)
        return self._extract_code(response)

    def debug_code(self, error_log: str, code: str) -> str:
        '''Fix broken PocketPy game code using the provided error traceback.'''
        user = f'Code:\n{code}\n\nError Log:\n{error_log}\n\nFix the bug and return the full script.'
        response = self._call_api(SYSTEM_DEBUG, user)
        return self._extract_code(response)

    def improve_code(self, context: dict) -> str:
        '''Improve an existing PocketPy game given improvement instructions.'''
        user = (
            f"Improvement instructions: {context.get('instructions', '')}\n"
            f"Current Code:\n{context.get('code', '')}"
        )
        response = self._call_api(SYSTEM_IMPROVE, user)
        return self._extract_code(response)
