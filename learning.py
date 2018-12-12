import time
import random
import copy
import numpy as np
import pandas as pd
from anytree import Node, RenderTree
from anytree.dotexport import RenderTreeGraph
from test2p2 import deal, lookup_hand
from constants import FLOP, TURN, RIVER, BET_33, BET_66, BET_50, BET_100, FOLD, RAISE, CALL, CHECK, CARDS, CARDS_REVERSE

# Ranges or let it work out what to open on its own?}: not feasible
# Post-flop
# Calculate equity of hand and range. Ordered list of all equities, bet 1-a% or let it work it out?}obv let it work

# We're at some flop A92ss 7 turn 2sss river
# OOP, we take action randomly, villain also randomly for 1000 times
# Then we start learning for 10,000 saving each time <-- print every 100
# Bet sizes 1/3 1/2 2/3, 100bb
# Villain action?

# Villain 3b call range BTNvsBB: QQ-22, A2s+, K9s+, Q9s+, J9s+, T8s+, 97s+, 86s+, 75s+, 65s, 54s, ATo+, KTo+, QTo+, JTo

# TODO: For testing regrets, have opponent strategy = always call, % probability of call increasing with lower bet size to see if finds optimal

actions_to_read = {3: 'BET_33', 5: 'BET_50', 7: 'BET_66', 11: 'BET_100', 13: 'FOLD', 17: 'RAISE', 19: 'CALL',
                   23: 'CHECK'}


def profile(func):
    # rkern/line_profiler
    return func


