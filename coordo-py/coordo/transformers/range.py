from lark import Lark, Transformer
from coordo.helpers import removeQuotes


CONSTRAINT_GRAMMAR = r"""
?start: expression
expression: func_call | comparison (BOOL comparison)*
comparison: DOT COMP_OP expr

?expr: expr ARITHMETIC term
    | term

?term: NUMBER | VAR

func_call: CNAME "(" DOT "," arg_list? ")"
arg_list: STRING*

DOT: "."
COMP_OP: "<=" | ">=" | "<" | ">"
BOOL: "and" | "or"
ARITHMETIC: "+" | "-" | "*" | "/"
STRING: /("[^"]*")|'[^"]*'/
VAR: "${" /[A-Za-z_][A-Za-z_0-9]*/ "}"

%import common.CNAME
%import common.NUMBER
%import common.WS
%ignore WS
"""


def isCustomConstraint(constraint: str) -> bool:
        return not (isinstance(constraint, float) or isinstance(constraint, int))

class RangeTransformer(Transformer):
    def arg_list(self, items):
        return items

    def STRING(self, token):
        return token.value

    def CNAME(self, token):
        return token.value

    def NUMBER(self, token):
        return float(token.value)

    def expr(self, items):
        return "".join(str(item) for item in items)

    def comparison(self, items):
        op, expr = items[1], items[2]
        constraintName = "custom_" if isCustomConstraint(expr) else ""
        match op:
            case ">=":
                constraintName += "minimum"
            case "<=":
                constraintName +="maximum"
            case ">":
                constraintName += "exclusiveMinimum"
            case "<":
                constraintName +="exclusiveMaximum"
        
        return {constraintName: expr}

    def func_call(self, items):
        funcName, args = items[0], items[2]
        match funcName:
            case "regex":
                return {"pattern": removeQuotes(args[0])}

    def expression(self, items):
        result = {}
        for item in items:
            if isinstance(item, dict):
                result.update(item)
        return result


constraint_parser = Lark(
    CONSTRAINT_GRAMMAR, parser="lalr", transformer=RangeTransformer()
)
