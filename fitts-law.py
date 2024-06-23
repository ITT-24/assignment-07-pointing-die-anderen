import sys
import os
import pyglet
import math
import time
from itertools import combinations
from itertools import permutations
import random
import numpy as np

print(list(range(1, 10, 2 )))
# get system arguments
args = sys.argv

# check if the number of arguments is correct
if len(args) != 6:
    print("Usage: python fitts-law.py <user_id> <device> <simulated_latency> <config_file> <output_file>")
    sys.exit(1)

user_id = args[1]
device = args[2]
latent = args[3]
config_file = args[4]
output_file = args[5]

random.seed(42)

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 1000
window = pyglet.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT)
 
class Target():
    def __init__(self, x, y, diameter):
        self.x = x
        self.y = y
        self.diameter = diameter
        self.hit = False
        self.next_target = False

class FittsLaw():
    def __init__(self, user_id, latent, config_file, output_file):
        self.user_id = user_id
        self.latent = latent
        self.config_file = self.read_config(config_file)
        #self.target_distances = list(range(self.config_file["starting_target_distance"], self.config_file["ending_target_distance"], self.config_file["num_trials"]))
        #self.target_sizes = list(range(self.config_file["starting_target_size"], self.config_file["ending_target_size"], self.config_file["num_trials"]))
        #self.target_parameters = random.shuffle(list(combinations(self.target_distances, self.target_sizes)))
        #self.target_parameters = np.array(np.meshgrid(np.array(self.target_distances), np.array(self.target_sizes))).T.reshape(-1, 2) 

        self.target_distances = np.linspace(self.config_file["starting_target_distance"], self.config_file["ending_target_distance"], self.config_file["num_trials"])
        self.target_sizes = np.linspace(self.config_file["starting_target_size"], self.config_file["ending_target_size"], self.config_file["num_trials"])

        # Create a meshgrid and reshape it to get all combinations of distances and sizes
        self.target_parameters = np.array(np.meshgrid(self.target_distances, self.target_sizes)).T.reshape(-1, 2)


        self.output_file = output_file
        self.targets = []
        self.round = 0
        self.round_time = 0
        self.clicks = []
        self.round_clicks = []
        self.start_time = time.time()
        self.stats = []
        self.index_of_difficulty = math.log2(2*self.config_file["starting_target_distance"] / self.config_file["starting_target_size"])

    def read_config(self, file_path):
        config = {}
        with open(file_path, 'r') as file:
            for line in file:
                # Skip comments
                if line.startswith('#') or line.strip() == '':
                    continue
                # Split the line into key and value
                key, value = line.split('=')
                # Trim whitespace and convert value to integer
                config[key.strip()] = int(value.strip())
        print(config)
        return config

    def next_round(self):
        if self.round == self.config_file["num_trials"]:
            with open(self.output_file, 'w') as file:
                for stat in self.stats:
                    file.write(f"{stat[0]},{stat[1]},{stat[2]},{stat[3]}\n")
            sys.exit(0)

        self.round += 1
        self.round_time = 0

        self.round_clicks = []
        self.create_targets()
        self.targets[-1].next_target = True
        self.start_time = time.time()

    def click(self, x, y):
        self.clicks.append((x, y))
        self.round_clicks.append((x, y))
        target_distance, target_size = self.target_parameters[self.round]

        # To be logged:
        # - Time since last hit
        # - Width of Target (constant)
        # - Distance from Target to Target (constant)

        self.stats.append([len(self.clicks), self.user_id, self.latent,self.round_time, target_distance, target_size, self.index_of_difficulty])
        
        self.start_time = time.time()
  
        self.next_target()

        if len(self.round_clicks) >= self.config_file["target_num"]:
            self.next_round()

    def create_targets(self):
        self.targets = []
        num_targets = self.config_file["target_num"]
        print(self.target_parameters)
        angle_step = 2 * math.pi / num_targets
        target_distance, target_size = self.target_parameters[self.round]

        for i in range(num_targets):
            angle = angle_step * i
            x = WINDOW_WIDTH/2 + (target_distance * num_targets/10) * math.cos(angle)
            y = WINDOW_HEIGHT/2 + (target_distance  * num_targets/10) * math.sin(angle)
            self.targets.append(Target(x, y, target_size))

    def next_target(self):
        for target in self.targets:
            if target.next_target:
                self.targets[self.targets.index(target)].next_target = False
                self.targets[int((self.targets.index(target) + len(self.targets)/2)% len(self.targets))].next_target = True
                break  

    def draw_targets(self):
        for target in self.targets:
            if target.next_target:
                pyglet.shapes.Circle(target.x, target.y, target.diameter, color=(255, 0, 0)).draw()
            else:
                pyglet.shapes.Circle(target.x, target.y, target.diameter, color=(255, 255, 255)).draw()


law_test = FittsLaw(user_id, latent, config_file, output_file)

@window.event
def on_mouse_press(x, y, _button, _modifiers):
    global law_test
    print("Mouse pressed at: ", x, y)
    law_test.click(x, y)

start_time = time.time()

@window.event
def on_draw():
    global law_test
    window.clear()
    if law_test.round == 0:
        law_test.next_round()
        law_test.targets[-1].next_target = True
    law_test.draw_targets()
    law_test.round_time = time.time() - law_test.start_time
    pyglet.text.Label(f"Rounds: {law_test.round} / {law_test.config_file["num_trials"]} ", x=10, y=WINDOW_HEIGHT-20).draw()#
    pyglet.text.Label(f"Time: {law_test.round_time} ", x=10, y=WINDOW_HEIGHT-60).draw()


pyglet.app.run()