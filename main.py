
import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from jnius import autoclass
from kivy import BoxLayout
import time

PythonService = autoclass('org.kivy.android.PythonService')
#PythonService.mService.setAutoRestartService(True)
print(type(PythonService.mService))


class RemoSpeaker(BoxLayout):
    pass


class RemoSpeakerApp(App):
    def build(self):
        return RemoSpeaker()


if __name__ == '__main__':
    RemoSpeakerApp().run()
