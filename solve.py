import game


dir_to_str = {
    game.Dir.UP: 'U',
    game.Dir.DOWN: 'D',
    game.Dir.LEFT: 'L',
    game.Dir.RIGHT: 'R',
}


def main():
    map_ = game.Map()
    start = map_.read('input.txt')
    l = [start]
    d = {start.key(): None}
    i = 0
    finish = None
    while i < len(l) and finish is None:
        state = l[i]
        for dir_ in game.Dir:
            new_state = state.copy()
            new_state.move(dir_)
            key = new_state.key()
            if key not in d:
                d[key] = (state, dir_)
                l.append(new_state)
            if new_state.win_state == game.WinState.WIN:
                finish = new_state
                break
        i += 1
    res = []
    while True:
        data = d[finish.key()]
        if data is None:
            break
        res.append(data[1])
        finish = data[0]
    res = ''.join(dir_to_str[dir_] for dir_ in reversed(res))
    print(res)


if __name__ == '__main__':
    main()
