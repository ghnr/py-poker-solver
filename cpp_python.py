from time import time, sleep
import random
from ctypes import cdll
from ctypes import c_uint
import numpy as np
from constants import CARDS, CARDS_REVERSE

# C++ library for heavy computations

# 65,000,000 H/s C++ -O3 -m64
# 20,000,000 H/s C++ -O3 (no errors found with O3)
# 15,000,000 H/s C++
# 125,000 H/s Python calling C++

lib = cdll.LoadLibrary("main.dll")
lib.HandEval_evaluate.restype = c_uint
lib.main_main()
hands = []

deck_ = list(range(0, 52))
for i in range(100000):
    hands.append(random.sample(deck_, 7))

hero_h = [CARDS['As'], CARDS['Ts']]
villain_h = [CARDS['3s'], CARDS['3c']]
results = []


def reverse_cards(board):
    s = ""
    for card in board:
        s += CARDS_REVERSE[card] + " "
    return s


def simulate():
    deck = list(range(0, 52))
    dead_cards = hero_h + villain_h
    np.random.shuffle(deck)
    board = []
    for j in range(5):
        card = deck[j]
        x = j + 5
        while card in dead_cards:
            card = deck[x]
            x += 5
        board.append(card)
    
    hero_score = lib.HandEval_evaluate(hero_h[0], hero_h[1], board[0], board[1], board[2], board[3], board[4])
    
    villain_score = lib.HandEval_evaluate(villain_h[0], villain_h[1], board[0], board[1], board[2], board[3], board[4])
    
    if hero_score > villain_score:
        results.append(1)
    elif hero_score < villain_score:
        results.append(2)
    else:
        results.append(0)


z = 0
runtime = time()
while z < 100000:
    simulate()
    z += 1

print(time() - runtime)
print(z / (time() - runtime), "hands per second")

print(100 * (results.count(1) + (results.count(0) / 2)) / len(results), "%")
print(100 * (results.count(2) + (results.count(0) / 2)) / len(results), "%")
