class Query:
    
    def __init__(self):
        self.services = None
        self.tags_optional = []
        self.tags_required = []
        self.date_from = None
        self.date_to = None
        self.force_update = False
        self.attributes = {}
        self.page = 1
        self.count = 50
        self.geo = {} 
        self.order_by = []       
        self.identities_by_id = []
        
    def add_geo_bounds(self, lower_left_coords, upper_right_coords):
        self.geo['bounds'] = { 'sw': lower_left_coords,
                            'ne': upper_right_coords}

    def add_geo_near(self, center_point, radius=5): 
        self.geo['near'] = {    
                            'center': center_point, 
                            'radius': radius
                        }
    
    def add_order_by(self, value):
        self.order_by.append(value)

    def remove_order_by(self, value):
        self.order_by.remove(value)
    
    def add_identity_id(self, id):
        self.identities_by_id.append(id)
        
    def remove_identity_id(self, id):
        self.identities_by_id.remove(id)
        
class Result:
    
    def __init__(self):
        self.total_number_of_results = 0
        self.count = 0
        self.page = 1
        self.objects = []
       
    def __str__(self):
        return "Result - Count: %s, Page %s, Total number of results: %s, Results: %s" % (self.count, self.page, self.total_number_of_results, self.objects) 
    
    def __repr__(self):
        return "<troveclient.Objects.Result instance with count %s, total_number_of_results %s and page %s>"  % (self.count, self.total_number_of_results, self.page)
    
class Photo:
    
    def __init__(self):
        self.service = ""
        self.title = ""
        self.owner = ""
        self.description = ""
        self.id = ""
        self.urls = {}  # thumbnail, large  //tn:48,96,192
        self.tags = {}
        self.date = ""
        self.album_id = ""
        self.license = ""
        self.height = ""
        self.width = ""
        self.tags = ""
        self.loc = None
        self.public = False
        self.trove_id = ""

    def __str__(self):
        return 'Photo "%s" from %s on %s' % (self.title, self.owner, self.service)
    
    def __repr__(self):
        return "<troveclient.Objects.Photo instance with id %s from %s@%s>" % (self.id, self.owner, self.service)
