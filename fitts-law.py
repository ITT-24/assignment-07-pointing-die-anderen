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

        #self.indexes = np.random.choice(list(range(len(self.target_parameters))), size=config["num_trials"], replace=False)
        self.indexes = list(range(len(self.target_parameters)))
        random.shuffle(self.indexes)
        self.targets = []
        self.round = -1
        self.round_time = 0
        self.clicks = []
        self.round_clicks = []
        self.start_time = time.time()
        self.index_of_difficulty = math.log2(2*config["min_target_distance"] / config["max_target_size"])

    def next_round(self):
        self.round += 1
        if self.round == (config["num_trials"]**2)*3:
            with open(OUTPUT_FILE, 'w') as file:
                for i in range(len(stats)):
                    stat = stats[i]
                    file.write(f"{stat[0]},{stat[1]},{stat[2]},{stat[3]},{stat[4]},{stat[5]},{stat[6]},{stat[7]}\n")
            pyglet.app.exit()
            window.close()
        else:
            print(self.round % config["num_trials"])
            self.round_time = 0

            self.round_clicks = []
            self.create_targets()
            self.targets[-1].next_target = True
            for i in range(self.round):
                self.next_target()
            self.start_time = time.time()
            self.index_of_difficulty = math.log2(2*self.target_parameters[self.indexes[(self.round)% len(self.indexes)]][0] / self.target_parameters[self.indexes[(self.round)% len(self.indexes)]][1])

    def click(self, x, y):
        print(f"target_parameters: {self.round}")
        target_distance, target_size = self.target_parameters[self.indexes[(self.round)% len(self.indexes)]]
        print(target_distance, target_size)
        # To be logged:
        # - Number of Clicks as ID
        # - User ID
        # - Device
        # - Latency
        # - Time since last hit
        # - Width of Target (constant)
        # - Distance from Target to Target (constant)
        # - Index of Difficulty
        
        for target in self.targets:
            if math.sqrt((target.x - x)**2 + (target.y - y)**2) < target.diameter and target.next_target :
                self.clicks.append((x, y))
                self.round_clicks.append((x, y))
                if len(self.round_clicks) != 1:
                    stats.append([len(self.clicks), USER_ID, DEVICE, LATENT, self.round_time, target_distance, target_size, self.index_of_difficulty])
                self.start_time = time.time()
  
                self.next_target()
                break

        if len(self.round_clicks) >= config["target_num"]+1:
            self.next_round()

    def create_targets(self):
        self.targets = []
        num_targets = config["target_num"]

        angle_step = 2 * math.pi / num_targets
        target_distance, target_size = self.target_parameters[self.indexes[(self.round) % len(self.indexes)]]

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


law_test = FittsLaw()

last_move = time.time()

mouse_cursor = pyglet.shapes.Circle(0, 0, 8, color=(0, 0, 255))
# set anchor position to the center of the circle
#mouse_cursor.anchor_position = (4, 4)

#mouse_cursor = window.get_system_mouse_cursor(window.CURSOR_DEFAULT)

# mouse_image = pyglet.image.load('./curser.png')
# mouse_image.anchor_x = 0
# mouse_image.anchor_y = 0
# mouse_cursor = pyglet.sprite.Sprite(mouse_image)
# mouse_cursor.scale = 0.1

def move_mouse(dt, x,y):
    global mouse_cursor
    mouse_cursor.x = x
    mouse_cursor.y = y

    #mouse.position = (x, y)

@window.event
def on_mouse_enter(x, y):
    global mouse_cursor
    mouse_cursor.x = x
    mouse_cursor.y = y

@window.event
def on_mouse_motion(x, y, dx, dy):
    # global last_move
    # if time.time() - last_move < LATENT:
    #     # simulate latency by moving the mouse back to the previous position unless the latency has passed
    #     # but due to it not putting the mouse position instantly, the moouse flickers a lot, and not really "lags"
    #     mouse.position = (mouse.position[0] - dx, mouse.position[1] + dy)
    #     return
    # last_move = time.time()
    pyglet.clock.schedule_once(move_mouse, LATENT, x,y)

@window.event
def on_mouse_press(x, y, _button, _modifiers):
    global law_test
    print(f"round: {law_test.round}")
    if law_test.round != (config["num_trials"]**2)*3+1:
        law_test.click(x, y)

start_time = time.time()

law_test.next_round()
law_test.targets[-1].next_target = True

@window.event
def on_draw():
    global law_test
    global mouse_cursor
    window.clear()        
    law_test.draw_targets()
    law_test.round_time = time.time() - law_test.start_time
    #pyglet.text.Label(f'Rounds: {law_test.round+1} / {(config['num_trials']**2)*3} ', x=10, y=WINDOW_HEIGHT-20).draw()#
    #pyglet.text.Label(f'Time: {law_test.round_time} ', x=10, y=WINDOW_HEIGHT-60).draw()
    mouse_cursor.draw()

window.set_mouse_visible(False)
window.set_fullscreen(True)
pyglet.app.run()