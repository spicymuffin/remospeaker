from this import d
from kivy.logger import Logger
import threading as tr
import datetime
import os
import time
import requests
import vk_api
import random
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import kivy
from kivy.core.audio import SoundLoader
from kivy.utils import platform
import gtts

kivy.require('2.1.0')
__version__ = '1.1'

# region API initialization
LONGPOLL_TOKEN = "af710c5a4eff1ccc9e2136eaaf29fa1d4c33e57d7b6118a8b38226700add8b28f2825568d4a875890bdfc"
vk = vk_api.VkApi(token=LONGPOLL_TOKEN)
vk._auth_token()
vk.get_api()
longpoll = VkBotLongPoll(vk, 199164285)
# endregion

# region global variables
# region misc
vk_longpoll_loop_thread = None
schedule_clock_thread = None
vk_longpoll_loop_flag = False
schedule_clock_flag = False
debug_flag = False
HELP_MESSAGE = """
============================================

!promote {id}: делает админом (требует прав)

id - id повышаемого

============================================

!demote {id}: понижает с должности админа (требует прав)

id - id понижаемого

============================================

!nuke: удаляет всех админов (требует прав)

============================================

!showid: показывает id отправителя

============================================

!cringepic: я не знаю что это

============================================

!debug: проверяет доступность робота

============================================

!showadmin: показывает список админов

============================================

!showaudiofiles: показать аудио файлы в локальной памяти
сокращения: !saf

============================================

!scheduleplaybacktimer: {af_index} {delta}{unit}: воспроизводит аудио файл через заданное время

af_index - индекс воспроизводимого аудио файла
delta - через сколько воспроизводить
unit - единицы измерения

ПРИМЕР ИСПОЛЬЗОВАНИЯ:
!scheduleplaybacktimer 0 5h
(воспроизводит аудио файл номер 0 через 5 часов)

сокращения: !spbt

============================================

!scheduleplayback: {af_index} {timestamp}: воспроизвести аудио файл в назначенную дату

af_index - индекс воспроизводимого аудио файла
timestamp - дата воспроизведения (формат: год-месяц-день@час:минута:секунда)

ПРИМЕР ИСПОЛЬЗОВАНИЯ:
!scheduleplayback 0 2022-06-30@23:42:40
(воспроизводит аудио файл номер 0 в 11:42:40 2022 года 30 июня)

сокращения: !spb

============================================

!showschedule: показывает "расписание"

сокращения: !ss

============================================

!deleteaudiofile {af_index}: удаляет аудио файл

af_index - индекс удаляемого аудио файла

сокращения: !daf

============================================

!deletetask {task_index}: удаляет задачу

task_index - индекс удаляемой "задачи"

сокращения: !dt

============================================

!tts {lang} {message}: генерирует и воспроизводит аудио файл с роботическим голосом, читающий сообщение

lang - код языка
message - сообщение (творите, не стесняйтесь, но не перебарщивайте с длиной, бот может впасть в тильт!)

============================================

!setvolume {val}: устанавливает громкость на устройстве

val - число в [0;15] (целое!), громкость

сокращения: !sv

============================================

!status {arg}: дает статус модуля бота

arg - строка, принимает значения: ["battery", "bat", "volume", "vol", "tts"]

============================================

!quit: убивает бота (так делать не надо!)

============================================
"""
GREETING = "photo-199164285_457239024"
# endregion
# region IDs
ILYA_ID = 392697013
CREATOR_ID = 392697013
groupId = 2000000001
# me   392697013
# ilya 337883597
# endregion
# region directory management
AUDIO_FILES_FOLDER_NAME = "audiofiles"
AUDIO_FILES_DIR = ""
TTS_FILES_FOLDER_NAME = "ttsfiles"
TTS_FILES_DIR = ""
# endregion
# region lists
# Photo list (upload to bot's community)
PHOTOS = ["photo-199164285_457239021", "photo-199164285_457239019",
          "photo-199164285_457239022", "photo-199164285_457239023"]
ADMIN_ID_LIST = [CREATOR_ID]
AUDIO_FILES_LIST = []
SCHEDULE = []
# endregion
# region time management
starttime = None
REFRESH_RATE = 1
# endregion
# endregion

# from jnius import autoclass

# from jnius import autoclass
# Context = autoclass('android.content.Context')
# BatteryManager = autoclass('android.os.BatteryManager')
# service = autoclass('org.kivy.android.PythonService').mService
# BatteryService = service.getSystemService(Context.BATTERY_SERVICE)
# charge = BatteryService.getIntProperty(
#     BatteryManager.BATTERY_PROPERTY_CAPACITY)
# isCharging = BatteryService.isCharging()

# getSystemService(Context.POWER_SERVICE) as PowerManager).run


# region classes


class MusicPlayerAndroid(object):
    def __init__(self):
        from jnius import autoclass
        MediaPlayer = autoclass('android.media.MediaPlayer')
        self.mplayer = MediaPlayer()

        self.secs = 0
        self.actualsong = ''
        self.length = 0
        self.isplaying = False

    def __del__(self):
        self.stop()
        self.mplayer.release()
        Logger.info('mplayer: deleted')

    def load(self, filename):
        try:
            self.actualsong = filename
            self.secs = 0
            self.mplayer.setDataSource(filename)
            self.mplayer.prepare()
            self.length = self.mplayer.getDuration() / 1000
            Logger.info('mplayer load: %s' % filename)
            Logger.info('type: %s' % type(filename))
            return True
        except:
            Logger.info('error in title: %s' % filename)
            return False

    def unload(self):
        self.mplayer.reset()

    def play(self):
        self.mplayer.start()
        self.isplaying = True
        Logger.info('mplayer: play')

    def stop(self):
        self.mplayer.stop()
        self.secs = 0
        self.isplaying = False
        Logger.info('mplayer: stop')

    def seek(self, timepos_secs):
        self.mplayer.seekTo(timepos_secs * 1000)
        Logger.info('mplayer: seek %s' % int(timepos_secs))


