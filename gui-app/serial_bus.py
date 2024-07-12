#!/usr/bin/env python3 -m main

import threading
import logging
import serial
from serial.tools import list_ports
import queue as Queue

def get_ports():
    ports = []
    for comport in list_ports.comports():
        port = comport[0]
        if ((port.startswith('/dev/tty') and (port.find('ACM') or port.find('USB'))) or
            port.startswith('COM') or
            port.startswith('/dev/cu.')):
            ports.append(port)
    ports.sort()
    return ports

PARITY_DICT = {'None': serial.PARITY_NONE, 'Even': serial.PARITY_EVEN,
               'Odd': serial.PARITY_ODD, 'Mask': serial.PARITY_MARK,
               'Space': serial.PARITY_SPACE}

class SerialBus(object):

    def __init__(self, on_received, on_failed):
        self.notify = on_received
        self.warn = on_failed

        self.tx_queue = Queue.Queue()
        self.rx_queue = Queue.Queue()
        self.serial = None
        self.tx_thread = None
        self.rx_thread = None

        self.stop_event = threading.Event()

    def start(self, port, baud, bytesize, stopbits, parity):
        if self.serial:
            self.serial.close()

        try:
            self.serial = serial.Serial(port=port,
                                        baudrate=baud,
                                        bytesize=bytesize,
                                        stopbits=stopbits,
                                        parity=PARITY_DICT[parity],
                                        timeout=0.2)
            self.tx_queue.queue.clear()
            self.rx_queue.queue.clear()
            self.stop_event.set()
            self.tx_thread = threading.Thread(target=self._send)
            self.rx_thread = threading.Thread(target=self._recv)
            self.stop_event.clear()
            self.tx_thread.start()
            self.rx_thread.start()

        except IOError as e:
            logging.warning(e)
            self.warn()

    def join(self):
        self.stop_event.set()
        if self.tx_thread:
            self.tx_thread.join()
            self.rx_thread.join()

        if self.serial:
            self.serial.close()

    def write(self, data):
        self.tx_queue.put(data)

    def read(self):
        return self.rx_queue.get()

    def _send(self):
        logging.info('tx thread is started')
        while not self.stop_event.is_set():
            try:
                data = self.tx_queue.get(True, 1)
                logging.info('tx:' + data)
                self.serial.write(data.encode())
            except Queue.Empty:
                continue
            except IOError as e:
                logging.warning(e)
                self.serial.close()
                self.stop_event.set()
                self.warn()

        logging.info('tx thread exits')

    def _recv(self):
        logging.info('rx thread is started')
        while not self.stop_event.is_set():
            try:
                data = self.serial.read(1024)

                if data and len(data) > 0:
                    data = data.decode('utf-8', 'replace')
                    logging.info('rx:' + data)
                    self.rx_queue.put(data)
                    if self.notify:
                        self.notify()
            except IOError as e:
                logging.warning(e)
                self.serial.close()
                self.stop_event.set()
                self.warn()

        logging.info('rx thread exits')

# The MIT License (MIT)
#
# Copyright (c) 2015 Yihui Xiong
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Source: https://github.com/xiongyihui/pqcom