"""
Orchestration observer for AutoScript scripts.
Subscribes to ASTokenizer parsing events to produce a structured
block representation for the orchestration dialog UI.
"""
from autoscript.ASObserver import ParsingObserver
from autoscript.ASTokenizer import (
    ASTokenizer,
    K_IF,
    K_ELSE_IF,
    K_ELSE,
    K_ENDIF,
    K_SET,
    K_ADD,
    K_SUB,
)


__all__ = ["ScriptOrchObserver", "parseBlocks"]


class ScriptOrchObserver(ParsingObserver):
    """
        Builds an ordered list of (block_type, condition, actions) tuples
        from tokenization events.

        Each block:
            (type: str, condition: str | None, actions: list[(target, value_expr, op_type)])
    """

    def __init__(
        self
    ):

        super().__init__()
        self._blocks = []
        self._current_type = None
        self._current_condition = None
        self._current_actions = []


    def onTokenParsed(
        self,
        kind: str | None,
        data,
        line_num: int,
        raw_line: str
    ):

        if kind in (K_IF, K_ELSE_IF, K_ELSE):
            self._flushCurrentBlock()
            self._current_type = kind
            self._current_condition = data if kind != K_ELSE else None
            self._current_actions = []
        elif kind in (K_SET, K_ADD, K_SUB):
            target, value = data
            if kind == K_SET:
                self._current_actions.append((target, value, "set"))
            elif kind == K_ADD:
                prefixed = value if value.startswith("-") else f"+{value}"
                self._current_actions.append((target, prefixed, "add"))
            else:
                prefixed = value if value.startswith("-") else f"-{value}"
                self._current_actions.append((target, prefixed, "sub"))
        elif kind == K_ENDIF:
            self._flushCurrentBlock()
            self._current_type = None
            self._current_condition = None
            self._current_actions = []


    def onParseComplete(
        self,
        statements: list
    ):

        self._flushCurrentBlock()


    def _flushCurrentBlock(
        self
    ):

        if self._current_type is not None:
            self._blocks.append((
                self._current_type,
                self._current_condition,
                list(self._current_actions),
            ))

    @property
    def blocks(
        self
    ) -> list:

        return list(self._blocks)


def parseBlocks(
    script: str
) -> list:
    """
        Tokenize a script via observer pipeline and return its
        structured block representation.
    """

    observer = ScriptOrchObserver()
    ASTokenizer.tokenizeWithObservers(script, [observer])
    return observer.blocks