class AudioFile:
    def __init__(self, date, creator_id, creator_name, link, filename, path):
        self.filename = filename
        self.date = date
        self.creator_id = creator_id
        value = datetime.datetime.fromtimestamp(int(date))
        self.hdate = f"{value:%Y-%m-%d@%H:%M:%S}"
        self.creator_name = creator_name
        self.path = path
        self.link = link
        self.index = -1
        self.associated_tasks = []

    def __str__(self):
        return f"Date: {self.hdate}\nCreator name: {self.creator_name}\nLink: {self.link}\nName: {self.filename}\nAssociated tasks: {len(self.associated_tasks)}"

    def delete_associated_tasks(self):
        dellist = []
        i = 0
        while i < len(self.associated_tasks):
            if self.associated_tasks[i].afile.index == self.index:
                print(f"deleted task {self.associated_tasks[i].index}")
                # self.associated_tasks[i].popself()
                dellist.append(self.associated_tasks[i].index)
                i += 1

        del_list_inplace(SCHEDULE, dellist)


class Task:
    def __init__(self, creation_date, target_date, afile, creator_id):
        self.creation_date = creation_date
        self.target_date = target_date
        value = datetime.datetime.fromtimestamp(int(creation_date))
        self.hcdate = f"{value:%Y-%m-%d@%H:%M:%S}"
        value = datetime.datetime.fromtimestamp(int(target_date))
        self.htdate = f"{value:%Y-%m-%d@%H:%M:%S}"
        self.afile = afile
        self.creator_id = creator_id
        self.creator_name = get_full_name(creator_id)
        self.index = -1

    def remove_refs(self):
        self.afile.associated_tasks.remove(self)

    def __str__(self):
        return f"Date: {self.hcdate}\nCreator name: {self.creator_name}\nTarget date: {self.htdate}\nAFIndex: {self.afile.index}"

# endregion classes

# region command funcitons

# region interal functions


def get_name(_id):
    return vk.method("users.get", {"user_ids": _id, "lang": 0})[0]['first_name']


def get_full_name(_id):
    return vk.method("users.get", {"user_ids": _id, "lang": 0})[0]['first_name'] + ' ' + vk.method("users.get", {"user_ids": _id, "lang": 0})[0]['last_name']


def check_id(_id):
    return True


def send_message(_chatId, _message):
    return vk.method("messages.send", {
        "peer_id": _chatId, "message": _message, "random_id": 0})


def send_message_attachement(_chatId, _message, _attachement):
    return vk.method("messages.send", {
        "peer_id": _chatId, "message": _message, "attachment": _attachement, "random_id": 0})


def is_command(_message):
    if _message[0] == '!':
        return 0
    else:
        return 1


def log_error(_groupId, explanation):
    send_message(_groupId, "ERROR: " + explanation)


def log_access_denied(_groupId):
    send_message(_groupId, "ACCESS DENIED. are you admin?")

# endregion

# region demote


def handle_demote_request(_message):
    try:
        try:
            demoteId = int(_message.split(" ")[1])
        except:
            return 1  # invalid id
        if not check_id(demoteId):
            return 1  # invalid id
        if demoteId not in ADMIN_ID_LIST:
            return 2  # admin id isnt in admin id list
        if demoteId == CREATOR_ID:
            return 3  # cant demote creator
        if demoteId in ADMIN_ID_LIST:
            return 0  # success
    except Exception as ex:
        return ex  # unknown error
    return 100  # unknown error


def demote_action(parameters):
    _sender = parameters[0]
    _message = parameters[1]
    _groupId = parameters[2]

    result = handle_demote_request(_message)

    if isinstance(result, Exception):
        log_error(_groupId, str(result))
        return  # abort if unknown error

    if result == 1:
        log_error(_groupId, f"couldn't demote, parameter ID is invalid.")
        return  # abort if parameter is inivalid

    if result == 2:
        log_error(
            _groupId, f"couldn't demote {get_name(demoteId)}, ADMIN_ID_LIST doesn't contain {get_name(demoteId)}.")
        return  # abort if ADMIN_ID_LIST doesn't contain id

    if result == 3:
        log_error(
            _groupId, f"couldn't demote {get_name(demoteId)}, CREATOR can't be demoted.")
        return  # abort if CREATOR

    if result == 100:
        log_error(_groupId, f"unknown.")
        return  # abort if unknown error

    demoteId = int(_message.split(" ")[1])

    if result == 0:
        ADMIN_ID_LIST.remove(demoteId)
        send_message(_groupId, f"demoted {get_name(demoteId)} successfully.")


# endregion

# region promote


def handle_promote_request(_message):
    try:
        try:
            promoteId = int(_message.split(" ")[1])
        except:
            return 1  # invalid id
        if not check_id(promoteId):
            return 1  # invalid id
        elif promoteId in ADMIN_ID_LIST:
            return 2  # admin id list already contains this id
        elif promoteId not in ADMIN_ID_LIST:
            return 0  # success
    except Exception as ex:
        return ex  # unknown error
    return 100  # unknown error


