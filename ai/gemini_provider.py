import os
from google import genai
from dotenv import load_dotenv
from ai.base_provider import BaseProvider
from ai.prompts import SYSTEM_GENERATE, SYSTEM_DEBUG, SYSTEM_IMPROVE
from utils.logger import app_logger

# Load environment variables from .env
load_dotenv()


class GeminiProvider(BaseProvider):
    '''AI provider backed by Google Gemini, generating PocketPy-compatible text games.'''

    def __init__(self, model: str = 'gemini-2.5-flash', api_key: str = None):
        self.model_name = model
        # Use provided key or fall back to environment variable
        resolved_key = api_key or os.getenv('GEMINI_API_KEY')
        if resolved_key is None:
            app_logger.error('GEMINI_API_KEY not found in environment or arguments')
            raise ValueError('GEMINI_API_KEY environment variable is required')

        self.client = genai.Client(api_key=resolved_key)
        app_logger.info(f'Initialized GeminiProvider with model {self.model_name}')

    def update_api_key(self, api_key: str):
        '''Hot-swap the Gemini API key without restarting the agent.'''
        if api_key:
            self.client = genai.Client(api_key=api_key)
            app_logger.info('Gemini API key updated successfully')

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        '''Call the Gemini generate_content API with system and user prompts.'''
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
