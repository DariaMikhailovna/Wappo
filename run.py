import game


str_to_dir = {
    'U': game.Dir.UP,
    'D': game.Dir.DOWN,
    'L': game.Dir.LEFT,
    'R': game.Dir.RIGHT,
}


def main():
    map_ = game.Map()
    state = map_.read('input.txt')
    while True:
        state.print()
        if state.win_state == game.WinState.WIN:
            print('YOU WIN')
            break
        if state.win_state == game.WinState.LOSE:
            print('GAME OVER')
            break
        s = input()
        if s not in str_to_dir:
            continue
        state.move(str_to_dir[s])


if __name__ == '__main__':
    main()
