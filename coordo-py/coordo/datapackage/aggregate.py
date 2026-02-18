from dataclasses import dataclass, field

from lark import Lark, Transformer
from pygeofilter.ast import AstType, Node
from pygeofilter.backends.evaluator import Evaluator, handle
from sqlalchemy import Float, Function, case, cast, func, text

GRAMMAR = r"""
    ?start: expr

    ?expr: sum ("if" comparison ("else" expr)? )?

    ?sum: sum SUM term -> op
        | term

    SUM: "+" | "-"

    ?term: term MULT factor -> op
         | factor

    MULT: "*" | "/"

    ?factor: "-" factor    -> op
           | atom

    ?atom: func_call
         | variable
         | NUMBER
         | QUOTED
         | "(" expr ")"

    arg_list: expr ("," expr)*
    func_call: CNAME "(" arg_list ")"

    variable: CNAME ("." CNAME)?

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


class AggregateTransformer(Transformer):
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
        return Func(children[0], children[1])

    def variable(self, children):
        return Column(children)

    def CNAME(self, token):
        return token.value

    def NUMBER(self, token):
        return float(token.value)

    def QUOTED(self, token):
        return token.value


class SQLCompiler(Evaluator):
    def __init__(self, base_model):
        self.base_model = base_model
        self.joins = []
        self.subqueries = []

    @handle(Arithmetic)
    def arithmetic(self, node, lhs, rhs):
        match node.op:
            case "+":
                return lhs + rhs
            case "-":
                return lhs - rhs
            case "/":
                return lhs / cast(rhs, Float)
            case "*":
                return lhs * rhs

    @handle(Column)
    def column(self, node):
        model = self.base_model
        var = None
        for part in node.parts:
            var = getattr(model, part)
            if hasattr(var.property, "direction"):
                model = var.property.mapper.class_
                self.joins.append(var)
        return var

    @handle(Comparison)
    def comparison(self, node, lhs, rhs):
        if isinstance(rhs, Function):
            self.subqueries.append(rhs)
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
        if node.name == "centroid":
            return func.ST_Centroid(func.ST_Collect(args[0]))
        if node.name == "unique":
            return args[0].distinct()
        return getattr(func, node.name)(*args)

    @handle(float)
    def float(self, node):
        return node

    @handle(str)
    def str(self, node):
        return text(node)


def parse(text: str, model):
    expr = Lark(GRAMMAR, parser="lalr", transformer=AggregateTransformer()).parse(text)
    compiler = SQLCompiler(model)
    query = compiler.evaluate(expr)
    return query, compiler.joins, compiler.subqueries
