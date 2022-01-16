def keyboard_closed(self):
    self._keyboard.unbind(on_key_down=self.on_keyboard_down)
    self._keyboard.unbind(on_key_up=self.on_keyboard_up)
    self._keyboard = None

def on_keyboard_down(self, keyboard, keycode, text, modifiers):
    if keycode[1] == 'left':
        self.current_speed_x = self.SPEED_X
        print("<- left")
    elif keycode[1] == 'right':
        self.current_speed_x = -self.SPEED_X
        print("right ->")
    return True


def on_keyboard_up(self, keyboard, keycode):
    self.current_speed_x = 0
    print("stop")
    return True


def on_touch_down(self, touch):
    if touch.x < self.width / 2:
        print("<- left")
        self.current_speed_x = self.SPEED_X
    else:
        print("right ->")
        self.current_speed_x = -self.SPEED_X


def on_touch_up(self, touch):
    print("stop")
    self.current_speed_x = 0