def promote_action(parameters):
    _sender = parameters[0]
    _message = parameters[1]
    _groupId = parameters[2]

    result = handle_promote_request(_message)

    if isinstance(result, Exception):
        log_error(_groupId, str(result))
        return  # abort if unknown error

    if result == 1:
        log_error(_groupId, "couldn't demote, parameter ID is invalid.")
        return  # abort if parameter is inivalid

    if result == 2:
        log_error(
            _groupId, f"couldn't promote {get_name(promoteId)}, ADMIN_ID_LIST already contains {get_name(promoteId)}.")
        return  # abort if ADMIN_ID_LIST already contains id

    if result == 100:
        log_error(_groupId, "unknown.")
        return  # abort if unknown error

    promoteId = int(_message.split(" ")[1])

    if result == 0:
        ADMIN_ID_LIST.append(promoteId)
        send_message(_groupId, f"promoted {get_name(promoteId)} successfully.")


# endregion

# region nuke


def handle_nuke_request(_requester):
    try:
        if _requester != CREATOR_ID:
            return 1  # requester isnt creator
        if _requester == CREATOR_ID:
            return 0  # success
    except Exception as ex:
        return ex  # unknown error
    return 100  # unknown error


def nuke_action(_sender, _groupId):
    global ADMIN_ID_LIST

    result = handle_nuke_request(_sender)

    if isinstance(result, Exception):
        log_error(_groupId, str(result))
        return  # abort if unknown error

    if result == 1:
        log_access_denied(_groupId)
        return  # abort if access denied

    if result == 100:
        log_error(_groupId, "unknown.")
        return  # abort if unknown error

    if result == 0:
        ADMIN_ID_LIST = [CREATOR_ID]
        send_message(_groupId, f"nuked successfully")


# endregion

# region showadmin


def showadmin_action(_groupId):
    if len(ADMIN_ID_LIST) == 0:
        send_message(_groupId, "no admins to display.")
    toPrint = ""
    for adminId in ADMIN_ID_LIST:
        toPrint += get_name(str(adminId))
        toPrint += f"({adminId}); "
    toPrint = toPrint[0:-2]
    send_message(_groupId, toPrint)

# endregion

# region authandexecute


def authenticate_and_execute(_toAuthenticate, _toExecute, _parameters, _groupId, creator=False):
    if _toAuthenticate in ADMIN_ID_LIST:
        _toExecute(_parameters)
    else:
        send_message(_groupId, "ACCESS DENIED: not admin.")
    if _toAuthenticate == CREATOR_ID:
        _toExecute(_parameters)
    else:
        send_message(_groupId, "ACCESS DENIED: not creator.")


# endregion authandexecute

# region quit #TODO: error handling


def quit_action(parameters):
    _groupId = parameters[0]
    send_message(_groupId, f"quitting...")
    exit(0)


# endregion quit

# region tts

TTS_GENERATING = 0
TTS_READING = 0


def format_message(msg):
    if len(msg) > 30:
        return '"' + msg[:30] + "..." + '"'
    return '"' + msg + '"'


def handle_tts_request(_message):
    try:
        splt = _message.split(" ")
        if len(splt) < 3:
            return 5  # invalid parameter count

        if not splt[1] in gtts.lang.tts_langs().keys():
            return 1  # invalid language code

        return 0  # success
    except Exception as ex:
        return ex
    return 100  # unknown error


def tts_action(_userId, _message, _groupId):
    result = handle_tts_request(_message)

    if isinstance(result, Exception):
        log_error(_groupId, str(result))
        return  # abort if unknown error

    if result == 1:
        log_error(_groupId, f"invalid language code")
        return  # abort if invalid langage code

    if result == 5:
        log_error(_groupId, f"invalid parameter count")
        return  # abort if invalid parameter count

    if result == 100:
        log_error(_groupId, f"unknown.")
        return  # abort if unknown error

    if result == 0:
        tts_thread_instance = tr.Thread(
            target=tts_thread, args=(_message, _groupId))
        tts_thread_instance.setDaemon(True)
        tts_thread_instance.start()


def tts_thread(_message, _groupId):

    global TTS_GENERATING
    global TTS_READING

    languagecode = _message.split(" ")[1]
    msg = " ".join(_message.split(" ")[2:])
    send_message(
        _groupId, f'started tts thread, processing...\nmsg: {format_message(msg)}')
    TTS_GENERATING += 1
    try:
        if platform == 'android':
            from jnius import autoclass
            tts = gtts.gTTS(text=msg, lang=languagecode)

            arr = os.listdir(TTS_FILES_DIR)
            path = f"{TTS_FILES_DIR}/tts{len(arr)}.ogg"
            tts.save(path)
            MediaPlayer = autoclass('android.media.MediaPlayer')

            # create our player
            mPlayer = MediaPlayer()
            mPlayer.setDataSource(path)
            mPlayer.prepare()
            send_message(
                _groupId, f'file generated. reading...\nmsg: {format_message(msg)}')
            TTS_GENERATING -= 1
            TTS_READING += 1
            # play
            mPlayer.start()
            print('duration:', mPlayer.getDuration())
            print('current position:', mPlayer.getCurrentPosition())

            time.sleep(mPlayer.getDuration()/1000 + 1)

            os.remove(path)
        else:
            tts = gtts.gTTS(text=msg, lang=languagecode)
            print(f'{TTS_FILES_DIR}/tts.mp3')
            tts.save(f'{TTS_FILES_DIR}/tts.mp3')
            sound = SoundLoader.load(f'{TTS_FILES_DIR}/tts.mp3')
            sound.play()

    except Exception as ex:
        send_message(_groupId, f'error while executing tts: {ex}')
        print(ex)

    send_message(
        _groupId, f'finished reading {format_message(msg)} in {gtts.lang.tts_langs()[languagecode]}')

    TTS_READING -= 1

# endregion tts

# region schedulepb


