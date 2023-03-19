import os
import re
import requests
import json
# from kivy.core.spelling import Spelling
from kivy.logger import Logger

class Data():
    def __init__(self) -> None:
        ## initialize directory to story learning units
        #  load existing learning units
        self.work_dir = os.getcwd()
        self.units_path = os.path.join(self.work_dir, 'units_df.json')
        self.stored_dict_path = os.path.join(self.work_dir, 'saved_variables.json')

        ## initialize url parts
        self.base_url = 'https://signsuisse.sgb-fss.ch'
        self.lexikon_url = self.base_url + '/de/lexikon/g/'
        self.special_char_map = {ord('ä'):'ae', ord('ü'):'ue', ord('ö'):'oe', ord('ß'):'ss', ord(' '):'-'}

        ## initialize all the information for a word
        self.word = ''
        self.videos = ['']
        self.examples = ['']
        self.example_phrases = ['']
        self.categories = ['']
        self.categorie = 0

        ## initialize last selected item in units dropdown
        if os.path.exists(self.stored_dict_path):
            self.saved_variables = json.load(open(self.stored_dict_path, 'r'))
        else:
            self.saved_variables = {
                'last_unit': 'Neue Lerneinheit'
            }

        ## load dataframe for learning units
        self.units_df_indices = ['Lerneinheit', 'Wort']
        self.units_df_columns = ['Video', 'Beispielvideo', 'Beispielsatz', 'Fortschritt']
        if os.path.exists(self.units_path):
            self.units_df = json.load(open(self.units_path, 'r'))
            for unit in self.units:
                self.unit = unit
                for word in self.words:
                    self.units_df[unit][word][self.units_df_columns.index('Fortschritt')] = int(self.units_df[unit][word][self.units_df_columns.index('Fortschritt')])
        else:
            first_units = {
                'Familie': ['schwester-1', 'bruder', 'familie', 'mutter', 'vater', 'gemeinsam', 'haus', 'hund', 'katze'],
            }
            self.units_df = {}
            for unit, words in first_units.items():
                self.unit = unit
                self.units_df[unit] = {}
                for word in words:
                    self.load_word(word)
                    self.add_to_learning_unit()

    ## load all data for a word
    ## first reinitialize the lists to clean old data
    ## get data from source url or device storage
    def load_word(self, word, url_source=True):
        self.word = word.split('-')[0]
        self.videos = []
        self.examples = []
        self.example_phrases = []
        self.categories = []
        self.categorie = 0

        if url_source:
            for i in range(100):
                url = f'{self.lexikon_url}{word.translate(self.special_char_map)}'
                if i > 0: url += f'-{i}'
                url += '/'
                Logger.info(f'requests: {url}')
                r = requests.get(url)
                title_pattern = re.compile('<title>(.*?)[( . )(</title>)]')
                title = title_pattern.search(r.text).group(1).lower()
                if title == self.word.lower():
                    kategorie_pattern = re.compile('<strong>Kategorien:</strong> <span> (.*?) </span>')
                    kategorie = kategorie_pattern.search(r.text).group(1)
                    self.categories.append(kategorie)
                    video_url_pattern = re.compile('<video id="video-main" .*? <source src="(.*?)"')
                    video_url = video_url_pattern.search(r.text).group(1)
                    video_url = self.base_url + video_url
                    self.videos.append(video_url)
                    beispiel_url_pattern = re.compile('<video id="video-example.*? <source src="(.*?)"')
                    beispiel_url = beispiel_url_pattern.search(r.text).group(1)
                    beispiel_url = self.base_url + beispiel_url
                    self.examples.append(beispiel_url)
                    beispiel_satz_pattern = re.compile('<h2>Beispiel</h2> <p>(.*?)</p>')
                    beispiel_satz = beispiel_satz_pattern.search(r.text).group(1)
                    self.example_phrases.append(beispiel_satz)
                else:
                    if i == 0:
                        self.videos.append('')
                        self.examples.append('')
                        self.example_phrases.append('')
                        self.categories.append('keine Gebärden vorhanden')
                    break
            return self.categories
        elif self.words_df is not None:
            self.videos.append(self.words_df[self.word][self.units_df_columns.index('Video')])
            self.examples.append(self.words_df[self.word][self.units_df_columns.index('Beispielvideo')])
            self.example_phrases.append(self.words_df[self.word][self.units_df_columns.index('Beispielsatz')])
            return
        else:
            Logger.error('Loading: No learning unit selected before accessing storage')
            return
    
    def add_to_learning_unit(self):
        self.word = self.correct_word()
        self.units_df[self.unit][self.word] = [self.video, self.example, self.example_phrase, 0]
        self.save_units()
        return

    def rename_learning_unit(self, unit, new_name):
        self.units_df[new_name] = self.units_df.pop(unit)
        self.save_units()
        return

    def remove_learning_unit(self, word, level):
        if level == 0:
            self.units_df.pop(word)
        elif level == 1:
            self.units_df[self.unit].pop(word)
        self.save_units()
        return
    
    def save_progress(self, percent):
        old_percent = self.get_progress(self.unit, number=True)
        if old_percent < percent:
            for word in self.words:
                self.units_df[self.unit][word][self.units_df_columns.index('Fortschritt')] = percent
            self.save_units()
        return
    
    def get_progress(self, unit, number = False):
        self.unit = unit
        percent = 0
        nr_words = len(self.words)
        if nr_words > 0:
            for value in self.words_df.values():
                percent += value[self.units_df_columns.index('Fortschritt')]
            percent /= nr_words
            if not number: return f'Bester Versuch: {int(percent)}% richtig'
        if not number:
            return ' '
        return int(percent)
    
    def save_units(self):
        self.units_df = dict(sorted(self.units_df.items()))
        for unit in self.units:
            self.units_df[unit] = dict(sorted(self.units_df[unit].items()))
        json.dump(self.units_df, open(self.units_path, 'w'), indent=4)
        return
    
    def correct_word(self):
        if requests.get('https://www.duden.de/rechtschreibung/' + self.word).status_code > 200:
            return self.word[0].upper()+self.word[1:]
        else:
            return self.word

    @property
    def units(self):
        return list(self.units_df.keys())

    @property
    def video(self):
        return self.videos[self.categorie]

    @property
    def example(self):
        return self.examples[self.categorie]

    @property
    def example_phrase(self):
        return self.example_phrases[self.categorie]

    def _get_saved_variable(variable):
        def func(self):
            return self.saved_variables[variable]
        return func

    def _set_saved_variable(variable):
        def func(self, value):
            self.saved_variables[variable] = value
            json.dump(self.saved_variables, open(self.stored_dict_path, 'w'), indent=4)
            return
        return func

    unit = property(
        fget=_get_saved_variable('last_unit'),
        fset=_set_saved_variable('last_unit')
    )

    @property
    def words(self):
        return list(self.units_df[self.unit].keys())

    @property
    def words_df(self):
        try:
            return self.units_df[self.unit]
        except:
            return None
    
    @property
    def units_array(self):
        array = []
        def get_row(old_row, dict_or_list):
            if type(dict_or_list) is list:
                array.append(old_row + dict_or_list)
            elif type(dict_or_list) is dict:
                for key, value in dict_or_list.items():
                    get_row(old_row + [key], value)
            else:
                array.append(old_row + [dict_or_list])
        get_row([], self.units_df)
        return array