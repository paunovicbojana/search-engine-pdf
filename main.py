from pdf_parser import PDFParser
from search_engine import SearchEngine
from tokenizer import Tokenizer
from consts import ORANGE, GREEN, RESET


if __name__ == "__main__":
    parser = PDFParser("Data Structures and Algorithms in Python.pdf")
    search_engine = SearchEngine(parser.trie, parser.text, parser.generate_graph())
    print(f"{ORANGE}\nWelcome to the search engine!{RESET}\n")
    print("Make sure to read the instructions before using the search engine.")
    print(f" - Use {GREEN}AND{RESET}/{GREEN}OR{RESET}/{GREEN}NOT{RESET} for more specific search queries.")
    print(f" - Add {GREEN}*{RESET} after a word for autocomplete suggestions (e.g., radi* matches radio, radix, etc.).")
    print(f" - Use {GREEN}\"\"{RESET} for exact phrase search.")
    print(f" - Utilize the {GREEN}Did you mean?{RESET} feature for spelling suggestions.\n")

    while True:
        query = input(f"\n{ORANGE}  Enter your query: {RESET}")
        print()
        if query.lower() == "x":
            print("Goodbye!\n")
            break
        query = query.replace("(", "").replace(")", "")
        is_only_words = True
        forbidden = [" and ", " or ", " not ", "*", '"']
        is_only_words = not any(f in query.lower() for f in forbidden)
        if is_only_words:
            did_you_mean = parser.did_you_mean(query)
            if query != did_you_mean:
                anw = input(f"Did you mean {GREEN}{did_you_mean.upper()}{RESET} (y/n): ")
                print()
                if anw.lower() == "y":
                    query = did_you_mean
        tokenizer = Tokenizer(query)
        terms, operations = tokenizer.tokenize()
        search_engine.search(terms, operations)