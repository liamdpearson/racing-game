import edit_file

class Marker():
    def __init__(self):
        self.counter = 0

        self.positions = edit_file.get_positions().split(",")
        for pos in self.positions:
            pos.split()
        
        print(self.positions)
    
    def update_pos(self, new_x, new_y):

        self.x = new_x
        self.y = new_y