class PokerGame:
    def __init__(self, AI_obj, hero_hand, villain_hand, villain_range, board=None, betting_lead=False, initial_pot=20,
                 hero_stack=100 - 10):
        # self.AI = AI_obj
        self.hand_h = hero_hand
        self.hand_v = villain_hand
        # self.range = villain_range
        self.game_state = None
        self.board = board
        self.villain_stack = hero_stack
        self.actions_taken = []
        self.strategy = ""
        self.tree = Node('Root')
    
    @profile
    def set_board(self, current_board):
        if not current_board:
            self.board = deal(self.hand_h + self.hand_v)
        else:
            num_cards = len(current_board)
            if num_cards < 5:
                self.board = current_board + deal(self.hand_h + self.hand_v + self.board, 5 - num_cards)
    
    def get_opponent_response(self, game_state):
        rng = random.random()
        if game_state['last_bet'] == 0:
            if rng > 99999:
                # force opponent to check
                pass
            else:
                bet_amount = BET_33 * self.game_state['pot_size']
                if bet_amount >= self.game_state['hero_stack']:
                    # all in  >= needed?
                    bet_amount = self.game_state['hero_stack']
                    # TODO: Go to showdown directly
                self.game_state['betting_lead'] = False
                self.game_state['pot_size'] += bet_amount
                self.game_state['last_bet'] = bet_amount
                # opponent checks
        
        else:
            # opponent calls or folds
            if rng > 0.25:
                # villain calls
                game_state['pot_size'] += game_state['last_bet']
            else:
                if game_state['reraised']:
                    # villain calls raise
                    game_state['pot_size'] += game_state['last_bet']
                else:
                    # villain raises
                    game_state['raised'] = True
                    game_state['pot_size'] += 3 * game_state['last_bet']
    
    def get_actions(self):
        if not self.game_state['betting_lead']:
            actions = [CHECK]
        elif self.game_state['last_bet'] == 0:
            actions = [BET_33, BET_50, BET_66, BET_100, CHECK]
        elif not self.game_state['reraised']:
            actions = [FOLD, RAISE, CALL]
        else:
            actions = [FOLD, CALL]
        return actions
    
    def set_node(self, game_round, action, parent_node, extend=False):
        if game_round == FLOP and not extend:
            node_ID = actions_to_read[action]
        else:
            node_ID = str(parent_node.name) + ":" + actions_to_read[action]
        
        for existing_node in parent_node.children:
            if existing_node.name == node_ID:
                action_node = existing_node
                break
        else:
            action_node = Node(node_ID, parent=parent_node)
        return action_node
    
    def action_node(self, game_round, initial_state, action, parent_node):
        self.game_state = initial_state.copy()
        
        action_node = self.set_node(game_round, action, parent_node)
        self.take_action(action)
        self.get_opponent_response(self.game_state)
        
        # Needs changing:
        if self.game_state['raised']:
            self.take_action(CALL)
            action_node = self.set_node(game_round, CALL, action_node, extend=True)
        elif self.game_state['last_bet'] != 0 and not self.game_state['betting_lead']:
            self.take_action(CALL)
            action_node = self.set_node(game_round, CALL, action_node, extend=True)
        
        if self.game_state['hero_stack'] == 0 or game_round == RIVER:
            utility = self.showdown(game_round)
        elif self.game_state['villain_folded']:
            utility = self.game_state['pot_size'] - (100 - self.game_state['hero_stack'])
        elif self.game_state['folded']:
            utility = self.game_state['hero_stack'] - 100
        else:
            utility = self.simulate_round(game_round + 1, self.game_state, action_node)
        
        # if not action_node.is_leaf:
        #     # TODO: sum product with % opp strategy
        #     sum_utilities = 0
        #     for node in action_node.children:
        #         node_utility = node.get_value()
        #         sum_utilities += node_utility
        #
        #     average_utility = sum_utilities/len(action_node.children)
        #     action_node.set_value("utility", round(average_utility, 3))
        #     # self.compute_regret(action_node, max_utility)
        # else:
        #     action_node.set_value("utility", round(utility, 3))
        # if action_node.siblings:
        #     # TODO: move this to end of iteration
        #     self.compute_regret(action_node)
        #     self.update_strategy(action_node.parent)
        return utility
    
    def compute_regret(self, action_node):
        max_utility = 0
        for node in action_node.parent.children:
            utility = node.get_value()
            max_utility = utility if utility > max_utility else max_utility
        for node in action_node.parent.children:
            regret = node.get_value() - max_utility
            # print(regret)
            node.set_value("regret", regret)
            regretSum = node.get_value("regretSum")
            if regretSum:
                node.set_value("regretSum", regretSum + regret)
            else:
                node.set_value("regretSum", regret)
    
    def compute_all_regret(self):
        """Build key-value structure for every possible line and its utility (pair: depends on won or lost, maybe not
         needed if just using the size of the pot and work out net later)
        Won or lost calculated once using current board if on the river else using % equity
        Iterate through every (other) possible action and update node regret value based on chosen action's utility"""
        pass
    
    def update_strategy(self, parent_node):
        normalizingSum = 0
        strategies = []
        for child in parent_node.children:
            regretSum = child.get_value("regretSum")
            strategy = 0
            if regretSum > 0:
                strategy = regretSum
            strategies.append(strategy)
            normalizingSum += strategy
        if normalizingSum > 0:
            strategies = [strategy / float(normalizingSum) for strategy in strategies]
        else:
            # equal strategies
            strategies = [1 / len(strategies)] * len(strategies)
        strategy_values = parent_node.get_value("strategy")
        for x, child in enumerate(parent_node.children):
            if strategy_values:
                strategy_values.update({child.name: strategies[x]})
                parent_node.set_value("strategy", strategy_values)
            else:
                parent_node.set_value("strategy", {child.name: strategies[x]})
    
    def next_round(self):
        self.game_state['last_bet'] = 0
        self.game_state['raised'] = False
        self.game_state['reraised'] = False
    
    def simulate_round(self, game_round, game_state, parent_node, initial=False):
        if not parent_node:
            parent_node = self.tree
        if initial or not self.game_state:
            self.game_state = game_state.copy()
        
        self.next_round()
        legal_actions = self.get_actions()
        if game_round == FLOP:
            action = random.choice(legal_actions)
            utility = self.action_node(game_round, game_state, action, parent_node)
        elif game_round == TURN:
            # for action in legal_actions:
            # print(game_round)
            action = random.choice(legal_actions)
            utility = self.action_node(game_round, game_state, action, parent_node)
        else:
            # for action in legal_actions:
            # print(game_round)
            action = random.choice(legal_actions)
            utility = self.action_node(game_round, game_state, action, parent_node)
            print([actions_to_read[x] for x in self.game_state['line']])
        return utility
    
    # @profile
    # def flop(self):
    #     self.set_board()
    #     if not self.betting_lead:
    #         self.action_check()
    #     else:
    #         legal_actions = self.get_actions()
    #         state = self.hand_h + self.board[:3] + self.actions_taken
    #         action = self.AI.choose_action(state, legal_actions)
    #         self.take_action(action)
    #     if self.hero_stack == 0:
    #         return self.showdown(2) # assuming eff stacks equal
    #
    # @profile
    # def turn(self):
    #     self.reraised = False
    #     self.last_bet = 0
    #     if not self.betting_lead:
    #         self.action_check()
    #     else:
    #         legal_actions = self.get_actions()
    #         state = self.hand_h + self.board[:4] + self.actions_taken
    #         action = self.AI.choose_action(state, legal_actions)
    #         self.take_action(action)
    #     if self.hero_stack == 0:
    #         return self.showdown(1) # assuming eff stacks equal
    #
    # @profile
    # def river(self):
    #     self.reraised = False
    #     self.last_bet = 0
    #     if not self.betting_lead:
    #         self.action_check()
    #     else:
    #         legal_actions = self.get_actions()
    #         state = self.hand_h + self.board + self.actions_taken
    #         action = self.AI.choose_action(state, legal_actions)
    #         self.take_action(action)
    #     return self.showdown(0)
    
    @profile
    def take_action(self, action):
        actions = {BET_33: lambda: self.action_bet(0.3333),
                   BET_50: lambda: self.action_bet(0.50),
                   BET_66: lambda: self.action_bet(0.6666),
                   BET_100: lambda: self.action_bet(1.00),
                   FOLD: lambda: self.action_fold(),
                   RAISE: lambda: self.action_raise(),
                   CALL: lambda: self.action_call(),
                   CHECK: lambda: self.action_check()}
        actions[action]()
        self.game_state['line'].append(action)
        # self.actions_taken.append(action)
        # print(actions_to_read[action], game_state)
    
    def action_fold(self):
        self.game_state['folded'] = True
        self.actions_taken.append("fold")
    
    def action_check(self):
        # TODO: separate object for villain
        # TODO: Set betting lead
        self.actions_taken.append("check")
        self.game_state['last_bet'] = 0
        # game_state['betting_lead'] = False
        pass
    
    def action_call(self):
        self.update_chips(self.game_state['last_bet'])
        self.actions_taken.append("call")
        self.game_state['betting_lead'] = False
    
    def action_bet(self, size):
        bet_amount = size * self.game_state['pot_size']
        self.update_chips(bet_amount)
        self.actions_taken.append("bet " + str(size))
        self.game_state['betting_lead'] = True
    
    def action_raise(self):
        bet_amount = 3 * self.game_state['last_bet']
        self.update_chips(bet_amount)
        if self.game_state['raised']:
            self.game_state['reraised'] = True
        else:
            self.game_state['raised'] = True
        self.game_state['betting_lead'] = True
    
    @profile
    def update_chips(self, bet_amount):
        if bet_amount >= self.game_state['hero_stack']:
            # all in  >= needed?
            bet_amount = self.game_state['hero_stack']
            # TODO: Go to showdown directly
        self.game_state['hero_stack'] -= bet_amount
        self.game_state['pot_size'] += bet_amount
        self.game_state['last_bet'] = bet_amount
    
    @profile
    def showdown(self, game_round):
        cards_to_be_dealt = 3 - game_round  # 3 on the flop already
        if self.game_state['folded'] or cards_to_be_dealt == -1:
            reward = self.game_state['hero_stack'] - 100
        else:
            if cards_to_be_dealt > 0:
                # TODO: Enumerate all
                reward = self.game_state['pot_size'] - (100 - self.game_state['hero_stack'])
                # TODO: Change above
                pass
            else:
                board_p = lookup_hand(self.board)
                hero_score = lookup_hand(self.hand_h, p=board_p)
                villain_score = lookup_hand(self.hand_v, p=board_p)
                if hero_score > villain_score or self.game_state['villain_folded']:
                    reward = self.game_state['pot_size'] - (100 - self.game_state['hero_stack'])
                elif hero_score < villain_score:
                    reward = self.game_state['hero_stack'] - 100
                else:
                    reward = 0
        return reward


