import fitz
import re
from trie import *
import os
from consts import *
import Levenshtein
from page_rank import PageRank


class PDFParser:
    def __init__(self, document):
        self.document = fitz.open(document)
        self.text = {}
        self.trie = Trie()
        self.all_words = set()
        self.deserialize_all()

    def generate_graph(self):
        graph = PageRank()
        regex = r"see\s*page\s*(\d+)|see\s*pages\s*(\d+)\s*and\s*(\d+)|on\s*page\s*(\d+)"
        for page in self.document:
            page_number = page.number
            text: str = self.text[page_number]
            matches = re.finditer(regex, text, re.IGNORECASE)
            for match in matches:
                for group in match.groups():
                    if group is not None:
                        destination_page = int(group)
                        if destination_page >= 0 and destination_page < self.document.page_count:
                            graph.add_edge(page_number, destination_page)
        return graph

    def get_text(self):
        for page in self.document:
            page_number = page.number
            page_text = page.get_text("text")
            self.text[page_number] = page_text
            words = self.split_words(page_text)
            self.all_words.update(words)
            for position, word in enumerate(words):
                self.trie.insert(word, page_number, position)
        serialized_trie = serialize(self.trie)
        serialized_text = serialize(self.text)
        serialized_all_words = serialize(self.all_words)
        with open(TRIE_PATH, "wb") as file:
            file.write(serialized_trie)
        with open(TEXT_PATH, "wb") as file:
            file.write(serialized_text)
        with open(DICTIONARY, "wb") as file:
            file.write(serialized_all_words)
    
    def __len__(self):
        return len(self.text)
    
    def __getitem__(self, k):
        return self.text[k]
    
    def split_words(self, text):
        words = re.split(r'\W+', text)
        words = [word.lower() for word in words if word]
        return words
    
    def deserialize_all(self):
        if not os.path.exists(TRIE_PATH) or os.path.getsize(TRIE_PATH) == 0:
            self.get_text()
        else:
            with open(TRIE_PATH, "rb") as file:
                data = file.read()
                self.trie = deserialize(data)
            with open(TEXT_PATH, "rb") as file:
                data = file.read()
                self.text = deserialize(data)
            with open(DICTIONARY, "rb") as file:
                data = file.read()
                self.all_words = deserialize(data)

    def did_you_mean(self, query):
        tokens = query.split()
        output = []
        for index, token in enumerate(tokens):
            output.append(self.suggest_correction(token))

            if index < len(tokens) - 1:
                output.append(" ")

        return "".join(output)

    def suggest_correction(self, typed_word):
        min_distance = float("inf")
        closest_word = None

        for word in self.all_words:
            distance = Levenshtein.distance(typed_word, word)
            if distance < min_distance:
                min_distance = distance
                closest_word = word

        return closest_word
    

class PDFHandler:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open()
    
    def create_initial_pdf(self, output_path):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Results:\n\n", fontsize=12)
        doc.save(output_path)
        return doc

    def add_text(self, doc, text, page_height=792, page_width=612, margin_top=90, margin_bottom=90, margin_left=72, margin_right=72, line_height=14, fontsize=12):
        y = margin_top
        usable_height = page_height - margin_top - margin_bottom
        usable_width = page_width - margin_left - margin_right
        
        average_char_width = 0.5 * fontsize

        for snippet in text:
            clean_text = re.sub(r'\x1b\[[0-9;]*m', '', snippet)
            text_lines = clean_text.split('\n')

            for line in text_lines:
                words = line.split()
                current_line = ""
                
                for word in words:
                    test_line = f"{current_line} {word}".strip()
                    text_width = len(test_line) * average_char_width

                    if text_width <= usable_width:
                        current_line = test_line
                    else:
                        if y + line_height > page_height - margin_bottom:
                            doc.new_page()
                            y = margin_top

                        doc[-1].insert_text((margin_left, y), current_line, fontsize=fontsize)
                        y += line_height
                        current_line = word

                if current_line:
                    if y + line_height > page_height - margin_bottom:
                        doc.new_page()
                        y = margin_top

                    doc[-1].insert_text((margin_left, y), current_line, fontsize=fontsize)
                    y += line_height

    def highlight_text(self, doc, keyword, phrase):
        if phrase:
            for page in doc:
                phrase_instances = page.search_for(keyword)
                for inst in phrase_instances:
                    highlight = page.add_highlight_annot(inst)
                    highlight.update()
        else:
            keywords = keyword.split()
            for page in doc:
                phrase_instances = page.search_for(keyword)
                for inst in phrase_instances:
                    highlight = page.add_highlight_annot(inst)
                    highlight.update()

                for word in keywords:
                    word_instances = page.search_for(f" {word} ")
                    for inst in word_instances:
                        highlight = page.add_highlight_annot(inst)
                        highlight.update()

    def save_pdf(self, doc, output_path):
        if len(doc) == 0:
            raise ValueError("Cannot save an empty PDF document.")
        doc.save(output_path)