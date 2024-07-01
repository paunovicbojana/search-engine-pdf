import pickle


class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, page_num, position):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        if "positions" not in node.children:
            node.children["positions"] = []
        node.children["positions"].append((page_num, position))
        node.is_end_of_word = True

    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return []  
            node = node.children[char]
        return node.children.get("positions")
    
    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        words_with_positions = []
        self._dfs(node, prefix, words_with_positions)
        return words_with_positions

    def _dfs(self, node, prefix, words_with_positions):
        if node.is_end_of_word:
            words_with_positions.append((prefix, node.children.get("positions", [])))
        for char, next_node in node.children.items():
            if char != "positions":
                self._dfs(next_node, prefix + char, words_with_positions)

def serialize(data):
    return pickle.dumps(data)

def deserialize(data):
    return pickle.loads(data)