def readable(hand):
    return [CARDS_REVERSE[x] for x in hand]


def iterate_children(node):
    if not node.is_leaf:
        indent = node.depth * "    "
        optimal_node = None
        for child in node.children:
            if not optimal_node:
                optimal_node = child
            elif child.value > optimal_node.value:
                optimal_node = child
            print(indent, child.name.split(":")[-1], child.value)
            iterate_children(child)
        print("Optimal node", optimal_node.name)


def optimal_action(node):
    optimal_node = None
    if not node.is_leaf:
        for child in node.children:
            if not optimal_node:
                optimal_node = child
            elif child.value > optimal_node.value:
                # if bet sizes are ordered min to max then this has the side effect
                # of picking the smallest size that gives the same reward
                optimal_node = child
        print(optimal_node.name.split(":")[-1], optimal_node.value)
        optimal_action(optimal_node)


N = 10000


@profile
def run():
    hero = [CARDS['Ah'], CARDS['Qd']]
    villain = [CARDS['2s'], CARDS['2d']]
    board_test = [CARDS['Ad'], CARDS['Ac'], CARDS['As']]
    root = Node('Root')
    initial_game_state = {'pot_size': 2, 'betting_lead': True, 'hero_stack': 97, 'last_bet': 0, 'raised': False,
                          'reraised': False, 'folded': False, 'villain_folded': False, 'line': []}
    game = PokerGame(None, hero, villain, None, board=board_test)
    for i in range(N):
        game.set_board(board_test)
        game_state = copy.deepcopy(initial_game_state)
        game.simulate_round(FLOP, game_state, root, initial=True)
    
    RenderTreeGraph(root).to_picture("tree.png")
    for pre, fill, node in RenderTree(root):
        print("%s%s (%s) (%s) (%s) (%s)" % (
            pre, str(node.name).split(":")[-1], node.get_value(), node.get_value("regret"), node.get_value("regretSum"),
            node.get_value("strategyNOT")))


t0 = time.time()
run()
t = time.time() - t0
print(N / t, "cycles per second")
print(t, "seconds total")
