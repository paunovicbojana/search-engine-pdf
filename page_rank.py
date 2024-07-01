from collections import defaultdict
import re


class PageRank:
    def __init__(self):
        self.graph = defaultdict(list)
        self.rank = defaultdict(float)
        self.word_count = defaultdict(int)

    def add_edge(self, from_page, to_page):
        self.graph[from_page].append(to_page)

    def set_word_count(self, page, count):
        self.word_count[page] = count

    def calculate_page_rank(self, num_pages, d: float = 0.85, max_iterations: int = 100, tol: float = 1e-6):
        for page in range(1, num_pages + 1):
            self.rank[page] = 1.0 / num_pages

        for iteration in range(max_iterations):
            new_rank = defaultdict(float)
            for page in range(1, num_pages + 1):
                summation = 0
                for referring_page in self.graph:
                    if page in self.graph[referring_page]:
                        count = self.word_count[referring_page]
                        out_degree = len(self.graph[referring_page])
                        if out_degree > 0:
                            summation += self.rank[referring_page] * count / out_degree
                new_rank[page] = (1 - d) + d * summation
            
            if all(abs(new_rank[page] - self.rank[page]) < tol for page in range(1, num_pages + 1)):
                break
            
            self.rank = new_rank

    def get_page_rank(self):
        return dict(self.rank)

    def extract_links(self, text):
        pattern = re.compile(r'\b(?:see page|see pages|on page)\s+(\d+(?:\s*and\s*\d+)*)', re.IGNORECASE)
        matches = pattern.findall(text)
        links = []
        for match in matches:
            pages = re.split(r'\s*and\s*', match)
            for page in pages:
                links.append(int(page))
        return links
    
    def __str__(self) -> str:
        ans = ""
        for page, links in self.graph.items():
            ans += f"Page {page}: {links}\n"
        return ans