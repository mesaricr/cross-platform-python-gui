# this is needed for supporting Windows 10 with OpenGL < v2.0
# Example: VirtualBox w/ OpenGL v1.1
import platform, os
if platform.system() == 'Windows':
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import kivy
kivy.require('2.1.0') # replace with your current kivy version !

from kivy.app import App
from kivy.uix.label import Label

from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.uix.button import Button, ButtonBehavior
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.button import MDRoundFlatButton, MDIconButton
from kivymd.uix.list import IRightBodyTouch, OneLineRightIconListItem, MDList, TwoLineListItem
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard, MDCardSwipe
from kivy.metrics import dp
from kivy.logger import Logger
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty
from kivy.core.window import Window
from kivy.base import EventLoop
from data import Data
from random import shuffle


Window.softinput_mode = 'below_target'
app_data = Data()

class TopRibbon(BoxLayout):
    pass

class PlayButton(ButtonBehavior, Label):
    pass

class ListItemWithCheckbox(OneLineRightIconListItem):
    pass

class RightCheckbox(IRightBodyTouch, MDCheckbox):
    pass

class SwipeToDeleteItem(MDCardSwipe):
    text = StringProperty()
    on_release = ObjectProperty()
    rename = BooleanProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.rename:
            self.ids.back.add_widget(MDIconButton(icon='lead-pencil', pos_hint = { 'center_y': 0.5 }, on_release = self.show_textfield))

    def show_textfield(self, instance):
        self.parent.renaming = True
        setattr(self.parent, 'active_item', self)
        self.ids.front.clear_widgets()
        setattr(self.ids, 'rename', MDTextField(text = self.text, on_text_validate= self.rename_unit, mode = 'round', pos_hint={ 'center_y': 0.5 }))
        self.ids.front.add_widget(self.ids.rename)

    def rename_unit(self, instance):
        global app_data
        app_data.rename_learning_unit(self.ids.content.text, self.ids.rename.text)
        self.parent.root.update()

    def remove_unit(self, instance):
        global app_data
        level = 0
        if self.parent == self.parent.root.ids.words_list:
            level = 1
        app_data.remove_learning_unit(instance.text, level)
        self.parent.remove_widget(instance)
    
    def on_release(self, instance):
        if self.open_progress < 0.2:
            if self.parent == self.parent.root.ids.units_list:
                self.parent.root.open_unit(instance)
            elif self.parent == self.parent.root.ids.words_list:
                self.parent.root.open_word(instance.text)
        else:
            pass

class Pages():
    def __init__(self) -> None:
        self.pages = {}
        self.counter = 0

    def add(self, screen, name, text, icon):
        self.pages[name] = MDBottomNavigationItem(name=name, text=text, icon=icon)
        self.pages[name].add_widget(screen)
        return
    
    def get(self, name):
        return self.pages[name]
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.counter < len(self.pages):
            self.counter += 1
            return list(self.pages.values())[self.counter - 1]
        raise StopIteration

class VideoTab(Button):
    def release(self, tab):
        tab.background_color = (1, 0.21875, 0.109375, 1)
        return

