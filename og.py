try:
    import curses
except ModuleNotFoundError as e:
    import os
    if os.name.startswith("nt"):
        print("windows-curses package is required")
        exit(-1)
    else:
        raise e

class App:
    def __init__(self):
        self.c = 1
        self.y = 1
        self.x = 30
        self.running = True
        self.missleyx = None
        self.recent_missleyx = None
        self.enemy_rows = self.init_enemies()
        self.enemy_delay = 0
        self.enemy_dx = 1
        self.frame_time = 25
        self.num = 0
        self.score = 0
        self.hiscore = 0
        self.starting_enemy_delay = 5
        self.state = "start"

    def init_enemies(self):
        enemies = []
        for a in range (30, 40, 2):
            line = []
            for i in range (5, 55, 4):
                line.append((a, i))
            enemies.append(line)
        return enemies
        
    def on_joystick(self,dx,dy):
        if 2 < (dx + self.x) < 59:
            self.x += dx
        if 0 < (dy + self.y) < 2:
            self.y += dy
    
    def on_next_level(self, new_delay_val):
        self.state = "game"
        self.enemy_rows = self.init_enemies()
        self.starting_enemy_delay = new_delay_val
    
    def on_win(self):
        self.on_next_level(self.starting_enemy_delay - 1)
        if self.hiscore < self.score:
            self.hiscore = self.score
    
    def on_lose(self):
        self.on_next_level(5)
        if self.hiscore < self.score:
            self.hiscore = self.score
        self.score = 0
        
    def on_shoot(self):
        if self.state.startswith("game"):
            if self.missleyx is None:
                self.missleyx = (self.y, self.x)
        elif self.state.startswith("start"):
            self.on_next_level(5)
        elif self.state.startswith("win"):
            self.on_win()
        elif self.state.startswith("lose"):
            self.on_lose()
        
    def onHit(self):
        self.recent_missleyx = self.missleyx 
        self.missleyx = None
        
    def onKey(self, key, window):
        if key == curses.KEY_LEFT: #68
            self.on_joystick(-1,0)
        elif key == curses.KEY_RIGHT: #67
            self.on_joystick(1,0)
        elif key == curses.KEY_UP: #65
            self.on_joystick(0,-1)
        elif key == curses.KEY_DOWN: #66
            self.on_joystick(0,1)
        elif key == 32: # space
            self.on_shoot()
        elif key == 120:
            self.running = False

    def event(self, window):
        ch = window.getch()
        if ch != curses.ERR:
            self.onKey(ch, window)

    def render_game(self, window):
        window.addstr(self.y, self.x-2, "\-V-/")
        for i in range(0, 41):
            window.addstr( i, 62, "||")
            window.addstr(2, 65, f"  Score: {self.score}")
            window.addstr(4, 65, f"Hiscore: {self.hiscore}")
        for line in self.enemy_rows:
            for ey, ex in line:
                window.addstr(ey, ex-1, "<%>", curses.color_pair(self.enemy_rows.index(line)+1))
        if self.missleyx:
            my, mx = self.missleyx
            window.addstr(my,   mx, "|", self.next_col_pair())
            
    def next_col_pair(self):
        self.c = (self.c+1) % 7
        return curses.color_pair(self.c)

    def render(self, window):
        window.erase()
        if self.state.startswith("game"):
            self.render_game(window)
        elif self.state.startswith("win"):
            window.addstr(20, 30, "You've won! Hit spacebar for next level.")
        elif self.state.startswith("lose"):
            window.addstr(20, 30, "  You've lost! Hit spacebar for regame.")
        elif self.state.startswith("start"):
            window.addstr( 5, 10, r"/-\|-\|-\/-\|'|/-\\ /", self.next_col_pair())
            window.addstr( 6, 10, r"| ||-<|-/| ||\||   V ", self.next_col_pair())
            window.addstr( 7, 10, r"\-/|-/| \\-/| |\-/ | ", self.next_col_pair())
            window.addstr( 8, 10, r"   /-\/-\|  /-\| /-|-\ /| /|", self.next_col_pair())
            window.addstr( 9, 10, r"   |  |-||  |-||<  |  V |< |", self.next_col_pair())
            window.addstr(10, 10, r"   \-7| ||--| || \ |  | | \|", self.next_col_pair())
            window.addstr(30, 30, "coded by GertosPP")
            window.addstr(20, 30, "       Hit spacebar for new game.")
        window.refresh()

    def get_hitten_enemy(self, my, mx):
        for line in self.enemy_rows:
            targets = list(filter(lambda e: e[0] == my and\
                (e[1] in [mx-1, mx, mx+1]), line))
            if targets:
                return targets.pop()
        return None

    def simulate_missle(self):
        if self.missleyx is not None:
            my, mx = self.missleyx
            my += 1
            if my > 40:
                self.onHit()
            else:
                self.missleyx = (my, mx)
                enemy = self.get_hitten_enemy(my, mx)
                if enemy:
                    for line in self.enemy_rows:
                        if enemy in line:
                            line.pop(line.index(enemy))
                            self.score += 10
                            self.onHit()

    def simulate_enemies(self):
        go_up = False
        for line in self.enemy_rows:
            for enemy in line:
                ey, ex = enemy
                ex += self.enemy_dx
                if 1 == (ex + self.enemy_dx) or\
                    (ex + self.enemy_dx) == 60:
                    go_up = True
                line[line.index(enemy)] = (ey, ex)
        if go_up:
            self.enemy_dx = -self.enemy_dx
            for line in self.enemy_rows:
                for enemy in line:
                    ey, ex = enemy
                    ey -= 1
                    if enemy in line:
                        line[line.index(enemy)] = (ey, ex)

    def enemies_on_top_line(self):
        def first_enemy_is_on_top_row(enemy_line):
            if len(enemy_line) > 0 and enemy_line[0][0] < 2:
                return True
        return len(list(filter(first_enemy_is_on_top_row, self.enemy_rows)))

            
    def no_enemies_left(self):
        return len(list(filter(lambda er: len(er) > 0, self.enemy_rows))) == 0
        
    def simulate(self, window):
        self.simulate_missle()
        if self.enemy_delay > 0:
            self.enemy_delay -= 1
        else:
            self.enemy_delay = self.starting_enemy_delay
            self.simulate_enemies()
        if self.no_enemies_left():
            self.state = "win"
        elif self.enemies_on_top_line():
            self.state = "lose"
    
    def start(self, window):
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
        window.keypad(True)
        window.nodelay(False)
        window.timeout(self.frame_time)
    
    def main(self, window):
        self.start(window)
        curses.resize_term(42,90)
        while self.running:
            self.event(window)
            self.simulate(window)
            self.render(window)
        window.keypad(False)
        
app = App()
curses.wrapper(app.main)
