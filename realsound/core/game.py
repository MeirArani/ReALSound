from realsound.core import FSM, State
import enum


class GameStates(enum.IntEnum):
    Attract = 1
    Break = 2
    Match = 3
    Goal = 4
    Win = 5


class Game(FSM):
    def __init__(self):
        super().__init__(self)


def attract(data):
    yield data


def intermission(data):  # Curse you break statement
    yield data


def match(data):
    yield data


def goal(data):
    yield data


def win(data):
    yield data
