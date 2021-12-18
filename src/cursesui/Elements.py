import curses
from curses.textpad import rectangle
from math import atan2, pi, sqrt

from cursesui.Utility import _check_and_add, draw_borders, draw_separator, message_box, put, init_colors, cct_len, show_controls_window, str_smart_split, color_pair_nums

Y_OFFSET = 3
X_OFFSET = 1

class Window:
    def __init__(self, window):
        init_colors()
        self.window = window
        self.HEIGHT, self.WIDTH = window.getmaxyx()
        self.current_menu = None
        self.running = True
        self.window.keypad(1)
        self.initUI()

    def get_window(self):
        return self.window

    def start(self):
        while self.running:
            if self.current_menu:
                self.current_menu.draw()
                key = self.window.getch()
                self.handle_key(key)
                self.current_menu.handle_key(key)

    def exit(self):
        self.running = False

    def initUI(self):
        pass

    def handle_key(self, key: int):
        pass

class MenuTab:
    def __init__(self, parent: Window, name: str):
        self.parent = parent
        self.name = name
        self.elements = []

    def add_element(self, element: 'UIElement'):
        self.elements += [element]

    def draw(self):
        for element in self.elements:
            element.draw()

    def handle_key(self, key: int):
        if len(self.elements) > 0:
            focused_element_id = self.get_focused_element_id()
            if focused_element_id == -1:
                return
            element = self.elements[focused_element_id]
            element.handle_key(key)

    def unfocus_all(self):
        for e in self.elements:
            e.set_focused(False)

    def focus(self, id: int):
        self.elements[id].set_focused(True)

    def get_focused_element_id(self):
        for i in range(len(self.elements)):
            if self.elements[i].focused:
                return i
        return -1

class Menu:
    def __init__(self, parent: Window, title: str):
        self.parent = parent
        self.title = title
        self.border_color_pair = 'normal'
        self.bottom_description = ''
        self.controls = {}
        self.display_tabs = False

        self.tabs = []
        self.selected_tab = 0
        self.tabs += [MenuTab(self.parent, 'MAIN TAB')]

    def get_window(self):
        return self.parent.window

    def handle_key(self, key: int):
        if key == 63: # ?
            self.show_controls()
        if key == 9: # TAB
            self.selected_tab += 1
            if self.selected_tab >= len(self.tabs):
                self.selected_tab = 0
        if key == 353: # SHIFT+TAB
            self.selected_tab -= 1
            if self.selected_tab < 0:
                self.selected_tab = len(self.tabs) - 1
        self.tabs[self.selected_tab].handle_key(key)

    def add_element(self, element: 'UIElement'):
        self.tabs[self.selected_tab].add_element(element)

    def add_tab(self, tab: MenuTab):
        self.display_tabs = True
        self.tabs += [tab]

    def draw_tabs(self):
        parent_window = self.get_window()
        x = 1
        y = 2
        for i in range(len(self.tabs)):
            tab = self.tabs[i]
            parent_window.addstr(y, x, '[')
            attr = curses.A_REVERSE if i == self.selected_tab else 0
            put(parent_window, y, x + 1, tab.name, attr)
            x += cct_len(tab.name) + 4
            put(parent_window, y, x - 3, ']')

    def draw(self):
        parent_window = self.get_window()
        parent_window.clear()
        draw_borders(parent_window, self.border_color_pair)
        put(parent_window, 1, 1, self.title)
        draw_separator(parent_window, 2, self.border_color_pair)
        if self.display_tabs:
            self.draw_tabs()
        self.tabs[self.selected_tab].draw()
        if self.bottom_description != '':
            self.draw_bottom_description()
        parent_window.refresh()

    def draw_bottom_description(self):
        parent_window = self.get_window()
        lines = str_smart_split(self.bottom_description, self.parent.WIDTH - 2)
        y = self.parent.HEIGHT - len(lines) - 1
        for i in range(len(lines)):
            put(parent_window, y + i, 1, lines[i])

    def show_controls(self):
        if self.controls == {}:
            message_box(self.parent, '#red-black No controls set!', ['Ok'])
        else:
            show_controls_window(self.parent, self.controls)

    def rename_main_tab(self, name: str):
        self.tabs[0].name = name