def add_task(creation_date, target_date, afile, creator_id):
    global SCHEDULE
    i = 0
    while i < len(SCHEDULE) and SCHEDULE[i].target_date <= target_date:
        print(f"skip; {i}\n {target_date} ? {SCHEDULE[i].target_date}")
        i += 1

    SCHEDULE.insert(i, Task(creation_date, target_date, afile, creator_id))
    task = SCHEDULE[i]
    update_indexes_sdl()
    afile.associated_tasks.append(task)
    print(i)


def handle_schedulepb_request(_message):
    try:
        splt = _message.split(" ")
        if len(splt) != 3:
            return 5  # invalid parameter count

        index = _message.split(" ")[1]
        target_date = _message.split(" ")[2]

        try:
            index = int(index)
        except:
            return 1  # index not an integer
        try:
            date = datetime.datetime.strptime(
                target_date, "%Y-%m-%d@%H:%M:%S").timestamp()
        except:
            return 2  # date bad format

        indexflag = False
        requestindex = -1
        for i in range(len(AUDIO_FILES_LIST)):
            if AUDIO_FILES_LIST[i].index == index:
                requestindex = i
                indexflag = True
                break

        if date <= int(time.time()) + 5:
            return 4  # date should be at least 5 secs away from now

        if indexflag:
            return 0  # success
        else:
            return 3  # audio file not present
    except Exception as ex:
        return ex  # unknown error
    return 100


def schedulepb_action(_userId, _message, _groupId, _messageObject):

    result = handle_schedulepb_request(_message)

    if isinstance(result, Exception):
        log_error(_groupId, str(result))
        return

    if result == 1:
        log_error(_groupId, "parameter ID is invalid.")
        return  # abort if parameter is inivalid

    if result == 2:
        log_error(_groupId, "parameter DATE is invalid.")
        return  # abort if parameter is inivalid

    if result == 3:
        log_error(_groupId, "INDEX out of bounds.")
        return  # abort if index abort if audio file index not present

    if result == 4:
        log_error(_groupId, "target date should be at least 5 secs away from now.")
        return  # abort if date is too close

    if result == 5:
        log_error(_groupId, "invalid number of parameters")
        return  # abort if invalid number of parameters

    elif result == 100:
        log_error(_groupId, "unknown.")
        return  # abort if unknown error

    index = int(_message.split(" ")[1])
    target_date = datetime.datetime.strptime(
        _message.split(" ")[2], "%Y-%m-%d@%H:%M:%S").timestamp()

    if result == 0:
        requestindex = -1
        for i in range(len(AUDIO_FILES_LIST)):
            if AUDIO_FILES_LIST[i].index == index:
                requestindex = i
                break
        add_task(_messageObject["date"], target_date,
                 AUDIO_FILES_LIST[requestindex], _userId)
        send_message(
            _groupId, f"scheduled playback:\nFile: {index}\nDate: {_message.split(' ')[2]}")


# endregion schedulepb

# region schedulepbtimer


def handle_schedulepbt_request(_message):
    try:
        splt = _message.split(" ")
        if len(splt) != 3:
            return 5  # invalid parameter count

        index = _message.split(" ")[1]
        delta = _message.split(" ")[2].lower()

        try:
            index = int(index)
        except:
            return 1  # index not an integer
        allowed_metrics = ['s', 'm', 'h', 'd']
        if delta[-1] not in allowed_metrics:
            return 2  # incorrect metrics
        try:
            intdelta = int(delta[0:-1])
        except:
            return 3  # delta not an integer

        indexflag = False
        requestindex = -1
        for i in range(len(AUDIO_FILES_LIST)):
            if AUDIO_FILES_LIST[i].index == index:
                requestindex = i
                indexflag = True
                break

        if indexflag:
            return 0  # success
        else:
            return 4  # index not present
    except Exception as ex:
        return ex  # unknown error
    return 0  # unknown error


def schedulepbt_action(_userId, _message, _groupId, _messageObject):

    result = handle_schedulepbt_request(_message)

    if isinstance(result, Exception):
        log_error(_groupId, str(result))
        return  # abort if unknown error

    if result == 1:
        log_error(_groupId, "arameter ID is invalid.")
        return  # abort if parameter is inivalid

    if result == 2:
        log_error(_groupId, "incorrect metrics.")
        return  # abort if parameter is inivalid

    if result == 3:
        log_error(_groupId, "delta not an integer.")
        return  # abort if parameter is inivalid

    if result == 4:
        log_error(_groupId, "audio file index not present")
        return  # abort if audio file index not present

    if result == 5:
        log_error(_groupId, "invalid number of parameters")
        return  # abort if invalid number of parameters

    if result == 100:
        log_error(_groupId, "unknown.")
        return  # abort if unknown error

    mul = 0
    delta = _message.split(" ")[2].lower()
    metric = delta[-1]
    intdelta = int(delta[0:-1])
    if metric == "s":
        mul = 1
    elif metric == "m":
        mul = 1 * 60
    elif metric == "h":
        mul = 1 * 60 * 60
    elif metric == "d":
        mul = 1 * 60 * 60 * 24

    index = int(_message.split(" ")[1])
    target_date = int(time.time()) + intdelta * mul

    if result == 0:
        requestindex = -1
        for i in range(len(AUDIO_FILES_LIST)):
            if AUDIO_FILES_LIST[i].index == index:
                requestindex = i
                break
        add_task(_messageObject["date"], target_date,
                 AUDIO_FILES_LIST[requestindex], _userId)
        printdate = str(datetime.datetime.fromtimestamp(
            int(target_date))).replace(" ", "@")
        send_message(
            _groupId, f"scheduled playback:\nFile: {index}\nDate: {printdate}")


