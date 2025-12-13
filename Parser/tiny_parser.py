# tiny_parser.py
from pathlib import Path
import sys


##Abstract Syntax Tree Node class
class ASTNode:
    def __init__(self, label, children=None):
        self.label = label
        self.children = children or []

#####Print the tree to the console
    def __repr__(self, level=0):
        ret = "  " * level + repr(self.label) + "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret


class TinyParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0



    # ---------------------------
    # Token Helpers
    # ---------------------------

##### return the current token without advancing
    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ('EOF','EOF')

##### return the current token and move one step forward 
    def advance(self):
        tok = self.peek()
        self.pos += 1
        return tok

##### match the current token with expected type , advance if match else raise error
    def match(self, expected_type):
        tok = self.peek()
        if tok[1] == expected_type:
            self.advance()
            return tok
        else:
            raise Exception(f"Syntax Error: Expected {expected_type} but got {tok}")






     # ---------------------------
     # EBNF Recursive Parsing
     # --------------------------- 

    # Program -> stmt_seq
    def parse_program(self):
        node = ASTNode("Program")
        node.children.append(self.parse_stmt_seq())

        ### Check for extra tokens after a valid program and ensure input ends exactly at EOF
        if self.peek()[1] != "EOF":
            lexeme, tok = self.peek()
            raise Exception(f"Unexpected token after valid program: '{lexeme}' ({tok})")
        return node


    # stmt_seq -> stmt { ; stmt }
    def parse_stmt_seq(self):
        node = ASTNode("StmtSeq")
        node.children.append(self.parse_stmt())

        while self.peek()[1] == 'SEMICOLON': 
            self.match('SEMICOLON')
            # Stop if the next token is NOT the start of a statement
            if self.peek()[1] not in ('IF', 'REPEAT', 'READ', 'WRITE', 'IDENTIFIER'):
                break
            node.children.append(self.parse_stmt())

        return node






    # stmt -> if | repeat | assign | read | write
    def parse_stmt(self):
        tok = self.peek()
        token_type = tok[1]
    
        if token_type == 'IF':
            return self.parse_if()
        elif token_type == 'REPEAT':
            return self.parse_repeat()
        elif token_type == 'READ':
            return self.parse_read()
        elif token_type == 'WRITE':
            return self.parse_write()
        elif token_type == 'IDENTIFIER':
            return self.parse_assign()
        else:
            raise Exception(f"Syntax Error")




    # if_stmt -> IF expr THEN stmt_seq [ELSE stmt_seq] END
    def parse_if(self):
        node = ASTNode("IfStmt")
        self.match('IF')
        node.children.append(self.parse_expr())
        self.match('THEN')
        then_branch = self.parse_stmt_seq()
        node.children.append(then_branch)
        
        if self.peek()[1] == 'ELSE':
            self.match('ELSE')
            else_branch = self.parse_stmt_seq()
            node.children.append(else_branch)
        
        self.match('END')
        return node




    # repeat_stmt -> REPEAT stmt_seq UNTIL expr
    def parse_repeat(self):
        node = ASTNode("RepeatStmt")
        self.match('REPEAT')
        body = self.parse_stmt_seq()
        node.children.append(body)
        
        self.match('UNTIL')
        condition = self.parse_expr()
        node.children.append(condition)
        return node




    # assign_stmt -> IDENTIFIER := expr
    def parse_assign(self):
        node = ASTNode("AssignStmt")
        identifier_tok = self.match('IDENTIFIER')
        identifier_node = ASTNode(f"Identifier({identifier_tok[0]})")
        node.children.append(identifier_node)
        
        self.match('ASSIGN')
        expr_node = self.parse_expr()
        node.children.append(expr_node)
        return node



    # read_stmt -> READ IDENTIFIER
    def parse_read(self):
        node = ASTNode("ReadStmt")   
        self.match('READ')
        identifier_tok = self.match('IDENTIFIER')
        identifier_node = ASTNode(f"Identifier({identifier_tok[0]})")
        node.children.append(identifier_node)
        return node




    # write_stmt -> WRITE exp
    def parse_write(self):
        node = ASTNode("WriteStmt")
        self.match('WRITE')
        expr_node = self.parse_expr()   
        node.children.append(expr_node)
        return node



    # expr -> simple_expr [ ( < | = ) simple_expr ]
    def parse_expr(self):
        left = self.parse_simple_expr()
        if self.peek()[1] in ('LESSTHAN', 'EQUAL'):  
            op_tok = self.advance()
            op_node = ASTNode(f"Op({op_tok[0]})")
            right = self.parse_simple_expr()
            return ASTNode("OpExpr", [op_node, left, right])
        return left


    

    # simple_expr -> term { (+|-) term }
    def parse_simple_expr(self):
        left = self.parse_term()
        while self.peek()[1] in ('PLUS', 'MINUS'):
            op_tok = self.advance()       
            op_node = ASTNode(f"Op({op_tok[0]})")
            right = self.parse_term()
            left = ASTNode("OpExpr", [op_node, left, right])
        return left




    # term -> factor { (*|/) factor }
    def parse_term(self):
        left = self.parse_factor()
        while self.peek()[1] in ('MULT', 'DIV'):
            op_tok = self.advance()             
            op_node = ASTNode(f"Op({op_tok[0]})")
            right = self.parse_factor()
            left = ASTNode("OpExpr", [op_node, left, right])
        return left





    # factor -> NUMBER | IDENTIFIER | ( expr )
    def parse_factor(self):
        tok = self.peek()

        # NUMBER
        if tok[1] == 'NUMBER':
            number_tok = self.advance()
            return ASTNode(f"Number({number_tok[0]})")

        # IDENTIFIER
        elif tok[1] == 'IDENTIFIER':
            ident_tok = self.advance()
            return ASTNode(f"Identifier({ident_tok[0]})")

        # ( expr )
        elif tok[1] == 'LPAREN':   # ( 
            self.match('LPAREN')
            expr_node = self.parse_expr()
            self.match('RPAREN')   # )
            return expr_node

        else:
            raise Exception(f"Syntax Error in factor: unexpected token {tok}")











def read_token_file(file_path):
    """
    Reads a token file where each line is:
    tokenvalue , tokentype
    Returns a list of (TokenValue, TokenType) .
    """
    tokens = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):  # skip empty or comment lines
                continue
            parts = line.split(',')
            if len(parts) != 2:
                raise Exception(f"Invalid token line: {line}")
            tokenValue = parts[0].strip()
            tokenType = parts[1].strip()
            tokens.append((tokenValue, tokenType))

        # Ensure EOF exists as the last token
    if not tokens or tokens[-1][1] != 'EOF':
        tokens.append(("EOF", "EOF"))

    return tokens





def main():
    # Determine input file path
    if len(sys.argv) == 2:
        input_file = Path(sys.argv[1])
    else:
        input_file = Path("tokens.txt")  # default filename

    if not input_file.exists():
        print(f"Error: Input file '{input_file}' does not exist.")
        return

    # Read tokens from file
    tokens = read_token_file(input_file)

    # Ensure EOF token is present
    if tokens[-1][1] != 'EOF':
        tokens.append(('EOF','EOF'))

    # Parse
    parser = TinyParser(tokens)
    try:
        ast = parser.parse_program()
        print("--- AST ---")
        print(ast)
        print("Parsing successful ")
    except Exception as e:
        print(f"Parsing failed : {e}")


if __name__ == "__main__":
    main()
