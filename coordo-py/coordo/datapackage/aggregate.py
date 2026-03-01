from dataclasses import dataclass, field

from lark import Lark, Transformer
from pygeofilter.ast import AstType, Node
from pygeofilter.backends.evaluator import Evaluator, handle
from sqlalchemy import Float, Function, case, cast, func, text, select
from sqlalchemy.orm import Session
from functools import reduce

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
         | for_loop
         | loop_variable
         | variable
         | NUMBER
         | QUOTED
         | "(" expr ")"

    ?for_loop_content: func_call
                     | variable

    for_loop: "for" loop_variable "in" for_loop_content "do" expr

    arg_list: expr ("," expr)*
    func_call: CNAME "(" arg_list ")"

    variable: CNAME ("." CNAME)?

    loop_variable: "$" CNAME
    
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
class LoopVariable(Node):
    name: str


@dataclass
class ForLoop(Node):
    variable: LoopVariable
    query: Node
    body: Node

    def get_sub_nodes(self) -> list[AstType]:
        return [self.query]


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

    def for_loop(self, children):
        return ForLoop(children[0], children[1], children[2])

    def loop_variable(self, children):
        return LoopVariable(children[0])

    def variable(self, children):
        return Column(children)

    def CNAME(self, token):
        return token.value

    def NUMBER(self, token):
        return float(token.value)

    def QUOTED(self, token):
        return token.value


class SQLCompiler(Evaluator):
    def __init__(self, base_model, session: Session = None):
        self.base_model = base_model
        self.joins = []
        self.subqueries = []
        self.session = session
        self.loop_variables_values = {}

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
        # Handling list type param (= loop inside function)
        if len(args) == 1 and isinstance(args[0], list):
            list_arg = args[0]

            if node.name == "sum":
                if isinstance(list_arg[0], str):
                    return reduce(lambda a, b: f"{a} + {b}", list_arg)

                return reduce(lambda a, b: a + b, list_arg)

            raise ValueError(f"Function {node.name} cannot handle list.")

        if node.name == "centroid":
            return func.ST_Centroid(func.ST_Collect(args[0]))
        if node.name == "unique":
            return args[0].distinct()
        if node.name == "count_occ":
            return func.sum(case((args[0] == args[1], 1), else_=0))
        
        return getattr(func, node.name)(*args)
    
    @handle(ForLoop)
    def for_loop(self, node, query):
        if self.session is None:
            raise ValueError(
                "A database session is required to evaluate for loops. "
            )
        
        values = self.session.execute(select(query)).scalars().all()

        body = []

        for item in values:
            self.loop_variables_values[node.variable.name] = item
            item_body = self.evaluate(node.body)
            body.append(item_body)

        del self.loop_variables_values[node.variable.name]

        return body

    @handle(LoopVariable)
    def loop_variable(self, node):
        if node.name not in self.loop_variables_values:
            raise ValueError(f"Loop variable '{node.name}' not found. Are you inside a for loop?")
        return self.loop_variables_values[node.name]

    @handle(float)
    def float(self, node):
        return node

    @handle(str)
    def str(self, node):
        return text(node)


def parse(text: str, model, session):
    expr = Lark(GRAMMAR, parser="lalr", transformer=AggregateTransformer()).parse(text)
    compiler = SQLCompiler(model, session)
    query = compiler.evaluate(expr)
    return query, compiler.joins, compiler.subqueries
