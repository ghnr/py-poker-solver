import random
import array
from time import time, sleep
import struct
import numpy as np

# 125,000 H/s
# Test hand evaluation per second of 2p2 lookup table

handsDB = open('HandRanks.dat', 'rb')
ranks = array.array('i')
ranks.fromfile(handsDB, 32487834)
handsDB.close()

handTest = {}
results = []
wins = 0
losses = 0
ties = 0

cards = {'Ts': 35, '3h': 6, 'Qh': 42, 'Ks': 47, 'Td': 33, '2h': 2, 'As': 51, 'Kc': 48, '4s': 11, 'Js': 39, '4h': 10,
         'Ac': 52, '8c': 28, '6c': 20, '8s': 27, 'Qs': 43, 'Ah': 50, '7c': 24, '8h': 26, 'Qc': 44, '5s': 15, '8d': 25,
         '5d': 13, 'Qd': 41, '4d': 9, 'Kd': 45, '7h': 22, '9d': 29, '9c': 32, '2c': 4, 'Th': 34, '5h': 14, '3d': 5,
         '6h': 18, '9s': 31, '2s': 3, '6s': 19, '7s': 23, 'Jd': 37, '6d': 17, '3c': 8, '9h': 30, '3s': 7, '4c': 12,
         'Jh': 38, 'Tc': 36, '5c': 16, '7d': 21, '2d': 1, 'Ad': 49, 'Kh': 46, 'Jc': 40}
cards_reverse = {0: '2d', 1: '2h', 2: '2s', 3: '2c', 4: '3d', 5: '3h', 6: '3s', 7: '3c', 8: '4d', 9: '4h', 10: '4s',
                 11: '4c', 12: '5d', 13: '5h', 14: '5s', 15: '5c', 16: '6d', 17: '6h', 18: '6s', 19: '6c', 20: '7d',
                 21: '7h', 22: '7s', 23: '7c', 24: '8d', 25: '8h', 26: '8s', 27: '8c', 28: '9d', 29: '9h', 30: '9s',
                 31: '9c', 32: 'Td', 33: 'Th', 34: 'Ts', 35: 'Tc', 36: 'Jd', 37: 'Jh', 38: 'Js', 39: 'Jc', 40: 'Qd',
                 41: 'Qh', 42: 'Qs', 43: 'Qc', 44: 'Kd', 45: 'Kh', 46: 'Ks', 47: 'Kc', 48: 'Ad', 49: 'Ah', 50: 'As',
                 51: 'Ac'}
r = ['', '', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
s = ['c', 'd', 'h', 's']


def profile(func):
    return func


@profile
def lookup_hand(h, p=53):
    for card in h:
        p = ranks[p + card]
    return p


@profile
def readable(x):
    # disgusting, fix
    return " ".join([r[(x[y] + 7) // 4] + s[x[y] % 4] for y in range(0, len(x))])


@profile
def deal(dead_cards, num_cards=5):
    # changed from 52 0 -1
    deck = list(range(52, 0, -1))
    np.random.shuffle(deck)
    board = []
    for j in range(num_cards):
        card = deck[j]
        x = j + num_cards
        while card in dead_cards:
            card = deck[x]
            x += num_cards
        board.append(card)
    return board


@profile
def simulate(hand_h, hand_v, board=None, N=100000):
    for x in range(N):
        if not board:
            board = deal(hand_h + hand_v)
        
        # need to modify input based on game round
        if len(board) == 3:
            hero_score = lookup_hand([lookup_hand(hand_h + board)], p=0)
            villain_score = lookup_hand([lookup_hand(hand_v + board)], p=0)
        elif len(board) == 4:
            hero_score = lookup_hand([lookup_hand(hand_h + board)], p=0)
            villain_score = lookup_hand([lookup_hand(hand_v + board)], p=0)
        else:
            board_p = lookup_hand(board)
            hero_score = lookup_hand(hand_h, p=board_p)
            villain_score = lookup_hand(hand_v, p=board_p)
        
        if hero_score > villain_score:
            results.append(1)
        elif hero_score < villain_score:
            results.append(2)
        else:
            results.append(0)
        
        board = []


if __name__ == "__main__":
    runtime = time()
    N = 100000
    hand_1 = [cards['As'], cards['Ts']]
    hand_2 = [cards['3s'], cards['3c']]
    simulate(hand_1, hand_2, N=N)
    
    print(time() - runtime)
    print(N / (time() - runtime), "hands per second")
    print(100 * (results.count(1) + (results.count(0) / 2)) / len(results), "%")
    print(100 * (results.count(2) + (results.count(0) / 2)) / len(results), "%")
