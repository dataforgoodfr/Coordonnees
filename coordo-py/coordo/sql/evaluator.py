from dataclasses import dataclass
from typing import Any

from pygeofilter.ast import AstType
from sqlalchemy import Integer, and_, case, cast, func, select, text

from coordo.sql.helpers import AGGREGATES, SPATIAL_FUNCTIONS
from coordo.sql.mapper import FieldMapper


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

    def __repr__(self):
        return str(self.data)


@dataclass
class Context:
    expr: Any
    joins: oset


class SQLEvaluator:
    def __init__(self, mapper, base_query=None):
        if base_query is None:
            base_query = select(mapper.table)
        group_cols = (
            list(base_query._group_by_clause) or mapper.table.primary_key.columns
        )
        self.base_query = base_query.with_only_columns(*group_cols)
        self.join_cols = group_cols

    def evaluate(self, node: AstType, mapper: FieldMapper) -> Any:
        sub_args = []
        if hasattr(node, "get_sub_nodes"):
            subnodes = node.get_sub_nodes()  # type: ignore
            if subnodes:
                if isinstance(subnodes, list):
                    sub_args = [
                        self.evaluate(sub_node, mapper) for sub_node in subnodes
                    ]
                else:
                    sub_args = [self.evaluate(subnodes, mapper)]

        method_name = type(node).__name__.lower()
        handler = getattr(self, method_name, None)
        if handler is not None:
            result = handler(node, *sub_args, mapper=mapper)
        else:
            raise NotImplementedError(
                f"No method set to evaluate node of type {type(node)}"
            )

        return result

    def arithmetic(self, node, lhs, rhs, *, mapper: FieldMapper):
        match node.op:
            case "+":
                expr = lhs.expr + rhs.expr
            case "-":
                expr = lhs.expr - rhs.expr
            case "/":
                expr = lhs.expr / rhs.expr
            case "*":
                expr = lhs.expr * rhs.expr
            case "^":
                expr = func.pow(lhs.expr, rhs.expr)
            case _:
                raise ValueError("Unsupported operation :", node.op)

        return Context(expr, lhs.joins.union(rhs.joins))

    def column(self, node, *, mapper):
        joins = oset()
        col = mapper
        for part in node.parts:
            col = col[part]
            if isinstance(col, FieldMapper):
                joins.add((col.table, None))
            else:
                return Context(col, joins)
        return Context(col, joins)

    def comparison(self, node, lhs, rhs, *, mapper: FieldMapper):
        match node.op:
            case "<":
                expr = lhs.expr < rhs.expr
            case ">":
                expr = lhs.expr > rhs.expr
            case "=":
                expr = lhs.expr == rhs.expr
            case "!=":
                expr = lhs.expr != rhs.expr
            case ">=":
                expr = lhs.expr >= rhs.expr
            case "<=":
                expr = lhs.expr <= rhs.expr
            case "in":
                expr = rhs.expr.contains(lhs.expr)
            case _:
                raise ValueError("Unsupported comparison :", node.op)

        return Context(expr, lhs.joins.union(rhs.joins))

    def conditional(self, node, expr, if_, else_=None, *, mapper: FieldMapper):
        joins = expr.joins.union(if_.joins)

        if else_ is not None:
            else_expr = else_.expr
            joins.update(else_.joins)
        else:
            else_expr = None

        result = case((if_.expr, expr.expr), else_=else_expr)

        return Context(result, joins)

    def func(self, node, *, mapper: FieldMapper):
        args = []
        joins = oset()
        if node.target:
            ctx = self.evaluate(node.target, mapper)

            if isinstance(ctx.expr, FieldMapper):
                mapper = ctx.expr
            else:
                args.append(ctx.expr)

            joins.update(ctx.joins)

        for arg in node.args:
            ctx = self.evaluate(arg, mapper)
            args.append(ctx.expr)
            joins.update(ctx.joins)

        if node.name.lower() in SPATIAL_FUNCTIONS:
            node.name = "st_" + node.name

        match node.name:
            case "int":
                f = cast(args[0], Integer)
            case "unique":
                f = args[0].distinct()
            case _:
                f = getattr(func, node.name)(*args)

        if node.name.lower() in AGGREGATES:
            query = self.base_query
            for join, on in joins:
                query = query.join(join, on)
            cte = query.add_columns(f.label("value")).cte()
            return Context(
                cte.columns["value"],
                oset(
                    [
                        (
                            cte,
                            and_(*([col == cte.c[col.name] for col in self.join_cols])),
                        )
                    ]
                ),
            )
        return Context(f, joins)

    def number(self, node, *, mapper: FieldMapper):
        return Context(node.value, oset())

    def text(self, node, *, mapper: FieldMapper):
        return Context(text(node.value), oset())

    def nonetype(self, node, *, mapper: FieldMapper):
        return Context(None, oset())


def to_sql(ast: AstType, field_map, base_query=None):
    compiler = SQLEvaluator(field_map, base_query)
    ctx = compiler.evaluate(ast, field_map)
    return ctx.expr, ctx.joins
