"""
Test cases for the Throbac to C transpiler

Author: OCdt Syed, OCdt Noyes

Version: 2026-01-29
"""

import unittest

import generic_parser
from antlr4 import ParseTreeWalker
from throbac.ThrobacLexer import ThrobacLexer
from throbac.ThrobacParser import ThrobacParser
from throbac2c import Throbac2CTranslator


def as_c(source, start_rule):
    """
    Translates the given Throbac source string to C, using start_rule for parsing.
    """
    parse_tree = generic_parser.parse(source, start_rule, ThrobacLexer, ThrobacParser)
    walker = ParseTreeWalker()
    translator = Throbac2CTranslator()
    walker.walk(translator, parse_tree)
    if parse_tree in translator.c_translation:
        return translator.c_translation[parse_tree]
    else:
        return 'No generated C found'


"""
 `TEST_CASES` is a list of triples, where the first element is the expected
 C equivalent, the second is the Throbac source, and the third is the parser
 rule to be used to parse the Throbac. These are intended to be processed by
 the `test_all_cases` method in the `TranslationTest` class below.
 
For complex tests you may wish to write separate test cases, rather than using
the `TEST_CASES` approach.

The comments in `TEST_CASES` suggest a reasonable order in which to proceed with
implementation of your `Throbac2CTranslator`.
 """

TEST_CASES = [
    # numbers
    ('0', '.NIL.', 'expr'),
    ('7', '.NIL.NIL.VII.', 'expr'),  # trim leading zeroes
    ('1234567890', '.I.II.III.IV.V.VI.VII.VIII.IX.NIL.', 'expr'),
    # strings
    ('"HELLO.WORLD"', '^HELLO.WORLD^', 'expr'),
    ('""', '^^', 'expr'),
    (r'"YO\nYOYO\n\n"', '^YO+YOYO++^', 'expr'),  # Note the use of raw string to permit \n
                                                 # alternative would have been '"YO\\nYOYO\\n\\n"'
    # booleans
    ('1', 'VERUM', 'expr'),
    ('0', 'FALSUM', 'expr'),
    # variables
    ('count', 'count', 'expr'),
    ('asdgefawfawda', 'asdgefawfawda', 'expr'),
    # parentheses
    ('(55)', '(.V.V.)', 'expr'),
    ('(5)', '(.V.)', 'expr'),
    ('5 * (1 + 2)', '.V. CONGERO (.I. ADDO .II.)', 'expr'),
    # compare
    ('1 <= 5', '.I.INFRA.IDEM.V.', 'expr'),
    # concatenation
    ('__throbac_cat("HELLO.","WORLD")', '^HELLO.^IUNGO^WORLD^', 'expr'),
    # add and subtract
    ('(5 - (1 + 2))', '(.V. SUBTRAHO (.I. ADDO .II.))', 'expr'),
    # multiply and divide
    ('5 * (1 / 2)', '.V. CONGERO (.I. PARTIO .II.)', 'expr'),
    ('1 - 5 * (1 / 2)', '.I. SUBTRAHO .V. CONGERO (.I. PARTIO .II.)', 'expr'),
    # negation
    ('(-(-(-1)))', 'NI NI NI VERUM', 'expr'),
    # function call
    ('apple(1)', 'APUD VERUM VOCO apple', 'funcCall'),
    ('apple(count)', 'APUD count VOCO apple', 'funcCall'),
    # function call expression
    ('apple(count,1)', 'APUD count,VERUM VOCO apple', 'expr'),
    # function call statement
    ('apple(count,1,rotten);', 'APUD count,VERUM,rotten VOCO apple', 'statement'),
    # assignment
    ('count = 37;', 'count .III.VII. VALORUM', 'statement'),
    ('count = getnum(something);', 'count APUD something VOCO getnum VALORUM', 'statement'),
    # return
    ('return 5;', '.V. REDEO', 'statement'),
    ('return 1 + 3 * (2 - 1);', '.I. ADDO .III. CONGERO (.II. SUBTRAHO .I.) REDEO', 'statement'),
    # print int
    ('printf("%d", 55);','.V.V. NUMERUS.IMPRIMO','statement'),
    ('printf("%d", apples);','apples NUMERUS.IMPRIMO','statement'),
    # print string
    ('printf("%s", "HELLO");',' ^HELLO^ LOCUTIO.IMPRIMO','statement'),
    # print bool
    ('printf("%s", (1)?"True":"False");','VERUM VERITAS.IMPRIMO','statement'),

    ## ALL TEST CASES BELOW ARE MULTI LINE AND ARE TESTED IN TESTCASE.THROBAC GENERATED C FILE IS COMMENTED TO HIGHLIGHT EACH SPECIFIC PART
    # block
    # while
    # if
    # nameDef
    ('int newint','newint : NUMERUS','nameDef')
    # varDec
    # varBlock
    # body
    # main
    # funcdef
    # script
]


class TranslationTest(unittest.TestCase):

    def test_all_cases(self):
        self.maxDiff = None
        for c, throbac, rule in TEST_CASES:
            with self.subTest(c=c,
                              throbac=throbac,
                              rule=rule):
                self.assertEqual(c, as_c(throbac, rule))

if __name__ == '__main__':
    unittest.main()