from math import ceil
import asyncio
import curses
import random
import time


TIC_TIMEOUT = 0.1
STARS_COUNT = 200

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258


def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -2

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 2

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 2

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -2

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


def draw_frame(canvas, start_row, start_column, text, negative=False):
    """Draw multiline text fragment on canvas. Erase text instead of drawing if negative=True is specified."""

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            # Check that current position it is not in a lower right corner of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def get_frame_size(text):
    """Calculate size of multiline text fragment. Returns pair (rows number, colums number)"""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


async def blink(canvas, row, column, symbol='*'):
    for _ in range(random.randint(1, STARS_COUNT)):
        await asyncio.sleep(0)

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas, start_row, start_column, frames_and_sizes):
    row = start_row
    column = start_column

    rows_max, columns_max = canvas.getmaxyx()

    while True:

        for frame, frame_rows, frame_columns in frames_and_sizes:
            rows_direction, columns_direction, space_pressed = read_controls(canvas)

            row += rows_direction
            row = max((row, 1))
            row = min((row, rows_max - frame_rows - 1))

            column += columns_direction
            column = max((column, 1))
            column = min((column, columns_max - frame_columns - 1))

            draw_frame(canvas, row, column, frame)
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, frame, negative=True)


def draw(canvas):
    canvas.nodelay(True)

    rocket_frames = read_frames()

    y, x = canvas.getmaxyx()

    canvas.border()
    curses.curs_set(False)
    canvas.refresh()

    coroutines = []
    for i in range(STARS_COUNT):
        coroutine = blink(
            canvas=canvas, row=random.randint(1, y - 2), column=random.randint(1, x - 2), symbol=random.choice('+*.:')
        )
        coroutines.append(coroutine)

    # coroutines.append(
    #     fire(
    #         canvas=canvas, start_row=y-2, start_column=round(x / 2)
    #     )
    # )

    rocker_rows, _ = get_frame_size(rocket_frames[0])
    frames_and_sizes = [(frame, *get_frame_size(frame)) for frame in rocket_frames]

    coroutines.append(
        animate_spaceship(
            canvas=canvas,
            start_row=round(y / 2 - ceil(rocker_rows / 2)),
            start_column=round(x / 2),
            frames_and_sizes=frames_and_sizes,
        )
    )

    while True:

        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
                break

        canvas.refresh()
        time.sleep(TIC_TIMEOUT)

        if len(coroutines) == 0:
            break


def read_frames():
    frames = []
    frame_files = [
        'frames/rocket_frame_1.txt',
        'frames/rocket_frame_2.txt',
    ]
    for frame_file in frame_files:
        with open(frame_file, 'r') as f:
            frames.append(f.read())

    return frames


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
