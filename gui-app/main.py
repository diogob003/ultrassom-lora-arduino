#!/usr/bin/env python3

import serial_bus
import os
import re
import signal
import sqlite3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, GObject
from matplotlib.ticker import PercentFormatter
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk4agg import FigureCanvas # gtk4cairo or gtk4agg
from matplotlib.backends.backend_gtk4 import NavigationToolbar2GTK4 as NavigationToolbar

class convert_to_dot_notation(dict):
    """ Access dictionary attributes via dot notation """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, self.quit) ## Handle SIGINT / ctrl + c
        self.serial = serial_bus.SerialBus(self.notify_data_received, self.on_serial_failed)
        GObject.signal_new("data_received", self, GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, ())
        self.connect("data_received", self.on_data_received)
        self.connect("activate", self.on_activate)
        self.connect("shutdown", self.on_quit_shutdown)
        self.level_history = []
        self.options = convert_to_dot_notation({
            "serial_port": "/dev/cu.SLAB_USBtoUART",
            "sqlite3db": "fluid_level_history.sqlite3",
            "baud_rate": 9600,
            "bytesize": 8,
            "stopbits": 1,
            "parity": "None",
            "min": 0, # cm
            "max": 100, # cm
        })
        self.db_connection = sqlite3.connect(self.options.sqlite3db)

    def notify_data_received(self):
        # This ensure that "data_received" signal is thrown on
        # main thread. Need for sqlite3 related tasks
        GLib.idle_add(lambda: self.emit("data_received"))

    def graph_canvas_update(self):
        # Check if "fig" is defined on self
        if hasattr(self, "fig"):
            # Define the x-axis for all axes (graphs)
            x = range(0, len(self.level_history), 1)
            y = self.level_history

            # Clear graphs axes and plot again
            self.axLevel.clear()
            # self.axLevel.set_title("Gerador 1")
            self.axLevel.xaxis.grid(linestyle="--")
            self.axLevel.xaxis.set_label_text("Medição nº")
            # self.axLevel.sharex = False
            self.axLevel.yaxis.set_major_formatter(PercentFormatter(xmax=100))
            self.axLevel.plot(x, y, color="red", label="gerador 1") # plot on axes

            # Show graph legend
            if len(self.level_history) > 0:
                self.axLevel.legend(loc="upper right")

            # Draw changes on axes into canvas
            self.fig.canvas.draw()

    def graph_canvas_show(self):
        # Check if "fig" is defined on self
        if hasattr(self, "fig"):
            return

        # Create a new figure with 100 dots per inch
        # and set a subscript title
        self.fig = Figure(dpi=100)
        self.fig.suptitle("Nível do fluido", fontsize="x-large", fontweight="bold")
        self.fig.subplots_adjust(top=.85, hspace=.5)

        # Define a new axes to plot digital modulation
        self.axLevel = self.fig.add_subplot(1, 1, 1)

        figCanvas = FigureCanvas(self.fig)
        figCanvas.set_size_request(600,500)
        #toDo: fix crash# navBar = NavigationToolbar(figCanvas)

        self.boxPreview.append(figCanvas)
        #toDo: fix crash# self.boxPreview.append(navBar)

        self.txtVwQuadros.get_buffer().set_text("O nível varia de 0 a 1 conforme min and max")
        self.graph_canvas_update()

    def level_history_append(self, distance):
        # map from [max, min] to [0, 1]*100
        self.level_history.append((self.options.max - distance)*100 / (self.options.max - self.options.min))
        self.graph_canvas_update()

    def send(self, text, form="N"):
        if form == "N": # pain text
            data = text
            data += '\n'
        if form == "H": # hexadecimal
            data = str(bytearray.fromhex(text.replace('\n', ' ')))
        self.serial.write(data)

    def on_data_received(self, app):
        data = self.serial.read()
        txt = str(data).strip()
        match = re.search(r"(\d+)", txt)
        if match != None:
            distance = int(match.group(0))
            print(f"Received: {txt}")
            cursor = self.db_connection.cursor()
            cursor.execute(f"INSERT INTO gerador1(distance) VALUES ({distance})")
            self.level_history_append(distance)

    def on_serial_failed(self):
        print("Failed")

    def on_toggle_port(self, dropdown, _pspec):
        com_port = dropdown.get_selected_item().get_string()
        if com_port is not None:
            self.options.serial_port = com_port

    def on_toggle_rate(self, dropdown, _pspec):
        baud_rate = dropdown.props.selected_item.props.string
        if baud_rate is not None:
            self.options.baud_rate = baud_rate

    def on_submit(self, button):
        self.serial.start(
            self.options.serial_port,
            self.options.baud_rate,
            self.options.bytesize,
            self.options.stopbits,
            self.options.parity )
        button.set_sensitive(False)

    def on_quit_shutdown(self, app):
        app.serial.join()       # block serial, finish queue and close serial
        print("committing changes...")
        self.db_connection.commit() # commit changes into database
        self.db_connection.close()
        print("exiting...")

    # When the application is launched…
    def on_activate(self, app):
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(os.path.dirname(__file__) , "main.ui"))

        # Get objects reference
        self.win = builder.get_object("winMain")
        self.dropdownPort = builder.get_object("dropdownPort")
        self.dropdownRate = builder.get_object("dropdownRate")
        self.btnSubmit = builder.get_object("btnSubmit")
        self.boxPreview = builder.get_object("boxPreview")
        self.txtVwQuadros = builder.get_object("txtVwQuadros")

        # Connect signals
        self.dropdownPort.connect_after("notify::selected-item", self.on_toggle_port)
        self.dropdownRate.connect_after("notify::selected-item", self.on_toggle_rate)
        self.btnSubmit.connect("clicked", self.on_submit)

        # Get serial ports and populate DropDown
        portsStringList = Gtk.StringList()
        for port in serial_bus.get_ports():
            portsStringList.append(port)
        Gtk.DropDown.set_model(self.dropdownPort, portsStringList)

        # Create and load database
        db_cursor = self.db_connection.cursor()
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS gerador1 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                distance INTEGER
            );
        """) # db_cursor.execute("INSERT INTO gerador1(distance) VALUES (90),(83),(82),(50),(40)")
        for row in db_cursor.execute("SELECT distance FROM gerador1"):
            self.level_history_append(row[0])

        self.graph_canvas_show() # Add a canvas where to plot graphs
        self.win.set_application(self)  # Application will close if it has no active windows attached to it
        self.win.present()

def log_writer(log_level, fields, user_data):
    if os.getenv("G_DEBUG") is not None:
        # Let GLib handle errors
        return GLib.log_writer_default(log_level, fields, user_data)
    else:
        # Do nothing and return errors handled
        return GLib.LogWriterOutput.HANDLED

def main():
    GLib.log_set_writer_func(log_writer)

    app = MyApp(application_id="com.github.diogob003.tr2app")
    app.run(None)

if __name__ == '__main__':
    main()
