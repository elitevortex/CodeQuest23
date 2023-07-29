import random
import sys
import heapq

import comms
from object_types import ObjectTypes

class Game:
    """
    Stores all information about the game and manages the communication cycle.
    Available attributes after initialization will be:
    - tank_id: your tank id
    - objects: a dict of all objects on the map like {object-id: object-dict}.
    - width: the width of the map as a floating point number.
    - height: the height of the map as a floating point number.
    - current_turn_message: a copy of the message received this turn. It will be updated everytime `read_next_turn_data`
        is called and will be available to be used in `respond_to_turn` if needed.
    """
    def __init__(self):
        tank_id_message: dict = comms.read_message()
        self.tank_id = tank_id_message["message"]["your-tank-id"]
        self.enemy_tank_id = tank_id_message["message"]["enemy-tank-id"]

        self.current_turn_message = None

        # variables for moving away from boundary
        # distance away from boundary
        self.allowable_boundary_distance = 100
        self.moving_ticks = 0

        # We will store all game objects here
        self.objects = {}

        # Get the current position of your tank
        self.my_tank_pos = self.objects.get(self.tank_id)

        # Get current position of enemy
        self.enemy_tank_pos = self.objects.get(self.enemy_tank_id)

        next_init_message = comms.read_message()
        while next_init_message != comms.END_INIT_SIGNAL:
            # At this stage, there won't be any "events" in the message. So we only care about the object_info.
            object_info: dict = next_init_message["message"]["updated_objects"]

            # Store them in the objects dict
            self.objects.update(object_info)

            # Read the next message
            next_init_message = comms.read_message()

        # We are outside the loop, which means we must've received the END_INIT signal

        # Let's figure out the map size based on the given boundaries

        # Read all the objects and find the boundary objects
        boundaries = []
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.BOUNDARY.value:
                boundaries.append(game_object)

        # The biggest X and the biggest Y among all Xs and Ys of boundaries must be the top right corner of the map.

        # Let's find them. This might seem complicated, but you will learn about its details in the tech workshop.
        biggest_x, biggest_y = [
            max([max(map(lambda single_position: single_position[i], boundary["position"])) for boundary in boundaries])
            for i in range(2)
        ]

        self.width = biggest_x
        self.height = biggest_y

    def read_next_turn_data(self):
        """
        It's our turn! Read what the game has sent us and update the game info.
        :returns True if the game continues, False if the end game signal is received and the bot should be terminated
        """
        # Read and save the message
        self.current_turn_message = comms.read_message()

        # Break out condition
        if self.current_turn_message == comms.END_SIGNAL:
            return False

        # Delete the objects that have been deleted
        # NOTE: You might want to do some additional logic here. For example check if a powerup you were moving towards
        # is already deleted, etc.
        for deleted_object_id in self.current_turn_message["message"]["deleted_objects"]:
            try:
                del self.objects[deleted_object_id]
            except KeyError:
                pass

        # Update your records of the new and updated objects in the game
        # NOTE: you might want to do some additional logic here. For example check if a new bullet has been shot or a
        # new powerup is now spawned, etc.
        self.objects.update(self.current_turn_message["message"]["updated_objects"])

        return True

    def respond_to_turn(self):
        """
        This is where you should write your bot code to process the data and respond to the game.
        """

        self.close_to_boundary()

        # Write your code here... For demonstration, this bot just shoots randomly every turn.

        # First element is the closest power up to our tank
        # index has 3 elements -> distance between the tank n the power up, position of the powerup, type of the powerup
        self.power_ups_distances = []
    
        # # Iterate through the updated objects
        for updated_object in self.current_turn_message["message"]["updated_objects"]:
            # if the object has no velocity, just position (Walls: 3 & 4, PowerUps: 7, Boundary is type 5)
            if updated_object["type"] == ObjectTypes.POWERUP.value:
                self.update_powerUp_distances(updated_object["position"], updated_object["powerup_type"])
            # if the object has velocity + position (Tank: 1, Bullet: 2, Closing Boundary is type 6)

        
    def update_powerUp_distances(self, position: list(), powerup_type: str) -> None:
        """
        takes in the details of the position and powerup type of a Power Up object
        position: position of the power up
        powerup_type: "HEALTH" / "SPEED" / "DAMAGE"

        modifies the power_ups_reachability array
        """
        heapq.heappush(self.power_ups_distances, (distance(self.my_tank_pos, position), position, powerup_type))


    # checks if we are close to boundary
    def close_to_boundary(self):

        # check if we are currently moving
        if (self.moving_ticks > 0):
            self.moving_ticks -= 1

            # if moved enough, stop moving
            if (self.moving_ticks == 0):
                comms.post_message({"move": -1})
            return
        
        # finds closing boundary
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.CLOSING_BOUNDARY.value:
                closing_boundary = game_object
                break
        
        # finds top, bottom, left and right
        positions = closing_boundary["position"]
        top = positions[3][1]
        right = positions[3][0]
        bottom = positions[1][1]
        left = positions[1][0]

        # finds tank coordinates
        my_tank = self.objects.get(self.tank_id)
        my_tank_x = my_tank["position"][0]
        my_tank_y = my_tank["position"][1]

        # checks distances between tank and boundary
        if (my_tank_y - bottom < self.allowable_boundary_distance
            or top - my_tank_y < self.allowable_boundary_distance
            or my_tank_x - left < self.allowable_boundary_distance
            or right - my_tank_x < self.allowable_boundary_distance):
            self.moving_ticks = 5 # MAGIC
            comms.post_message({"path": [self.width/2, self.height/2]})

    def check_wall(self):
        '''
        Checks if we hit a boundary, wall, or tank

        "destructibleWall-id": {
            "type": 4,
            "position": [356.12, 534.39],
            "hp": 1
        }mkkn

        "boundary-id": {
            "type": 6, 
            "position": [
                [1.50, 998.5],
                [1.50, 1.50],
                [1798.5, 1.50],
                [1798.5, 998.5]
            ], 
            "velocity": [
                [10.0, 0.0],
                [0.0, 10.0],
                [-10.0, 0.0],
                [0.0, -10.0]
            ]
        }

        "wall-id": {
            "type": 3,
            "position": [356.12, 534.39]
        }
        '''
        # WALL
        # check if our position is near another position
        

        pass


    def shoot_tank(self):
        '''
        Shoots tank towards a desired target 
        Considerations
            - Nearby walls that could cause reboself.enemy_tank_pos[1] - self.my_tank_pos[1]und (don't shoot perpendicularly) - includes boundaries
            - Shoot at their projected position -
            - 
        '''
        # See where their tank is,
        # Check if there's a wall between s and them
        
        # shoot
        # Maths to find angle
        y_diff = self.enemy_tank_pos[1] - self.my_tank_pos[1]
        x_diff = self.enemy_tank_pos[0] - self.my_tank_pos[0]
        shoot_angle = math.atan(y_diff // x_diff)
        comms.post_message({"shoot": shoot_angle})



import math
## HELPER FUNCTIONS 
def distance(point1, point2):

    return math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)

