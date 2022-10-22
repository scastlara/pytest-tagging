class FakeCache:
    def __init__(self):
        self.data = {}

    def set(self, key, value):
        self.data[key] = value

    def get(self, key, default):
        return self.data.get(key, default)