# endregion

# region showschedule


def showschedule_action(_groupId):
    global SCHEDULE
    if len(SCHEDULE) == 0:
        send_message(_groupId, "no tasks to display.")
        return
    toPrint = ""
    for task in SCHEDULE:
        toPrint += f" INDEX: {task.index}\n"
        toPrint += str(task)
        toPrint += "\n\n"
    send_message(_groupId, toPrint)


# endregion

# region helperfuncs


def update_indexes_sdl():
    i = 0
    for task in SCHEDULE:
        task.index = i
        i += 1


def update_indexes_afl():
    i = 0
    for file in AUDIO_FILES_LIST:
        file.index = i
        i += 1


def del_list_inplace(l, id_to_del):
    for i in sorted(id_to_del, reverse=True):
        del(l[i])
# endregion

# region showaudiofiles


def showaudiofiles_action(_groupId):
    if len(AUDIO_FILES_LIST) == 0:
        send_message(_groupId, "no audio files to display.")
        return
    toPrint = ""
    for file in AUDIO_FILES_LIST:
        toPrint += f" INDEX: {file.index}\n"
        toPrint += str(file)
        toPrint += "\n\n"
    send_message(_groupId, toPrint)


# endregion

# region deleteaf


def handle_deleteaf_request(_message):
    try:
        index = -1
        try:
            index = int(_message.split(" ")[1])
        except:
            return 1  # invalid index

        removeindex = -1
        for i in range(len(AUDIO_FILES_LIST)):
            if AUDIO_FILES_LIST[i].index == index:
                removeindex = i
                return 0

        if removeindex == -1:
            return 2  # index not in aflist
    except Exception as ex:
        return ex  # unknown error
    return 100  # unknown error


def deleteaf_action(_userId, _message, _groupId):

    result = handle_deleteaf_request(_message)

    if isinstance(result, Exception):
        log_error(_groupId, str(result))
        return  # abort if unknown error

    if result == 1:
        log_error(_groupId, "couldn't delete, parameter INDEX is invalid.")
        return  # abort if parameter is inivalid

    if result == 2:
        log_error(_groupId, "couldn't delete, INDEX is out of bounds")
        return  # abort if index out of bounds

    if result == 100:
        log_error(_groupId, "unknown.")
        return  # abort if unknown error

    index = int(_message.split(" ")[1])

    if result == 0:
        removeindex = -1

        for i in range(len(AUDIO_FILES_LIST)):
            if AUDIO_FILES_LIST[i].index == index:
                removeindex = i

        af = AUDIO_FILES_LIST[removeindex]
        af.delete_associated_tasks()
        os.remove(af.path)
        AUDIO_FILES_LIST.pop(removeindex)

        print(f"successfully deleted file of index {index}.")
        send_message(
            _groupId, f"successfully deleted file of index {index}.")


# endregion

# region deletetask


def handle_deletetask_request(_message):
    try:
        index = -1
        try:
            index = int(_message.split(" ")[1])
        except:
            return 1  # invalid index
        if len(SCHEDULE) <= index:
            return 2  # invalid index
        if len(SCHEDULE) > index:
            return 0  # success
    except Exception as ex:
        return ex
    return 100  # unknown error


def deletetask_action(_userId, _message, _groupId):

    result = handle_deletetask_request(_message)

    if isinstance(result, Exception):
        log_error(_groupId, str(result))
        return  # abort if unknown error

    if result == 1:
        log_error(_groupId, "couldn't delete, parameter INDEX is invalid.")
        return  # abort if parameter is inivalid

    if result == 2:
        log_error(_groupId, "couldn't delete, INDEX is out of bounds")
        return  # abort if index out of bounds

    if result == 100:
        log_error(_groupId, "unknown.")
        return  # abort if unknown error

    index = int(_message.split(" ")[1])

    if result == 0:
        task = SCHEDULE[index]
        task.remove_refs()
        SCHEDULE.pop(index)
        update_indexes_sdl()
        send_message(_groupId, f"successfully deleted task of index {index}.")


# endregion

# region af managment


def make_AudioFile_from_path(path, index):
    #path = AUDIO_FILES_DIR + '/' + path
    name = path.split("/")[-1]
    data = name.split(";")
    print(path)
    af = AudioFile(data[0], data[1], data[2], data[3].replace(
        "@", ":").replace("$", "/").replace("#", "?"), data[4][0:-4], path)
    af.index = index
    return af


# endregion

# region setvolume


def handle_setvolume_request(_message):
    try:
        splt = _message.split(" ")

        if len(splt) < 2:
            return 2  # invalid arg count

        volume = _message.split(" ")[1]
        volume = int(volume)

        if 0 <= volume <= 15:
            return 0
        else:
            return 1  # volume should be between 0 and 15

    except Exception as ex:
        return ex
    return 100  # unknown error


def setvolume_action(_userId, _message, _groupId):

    result = handle_setvolume_request(_message)

    if isinstance(result, Exception):
        log_error(_groupId, str(result))
        return  # abort if unknown error

    if result == 1:
        log_error(_groupId, "volume should be between 0 and 15")
        return  # abort if volume not between 0 and 15

    if result == 2:
        log_error(_groupId, "invalid number of parameters")
        return  # abort if invalid number of parameters

    if result == 100:
        log_error(_groupId, "unknown.")
        return  # abort if unknown error

    if result == 0:
        splt = _message.split(" ")
        volume = _message.split(" ")[1]
        volume = int(volume)

        from jnius import autoclass
        Context = autoclass('android.content.Context')
        AudioManager = autoclass('android.media.AudioManager')
        service = autoclass('org.kivy.android.PythonService').mService
        AudioService = service.getSystemService(Context.AUDIO_SERVICE)
        AudioService.setStreamVolume(AudioManager.STREAM_MUSIC, volume, 0)
        send_message(_groupId, f"successfully set volume to {volume}")


