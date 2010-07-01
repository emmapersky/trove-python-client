class Query:
        
    def __init__(self):
        self.services = []
        self.tags_optional = []
        self.tags_required = []
        self.date_from = None
        self.date_to = None
        self.force_update = False
        self.attributes = {}
        