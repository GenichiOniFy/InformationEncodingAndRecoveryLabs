class Node:
    def __init__(self, value, freq, left=None, right=None):
        self.Value = value
        self.Freq = freq
        self.Left = left
        self.Right = right
    def __lt__(self, other):
        return self.Freq < other.Freq
