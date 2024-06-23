[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/KHzC7ivQ)

# Task 1

Wir haben uns dafür entschieden, die Hand als Eingabemethode zu verwenden. Deswegen haben wir auch das Google MediaPipe Handmodell verwendet, um genauere Werte zu bekommen. Es wird immer nur eine Hand erkannt (die erste, die erkannt wurde und falls diese nicht mehr sichtbar ist, kann auch zu einer anderen Hand gewechselt werden). Der Mauszeiger folgt dabei der Handmitte (erstes Gelenk des Mittelfingers). Man klickt, indem man Daumen und Zeigefinger berührt. Die linke Maustaste wird losgelassen, sobald sich die beiden Finger wieder voneinander entfernen.

Da die Dimensionen gleich zu beginn auf Bildschirmgröße eingestellt werden, ist ein Mapping nicht notwendig.

# Task 2

In der config.config-Datei können die Werte für den Fitts's Law Test angepasst werden. Hierfür werden max und min Werrte für die Distanz zwischen den Zielen und die Größe der Ziele angegeben. Die Anzahl der Versuche kann ebenfalls angepasst werden.

Aus den Distanzen und Größen werden dann zufällige Kombinationen generiert (mit Seed, damit jeder Tester die gleichen Kombinationen bekommt). Dies verhindert repetitive Muster.

# Task 3