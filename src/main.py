import curses
import os
import clipboard
from mtgsdk import CARD_TYPES, CCT_COLORS, THEMES, Card, Cube, COLORS, STRONG_LABEL, MED_LABEL, WEAK_LABEL, PIE_WHEEL_TYPE_COLORS

from cursesui.Elements import BarChart, Button, Menu, MenuTab, PieChart, Separator, TextField, UIElement, VerticalLine, Widget, Window, List
from cursesui.Utility import SINGLE_ELEMENT, cct_len, cct_real_str, choose_file, draw_borders, draw_separator, drop_down_box, get_percentages, message_box, put, reverse_color_pair, str_smart_split

os.environ.setdefault('ESCDELAY', '25')

SAVE_PATH = 'cubes'

CARD_HEIGHT = 25
CARD_WIDTH = 40


def get_saved_cube_names():
    if not os.path.exists(SAVE_PATH):
        os.mkdir(SAVE_PATH)
        return []
    return [os.path.splitext(f)[0] for f in os.listdir(SAVE_PATH) if os.path.isfile(os.path.join(SAVE_PATH, f)) and os.path.splitext(f)[1] == '.cube']

def draw_card(card: Card, y: int, x: int):
    window = curses.newwin(CARD_HEIGHT, CARD_WIDTH, y, x)
    color_pair = CCT_COLORS[card.get_color()]
    # draw
    draw_borders(window, color_pair)
    window.addstr(1, 1, card.name)
    manacost = card.get_cct_mana_cost()
    put(window, 1, CARD_WIDTH - cct_len(manacost) - 1, manacost)
    draw_separator(window, 2, color_pair)
    card_type = card.get_cct_type()
    put(window, 3, 1, card_type)
    draw_separator(window, 4, color_pair)
    y = 5
    text = card.get_cct_text().split('\n')
    for line in text:
        for l in str_smart_split(line, CARD_WIDTH - 2):
            put(window, y, 1, l)
            y += 1
    window.getch()

def open_card_description_window(parent: Window, card: Card):
    if card == None:
        return
    draw_card(card, 10, 10)
    # height = parent.HEIGHT * 2 // 3
    # width = parent.WIDTH * 2 // 3
    # y = (parent.HEIGHT - height) // 2
    # x = (parent.WIDTH - width) // 2
    # window = curses.newwin(height, width, y, x)
    # card_description = card.get_cct_description().split('\n')
    # draw_borders(window, 'magenta-black')
    # put(window, 0, 1, f'Card description')
    # put(window, 1, width - cct_len(card_description[0]) - 1, card_description[0])
    # put(window, 2, 2, card_description[1])
    # put(window, 3, 2, card_description[2])
    # y = 4
    # for l in range(3, len(card_description)):
    #     desc = str_smart_split(card_description[l], width - 4)
    #     for i in range(len(desc)):
    #         y += 1
    #         put(window, y, 2, desc[i])
    # themes = card.get_themes()
    # y += 2
    # put(window, y, 1, '#pink-black Themes:')
    # for i in range(len(themes)):
    #     put(window, y + 1 + i, 2, themes[i])
    # window.getch()

