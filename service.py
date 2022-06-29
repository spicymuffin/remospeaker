import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget 
from jnius import autoclass
import time


PythonService = autoclass('org.kivy.android.PythonService')
PythonService.mService.setAutoRestartService(True)

print(type(PythonService.mService))

while True:
    print('this is my service and its running')
    time.sleep(1)