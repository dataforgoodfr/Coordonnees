import functools

import pandas as pd
from lark import Lark, Transformer

from .sources.kobotoolbox import KoboToolboxSource

grammar = r"""
    start: aggregation
    aggregation: func_name variable ("where" condition)? | func_name aggregation
    func_name: /centroid|count|avg|unique|percentile/
    variable: /[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*/
    condition: variable bin_op value
    value: variable | function_call
    function_call: func_name "(" variable "," NUMBER ")"
    bin_op: />|<|==|!=|>=|<=/
    %import common.NUMBER
    %import common.WS
    %ignore WS
"""

parser = Lark(grammar)


class PandasTransformer(Transformer):
    def __init__(self, df):
        self.df = df

    def start(self, children):
        aggregation = children[0]
        return aggregation

    def aggregation(self, children):
        func_name = children[0]
        target = children[1]
        if len(children) > 2:
            target = target[children[2]]
        return self._apply_func(func_name, target)

    def _apply_func(self, func_name, target):
        if func_name == "centroid":
            return target.union_all().centroid
        elif func_name == "count":
            return len(target)
        elif func_name == "avg":
            return target.mean()
        elif func_name == "unique":
            return target.unique()
        elif func_name == "percentile":
            return target.quantile()
        else:
            raise ValueError(f"Unknown function: {func_name}")

    def variable(self, children):
        return self._cached_variable(children[0])

    @functools.cache
    def _cached_variable(self, name):
        cols = name.split(".")
        df = self.df
        col = cols[0]
        if len(cols) > 1:
            df = pd.json_normalize(df[cols[0]].explode())
            col = cols[1]
        return df[col]

    def condition(self, children):
        var, op, value = children
        value = value.children[0]
        match op.value:
            case ">":
                return var > value
            case "<":
                return var < value
            case "==":
                return var == value
            case "!=":
                return var != value
            case ">=":
                return var >= value
            case "<=":
                return var <= value
            case _:
                raise ValueError(f"Unknown operator: {op.value}")

    def function_call(self, children):
        func_name, var, num = children
        if func_name == "percentile":
            return var.astype(float).quantile(num / 100)
        else:
            raise ValueError(f"Unknown function: {func_name}")

    def func_name(self, children):
        return children[0]

    def bin_op(self, children):
        return children[0]

    def NUMBER(self, token):
        return float(token)


queries = {
    "geometry": "centroid gps",
    "richness": "count unique ind.ess_arb",
    "dominant height": "avg ind.haut where ind.haut > percentile(ind.haut, 80)",
}


def apply_queries(df, queries):

    def apply(df):
        out = []
        transformer = PandasTransformer(df)
        for query in queries.values():
            ast = parser.parse(query)
            out.append(transformer.transform(ast))
        return pd.Series(out, queries.keys())

    return df.apply(apply)
