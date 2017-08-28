#
# Glue.py -- Glue plugin for Ginga viewer
#
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
#
"""
The Glue plugin implements a Glue interface for the Ginga viewer.
"""
from __future__ import absolute_import, division, print_function

import sys
import warnings

from astropy.table import Table
from astropy.wcs import WCS

from ginga import GingaPlugin
from ginga import AstroImage
from ginga.gw import Widgets
from ginga.misc.Datasrc import Datasrc
from ginga.misc.Callback import Callbacks
from ginga.table import AstroTable
from ginga.util.six.moves import map

from glue.core import Data
from glue.core.coordinates import WCSCoordinates
from glue.core.message import (DataCollectionAddMessage,
                               DataCollectionDeleteMessage,
                               ApplicationClosedMessage)
from glue.core.hub import HubListener
from glue.utils.error import GlueDeprecationWarning

help_msg = sys.modules[__name__].__doc__

__all__ = ['Glue']


class GingaHubListener(Callbacks, HubListener):
    """
    Acts as a bridge between the Glue data collection hub and ginga callbacks.
    """

    def __init__(self, datasrc):
        super(GingaHubListener, self).__init__()

        self.datasrc = datasrc

        for cbname in ['data_in', 'data_out', 'app_closed']:
            self.enable_callback(cbname)

    def connect_hub(self, hub):
        hub.subscribe(self, DataCollectionAddMessage,
                      self._data_added_cb)
        hub.subscribe(self, DataCollectionDeleteMessage,
                      self._data_removed_cb)

        # This needs https://github.com/glue-viz/glue/pull/1168
        hub.subscribe(self, ApplicationClosedMessage,
                      self._app_closed_cb)

    def _data_added_cb(self, msg):
        data = msg.data
        name = data.label
        if data.ndim == 1:
            image = self._data_to_table(data)
        else:
            image = self._data_to_image(data)
        image.set(name=name)
        self.datasrc[name] = image
        self.make_callback('data_in', image)

    def _data_removed_cb(self, msg):
        data = msg.data
        name = data.label
        image = self.datasrc.remove(name)
        self.make_callback('data_out', image)

    def _app_closed_cb(self, msg):
        self.make_callback('app_closed', None)

    def get_data(self, name):
        return self.datasrc[name]

    @staticmethod
    def _data_to_image(data):
        ids = data.component_ids()
        data_np = data[ids[0]]
        data_meta = {}

        if hasattr(data.coords, 'header'):
            h = AstroImage.AstroHeader()
            h.update(data.coords.header)
            data_meta['header'] = h

        image = AstroImage.AstroImage(data_np=data_np, metadata=data_meta)

        if hasattr(data.coords, 'wcs'):
            image.wcs.load_header(data.coords.wcs.to_header())

        return image

    @staticmethod
    def _data_to_table(data):
        tab = Table()

        for cid in data.visible_components:
            comp = data.get_component(cid)
            if comp.categorical:
                tab[cid.label] = comp.labels
            else:
                tab[cid.label] = comp.data

        return AstroTable.AstroTable(data_ap=tab)


