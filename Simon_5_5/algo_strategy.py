import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # define exit_locations for our attacks
        self.stage_1 = 12
        self.stage_2 = 36
        self.breaking_locations = []
        self.remove_turn = []
        self.exit_locations_1 = [[6, 9], [21, 19], [24, 12], [25, 12], [26, 13], [23, 11]]
        self.exit_locations_2 = [[14, 11]]
        self.scout_spawn_location_options = [[13, 0], [14, 0], [8, 5], [19 ,5]]
        self.essential_locations = [[0, 13], [27, 13]]
        self.essential_locations_2 = [[1, 12], [26, 12]]

        self.attacked_locations = []
        # First, place basic defenses
        self.detect_scored_on_locations(game_state)
        for location in self.essential_locations:
            for unit in game_state.game_map[location]:
                if unit.player_index == 0 and unit.unit_type == WALL and unit.health/unit.max_health < 0.55:
                    game_state.attempt_remove(location)
                    self.attacked_locations.append(location)
        if game_state.turn_number > 20:
            for location in self.essential_locations:
                for unit in game_state.game_map[location]:
                    if unit.player_index == 0 and unit.unit_type == WALL and unit.health/unit.max_health < 1:
                        game_state.attempt_remove(location)
                        self.attacked_locations.append(location)

        for location in self.essential_locations_2:
            for unit in game_state.game_map[location]:
                if unit.player_index == 0 and unit.unit_type == WALL and unit.health/unit.max_health < 0.35:
                    game_state.attempt_remove(location)
        
        for location in self.scored_on_locations:
            if location[0]>=14 and location[1]>10:
                game_state.attempt_spawn(WALL, [24, 12])
                game_state.attempt_spawn(TURRET, [24, 11])
            if location[0]<14 and location[1]>10:
                game_state.attempt_spawn(WALL, [3, 12])
                game_state.attempt_spawn(TURRET, [3, 11])


        
        self.build_defences(game_state)
        if len(self.attacked_locations) != 0:
            if self.essential_locations[0] in self.attacked_locations:
                game_state.attempt_spawn(WALL, [3, 12])
                game_state.attempt_spawn(TURRET, [3, 11])
                

            if self.essential_locations[1] in self.attacked_locations:
                game_state.attempt_spawn(WALL, [24, 12])
                game_state.attempt_spawn(TURRET, [24, 11])
        game_state.attempt_upgrade([[3, 11], [24, 11], [3, 12], [24, 12]])

        # Now build reactive defenses based on where the enemy scored
        # self.build_reactive_defense(game_state)

        self.upgrade_defences(game_state, nums = 0)

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number == 0:
            pass
        else:
            # if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[17, 18]) > 30:
                # self.demolisher_line_strategy(game_state)
                # They don't have many units in the front so lets figure out their least defended area and send Scouts there.
            if game_state.turn_number < self.stage_1:
                if game_state.turn_number % 3 == 0:
                    # Only attack every other turn

                    # If they have many units in the front we can build a line for our demolishers to attack them at long range.
                    # Now let's analyze the enemy base to see where their defenses are concentrated.
                    if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[17, 18]) > 30:
                        self.demolisher_line_strategy(game_state)
                        scout_spawn_location_options = self.scout_spawn_location_options
                        best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                        game_state.attempt_spawn(SCOUT, best_location, 1000)
                    else:
                    # Sending more at once is better since attacks can only hit a single scout at a time
                    # To simplify we will just check sending them from back left and right
                        scout_spawn_location_options = self.scout_spawn_location_options
                        best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                        game_state.attempt_spawn(SCOUT, best_location, 1000)
                elif game_state.turn_number % 3 == 1:
                    self.build_active_defense(game_state)
                else:
                    self.build_active_defense(game_state)
                    game_state.attempt_remove(self.exit_locations_2)
                
            elif game_state.turn_number >= self.stage_1 and game_state.turn_number < self.stage_2: 
                if game_state.turn_number % 4 == 0 and game_state.turn_number < 24:
                    # Only attack every other turn
                    if game_state.turn_number == 11:
                        pass
                    elif self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[17, 18]) > 30:
                        self.demolisher_line_strategy(game_state)
                        scout_spawn_location_options = self.scout_spawn_location_options
                        best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)

                        game_state.attempt_spawn(SCOUT, best_location, 1000)
                    else:
                        scout_spawn_location_options = self.scout_spawn_location_options
                        best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                        game_state.attempt_spawn(SCOUT, best_location, 1000)
                elif game_state.turn_number % 4 == 1 and game_state.turn_number >= 24:
                    if game_state.turn_number == 11:
                        pass
                    elif self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[17, 18]) > 30:
                        self.demolisher_line_strategy(game_state)
                        scout_spawn_location_options = self.scout_spawn_location_options
                        best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)

                        game_state.attempt_spawn(SCOUT, best_location, 1000)
                    else:
                        scout_spawn_location_options = self.scout_spawn_location_options
                        best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                        game_state.attempt_spawn(SCOUT, best_location, 1000)
                else:
                    self.build_active_defense(game_state)
                    game_state.attempt_remove(self.exit_locations_2)
                    # If they have many units in the front we can build a line for
            
            else:
                if game_state.turn_number % 6 == 1:
                    # Only attack every other turn
                    if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[17, 18]) > 30:
                        self.demolisher_line_strategy(game_state)
                        scout_spawn_location_options = self.scout_spawn_location_options
                        best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)

                        game_state.attempt_spawn(SCOUT, best_location, 1000)
                    else:
                        scout_spawn_location_options = self.scout_spawn_location_options
                        best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                        game_state.attempt_spawn(SCOUT, best_location, 1000)
                else:
                    self.build_active_defense(game_state)
                    game_state.attempt_remove(self.exit_locations_2)

            # Lastly, if we have spare SP, let's build some supports
            support_locations = self.basic_support_locations
            game_state.attempt_spawn(SUPPORT, support_locations)
            game_state.attempt_upgrade(support_locations)

    def upgrade_defences(self, game_state, wall_locations = None, nums = 2):
        if wall_locations is None:
            locations = self.basic_wall_locations
        else:
            locations = wall_locations
        temp = 0
        for location in locations:
            for unit in game_state.game_map[location]:
                if unit.unit_type == WALL and temp < nums and (not unit.upgraded) and unit.health/unit.max_health < 0.33:
                    game_state.attempt_upgrade(location)
                    temp += 1           
        

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        # turret_locations = [[0, 13], [27, 13], [8, 11], [19, 11], [13, 11], [14, 11]]
        turret_locations = [[12, 10], [16, 10], [16, 9], [12, 9]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        
        # Place walls in front of turrets to soak up damage for them
        # wall_locations = [[8, 12], [19, 12]]
        wall_locations = [[0, 13], [27, 13], [1, 12], [26, 12], [2, 11], [25, 11], [12, 11], [16, 11], 
                          [13, 12], [15, 12], [2, 12], [25, 12], [13, 10], [15, 10], [13, 9], [15, 9]]
        support_locations = [[11, 9], [17, 9], [10, 9], [18 ,9]]

        self.basic_turret_locations = turret_locations
        self.basic_wall_locations = wall_locations
        self.basic_support_locations = support_locations
        self.important_wall_locations = [[2, 12], [25, 12], [12, 11], [16, 11], [13, 10], [15, 10], [13, 9], [16, 9]]
        # round 0
        game_state.attempt_spawn(WALL, wall_locations[:9])
        for x in range(3, 11):
            game_state.attempt_spawn(WALL, [x, 10])
            game_state.attempt_spawn(WALL, [27-x, 10])
        game_state.attempt_spawn(WALL, [11, 10])
        game_state.attempt_spawn(TURRET, turret_locations[:2])
        game_state.attempt_upgrade(turret_locations[0])

        # round 1
        game_state.attempt_spawn(WALL, wall_locations[9])
        game_state.attempt_upgrade(wall_locations[:2])
        
        # round 2
        game_state.attempt_spawn(WALL, wall_locations[10:14])

        # round 3
        game_state.attempt_spawn(SUPPORT, support_locations[0])
        game_state.attempt_upgrade(support_locations[0])
        
        # round 4
        game_state.attempt_upgrade(turret_locations[1])

        # round 5
        game_state.attempt_upgrade(wall_locations[2:4])

        # round 6
        game_state.attempt_spawn(WALL, wall_locations[14:])
        game_state.attempt_spawn(TURRET, turret_locations[2:])

        # round 7
        game_state.attempt_upgrade(turret_locations[2:])

        # round 8~
        game_state.attempt_upgrade(self.important_wall_locations)

        # upgrade walls so they soak more damage
        #game_state.attempt_upgrade(wall_locations)
    def detect_scored_on_locations(self, game_state):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        for location in self.scored_on_locations:
            self.breaking_locations.append([location[0], location[1]])

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        self.detect_scored_on_locations(game_state)
        if len(self.breaking_locations) != 0:
            for location in self.breaking_locations:
                if location[0] < 2:
                    game_state.attempt_spawn(TURRET, [1, 12])
                    game_state.attempt_upgrade([1, 12])
                if location[0] > 25:
                    game_state.attempt_spawn(TURRET, [26, 12])
                    game_state.attempt_upgrade([26, 12])
                    break
                
            

    def build_active_defense(self, game_state):
        turret_locations_stage_1 = [[11, 8], [16, 8]]
        wall_locations_stage_1 = [[12, 8], [15, 8]]
        support_locations_stage_1 = self.basic_support_locations

        turret_locations_stage_2  = turret_locations_stage_1 + [[11, 7], [15, 7]]
        wall_locations_stage_2 = wall_locations_stage_1 + [[12, 7], [14, 7]]
        support_locations_stage_2 = support_locations_stage_1 + [[9, 9], [19, 9]]

        wall_locations_stage_3 = []
        support_locations_stage_3 =  [[11, 8], [17, 9], [10, 8], [18, 8], [8, 8], [19, 8]]
        turret_locations_stage_3 = [[11, 6], [16, 6], [12, 5], [16, 5], [11, 4], [16, 4], 
                                                               [11, 3], [15, 3]]
        guard_walls = [[12, 6], [15, 6], [13, 5], [15, 5], [12, 4], [15, 4], 
                                                               [12, 3], [14, 3]]

        if game_state.turn_number < self.stage_1:
            game_state.attempt_spawn(TURRET, turret_locations_stage_1)
            game_state.attempt_spawn(WALL, wall_locations_stage_1)
            game_state.attempt_upgrade(turret_locations_stage_1)
            game_state.attempt_upgrade(wall_locations_stage_1)
            
        if game_state.turn_number >= self.stage_1 and game_state.turn_number < self.stage_2:

            game_state.attempt_spawn(TURRET, turret_locations_stage_1)
            game_state.attempt_upgrade(turret_locations_stage_1)

            game_state.attempt_spawn(TURRET, turret_locations_stage_2)

            game_state.attempt_spawn(WALL, wall_locations_stage_2)
            game_state.attempt_spawn(SUPPORT, support_locations_stage_2)
            game_state.attempt_upgrade(turret_locations_stage_2)
            game_state.attempt_upgrade(wall_locations_stage_2)
            game_state.attempt_upgrade(support_locations_stage_2)

            game_state.attempt_upgrade([[2, 11], [25, 11]])

        if game_state.turn_number >= self.stage_2:
            game_state.attempt_spawn(TURRET, turret_locations_stage_2)
            game_state.attempt_spawn(WALL, wall_locations_stage_2)
            game_state.attempt_spawn(SUPPORT, support_locations_stage_2)
            game_state.attempt_upgrade(turret_locations_stage_2)
            game_state.attempt_upgrade(wall_locations_stage_2)
            game_state.attempt_upgrade(support_locations_stage_2)

            game_state.attempt_spawn(WALL, wall_locations_stage_3)
            game_state.attempt_upgrade([[13, 12], [15, 12]])
            game_state.attempt_upgrade([[3, 11],[24, 11],[3,12],[24,12]])

            for i in range(len(turret_locations_stage_3)):
                game_state.attempt_spawn(WALL, guard_walls[i])
                if turret_locations_stage_3[i] != [11, 3]:
                    game_state.attempt_spawn(TURRET, turret_locations_stage_3[i])
                if i<6:
                    game_state.attempt_spawn(SUPPORT, support_locations_stage_3[i])

                game_state.attempt_upgrade(turret_locations_stage_3[i])
                game_state.attempt_upgrade(guard_walls[i])
                if i < 6:
                    game_state.attempt_upgrade(support_locations_stage_3[i])
            



    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state, nums = 2):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        #for x in range(27, 5, -1):
            #game_state.attempt_spawn(cheapest_unit, [x, 10])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], nums)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
