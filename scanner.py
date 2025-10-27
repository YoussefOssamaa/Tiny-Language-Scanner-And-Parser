from pathlib import Path
import sys

# Token definitions
KEYWORDS = {
    'if': 'IF',
    'then': 'THEN',
    'end': 'END',
    'repeat': 'REPEAT',
    'until': 'UNTIL',
    'read': 'READ',
    'write': 'WRITE'
}

SINGLE_CHAR_TOKENS = {
    ';': 'SEMICOLON',
    '<': 'LESSTHAN',
    '=': 'EQUAL',
    '+': 'PLUS',
    '-': 'MINUS',
    '*': 'MULT',
    '/': 'DIV',
    '(': 'OPENBRACKET',
    ')': 'CLOSEDBRACKET'
}



class TinyLexer:

    ### Initialize with input text
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.length = len(text)

    ### retrun the current character without advancing
    def peek(self):
        if self.pos < self.length:
            return self.text[self.pos]
        return None

    ### return the current character and advance the position by 1
    def advance(self):
        ch = self.peek()
        if ch is not None:
            self.pos += 1
        return ch


    ### Skip whitespace and comments , tabs, newlines , comments enclosed in { ... }
    def skip_whitespace(self):
        while True:
            ch = self.peek()
            if ch is None:
                return
            if ch.isspace():
                self.advance()
            # Skip comments of the form { ... } if present
            elif ch == '{':
                self.advance()  # skip '{'
                while True:
                    ch = self.peek()
                    if ch is None or ch == '}':
                        self.advance()  # skip '}' if present
                        break
                    self.advance()
            else:
                return
            

            

    ## expecting to return the value and its type either identifier or keyword   ex: ('read', 'READ') or ('x', 'IDENTIFIER')
    def collect_identifier_or_keyword(self):
        return 




    ## expecting to return the value of the number as a string and its type as 'NUMBER'    ex: ('123', 'NUMBER')
    def collect_number(self):
        return 
    


    ## expecting to return the value and its type for operators and symbols  ex: (':=', 'ASSIGN') or (';', 'SEMICOLON') and check for unrecognized symbols also
    def collect_operators_and_symbols(self):
        ch = self.peek()
        if ch == ':':
            self.advance()
            if self.peek() == '=':
                self.advance()
                return (':=', 'ASSIGN')
            else:
                return (':', 'UNKNOWN')
        elif ch in SINGLE_CHAR_TOKENS:
            self.advance()
            return (ch, SINGLE_CHAR_TOKENS[ch])
        else:
            self.advance()
            return (ch, 'UNKNOWN')
        
    
"""
the function should return a list called tokens,
you can use the functions we created above (collect_identifier_or_keyword, collect_number, collect_operators_and_symbols, skip_whitespace, peek, advance)
"""
    def tokenize(self):


            ## if ch.isalpha():

            ## ch.isdigit()

            ## if ch == ':' or ch in SINGLE_CHAR_TOKENS:

            ## if unrecognized character

        return tokens





def main():


## Prepare the input file as a string called text



    lexer = TinyLexer(text)
    tokens = lexer.tokenize()


# Write tokens to output.txt



if __name__ == '__main__':
    main()
