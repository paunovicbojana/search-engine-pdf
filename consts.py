TRIE_PATH = "library"
TEXT_PATH = "text"
DICTIONARY = "dictionary"
RESULTS = "search_results.pdf"

expression_priority = {
    "AND": 2,
    "OR": 1,
    "NOT": 3
}

def calculate_priority(expression):
    return expression_priority[expression]

GREEN = "\033[32m"
ORANGE = "\033[38;2;255;165;0m"
LIGHT_BLUE = "\033[94m"
RESET = "\033[0m"