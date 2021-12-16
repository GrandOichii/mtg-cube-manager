import curses
import os
import clipboard
from mtgsdk import CARD_TYPES, CCT_COLORS, Card, Cube, COLORS

from cursesui.Elements import Button, Menu, MenuTab, PieChart, Separator, TextField, UIElement, VerticalLine, Widget, Window, List
from cursesui.Utility import SINGLE_ELEMENT, cct_real_str, choose_file, draw_borders, drop_down_box, message_box, put, reverse_color_pair, str_smart_split

os.environ.setdefault('ESCDELAY', '25')

SAVE_PATH = 'cubes'
PIE_WHEEL_TYPE_COLORS = {
    'Creature': 'red',
    'Sorcery': 'pink',
    'Instant': 'cyan',
    'Enchantment': 'orange',
    'Artifact': 'gray',
    'Land': 'white',
    'Planeswalker': 'magenta'
}

def get_saved_cube_names():
    if not os.path.exists(SAVE_PATH):
        os.mkdir(SAVE_PATH)
        return []
    return [os.path.splitext(f)[0] for f in os.listdir(SAVE_PATH) if os.path.isfile(os.path.join(SAVE_PATH, f)) and os.path.splitext(f)[1] == '.cube']

class ColorStatisticsTab(MenuTab):
    def __init__(self, parent: Window, color: str, cube: Cube):
        super().__init__(parent, f'#{CCT_COLORS[color]} {color} statistics')
        self.color = color
        self.cube = cube
        self.initUI()

    def initUI(self):
        self.pie_chart_values = [2, 1, 1, 4]

        self.total_count_label = UIElement(self.parent, '')
        self.total_count_label.set_pos(1, 1)

        pie_chart_height = self.parent.HEIGHT - 35
        pie_chart_width = self.parent.WIDTH - 100
        self.pie_chart = PieChart(self.parent, pie_chart_height, pie_chart_width, self.pie_chart_values, ['red', 'blue', 'yellow', 'green'])
        self.pie_chart.set_pos(4, 1)

        self.creature_count_label = UIElement(self.parent, '')
        self.creature_count_label.set_pos(4, 80)
        
        self.sorcery_count_label = UIElement(self.parent, '')
        self.sorcery_count_label.set_pos(5, 80)

        self.instant_count_label = UIElement(self.parent, '')
        self.instant_count_label.set_pos(6, 80)

        self.enchantment_count_label = UIElement(self.parent, '')
        self.enchantment_count_label.set_pos(7, 80)

        self.artifact_count_label = UIElement(self.parent, '')
        self.artifact_count_label.set_pos(8, 80)

        self.land_count_label = UIElement(self.parent, '')
        self.land_count_label.set_pos(9, 80)

        self.planeswalker_count_label = UIElement(self.parent, '')
        self.planeswalker_count_label.set_pos(10, 80)

        self.type_labels = {
            'Creature': self.creature_count_label, 
            'Sorcery': self.sorcery_count_label, 
            'Instant': self.instant_count_label, 
            'Enchantment': self.enchantment_count_label, 
            'Artifact': self.artifact_count_label, 
            'Land': self.land_count_label,
            'Planeswalker': self.planeswalker_count_label
        }

        self.add_element(self.total_count_label)
        self.add_element(Separator(self.parent, 3, color_pair='orange-black'))
        self.add_element(self.pie_chart)
        self.add_element(Separator(self.parent, 3 + pie_chart_height + 1, color_pair='orange-black'))
        self.add_element(VerticalLine(self.parent, pie_chart_height + 2, 'orange-black', 3, 78))
        self.add_element(self.creature_count_label)
        self.add_element(self.sorcery_count_label)
        self.add_element(self.instant_count_label)
        self.add_element(self.enchantment_count_label)
        self.add_element(self.artifact_count_label)
        self.add_element(self.land_count_label)
        self.add_element(self.planeswalker_count_label)
        self.add_element(VerticalLine(self.parent, pie_chart_height + 2, 'orange-black', 3, 98))

    def update(self):
        count = self.cube.get_color_counts()[self.color]
        all_count = count['all']
        self.total_count_label.text = f'Total: #{CCT_COLORS[self.color]} {all_count}'

        pie_chart_values = []
        pie_chart_colors = []
        for card_type in CARD_TYPES:
            c = count[card_type]
            self.type_labels[card_type].text = f'#{PIE_WHEEL_TYPE_COLORS[card_type]}-black {card_type}: {c}'
            if c != 0:
                pie_chart_values += [c]
                pie_chart_colors += [PIE_WHEEL_TYPE_COLORS[card_type]]

        self.pie_chart.set_values(pie_chart_values)
        self.pie_chart.set_colors(pie_chart_colors)

    def handle_key(self, key: int):
        super().handle_key(key)

