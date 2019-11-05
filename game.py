import pickle
from collections import defaultdict
from copy import deepcopy
from enum import Enum
from typing import Optional, List, Dict, Any


class Dir(Enum):
    LEFT = 0
    RIGHT = 1
    UP = 2
    DOWN = 3


class Map:
    DR = {Dir.LEFT: 0, Dir.RIGHT: 0, Dir.UP: -1, Dir.DOWN: 1}
    DC = {Dir.LEFT: -1, Dir.RIGHT: 1, Dir.UP: 0, Dir.DOWN: 0}

    def __init__(self):
        self.H = 0
        self.W = 0
        self.grid = []  # сетка

    def read(self, filename):
        with open(filename) as file:
            self.H, self.W = map(int, file.readline().strip().split())
            self.grid = [x[:2 * self.W + 1] for x in file][:2 * self.H + 1]
        state = State(self)
        for r in range(2 * self.H + 1):
            for c in range(2 * self.W + 1):
                if self.grid[r][c] == 'P':
                    assert state.player is None
                    state.player = Position(r, c)
                    self.grid[r] = self.grid[r][:c] + ' ' + self.grid[r][c + 1:]
                if self.grid[r][c] == 'E':
                    state.enemies.append(Enemy(r, c))
                    self.grid[r] = self.grid[r][:c] + ' ' + self.grid[r][c + 1:]
        self.validate()
        state.validate()
        return state

    def validate(self):
        assert len(self.grid) == 2 * self.H + 1
        for row in self.grid:
            assert len(row) == 2 * self.W + 1
        for r in range(2 * self.H + 1):
            for c in range(2 * self.W + 1):
                if r % 2 == 0 and c % 2 == 0:
                    assert self.grid[r][c] == '+'
                if r % 2 == 0 and c % 2 != 0:
                    if r == 0 or r == 2 * self.H:
                        assert self.grid[r][c] in ['-', 'H']
                    else:
                        assert self.grid[r][c] in ['-', ' ']
                if r % 2 != 0 and c % 2 == 0:
                    if c == 0 or c == 2 * self.W:
                        assert self.grid[r][c] in ['|', 'H']
                    else:
                        assert self.grid[r][c] in ['|', ' ']
                if r % 2 != 0 and c % 2 != 0:
                    assert self.grid[r][c] in [' ', 'X', 'H']
        assert sum(sum(c == 'H' for c in row) for row in self.grid) == 1


class Position:
    def __init__(self, r, c):
        self.r = r
        self.c = c

    def coincide(self, pos):
        return self.r == pos.r and self.c == pos.c


class Enemy(Position):
    def __init__(self, r, c):
        super().__init__(r, c)
        self.is_big = False
        self.cooldown = 0


class WinState(Enum):
    NA = 0
    WIN = 1
    LOSE = 2


class State:  # текущее состояние игры
    def __init__(self, map_):
        self.player: Optional[Position] = None
        self.enemies: List[Enemy] = []
        self.map = map_
        self.win_state = WinState.NA

    def key(self):
        if self.win_state != WinState.NA:
            return self.win_state
        return pickle.dumps((self.player, self.enemies))

    def print(self):
        grid = deepcopy(self.map.grid)

        def change_symbol(r, c, ch):
            grid[r] = grid[r][:c] + ch + grid[r][c + 1:]

        change_symbol(self.player.r, self.player.c, 'P')
        for enemy in self.enemies:
            change_symbol(enemy.r, enemy.c, 'E')
        for s in grid:
            print(s)

    def copy(self):
        state_copy = State(self.map)
        state_copy.player = deepcopy(self.player)
        state_copy.enemies = deepcopy(self.enemies)
        state_copy.win_state = deepcopy(self.win_state)
        return state_copy

    def validate_pos(self, pos):
        assert 0 <= pos.r < 2 * self.map.H + 1
        assert pos.r % 2 != 0
        assert 0 <= pos.c < 2 * self.map.W + 1
        assert pos.c % 2 != 0

    def validate(self):
        if self.win_state != WinState.NA:
            return
        assert self.player is not None
        assert 1 <= len(self.enemies) <= 2
        self.validate_pos(self.player)
        for enemy in self.enemies:
            self.validate_pos(enemy)

    def _is_killed_by_enemy(self):
        for enemy in self.enemies:
            if enemy.coincide(self.player):
                return True
        return False

    def _move_player(self, d):
        dr = self.map.DR[d]
        dc = self.map.DC[d]
        outline = self.map.grid[self.player.r + dr][self.player.c + dc]
        if outline in ['-', '|']:
            return False
        if outline == 'H':
            self.win_state = WinState.WIN
            return True
        self.player.r += dr * 2
        self.player.c += dc * 2
        new_cell = self.map.grid[self.player.r][self.player.c]
        if new_cell == 'H':
            self.win_state = WinState.WIN
            return True
        if new_cell == 'X':
            self.win_state = WinState.LOSE
            return True
        if self._is_killed_by_enemy():
            self.win_state = WinState.LOSE
            return True
        return True

    def _move_enemy_one_step(self, enemy):
        pr = self.player.r
        pc = self.player.c
        er = enemy.r
        ec = enemy.c
        for d in Dir:
            dr = self.map.DR[d]
            dc = self.map.DC[d]
            if (pr - er) * dr + (pc - ec) * dc <= 0:
                continue
            outline = self.map.grid[er + dr][ec + dc]
            if outline in ['-', '|']:
                continue
            enemy.r += dr * 2
            enemy.c += dc * 2
            if not enemy.is_big and self.map.grid[enemy.r][enemy.c] == 'X':
                enemy.cooldown = 4
            break

    def _merge_enemies(self):
        by_cell: Dict[Any, List[Enemy]] = defaultdict(list)
        for enemy in self.enemies:
            by_cell[(enemy.r, enemy.c)].append(enemy)
        self.enemies = []
        for l in by_cell.values():
            if len(l) > 1:
                l[0].is_big = True
                l[0].cooldown = 1
            self.enemies.append(l[0])

    def _move_enemies(self):
        for step in range(3):
            for enemy in self.enemies:
                if enemy.cooldown > 0:
                    continue
                if step == 2 and not enemy.is_big:
                    continue
                self._move_enemy_one_step(enemy)
                if self.win_state != WinState.NA:
                    return
            if self._is_killed_by_enemy():
                self.win_state = WinState.LOSE
                return
            self._merge_enemies()
        for enemy in self.enemies:
            if enemy.cooldown > 0:
                enemy.cooldown -= 1

    def move(self, d):
        if self.win_state != WinState.NA:
            return
        if not self._move_player(d):
            return
        if self.win_state != WinState.NA:
            return
        self._move_enemies()


def main():
    map_ = Map()
    state = map_.read('input.txt')


if __name__ == '__main__':
    main()