class Glue(GingaPlugin.GlobalPlugin):
    """Glue global plugin for Ginga reference viewer."""

    def __init__(self, fv):
        # superclass defines some variables for us, like logger
        super(Glue, self).__init__(fv)

        self.glue_app = None
        self.glue_hl = GingaHubListener(Datasrc(length=0))
        self.glue_hl.add_callback('data_in', self.data_added_cb)
        self.glue_hl.add_callback('data_out', self.data_removed_cb)
        self.glue_hl.add_callback('app_closed', self.app_closed_cb)

        self.data_names = []
        self.gui_up = False

    def build_gui(self, container):
        top = Widgets.VBox()
        top.set_border_width(4)

        vbox, sw, orientation = Widgets.get_oriented_box(container)

        vbox.set_border_width(4)
        vbox.set_spacing(2)

        self.msg_font = self.fv.get_font("sansFont", 12)
        tw = Widgets.TextArea(wrap=True, editable=False)
        tw.set_font(self.msg_font)
        self.tw = tw

        fr = Widgets.Expander("Instructions")
        fr.set_widget(tw)
        vbox.add_widget(fr, stretch=0)

        fr = Widgets.Frame("Glue Interface")

        captions = [
            ('Start Glue', 'button', 'Stop Glue', 'button'),
            ('Put Data', 'button'),
            ('Get Data', 'button', 'dataitem', 'combobox'),
            ]
        w, b = Widgets.build_info(captions)
        self.w.update(b)

        fr.set_widget(w)
        vbox.add_widget(fr, stretch=0)

        b.start_glue.add_callback('activated', lambda w: self.start_glue_cb())
        b.start_glue.set_tooltip('Start a Glue session')

        b.stop_glue.add_callback('activated', lambda w: self.stop_glue_cb())
        b.stop_glue.set_tooltip('Stop a Glue session')
        b.stop_glue.set_enabled(False)

        b.put_data.add_callback('activated', lambda w: self.put_data_cb())
        b.put_data.set_tooltip('Send data to Glue')
        b.put_data.set_enabled(False)

        b.get_data.add_callback('activated', lambda w: self.get_data_cb())
        b.get_data.set_tooltip('Get selected data from Glue')
        b.get_data.set_enabled(False)

        b.dataitem.set_tooltip('Select data to get from Glue')

        # stretch
        top.add_widget(sw, stretch=1)

        btns = Widgets.HBox()
        btns.set_spacing(4)
        btns.set_border_width(4)

        btn = Widgets.Button("Close")
        btn.add_callback('activated', lambda w: self.close())
        btn.set_tooltip('Close this plugin and Glue')
        btns.add_widget(btn)
        btns.add_widget(Widgets.Label(''), stretch=1)

        top.add_widget(btns, stretch=0)
        container.add_widget(top, stretch=1)

        self.gui_up = True

    def instructions(self):
        self.tw.set_text("""This plugin enables interface with Glue.

Press "Start Glue" to start a new Glue session. Glue started independently (without using this button) does not work with this plugin. Glue started this way is tied to the Ginga session; i.e., closing Ginga will also close Glue.

Press "Stop Glue" to end the Glue session without closing the plugin. This might not work correctly if there are multiple Glue sessions. This is unnecessary if Glue is already closed, e.g., by pressing "X" in Glue.

To send an image or table to Glue, make it the currently active image/table and press "Put Data". Then switch to the Glue application to interact with it.

To get an image or table from Glue to the currently active channel, select the associated name from the drop-down menu and then press "Get Data". If there is already an image with the same name in the Ginga channel, it will be overwritten.

Press "Close" to close this plugin. This also closes the associated Glue session, if not already.""")  # noqa

    def error_no_glue(self, verbose=True):
        """Call this to reset GUI when Glue session disappears."""
        self.w.start_glue.set_enabled(True)
        self.w.stop_glue.set_enabled(False)
        self.w.put_data.set_enabled(False)
        self.w.get_data.set_enabled(False)
        self.w.dataitem.clear()
        self.data_names = []
        if verbose:
            self.fv.show_error("No glue session running!")

    def put_data_cb(self):
        if self.glue_app is None:
            self.error_no_glue()
            return

        channel = self.fv.get_current_channel()
        if channel is None:
            self.fv.show_error("No active channel!")
            return

        image = channel.get_current_image()
        if image is None:
            self.fv.show_error("No data in channel '%s'" % (channel.name))
            return

        data_np = image.get_data()
        name = image.get('name', 'noname')
        kwargs = {name: data_np}

        try:
            # Pass in WCS for image.
            if isinstance(image, AstroImage.AstroImage):
                gdata = Data(**kwargs)
                h = image.get_header()
                w = WCS(h)
                gdata.coords = WCSCoordinates(h, wcs=w)
                self.glue_app.add_data(**{name: gdata})
            # Table data
            else:
                self.glue_app.add_data(**kwargs)

            self.glue_app.raise_()

        except Exception as e:
            self.fv.show_error("Error sending data to Glue: %s" % (str(e)))
            self.error_no_glue()

    def get_data_cb(self):
        if self.glue_app is None:
            self.error_no_glue()
            return

        # channel = self.fv.get_channel_on_demand('Glue')
        channel = self.fv.get_current_channel()
        if channel is None:
            self.fv.show_error("No active channel!")
            return

        idx = self.w.dataitem.get_index()
        name = self.data_names[idx]
        dataobj = self.glue_hl.get_data(name)

        channel.add_image(dataobj)

    def _adj_data_list(self):
        # adjust available items list
        dc = self.glue_app.data_collection
        self.w.dataitem.clear()

        self.data_names = list(map(lambda data: data.label, dc.data))

        if len(self.data_names) == 0:
            self.w.get_data.set_enabled(False)
            return

        for name in self.data_names:
            self.w.dataitem.append_text(name)

        self.w.dataitem.set_index(0)
        self.w.get_data.set_enabled(True)

    def data_added_cb(self, hub, dataobj):
        self._adj_data_list()

    def data_removed_cb(self, hub, dataobj):
        self._adj_data_list()

    def app_closed_cb(self, hub, dataobj):
        self.glue_app = None
        self.error_no_glue(verbose=False)

    def start_glue_cb(self):
        self.glue_app = qglue()
        hub = self.glue_app.data_collection.hub
        if hub is not None:
            self.glue_hl.connect_hub(hub)

        # self.glue_app._create_terminal()
        sgeo = self.glue_app.app.desktop().screenGeometry()
        self.glue_app.show()
        self.glue_app.resize(sgeo.width() * 0.9, sgeo.height() * 0.9)
        # self.glue_app.lower()

        # Toggle buttons accordingly.
        self.w.start_glue.set_enabled(False)
        self.w.stop_glue.set_enabled(True)
        self.w.put_data.set_enabled(True)

    def stop_glue_cb(self):
        if self.glue_app is None:
            self.error_no_glue(verbose=False)
            return

        w, self.glue_app = self.glue_app, None

        try:
            w.deleteLater()
        except Exception as e:  # Glue is closed already
            self.logger.debug(str(e))
        finally:
            self.error_no_glue(verbose=False)

    def glue_new_data_cb(self, msg):
        print(dir(msg))

    def start(self):
        self.instructions()

        if self.glue_app is not None:
            self.w.start_glue.set_enabled(False)
            self.w.stop_glue.set_enabled(True)
            self.w.put_data.set_enabled(True)
            self._adj_data_list()

    def stop(self):
        self.gui_up = False
        # self.stop_glue_cb()  # Uncomment this to close Glue when plugin close

    def close(self):
        self.w.dataitem.clear()

        self.fv.stop_global_plugin(str(self))
        return True

    def __str__(self):
        return 'glue'


def qglue():
    """
    Quickly send python variables to Glue for visualization.

    Returns
    -------
    ga : ``GlueApplication`` object

    """
    from glue.core import DataCollection
    from glue.app.qt import GlueApplication

    dc = DataCollection()

    # Suppress pesky Glue warnings.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', GlueDeprecationWarning)
        ga = GlueApplication(data_collection=dc)

    return ga

# END
