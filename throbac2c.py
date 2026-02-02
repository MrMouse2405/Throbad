"""
When used as a parse tree Listener on a valid Throbac parse tree, creates a
translation to C for each node and and stores this in the `self.c_translation`
dictionary. The complete program translation will be for the root of the
tree, which is the `ScriptContext` node.

Author: OCdt Syed, OCdt Noyes

Version: 2026-01-29
"""

from throbac.ThrobacListener import ThrobacListener
from throbac.ThrobacParser import ThrobacParser

DIGIT_MAP = {'NIL': '0', 'I': '1', 'II': '2', 'III': '3', 'IV': '4',
             'V': '5', 'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9'}
OPERATIONS_MAP = {'IDEM' : '==', 'NI.IDEM': '!=', 'INFRA': '<', 'INFRA.IDEM' : '<=', 'SUPRA' : '>', 'SUPRA.IDEM' : '>='}

HEADER = """
/*

    Throbac Programming Language

    This code is C transpiled version of the Throbac program.


*/

/*

    STDLIB

*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char *__throbac_cat(char *first, char *second) {
    size_t length = strlen(first) + strlen(second) + 1;
    void *value = malloc(length);
    if (value == 0) {
        abort();
    }
    strcpy((char *) value, first);
    return strcat((char *) value, second);
}

int stringlength(char *str) {
    return (int)strlen(str);
}

char *substring(char* str, int start, int length) {
    if (start < 0 ||  start > length || length > strlen(str) - 1 || start + length > strlen(str)) abort();
    char *sub = malloc(length + 1);
    if (!sub) abort();

    strncpy(sub, str + start, length);
    sub[length] = '\0';

    return sub;
}

/*


    Source


*/


/*

    Function Declarations

*/
"""

MAIN_COMMENT = """
/*

    Main

*/
"""

FUNCTION_DEFS_COMMENT = """
/*

    Implementation

*/
"""