def calculate_projected_position(position, velocity, time):
    x = position[0] + velocity[0] * time
    y = position[1] + velocity[1] * time
    return [x, y]

def prioritize_bullets(self, tank):
    '''
    Class function
    Returns list of bullets based on their closeness to hitting the current tank 
            (based on tank and bullet trajectory)
    '''
    tank_position = tank["position"]
    tank_velocity = tank["velocity"]
    bullet_priority = []

    for bullet in self.objects.values():
        if bullet == ObjectTypes.BULLET:
 
            bullet_position = bullet["position"]
            bullet_velocity = bullet["velocity"]

            # Calculate the time of intersection between the bullet and the tank
            time_x = (tank_position[0] - bullet_position[0]) / (bullet_velocity[0] - tank_velocity[0])
            time_y = (tank_position[1] - bullet_position[1]) / (bullet_velocity[1] - tank_velocity[1])
            time = max(time_x, time_y)

            # Calculate the projected position of the tank and bullet at the time of intersection
            tank_projected_position = calculate_projected_position(tank_position, tank_velocity, time)
            bullet_projected_position = calculate_projected_position(bullet_position, bullet_velocity, time)

            # Calculate the distance between the tank and the bullet's projected position
            distance_to_bullet = distance(tank_projected_position, bullet_projected_position)

            bullet_priority.append((bullet, distance_to_bullet))

    # Sort bullets by distance in ascending order (closer bullets have higher priority)
    bullet_priority.sort(key=lambda x: x[1])

    # Return a sequence of bullets in order of priority
    return [bullet_id for bullet_id, _ in bullet_priority]





