import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk


class DeviceSelectionWindow(Gtk.Window):
    def __init__(self, devices):
        Gtk.Window.__init__(self, title="Connect to BT Audio Device")
        self.set_border_width(10)

        # Setting up the self.grid in which the elements are to be positionned
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.add(self.grid)

        # Creating the ListStore model
        self.device_liststore = Gtk.ListStore(str, str)
        for device in devices:
            self.device_liststore.append([device["name"], device["mac_address"]])

        # creating the treeview, making it use the filter as a model, and adding the columns
        self.treeview = Gtk.TreeView.new_with_model(self.device_liststore)
        for i, column_title in enumerate(["Name", "MAC"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            self.treeview.append_column(column)

        # setting up the layout, putting the treeview in a scrollwindow, and the buttons in a row
        self.scrollable_treelist = Gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.grid.attach(self.scrollable_treelist, 0, 0, 8, 10)
        self.scrollable_treelist.add(self.treeview)

        self.connect('key_press_event', self.key_pressed)

        self.connect("delete-event", Gtk.main_quit)
        self.show_all()
        # TODO improve device list: show available devices, update, icons

    def key_pressed(self, target, event):
        if isinstance(event, Gdk.EventKey) and event.get_keycode().keycode == 36:
            store, paths = self.treeview.get_selection().get_selected_rows()
            self.mac = store.get_value(store.get_iter(paths[0]), 1)
            self.close()
            # TODO ESC, double click


def show_window(devices):
    win = DeviceSelectionWindow(devices)
    Gtk.main()
    return win.mac
