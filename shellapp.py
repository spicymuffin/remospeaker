#!/usr/bin/env python

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.app import App
import kivy
kivy.require('2.1.0')


__version__ = '0.1'


class HistoryInput(BoxLayout):
    def collapse_row(self, app, lbl):
        if lbl.shorten:
            lbl.shorten = False
        else:
            lbl.shorten = True
        Clock.schedule_once(app.root.recalc_height)


class HistoryOutput(BoxLayout):
    def collapse_row(self, app, lbl):
        if lbl.shorten:
            lbl.shorten = False
        else:
            lbl.shorten = True
        Clock.schedule_once(app.root.recalc_height)


class RemoSpeaker(BoxLayout):
    line_count = 0
    io_history = ObjectProperty(None)

    def run_input(self, command):
        # Add input to history
        self.line_count += 1
        row = HistoryInput()
        row.line_num = str(self.line_count)
        row.input_text = "<<<" + command
        self.io_history.add_widget(row)

        # Add output to history
        self.line_count += 1
        row = HistoryOutput()
        row.line_num = str(self.line_count)
        row.output_text = '>>>' + command
        self.io_history.add_widget(row)

        # Work-around for height issues
        Clock.schedule_once(self.recalc_height)

    def recalc_height(self, dt):
        ''' A method to add and remove a widget from the io_history to force
            the recalculation of its height. Without this, the scrollview will
            not work correctly.
        '''
        work_around = Widget()
        self.io_history.add_widget(work_around)
        self.io_history.remove_widget(work_around)


class RemoSpeakerApp(App):
    def build(self):
        return RemoSpeaker()


if __name__ == '__main__':
    RemoSpeakerApp().run()