class Throbac2CTranslator(ThrobacListener):

    def __init__(self):
        self.c_translation = {}
        self.func_declarations = {}

    # --- provided for you

    @staticmethod
    def c_block(node):
        """
        Given a parse tree node with a .c attribute, surrounds the text of the .c
        attribute with curly braces and indents each line by four spaces.
        """
        lines = node.split('\n')
        indented_lines = [
            ('    ' + line).rstrip()
            for line in lines
        ]
        block = ('\n'.join(indented_lines))
        return f'{{\n{block}\n}}'

    def exitNumber(self, ctx: ThrobacParser.NumberContext):
        throbac_number = ctx.getText()
        throbac_digits = throbac_number.strip('.').split('.')
        c_digits = [DIGIT_MAP[td] for td in throbac_digits]
        number = ''.join(c_digits)
        # str(int(...)) removes leading zeroes, since C doesn't permit them
        self.c_translation[ctx] = str(int(number))

    def exitString(self, ctx: ThrobacParser.StringContext):
        throbac = ctx.getText()
        c_with_pluses = f'"{throbac.strip("^")}"'
        self.c_translation[ctx] = c_with_pluses.replace('+', r'\n')  # note the raw string


    @staticmethod
    def translate_type(t: str) -> str:
        match t:
            case 'NUMERUS':
                return 'int'
            case 'LOCUTIO':
                return 'char *'
            case 'VERITAS':
                return 'short int'
            case _:
                raise ValueError(f'Unknown type: {t}')

    def exitBool(self, ctx: ThrobacParser.BoolContext):
        throbac_bool = ctx.getText()
        c_nonlatin_bool = '1' if throbac_bool == 'VERUM' else '0'
        self.c_translation[ctx] = c_nonlatin_bool

    def exitVariable(self, ctx: ThrobacParser.VariableContext):
        self.c_translation[ctx] = ctx.getText()

    def exitParens(self, ctx: ThrobacParser.ParensContext):
        self.c_translation[ctx] = f'({self.c_translation[ctx.expr()]})'

    def exitCompare(self, ctx: ThrobacParser.CompareContext):
        left = self.c_translation[ctx.expr(0)]
        right = self.c_translation[ctx.expr(1)]
        operator = OPERATIONS_MAP[ctx.op.text]
        self.c_translation[ctx] = f'{left} {operator} {right}'

    def exitConcatenation(self, ctx: ThrobacParser.ConcatenationContext):
        left = self.c_translation[ctx.expr(0)]
        right = self.c_translation[ctx.expr(1)]
        self.c_translation[ctx] = f'__throbac_cat({left},{right})'

    def exitAddSub(self, ctx: ThrobacParser.AddSubContext):
        left = self.c_translation[ctx.expr(0)]
        right = self.c_translation[ctx.expr(1)]
        self.c_translation[ctx] = f'{left} {'+' if ctx.op.text == 'ADDO' else '-'} {right}'

    def exitMulDiv(self, ctx: ThrobacParser.MulDivContext):
        left = self.c_translation[ctx.expr(0)]
        right = self.c_translation[ctx.expr(1)]
        self.c_translation[ctx] = f'{left} {'*' if ctx.op.text == 'CONGERO' else '/'} {right}'

    def exitNegation(self, ctx: ThrobacParser.NegationContext):
        self.c_translation[ctx] = f"(-{self.c_translation[ctx.expr()]})"

    def exitFuncCallExpr(self, ctx: ThrobacParser.FuncCallExprContext):
        self.c_translation[ctx] = self.c_translation[ctx.funcCall()]

    def exitFuncCallStmt(self, ctx: ThrobacParser.FuncCallStmtContext):
        self.c_translation[ctx] = f"{self.c_translation[ctx.funcCall()]};"

    def exitFuncCall(self, ctx: ThrobacParser.FuncCallContext):
        name = ctx.ID().getText()
        parameters = ",".join(
            self.c_translation[e]
            for e in ctx.expr()
        )
        self.c_translation[ctx] = f"{name}({parameters})"

    def exitReturn(self, ctx: ThrobacParser.ReturnContext):
        count = len(list(ctx.getChildren()))
        if count == 1:
            self.c_translation[ctx] = "return;"
        else:
            self.c_translation[ctx] = f"return {self.c_translation[ctx.getChild(0)]};"

    def exitScript(self, ctx: ThrobacParser.ScriptContext):
        func_defs = ctx.funcDef()
        header = HEADER
        declarations = "\n".join(self.func_declarations[f] for f in func_defs)
        main = self.c_translation[ctx.main()]
        definitions = "\n".join(self.c_translation[f] for f in func_defs)
        self.c_translation[ctx] = "\n".join(
            part for part in (header, declarations, MAIN_COMMENT, main, FUNCTION_DEFS_COMMENT, definitions) if part
        )

    def exitFuncDef(self, ctx: ThrobacParser.FuncDefContext):
        name = ctx.ID().getText()
        arguments = ", ".join(
            self.c_translation[nd]
            for nd in ctx.nameDef()
        )
        returnee = ctx.TYPE()
        if returnee:
            returnee = self.translate_type(returnee.getText())
        else:
            returnee = 'void'
        body = self.c_translation[ctx.body()]
        self.c_translation[ctx] = f"{returnee} {name}({arguments}) {body}"
        self.func_declarations[ctx] = f"{returnee} {name}({arguments});"

    def exitMain(self, ctx: ThrobacParser.MainContext):
        body = self.c_translation[ctx.body()]
        self.c_translation[ctx] = f"void main() {body}"

    def exitBody(self, ctx: ThrobacParser.BodyContext):
        var_block = ctx.varBlock()
        block = ctx.block()
        self.c_translation[ctx] = self.c_block("\n".join([
            self.c_translation[var_block],
            self.c_translation[block]
        ]))

    def exitVarBlock(self, ctx: ThrobacParser.VarBlockContext):
        self.c_translation[ctx] = "\n".join(
            self.c_translation[c]
            for c in ctx.getChildren()
        )

    def exitVarDec(self, ctx: ThrobacParser.VarDecContext):
        declaration = self.c_translation[ctx.nameDef()]
        self.c_translation[ctx] = declaration + ';'

    def exitNameDef(self, ctx: ThrobacParser.NameDefContext):
        name = ctx.ID().getText()
        t = ctx.TYPE().getText()
        self.c_translation[ctx] = f"{self.translate_type(t)} {name}"


    def exitBlock(self, ctx: ThrobacParser.BlockContext):
        self.c_translation[ctx] = self.c_block("\n".join(
            self.c_translation[c]
            for c in ctx.getChildren()
        ))

    def exitAssignment(self, ctx: ThrobacParser.AssignmentContext):
        self.c_translation[ctx] = f"{ctx.ID()} = {self.c_translation[ctx.expr()]};"

    def exitWhile(self, ctx: ThrobacParser.WhileContext):
        expr = self.c_translation[ctx.expr()]
        block = self.c_translation[ctx.block()]
        self.c_translation[ctx] = f"while ({expr}) {block}"

    def exitIf(self, ctx: ThrobacParser.IfContext):
        expr = self.c_translation[ctx.expr()]
        blocks = ctx.block()

        self.c_translation[ctx] = (
                f"if ({expr}) {self.c_translation[blocks[0]]}"
                + (f" else {self.c_translation[blocks[1]]}" if len(blocks) > 1 else "")
        )

    @staticmethod
    def cprintf(specifier: str, expr: str) -> str:
        return f'printf("{specifier}", {expr});'

    def exitPrintNumber(self, ctx: ThrobacParser.PrintNumberContext):
        self.c_translation[ctx] = self.cprintf("%d", self.c_translation[ctx.expr()])

    def exitPrintString(self, ctx: ThrobacParser.PrintStringContext):
        self.c_translation[ctx] = self.cprintf("%s", self.c_translation[ctx.expr()])

    def exitPrintBool(self, ctx: ThrobacParser.PrintBoolContext):
        self.c_translation[ctx] = self.cprintf("%s", f'({self.c_translation[ctx.expr()]})?"True":"False"')
