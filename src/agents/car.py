class Car(Agent):
    """
    Car agent that moves in the city
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "moving"
        self.speed = 1

    def move(self):
        """
        Moves the car one cell to the right
        """
        # Get next position to the right
        next_pos = (self.pos[0] + 1, self.pos[1])
        
        # If we reach the right edge, go back to left
        if next_pos[0] >= self.model.grid.width:
            next_pos = (0, self.pos[1])
            
        # Check if next position is a road and is empty of cars
        cell_contents = self.model.grid.get_cell_list_contents(next_pos)
        has_car = any(isinstance(obj, Car) for obj in cell_contents)
        has_road = any(isinstance(obj, Road) for obj in cell_contents)
        
        # Only move if there's a road and no car
        if has_road and not has_car:
            self.model.grid.move_agent(self, next_pos)
            self.state = "moving"
        else:
            self.state = "stopped"

    def step(self):
        """
        Moves the car
        """
        self.move()
