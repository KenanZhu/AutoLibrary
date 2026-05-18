# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import re


__all__ = [
    "ASTokenizer",
    "Stmt",
    "Script",
    "IfNode",
    "ElifNode",
    "SetNode",
    "OpNode",
    "PassNode",
    "UnrecogNode",
    "NodeVisitor",
    "LineStrategy"
]


# Token kind constants
K_IF      = "IF"
K_ELSE_IF = "ELSE IF"
K_ELSE    = "ELSE"
K_ENDIF   = "ENDIF"
K_SET     = "SET"
K_ADD     = "ADD"
K_SUB     = "SUB"
K_PASS    = "PASS"

# Op-type constants
OP_SET = "set"
OP_ADD = "add"
OP_SUB = "sub"

# Compiled line patterns
_RE_IF      = re.compile(r"^IF\((.+)\)(?:\s+THEN\s*)?$", re.IGNORECASE)
_RE_ELSE_IF = re.compile(r"^ELSE\s+IF\((.+)\)(?:\s+THEN\s*)?$", re.IGNORECASE)
_RE_ELSE    = re.compile(r"^ELSE\s*$", re.IGNORECASE)
_RE_ENDIF   = re.compile(r"^(ENDIF|END IF)$", re.IGNORECASE)
_RE_SET     = re.compile(r"^SET\s+(\w+)\s*=\s*(.+)$", re.IGNORECASE)
_RE_ADD     = re.compile(r"^(\w+)\s+\.ADD\.\s+(\d+)$", re.IGNORECASE)
_RE_SUB     = re.compile(r"^(\w+)\s+\.SUB\.\s+(\d+)$", re.IGNORECASE)
_RE_PASS    = re.compile(r"^\s*PASS\s*$", re.IGNORECASE)


class Script:
    """
        Root AST node for an entire AutoScript.
        Contains an ordered list of top-level statement nodes.
    """

    def __init__(
        self,
        body: list = None
    ):

        self.body = body or []

    def accept(
        self,
        visitor
    ):

        return visitor.visitScript(self)


class IfNode:
    """
        IF conditional block with optional ELSE IF / ELSE branches.

        Attributes:
            condition (str): Raw condition expression.
            body (list): Statements executed when condition is true.
            elif_branches (list[ElifNode]): ELSE IF branches in order.
            else_body (list): Statements executed for the ELSE branch.
            closed (bool): Whether this IF has a matching ENDIF token.
    """

    def __init__(
        self,
        condition: str = "",
        body: list = None,
        elif_branches: list = None,
        else_body: list = None,
        closed: bool = True
    ):

        self.condition = condition
        self.body = body or []
        self.elif_branches = elif_branches or []
        self.else_body = else_body or []
        self.closed = closed

    def accept(
        self,
        visitor
    ):

        return visitor.visitIf(self)


class ElifNode:
    """
        ELSE IF branch within an IfNode.
    """

    def __init__(
        self,
        condition: str = "",
        body: list = None
    ):

        self.condition = condition
        self.body = body or []


class SetNode:
    """
        SET assignment statement.
    """

    def __init__(
        self,
        target: str = "",
        value: str = ""
    ):

        self.target = target
        self.value = value

    def accept(
        self,
        visitor
    ):

        return visitor.visitSet(self)


class OpNode:
    """
        .ADD. / .SUB. operation statement.
    """

    def __init__(
        self,
        op_type: str = "",
        target: str = "",
        value: str = ""
    ):

        self.op_type = op_type
        self.target = target
        self.value = value

    def accept(
        self,
        visitor
    ):

        return visitor.visitOp(self)


class PassNode:
    """
        PASS no-op statement.
    """

    def accept(
        self,
        visitor
    ):

        return visitor.visitPass(self)


class UnrecogNode:
    """
        Unrecognised line preserved for downstream error reporting.
    """

    def __init__(
        self,
        raw_line: str = ""
    ):

        self.raw_line = raw_line

    def accept(
        self,
        visitor
    ):

        return visitor.visitUnrecog(self)


