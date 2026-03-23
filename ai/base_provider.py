import json
from abc import ABC, abstractmethod


class BaseProvider(ABC):
    '''Abstract base class for all AI providers.

    All providers must implement code generation, debugging, and improvement
    for PocketPy-compatible, multi-file Python packages. No Pygame or
    graphical dependencies are permitted in generated code.
    '''

    def _extract_json(self, text: str) -> dict:
        '''Extract the first JSON block from a markdown-formatted response or raw text.
        
        If the JSON is invalid or missing, it returns a dict that will cause an intentional failure
        during evaluation, ensuring the agent's debug loop activates for a retry.
        '''
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1], strict=False)
            except json.JSONDecodeError:
                pass
                
        # Fallback to trigger an evaluator failure so the loop retries
        return {
            "main.py": f"""raise ValueError('''
Failed to parse AI output as JSON.
The AI must strictly output a valid JSON code object matching the requested structure.
Raw Response Fragment:
{text[:200]}...
''')""",
            "src/__init__.py": ""
        }

    @abstractmethod
    def generate_code(self, prompt: str) -> dict:
        '''Generates a PocketPy-compatible text/grid-based game from the prompt.'''
        ...

    @abstractmethod
    def debug_code(self, error_log: str, project_files: dict) -> dict:
        '''Fixes broken PocketPy game code given the code and its error traceback.'''
        ...

    @abstractmethod
    def improve_code(self, context: dict) -> dict:
        '''Iteratively improves a PocketPy game given a context dict with instructions and code.'''
        ...