class SearchPage(BoxLayout):
    def on_focus(self, instance):
        if instance.focus:
            instance.text = ''
        else:
            pass

    def play_video(self, tab):
        global app_data
        app_data.categorie = tab.nr
        for child in tab.parent.children:
            child.background_color = (0.0234375, 0.73046875, 0.921875, 1)
        tab.background_color = (105/256 ,64/256 ,50/256, 1)
        self.ids.video.source = app_data.video
        self.ids.video.state = 'play'
        self.ids.video.options = { 'eos': 'stop'}
        self.ids.beispiel.opacity = 1
        self.ids.example_label.text = app_data.example_phrase
        self.load_dropdown()
        return
    
    def play_example(self):
        global app_data
        Logger.info('Example: Trying to play video')
        self.ids.video.source = app_data.example
        self.ids.video.state = 'play'
        self.ids.video.options = { 'eos': 'stop'}
        return

    def search_signwise(self, word):
        global app_data
        self.ids.kategories.clear_widgets()
        self.ids.gebaerde_label.text = word.upper()
        for i, kategorie in enumerate(app_data.load_word(word)):
            tab = VideoTab(text=kategorie, color=(0,0,0,1))
            setattr(tab, 'nr', i)
            self.ids.kategories.add_widget(tab)
            if i == 0:
                self.play_video(tab)
                tab.release(tab)
        return
    
    def load_dropdown(self):
        global app_data
        units = app_data.units
        items = [{
            "text": 'Neue Lerneinheit',
            "viewclass": "OneLineListItem",
            "on_release": lambda x = 'Neue Lerneinheit': self.menu_callback(x),
        }]
        items += [{
            "text": unit,
            "viewclass": "OneLineListItem",
            "on_release": lambda x = unit: self.menu_callback(x),
        } for unit in units]
        self.unit_menu = MDDropdownMenu(
            caller=self.ids.dropdown,
            items =items,
            width_mult=4
        )
        self.ids.dropdown.disabled = False
        self.ids.save_in_unit.opacity = 1
    
    def menu_callback(self, unit):
        global app_data
        app_data.unit = unit
        self.ids.dropdown.text = unit
        self.ids.dropdown.children[0].texture_update()
        self.ids.dropdown.padding = [(self.ids.searching_word.width-self.ids.dropdown.children[0].width)/2, 0]
        self.unit_menu.dismiss()
    
    def add_to_learning_unit(self):
        global app_data
        if app_data.unit != 'Neue Lerneinheit':
            app_data.word = self.ids.searching_word.text
            app_data.add_to_learning_unit()
        else:
            self.create_new_learning_unit()
    
    def create_new_learning_unit(self):
        global app_data
        self.card = MDCard(
            size_hint = (0.9, None),
            pos_hint = { 'center_x': 0.5, 'center_y': 0.5 },
            height = dp(120),
            style = 'elevated',
            shadow_softness=2,
            shadow_offset=(0, 1),
        )
        layout = BoxLayout(orientation = 'vertical', size_hint = (1, 0.6), pos_hint = { 'center_x': 0.5, 'center_y': 0.5 })
        layout.add_widget(MDLabel(text = 'Neue Lerneinheit', size_hint = (0.9, 1), pos_hint = { 'center_x': 0.5 }, font_size=dp(64), bold = True, valign = 'center', halign = 'center'))
        self.new_unit = MDTextField(
            size_hint = (0.9, 1),
            pos_hint = { 'center_y': 0.5, 'center_x': 0.5 },
            hint_text = 'Name der Lerneinheit eingeben',
            mode = 'round',
        )
        self.new_unit.on_text_validate = self.add_to_new_learning_unit
        layout.add_widget(self.new_unit)
        self.card.add_widget(layout)
        self.parent.add_widget(self.card)
    
    def add_to_new_learning_unit(self):
        global app_data
        app_data.units_df[self.new_unit.text] = {}
        app_data.unit = self.new_unit.text
        self.ids.dropdown.text = self.new_unit.text
        self.ids.dropdown.children[0].texture_update()
        self.ids.dropdown.padding = [(self.ids.searching_word.width-self.ids.dropdown.children[0].width)/2, 0]
        self.load_dropdown()
        app_data.word = self.ids.searching_word.text
        self.parent.remove_widget(self.card)
        app_data.add_to_learning_unit()

