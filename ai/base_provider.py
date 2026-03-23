from abc import ABC, abstractmethod


class BaseProvider(ABC):
    '''Abstract base class for all AI providers.

    All providers must implement code generation, debugging, and improvement
    for PocketPy-compatible, text-grid-based Python games. No Pygame or
    graphical dependencies are permitted in generated code.
    '''

    @abstractmethod
    def generate_code(self, prompt: str) -> str:
        '''Generates a PocketPy-compatible text/grid-based game from the prompt.'''
        ...

    @abstractmethod
    def debug_code(self, error_log: str, code: str) -> str:
        '''Fixes broken PocketPy game code given the code and its error traceback.'''
        ...

    @abstractmethod
    def improve_code(self, context: dict) -> str:
        '''Iteratively improves a PocketPy game given a context dict with instructions and code.'''
        ...