class NodeVisitor:
    """
        Base visitor for the AutoScript AST.

        Subclass and override visit* methods to implement
        custom traversal logic.  Default walks tree depth-first.
    """

    def visitScript(
        self,
        _node: Script
    ):

        for child in _node.body:
            child.accept(self)

    def visitIf(
        self,
        _node: IfNode
    ):

        for child in _node.body:
            child.accept(self)
        for elif_node in _node.elif_branches:
            for child in elif_node.body:
                child.accept(self)
        for child in _node.else_body:
            child.accept(self)

    def visitSet(
        self,
        _node: SetNode
    ):

        pass

    def visitOp(
        self,
        _node: OpNode
    ):

        pass

    def visitPass(
        self,
        _node: PassNode
    ):

        pass

    def visitUnrecog(
        self,
        _node: UnrecogNode
    ):

        pass


class LineStrategy:
    """
        Encapsulates a regex pattern and its data-extraction handler.
        Used by the tokenizer to classify a single line.
    """

    def __init__(
        self,
        pattern,
        handler
    ):

        self.pattern = pattern
        self.handler = handler

    def match(
        self,
        line: str
    ):

        m = self.pattern.match(line)
        if m:
            return self.handler(m)
        return None


# Strategy instances — one per recognised AutoScript syntax form
_LINE_STRATEGIES = [
    LineStrategy(_RE_IF,      lambda m: (K_IF,      m.group(1))),
    LineStrategy(_RE_ELSE_IF, lambda m: (K_ELSE_IF, m.group(1))),
    LineStrategy(_RE_ELSE,    lambda m: (K_ELSE,    None)),
    LineStrategy(_RE_ENDIF,   lambda m: (K_ENDIF,   None)),
    LineStrategy(_RE_SET,     lambda m: (K_SET,     (m.group(1).strip(), m.group(2).strip()))),
    LineStrategy(_RE_ADD,     lambda m: (K_ADD,     (m.group(1).strip(), m.group(2).strip()))),
    LineStrategy(_RE_SUB,     lambda m: (K_SUB,     (m.group(1).strip(), m.group(2).strip()))),
    LineStrategy(_RE_PASS,    lambda m: (K_PASS,    None)),
]


class Stmt:
    """
        Flat statement container, backward-compatible with the original
        tokenize() output and the orchestration dialog's _classifyLine.
    """

    def __init__(
        self,
        kind: str | None = None,
        condition: str | None = None,
        target: str | None = None,
        value: str | None = None,
        op_type: str | None = None,
        raw_line: str = ""
    ):

        self.kind = kind
        self.condition = condition
        self.target = target
        self.value = value
        self.op_type = op_type
        self.raw_line = raw_line


