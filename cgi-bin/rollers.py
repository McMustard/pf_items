#!/usr/bin/env python3
# vim: set fileencoding=utf-8

# Pathfinder Item Generator
#
# Copyright 2012-2013, Steven Clark.
#
# This program is free software, and is provided "as is", without warranty of
# any kind, express or implied, to the extent permitted by applicable law.
# See the full license in the file 'LICENSE'.
#
# This software includes Open Game Content.  See the file 'OGL' for more
# information.
#
'''
This module implements manual and random rollers, that use simple 'd' dice
expressions for generating random rolls for the Pathfinder Item Generator.
'''

#
# Standard Imports

from __future__ import print_function

import random
from sys import stdin, stdout

#
# Utility Functions

# Dice Expression Parser
# Returns (number_of_dice, die_sides)
def parseDiceExpression(dice_expression):
    (number_str, sides_str) = dice_expression.split('d')
    return (int(number_str), int(sides_str))

# Roll virtual dice
def rollDice(dice_expression):
    (number, sides) = parseDiceExpression(dice_expression)
    #print('Rolling ' + str(number) + ' ' + str(sides) + '-sided dice.')
    rolls = [random.randrange(1, sides + 1) for x in range(number)]
    #print('Rolls:', rolls)
    return sum(rolls)

#
# Dice Rollers

# Base class for dice rollers
class Roller(object):
    # Roll a random number according to the specified dice expression.
    # Return integers only.
    def roll(self, dice_expression, purpose):
        # 0 is an invalid value.
        return 0

class PseudorandomRoller(Roller):
    # Roll a random number using the handy-dandy function we have here.
    def roll(self, dice_expression, purpose):
        # Simply return flat numbers.
        try:
            return int(dice_expression)
        except:
            pass
        # Generate a pseudomrandom number.
        return rollDice(dice_expression)

# Instructs the user via the command line to roll dice and input the results
# to return.
class ManualDiceRoller(Roller):
    def roll(self, dice_expression, purpose):
        # Simply return flat numbers.
        try:
            return int(dice_expression)
        except:
            pass
        # Print instructions for the user.
        print('Roll ' + dice_expression + ' for ' + purpose + \
                ' (enter 0 to roll via software):',
                end='')
        # Set up values in preparation for an indefinite loop.
        result = None
        value = 0
        while result == None:
            # Get user input.
            result = stdin.readline()
            if result == '\n':
                value = 0
                break
            try:
                # See if it's valid and convert to int.
                value = int(result)
            except ValueError:
                # Reset string to empty so the loop reiterates.
                result = None
        # If the user decided manual rolling was a bad idea, pick it
        # ourselves.
        if value == 0:
            roll = rollDice(dice_expression)
            print('    rolled: ', roll)
            return roll
        # Done.
        return value

#
# Tester

if __name__ == '__main__':
    pass