class CubeManagerMenu(Menu):
    def __init__(self, parent: Window, title: str, cube_name: str):
        super().__init__(parent, title)
        self.border_color_pair = 'orange-black'
        self.controls = {
            'Move selected tabs:': 'TAB/SHIFT+TAB',
            'Cards list movement': '</>',
            'Open card description window': 'D',
            'Save and exit': 'ESC'
        }

        self.cube = None
        self.load_cube(cube_name)
        self.initUI()
        self.update_color_count()

    def initUI(self):
        self.card_name_widget = Widget(self.parent)
        self.card_name_widget.add_element(UIElement(self.parent, 'Name:'))
            
        self.card_name_widget.add_element(TextField(self.parent, '', 20, self.change_name_action))
        self.card_name_widget.set_pos(1, 1)
        self.card_name_widget.focused_element_id = 1
        self.card_name_widget.set_focused(True)
            
        add_card_button = Button(self.parent, 'Add card', self.add_card_action)
        add_card_button.set_pos(2, 1)

        self.card_names_list = List(self.parent, self.cube.get_card_names(), self.parent.HEIGHT - 9, self.parent.WIDTH - 3, self.card_names_list_click_action)
        self.card_names_list.set_pos(5, 0)

        self.card_name_widget.prev = self.card_names_list
        self.card_name_widget.next = add_card_button

        add_card_button.prev = self.card_name_widget
        add_card_button.next = self.card_names_list

        self.card_names_list.prev = add_card_button
        self.card_names_list.next = self.card_name_widget

        self.add_element(self.card_name_widget)
        self.add_element(add_card_button)
        self.add_element(Separator(self.parent, 4, '#magenta-black Cards', self.border_color_pair))
        self.add_element(self.card_names_list)

        self.rename_main_tab('Cards')
        self.general_statistics_tab = MenuTab(self.parent, 'General statistics')

        self.init_general_statistics_tab()

        self.add_tab(self.general_statistics_tab)

        self.init_color_statistics_tabs()
    
    def init_general_statistics_tab(self):
        self.white_count_label = UIElement(self.parent, '')
        self.white_count_label.set_pos(1, 1)

        self.blue_count_label = UIElement(self.parent, '')
        self.blue_count_label.set_pos(2, 1)

        self.black_count_label = UIElement(self.parent, '')
        self.black_count_label.set_pos(3, 1)

        self.red_count_label = UIElement(self.parent, '')
        self.red_count_label.set_pos(4, 1)

        self.green_count_label = UIElement(self.parent, '')
        self.green_count_label.set_pos(5, 1)

        self.mc_count_label = UIElement(self.parent, '')
        self.mc_count_label.set_pos(6, 1)

        self.colorless_count_label = UIElement(self.parent, '')
        self.colorless_count_label.set_pos(7, 1)

        self.count_labels = {
            'White': self.white_count_label,
            'Blue': self.blue_count_label,
            'Black': self.black_count_label,
            'Red': self.red_count_label,
            'Green': self.green_count_label,
            'MC': self.mc_count_label,
            'Colorless': self.colorless_count_label
        }

        for key in self.count_labels:
            self.general_statistics_tab.add_element(self.count_labels[key])
        self.general_statistics_tab.add_element(Separator(self.parent, 9, color_pair=self.border_color_pair))

        label = UIElement(self.parent, 'label')
        label.set_pos(10, 1)
        label.set_focused(True)

        self.general_statistics_tab.add_element(label)

    def init_color_statistics_tabs(self):
        for color in COLORS:
            tab = ColorStatisticsTab(self.parent, color, self.cube)
            self.add_tab(tab)

    def update_color_count(self):
        counts = self.cube.get_color_counts()
        counts = [counts[color]['all'] for color in counts]
        required_length = 14
        for i in range(len(COLORS)):
            color = COLORS[i] 
            text = color + ': '
            cl = len(str(counts[i]))
            while len(text) + cl < required_length:
                text += ' '
            text += str(counts[i])
            self.count_labels[color].text = f'#{CCT_COLORS[color]} {text}'

    def add_card_action(self):
        name = self.card_name_widget.sub_elements[1].text
        cards = Card.from_name(name)
        result = drop_down_box([card.get_cct_name() for card in cards], 4, 5, 5, SINGLE_ELEMENT)
        if len(result) != 0:
            card = cards[result[0]]
            self.cube.add_card(card)
            self.change_name_action()
            self.update_color_count()

    def change_name_action(self):
        name = self.card_name_widget.sub_elements[1].text
        card_names = self.cube.get_card_names(name)
        self.card_names_list.set_options(card_names)

    def card_names_list_click_action(self, i: int, option: str):
        self.update_color_count()

    def load_cube(self, cube_name: str):
        self.cube = Cube.load(f'{SAVE_PATH}/{cube_name}.cube')

    def save_cube(self):
        self.cube.save(f'{SAVE_PATH}/{self.cube.name}.cube')

    def handle_key(self, key: int):
        super().handle_key(key)
        if key == 68: # D
            self.open_card_description_window()
        if key == 9 or key == 353: # TAB/SHIFT+TAB
            tab = self.tabs[self.selected_tab]
            if isinstance(tab, ColorStatisticsTab):
                tab.update()

    def open_card_description_window(self):
        if not self.card_names_list.focused:
            return
        height = self.parent.HEIGHT * 2 // 3
        width = self.parent.WIDTH * 2 // 3
        y = (self.parent.HEIGHT - height) // 2
        x = (self.parent.WIDTH - width) // 2
        window = curses.newwin(height, width, y, x)
        card_name = cct_real_str(self.card_names_list.options[self.card_names_list.choice])
        card = None
        for c in self.cube.cards:
            if c.name == card_name:
                card = c
                break
        if card == None:
            raise Exception(f'ERR: Card with name {card_name} not in cube.cards')
        card_description = card.get_cct_description().split('\n')
        draw_borders(window, 'magenta-black')
        put(window, 0, 1, f'Card description')
        put(window, 2, 2, card_description[0])
        put(window, 3, 2, card_description[1])
        for l in range(2, len(card_description) - 1):
            desc = str_smart_split(card_description[l], width - 4)
            for i in range(len(desc)):
                put(window, 3 + i + l, 2, desc[i])
        window.getch()

