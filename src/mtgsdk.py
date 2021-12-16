import requests
import json
import os.path

NAME_URL = 'https://api.magicthegathering.io/v1/cards'
ALL_CARDS_PATH = 'assets/all_cards.json'

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

    def get_cct_description(self):
        result = ''
        result += self.get_cct_name() + '\n'
        result += '#orange-black ' + self.type + '#normal \n'
        result += self.text + '\n'
        return result

class CreatureCard(Card):
    def __init__(self):
        super().__init__()
        self.power = ''
        self.toughness = ''

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
        result.wubrg_sort()
        return result

    def __init__(self, name: str):
        self.name = name
        self.cards = []

    def add_card(self, card: Card):
        if not card.name in [c.name for c in self.cards]:
            self.cards += [card]
            self.wubrg_sort()

    def save(self, path: str):
        ids = [card.multiverseid for card in self.cards]
        data = dict()
        data['card_ids'] = ids
        data['name'] = self.name
        text = json.dumps(data, indent=4, sort_keys=True)
        open(path, 'w').write(text)

    def get_card_names(self, query=''):
        result = []
        for card in self.cards:
            if card.name_matches(query):
                result += [card.get_cct_name()]
        return result

    def wubrg_sort(self):
        cards = dict()
        for key in COLORS:
            cards[key] = []
        for card in self.cards:
            cards[card.get_color()] += [card]
        self.cards = []
        for key in cards:
            self.cards += cards[key]

    def get_color_counts(self):
        counts = dict()
        for color in COLORS:
            counts[color] = {
                'all': 0
            }
            for type in CARD_TYPES:
                counts[color][type] = 0
        for card in self.cards:
            card_color = card.get_color()
            counts[card_color]['all'] += 1
            for card_type in card.types:
                counts[card_color][card_type] += 1
        return counts

    def get_cmcs(self):
        result = dict()
        for color in COLORS:
            max_cmc = max([card.cmc for card in self.cards if card.get_color() == color])
            result[color] = [0 for i in range(int(max_cmc) + 1)]
        for card in self.cards:
            card_color = card.get_color()
            result[card_color][int(card.cmc)] += 1
        return result
        