from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatIconButton
from kivymd.uix.textfield import MDTextField
from kivy.utils import platform
from plyer import filechooser
from threading import Event
import threading
import socket
import time
import re
import os
import cv2
import imutils
import pickle
import struct


class MyApp(MDApp):
    """
    Clasa pentru interfata grafica.
    """

    def __init__(self, **kwargs):
        """
        initializarea clasei
        """
        super().__init__(**kwargs)
        self.client = 0
        self.status = 0
        self.path = ""

    def build(self):
        """
        Crearea interfetei grafice
        """

        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.accent_palette = "Cyan"
        self.theme_cls.material_style = "M3"

        screen = MDScreen()
        self.BoxLayout = MDBoxLayout(orientation='vertical')
        screen.add_widget(self.BoxLayout)

        self.BoxLayout.add_widget(MDTopAppBar(
            title="My Cast App",
            anchor_title="center",
            pos_hint={'top': 1}))

        self.BottomNavigation = MDBottomNavigation()
        self.BoxLayout.add_widget(self.BottomNavigation)

        self.FileChooser = MDBottomNavigationItem(
            name="screen 1",
            text='File',
            icon='file-video')

        self.FileChooser.add_widget(MDLabel(
            text='Choose the file you want to share',
            halign='center',
            pos_hint={'center_x': 0.5, 'center_y': 0.75},
            theme_text_color="Secondary"))

        self.PathLabel = MDLabel(
            text='',
            halign='center',
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            theme_text_color="Secondary")
        self.FileChooser.add_widget(self.PathLabel)

        self.FileChooser.add_widget(MDRaisedButton(
            text='Choose File',
            md_bg_color='gray',
            halign='center',
            size_hint=(0.4, 0.05),
            pos_hint={'center_x': 0.5, 'center_y': 0.25},
            theme_text_color="Secondary",
            on_release=self.file_chooser
        ))

        self.BottomNavigation.add_widget(self.FileChooser)

        self.PlayerButtons = MDBottomNavigationItem(
            name="screen 2",
            text='Player',
            icon='video-box')

        self.PlayerButtons.add_widget(MDRaisedButton(
            text='Start Sharing',
            md_bg_color='gray',
            halign='center',
            size_hint=(0.8, 1),
            size_hint_x=1,
            size_hint_y=None,
            height=50,
            pos_hint={'center_x': 0.5, 'center_y': 0.1},
            theme_text_color="Secondary",
            on_press=lambda obj: self.button_function(obj, 'START_SHARING')
        ))
        self.PlayerButtons.add_widget(MDRectangleFlatIconButton(
            icon='play',
            text="play",
            theme_icon_color="Custom",
            icon_color="orange",
            text_color="white",
            md_bg_color='gray',
            halign='center',
            size_hint=(0.25, 0.05),
            pos_hint={'center_x': 0.3, 'center_y': 0.3},
            theme_text_color="Secondary",
            on_press=lambda obj: self.button_function(obj, 'PLAY')
        ))
        self.PlayerButtons.add_widget(MDRectangleFlatIconButton(
            icon='pause',
            text="pause",
            theme_icon_color="Custom",
            icon_color="orange",
            text_color="white",
            md_bg_color='gray',
            halign='center',
            size_hint=(0.25, 0.05),
            pos_hint={'center_x': 0.7, 'center_y': 0.3},
            theme_text_color="Secondary",
            on_press=lambda obj: self.button_function(obj, 'PAUSE')
        ))
        self.PlayerButtons.add_widget(MDRectangleFlatIconButton(
            icon="rewind-10",
            text="backward",
            theme_icon_color="Custom",
            icon_color="orange",
            text_color="white",
            md_bg_color='gray',
            halign='center',
            size_hint=(0.25, 0.05),
            pos_hint={'center_x': 0.3, 'center_y': 0.7},
            theme_text_color="Secondary",
            on_press=lambda obj: self.button_function(obj, 'BACKWARD')
        ))
        self.PlayerButtons.add_widget(MDRectangleFlatIconButton(
            icon="fast-forward-10",
            text="forward",
            theme_icon_color="Custom",
            icon_color="orange",
            text_color="white",
            md_bg_color='gray',
            halign='center',
            size_hint=(0.25, 0.05),
            pos_hint={'center_x': 0.7, 'center_y': 0.7},
            theme_text_color="Secondary",
            on_press=lambda obj: self.button_function(obj, 'FORWARD')
        ))
        self.BottomNavigation.add_widget(self.PlayerButtons)

        self.RaspberyConnection = MDBottomNavigationItem(
            name="screen 3",
            text='Connect',
            icon='lan-connect')

        self.RaspberyConnection.add_widget(MDLabel(
            text='Raspberry Pi - Connection',
            halign='center',
            pos_hint={'center_x': 0.5, 'center_y': 0.8},
            theme_text_color="Secondary"))

        self.IP = MDTextField(
            halign="center",
            size_hint=(0.8, 1),
            mode='round',
            max_text_length=15,
            font_size=18,
            hint_text="IP Address",
            pos_hint={'center_x': 0.5, 'center_y': 0.6})

        self.RaspberyConnection.add_widget(self.IP)

        self.PORT = MDTextField(
            halign="center",
            size_hint=(0.8, 1),
            mode='round',
            max_text_length=5,
            font_size=18,
            hint_text="Port",
            pos_hint={'center_x': 0.5, 'center_y': 0.4})

        self.RaspberyConnection.add_widget(self.PORT)

        self.RaspberyConnection.add_widget(MDRaisedButton(
            text='Connect',
            md_bg_color='gray',
            size_hint=(0.4, 0.05),
            halign='center',
            pos_hint={'center_x': 0.25, 'center_y': 0.2},
            theme_text_color="Secondary",
            on_press=self.connect))

        self.RaspberyConnection.add_widget(MDRaisedButton(
            text='Disconnect',
            md_bg_color='gray',
            size_hint=(0.4, 0.05),
            halign='center',
            pos_hint={'center_x': 0.75, 'center_y': 0.2},
            theme_text_color="Secondary",
            on_press=self.disconnect
        ))
        self.BottomNavigation.add_widget(self.RaspberyConnection)

        return screen

    def file_chooser(self, obj):
        """
        Deschide managerul de fisiere.
        """

        filechooser.open_file(on_selection=self.selected)
        print("""I AM ON FILE CHOOSER""")

    def selected(self, selection):
        """
        Selecteaza fisierul video.
        """

        if selection:
            self.path = selection[0]
            self.PathLabel.text = os.path.basename(self.path)
            print("""I AM ON SELECTED""")

    def button_function(self, obj, text):
        """
        Trimite informatiile primite de la interfata grafica
        si le trimite catre clasa ClinetConnection.
        """
        if self.status:
            if text == 'START_SHARING':
                if self.path != "":
                    print(self.client.file_in_transfer)
                    if self.client.file_in_transfer.is_alive():
                        toast("file allready in transfer")
                    else:
                        try:
                            self.client.send_button_function(text)
                            self.client.file_in_transfer = threading.Thread(
                                target=self.client.send_video, args=(self.path, self.PathLabel.text, self.client.event))
                            self.client.file_in_transfer.start()
                        except Exception as e:
                            toast(f"Choose a corect file.\n {e}")
                else:
                    toast("Path to file not selected.")
            else:
                self.client.send_button_function(text)
                toast(text)
        else:
            toast("You are not connected.")

    def connect(self, obj):
        """
        Initializeaza conectarea de la server.
        """
        if self.status == 0:
            if re.match(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", self.IP.text) and re.match(r'^(?:[1-9]\d{0,4}|10000)$', self.PORT.text):
                print(self.IP.text, self.PORT.text)
                try:
                    self.client = ClientConnection(
                        self.IP.text, int(self.PORT.text))
                    a = self.client.start()
                    if a == "OK":
                        toast("Successfully Connected")
                        self.status = 1
                    elif a == "BUSY":
                        toast('Someone is presenting now')
                        self.client.CLIENT.close()
                        del self.client

                    else:
                        toast("the ip adress is not corect")
                        self.client.CLIENT.close()
                        del self.client

                except Exception as e:
                    print(e)
                    toast(
                        f"Could not conect to {self.IP.text}. Make sure it is the write one.")
            else:
                toast("Invalid Port or Ip Address")
        else:
            toast("Alredy Connected")

    def disconnect(self, *obj):
        """
        Initializeaza deconectarea de la server.
        """
        if self.status == 1:
            self.client.send_button_function("DISCONNECT")
            self.client.event.set()
            print(self.client.file_in_transfer)
            self.client.CLIENT.close()
            del self.client
            self.status = 0
            toast("Disconnected")
        else:
            toast("You are not connected")


class ClientConnection:
    """
    Clasa responsabila cu trimiterea datelor catre server.
    """

    def __init__(self, IP, PORT):
        """Initializarea clasei"""
        self.MY_IP = ''
        self.IP = IP
        self.PORT = PORT
        self.ADDR = (self.IP, self.PORT)
        self.HEADER = 1024
        self.FORMAT = "utf-8"
        self.STATUS = 0
        self.CLIENT = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file_in_transfer = threading.Thread()
        self.event = Event()

    def start(self):
        '''
        Metoda de conectare la server.
        '''
        self.CLIENT.connect(self.ADDR)
        self.CLIENT.settimeout(1)
        msg = self.CLIENT.recv(self.HEADER).decode(self.FORMAT)
        if msg == "OK":
            self.MY_IP = self.CLIENT.recv(self.HEADER).decode(self.FORMAT)
            print("STARTING")
            recv_thread = threading.Thread(target=self.recv_msg)
            recv_thread.start()
            return msg
        if msg == "BUSY":
            return msg
        else:
            return 'NOT OK'

    def send_button_function(self, msg):
        """
        Metoda de trimitere a comenzilor.( start, stop...)
        """
        self.CLIENT.send(msg.encode(self.FORMAT))

    def recv_msg(self):
        """
        Metoda de receptionare a mesajelor.
        """
        try:
            connected = True
            self.CLIENT.setblocking(1)
            while connected:
                try:
                    msg = self.CLIENT.recv(self.HEADER).decode(self.FORMAT)
                    print(msg)
                except Exception as e:
                    connected = False
        except Exception as e:
            print(e)

    def send_video(self, path, title, event):
        """
        Metoda de trimitere a datelor video.
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print((self.MY_IP, (self.PORT-1)))
        server_socket.bind((self.MY_IP, (self.PORT-1)))
        server_socket.listen(1)
        print("LISTENING AT:", (self.MY_IP, (self.PORT-1)))
        client_socket, addr = server_socket.accept()
        print('GOT CONNECTION FROM:', addr)

        vid = cv2.VideoCapture(path)
        fps = vid.get(cv2.CAP_PROP_FPS)
        client_socket.send(str(fps).encode(self.FORMAT))
        time.sleep(0.1)
        width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        client_socket.send(str(width).encode(self.FORMAT))
        time.sleep(0.1)
        height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
        client_socket.send(str(height).encode(self.FORMAT))
        time.sleep(0.1)
        print(f'frames per second = {fps} , {width} - {height}')
        frame_count = 0
        start_time = time.time()
        try:
            if client_socket:
                while vid.isOpened():
                    if event.is_set():
                        event.clear()
                        client_socket.close()
                        print('The thread was stopped prematurely. 2')
                        break
                    img, frame = vid.read()
                    if img:
                        if width > 1920:
                            frame = imutils.resize(frame, width=1920)
                        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
                        _, encimg = cv2.imencode('.jpg', frame, encode_param)
                        if int(vid.get(cv2.CAP_PROP_POS_FRAMES)) == 500:
                            print(len(encimg))
                        a = pickle.dumps(encimg)

                        message = struct.pack("Q", len(a))+a

                        client_socket.sendall(message)

                        frame_count += 1

                        elapsed_time = time.time() - start_time
                        if elapsed_time >= 1.0:

                            print("FPS : ", frame_count)

                            frame_count = 0
                            start_time = time.time()
                    else:
                        break
                client_socket.close()
        except:
            client_socket.close()
            print(f'Connectoin close')

        print('disconected')
        client_socket.close()


if __name__ == '__main__':
    global a
    a = MyApp()
    a.run()
