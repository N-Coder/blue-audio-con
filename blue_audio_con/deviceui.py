import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk


class DeviceSelectionWindow(Gtk.Window):
    def __init__(self, devices):
        Gtk.Window.__init__(self, title="Connect to BT Audio Device")
        self.mac = None
        self.set_border_width(10)

        # Setting up the self.grid in which the elements are to be positioned
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.add(self.grid)

        # Creating the ListStore model
        self.device_liststore = Gtk.ListStore(str, str, str)

        # creating the treeview, making it use the filter as a model, and adding the columns
        self.treeview = Gtk.TreeView.new_with_model(self.device_liststore)

        renderer = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn("", renderer, icon_name=0)
        self.treeview.append_column(column)

        for i, column_title in enumerate(["Name", "MAC"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i + 1)
            self.treeview.append_column(column)

        # setting up the layout, putting the treeview in a scrollwindow, and the buttons in a row
        self.scrollable_treelist = Gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.grid.attach(self.scrollable_treelist, 0, 0, 1, 1)
        self.scrollable_treelist.add(self.treeview)

        self.treeview.connect('row-activated', self.row_activated)
        self.connect('key_press_event', self.key_pressed)
        self.connect("delete-event", Gtk.main_quit)

        self.update_model(devices)

        self.set_default_size(350, 200)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()

    def update_model(self, devices):
        mac, sel_path = None, None
        store, paths = self.treeview.get_selection().get_selected_rows()
        if paths:
            mac = store.get_value(store.get_iter(paths[0]), 2)
        self.device_liststore.clear()

        devices.sort(key=lambda d: (d["available"], d["name"]))
        for device in devices:
            iter = self.device_liststore.append([
                "bluetooth-active" if device["available"] else "bluetooth-disabled",
                device["name"],
                device["mac_address"]])
            if device["mac_address"] == mac:
                sel_path = store.get_path(iter)

        if sel_path:
            self.treeview.get_selection().select_path(sel_path)

    def row_activated(self, target, path, column):
        self.device_selected()

    def key_pressed(self, target, event):
        if isinstance(event, Gdk.EventKey):
            if event.get_keycode().keycode == 9:  # ESC
                self.close()
            elif event.get_keycode().keycode == 36:  # Enter
                self.device_selected()

    def device_selected(self):
        store, paths = self.treeview.get_selection().get_selected_rows()
        self.mac = store.get_value(store.get_iter(paths[0]), 2)
        self.close()


def show_chooser(devices):
    win = DeviceSelectionWindow(devices)
    Gtk.main()
    if not win.mac:
        raise KeyboardInterrupt()
    return win.mac
