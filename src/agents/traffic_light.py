# src/agents/traffic_light.py
from mesa import Agent


class Traffic_Light(Agent):
    def __init__(self, unique_id, model, state=False, timeToChange=10, pair_id=None):
        super().__init__(unique_id, model)
        self.pair_id = pair_id
        self.timeToChange = timeToChange
        self._initial_state = state
        self.state = state
        self.orientation = getattr(self.model, "pair_orientations", {}).get(
            pair_id, "vertical"
        )

    def post_init(self):
        """Called after the agent is placed in the grid"""
        if self.pos is None:
            return

        # First, identify if we're part of a corner intersection
        corner_pairs = self.identify_corner_pairs()
        is_corner = self.pair_id in corner_pairs

        # For all traffic lights (since they're all corners)
        corner_group = self.get_corner_group()
        
        # Set states based on corner group and orientation
        if self.orientation == "horizontal":
            self.state = corner_group % 2 == 0
        else:  # vertical orientation
            self.state = corner_group % 2 == 1



    def identify_corner_pairs(self):
        """Identify pairs that are part of corner intersections"""
        corner_pairs = set()
        
        # Get both lights in our pair
        our_pair_lights = [light for light in self.model.traffic_lights if light.pair_id == self.pair_id]
        our_orientation = self.model.pair_orientations.get(self.pair_id)
        
        # For each light in our pair
        for our_light in our_pair_lights:  # Check from both positions in our pair
            our_x, our_y = our_light.pos
            
            for other_light in self.model.traffic_lights:
                if other_light.pair_id == self.pair_id:
                    continue
                    
                other_orientation = self.model.pair_orientations.get(other_light.pair_id)
                other_x, other_y = other_light.pos
                
                # Calculate Manhattan distance
                dx = abs(other_x - our_x)
                dy = abs(other_y - our_y)
                
                # Check if perpendicular and close enough
                if (our_orientation != other_orientation and 
                    our_orientation is not None and 
                    other_orientation is not None and
                    dx <= 2 and dy <= 2):
                    
                    corner_pairs.add(self.pair_id)
                    corner_pairs.add(other_light.pair_id)
        
        return corner_pairs

    def get_corner_group(self):
        """Get the corner group number for this traffic light"""
        # Group corners based on their position in the grid
        x, y = self.pos
        if y > self.model.grid.height / 2:
            return 1 if x < self.model.grid.width / 2 else 2
        else:
            return 3 if x < self.model.grid.width / 2 else 4

    def get_neighboring_pairs(self):
        """Get the traffic light pairs that intersect with this one"""
        neighbor_pairs = set()
        
        # Get both lights in our pair
        our_pair_lights = [light for light in self.model.traffic_lights if light.pair_id == self.pair_id]
        
        # For each light in our pair
        for our_light in our_pair_lights:
            our_x, our_y = our_light.pos
            
            # Find perpendicular pairs nearby
            for other_light in self.model.traffic_lights:
                if other_light.pair_id != self.pair_id:
                    other_x, other_y = other_light.pos
                    dx = abs(other_x - our_x)
                    dy = abs(other_y - our_y)
                    
                    # If perpendicular orientation and close enough
                    if (self.model.pair_orientations.get(other_light.pair_id) != 
                        self.model.pair_orientations.get(self.pair_id) and
                        dx <= 2 and dy <= 2):
                        neighbor_pairs.add(other_light.pair_id)
        
        return sorted(list(neighbor_pairs))

    def step(self):
        current_step = self.model.schedule.steps
        
        # Only let the pair controller handle changes
        if not self.is_pair_controller():
            return
            
        # Horizontal pairs change on multiples of timeToChange
        # Vertical pairs change on multiples of timeToChange + timeToChange/2
        if self.orientation == "horizontal":
            should_change = current_step % self.timeToChange == 0
        else:  # vertical
            should_change = current_step % self.timeToChange == self.timeToChange // 2
            
        if should_change:
            self.coordinate_light_change()

    def coordinate_light_change(self):
        """Coordinate light changes with neighboring intersections"""
        # Get all intersecting pairs
        neighbor_pairs = self.get_neighboring_pairs()
        new_state = not self.state
        
        # First, change our state
        pair_lights = [
            light
            for light in self.model.traffic_lights
            if light.pair_id == self.pair_id
        ]
        for light in pair_lights:
            light.state = new_state

        # Then force all intersecting pairs to opposite state
        for neighbor_id in neighbor_pairs:
            neighbor_lights = [
                light
                for light in self.model.traffic_lights
                if light.pair_id == neighbor_id
            ]
            for light in neighbor_lights:
                light.state = not new_state  # Set to opposite state


    def is_pair_controller(self):
        """Check if this traffic light controls its pair"""
        if not self.pair_id:
            return True
        pair_lights = [
            light
            for light in self.model.traffic_lights
            if light.pair_id == self.pair_id
        ]
        return self == min(pair_lights, key=lambda x: x.unique_id)