class UIElement:
    def __init__(self, parent: Window, text: str):
        self.parent = parent
        self.text = text
        self.focused = False

        self.focused_format = '{}'
        self.focused_attribute = curses.A_REVERSE

        self.y = 0
        self.x = 0

        self.next = None
        self.next_key = 258

        self.prev = None
        self.prev_key = 259

    def set_focused(self, value: bool):
        self.focused = value

    def set_pos(self, y: int, x: int):
        self.y = y
        self.x = x

    def draw(self):
        parent_window = self.parent.window
        if self.focused:
            put(parent_window, self.y + Y_OFFSET, self.x + X_OFFSET, self.focused_format.format(self.text), self.focused_attribute)
        else:
            put(parent_window, self.y + Y_OFFSET, self.x + X_OFFSET, self.text)

    def handle_key(self, key: int):
        if key == self.next_key and self.next:
            self.set_focused(False)
            self.next.set_focused(True)
        if key == self.prev_key and self.prev:
            self.set_focused(False)
            self.prev.set_focused(True)

    def draw_width(self):
        return cct_len(self.focused_format.format(self.text))

class Canvas(UIElement):
    def __init__(self, parent: Window, text: str, height: int, width: int, border_color_pair: str='none'):
        super().__init__(parent, text)
        self.height = height
        self.width = width
        self.border_color_pair = border_color_pair

    def draw(self):
        if self.border_color_pair == 'none':
            return
        y = self.y + Y_OFFSET
        x = self.x + X_OFFSET
        parent_window = self.parent.get_window()
        parent_window.attron(curses.color_pair(color_pair_nums[self.border_color_pair]))
        rectangle(parent_window, y, x, y + self.height, x + self.width)
        parent_window.attroff(curses.color_pair(color_pair_nums[self.border_color_pair]))

class BarChart(Canvas):
    def __init__(self, parent: Window, height: int, width: int, values: list[int], label_color_pair: str='none', distance_between_columns: int=1, border_color_pair: str='none'):
        super().__init__(parent, '', height, width, border_color_pair)
        if width / (distance_between_columns + 1) < len(values):
            raise Exception('ERR: in BarChart width is bigger than the amount of values')
        self.values = values
        self.label_color_pair = label_color_pair
        self.distance_between_columns = distance_between_columns

    def draw(self):
        super().draw()
        y = self.y + Y_OFFSET
        x = self.x + X_OFFSET
        parent_window = self.parent.get_window()
        if len(self.values) == 0:
            return
        max_val = max(self.values)
        temp_vals = list(self.values)
        temp_vals = [int(value * (self.height - 2) / max_val) for value in temp_vals]
        if self.label_color_pair != 'none':
            parent_window.attron(curses.color_pair(color_pair_nums[self.label_color_pair]))
            for i in range(len(self.values)):
                parent_window.addstr(y + self.height - 1, x + 1 + (self.distance_between_columns + 1) * i, str(i))
            parent_window.attroff(curses.color_pair(color_pair_nums[self.label_color_pair]))
        for i in range(self.height - 2):
            for j in range(len(temp_vals)):
                if temp_vals[j] > 0:
                    parent_window.addstr(y + self.height - i - 2, x + 1 + (self.distance_between_columns + 1) * j, '#')
                    temp_vals[j] -= 1