# endregion

# region status

STATUS_ARGS = ["battery", "bat", "volume", "vol", "tts"]


def handle_status_request(_message):
    try:
        splt = _message.split(" ")

        if len(splt) < 2:
            return 2  # invalid arg count

        arg = _message.split(" ")[1]

        if arg not in STATUS_ARGS:
            return 1  # invalid arg
        if arg in STATUS_ARGS:
            return 0  # success
        return 100  # unknown error
    except Exception as ex:
        return ex


def on_broadcast(context, intent):
    extras = intent.getExtras()
    print(extras)


def status_action(_userId, _message, _groupId):

    global TTS_GENERATING
    global TTS_READING

    result = handle_status_request(_message)

    if isinstance(result, Exception):
        log_error(_groupId, str(result))
        return  # abort if unknown error

    if result == 1:
        log_error(
            _groupId, f"invalid argument, possible are: {' '.join(STATUS_ARGS)}")
        return  # abort if invalid arg

    if result == 2:
        log_error(_groupId, "invalid number of parameters")
        return  # abort if invalid number of parameters

    if result == 100:
        log_error(_groupId, "unknown.")
        return  # abort if unknown error

    if result == 0:
        splt = _message.split(" ")
        arg = _message.split(" ")[1]

        if arg == "bat" or arg == "battery":
            from jnius import autoclass
            Context = autoclass('android.content.Context')
            BatteryManager = autoclass('android.os.BatteryManager')
            service = autoclass('org.kivy.android.PythonService').mService
            BatteryService = service.getSystemService(Context.BATTERY_SERVICE)
            charge = BatteryService.getIntProperty(
                BatteryManager.BATTERY_PROPERTY_CAPACITY)
            isCharging = BatteryService.isCharging()
            send_message(
                _groupId, f"charge: {charge}%\ncharging: {isCharging}")

        if arg == "vol" or arg == "volume":
            from jnius import autoclass
            Context = autoclass('android.content.Context')
            AudioManager = autoclass('android.media.AudioManager')
            service = autoclass('org.kivy.android.PythonService').mService
            AudioService = service.getSystemService(Context.AUDIO_SERVICE)
            volume = AudioService.getStreamVolume(AudioManager.STREAM_MUSIC)
            send_message(_groupId, f"volume: {volume}")

        if arg == "tts":
            send_message(
                _groupId, f"tts reading: {TTS_READING}\ntts generating: {TTS_GENERATING}")

        # if arg == "dev" or arg == "device":
        #     from jnius import autoclass
        #     Context = autoclass('android.content.Context')
        #     HardwarePropertiesManager = autoclass(
        #         'android.os.HardwarePropertiesManager')
        #     service = autoclass('org.kivy.android.PythonService').mService
        #     HardwarePropertiesService = service.getSystemService(
        #         Context.HARDWARE_PROPERTIES_SERVICE)
        #     print(type(HardwarePropertiesManager))
        #     print(type(HardwarePropertiesService))

        #     cpu_temp = HardwarePropertiesService.getDeviceTemperatures(
        #         HardwarePropertiesManager.DEVICE_TEMPERATURE_CPU, HardwarePropertiesManager.TEMPERATURE_CURRENT)
        #     bat_temp = HardwarePropertiesService.getDeviceTemperatures(
        #         HardwarePropertiesManager.DEVICE_TEMPERATURE_BATTERY, HardwarePropertiesManager.TEMPERATURE_CURRENT)
        #     gpu_temp = HardwarePropertiesService.getDeviceTemperatures(
        #         HardwarePropertiesManager.DEVICE_TEMPERATURE_GPU, HardwarePropertiesManager.TEMPERATURE_CURRENT)
        #     skn_temp = HardwarePropertiesService.getDeviceTemperatures(
        #         HardwarePropertiesManager.DEVICE_TEMPERATURE_SKIN, HardwarePropertiesManager.TEMPERATURE_CURRENT)
        #     cpu_usages = HardwarePropertiesService.getCpuUsages()
        #     send_message(
        #         _groupId, f"cpu temp: {cpu_temp}\nbat temp: {bat_temp}\ngpu temp: {gpu_temp}\nskin temp: {skn_temp}\ncpu_usages: {cpu_usages}")

# endregion

# endregion

# region main functions


def reset():
    global SCHEDULE
    global AUDIO_FILES_LIST
    global ADMIN_ID_LIST
    global AUDIO_FILES_FOLDER_NAME
    global AUDIO_FILES_DIR
    global TTS_FILES_FOLDER_NAME
    global TTS_FILES_DIR
    global vk
    global longpoll
    global LONGPOLL_TOKEN
    global TTS_GENERATING
    global TTS_READING
    global groupId
    global debug_flag

    groupId = 2000000001

    SCHEDULE = []
    AUDIO_FILES_LIST = []
    ADMIN_ID_LIST = [CREATOR_ID]
    AUDIO_FILES_FOLDER_NAME = "audiofiles"
    AUDIO_FILES_DIR = ""
    TTS_FILES_FOLDER_NAME = "ttsfiles"  # why? idk this is madness anyways lol
    TTS_FILES_DIR = ""
    debug_flag = False

    vk = vk_api.VkApi(token=LONGPOLL_TOKEN)
    vk._auth_token()
    vk.get_api()
    longpoll = VkBotLongPoll(vk, 199164285)

    TTS_READING = 0
    TTS_GENERATING = 0

    startup()