class ASTokenizer:
    """
        Tokenizer / parser for the AutoScript DSL.

        Main class-level entry points (engine-facing):
          - classifyLine(line)   — single-line classifier.
          - tokenize(script)      — flat Stmt list.
          - parse(script)         — structured AST (Script root).

        Observer-enabled API (used by pre-check & orchestration):
          >>> obs = ScriptPrecheckObserver()
          >>> stmts = ASTokenizer.tokenizeWithObservers(script, [obs])
    """

    @classmethod
    def _notifyObservers(
        cls,
        observers: list,
        method: str,
        *args
    ):

        for obs in observers:
            getattr(obs, method)(*args)

    @classmethod
    def _matchLine(
        cls,
        stripped: str
    ):

        for strategy in _LINE_STRATEGIES:
            result = strategy.match(stripped)
            if result:
                return result
        return (None, None)

    @classmethod
    def _buildStmt(
        cls,
        stripped: str,
        kind: str | None,
        data
    ) -> Stmt:

        stmt = Stmt(kind=kind, raw_line=stripped)
        if kind == K_IF or kind == K_ELSE_IF:
            stmt.condition = data
        elif kind == K_SET:
            stmt.target, stmt.value = data
            stmt.op_type = OP_SET
        elif kind == K_ADD:
            stmt.target, stmt.value = data
            stmt.op_type = OP_ADD
        elif kind == K_SUB:
            stmt.target, stmt.value = data
            stmt.op_type = OP_SUB
        return stmt

    @classmethod
    def _stripComment(
        cls,
        line: str
    ) -> str:

        in_single = False
        for i, ch in enumerate(line):
            if ch == "'":
                in_single = not in_single
            elif ch == "/" and i + 1 < len(line) and line[i + 1] == "/" and not in_single:
                return line[:i].rstrip()
        return line

    @classmethod
    def _tokenizeImpl(
        cls,
        script: str
    ) -> list:

        statements = []
        for raw_line in script.split("\n"):
            code = cls._stripComment(raw_line.strip())
            if not code:
                continue
            kind, data = cls._matchLine(code)
            statements.append(cls._buildStmt(code, kind, data))
        return statements

    @classmethod
    def _parseTokens(
        cls,
        tokens: list
    ) -> Script:

        body = []
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            kind = tok.kind

            if kind == K_IF:
                node, consumed = cls._parseIfBlock(tokens, i)
                body.append(node)
                i += consumed
            elif kind in (K_ELSE_IF, K_ELSE, K_ENDIF):
                i += 1
            elif kind == K_SET:
                body.append(SetNode(target=tok.target, value=tok.value))
                i += 1
            elif kind in (K_ADD, K_SUB):
                body.append(OpNode(
                    op_type=tok.op_type,
                    target=tok.target,
                    value=tok.value
                ))
                i += 1
            elif kind == K_PASS:
                body.append(PassNode())
                i += 1
            else:
                body.append(UnrecogNode(raw_line=tok.raw_line))
                i += 1
        return Script(body=body)

    @classmethod
    def classifyLine(
        cls,
        stripped: str
    ):

        kind, data = cls._matchLine(stripped)
        if kind is None or kind == K_PASS:
            return None
        return (kind, data)

    @classmethod
    def tokenize(
        cls,
        script: str
    ) -> list:

        return cls._tokenizeImpl(script)

    @classmethod
    def parse(
        cls,
        script: str
    ) -> Script:

        return cls._parseTokens(cls._tokenizeImpl(script))

    @classmethod
    def tokenizeWithObservers(
        cls,
        script: str,
        observers: list
    ) -> list:
        """
            Tokenize and notify observers for each classified line.

            Fires onParseStart, onTokenParsed, and onParseComplete
            events to each observer.  This is the single tokenization
            pipeline shared by pre-check and orchestration modules.
        """

        cls._notifyObservers(observers, "onParseStart", script)
        statements = []
        for i, raw_line in enumerate(script.split("\n"), 1):
            code = cls._stripComment(raw_line.strip())
            if not code:
                continue
            kind, data = cls._matchLine(code)
            cls._notifyObservers(observers, "onTokenParsed", kind, data, i, code)
            statements.append(cls._buildStmt(code, kind, data))
        cls._notifyObservers(observers, "onParseComplete", statements)
        return statements

    @classmethod
    def parseWithObservers(
        cls,
        script: str,
        observers: list
    ) -> Script:
        """
            Parse and notify observers throughout the pipeline.

            Calls tokenizeWithObservers (which fires per-token events),
            then builds the AST and fires onASTReady.
        """

        tokens = cls.tokenizeWithObservers(script, observers)
        ast = cls._parseTokens(tokens)
        cls._notifyObservers(observers, "onASTReady", ast)
        return ast

    @classmethod
    def _parseIfBlock(
        cls,
        tokens: list,
        start: int
    ):

        first = tokens[start]
        node = IfNode(condition=first.condition or "")
        body = []
        elif_branches = []
        else_body = []
        current_target = body
        i = start + 1

        while i < len(tokens):
            tok = tokens[i]
            kind = tok.kind
            if kind == K_IF:
                sub_node, consumed = cls._parseIfBlock(tokens, i)
                current_target.append(sub_node)
                i += consumed
            elif kind == K_ELSE_IF:
                elif_branches.append(ElifNode(condition=tok.condition or ""))
                current_target = elif_branches[-1].body
                i += 1
            elif kind == K_ELSE:
                else_body = []
                current_target = else_body
                i += 1
            elif kind == K_ENDIF:
                node.body = body
                node.elif_branches = elif_branches
                node.else_body = else_body
                return (node, i - start + 1)
            elif kind == K_SET:
                current_target.append(SetNode(target=tok.target, value=tok.value))
                i += 1
            elif kind in (K_ADD, K_SUB):
                current_target.append(OpNode(
                    op_type=tok.op_type,
                    target=tok.target,
                    value=tok.value
                ))
                i += 1
            elif kind == K_PASS:
                current_target.append(PassNode())
                i += 1
            else:
                current_target.append(UnrecogNode(raw_line=tok.raw_line))
                i += 1
        node.body = body
        node.elif_branches = elif_branches
        node.else_body = else_body
        node.closed = False
        return (node, i - start)
