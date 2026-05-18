"""
Pre-check observer for AutoScript scripts.
Subscribes to ASTokenizer parsing events to validate script syntax
before it reaches the orchestration dialog, eliminating duplicate parsing.
"""
from autoscript.ASObserver import ParsingObserver
from autoscript.ASTokenizer import (
    K_IF,
    K_ELSE_IF,
    K_ELSE,
    K_ENDIF,
    K_SET,
    K_ADD,
    K_SUB,
    ASTokenizer,
)


__all__ = ["ScriptPrecheckObserver", "precheck"]


class ScriptPrecheckObserver(ParsingObserver):
    """
        Validates script syntax and structure during tokenization.

        Checks performed:
          - IF/ENDIF depth matching
          - No nested IF blocks (orchestration limitation)
          - ELSE IF / ELSE appear only inside an IF block
          - Only allowed variables appear in SET/ADD/SUB targets
          - No completely unrecognized syntax lines
    """

    def __init__(
        self,
        allowed_vars: set = None
    ):

        super().__init__()
        self._allowed = allowed_vars or set()
        self._if_depth = 0
        self.errors = []
        self._stmts = []


    def onTokenParsed(
        self,
        kind: str | None,
        data,
        line_num: int,
        raw_line: str
    ):

        if kind == K_IF:
            self._if_depth += 1
            if self._if_depth > 1:
                self.errors.append(
                    f"静态检查：错误(第{line_num}行): 检测到嵌套 IF，编排窗口不支持嵌套条件块。"
                )
        elif kind == K_ELSE_IF:
            if self._if_depth < 1:
                self.errors.append(
                    f"静态检查：错误(第{line_num}行): ELSE IF 前缺少 IF。"
                )
        elif kind == K_ELSE:
            if self._if_depth < 1:
                self.errors.append(
                    f"静态检查：错误(第{line_num}行): ELSE 前缺少 IF。"
                )
        elif kind == K_ENDIF:
            self._if_depth -= 1
            if self._if_depth < 0:
                self.errors.append(
                    f"静态检查：错误(第{line_num}行): 多余的 ENDIF。"
                )
        elif kind is None:
            self.errors.append(
                f"静态检查：错误(第{line_num}行): 无法识别的语法 '{raw_line}'。"
            )
        elif kind in (K_SET, K_ADD, K_SUB):
            target = data[0] if isinstance(data, tuple) else ""
            if self._allowed and target.upper() not in self._allowed:
                self.errors.append(
                    f"静态检查：错误(第{line_num}行): 目标变量 '{target}' 不是预设变量，"
                    f"编排窗口不支持。"
                )


    def onParseComplete(
        self,
        statements: list
    ):

        if self._if_depth != 0:
            self.errors.append(
                f"静态检查：错误(不适用): IF 与 ENDIF 不匹配。")
        self._stmts = statements

    @property
    def valid(
        self
    ) -> bool:

        return len(self.errors) == 0


    def getErrorMessage(
        self
    ) -> str:

        return self.errors[0] if self.errors else ""


    def buildSimplifiedScript(
        self
    ) -> str:
        """Replace all non-control-flow statements with PASS for engine validation."""

        lines = []
        for stmt in self._stmts:
            if stmt.kind in (K_IF, K_ELSE_IF, K_ELSE, K_ENDIF):
                lines.append(stmt.raw_line)
            else:
                lines.append("PASS")
        return "\n".join(lines)


def precheck(
    script: str,
    allowed_vars: set = None
) -> tuple[bool, str]:
    """
        Run the full precheck pipeline on a script.

        Steps:
          1. Create a ScriptPrecheckObserver and subscribe it to an ASTokenizer.
          2. Tokenize — the observer validates syntax during token events.
          3. Replace action lines with PASS and run engine validation
             with mock target data.
    """

    if not script or not script.strip():
        return True, ""
    observer = ScriptPrecheckObserver(allowed_vars=allowed_vars)
    ASTokenizer.tokenizeWithObservers(script, [observer])
    if not observer.valid:
        return False, observer.getErrorMessage()
    simplified = observer.buildSimplifiedScript()
    if not simplified.strip():
        return True, ""
    try:
        from autoscript import (
            registerDefaultTargetVars,
            buildMockTargetData,
            execute
        )
        registerDefaultTargetVars()
        execute(simplified, buildMockTargetData())
    except ValueError as e:
        return False, f"运行时检查: {e}"
    except Exception:
        return False, "执行环境异常，请检查 AutoScript 配置。"
    return True, ""
