from os import replace
import requests
import json
import os.path

NAME_URL = 'https://api.magicthegathering.io/v1/cards'
ALL_CARDS_PATH = 'assets/all_cards.json'

STRONG_LABEL = '#green-black Strong'
MED_LABEL = '#yellow-black Med'
WEAK_LABEL = '#red-black Weak'
LABELS = [STRONG_LABEL, MED_LABEL, WEAK_LABEL]

COLORS = ['White', 'Blue', 'Black', 'Red', 'Green', 'MC', 'Colorless']
CARD_TYPES = ['Creature', 'Sorcery', 'Instant', 'Enchantment', 'Artifact', 'Planeswalker', 'Land']

CCT_COLORS = {
    'White': 'white-black',
    'Blue': 'cyan-black',
    'Black': '239-black',
    'Red': 'red-black',
    'Green': 'green-black',
    'MC': 'yellow-black',
    'Colorless': 'gray-black'
}

THEME_WORDS = {
    '+1/+1 counters': [ '+1/+1 counter', 'proliferate', 'renown' ],
    'Removal': ['destroy target', 'enchanted creature can\'t attack or block', 'enchanted creature can\'t attack, block', 'enchanted creature loses all abilities', 'damage to target attacking', 'damage to target creature', 'damage to any target', 'target creature gets -'],
    'Tokens': [ 'token', 'convoke' ],
    'ETB': [ 'when <cardname> enters the battlefield', 'exile target creature you control' ],
    'Lifegain': [ 'lifelink', 'you gain' ],
    'Color matters': [ 'white creature', 'blue creature', 'black creature', 'red creature', 'green creature' ],
    'Flying': [ 'flying' ],
    'Death matters': [ 'dies', 'leaves the battlefield', 'your graveyard', 'mill ', 'sacrifice a creature' ],
    'Card drawing': [ 'draw' ],
    'Direct damage': [ 'damage to any target' ],
    'Energy': [ '{E}' ],
    'Treasure': [ 'Treasure token' ],
    'Evasion': [ 'can\'t be blocked' ],
    'Spells matter': [ 'instant or sorcery', 'noncreature', 'instant and sorcery' ],
    'Mill': [ 'mills' ],
    'Hand attack': [ 'discards' ]
}

THEMES = list(THEME_WORDS.keys())

MANA_SYMBOL_COLORS = {
    '{W}': '#white-black W',
    '{U}': '#cyan-black U',
    '{B}': '#239-black B',
    '{R}': '#red-black R',
    '{G}': '#green-black G',
    '{C}': '#gray-black C',
    '{T}': '#orange-black T',
    '{E}': '#yellow-black E'
}

KEYWORD_COLORS = {
    'Flying': '#cyan-black Flying#normal ',
    'flying': '#cyan-black flying#normal ',
    'Destroy': '#red-black Destroy#normal ',
    'draw a card': '#cyan-black DRAW A CARD#normal ',
    'Draw a card': '#cyan-black DRAW A CARD#normal ',
    'Lifelink': '#169-black Lifelink#normal ',
    'lifelink': '#169-black lifelink#normal ',
    'Counter': '#21-black Counter#normal ',
    'Threshold': '#239-black Threshold#normal ',
    'Treasure': '#yellow-black Treasure#normal ',
    'Deathtouch': '#green-black Deathtouch#normal ',
    'deathtouch': '#green-black deathtouch#normal ',
    'Menace': '#magenta-black Menace#normal ',
    'menace': '#magenta-black menace#normal ',
    'Flash': '#orange-black Flash#normal ',
    'flash': '#orange-black flash#normal ',
    'Exile': '#magenta-black Exile#normal ',
    'exile': '#magenta-black exile#normal ',
    'Vigilance': '#orange-black Vigilance#normal ',
    'vigilance': '#orange-black vigilance#normal ',
    'Convoke': '#green-black Convoke#normal ',
    'Double strike': '#red-black Double strike#normal ',
    'First strike': '#yellow-black First strike#normal ',
    'first strike': '#yellow-black first strike#normal ',
    'Scry {}': '#cyan-black Scry {}#normal ',
    'deals {} damage': '#red-black deals {} damage#normal ',
    'gain {} life': '#168-black gain {} life#normal ',
    'loses {} life': '#239-black loses {} life#normal ',
}

PIE_WHEEL_TYPE_COLORS = {
    'Creature': 'red',
    'Sorcery': 'pink',
    'Instant': 'cyan',
    'Enchantment': 'orange',
    'Artifact': 'gray',
    'Land': 'white',
    'Planeswalker': 'magenta'
}