class PieChart(Canvas):
    def __init__(self, parent: Window, height: int, width: int, values: list[int], border_color_pair: str='none', colors: list[str]=None):
        super().__init__(parent, '', height, width, border_color_pair)
        self.values = values
        self.center_y = 0
        self.center_x = 0
        self.radius = 0
        self.set_position_vars()
        self.set_values_vars()
        if colors == None:
            colors = [f'{(i + 1) * 20}' for i in range(len(self.values))]
        self.set_colors(colors)

    def set_values(self, values: list[int]):
        self.values = list(values)
        self.set_values_vars()

    def set_colors(self, colors: list[str]):
        self.colors = colors
        colors = [f'{color}-black' for color in colors]
        for color_pair in colors:
            _check_and_add(color_pair)
        # message_box(self.parent, str(colors))
        self.color_pairs = [curses.color_pair(color_pair_nums[color_pair]) for color_pair in colors]
        # self.color_pairs.reverse()

    def set_values_vars(self):
        self.total = sum(self.values)
        if self.total == 0:
            return
        # self.values = sorted(self.values)
        for i in range(1, len(self.values)):
            self.values[i] = self.values[i] + self.values[i - 1]
        self.rads = [value * pi * 2 / self.total - pi for value in self.values]

    def set_position_vars(self):
        self.center_y = self.height // 2 + Y_OFFSET + self.y
        self.center_x = self.width // 2 + X_OFFSET + self.x
        self.radius = min(self.height // 2, self.width // 2)

    def set_pos(self, y: int, x: int):
        super().set_pos(y, x)
        self.set_position_vars()

    def draw(self):
        super().draw()
        parent_window = self.parent.get_window()
        y = self.y + Y_OFFSET
        x = self.x + X_OFFSET
        double_radius = self.radius * 2
        # parent_window.addstr(y, x, str(self.colors))
        # parent_window.addstr(y + 1, x, str(self.values))
        # rs = ['%.2f' % rad for rad in self.rads]
        # parent_window.addstr(y + 2, x, str(rs))
        for i in range(1, double_radius):
            for j in range(double_radius * 2):
                y_pos = y + i
                x_pos = self.center_x - double_radius + j
                distance = sqrt((self.center_y - y_pos) ** 2 + ((self.center_x - x_pos) // 2) ** 2)
                if distance <= self.radius:
                    if self.total == 0:
                        parent_window.addstr(y_pos, x_pos, '#')
                        continue
                    top = y_pos - self.center_y
                    bottom = x_pos - self.center_x
                    rad = atan2(top, bottom)
                    ri = 0
                    for ri in range(len(self.rads)):
                        if rad <= self.rads[ri]:
                            break
                    parent_window.addstr(y_pos, x_pos, '#', self.color_pairs[ri])

class Separator(UIElement):
    def __init__(self, parent: Window, y: int, text: str='', color_pair: str='normal'):
        super().__init__(parent, text)
        self.color_pair = color_pair
        self.y = y

    def draw(self):
        draw_separator(self.parent.get_window(), self.y + Y_OFFSET, self.color_pair)
        if self.text != '':
            put(self.parent.get_window(), self.y + Y_OFFSET, 1, self.text)

class VerticalLine(UIElement):
    def __init__(self, parent: Window, height: int, color_pair: str='normal', y: int=0, x: int=0):
        super().__init__(parent, '')
        self.height = height
        self.color_pair = color_pair
        self.y = y
        self.x = x

    def draw(self):
        parent_window = self.parent.get_window()
        y = self.y + Y_OFFSET
        x = self.x + X_OFFSET
        color_pair_attr = curses.color_pair(color_pair_nums[self.color_pair])
        parent_window.attron(color_pair_attr)
        for i in range(self.height):
            if parent_window.inch(y + i, x) - color_pair_attr == curses.ACS_HLINE:
                if i == 0:
                    parent_window.addch(y + i, x, curses.ACS_TTEE)
                elif i == self.height - 1:
                    parent_window.addch(y + i, x, curses.ACS_BTEE)
                else:
                    parent_window.addch(y + i, x, curses.ACS_PLUS)
            else:
                parent_window.addch(y + i, x, curses.ACS_VLINE)
        parent_window.attroff(color_pair_attr)

class Button(UIElement):
    def __init__(self, parent: Window, text: str, click=None):
        super().__init__(parent, text)
        self.click = click
        self.clickKey = 10

    def handle_key(self, key: int):
        super().handle_key(key)
        if key == self.clickKey and self.click:
            self.click()

class TextField(UIElement):
    def __init__(self, parent: Window, text: str, max_width: int, on_change=None):
        if len(text) > max_width:
            raise Exception('ERR: Starting text in TextField is longer than max_width')
        super().__init__(parent, text)
        self.cursor = len(text)
        self.max_width = max_width
        self.placeholder_char = '_'
        self.on_change = on_change

    def handle_key(self, key: int):
        super().handle_key(key)
        if (key == 127 or key == 8) and len(self.text) > 0:
            self.text = self.text[:-1]
            self.cursor -= 1
        if len(self.text) == self.max_width:
            return
        if key >= 97 and key <= 122:
            self.text += chr(key)
            self.cursor += 1
        if key >= 65 and key <= 90:
            self.text += chr(key)
            self.cursor += 1
        if key == 45 or key == 39 or key == 58: # -/'/:
            self.text += chr(key)
            self.cursor += 1
        if key == 32:
            self.text += ' '
            self.cursor += 1
        if self.on_change != None:
            self.on_change()

    def draw(self):
        y = self.y + Y_OFFSET
        x = self.x + X_OFFSET
        parent_window = self.parent.window
        placeholder = self.placeholder_char * (self.max_width - len(self.text))
        parent_window.addstr(y, x, self.text)
        parent_window.addstr(y, x + len(self.text), placeholder)
        if self.focused:
            char = ' '
            if self.cursor < len(self.text):
                char = self.text[self.cursor]
            parent_window.addch(y, x + self.cursor, char, curses.A_REVERSE)

    def draw_width(self):
        return self.max_width

    def reset_text(self):
        self.text = ''
        self.cursor = 0

class NumericLeftRight(UIElement):
    def __init__(self, parent: Window, value: int, min_val: int, max_val: int):
        super().__init__(parent, '')
        self.min_val = min_val
        self.max_val = max_val
        self.value = value

    def handle_key(self, key: int):
        super().handle_key(key)
        if key == 261 and self.value < self.max_val: # LEFT
            self.value += 1
        if key == 260 and self.value > self.min_val: # RIGHT
            self.value -= 1

    def draw_width(self):
        return len(str(self.max_val)) + 2

    def draw(self):
        y = self.y + Y_OFFSET
        x = self.x + X_OFFSET
        parent_window = self.parent.window
        placeholder = ' ' * (len(str(self.max_val)) - len(str(self.value)))
        parent_window.addstr(y, x, f'<{self.value}{placeholder}>')
        if self.focused:
            parent_window.addch(y, x, '<', curses.A_REVERSE)
            parent_window.addch(y, x + len(str(self.max_val)) + 1, '>', curses.A_REVERSE)

class WordChoice(UIElement):
    def __init__(self, parent: Window, options: list[str], start=0):
        super().__init__(parent, '')
        if start >= len(options):
            raise Exception('ERR: start in WordChoice is bigger than amount of options')
        self.choice = start
        self.options = options
        self.max_width = max([cct_len(o) for o in options])

    def draw(self):
        y = self.y + Y_OFFSET
        x = self.x + X_OFFSET
        placeholder = ' ' * (self.max_width - cct_len(self.options[self.choice]))
        parent_window = self.parent.window
        put(parent_window, y, x, f'<{self.options[self.choice]}{placeholder}>')
        if self.focused:
            parent_window.addch(y, x, '<', curses.A_REVERSE)
            parent_window.addch(y, x + self.max_width + 1, '>', curses.A_REVERSE)

    def handle_key(self, key: int):
        super().handle_key(key)
        if key == 261 and self.choice < len(self.options) - 1: # LEFT
            self.choice += 1
        if key == 260 and self.choice > 0: # RIGHT
            self.choice -= 1

    def draw_width(self):
        return self.max_width + 2

    def get_selected_value(self):
        return self.options[self.choice]

class Widget(UIElement):
    def __init__(self, parent: Window, stretch: bool=False):
        super().__init__(parent, 'err')
        self.sub_elements = []
        self.distance = 0
        self.focused_element_id = 0
        self.stretch = stretch

    def set_pos(self, y: int, x: int):
        super().set_pos(y, x)
        self.distance = 0
        elements = list(self.sub_elements)
        self.sub_elements = []
        for element in elements:
            self.add_element(element)

    def add_element(self, element: UIElement):
        element.set_pos(self.y, self.x + self.distance)
        self.sub_elements += [element]
        self.distance += 1 + element.draw_width()

    def set_focused(self, value: bool):
        super().set_focused(value)
        self.sub_elements[self.focused_element_id].set_focused(value)

    def handle_key(self, key: int):
        self.sub_elements[self.focused_element_id].handle_key(key)
        super().handle_key(key)

    def draw(self):
        if not self.stretch:
            for e in self.sub_elements:
                e.draw()
            return
        if len(self.sub_elements) != 2:
            raise Exception(f'ERR: Not implemented stretched draw with more than 2 elements(amount of elements: {len(self.sub_elements)})')
        # TO-DO: Implement a better way to stretch elements
        self.sub_elements[0].draw()
        last = self.sub_elements[1]
        width = last.draw_width()
        last.set_pos(self.y, self.parent.WIDTH - width - 2)
        last.draw()

class List(Canvas):
    def __init__(self, parent: Window, options: list[str], height: int=-1, width: int=-1, click=None, border_color_pair='none'):
        super().__init__(parent, '', height, width, border_color_pair)
        self.options = options
        self.click = click
        self.border_color = 'none'
        self.scroll_down_key = 62
        self.scroll_up_key = 60
        self.choice = 0
        self.page_n = 0
        self.cursor = 0
        if height == -1:
            self.height = len(options) + 2
        self.displayed_elements_num = self.height - 2
        if width == -1:
            self.width = max([cct_len(o) for o in self.options]) + 3

    def set_pos(self, y: int, x: int):
        if self.displayed_elements_num + y + Y_OFFSET > self.parent.HEIGHT:
            # curses.beep()
            self.displayed_elements_num = self.parent.HEIGHT - x - X_OFFSET
        super().set_pos(y, x)

    def draw_scroller(self):
        if len(self.options) > self.displayed_elements_num:
            y = self.y + Y_OFFSET
            x = self.x + X_OFFSET + 1
            parent_window = self.parent.get_window()
            # draw arrows
            if self.page_n != 0:
                parent_window.addch(1 + y, self.width - 2 + x, curses.ACS_UARROW)
            if self.page_n != len(self.options) - self.displayed_elements_num:
                parent_window.addch(self.height - 2 + y, self.width - 2 + x, curses.ACS_DARROW)
            # draw the scroller
            scroller_length = self.height - 4
            for i in range(scroller_length):
                parent_window.addch(2 + y + i, self.width - 2 + x, curses.ACS_VLINE)
    
    def draw(self):
        super().draw()
        y = self.y + Y_OFFSET
        x = self.x + X_OFFSET
        parent_window = self.parent.get_window()
        # parent_window.addstr(y, x, str(self.displayed_elements_num))
        self.draw_scroller()
        for i in range(min(self.displayed_elements_num, len(self.options))):
            if i == self.cursor and self.focused:
                put(parent_window, i + y + 1, x + 1, self.options[i + self.page_n], curses.A_REVERSE)
            else:
                put(parent_window, i + y + 1, x + 1, self.options[i + self.page_n])

    def handle_key(self, key: int):
        # the main thing
        if key == 10 and len(self.options) > 0: # ENTER
            self.click(self.choice, self.cursor, self.options[self.choice])
        if key == self.scroll_up_key: # SCROLL UP
            self.choice -= 1
            self.cursor -= 1
            if self.cursor < 0:
                if len(self.options) > self.displayed_elements_num:
                    if self.page_n == 0:
                        self.cursor = self.displayed_elements_num - 1
                        self.choice = len(self.options) - 1
                        self.page_n = len(self.options) - self.displayed_elements_num
                    else:
                        self.page_n -= 1
                        self.cursor += 1
                else:
                    self.cursor = len(self.options) - 1
                    self.choice = self.cursor
        if key == self.scroll_down_key: # SCROLL DOWN
            self.choice += 1
            self.cursor += 1
            if len(self.options) > self.displayed_elements_num:
                if self.cursor >= self.displayed_elements_num:
                    self.cursor -= 1
                    self.page_n += 1
                    if self.choice == len(self.options):
                        self.choice = 0
                        self.cursor = 0
                        self.page_n = 0
            else:
                if self.cursor >= len(self.options):
                    self.cursor = 0
                    self.choice = 0
        # check parent keys
        super().handle_key(key)

    def set_options(self, options: list[str]):
        self.options = options
        self.cursor = 0
        self.page_n = 0
        self.choice = 0

    def set_option_at(self, index: int, value: str):
        self.options[index] = value

    def get_selected(self):
        return self.options[self.choice]
