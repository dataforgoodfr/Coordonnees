from lark import Lark, Transformer

grammar = r"""
start: expr
expr: comparison | comparison AND comparison
comparison: DOT OP NUMBER
DOT: "."
OP: "<=" | ">=" | "<" | ">"
AND: "and"
%import common.NUMBER
%import common.WS
%ignore WS
"""


class RangeTransformer(Transformer):
    def comparison(self, items):
        op, number = items[1], float(items[2])
        match op:
            case ">=":
                self.range["minimum"] = number
            case "<=":
                self.range["maximum"] = number
            case ">":
                self.range["exclusiveMinimum"] = number
            case "<":
                self.range["exclusiveMaximum"] = number

    def start(self, item):
        return self.range


parser = Lark(grammar, parser="lalr", transformer=RangeTransformer())