class CollectionPage(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.hook_keyboard)

    def hook_keyboard(self, window, key, *largs):
        if key == 27:
            return self.back()

    def back(self):
        self.ids.manager.transition.direction = 'right'
        if self.ids.manager.current == 'units screen':
            if self.ids.units_list.renaming:
                self.ids.units_list.renaming = False
                self.ids.units_list.active_item.ids.front.remove_widget(self.ids.units_list.active_item.ids.rename)
                self.ids.units_list.active_item.ids.front.add_widget(self.ids.units_list.active_item.ids.content)
                return True
            else:
                return False
        elif self.ids.manager.current == 'words screen':
            self.ids.manager.current = 'units screen'
        else: self.ids.manager.current = 'words screen'
        return True

    def update(self):
        global app_data
        self.ids.units_list.clear_widgets()
        for unit in app_data.units:
            item = SwipeToDeleteItem(text=unit, on_release=self.open_unit)
            item.add_widget(RightCheckbox(opacity=0))
            self.ids.units_list.add_widget(item)
    
    def open_unit(self, unit):
        global app_data
        self.ids.words_list.clear_widgets()
        app_data.unit = unit.text
        for word in app_data.words:
            item = SwipeToDeleteItem(text=word, on_release=lambda s, x=word: self.open_word(x.lower()), rename = False)
            item.add_widget(RightCheckbox(opacity=0))
            self.ids.words_list.add_widget(item)
        self.ids.manager.transition.direction = 'left'
        self.ids.manager.current = 'words screen'
    
    def open_word(self, word):
        global app_data
        app_data.load_word(word, url_source=False)
        self.ids.gebaerde_label.text = word.upper()
        self.ids.example_label.text = app_data.example_phrase
        self.ids.video.source = app_data.video
        self.ids.video.state = 'play'
        self.ids.video.options = { 'eos': 'stop'}
        self.ids.manager.transition.direction = 'left'
        self.ids.manager.current = 'word video'

    def open_last_word(self):
        words = app_data.words
        for w, word in enumerate(words):
            if word.lower() == self.ids.gebaerde_label.text.lower():
                if w > 0:
                    self.open_word(words[w-1])
                else: self.open_word(words[-1])
                break

    def open_next_word(self):
        words = app_data.words
        for w, word in enumerate(words):
            if word.lower() == self.ids.gebaerde_label.text.lower():
                if w < len(words)-1:
                    self.open_word(words[w+1])
                else: self.open_word(words[0])
                break
    
    def play_example(self):
        global app_data
        self.ids.video.source = app_data.example
        self.ids.video.state = 'play'
        self.ids.video.options = { 'eos': 'stop'}
        return

        