def load_files():
    arr = os.listdir(AUDIO_FILES_DIR)
    i = 0
    for entry in arr:
        AUDIO_FILES_LIST.append(make_AudioFile_from_path(
            f"{AUDIO_FILES_DIR}/{entry}", i))
        i += 1

    print(f"loaded {len(arr)} files")


def startup():
    global starttime
    global AUDIO_FILES_DIR
    global TTS_FILES_DIR
    starttime = time.time()
    if platform == 'android':
        from android.storage import primary_external_storage_path
        AUDIO_FILES_DIR = primary_external_storage_path() + "/" + AUDIO_FILES_FOLDER_NAME
        TTS_FILES_DIR = primary_external_storage_path() + "/" + TTS_FILES_FOLDER_NAME
        print(AUDIO_FILES_DIR)
        print(TTS_FILES_DIR)
        if not os.path.exists(AUDIO_FILES_DIR):
            os.makedirs(AUDIO_FILES_DIR)
            print("Made audio files directory")
        if not os.path.exists(TTS_FILES_DIR):
            os.makedirs(TTS_FILES_DIR)
            print("Made tts files directory")
    else:
        AUDIO_FILES_DIR = os.path.dirname(
            __file__) + "/" + AUDIO_FILES_FOLDER_NAME
        TTS_FILES_DIR = os.path.dirname(
            __file__) + "/" + TTS_FILES_FOLDER_NAME
        print(AUDIO_FILES_DIR)
        print(TTS_FILES_DIR)
        if not os.path.exists(AUDIO_FILES_DIR):
            os.makedirs(AUDIO_FILES_DIR)
            print("Made audio files directory")
        if not os.path.exists(TTS_FILES_DIR):
            os.makedirs(TTS_FILES_DIR)
            print("Made tts files directory")

    load_files()


def schedule_clock():

    global SCHEDULE
    global schedule_clock_thread
    global schedule_clock_flag
    global vk_longpoll_loop_flag

    send_message(groupId, "schedule_clock started, setting flags")
    schedule_clock_flag = True
    while True:
        try:
            if debug_flag:
                a = 1/0
            while len(SCHEDULE) > 0 and SCHEDULE[0].target_date <= datetime.datetime.now().timestamp():
                # while len(SCHEDULE) != 0:
                task = SCHEDULE[0]
                task.remove_refs()
                SCHEDULE.pop(0)
                update_indexes_sdl()
                print(task.afile.path)
                if platform == 'android':
                    sound = MusicPlayerAndroid()
                    sound.load(task.afile.path)
                    sound.play()
                else:
                    sound = SoundLoader.load(task.afile.path)
                    sound.play()
                send_message(
                    groupId, f"played af of index: {task.afile.index} successfully, dequeing task. {len(SCHEDULE)} tasks remaining.")
            time.sleep(REFRESH_RATE -
                       ((time.time() - starttime) % REFRESH_RATE))
        except Exception as ex:
            send_message(
                groupId, f"FATAL ERROR: {ex}. schedule_clock_thread dead!! attempting restart...")
            schedule_clock_flag = False
            reset()
            schedule_clock_thread = tr.Thread(target=schedule_clock, args=())
            schedule_clock_thread.start()
            return


