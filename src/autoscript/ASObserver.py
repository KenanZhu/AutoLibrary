# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""


class ParsingObserver:
    """
        Base observer for AutoScript parsing events.

        Subclass and override the relevant methods to react to
        tokenization / parsing events produced by ASTokenizer.
        This is the core abstraction that lets pre-check and
        orchestration modules subscribe to the same parsing pipeline.
    """

    def onParseStart(
        self,
        script_text: str
    ):
        """
            Called when tokenization of a new script begins.

            Args:
                script_text (str): The full script text being parsed.
        """
        pass

    def onTokenParsed(
        self,
        kind: str | None,
        data,
        line_num: int,
        raw_line: str
    ):
        """
            Called after each script line has been classified as a token.

            Args:
                kind (str | None): Token kind (K_IF, K_ELSE_IF, K_ELSE,
                                   K_ENDIF, K_SET, K_ADD, K_SUB) or
                                   None if unrecognised.
                data:      Token payload — condition string for IF/ELSE IF,
                           (target, value) tuple for SET/ADD/SUB,
                           None for ELSE/ENDIF/unrecognised.
                line_num (int): 1-based line number.
                raw_line (str): The stripped raw line text.
        """
        pass

    def onParseComplete(
        self,
        statements: list
    ):
        """
            Called when flat tokenization is complete.

            Args:
                statements (list[Stmt]): The list of parsed Stmt objects.
        """
        pass

    def onASTReady(
        self,
        ast
    ):
        """
            Called when full AST construction is complete (after parse()).

            Args:
                ast (Script): The root Script AST node.
        """
        pass