class QuizPage(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.hook_keyboard)

    def hook_keyboard(self, window, key, *largs):
        if key == 27:
            return self.back()
    
    def back(self):
        self.ids.manager.transition.direction = 'right'
        if self.ids.manager.current == 'units screen':
            return False
        else:
            self.ids.back_button.disabled = True
            self.card = MDCard(
                size_hint = (0.9, None),
                pos_hint = { 'center_x': 0.5, 'center_y': 0.5 },
                height = dp(120),
                style = 'elevated',
                shadow_softness=2,
                shadow_offset=(0, 1),
            )
            layout = BoxLayout(orientation = 'vertical', size_hint = (1, 0.6), pos_hint = { 'center_x': 0.5, 'center_y': 0.5 }, spacing = dp(30))
            layout.add_widget(MDLabel(text = 'Fortschritt wird gelöscht. Trotzdem verlassen?',
                size_hint = (0.9, 1), pos_hint = { 'center_x': 0.5 },
                font_size=dp(64), bold = True, valign = 'center', halign = 'center'))
            button_box = MDBoxLayout(orientation = 'horizontal', adaptive_width = True, pos_hint = { 'center_x': 0.5 })
            button_box.spacing = 0.8*button_box.width
            button_box.add_widget(MDIconButton(icon = 'check-bold', theme_icon_color = "Custom", icon_color = (0,1,0,1), on_press = self.go_to_units_screen))
            button_box.add_widget(MDIconButton(icon = 'close-thick', theme_icon_color = "Custom", icon_color = (1,0,0,1), on_press = self.dont_go_to_units_screen))
            layout.add_widget(button_box)
            self.card.add_widget(layout)
            self.ids.manager.current_screen.add_widget(self.card)
        return True
    
    def go_to_units_screen(self, instance):
        self.ids.manager.current_screen.remove_widget(self.card)
        self.ids.manager.current = 'units screen'
        self.ids.back_button.disabled = False
        return
    
    def dont_go_to_units_screen(self, instance):
        self.ids.manager.current_screen.remove_widget(self.card)
        self.ids.back_button.disabled = False
        return

    def update(self):
        global app_data
        self.ids.units_list.clear_widgets()
        for unit in app_data.units:
            item = TwoLineListItem(text=unit, secondary_text=app_data.get_progress(unit), on_release=self.open_unit)
            self.ids.units_list.add_widget(item)
    
    def open_unit(self, unit):
        global app_data
        app_data.unit = unit.text
        self.words = [w for w in app_data.words]
        shuffle(self.words)
        self.ids.progressbar.max = len(self.words)
        self.ids.progressbar.value = 0
        self.ids.manager.transition.direction = 'left'
        self.ids.manager.current = 'quiz screen'
        self.open_word(self.words[0])
        self.correct_answer = []
    
    def open_word(self, word):
        global app_data
        app_data.load_word(word, url_source=False)
        self.i = self.words.index(word)
        self.ids.video.source = app_data.video
        self.ids.video.state = 'play'
        self.ids.video.options = { 'eos': 'loop'}
        self.ids.answer_label.text = word.upper()
        to_answer = self.i == self.ids.progressbar.value
        self.ids.answer.disabled = not to_answer
        self.ids.next_button.disabled = to_answer
        self.ids.last_button.disabled = self.i == 0
        if not to_answer:
            self.ids.answer_label.opacity = 1
            if self.correct_answer[self.i]:
                self.ids.answer_label.color = (0, 1, 0, 1)
            else: self.ids.answer_label.color = (1, 0, 0, 1)
        else: self.ids.answer_label.opacity = 0

    def open_last_word(self):
        self.open_word(self.words[self.i-1])

    def open_next_word(self):
        if self.i + 1 < len(self.words): self.open_word(self.words[self.i+1])
        else:
            end_window = BoxLayout(orientation='vertical', size_hint = (1, 0.8), pos_hint = { 'center_y': 0.5 })
            end_window.add_widget(MDLabel(text='Gratuliere!', font_style='H3', bold = True, halign = 'center', valign = 'center'))
            percent = int(self.correct_answer.count(True)/len(self.correct_answer)*100)
            end_window.add_widget(MDLabel(text=f'{percent}% richtig', halign = 'center', valign = 'center'))
            end_window.add_widget(MDRoundFlatButton(text='beenden', pos_hint = {'center_x': 0.5, 'center_y': 0.5 }, on_release = self.close_unit))
            card = MDCard(
                size_hint = (None, None),
                size = (dp(250), dp(150)),
                pos_hint = { 'center_x': 0.5, 'center_y': 0.5 },
                style = 'elevated',
                shadow_softness=2,
                shadow_offset=(0, 1),
            )
            card.add_widget(end_window)
            self.ids.manager.current_screen.add_widget(card)
            app_data.save_progress(percent)
    
    def check_answer(self, text):
        if text.lower() == self.ids.answer_label.text.lower():
            self.ids.answer_label.color = (0, 1, 0, 1)
            self.correct_answer.append(True)
        else:
            self.ids.answer_label.color = (1, 0 , 0, 1)
            self.correct_answer.append(False)
        self.ids.answer_label.opacity = 1
        self.ids.progressbar.value += 1
        self.ids.next_button.disabled = False
        self.ids.answer.text = ''
    
    def close_unit(self, isntance):
        self.ids.manager.current_screen.remove_widget(self.ids.manager.current_screen.children[-1])
        self.ids.manager.transition.direction = 'right'
        self.ids.manager.current = 'units screen'
        self.update()


class Manager(MDBottomNavigation):
    pass


class SignWiseApp(MDApp):
    def build(self):
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Light"

    @property
    def data(self):
        global app_data
        return app_data

#home = SignWiseApp()

#if __name__ == '__main__':
#    home.run()

#class MyApp(App):
#
#    def build(self):
#        return Label(text='Hello world!')


if __name__ == '__main__':
    #MyApp().run()
    SignWiseApp().run()