def replace_mana_symbols(text: str):
    result = str(text)
    for mana_symbol in MANA_SYMBOL_COLORS:
        result = result.replace(mana_symbol, f'{MANA_SYMBOL_COLORS[mana_symbol]}#normal ')
    for i in range(1, 20):
        result = result.replace(f'{{{i}}}', f'#gray-black {i}#normal ')
    return result

def colorize_keywords(text: str):
    result = str(text)
    for keyword in KEYWORD_COLORS:
        if '{}' in keyword:
            replacement = KEYWORD_COLORS[keyword]
            result = result.replace(keyword.format('X'), replacement.format('X'))
            for i in range(1, 27):
                result = result.replace(keyword.format(i), replacement.format(i))
        else:
            result = result.replace(keyword, KEYWORD_COLORS[keyword])
    # gs = 'gain {} life'
    # result.replace(gs.format('X'), gs.format('#168-black {}#normal '.format(gs.format('X'))))
    # for i in range(1, 27):
    #     result = result.replace(gs.format(i), gs.format(f'#168-black {gs.format(i)}#normal '))
    # ls = 'loses {} life'
    # result.replace(ls.format('X'), ls.format('#239-black {}#normal '.format(ls.format('X'))))
    # for i in range(1, 27):
    #     result = result.replace(ls.format(i), ls.format(f'#239-black {ls.format(i)}#normal '))
    return result

class Card:
    def get_saved_data():
        if not os.path.exists(ALL_CARDS_PATH):
            open(ALL_CARDS_PATH, 'w').write('{}')
            return dict()
        text = open(ALL_CARDS_PATH, 'r').read()
        if len(text) == 0:
            open(ALL_CARDS_PATH, 'w').write('{}')
            return dict()
        items = json.loads(text)
        result = dict()
        for key in items:
            result[key] = Card.from_json(items[key])
        return result

    def card_saved(name):
        return False

    def save_card(card: 'Card'):
        cards = dict()
        if os.path.exists(ALL_CARDS_PATH):
            cards = json.loads(open(ALL_CARDS_PATH, 'r').read())
        cards[card.multiverseid] = card.to_json()
        text = json.dumps(cards, indent=4, sort_keys=True)
        open(ALL_CARDS_PATH, 'w').write(text)

    def from_id(multiverseid: str):
        data = Card.get_saved_data()
        if not multiverseid in data:
            # fetch card
            request = requests.get(url=NAME_URL + f'/{multiverseid}')
            data = request.json()
            card = Card.from_json(data['card'])
            Card.save_card(card)
            return card
        return Card.get_saved_data()[multiverseid]

    def from_name_in_saved(name: str):
        data = Card.get_saved_data()
        result = []
        for key in data:
            card = data[key]
            if card.name_matches(name):
                result += [card]
        return result

    def from_name(name: str):
        in_saved = Card.from_name_in_saved(name)
        if len(in_saved) != 0:
            return in_saved
        return Card.from_name_online(name)

    def from_name_online(name: str):
        PARAMS = {'name': name}
        request = requests.get(url=NAME_URL, params=PARAMS)
        data = request.json()
        result = []
        for item in data['cards']:
            if not 'multiverseid' in item or item['multiverseid'] == '':
                continue
            if not item['name'] in [card.name for card in result]:
                result += [Card.from_json(item)]
        for card in result:
            Card.save_card(card)
        return result

    def from_json(js: dict):
        result = Card()
        if 'Creature' in js['types']:
            result = CreatureCard()
        for key in list(result.__dict__.keys()):
            if key in js:
                result.__dict__[key] = js[key]
        # result.__dict__ = js
        return result

    def __init__(self):
        self.name = ''
        self.text = ''
        self.cmc = 0
        self.colorIdentity = []
        self.colors = []
        self.manaCost = ''
        self.multiverseid = ''
        self.type = ''
        self.types = []
        self.supertypes = []
        self.subtypes = []

    def to_json(self):
        return self.__dict__

    def name_matches(self, name: str):
        return name.lower() in self.name.lower()

    def get_color(self):
        if len(self.colors) == 0:
            return 'Colorless'
        if len(self.colors) > 1:
            return 'MC'
        return self.colors[0]

    def get_cct_name(self):
        return f'#{CCT_COLORS[self.get_color()]} {self.name}'

    def get_cct_mana_cost(self):
        return replace_mana_symbols(self.manaCost)

    def get_cct_type(self):
        return replace_mana_symbols(self.type)

    def get_cct_text(self):
        return colorize_keywords(replace_mana_symbols(self.text))

    def get_cct_description(self):
        result = ''
        result += self.manaCost + '\n'
        result += self.get_cct_name() + '\n'
        result += '#orange-black ' + self.type + '#normal \n'
        result += self.text
        return result

    def get_themes(self):
        result = set()
        for theme in THEME_WORDS:
            for theme_words in THEME_WORDS[theme]:
                if theme_words.replace('<cardname>', self.name).lower() in self.text.lower():
                    result.add(theme)
        return list(result)