class CubeManagerWindow(Window):
    def __init__(self, window):
        super().__init__(window)
        self.state = 'main_menu'
        self.imported_text = ''

    def initUI(self):
        color_pair = '98-black'
        self.main_menu = Menu(self, f'Cube manager')
        self.main_menu.border_color_pair = color_pair

        cube_creation_menu = Menu(self, f'#{color_pair} Cube creation')
        cube_creation_menu.border_color_pair = color_pair

        def to_creation_menu_action():
            self.current_menu = cube_creation_menu
        to_creation_menu_button = Button(self, 'Create cube', to_creation_menu_action)
        to_creation_menu_button.set_focused(True)
        to_creation_menu_button.set_pos(0, 0)

        def load_cube_action():
            cube_names = get_saved_cube_names()
            if len(cube_names) == 0:
                message_box(self, '#red-black No cube files found!')
                return
            choice = drop_down_box(cube_names, 4, 4, 10, SINGLE_ELEMENT)
            if len(choice) != 0:
                cube_name = cube_names[choice[0]]
                mbchoice = message_box(self, f'Load #magenta-black {cube_name}#normal ?', ['Load', 'Delete', 'Cancel'])
                if mbchoice == 'Load':
                    self.load_cube(cube_name)
                    return
                if mbchoice == 'Delete':
                    if message_box(self, f'Are you sure you want to delete #magenta-black {cube_name}#normal ?', ['No', 'Yes'], border_color='red-black') == 'Yes':
                        os.remove(f'{SAVE_PATH}/{cube_name}.cube')
        load_cube_button = Button(self, 'Load cube', load_cube_action)
        load_cube_button.set_pos(1, 0)

        exit_button = Button(self, 'Exit', self.exit)
        exit_button.set_pos(2, 0)

        cube_name_widget = Widget(self)
        cube_name_widget.add_element(UIElement(self, 'Name: '))
        cube_name_widget.add_element(TextField(self, '', 20))
        cube_name_widget.focused_element_id = 1
        cube_name_widget.set_focused(True)
        cube_name_widget.set_pos(0, 0)

        def create_cube_action():
            self.draw_cube_creation_window()
            cube = Cube(cube_name_widget.sub_elements[1].text)
            if self.imported_text != '':
                cube.cards = Cube.import_from(self.imported_text).cards
            self.current_menu.draw()
            cube.save(f'{SAVE_PATH}/{cube.name}.cube')
            self.load_cube(cube.name)
        create_cube_button = Button(self, 'Create', create_cube_action)
        create_cube_button.set_pos(1, 0)

        def import_action():
            options = ['From clipboard', 'From file', 'Clear']
            copy_choice = drop_down_box(options, 3, 6, 1, SINGLE_ELEMENT)
            if len(copy_choice) == 0:
                return
            if copy_choice[0] == 0:
                # copy from clipboard
                self.imported_text = clipboard.paste()
                import_widget.sub_elements[1].text = '#yellow-black Imported from clipboard'
            if copy_choice[0] == 1:
                # copy form file
                file = choose_file(self, 'Import from file')
                self.imported_text = open(file, 'r').read()
                import_widget.sub_elements[1].text = f'#yellow-black Imported from file: #cyan-black {file}'
            if copy_choice[0] == 2:
                self.imported_text = ''
                import_widget.sub_elements[1].text = '<No file selected>'

        import_widget = Widget(self)
        import_widget.add_element(Button(self, 'Import', import_action))
        import_widget.add_element(UIElement(self, '<No file selected>'))
        import_widget.focused_element_id = 0
        import_widget.set_pos(2, 0)

        def back_to_main_menu_action():
            self.current_menu = self.main_menu
        back_to_main_menu_button = Button(self, 'Back', back_to_main_menu_action)
        back_to_main_menu_button.set_pos(4, 0)

        # main menu
        to_creation_menu_button.prev = exit_button
        to_creation_menu_button.next = load_cube_button

        load_cube_button.prev = to_creation_menu_button
        load_cube_button.next = exit_button

        exit_button.prev = load_cube_button
        exit_button.next = to_creation_menu_button

        # cube creation menu
        cube_name_widget.prev = back_to_main_menu_button
        cube_name_widget.next = create_cube_button

        create_cube_button.prev = cube_name_widget
        create_cube_button.next = import_widget

        import_widget.prev = create_cube_button
        import_widget.next = back_to_main_menu_button

        back_to_main_menu_button.prev = import_widget
        back_to_main_menu_button.next = cube_name_widget

        self.main_menu.add_element(to_creation_menu_button)
        self.main_menu.add_element(load_cube_button)
        self.main_menu.add_element(exit_button)

        cube_creation_menu.add_element(cube_name_widget)
        cube_creation_menu.add_element(create_cube_button)
        cube_creation_menu.add_element(import_widget)
        cube_creation_menu.add_element(Separator(self, 3, color_pair=color_pair))
        cube_creation_menu.add_element(back_to_main_menu_button)

        self.current_menu = self.main_menu

    def draw_window_with_message(self, message: str):
        height = 3
        width = len(message) + 2
        y = (self.HEIGHT - height) // 2
        x = (self.WIDTH - width) // 2
        window = curses.newwin(height, width, y, x)
        draw_borders(window, 'red-black')
        window.addstr(1, 1, message)
        window.refresh()

    def draw_cube_creation_window(self):
        self.draw_window_with_message('Cube creation...')

    def draw_cube_loading_window(self):
        self.draw_window_with_message('Loading cube...')

    def handle_key(self, key: int):
        if key == 27: # ESC
            if self.state == 'main_menu':
                self.exit()
            if self.state == 'managing_cube':
                if message_box(self, 'Return to main menu? Cube will be saved', ['No', 'Yes']) == 'Yes':
                    self.current_menu.save_cube()
                    self.current_menu = self.main_menu
                    self.state = 'main_menu'

    def load_cube(self, cube_name: str):
        self.state = 'managing_cube'
        self.draw_cube_loading_window()
        self.current_menu = CubeManagerMenu(self, 'Cube manager', cube_name)

def main(stdscr):
    curses.curs_set(0)
    window = CubeManagerWindow(stdscr)
    window.start()

curses.wrapper(main)