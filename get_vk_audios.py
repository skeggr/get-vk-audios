import requests
import shutil
from tkinter import Button, Label, Text, Listbox, Entry
from tkinter import TclError, Tk
from tkinter import filedialog, messagebox
from tkinter import EXTENDED, END
from tkinter import ttk
import os
import re
import threading
import webbrowser

# https://api.vk.com/method/'''METHOD_NAME'''?'''PARAMETERS'''&access_token='''ACCESS_TOKEN'''


class Track(object):
    def __init__(self, artist, title, url):
        self.artist = artist
        self.title = title
        self.url = url

    def get_full_name(self):
        return self.artist + ' - ' + self.title


class App(Tk):
    def __init__(self):
        super().__init__()
        self.geometry('385x790')
        self.resizable(False, False)
        self.title('Get_VK_Audios')
        self.btn_get_token = Button(text='Получить токен', command=lambda: threader(get_token))
        self.oauth_lbl = Label(justify='left', text='Скопируйте ссылку из строки браузера в поле ниже:')
        self.oauthtext = Text(height=3, width=35)
        self.owner_lbl = Label(justify='left', text='ID страницы (по-умолчанию - ваш):')
        self.owner_entry = Entry()
        self.btn_get_tracks = Button(text='Получить список треков', command=lambda: self.fill_listbox(self.oauthtext.\
                                                                                            get(0.0, END).strip()))
        self.btn_sort = Button(text='Сортировать', command=self.sort_tracklist)
        self.btn_select_all = Button(text='Выбрать все', command=lambda: self.list_tracks.selection_set(0, END))
        self.list_tracks = Listbox(height=14, width=45, selectmode=EXTENDED)
        self.count_lbl = Label(justify='left', text='Доступно: {0}'.format(self.list_tracks.size()))
        self.path_entry = Entry(width=43)
        self.path_lbl = Label(justify='left', text='Путь для сохранения аудиозаписей:')
        self.choose_btn = Button(text='Выбрать', height=1, command=self.opendialog)
        self.btn_start = Button(text='Начать', command=lambda: threader(self.save_tracks))
        self.prgs_bar = ttk.Progressbar(length=350)
        self.prgs_info = Label(justify='center', text=' ')
        self.btn_get_token.grid(pady=10, columnspan=3)
        self.oauth_lbl.grid(padx=10, columnspan=3)
        self.oauthtext.grid(padx=10, columnspan=3, sticky='w')
        self.owner_lbl.grid(padx=10, pady=5, columnspan=3, sticky='w')
        self.owner_entry.grid(padx=10, columnspan=3, sticky='w')
        self.btn_get_tracks.grid(pady=10, columnspan=3)
        self.list_tracks.grid(padx=10, pady=5, columnspan=3, sticky='w')
        #TODO
        #self.count_lbl.grid(padx=10, pady=5, sticky='w')
        self.btn_sort.grid(padx=10, pady=5, row=7, column=0, sticky='w')
        self.btn_select_all.grid(column=1, sticky='e', row=7)
        self.path_lbl.grid(padx=10, columnspan=3, sticky='w')
        self.path_entry.grid(padx=10, pady=10, column=0, columnspan=2, sticky='w', row=10)
        self.choose_btn.grid(row=10, column=1, sticky='e')
        self.btn_start.grid(pady=10, columnspan=3)
        self.prgs_bar.grid(padx=5, columnspan=3)
        self.prgs_info.grid(columnspan=3)

    def opendialog(self):
        self.path_entry.delete(0, END)
        self.path_entry.insert(0, os.path.normpath(filedialog.askdirectory()))

    def sort_tracklist(self):
        self.list_tracks.delete(0, END)
        global tracklist
        for name in sorted([tr.get_full_name() for tr in tracklist]):
            self.list_tracks.insert(END, name)

    def check_owner(self, owner):
        new_owner = self.owner_entry.get().strip()
        if new_owner:
            return new_owner
        else:
            return owner

    def fill_listbox(self, link):
        if link:
            auth_info = parse_link(link)
            global tracklist
            tracklist = list(get_audio(token=auth_info[0], owner_id=self.check_owner(auth_info[1])))
            self.list_tracks.delete(0, END)
            for track in tracklist:
                self.list_tracks.insert(END, track.get_full_name())
            #TODO
            #self.count_lbl.configure(text='Доступно: {0}'.format(self.list_tracks.size()))
        else:
            messagebox.showerror(title='Ошибка', message='Сначала нужно получить токен и скопировать ссылку в поле')

    def save_tracks(self):
        global tracklist
        try:
            selected = self.list_tracks.selection_get().split(sep='\n')
            sel_count = len(selected)
        except TclError:
            messagebox.showerror(title='Ошибка', message='Не выбрано ни одного трека')
            return 1
        self.btn_start.configure(state='disabled')
        num = 0
        err = 0
        self.prgs_info.configure(text='Обработано: {0} из {1}. Ошибок: {2}'.format(num, sel_count, err))
        self.prgs_bar.configure(value=0, maximum=sel_count, mode='determinate')
        for track in tracklist:
            if track.get_full_name() in selected:
                resp = requests.get(track.url, stream=True)
                if resp.status_code == 200:
                    try:
                        with open(os.path.normpath(os.path.join(self.path_entry.get(), track.get_full_name() + '.mp3')),
                                  'wb') as file:
                            resp.raw.decode_content = True
                            shutil.copyfileobj(resp.raw, file)
                    except OSError:
                        print('Не удалось сохранить ' + track.get_full_name())
                        err += 1
                num += 1
                self.prgs_info.configure(text='Скачано {0} из {1}. Ошибок: {2}'.format(num, sel_count, err))
                self.prgs_bar.step()
        self.btn_start.configure(state='active')


def get_audio(**kwargs):
    audios = requests.get('https://api.vk.com/method/audio.get?v=5.50&count=600&owner_id={0}&access_token={1}'.format(kwargs['owner_id'], kwargs['token'])).json()['response']
    for track in audios['items']:
        yield Track(artist=track['artist'], title=track['title'], url=track['url'])


def threader(targ):   # запуск функции в отдельном процессе
    thr = threading.Thread(target=targ)
    thr.daemon = True
    thr.start()


def get_token():
    oauthlink = 'https://oauth.vk.com/authorize?client_id='+\
                '{0}&display={1}&redirect_uri={2}&scope={3}&response_type={4}&v={5}'.format(CL_ID, DISP, REDIR_URI, SCOPE, RESP_TYPE, VER)
    webbrowser.open(oauthlink)


def parse_link(link):
    parsed = re.split('#|&', link.strip())  # разбиваем ссылку на "параметр=значение"
    return re.split('=', parsed[1])[1], re.split('=', parsed[3])[1]  # разбиваем ещё раз, и возвращаем только значения


if __name__ == '__main__':
    CL_ID = '5289180'
    DISP = 'page'
    REDIR_URI = 'https://oauth.vk.com/blank.html'
    SCOPE = 'audio'
    RESP_TYPE = 'token'
    VER = '5.50'
    tracklist = []
    root = App()
    root.mainloop()
