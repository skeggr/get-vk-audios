import requests
import shutil
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import os
import re
import threading
from tkinter import ttk
import webbrowser

# https://api.vk.com/method/'''METHOD_NAME'''?'''PARAMETERS'''&access_token='''ACCESS_TOKEN'''

oauthlink = 'https://oauth.vk.com/authorize?client_id=5289180&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=friends,photos,audio&response_type=token&v=5.50'

def get_audio(**kwargs):
    audios = requests.get('https://api.vk.com/method/audio.get?v=5.50&count=600&owner_id={owner}&access_token={token}'.format(owner=kwargs['owner_id'], token=kwargs['token'])).json()['response']
    for track in audios['items']:
        yield track['artist'], track['title'], track['url']

def save_tracks():
    global tracklist
    try:
        selected = list_tracks.selection_get().split(sep='\n')
        sel_count = len(selected)
    except Exception:
        messagebox.showerror(title='Ошибка', message='Не выбрано ни одного трека')
        return 1
    btn_start.configure(state='disabled')
    num = 0
    prgs_info.configure(text='Скачано {number} из {count}'.format(number=num, count=sel_count))
    prgs_bar.configure(value=0, maximum=sel_count, mode='determinate')
    for track in tracklist:
        if track[0]+' - '+track[1] in selected:
            resp = requests.get(track[2], stream=True)
            if resp.status_code == 200:
                with open(os.path.normpath(os.path.join(path_entry.get(), track[0]+ ' - '+track[1]+'.mp3')), 'wb') as file:
                    resp.raw.decode_content = True
                    shutil.copyfileobj(resp.raw, file)
            num += 1
            prgs_info.configure(text='Скачано {number} из {count}'.format(number=num, count=sel_count))
            prgs_bar.step()
    btn_start.configure(state='active')

def threader(targ):   # запуск функции в отдельном процессе
    thr = threading.Thread(target=targ)
    thr.daemon = True
    thr.start()

def get_token():
    webbrowser.open(oauthlink)

def parse_link(link):
    parsed = re.split('#|&', link.strip())  # разбиваем ссылку на "параметр=значение"
    return re.split('=', parsed[1])[1], re.split('=', parsed[3])[1]  # разбиваем ещё раз, и возвращаем только значения

def check_owner(owner):
    new_owner = owner_entry.get().strip()
    if new_owner != '':
        return new_owner
    else:
        return owner

def fill_listbox(link):
    if link != '':
        auth_info = parse_link(link)
        global tracklist
        tracklist = list(get_audio(token=auth_info[0], owner_id=check_owner(auth_info[1])))
        list_tracks.delete(0, END)
        for track in tracklist:
            list_tracks.insert(END, track[0]+' - '+track[1])
    else:
        messagebox.showerror(title='Ошибка', message='Сначала нужно получить токен и скопировать ссылку в поле')

def opendialog():
    path_entry.delete(0, END)
    path_entry.insert(0, os.path.normpath(filedialog.askdirectory()))

def sort_tracklist():
    list_tracks.delete(0, END)
    tracklist.sort()
    for track in tracklist:
        list_tracks.insert(END, track[0]+' - '+track[1])

tracklist = []

root = Tk()
root.geometry('385x790')
root.resizable(False, False)
root.title('Get_VK_Audios')
btn_get_token = Button(root, text='Получить токен', command=lambda: threader(get_token))
oauth_lbl = Label(root, justify='left', text='Скопируйте ссылку из строки браузера в поле ниже:')
oauthtext = Text(root, height=3, width=35)
owner_lbl = Label(root, justify='left', text='ID страницы (по-умолчанию - ваш):')
owner_entry = Entry(root)
btn_get_tracks = Button(root, text='Получить список треков', command=lambda: fill_listbox(oauthtext.get(0.0, END).strip()))
btn_sort = Button(root, text='Сортировать', command=lambda: sort_tracklist())
btn_select_all = Button(root, text='Выбрать все', command=lambda: list_tracks.selection_set(0, END))
count_lbl = Label(root, justify='left', text='Выбрано: ')
list_tracks = Listbox(root, height=14, width=45, selectmode=EXTENDED)
path_entry = Entry(root, width=43)
path_lbl = Label(root, justify='left', text='Путь для сохранения аудиозаписей:')
choose_btn = Button(root, text='Выбрать', height=1, command=lambda: opendialog())
btn_start = Button(root, text='Начать', command=lambda: threader(save_tracks))
prgs_bar = ttk.Progressbar(root, length=350)
prgs_info = Label(root, justify='center', text=' ')
btn_get_token.grid(pady=10, columnspan=3)
oauth_lbl.grid(padx=10, columnspan=3)
oauthtext.grid(padx=10, columnspan=3, sticky='w')
owner_lbl.grid(padx=10, pady=5, columnspan=3, sticky='w')
owner_entry.grid(padx=10, columnspan=3, sticky='w')
btn_get_tracks.grid(pady=10, columnspan=3)
list_tracks.grid(padx=10, pady=5, columnspan=3, sticky='w')
btn_sort.grid(padx=10, pady=5, column=0, row=8, sticky='w')
btn_select_all.grid(row=8, column=1, sticky='w')
path_lbl.grid(padx=10, columnspan=3, sticky='w')
path_entry.grid(padx=10, pady=10, column=0, columnspan=2, sticky='w', row=10)
choose_btn.grid(row=10, column=1, sticky='e')
btn_start.grid(pady=10, columnspan=3)
prgs_bar.grid(padx=5, columnspan=3)
prgs_info.grid(columnspan=3)
root.mainloop()
