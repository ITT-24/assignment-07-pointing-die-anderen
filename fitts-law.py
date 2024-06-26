import sys
import os
import pyglet
import math
import time
import random
import numpy as np
from pynput.mouse import Controller, Listener
import time

# get system arguments
args = sys.argv

# check if the number of arguments is correct
if len(args) != 6:
    print("Usage: python fitts-law.py <user_id> <device> <simulated_latency> <config_file> <output_file>")
    sys.exit(1)

USER_ID = args[1]
DEVICE = args[2]
LATENT = float(args[3])
config_file = args[4]
OUTPUT_FILE = args[5]

mouse = Controller()

config = {}
with open(config_file, 'r') as file:
    for line in file:
        # Skip comments
        if line.startswith('#') or line.strip() == '':
            continue
        # Split the line into key and value
        key, value = line.split('=')
        # Trim whitespace and convert value to integer
        config[key.strip()] = int(value.strip())

stats = []
random.seed(42)
np.random.seed(42)

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
    def __init__(self):
        self.target_distances = np.linspace(config["min_target_distance"], config["max_target_distance"], config["num_trials"])
        self.target_sizes = np.linspace(config["max_target_size"], config["min_target_size"], config["num_trials"])

        # Create a meshgrid and reshape it to get all combinations of distances and sizes
        self.target_parameters = np.array(np.meshgrid(self.target_distances, self.target_sizes)).T.reshape(-1, 2)

        self.indexes = np.random.choice(list(range(len(self.target_parameters))), size=5, replace=False)
        self.targets = []
        self.round = 0
        self.round_time = 0
        self.clicks = []
        self.round_clicks = []
        self.start_time = time.time()
        self.index_of_difficulty = math.log2(2*config["min_target_distance"] / config["max_target_size"])

    def next_round(self):
        if self.round == config["num_trials"]:
            with open(OUTPUT_FILE, 'w') as file:
                for stat in stats:
                    file.write(f"{stat[0]},{stat[1]},{stat[2]},{stat[3]},{stat[4]},{stat[5]},{stat[6]},{stat[7]}\n")
            pyglet.app.exit()
            window.close()
        else:
            self.round += 1
            self.round_time = 0

            self.round_clicks = []
            self.create_targets()
            self.targets[-1].next_target = True
            self.start_time = time.time()
            self.index_of_difficulty = math.log2(2*self.target_parameters[self.indexes[self.round-1]][0] / self.target_parameters[self.indexes[self.round-1]][1])

    def click(self, x, y):
        self.clicks.append((x, y))
        self.round_clicks.append((x, y))
        target_distance, target_size = self.target_parameters[self.round]

        # To be logged:
        # - Number of Clicks as ID
        # - User ID
        # - Device
        # - Latency
        # - Time since last hit
        # - Width of Target (constant)
        # - Distance from Target to Target (constant)
        # - Index of Difficulty

        stats.append([len(self.clicks), USER_ID, DEVICE, LATENT,self.round_time, target_distance, target_size, self.index_of_difficulty])
        
        self.start_time = time.time()
  
        self.next_target()

        if len(self.round_clicks) >= config["target_num"]:
            self.next_round()

    def create_targets(self):
        self.targets = []
        num_targets = config["target_num"]

        angle_step = 2 * math.pi / num_targets
        target_distance, target_size = self.target_parameters[self.indexes[self.round-1]]

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
        if self.round != config["num_trials"]+1:
            for target in self.targets:
                if target.next_target:
                    pyglet.shapes.Circle(target.x, target.y, target.diameter, color=(255, 0, 0)).draw()
                else:
                    pyglet.shapes.Circle(target.x, target.y, target.diameter, color=(255, 255, 255)).draw()


law_test = FittsLaw()

last_move = time.time()

@window.event
def on_mouse_motion(x, y, dx, dy):
    global last_move
    # Achtung! x und y sind koordinaten im Fenster, nicht auf dem Bildschirm, daher muss
    # die Mausposition korrekt gemapped werden
    window_x, window_y = window.get_location()
    if time.time() - last_move < LATENT:
        mouse.position = (mouse.position[0]-dx, mouse.position[1]-dy)
        return

    mouse.position = (window_x +x, window_y + WINDOW_HEIGHT-y)
    last_move = time.time()

@window.event
def on_mouse_press(x, y, _button, _modifiers):
    global law_test
    if law_test.round != config["num_trials"]+1:
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
    pyglet.text.Label(f"Rounds: {law_test.round} / {config["num_trials"]} ", x=10, y=WINDOW_HEIGHT-20).draw()#
    pyglet.text.Label(f"Time: {law_test.round_time} ", x=10, y=WINDOW_HEIGHT-60).draw()


pyglet.app.run()