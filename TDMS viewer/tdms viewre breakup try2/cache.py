class TableCache:
    def __init__(self):
        self.headers = []
        self.quick_view_data = []
        self.full_data = {}
        self.plot_keys = set()
        self.max_rows = 0
        self.quick_view_size = 1000
        self.is_fully_loaded = False
        self.visible_columns = set()

class SignalCache:
    def __init__(self):
        self.x_data = None
        self.y_data = None
