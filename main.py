from kivy.logger import Logger
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.clock import Clock


import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from jnius import autoclass
import time


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
        # commanc - input in string format

        # Add input to history
        self.line_count += 1
        row = HistoryInput()
        row.line_num = str(self.line_count)
        row.input_text = "> " + command
        self.io_history.add_widget(row)

        # Add output to history
        self.line_count += 1
        row = HistoryOutput()
        row.line_num = str(self.line_count)
        row.output_text = command
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



print("############################## PYTHON ACTIVITY BELOW ##############################")
import jnius
Context = jnius.autoclass('android.content.Context')
Intent = jnius.autoclass('android.content.Intent')
PendingIntent = jnius.autoclass('android.app.PendingIntent')
AndroidString = jnius.autoclass('java.lang.String')
NotificationBuilder = jnius.autoclass('android.app.Notification$Builder')
Notification = jnius.autoclass('android.app.Notification')
service_name = 'Worker'
package_name = Context.getApplicationContext()
PythonService = autoclass('org.kivy.android.PythonService')
print(type(PythonService))
service = PythonService.mService
print(type(PythonService.mService))
# Previous version of Kivy had a reference to the service like below.
#service = jnius.autoclass('{}.Service{}'.format(package_name, service_name)).mService
PythonActivity = jnius.autoclass('org.kivy.android' + '.PythonActivity')
notification_service = service.getSystemService(
    Context.NOTIFICATION_SERVICE)
app_context = service.getApplication().getApplicationContext()
notification_builder = NotificationBuilder(app_context)
title = AndroidString("EzTunes".encode('utf-8'))
message = AndroidString("Ready to play music.".encode('utf-8'))
app_class = service.getApplication().getClass()
notification_intent = Intent(app_context, PythonActivity)
notification_intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP |
    Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_NEW_TASK)
notification_intent.setAction(Intent.ACTION_MAIN)
notification_intent.addCategory(Intent.CATEGORY_LAUNCHER)
intent = PendingIntent.getActivity(service, 0, notification_intent, 0)
notification_builder.setContentTitle(title)
notification_builder.setContentText(message)
notification_builder.setContentIntent(intent)
Drawable = jnius.autoclass("{}.R$drawable".format(service.getPackageName()))
icon = getattr(Drawable, 'icon')
notification_builder.setSmallIcon(icon)
notification_builder.setAutoCancel(True)
new_notification = notification_builder.getNotification()
#Below sends the notification to the notification bar; nice but not a foreground service.
#notification_service.notify(0, new_noti)
service.startForeground(1, new_notification)

class RemoSpeakerApp(App):
    def on_start(self):
        pass




    def start_service(self):
        from jnius import autoclass
        from android import mActivity
        context = mActivity.getApplicationContext()
        SERVICE_NAME = str(context.getPackageName()) + '.Service' + 'Worker'
        print(SERVICE_NAME)
        service = autoclass(SERVICE_NAME)
        service.start(mActivity, '')
        return service

    def build(self):
        return RemoSpeaker()


if __name__ == '__main__':
    RemoSpeakerApp().run()
