from dataclasses import dataclass, field

from lark import Lark, Transformer
from pygeofilter.ast import AstType, Node
from pygeofilter.backends.evaluator import Evaluator, handle
from sqlalchemy import Integer, and_, case, cast, func, text

from .mapper import FieldMapper

# TODO: automatically create this list from Duckdb
AGG_FUNCS = [
    "sum",
    "avg",
    "max",
    "min",
    "list",
    "count",
    "percentile",
    "merge",
    "gini",
    "categorical_gini",
    "shannon",
]


class oset:
    def __init__(self, items=None):
        self.data = []
        if items:
            for item in items:
                self.add(item)

    def add(self, item):
        if item not in self.data:
            self.data.append(item)

    def union(self, other):
        result = oset(self)
        for item in other:
            result.add(item)
        return result

    def update(self, other):
        for item in other:
            self.add(item)

    def __getitem__(self, index):
        return self.data[index]

    def __bool__(self):
        return bool(self.data)


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
    def __init__(self, field_map, base_query):
        self.field_map = field_map
        self.base_query = base_query

    @handle(Arithmetic)
    def arithmetic(self, node, lhs, rhs):
        lhs_expr, lhs_joins = lhs
        rhs_expr, rhs_joins = rhs

        match node.op:
            case "+":
                expr = lhs_expr + rhs_expr
            case "-":
                expr = lhs_expr - rhs_expr
            case "/":
                expr = lhs_expr / rhs_expr
            case "*":
                expr = lhs_expr * rhs_expr
            case "^":
                expr = func.pow(lhs_expr, rhs_expr)

        return expr, lhs_joins.union(rhs_joins)

    @handle(Column)
    def column(self, node):
        col = self.field_map
        joins = oset()
        for part in node.parts:
            col = col[part]
            if isinstance(col, FieldMapper):
                joins.add((col.table, None))
            else:
                return col, joins

    @handle(Comparison)
    def comparison(self, node, lhs, rhs):
        lhs_expr, lhs_joins = lhs
        rhs_expr, rhs_joins = rhs

        match node.op:
            case "<":
                expr = lhs_expr < rhs_expr
            case ">":
                expr = lhs_expr > rhs_expr
            case "=":
                expr = lhs_expr == rhs_expr
            case "!=":
                expr = lhs_expr != rhs_expr
            case ">=":
                expr = lhs_expr >= rhs_expr
            case "<=":
                expr = lhs_expr <= rhs_expr
            case "in":
                expr = rhs_expr.contains(lhs_expr)

        return expr, lhs_joins.union(rhs_joins)

    @handle(Conditional)
    def conditional(self, node, expr, if_, else_=None):
        expr_expr, expr_joins = expr
        if_expr, if_joins = if_

        joins = expr_joins.union(if_joins)

        if else_ is not None:
            else_expr, else_joins = else_
            joins.add(else_joins)
        else:
            else_expr = None

        result = case((if_expr, expr_expr), else_=else_expr)

        return result, joins

    @handle(Func)
    def func(self, node, *args):
        exprs = []
        joins = oset()

        for arg in args:
            arg_expr, arg_joins = arg
            exprs.append(arg_expr)
            joins.update(arg_joins)

        match node.name:
            case "int":
                f = cast(exprs[0], Integer)
            case "unique":
                f = exprs[0].distinct()
            case "merge":
                f = func.st_union_agg(exprs[0])
            case "centroid":
                f = func.st_centroid(exprs[0])
            case "percentile":
                f = func.quantile_cont(exprs[0], exprs[1] / 100)
            case "shannon":
                f = func.ln(2) * func.list_entropy(func.list(exprs[0]))
            case _:
                f = getattr(func, node.name)(*exprs)

        if node.name in AGG_FUNCS:
            query = self.base_query
            for join, on in joins:
                query = query.join(join, on)
            cte = query.add_columns(f.label("value")).cte()
            group_cols = list(self.base_query._group_by_clause)
            return cte.columns["value"], oset(
                [
                    (
                        cte,
                        and_(*([col == cte.c[col.name] for col in group_cols])),
                    )
                ]
            )

        return f, joins

    @handle(float)
    def float(self, node):
        return node, oset()

    @handle(str)
    def str(self, node):
        return text(node), oset()


parse = Lark(GRAMMAR, parser="lalr", transformer=SQLTransformer()).parse


def to_sql(expr: AstType, field_map, base_query):
    compiler = SQLEvaluator(field_map, base_query)
    return compiler.evaluate(expr)
