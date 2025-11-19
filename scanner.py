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
        ch = self.peek()
        if not ch or not ch.isalpha():  # to ensure starting with a letter
            return None ## this is a number, this function should not handle it
    
        start = self.pos
        ## two conditions: is not None and is alphanumeric
        while self.peek() and self.peek().isalnum():
            self.advance()
        value = self.text[start:self.pos]
        if value.lower() in KEYWORDS: ## check for keywords in a case-insensitive manner (if case-sensitive, remove .lower())
            return (value, KEYWORDS[value.lower()])
        return (value, 'IDENTIFIER')

    ## expecting to return the value of the number as a string and its type as 'NUMBER'    ex: ('123', 'NUMBER')
    def collect_number(self):
        ch = self.peek()
        if not ch or not ch.isdigit():
            return None
        start = self.pos
        while self.peek() and self.peek().isdigit():
            self.advance()
        value = self.text[start:self.pos]
        return (value, 'NUMBER') 
        

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
        tokens = []
        while True:
            self.skip_whitespace()
            ch = self.peek()

            if ch is None:
                break
            if ch.isalpha():
                token = self.collect_identifier_or_keyword()
            elif ch.isdigit():
                token = self.collect_number()
            else:
                token = self. collect_operators_and_symbols()
            tokens.append(token)

        tokens.append(('EOF','EOF'))
        return tokens





def main():
    if len(sys.argv) != 3:
        print("Usage: python main.py <input_file> <output_file>")
        return

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist.")
        return

    text = input_path.read_text()

    lexer = TinyLexer(text)
    tokens = lexer.tokenize()

    with output_path.open('w', encoding='utf-8') as f:
        for value, ttype in tokens:
            f.write(f"{value} , {ttype}\n")

    print(f"Tokenization complete. {len(tokens)} tokens written to {output_path.resolve()}")
    print("--- Tokens ---")
    for value, ttype in tokens:
        print(f"{value} , {ttype}")

if __name__ == '__main__':
    main()






    