class ColorStatisticsTab(MenuTab):
    def __init__(self, parent: Window, color: str, cube: Cube):
        super().__init__(parent, f'#{CCT_COLORS[color]} {color}')
        self.color = color
        self.cube = cube
        self.cards = []
        self.theme_colors = [f'{(i + 1) * 10}' for i in range(len(THEMES))]
        self.initUI()

    def initUI(self):
        self.pie_chart_values = [2, 1, 1, 4]

        self.total_count_label = UIElement(self.parent, '')
        self.total_count_label.set_pos(1, 1)

        pie_chart_height = 20
        pie_chart_width = self.parent.WIDTH - 120
        self.pie_chart = PieChart(self.parent, pie_chart_height, pie_chart_width, self.pie_chart_values, colors=['red', 'blue', 'yellow', 'green'], border_color_pair='green-black')
        self.pie_chart.set_pos(4, 1)
 
        self.type_labels = []
        for i in range(len(CARD_TYPES)):
            label = UIElement(self.parent, 'ERR')
            label.set_pos(4 + i, pie_chart_width + 4)
            self.type_labels += [label]

        self.theme_pie_chart = PieChart(self.parent, pie_chart_height, pie_chart_width, [], colors=self.theme_colors, border_color_pair='green-black')
        self.theme_pie_chart.set_pos(pie_chart_height + 6, 1)
    
        self.theme_percentages_labels = []
        for i in range(len(THEMES)):
            label = UIElement(self.parent, 'ERR')
            label.set_pos(i + pie_chart_height + 6, pie_chart_width + 4)
            self.theme_percentages_labels += [label]

        card_names_list_width = self.parent.WIDTH - pie_chart_width - 35

        self.card_names_list = List(self.parent, ['hi:)'], pie_chart_height, card_names_list_width, border_color_pair='green-black')
        self.card_names_list.options
        self.card_names_list.set_pos(4, pie_chart_width + 32)
        self.card_names_list.set_focused(True)

        self.cmc_bar_chart = BarChart(self.parent,  pie_chart_height, card_names_list_width, [1, 4, 7, 5, 2], 'green-black', 2, 'green-black')
        self.cmc_bar_chart.set_pos(pie_chart_height + 6, pie_chart_width + 32)

        self.add_element(self.total_count_label)
        self.add_element(Separator(self.parent, 3, color_pair='orange-black'))
        self.add_element(self.pie_chart)
        self.add_element(Separator(self.parent, 3 + pie_chart_height + 2, color_pair='orange-black'))
        for label in self.type_labels:
            self.add_element(label)
        self.add_element(self.theme_pie_chart)
        for label in self.theme_percentages_labels:
            self.add_element(label)
        self.add_element(Separator(self.parent, pie_chart_height * 2 + 7, color_pair='orange-black'))
        self.add_element(self.card_names_list)
        self.add_element(self.cmc_bar_chart)
        self.add_element(VerticalLine(self.parent, pie_chart_height * 2 + 5, 'orange-black', 3, pie_chart_width + 2))
        self.add_element(VerticalLine(self.parent, pie_chart_height * 2 + 5, 'orange-black', 3, pie_chart_width + 31))

    def update(self):
        # counts
        count = self.cube.get_color_counts()[self.color]
        all_count = count['all']
        self.total_count_label.text = f'Total: #{CCT_COLORS[self.color]} {all_count}'

        # pie chart values
        pie_chart_values = []
        pie_chart_colors = []
        for i in range(len(CARD_TYPES)):
            card_type = CARD_TYPES[i]
            c = count[card_type]
            self.type_labels[i].text = f'#{PIE_WHEEL_TYPE_COLORS[card_type]}-black {card_type}: {c}'
            if c != 0:
                pie_chart_values += [c]
                pie_chart_colors += [PIE_WHEEL_TYPE_COLORS[card_type]]
        self.pie_chart.set_values(pie_chart_values)
        self.pie_chart.set_colors(pie_chart_colors)

        # percentages
        values = []
        for i in range(len(THEMES)):
            values += [count[THEMES[i]]]
        self.theme_pie_chart.set_values(values)
        percentages = get_percentages(values)
        length = 25
        for i in range(len(THEMES)):
            ps = '%.2f' % percentages[i]
            placeholder = ' ' * (length - len(ps) - len(THEMES[i]) - 1)
            self.theme_percentages_labels[i].text = f'#{self.theme_colors[i]}-black {THEMES[i]}#normal :{placeholder}#yellow-black {ps}%'

        # card list
        self.cards = self.cube.get_color_split()[self.color]
        card_names = [self.cube.get_labeled_name(card) for card in self.cards]
        self.card_names_list.set_options(card_names)

        # cmc bar chart
        self.cmc_bar_chart.values = self.cube.get_cmcs()[self.color]

    def get_selected_card(self):
        if not self.card_names_list.focused:
            return None
        return self.cards[self.card_names_list.choice]

    def handle_key(self, key: int):
        super().handle_key(key)
        if key == 68: # D
            open_card_description_window(self.parent, self.get_selected_card())

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
        self.filtered_cards = []
        self.load_cube(cube_name)
        self.initUI()
        self.update_color_count()
        self.change_name_action()

    def initUI(self):
        self.card_name_widget = Widget(self.parent)
        self.card_name_widget.add_element(UIElement(self.parent, 'Name:'))
            
        self.card_name_widget.add_element(TextField(self.parent, '', 20, self.change_name_action))
        self.card_name_widget.set_pos(1, 1)
        self.card_name_widget.focused_element_id = 1
        self.card_name_widget.set_focused(True)
            
        add_card_button = Button(self.parent, 'Add card', self.add_card_action)
        add_card_button.set_pos(2, 1)

        card_names_list_height = self.parent.HEIGHT - 15
        self.card_names_list = List(self.parent, [], card_names_list_height, self.parent.WIDTH - 3, self.card_names_list_click_action)
        self.card_names_list.set_pos(5, 0)

        def WUBRG_sort_action():
            self.card_name_widget.sub_elements[1].reset_text()
            self.cube.wubrg_sort()
            self.filtered_cards = self.cube.cards
            card_names = [self.cube.get_labeled_name(card) for card in self.filtered_cards]
            self.card_names_list.set_options(card_names)
        self.wubrg_sort_button = Button(self.parent, '#cyan-black WUBRG #normal sort', WUBRG_sort_action)
        self.wubrg_sort_button.set_pos(5 + card_names_list_height + 2, 1)

        def label_sort_action():
            self.card_name_widget.sub_elements[1].reset_text()
            self.cube.label_sort()
            self.filtered_cards = self.cube.cards
            card_names = [self.cube.get_labeled_name(card) for card in self.filtered_cards]
            self.card_names_list.set_options(card_names)
        self.label_sort_button = Button(self.parent, '#green-black Label #normal sort', label_sort_action)
        self.label_sort_button.set_pos(5 + card_names_list_height + 3, 1)

        self.card_name_widget.prev = self.label_sort_button
        self.card_name_widget.next = add_card_button

        add_card_button.prev = self.card_name_widget
        add_card_button.next = self.card_names_list

        self.card_names_list.prev = add_card_button
        self.card_names_list.next = self.wubrg_sort_button

        self.wubrg_sort_button.prev = self.card_names_list
        self.wubrg_sort_button.next = self.label_sort_button

        self.label_sort_button.prev = self.wubrg_sort_button
        self.label_sort_button.next = self.card_name_widget

        self.add_element(self.card_name_widget)
        self.add_element(add_card_button)
        self.add_element(Separator(self.parent, 4, '#magenta-black Cards', self.border_color_pair))
        self.add_element(self.card_names_list)
        self.add_element(Separator(self.parent, 5 + card_names_list_height, color_pair=self.border_color_pair, text='#magenta-black Sorters'))
        self.add_element(self.wubrg_sort_button)
        self.add_element(self.label_sort_button)

        self.rename_main_tab('Cards')
        self.init_general_statistics_tab()
        self.init_color_statistics_tabs()
    
    def init_general_statistics_tab(self):
        self.general_statistics_tab = MenuTab(self.parent, 'General statistics')
        self.count_labels = []
        for i in range(len(COLORS)):
            label = UIElement(self.parent, '')
            label.set_pos(1 + i, 1)
            self.count_labels += [label]

        for i in range(len(self.count_labels)):
            self.general_statistics_tab.add_element(self.count_labels[i])
        self.general_statistics_tab.add_element(Separator(self.parent, 9, color_pair=self.border_color_pair))
        self.add_tab(self.general_statistics_tab)

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
            self.count_labels[i].text = f'#{CCT_COLORS[color]} {text}'

    def add_card_action(self):
        name = self.card_name_widget.sub_elements[1].text
        cards = Card.from_name(name)
        if len(cards) == 0:
            message_box(self.parent, f'No cards with {name} in it\'s name found!')
            return
        result = drop_down_box([card.get_cct_name() for card in cards], 8, 5, 5, SINGLE_ELEMENT)
        if len(result) != 0:
            card = cards[result[0]]
            self.cube.add_card(card)
            self.change_name_action()
            self.update_color_count()

    def change_name_action(self):
        name = self.card_name_widget.sub_elements[1].text
        self.filtered_cards = self.cube.get_cards(name)
        card_names = [self.cube.get_labeled_name(card) for card in self.filtered_cards]
        self.card_names_list.set_options(card_names)

    def card_names_list_click_action(self, choice: int, cursor: int, option: str):
        options = [STRONG_LABEL, MED_LABEL, WEAK_LABEL, 'Remove']
        dbb_y = cursor + 9
        dbb_x = cct_len(option) + 2
        result = drop_down_box(options, 4, dbb_y, dbb_x, SINGLE_ELEMENT)
        card = self.filtered_cards[choice]
        real_card_name = card.name
        if len(result) > 0:
            command = result[0]
            if options[command] in options[:-1]:
                multiverseid = card.multiverseid
                self.cube.set_card_info(multiverseid, 'label', options[command])
                new_option = card.get_cct_name()
                if multiverseid in self.cube.card_info:
                    new_option += '#normal : ' + self.cube.card_info[multiverseid]['label']
                self.card_names_list.set_option_at(choice, new_option)
            if options[command] == 'Remove' and message_box(self.parent, f'Are you sure you want to delete {card.get_cct_name()} #normal from cube?', ['No', 'Yes']) == 'Yes':
                self.cube.remove_card_by_name(real_card_name)
                self.change_name_action()
        self.update_color_count()

    def get_selected_card(self):
        if not self.card_names_list.focused:
            return None
        return self.filtered_cards[self.card_names_list.choice]

    def load_cube(self, cube_name: str):
        self.cube = Cube.load(f'{SAVE_PATH}/{cube_name}.cube')

    def save_cube(self):
        self.cube.save(f'{SAVE_PATH}/{self.cube.name}.cube')

    def handle_key(self, key: int):
        super().handle_key(key)
        if key == 68: # D
            open_card_description_window(self.parent, self.get_selected_card())
        if key == 9 or key == 353: # TAB/SHIFT+TAB
            tab = self.tabs[self.selected_tab]
            if isinstance(tab, ColorStatisticsTab):
                tab.update()

class CubeManagerWindow(Window):
    def __init__(self, window):
        super().__init__(window)
        self.state = 'main_menu'
        self.imported_text = ''
        # options = []
        # for i in range(250):
        #     options += [f'#{i}-black color n{i}']
        # drop_down_box(options, 10, 1, 1, SINGLE_ELEMENT)

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
# cards = Card.from_name_online('defile')