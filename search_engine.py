import re
from collections import defaultdict
from page_rank import PageRank
from consts import *
from pdf_parser import PDFHandler
import os

class SearchEngine:
    def __init__(self, trie, pages_text, graph):
        self.trie = trie
        self.page_rank = None
        self.pages_text = pages_text
        self.pdf_handler = PDFHandler(RESULTS)
        self.page_rank = graph

    def search(self, terms, operations):
        if not terms:
            return {}
        
        res = {}
        term_results = []
        phrase = False
        prefix = False
        
        for term in terms:
            if term[1] == 'PREFIX':
                prefix = True
                positions = self.trie.starts_with(term[0])
                sorted_positions = sorted(positions, key=lambda x: len(x[0]))
                for p in sorted_positions:
                    print(p[0])
                continue

            elif term[1] == 'PHRASE':
                phrase = True

            results = defaultdict(list)
            positions = self.trie.search(term[0])
            if not positions:
                term_results.append((term[0], []))
                continue
            for data in positions:
                results[data[0]].append(data[1])
            sorted_results = sorted(results.items(), key=lambda item: (len(item[1]), self.page_rank.rank.get(item[0], 0)), reverse=True)
            term_results.append((term[0], sorted_results))

        if not term_results:
            return res

        combined_results = term_results[0][1]
        for i in range(1, len(term_results)):
            op = operations[i-1]
            next_results = term_results[i][1]

            if op == '2':  # AND operation
                combined_results = self.and_operation(combined_results, next_results)
            elif op == '1':  # OR operation
                combined_results = self.or_operation(combined_results, next_results)
            elif op == '3':  # NOT operation
                combined_results = self.not_operation(combined_results, next_results)

        if phrase:
            combined_results = self.phrase_search(combined_results, terms)
        
        res['combined'] = combined_results
        
        if prefix:
            return {}
        
        self.display_results(res, " ".join(term[0] for term in terms), phrase)
    
    def phrase_search(self, combined_results, terms):
        final_results = []
        term_words = [term[0] for term in terms]
        phrase_length = len(term_words)

        for page, positions in combined_results:
            text = self.pages_text[page].lower()
            words = re.findall(r'\b\w+\b', text)
            phrase_positions = []
            
            for pos in positions:
                if pos + phrase_length > len(words):
                    continue  
                if all(words[pos + i] == term_words[i] for i in range(phrase_length)):
                    phrase_positions.append(pos)
                    
            if phrase_positions:
                final_results.append((page, phrase_positions))
                
        return final_results

    def and_operation(self, results1, results2):
        result_dict = defaultdict(list)
        set_results2 = {doc for doc, _ in results2}
        for doc, pos in results1:
            if doc in set_results2:
                result_dict[doc].extend(pos)
        return sorted(result_dict.items(), key=lambda item: (len(item[1]), self.page_rank.rank.get(item[0], 0)), reverse=True)

    def or_operation(self, results1, results2):
        result_dict = defaultdict(lambda: {'positions': [], 'count': 0})
        for doc, pos in results1:
            result_dict[doc]['positions'].extend(pos)
            result_dict[doc]['count'] += 1
        for doc, pos in results2:
            result_dict[doc]['positions'].extend(pos)
            result_dict[doc]['count'] += 1

        sorted_results = sorted(result_dict.items(), key=lambda item: (item[1]['count'], len(item[1]['positions']), self.page_rank.rank.get(item[0], 0)), reverse=True)
        return [(doc, info['positions']) for doc, info in sorted_results]

    def not_operation(self, results1, results2):
        result_dict = defaultdict(list)
        set_results2 = {doc for doc, _ in results2}
        for doc, pos in results1:
            if doc not in set_results2:
                result_dict[doc].extend(pos)
        return sorted(result_dict.items(), key=lambda item: (len(item[1]), self.page_rank.rank.get(item[0], 0)), reverse=True)

    def display_results(self, results, query, phrase):
        if not results['combined']:
            print("\033[41m\033[1;37m{}\033[0m".format("No results found!"))
            return

        combined_results = results['combined']

        if os.path.exists(RESULTS):
            os.remove(RESULTS)
        
        combined_pdf = self.pdf_handler.create_initial_pdf(RESULTS)
       
        try:
            snippets = []
            for rank, (page_num, _) in enumerate(combined_results[:10], start=1):
                snippet = self.get_snippet(page_num, query, phrase)
                highlighted_snippet = self.highlight_words(snippet, query, phrase)
                snippet_text = f"Rank: {rank}, Page: {page_num}\n{highlighted_snippet}\n{'-' * 80}"
                snippets.append(snippet_text)
            self.pdf_handler.add_text(combined_pdf, snippets)
            self.pdf_handler.save_pdf(combined_pdf, RESULTS)
            self.pdf_handler.highlight_text(combined_pdf, query, phrase)
            self.pdf_handler.save_pdf(combined_pdf, RESULTS)
            
        except ValueError as e:
            print(f"Error: {e}")
        
        for rank, (page_num, _) in enumerate(combined_results, start=1):
            if rank % 10 == 0:
                quest = input("\nSee more (y/n): ")
                print()
                if quest.lower() != "y":
                    break
            snippet = self.get_snippet(page_num, query, phrase)
            highlighted_snippet = self.highlight_words(snippet, query, phrase)
            print(f"{LIGHT_BLUE}Rank: {rank}, Page: {page_num}{RESET}")
            print(highlighted_snippet)
            print(f"{ORANGE}{'-' * 92}{RESET}")

    def get_snippet(self, page_num, query, phrase):
        text = self.pages_text[page_num].lower()
        text_stripped = re.sub(r'[^\w\s]', '', text)
        
        snippets = []
        snippet_length = 30

        if phrase:
            phrase_pattern = re.compile(r'\b' + re.escape(query.lower()) + r'\b')
            phrase_positions = [match.start() for match in phrase_pattern.finditer(text_stripped)]

            for pos in phrase_positions:
                start = max(0, pos - snippet_length)
                end = min(len(text_stripped), pos + len(query) + snippet_length)
                snippet = text_stripped[start:end]
                if snippet not in snippets:
                    snippets.append(snippet)
        else:
            query_list = re.split(r'\W+', query.lower())
            query_list = [word for word in query_list if word]
            data = []
            
            for q in query_list:
                word_positions = [m.start() for m in re.finditer(r'\b' + re.escape(q) + r'\b', text_stripped)]
                data.extend(word_positions)
            
            for pos in sorted(set(data)):
                start = max(0, pos - snippet_length)
                end = min(len(text_stripped), pos + len(max(query_list, key=len)) + snippet_length)
                snippet = text_stripped[start:end]
                if snippet not in snippets:
                    snippets.append(snippet)
        
        if snippets:
            return " ... ".join(snippets)
        return ""

    def highlight_words(self, snippet, query, phrase):
        if phrase:
            snippet = re.sub(rf"(?i)\b{re.escape(query)}\b", rf"{GREEN}\g<0>{RESET}", snippet)
        else:
            words = re.split(r'\W+', query)
            words = [word.lower() for word in words if word]
            for word in words:
                snippet = re.sub(rf"(?i)\b{re.escape(word)}\b", rf"{GREEN}\g<0>{RESET}", snippet)
        return snippet