class CreatureCard(Card):
    def __init__(self):
        super().__init__()
        self.power = ''
        self.toughness = ''

    def get_cct_description(self):
        result = super().get_cct_description()
        result += f'\n\n({self.power}/{self.toughness})'
        return result

class Cube:
    def import_from(text: str):
        text = text.replace('\r', '')
        lines = text.split('\n')
        result = Cube('')
        for card_name in lines:
            cards = Card.from_name(card_name)
            if len(cards) == 0:
                cards = Card.from_name_online(card_name)
            if len(cards) == 0:
                raise Exception(f'ERR: card with name {card_name} not found')
            for card in cards:
                if card.name == card_name:
                    result.add_card(card)
                    break
        return result

    def load(path: str):
        result = Cube('')
        data = json.loads(open(path, 'r').read())
        result.name = data['name']
        for card_id in data['card_ids']:
            if card_id != '':
                result.cards += [Card.from_id(card_id)]
        result.card_info = data['card_info']
        result.wubrg_sort()
        return result

    def __init__(self, name: str):
        self.name = name
        self.cards = []
        self.card_info = dict()

    def set_card_info(self, card_multiverseid: str, key: str, value):
        if not card_multiverseid in self.card_info:
            self.card_info[card_multiverseid] = dict()
        self.card_info[card_multiverseid][key] = value

    def add_card(self, card: Card):
        if not card.name in [c.name for c in self.cards]:
            self.cards += [card]
            self.wubrg_sort()

    def remove_card_by_name(self, card_name: str):
        for card in self.cards:
            if card.name == card_name:
                self.card_info.pop(card.multiverseid, None)
                self.cards.remove(card)
                return

    def save(self, path: str):
        ids = [card.multiverseid for card in self.cards]
        data = dict()
        data['card_ids'] = ids
        data['name'] = self.name
        data['card_info'] = self.card_info
        text = json.dumps(data, indent=4, sort_keys=True)
        open(path, 'w').write(text)

    def get_card_names(self, query=''):
        result = []
        for card in self.cards:
            if card.name_matches(query):
                line = card.get_cct_name()
                if card.multiverseid in self.card_info:
                    line += '#normal : ' + self.card_info[card.multiverseid]['label']
                result += [line]
        return result

    def get_cards(self, name_query=''):
        result = []
        for card in self.cards:
            if card.name_matches(name_query):
                result += [card]
        return result

    def get_labeled_name(self, card: Card):
        result = card.get_cct_name()
        if card.multiverseid in self.card_info:
            result += '#normal : ' + self.card_info[card.multiverseid]['label']
        return result

    def wubrg_sort(self):
        cards = self.get_color_split()
        self.cards = []
        for color in cards:
            self.cards += cards[color]

    def label_sort(self):
        cards = {'no_label': []}
        for label in LABELS[::-1]:
            cards[label] = []
        for card in self.cards:
            if not card.multiverseid in self.card_info:
                cards['no_label'] += [card]
                continue
            cards[self.card_info[card.multiverseid]['label']] += [card]
        self.cards = []
        for label in cards:
            self.cards += cards[label]

    def get_color_split(self):
        result = dict()
        for color in COLORS:
            result[color] = []
        for card in self.cards:
            result[card.get_color()] += [card]
        return result

    def get_color_counts(self):
        counts = dict()
        for color in COLORS:
            counts[color] = {
                'all': 0
            }
            for type in CARD_TYPES:
                counts[color][type] = 0
            for theme in THEMES:
                counts[color][theme] = 0
        for card in self.cards:
            card_color = card.get_color()
            counts[card_color]['all'] += 1
            for card_type in card.types:
                counts[card_color][card_type] += 1
            for card_theme in card.get_themes():
                counts[card_color][card_theme] += 1
        return counts

    def get_cmcs(self):
        result = dict()
        for color in COLORS:
            cmcs = [card.cmc for card in self.cards if card.get_color() == color]
            if len(cmcs) == 0:
                result[color] = []
                continue
            max_cmc = max(cmcs)
            result[color] = [0 for i in range(int(max_cmc) + 1)]
        for card in self.cards:
            card_color = card.get_color()
            result[card_color][int(card.cmc)] += 1
        return result
        
    def get_card_by_name(self, card_name):
        for card in self.cards:
            if card.name == card_name:
                return card
        return None