from random import randint
from time import sleep


# Исключения
class BoardException(Exception):
    pass


class BoardOutException(BoardException):  # выход за пределы доски
    def __init__(self, text):
        self.txt = text


class BoardUsedException(BoardException):  # точка занята
    def __init__(self, text):
        self.txt = text


class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return (self.x == other.x) and (self.y == other.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def __str__(self):
        return f'({self.x},{self.y})'


class Ship:
    def __init__(self, d, ln, d_):
        self.dot = d  # стартовая точка корабля
        self.length = ln  # длина коробля
        self.direction = d_  # 0 - горизонтальное положение, 1 - вертикальное
        self.life = ln  # количество жизней равно длине корабля

    def dots(self):
        if self.direction:
            return [Dot(x, self.dot.y) for x in range(self.dot.x, self.dot.x + self.length)]
        else:
            return [Dot(self.dot.x, y) for y in range(self.dot.y, self.dot.y + self.length)]


class Board:
    def __init__(self, h):
        self.ships = []
        self.x_ships = 0
        self.hide = h  # True - скрывать корабли компа  (h)
        self.field = [[0] * 6 for _ in range(0, 6)]

    @staticmethod
    def contour(c_ship):  # возвращает контур коробля
        set_ = set()

        def add_dot(x1, y1):
            try:
                set_.add(Dot(x1, y1))
            except IndexError:
                pass

        for d in c_ship.dots():
            add_dot(d.x + 1, d.y)
            add_dot(d.x + 1, d.y + 1)
            add_dot(d.x, d.y + 1)
            add_dot(d.x - 1, d.y + 1)
            add_dot(d.x - 1, d.y)
            add_dot(d.x - 1, d.y - 1)
            add_dot(d.x, d.y - 1)
            add_dot(d.x + 1, d.y - 1)
        return set_.difference(c_ship.dots())

    @staticmethod
    def out(d):  # проверка на выход за границы доски
        return (d.x < 0) or (d.x >= 6) or (d.y < 0) or (d.y >= 6)

    def add_ship(self, add_s):  # метод добавления корабля на игровое поле
        try:
            for d in add_s.dots():
                if self.out(d):
                    raise BoardOutException('')
                if self.field[d.x][d.y] != 0:
                    raise BoardUsedException('')
                for i in self.ships:
                    if d in self.contour(i):
                        raise BoardUsedException('')
        except (BoardOutException, BoardUsedException):
            return False
        else:
            for d in add_s.dots():
                self.field[d.x][d.y] = 1
            self.ships.append(add_s)
            self.x_ships += 1
            return True

    def shot(self, d):  # выстрел в точку
        if self.out(d):
            raise BoardOutException(f'{d.x + 1} {d.y + 1} - {Game.yc}Вы стреляете мимо доски...{Game.dc}')
        if self.field[d.x][d.y] >= 10:
            raise BoardUsedException(f'{d.x + 1} {d.y + 1} - {Game.yc}В эту точку уже стреляли{Game.dc}')

        self.field[d.x][d.y] += 10
        if self.field[d.x][d.y] == 11:  # попадание в корабль
            for s in self.ships:
                if d in s.dots():  # корабль, в который попали
                    s.life -= 1  # отнимаем одну жизнь
                    if not s.life:  # если жизней не осталось
                        for d_ in s.dots():
                            self.field[d_.x][d_.y] += 10  # помечаем убитый корабль
                        for d_ in self.contour(s):  # контур убитого корабля
                            if not self.out(d_):  # может быть выход за границы поля
                                if self.field[d_.x][d_.y] < 10:
                                    self.field[d_.x][d_.y] += 10
                        self.x_ships -= 1
        return self.field[d.x][d.y]  # возвращаем значение выстрела

    def random_board(self):
        size_b = 6
        count = 0  # счетчик попыток расставить корабли
        for q in [3, 2, 2, 1, 1, 1, 1]:
            while True:
                x = randint(0, size_b - 1)
                y = randint(0, size_b - 1)
                d = randint(0, 1)
                if self.add_ship(Ship(Dot(x, y), q, d)):
                    break
                else:
                    count += 1
                if count > 2000:  # ограничение попыток
                    return False
        return True


class Player:
    def __init__(self, b_):
        self.board = b_
        self.last_shot_dot = []  # координаты последних попаданий в очереди
        self.last_shot_value = 0  # результат попаданий

    def ask(self):  # будет переопределяться в потомках и возвращать Dot
        x, y = 0, 0
        return Dot(x, y)

    def move(self, other):  # ход юзера
        try:
            Game.check = 0
            d_ = self.ask()
            shot_value = other.board.shot(d_)
            if shot_value > 10:  # если было попадание, продолжаем стрелять
                self.last_shot_dot.append(d_)  # точка с последним попаданием
                self.last_shot_value = shot_value
                if shot_value > 20:
                    print(f'{d_.x + 1} {d_.y + 1} - {Game.yc}Убил!{Game.dc}')
                    self.last_shot_dot.clear()  # если убили корабль, очищаем очередь стрельбы
                    Game.check += 1
                else:
                    print(f'{d_.x + 1} {d_.y + 1} - {Game.yc}Ранил!{Game.dc}')
                    Game.check += 1
                if other.board.x_ships:  # если остались корабли, продолжаем
                    return True
                else:
                    self.board.hide = False
                    return False  # если это победный выстрел, завершаем ход
            else:
                print(f'{d_.x + 1} {d_.y + 1} - {Game.yc}Мимо!{Game.dc}')
                return False  # если мимо, завершаем ход
        except (BoardOutException, BoardUsedException) as e:
            if type(self) is User:  # только для ходов юзера
                print(e.txt)
            return True


class User(Player):
    def ask(self):
        while True:
            entered_list = input(f"\nХод ваш, введите координаты: {Game.rct}")
            quit() if entered_list in ['stop', 'ыещз'] else ''
            entered_list = entered_list.split()
            if len(entered_list) != 2:
                print(f"{Game.yc}Введите две координаты...{Game.dc}")
                continue
            x, y = entered_list
            if not (x.isdigit()) or not (y.isdigit()):
                print(f"{Game.yc}Введите числа...{Game.dc}")
                continue
            x = int(entered_list[0]) - 1  # сдвигаем координаты
            y = int(entered_list[1]) - 1
            return Dot(x, y)


class AI(Player):
    def ask(self):
        if self.last_shot_value == 11:  # если ранили корабль
            if len(self.last_shot_dot) == 1:  # если только одно попадание
                d_ = self.last_shot_dot[0]
                t = randint(1, 4)  # пробуем стрелять в соседние клетки
                if t == 1:
                    return Dot(d_.x, d_.y - 1)
                elif t == 2:
                    return Dot(d_.x + 1, d_.y)
                elif t == 3:
                    return Dot(d_.x, d_.y + 1)
                elif t == 4:
                    return Dot(d_.x - 1, d_.y)
            else:  # если имеем несколько попаданий (многопалубный корабль)
                # находим координату, которая будет изменяться
                t = randint(0, 1)
                if self.last_shot_dot[0].x == self.last_shot_dot[1].x:  # x - не меняется, y - меняется
                    miny = self.last_shot_dot[0].y
                    maxy = miny
                    for d_ in self.last_shot_dot:
                        if miny > d_.y:
                            miny = d_.y
                        if maxy < d_.y:
                            maxy = d_.y
                    if t:
                        return Dot(self.last_shot_dot[0].x, miny - 1)
                    else:
                        return Dot(self.last_shot_dot[0].x, maxy + 1)
                else:  # y - не меняется, x - меняется
                    minx = self.last_shot_dot[0].x
                    maxx = minx
                    for d_ in self.last_shot_dot:
                        if minx > d_.x:
                            minx = d_.x
                        if maxx < d_.x:
                            maxx = d_.x
                    if t:
                        return Dot(minx - 1, self.last_shot_dot[0].y)
                    else:
                        return Dot(maxx + 1, self.last_shot_dot[0].y)
        else:
            x = randint(0, 5)
            y = randint(0, 5)
            return Dot(x, y)


class Game:
    check = 0
    # Цвета
    bc = '\033[94m'  # синий
    sc = '\033[35m\033[1m'  # сиреневый
    gc = '\033[92m'  # зеленый
    yc = '\033[93m'  # желтый
    rc = '\033[91m'  # красный
    dc = '\033[0m'  # дефолтный
    yct = '\033[33m' + '▪ ' + '\033[0m'  # желтый круг
    rct = "\033[0m\033[31m" + "► " + "\033[0m"  # красный треугольник
    pin = {
        0: bc + '·' + dc,   # пустая клетка
        1: gc + '■' + dc,   # корабль
        2: bc + '·' + dc,   # клетка на поле противника, в которую не стреляли
        10: rc + '•' + dc,  # выстрел по пустой клетке
        11: yc + '■' + dc,  # раненый корабль
        21: rc + '■' + dc   # потопленный корабль
    }

    def __init__(self):
        b_us = Board(False)
        b_ai = Board(True)
        while not b_us.random_board():
            b_us = Board(False)
        while not b_ai.random_board():
            b_ai = Board(True)
        self.board_us = b_us
        self.board_ai = b_ai
        self.us = User(b_us)
        self.ai = AI(b_ai)

    def print_board(self):
        size = 6

        def get_row(b):    # вывод в зависимости от параметра hide
            if b.hide:     # если нужно скрывать
                return '   '.join(self.pin[b.field[i][j] if b.field[i][j] >= 10 else 2] for j in range(0, size))
            else:          # если нужно показывать
                return '   '.join(self.pin[b.field[i][j]] for j in range(0, size))

        print(f'\nВаше поле:{"":38}Поле компьютера:')
        print(f'{"_" * 29}{"":19}{"_" * 29}')
        coord_numbers = '│ '.join(f'{str(s + 1):2}' for s in range(0, size))
        print(f'│ {self.rc}∷{self.dc} │ {coord_numbers}│{"":19}│ {self.rc}∷{self.dc} │ {coord_numbers}│')
        print(f'│{"–––│" * 7}{"":19}│{"–––│" * 7}')
        for i in range(0, size):
            print(f'│ {str(i + 1):2}│ {get_row(self.board_us)} │{"":19}│ {str(i + 1):2}│ {get_row(self.board_ai)} │')
        print(f'|___|{"_" * 23}|{"":19}|___|{"_" * 23}|')
        # print(f'|{"___|" * 7}{"":19}|{"___|" * 7}')

    def loop(self, user_move):
        if user_move:  # True - ходит юзер, false - компьютер
            while True:
                self.print_board()
                if self.us.move(self.ai):
                    continue
                else:
                    self.print_board()
                    break
        else:
            print('\nХод компьютера: ')
            sleep(1)
            while True:
                if Game.check == 1:
                    self.print_board()
                    print('\nХод компьютера: ')
                    sleep(1)
                if self.ai.move(self.us):
                    continue
                else:
                    break

    def start(self):
        user_move = True
        print(f'{self.bc}{"-" * 77}{self.dc}')
        print('\n⚓ ', end='')
        otv = ''
        while True:
            game = input(f'{otv}Начать игру? (Y/N): {self.rct}').lower()
            quit() if game in ['stop', 'ыещз'] else ''
            if game in ['y', 'н']:
                print(f'{self.yc}Игра началась...{self.dc}')
                while True:
                    self.loop(user_move)
                    user_move = not user_move  # переход хода другому игроку  !!!
                    if not self.board_us.x_ships:  # если победил комп
                        self.print_board()
                        print(f'{self.sc}\n🚩 ПОБЕДИЛ КОМПЬЮТЕР!\n{self.dc}')
                        break
                    if not self.board_ai.x_ships:  # если победил юзер
                        self.print_board()
                        print(f'{self.sc}\n🚩 ВЫ ПОБЕДИЛИ!\n{self.dc}')
                        break
                return False
            elif game in ['n', 'т']:
                quit()
            else:
                print(f'{self.yc}Ответ не распознан... {self.dc}', end='')


class Greet:
    @staticmethod
    def greet():  # напутствие перед боем
        print(f'{Game.gc}')
        print(f'{" " * 38}Sea Battle  |  v 1.0  |  Sabirov Rafail{Game.bc}')
        print('▓▓▓▓▓▓  ▓▓▓▓▓▓   ▓▓▓▓▓      ▓▓▓▓▓       ▓▓▓▓▓  ▓▓▓▓▓▓  ▓▓▓▓▓▓  ▓▓      ▓▓▓▓▓▓')
        print('▓▓      ▓▓      ▓▓  ▓▓      ▓▓  ▓▓     ▓▓  ▓▓    ▓▓      ▓▓    ▓▓      ▓▓    ')
        print('▓▓▓▓▓▓  ▓▓▓▓    ▓▓▓▓▓▓      ▓▓ ▓▓▓▓    ▓▓▓▓▓▓    ▓▓      ▓▓    ▓▓      ▓▓▓▓  ')
        print('    ▓▓  ▓▓      ▓▓  ▓▓      ▓▓    ▓▓   ▓▓  ▓▓    ▓▓      ▓▓    ▓▓      ▓▓    ')
        print('▓▓▓▓▓▓  ▓▓▓▓▓▓  ▓▓  ▓▓      ▓▓▓▓▓▓▓    ▓▓  ▓▓    ▓▓      ▓▓    ▓▓▓▓▓▓  ▓▓▓▓▓▓')
        print(f'{" " * 25}{Game.rc}C   O   N   S   O   L   E')
        print(f'{Game.bc}{"-" * 77}\n')
        print(f'{Game.yc} НАПУТСТВИЕ ПЕРЕД БОЕМ: {Game.dc}')
        print(f' {Game.yct} играть придется с грозным соперником - компьютером')
        print(f' {Game.yct} корабли располагаются в случайном порядке')
        print(f' {Game.yct} право первого хода всегда остается за вами')
        print(f' {Game.yct} чтобы сделать ход, введите координаты (строка колонка), например: 1 1')
        print(f' {Game.yct} побеждает тот, кто не проиграл')
        print(f' {Game.yct} если станет страшно и захочется досрочно выйти из игры,')
        print(f'    просто наберите - {Game.rc}STOP')
        print(f'{Game.bc}{"-" * 77}{Game.dc}')

        print(f'{Game.yc}Запомните главное: {Game.sc}       ', end='')
        text = 'ПРОИГРЫВАТЬ НЕ СТРАШНО, ОБИДНО НЕ ИГРАТЬ...'
        for i in text:
            sleep(0.04)
            print(i, end='')
        sleep(0.6)
        print(f'{Game.dc}')
        # print(f'{Game.bc}{"-" * 77}{Game.dc}')


Greet.greet()  # напутствие перед игрой
while True:
    g = Game()  # создаем экземпляр игры
    if g.start():
        break
    else:
        continue
