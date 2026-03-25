from dataclasses import dataclass, field

from lark import Lark, Transformer
from pygeofilter.ast import AstType, Node
from pygeofilter.backends.evaluator import Evaluator, handle
from sqlalchemy import Integer, case, cast, func, text

GRAMMAR = r"""
    ?start: expr

    ?expr: sum ("if" comparison ("else" expr)? )?

    SUM: "+" | "-"

    ?sum: sum SUM term -> op
        | term

    MULT: "*" | "/"

    ?term: term MULT power -> op
        | power

    POW: "^"

    ?power: factor POW NUMBER -> op
        | factor

    ?factor: "-" factor    -> op
        | atom

    ?atom: func_call
        | variable
        | NUMBER
        | QUOTED
        | "(" expr ")"


    arg_list: expr ("," expr)*
    func_call: CNAME "(" arg_list? ")"

    variable: CNAME ("." CNAME)*

    comparison: sum OP sum

    OP: ">" | "<" | "=" | "!=" | ">=" | "<=" | "in"
    QUOTED: /([\"\'])(.*)([\"\'])/

    %import common.CNAME
    %import common.NUMBER
    %import common.WS
    %ignore WS
"""
parser = Lark(GRAMMAR)


@dataclass
class Column:
    parts: list[str]


@dataclass
class Func(Node):
    name: str
    args: list = field(default_factory=list)

    def get_sub_nodes(self) -> list[AstType]:
        return self.args


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
class Query(Node):
    else_: Node | None = None


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

    def query(self, children):
        return Query(*children)

    def func_call(self, children):
        return Func(children[0], *children[1:])

    def variable(self, children):
        return Column(children)

    def CNAME(self, token):
        return token.value

    def NUMBER(self, token):
        return float(token.value)

    def QUOTED(self, token):
        return token.value


class SQLEvaluator(Evaluator):
    def __init__(self, field_map):
        self.field_map = field_map

    @handle(Arithmetic)
    def arithmetic(self, node, lhs, rhs):
        match node.op:
            case "+":
                return lhs + rhs
            case "-":
                return lhs - rhs
            case "/":
                return lhs / rhs
            case "*":
                return lhs * rhs
            case "^":
                return func.pow(lhs, rhs)

    @handle(Column)
    def column(self, node):
        col = self.field_map
        for part in node.parts:
            col = col[part]
        return col

    @handle(Comparison)
    def comparison(self, node, lhs, rhs):
        match node.op:
            case "<":
                return lhs < rhs
            case ">":
                return lhs > rhs
            case "=":
                return lhs == rhs
            case "!=":
                return lhs != rhs
            case ">=":
                return lhs >= rhs
            case "<=":
                return lhs <= rhs
            case "in":
                return rhs.contains(lhs)

    @handle(Conditional)
    def conditional(self, node, expr, if_, else_=None):
        return case((if_, expr), else_=else_)

    @handle(Func)
    def func(self, node, *args):
        match node.name:
            case "int":
                return cast(args[0], Integer)
            case "unique":
                return args[0].distinct()
            case "merge":
                return func.st_union_agg(args[0])
            case "centroid":
                return func.st_centroid(args[0])
            case "percentile":
                return func.quantile_cont(args[0], args[1] / 100)
            case "shannon":
                return func.ln(2) * func.list_entropy(func.list(args[0]))
            case _:
                return getattr(func, node.name)(*args)

    @handle(float)
    def float(self, node):
        return node

    @handle(str)
    def str(self, node):
        return text(node)


def parse(text: str, field_map):
    expr = Lark(GRAMMAR, parser="lalr", transformer=SQLTransformer()).parse(text)
    compiler = SQLEvaluator(field_map)
    query = compiler.evaluate(expr)
    return query
