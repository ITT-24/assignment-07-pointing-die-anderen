import sys
import os
import pyglet
import math
import time

# get system arguments
args = sys.argv

# check if the number of arguments is correct
if len(args) != 5:
    print("Usage: python fitts-law.py <user_id> <simulated_latency> <config_file> <output_file>")
    sys.exit(1)

user_id = args[1]
latent = args[2]
config_file = args[3]
output_file = args[4]


WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 1000
window = pyglet.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT)
 
class Target():
    def __init__(self, x, y, diameter):
        self.x = x
        self.y = y
        self.diameter = diameter
        self.hit = False

class FittsLaw():
    def __init__(self, user_id, latent, config_file, output_file):
        self.user_id = user_id
        self.latent = latent
        self.config_file = self.read_config(config_file)
        self.output_file = output_file
        self.targets = []
        self.accuracy = 1
        self.round_time = 0
        self.round_accuracy = 1
        self.clicks = []
        self.round_clicks = []
        self.start_time = time.time()
        self.stats = []

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
                    file.write(f"{stat[0]},{stat[1]},{stat[2]}\n")
            sys.exit(0)

        self.round += 1
        self.round_time = 0
        self.round_accuracy = 1

        self.round_clicks = []
        self.create_targets()
        self.start_time = time.time()

    def click(self, x, y):
        self.stats.append([self.round_time, self.round_accuracy/(len(self.round_clicks)+1)])
        self.last_click = time.time()
        self.clicks.append((x, y))
        self.round_clicks.append((x, y))
        for target in self.targets:
            if (x - target.x)**2 + (y - target.y)**2 <= (target.diameter)**2 and not target.hit:
                target.hit = True
                self.accuracy += 1
                self.round_accuracy += 1
                break
        
        if len(self.round_clicks) >= self.config_file["target_num"] and all(target.hit for target in self.targets):
            self.next_round()

    def create_targets(self):
        self.targets = []
        num_targets = self.config_file["target_num"]

        angle_step = 2 * math.pi / num_targets

        for i in range(num_targets):
            angle = angle_step * i
            x = WINDOW_WIDTH/2 + (self.config_file["target_distance"] * self.config_file["target_num"]/10) * math.cos(angle)
            y = WINDOW_HEIGHT/2 + (self.config_file["target_distance"] * self.config_file["target_num"]/10) * math.sin(angle)
            self.targets.append(Target(x, y, self.config_file["target_size"]))
            

    def draw_targets(self):
        for target in self.targets:
            if target.hit:
                pyglet.shapes.Circle(target.x, target.y, target.diameter, color=(0, 255, 0)).draw()
            else:
                pyglet.shapes.Circle(target.x, target.y, target.diameter, color=(255, 0, 0)).draw()

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
    law_test.draw_targets()
    law_test.round_time = time.time() - law_test.start_time
    pyglet.text.Label(f"Rounds: {law_test.round} / {law_test.config_file["num_trials"]} ", x=10, y=WINDOW_HEIGHT-20).draw()#
    pyglet.text.Label(f"Accuracy: {law_test.accuracy/(len(law_test.clicks)+1)} ", x=10, y=WINDOW_HEIGHT-40).draw()
    pyglet.text.Label(f"Time: {law_test.round_time} ", x=10, y=WINDOW_HEIGHT-60).draw()


pyglet.app.run()