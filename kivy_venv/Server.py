from threading import Event
import socket
import threading
import cv2
import pickle
import struct
import time
import numpy as np
import math
import netifaces as ni


class Server:

    def __init__(self):
        """
        Initializeaza Serverul
        """
        self.CLIENT_IP = ''
        self.IP = self.get_ip_address()
        self.PORT = self.chekc_ports(self.IP)
        self.ADDR = (self.IP, self.PORT)
        self.HEADER = 1024
        self.FORMAT = "utf-8"
        self.DISCONNECT_MESSAGE = "DISC"
        self.CLIENTS = []
        self.STATUS = 0

        self.send_event = Event()
        self.play_event = Event()
        self.play_event.set()
        self.decode_event = Event()
        self.foreword_and_backward_event = Event()
        self.VIDEO_FRAME_DECODED = []

        self.VIDEO_FRAME = []
        self.COUNT_FRAME = 0
        self.WIDTH = 0
        self.HEIGHT = 0
        self.WIDTH_POS = 0
        self.HEIGHT_POS = 0
        self.FPS = 0
        self.PLAY_STATE = False

        self.video_play_thread = threading.Thread()
        self.recive_state = 0

        self.min_dec_frame = 1000
        self.max_dec_frame = 0
        self.med_dec_frame = 0
        self.count_dec_frames = 0

    def get_ip_address(self):
        """
        Preia adresa IP a Raspberry Pi.
        """
        interfaces = ni.interfaces()
        for interface in interfaces:
            if interface == 'lo':
                continue
            addresses = ni.ifaddresses(interface)
            if ni.AF_INET in addresses:
                ip_address = addresses[ni.AF_INET][0]['addr']
                return ip_address

    def chekc_ports(self, ip):
        """
        Verifica porturile disponibile.
        """
        free_ports = []
        start_port = 0
        end_port = 10000
        for port in range(end_port, start_port, -1):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind((ip, port))
                next = port-1
                if next >= start_port:
                    try:
                        sock = socket.socket(
                            socket.AF_INET, socket.SOCK_STREAM)
                        sock.bind((ip, next))
                        free_ports.append(port)
                        free_ports.append(next)
                        if len(free_ports) == 2:
                            print(port)
                            return port
                    except socket.error as e:
                        pass
                    finally:
                        sock.close()
            except socket.error as e:
                pass
            finally:
                sock.close()

    def start(self):
        """
        Metoda care se ocupa cu acceptarea clientilor.
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(self.ADDR)
        print(f"STARTING at {self.ADDR}")

        server.listen()
        while True:
            client_conn, client_addr = server.accept()
            self.CLIENTS.append((client_conn, client_addr))
            thread = threading.Thread(
                target=self.handel_client, args=(client_conn, client_addr))
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count()-1}")

    def handel_client(self, conn, addr):
        """
        Metoda care se ocupa cu gestionarea clientilor.
        """
        if (conn, addr) != self.CLIENTS[0]:
            conn.send(f"BUSY".encode(self.FORMAT))
            conn.close()
            self.CLIENTS.pop(0)
        else:
            print(f"[NEW CONNECTION] {addr} connected.")
            self.CLIENT_IP = addr[0]
            conn.send(f"OK".encode(self.FORMAT))
            time.sleep(0.1)
            conn.send(f"{self.CLIENT_IP}".encode(self.FORMAT))
            connected = True
            while connected:
                try:
                    msg = conn.recv(self.HEADER).decode(self.FORMAT)
                    if msg == "START_SHARING":
                        print("START_SHARING", msg)
                        video_recv_thread = threading.Thread(
                            target=self.video_recv, args=())
                        self.send_event.clear()
                        video_recv_thread.start()
                        self.COUNT_FRAME = 0
                        decode_img_thread = threading.Thread(
                            target=self.decode, args=())
                        self.decode_event.clear()
                        decode_img_thread.start()

                    elif msg == "DISCONNECT":
                        print("DISCONNECT", msg)
                        time.sleep(1)
                        self.send_event.set()
                        self.play_event.set()
                        self.decode_event.set()
                        self.COUNT_FRAME = 0
                        self.VIDEO_FRAME = []
                        connected = False
                    elif msg == "PLAY":
                        print(msg)
                        if self.play_event.is_set():
                            self.play_event.clear()
                            if not self.video_play_thread.is_alive():
                                self.video_play_thread = threading.Thread(
                                    target=self.video_play, args=())
                                self.video_play_thread.start()

                            self.PLAY_STATE = True
                    elif msg == 'PAUSE':
                        self.play_event.set()
                        print(msg)
                    elif msg == 'BACKWARD':
                        self.video_backward()
                        print(msg)
                    elif msg == 'FORWARD':
                        self.video_forward()
                        print(msg)
                    else:
                        print(msg)
                        conn.send(f"you sent {msg}".encode(self.FORMAT))

                except Exception as e:
                    print(e)
                    connected = False
            conn.close()
            self.CLIENTS.pop(0)
            self.VIDEO_FRAME_DECODED = []
            self.COUNT_FRAME = 0
            print('CONNECTION CLOSE')

    def video_recv(self):
        """
        Se conecteaza la client si proceseaza datele video.
        """
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print((self.CLIENT_IP, (self.PORT-1)))
        client_socket.connect((self.CLIENT_IP, (self.PORT-1)))
        self.FPS = math.ceil(float(client_socket.recv(
            self.HEADER).decode(self.FORMAT)))
        self.WIDTH = int(float(client_socket.recv(
            self.HEADER).decode(self.FORMAT)))
        self.HEIGHT = int(float(client_socket.recv(
            self.HEADER).decode(self.FORMAT)))
        self.WIDTH_POS = int(960-(self.WIDTH/2))
        self.HEIGHT_POS = int(540-(self.HEIGHT/2))
        print(
            f'frames per second = {self.FPS} , {self.WIDTH} - {self.HEIGHT } , {self.WIDTH_POS} - {self.HEIGHT_POS}')
        data = b""
        payload_size = struct.calcsize("Q")
        try:
            self.recive_state = 1
            while True:
                if self.send_event.is_set():
                    print('The thread was stopped prematurely.')
                    client_socket.close()
                    break
                while len(data) < payload_size:
                    packet = client_socket.recv(4*1024)
                    if not packet:
                        break
                    data += packet
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q", packed_msg_size)[0]

                while len(data) < msg_size:
                    data += client_socket.recv(4*1024)
                frame_data = data[:msg_size]
                data = data[msg_size:]

                self.VIDEO_FRAME.append(frame_data)

            time.sleep(0.1)

        except Exception as e:
            print(e)
            print(f'Connectoin {(self.IP, (self.PORT-1))} close')
        finally:
            print(f'Connectoin {(self.IP, (self.PORT-1))} close')

        client_socket.close()
        self.recive_state = 0

    def decode(self):
        """
        Metoda care decodeaza cadrele din .jpg in frame-uri row.
        """
        time.sleep(1)
        count = 0
        while True:
            if self.decode_event.is_set():
                print('STOP DECODE')
                break

            if len(self.VIDEO_FRAME) > 250:
                if self.foreword_and_backward_event.is_set():
                    self.foreword_and_backward_event.clear()
                    count = self.COUNT_FRAME
                    c = 0
                    self.VIDEO_FRAME_DECODED = []
                    frame_count = 0
                    start_time = time.time()
                    while len(self.VIDEO_FRAME_DECODED) < 250:
                        if (count == len(self.VIDEO_FRAME)) and (self.recive_state == 0):
                            break
                        try:
                            if self.foreword_and_backward_event.is_set() or self.decode_event.is_set():
                                print('STOP DECODE 11111111')
                                break
                            else:
                                frame = pickle.loads(self.VIDEO_FRAME[count])
                                frame = cv2.imdecode(frame, 1)
                                self.VIDEO_FRAME_DECODED.insert(c, frame)
                                count += 1
                                c += 1
                                frame_count += 1
                                elapsed_time = time.time() - start_time
                                if elapsed_time >= 1.0:
                                    print(
                                        "Cadre decodate intr-o secunda: ", frame_count)
                                    self.countDecFrames(frame_count)
                                    frame_count = 0
                                    start_time = time.time()
                        except Exception as e:
                            print(e)
                else:
                    frame_count = 0
                    start_time = time.time()
                    while len(self.VIDEO_FRAME_DECODED) < 250:
                        if (count == len(self.VIDEO_FRAME)) and (self.recive_state == 0):
                            break
                        try:
                            if self.foreword_and_backward_event.is_set() or self.decode_event.is_set():
                                print('STOP DECODE 2222222222')
                                break
                            else:
                                frame = pickle.loads(self.VIDEO_FRAME[count])
                                frame = cv2.imdecode(frame, 1)
                                self.VIDEO_FRAME_DECODED.append(frame)
                                count += 1
                                frame_count += 1
                                elapsed_time = time.time() - start_time
                                if elapsed_time >= 1.0:

                                    print(
                                        "Cadre decodate intr-o secunda: ", frame_count)
                                    self.countDecFrames(frame_count)

                                    frame_count = 0
                                    start_time = time.time()
                        except Exception as e:
                            print(count, e)
    
    def countDecFrames(self, dec_frame_count):
        
        self.count_dec_frames += 1
        self.med_dec_frame += dec_frame_count

        if dec_frame_count < self.min_dec_frame :
            self.min_dec_frame = dec_frame_count
        
        if dec_frame_count > self.max_dec_frame :
            self.max_dec_frame = dec_frame_count
    

    def video_play(self):
        """
        Metoda care initializeaza playerul si reda videoclipul.
        """
        fps, st, frames_to_count, cnt = (0, 0, 24, 0)
        cv2.namedWindow("RECEIVING VIDEO", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(
            "RECEIVING VIDEO", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.moveWindow("RECEIVING VIDEO", self.WIDTH_POS, self.HEIGHT_POS)
        cv2.resizeWindow("RECEIVING VIDEO", self.WIDTH, self.HEIGHT)
        frame = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)
        while True:
            if (self.COUNT_FRAME == len(self.VIDEO_FRAME)) and (self.recive_state == 0):
                break
            # start_time = time.time()
            if self.send_event.is_set():
                print('you disconected')
                break

            if self.play_event.is_set():
                try:
                    frame = frame
                except:
                    pass
            else:
                try:
                    frame = self.VIDEO_FRAME_DECODED.pop(0)
                    self.COUNT_FRAME += 1
                except IndexError:
                    try:
                        frame = frame
                    except:
                        pass
                except Exception as e:
                    print(e)

            frame = cv2.putText(frame, 'FPS: '+str(fps), (10, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.imshow("RECEIVING VIDEO", frame)

            if cv2.waitKey(20) & 0xFF == ord('q'):
                break

            if cnt == frames_to_count:
                try:
                    fps = round(frames_to_count/(time.time()-st))
                    st = time.time()
                    cnt = 0
                except:
                    pass
            cnt += 1
            # end_time = time.time()  # Record the end time
            # execution_time = end_time - start_time
            # Calculate the difference
            # print(execution_time, " exec - secounds")
            # try:
            #     time.sleep((1 / self.FPS)-(execution_time))
            #     # cv2.waitKey(int((1000 / self.FPS+3)-(execution_time*1000)))
            #     end_t = time.time()  # Record the end time
            #     execution_t = end_t - start_time
            #     # print(
            #     #     f"whole {execution_t} seconds {(1 / self.FPS)-(execution_time)}")
            # except Exception as e:
            #     print(e)

        cv2.destroyAllWindows()
        print(f"Min : {self.min_dec_frame} FPS_decoded")
        print(f"Max : {self.max_dec_frame} FPS_decoded")
        media = self.med_dec_frame/ self.count_dec_frames
        print(f"Med : {media} FPS_decoded")

    def video_backward(self):
        """
        Metoda cu care ne putem deplasa prin videoclip inapoi.
        """
        if self.COUNT_FRAME > 241:
            print(self.COUNT_FRAME)
            self.COUNT_FRAME -= 240
            self.foreword_and_backward_event.set()
        else:
            self.COUNT_FRAME = 0
            self.foreword_and_backward_event.set()

    def video_forward(self):
        """
        Metoda cu care ne putem deplasa prin videoclip inainte.
        """
        if (len(self.VIDEO_FRAME) - self.COUNT_FRAME) > 241:
            print(self.COUNT_FRAME)
            self.COUNT_FRAME += 240
            self.foreword_and_backward_event.set()
        else:
            self.COUNT_FRAME = self.VIDEO_FRAME[-1]
            self.foreword_and_backward_event.set()


if __name__ == '__main__':

    Server().start()
