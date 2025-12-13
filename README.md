# Tiny-Language-Scanner
This program is a scanner (lexer) for the TINY programming language. It reads TINY source code from an input file, breaks it into tokens, and writes each token as "value , TYPE" into an output file. To run the scanner, 

use the command: python main.py <input_file> <output_file>. 

The input file should contain normal TINY code such as read x; write(x); x := 10 + y;, and the scanner will produce an output file listing recognized tokens like identifiers, numbers, keywords (read, write, if, then, repeat, end, until), symbols (;, :=, +, -, *, /, <, =, (, )), and UNKNOWN for invalid characters. The last token will always be EOF. This program helps verify and test the lexical structure of TINY programs.
