# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass, field

from lark import Lark, Transformer
from pygeofilter.ast import AstType, Node

GRAMMAR = r"""
    ?start: expr

    ?expr: sum ("if" boolean_expr ("else" expr)?)?

    ?boolean_expr: boolean_or

    ?boolean_or: boolean_and ( "||" | "or" ) boolean_or
            | boolean_and

    ?boolean_and: comparison ( "&&" | "and" ) boolean_and
            | comparison

    SUM: "+" | "-"

    ?sum: sum SUM term -> op
        | term

    MULT: "*" | "/"

    ?term: term MULT power -> op
        | power

    POW: "^"

    ?power: factor POW NUMBER -> op
        | factor

    ?factor: "-" factor -> op
            | atom

    ?atom: call_chain
        | func_call
        | NUMBER
        | QUOTED
        | NULL
        | "(" expr ")"

    call_chain: variable ("." (func_call | variable))*

    func_call: CNAME "(" arg_list? ")"

    variable: CNAME

    NULL: "null"

    arg_list: expr ("," expr)*

    comparison: sum OP sum

    OP: ">" | "<" | "=" | "!=" | ">=" | "<=" | "in"
    QUOTED: /'[^']*'|"[^"]*"/

    %import common.CNAME
    %import common.NUMBER
    %import common.WS
    %ignore WS
"""


@dataclass
class Column:
    parts: list[str]


@dataclass
class Func(Node):
    name: str
    args: list = field(default_factory=list)
    target: Node | None = None


@dataclass
class BinaryOp(Node):
    lhs: Node
    op: str
    rhs: Node

    def get_sub_nodes(self) -> list[AstType]:
        return [self.lhs, self.rhs]

    def get_template(self) -> str:
        return f"{{}} {self.op} {{}}"


@dataclass
class Arithmetic(BinaryOp):
    pass


@dataclass
class Comparison(BinaryOp):
    pass


@dataclass
class Chain(Node):
    steps: list[Node]


@dataclass
class Query(Node):
    else_: Node | None = None


@dataclass
class Number(Node):
    value: float


@dataclass
class Text(Node):
    value: str


@dataclass
class Conditional(Node):
    expr: Node
    if_: Node | None = None
    else_: Node | None = None

    def get_sub_nodes(self) -> list[AstType]:
        if self.if_ is not None:
            if self.else_ is not None:
                return [self.expr, self.if_, self.else_]
            return [self.expr, self.if_]
        return [self.expr]


class SQLTransformer(Transformer):
    def arg_list(self, items):
        return list(items)

    def op(self, children):
        return Arithmetic(*children)

    def expr(self, children):
        return Conditional(*children)

    def comparison(self, children):
        return Comparison(*children)

    def boolean_expr(self, children):
        return self.boolean_or(self, children)

    def boolean_and(self, children):
        if len(children) == 1:
            return children[0]
        return BinaryOp(children[0], 'and', children[2])  # children[1] is the "&&" or "and" token

    def boolean_or(self, children):
        if len(children) == 1:
            return children[0]
        return BinaryOp(children[0], 'or', children[2])  # children[1] is the "||" or "or" token

    def query(self, children):
        return Query(*children)

    def call_chain(self, children):
        node = children[0]
        for child in children[1:]:
            if isinstance(child, Column):
                node = Column(node.parts + child.parts)
            elif isinstance(child, Func):
                child.target = node
                node = child

        return node

    def func_call(self, children):
        return Func(children[0], *children[1:])

    def variable(self, children):
        return Column(children)

    def CNAME(self, token):
        return token.value

    def NUMBER(self, token):
        return Number(float(token.value))

    def QUOTED(self, token):
        return Text(token.value)

    def NULL(self, token):
        return None


parse = Lark(GRAMMAR, parser="lalr", transformer=SQLTransformer()).parse
