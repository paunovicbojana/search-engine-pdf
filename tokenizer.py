import re
from consts import calculate_priority


class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value
    
    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

class Tokenizer:
    def __init__(self, text):
        self.text = text.upper()
        self.position = 0
        self.tokens = []
        self.token_specification = [
            ('PHRASE', r'"[^"]+"'),   # Phrase enclosed in double quotes
            ('AND',    r'\bAND\b'),   # AND operator
            ('OR',     r'\bOR\b'),    # OR operator
            ('NOT',    r'\bNOT\b'),   # NOT operator
            ('TERM',   r'[^\s()]+'),  # Term (any non-whitespace, non-parenthesis sequence)
            ('SKIP',   r'\s+'),       # Skip over spaces and tabs
            ('PREFIX', r'\*'),        # Prefix operator
            ('MISMATCH', r'.'),       # Any other character

        ]
        self.token_regex = re.compile('|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in self.token_specification))

    def tokenize(self):
        previous_token = None
        for match in self.token_regex.finditer(self.text):
            kind = match.lastgroup
            value = match.group(kind)
            if kind == 'SKIP':
                continue
            elif kind == 'MISMATCH':
                raise RuntimeError(f'Unexpected character: {value}')
            else:
                current_token = Token(kind, value)
                if previous_token and previous_token.type in ('AND', 'OR', 'NOT') and current_token.type in ('AND', 'OR', 'NOT'):
                    raise RuntimeError(f'Missing term between operators: {previous_token.value} and {current_token.value}')
                
                if current_token.type == 'PHRASE':
                    phrase_terms = value.strip('"').split()
                    for i, term in enumerate(phrase_terms):
                        self.tokens.append(Token('PHRASE', term))
                        if i < len(phrase_terms) - 1:
                            self.tokens.append(Token('AND', 'AND'))
                else:
                    if previous_token and previous_token.type == 'TERM' and current_token.type == 'TERM':
                        self.tokens.append(Token('OR', 'OR'))
                    self.tokens.append(current_token)
                
                previous_token = current_token
        
        return self.divide()

    def divide(self):
        terms = []
        string = ""
        current_terms = []
        for token in self.tokens:
            if token.type == 'TERM' or token.type == 'PHRASE':
                term = token.value.lower()
                if term.endswith('*'):
                    term = term[:-1]
                    terms.append((term, 'PREFIX'))
                elif token.type == 'PHRASE':
                    terms.append((term, 'PHRASE'))
                else:
                    terms.append((term, []))

            else:
                if current_terms:
                    terms.append((' '.join(current_terms), []))
                    current_terms = []
                priority = str(calculate_priority(token.type))
                string += priority
        if current_terms:
            terms.append((' '.join(current_terms), []))
        return terms, string