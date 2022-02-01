import random

from kivy.config import Config
from kivy.lang import Builder
from kivy.uix.relativelayout import RelativeLayout

Config.set('graphics', 'width', '1400') # Zde si dáme velikost šírky našeho herního okna
Config.set('graphics', 'height', '600') # Zde si dáme velikost výšku našeho herního okna

from kivy import platform
from kivy.core.window import Window
from kivy.app import App
from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Line, Quad, Triangle
from kivy.properties import NumericProperty, Clock, ObjectProperty, StringProperty

Builder.load_file("menu.kv")

class MainWidget(RelativeLayout):
    from pov import transform, transform_2D, transform_perspective # Naimportujeme si pov (point_of_view) do našeho main.py
    from movement import keyboard_closed, on_keyboard_up, on_keyboard_down, on_touch_up, on_touch_down # Naimportujeme si movement do našeho main.py


    #   1)
    #TOHLE TO JSOU PROMĚNNÉ, KTERÉ JSOU NASTAVENÉ NA DEFAULT HODNOTU A MĚNÍ SE PODLE TOHO,
    #CO JE ZA PODMÍNKU V BUDOUCÍCH FUNKCÍCH A PODMÍNKÁCH

    level_widget = ObjectProperty() #Nastavení tzv. sub-class, abychom pak mohli pracovat s touhle proměnou v .kv a .py
    perspective_point_x = NumericProperty(0) #Opět nastavení tzv. sub-class
    perspective_point_y = NumericProperty(0) #A znova nastavení tzv. sub-class

    V_NB_LINES = 8 # Počet vertikálních přímek
    V_LINES_SPACING = .4  # Mezera mezi vertikálními přímkami (v procentech)
    vertical_lines = [] # List všech vertikálních přímek

    H_NB_LINES = 15 # Počet horizontálních přímek
    H_LINES_SPACING = .1  # Mezera mezi horizontálními přímkami (v procentech)
    horizontal_lines = [] # List všech horizontálních přímek

    SPEED = 1 # Rychlost vertikálních přímek dolů
    current_offset_y = 0 # Díky téhle proměnné se horizontální přímky pohybují směrem dolů (více info dole)
    current_y_loop = 0 # Pokud je current_offset_y větší než V_LINES_SPACING, tak se vygeneruje nový čtverec a opakuje se to takhle do nekonečna (více info dole)

    SPEED_X = 3.0 # Rychlost horizontálních přímek doleva/doprava
    current_speed_x = 0 # Funguje jako změna pohybu všech vertikálních přímek na opačnou stranu (current_speed_x < 0 --> doleva, 0 < current_speed_x --> doprava)
    current_offset_x = 0 # Díky téhle proměnné se vertikální přímky pohybují směrem doleva/doprava (více info dole)

    NB_TILES = 12 # Počet vykreslovaných bílých čtverců před ship (hráčem)
    tiles = [] # List všech vygenerovaných bílých čtverců
    tiles_coordinates = [] # Zde se budou ukládat pozice jednotlivých bílých čtverců od středu -> prostřední čtv. má (0,0) jeden čtverec doleva a o dvě nahoru (-1,2)

    SHIP_WIDTH = .1 # Šířka ship (hráče) v procentech - ono se to pak násobí šírkou okna, tak proto je tak nízká hodnota v % (např. 900 * 0.1 = 90)
    SHIP_HEIGHT = 0.035 # Výška ship (hráče) v procentech - opět se to násobí výškou okna (např. 400 * 0.035 = 14)
    SHIP_BASE_Y = 0.04 # Určuje, jak daleko bude ship (hráč) od spodní hrany v procentech - a znova se to násobí výškou okna (např. 400 * 0.04 = 16)
    ship = None # Zde se inicializuje Trinagle(), více na řádku 96
    ship_coordinates = [(0, 0), (0, 0), (0, 0)] # Zde se budou ukládat pozice jednotlivých vrcholů trojúhelníku (bude sloužit pro vyjetí z bílé trasy)
    state_game_over = False # Říká nám, jestli jsme prohráli nebo ne (více info dole - využívá se hlavně pro GAME OVER screen)
    state_game_has_started = False # Říká nám, jestli hra začala nebo ne (více info dole - využívá se hlavně pro button na začátku START místo RESTART)

    menu_title = StringProperty("S Y N T H W A V E") # Název labelu při STARTu nebo GAME OVERu
    menu_button_levels = StringProperty("LEVEL") # Název buttonu
    menu_button_settings = StringProperty("SETTINGS") # Název buttonu
    menu_button_credits = StringProperty("CREDITS") # Název buttonu
    score_txt = StringProperty() # Název labelu sloužící pro vypsání skóre

    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        self.init_vertical_lines()
        self.init_horizontal_lines()
        self.init_tiles()
        self.init_ship()
        self.reset_game()

        if self.is_desktop():
            self._keyboard = Window.request_keyboard(self.keyboard_closed, self)
            self._keyboard.bind(on_key_down=self.on_keyboard_down)
            self._keyboard.bind(on_key_up=self.on_keyboard_up)

        Clock.schedule_interval(self.update, 1.0 / 60.0)

    def reset_game(self):
        self.current_offset_y = 0
        self.current_y_loop = 0
        self.current_speed_x = 0
        self.current_offset_x = 0
        self.tiles_coordinates = []
        self.score_txt = "SCORE: " + str(self.current_y_loop)
        self.pre_fill_tiles_coordinates()
        self.generate_tiles_coordinates()
        self.state_game_over = False

    # Funkce pro zjištění, jestli hráč hraje na desktopu a jestli ne, tak logicky odvodíme,
    # že je na mobilním zařízení a přizpůsobí se tomu movement (desktop - šipky, mobil - klikání)
    def is_desktop(self):
        if platform in ('linux', 'win', 'macosx'):
            return True
        return False

    # Funkce pro inicializování ship (hráče) a dává to tvar a barvu (trojúhelník a bílá barva)
    def init_ship(self):
        with self.canvas:
            Color(0, 250, 250)
            self.ship = Triangle()

    # Funkce pro updatování ship (hráče) podle jeho movementu
    # center_x - slouží pro vycenterování ship (tedy 900 / 2 a dostaneme střed 450)
    # base_y - vysvětlění na řádku 54.
    # ship_half_width - slouží pro vypočítání pozice vrcholů v trojúhelníku (levého dolního a pravého dolního), použije se na 117. a 119. řádkách
    # ship_height - slouží pro vypočítání pozice vrcholu v trojúhelníku (horního středového), použije se na 118. řádku
    # ship.coordinates - slouží pro vypočítání jednotlivých vrcholů --> např. levý dolní vrchol = (center_x-ship_half_width, base_y)
    # x1, y1, atd.. - slouží pro transformování point of view (pov), více v souboru pov.py
    def update_ship(self):
        center_x = self.width / 2
        base_y = self.SHIP_BASE_Y * self.height
        ship_half_width = self.SHIP_WIDTH * self.width / 2
        ship_height = self.SHIP_HEIGHT * self.height
        # .......
        #    2
        #  1   3
        # .......
        self.ship_coordinates[0] = (center_x-ship_half_width, base_y)
        self.ship_coordinates[1] = (center_x, base_y + ship_height)
        self.ship_coordinates[2] = (center_x + ship_half_width, base_y)

        x1, y1 = self.transform(*self.ship_coordinates[0])
        x2, y2 = self.transform(*self.ship_coordinates[1])
        x3, y3 = self.transform(*self.ship_coordinates[2])

        self.ship.points = [x1, y1, x2, y2, x3, y3]

    def check_ship_collision(self):
        for i in range(0, len(self.tiles_coordinates)):
            ti_x, ti_y = self.tiles_coordinates[i]
            if ti_y > self.current_y_loop + 1:
                return False
            if self.check_ship_collision_with_tile(ti_x, ti_y):
                return True
        return False

    def check_ship_collision_with_tile(self, ti_x, ti_y):
        xmin, ymin = self.get_tile_coordinates(ti_x, ti_y)
        xmax, ymax = self.get_tile_coordinates(ti_x + 1, ti_y + 1)
        for i in range(0, 3):
            px, py = self.ship_coordinates[i]
            if xmin <= px <= xmax and ymin <= py <= ymax:
                return True
        return False

    def init_tiles(self):
        with self.canvas:
            Color(1, 1, 1)
            for i in range(0, self.NB_TILES):
                self.tiles.append(Quad())

    def pre_fill_tiles_coordinates(self):
        for i in range(0, 10):
            self.tiles_coordinates.append((0, i))

    def generate_tiles_coordinates(self):
        last_x = 0
        last_y = 0

        for i in range(len(self.tiles_coordinates)-1, -1, -1):
            if self.tiles_coordinates[i][1] < self.current_y_loop:
                del self.tiles_coordinates[i]

        if len(self.tiles_coordinates) > 0:
            last_coordinates = self.tiles_coordinates[-1]
            last_x = last_coordinates[0]
            last_y = last_coordinates[1] + 1

        for i in range(len(self.tiles_coordinates), self.NB_TILES):
            r = random.randint(0, 2)
            # 0 -> rovne
            # 1 -> doprava
            # 2 -> doleva
            start_index = -int(self.V_NB_LINES / 2) + 1
            end_index = start_index + self.V_NB_LINES - 1
            if last_x <= start_index:
                r = 1
            if last_x + 1 >= end_index:
                r = 2

            self.tiles_coordinates.append((last_x, last_y))
            if r == 1:
                last_x += 1
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))
            if r == 2:
                last_x -= 1
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))

            last_y += 1

    def init_vertical_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            for i in range(0, self.V_NB_LINES):
                self.vertical_lines.append(Line())

    def get_line_x_from_index(self, index):
        central_line_x = self.perspective_point_x
        spacing = self.V_LINES_SPACING * self.width
        offset = index - 0.5
        line_x = central_line_x + offset*spacing + self.current_offset_x
        return line_x

    def get_line_y_from_index(self, index):
        spacing_y = self.H_LINES_SPACING*self.height
        line_y = index*spacing_y-self.current_offset_y
        return line_y

    def get_tile_coordinates(self, ti_x, ti_y):
        ti_y = ti_y - self.current_y_loop
        x = self.get_line_x_from_index(ti_x)
        y = self.get_line_y_from_index(ti_y)
        return x, y

    def update_tiles(self):
        for i in range(0, self.NB_TILES):
            tile = self.tiles[i]
            tile_coordinates = self.tiles_coordinates[i]
            xmin, ymin = self.get_tile_coordinates(tile_coordinates[0], tile_coordinates[1])
            xmax, ymax = self.get_tile_coordinates(tile_coordinates[0]+1, tile_coordinates[1]+1)

            #  2    3
            #
            #  1    4
            x1, y1 = self.transform(xmin, ymin)
            x2, y2 = self.transform(xmin, ymax)
            x3, y3 = self.transform(xmax, ymax)
            x4, y4 = self.transform(xmax, ymin)

            tile.points = [x1, y1, x2, y2, x3, y3, x4, y4]

    def update_vertical_lines(self):
        # -1 0 1 2
        start_index = -int(self.V_NB_LINES/2)+1
        for i in range(start_index, start_index+self.V_NB_LINES):
            line_x = self.get_line_x_from_index(i)

            x1, y1 = self.transform(line_x, 0)
            x2, y2 = self.transform(line_x, self.height)
            self.vertical_lines[i].points = [x1, y1, x2, y2]

    def init_horizontal_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            for i in range(0, self.H_NB_LINES):
                self.horizontal_lines.append(Line())

    def update_horizontal_lines(self):
        start_index = -int(self.V_NB_LINES / 2) + 1
        end_index = start_index+self.V_NB_LINES-1

        xmin = self.get_line_x_from_index(start_index)
        xmax = self.get_line_x_from_index(end_index)
        for i in range(0, self.H_NB_LINES):
            line_y = self.get_line_y_from_index(i)
            x1, y1 = self.transform(xmin, line_y)
            x2, y2 = self.transform(xmax, line_y)
            self.horizontal_lines[i].points = [x1, y1, x2, y2]

    def update(self, dt):
        #Optimalizace kódu, protože máme frames per second nastaveno na 60, ale kompilátoru trvají některé věci déle, a proto to musíme vzít v potaz.
        #Pokud bychom tenhle time_factor neudělali, tak na řádku 277 bychom měli například 0 += (4*900/100)
        #Pro lepší vysvětlení command nížeł
        #print("dt: " + str(dt*60))
        time_factor = dt*60

        self.update_vertical_lines()
        self.update_horizontal_lines()
        self.update_tiles()
        self.update_ship()

        if not self.state_game_over and self.state_game_has_started:
            speed_y = self.SPEED * self.height / 100
            self.current_offset_y += speed_y * time_factor

            spacing_y = self.H_LINES_SPACING * self.height
            while self.current_offset_y >= spacing_y:
                self.current_offset_y -= spacing_y
                self.current_y_loop += 1
                self.score_txt = "SCORE: " + str(self.current_y_loop)
                self.generate_tiles_coordinates()

            speed_x = self.current_speed_x * self.width / 100
            self.current_offset_x += speed_x * time_factor

        if not self.check_ship_collision() and not self.state_game_over:
            self.state_game_over = True
            self.menu_title = "G A M E  O V E R"
            self.menu_button_title = "RESTART"
            self.level_widget.opacity = 1
            print("GAME OVER")

    def on_level_button_pressed(self):
        self.reset_game()
        self.state_game_has_started = True
        self.level_widget.opacity = 0

    def on_settings_button_pressed(self):
        pass

    def on_credits_button_pressed(self):
        pass





class SynthwaveApp(App):
    pass


SynthwaveApp().run()