def vk_longpoll_loop():

    global groupId
    global HELP_MESSAGE
    global vk_longpoll_loop_thread
    global vk_longpoll_loop_flag
    global schedule_clock_flag
    global debug_flag

    send_message(groupId, "vk_longpoll_loop started, setting flags")
    vk_longpoll_loop_flag = True
    send_message_attachement(groupId, " ", GREETING)
    send_message(groupId, 'remospeaker boot complete! type "!help" to get started.')
    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    if event.object.peer_id != event.object.from_id:
                        # get user in russian
                        user = vk.method(
                            "users.get", {"user_ids": event.object.from_id, "lang": 0})

                        # manage variables
                        name = user[0]['first_name']
                        userId = event.object.from_id  # message sender
                        groupId = event.object.peer_id  # chat ID
                        print(groupId)
                        messageText = event.object.text  # message body

                        # region debug
                        print(f"Message sender: {userId}")
                        print(f"Message sender name: {name}")
                        # print(event.object)
                        # endregion

                        # photo test
                        if '!cringepic' in messageText.lower():
                            # send photo
                            send_message_attachement(
                                groupId, "this pic is so cringe", random.choice(PHOTOS))

                        # debug
                        elif '!debug' in messageText.lower():
                            send_message(groupId, "debugreply")

                        # promote
                        elif '!promote' in messageText.lower():
                            authenticate_and_execute(userId, promote_action, [
                                userId, messageText, groupId], groupId)

                        # demote
                        elif '!demote' in messageText.lower():
                            authenticate_and_execute(userId, demote_action, [
                                userId, messageText, groupId], groupId)

                        # nuke
                        elif '!nuke' in messageText.lower():
                            nuke_action(userId, groupId)

                        # showid
                        elif '!showid' in messageText.lower():
                            send_message(groupId, f"your id: {userId}")

                        # showadmin
                        elif '!showadmin' in messageText.lower():
                            showadmin_action(groupId)

                        # region spaghetti code, open at own risk
                        # write to directory
                        elif event.object["attachments"] != []:
                            attachments = event.object["attachments"]
                            if attachments[0]["type"] == "audio_message":
                                audio_message = attachments[0]["audio_message"]
                                url = audio_message["link_mp3"]
                                r = requests.get(url, allow_redirects=True)
                                # replace illegal characters
                                localname = f'{event.object["date"]};{userId};{get_full_name(userId)};{audio_message["link_mp3"].replace("/", "$").replace(":", "@").replace("?", "#")};amsg.mp3'
                                open(f'{AUDIO_FILES_DIR}/{localname}', 'wb').write(
                                    r.content)  # date;owner_id;owner_name;link_mp3
                                print("Wrote audio file")

                                af = None

                                fl = False
                                if len(AUDIO_FILES_LIST) > 0:
                                    if AUDIO_FILES_LIST[0].index != 0:
                                        af = make_AudioFile_from_path(
                                            f'{AUDIO_FILES_DIR}/{localname}', 0)
                                        AUDIO_FILES_LIST.insert(0, af)
                                        fl = True
                                    else:
                                        for i in range(len(AUDIO_FILES_LIST) - 1):
                                            if AUDIO_FILES_LIST[i+1].index - AUDIO_FILES_LIST[i].index != 1:
                                                af = make_AudioFile_from_path(
                                                    f'{AUDIO_FILES_DIR}/{localname}', i+1)
                                                AUDIO_FILES_LIST.insert(
                                                    i+1, af)
                                                fl = True
                                                break
                                if fl == False:
                                    af = make_AudioFile_from_path(
                                        f'{AUDIO_FILES_DIR}/{localname}', len(AUDIO_FILES_LIST))
                                    AUDIO_FILES_LIST.append(af)
                                send_message(
                                    groupId, f"Got audio message. Wrote to storage, index: {af.index}")
                            # elif attachments[0]["type"] == "audio":
                            #     audio = attachments[0]["audio"]
                            #     if len(audio["url"]) > 0:
                            #         url = audio["url"]
                            #         r = requests.get(url, allow_redirects=True)
                            #         # replace illegal characters
                            #         # links for music on vk are too long
                            #         localname = f'{event.object["date"]};{userId};{get_full_name(userId)};{"https://www.youtube.com/watch?v=dQw4w9WgXcQ".replace("/", "$").replace(":", "@").replace("?", "#")};{audio["title"]} by {audio["artist"]}.mp3'
                            #         open(f'{AUDIO_FILES_DIR}/{localname}', 'wb').write(
                            #             r.content)  # date;owner_id;owner_name;url
                            #         print("Wrote audio track")
                            #         AUDIO_FILES_LIST.append(make_AudioFile_from_path(
                            #             f'{AUDIO_FILES_DIR}/{localname}'))
                            #         send_message(
                            #             groupId, f"Got audio track. Wrote to storage. localname: {localname}")
                            #     else:
                            #         print("Failed to get audio track, no link embedded.")
                            #         send_message(
                            #             groupId, "Failed to get audio track, no link embedded.")
                        # endregion

                        # showaudiofiles
                        elif '!showaudiofiles' in messageText.lower() or '!showaf' in messageText.lower() or '!saf' in messageText.lower():
                            showaudiofiles_action(groupId)

                        # scheduleplaybacktimer
                        elif '!scheduleplaybacktimer' in messageText.lower() or '!spbt' in messageText.lower():
                            schedulepbt_action(userId, messageText,
                                               groupId, event.object)

                        # scheduleplayback
                        elif '!scheduleplayback' in messageText.lower() or '!spb' in messageText.lower():
                            schedulepb_action(userId, messageText,
                                              groupId, event.object)

                        # showschedule
                        elif '!showschedule' in messageText.lower() or '!ss' in messageText.lower():
                            showschedule_action(groupId)

                        # deleteaf
                        elif '!deleteaudiofile' in messageText.lower() or '!daf' in messageText.lower():
                            deleteaf_action(userId, messageText, groupId)

                        # deletetask
                        elif '!deletetask' in messageText.lower() or '!dt' in messageText.lower():
                            deletetask_action(userId, messageText, groupId)

                        # ttstimed
                        elif '!ttstimed' in messageText.lower() or '!ttst' in messageText.lower():
                            pass

                        # tts
                        elif '!tts' in messageText.lower():
                            tts_action(userId, messageText, groupId)

                        # setvolume
                        elif '!setvolume' in messageText.lower() or '!sv' in messageText.lower():
                            setvolume_action(userId, messageText, groupId)

                        # status
                        elif '!status' in messageText.lower():
                            status_action(userId, messageText, groupId)

                        # quit
                        elif messageText.lower() == '!quit':
                            authenticate_and_execute(
                                userId, quit_action, [groupId], groupId, True)

                        # help
                        elif '!help' in messageText.lower():
                            send_message(groupId, HELP_MESSAGE)

                        # crash
                        elif '!crashvklp' in messageText.lower():
                            send_message(groupId, "crashing...")
                            a = 1/0  # wtf is this

                        elif '!crashslck' in messageText.lower():
                            send_message(groupId, "crashing...")
                            debug_flag = True

                    # to answer DMS
                    elif event.object.peer_id == event.object.from_id:
                        send_message(event.object.from_id, GREETING)
                        # successfully sent message to individual
                        print(f"replied to DM")
        except Exception as ex:
            send_message(
                groupId, f"FATAL ERROR: {ex}. vk_longpoll_loop_thread dead!! attempting restart...")
            vk_longpoll_loop_flag = False
            reset()
            vk_longpoll_loop_thread = tr.Thread(
                target=vk_longpoll_loop, args=())
            vk_longpoll_loop_thread.start()
            return


# endregion
print("############### <log start> ###############")
startup()

schedule_clock_thread = tr.Thread(target=schedule_clock, args=())
schedule_clock_thread.start()
vk_longpoll_loop_thread = tr.Thread(target=vk_longpoll_loop, args=())
vk_longpoll_loop_thread.start()
