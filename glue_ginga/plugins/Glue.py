#
# Glue.py -- Glue plugin for Ginga viewer
#
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
#
"""
The Glue plugin implements a Glue interface for the Ginga viewer.
"""
import sys

import numpy as np

from ginga import GingaPlugin
from ginga import AstroImage
from ginga.gw import Widgets
from ginga.misc.Datasrc import Datasrc
from ginga.misc.Callback import Callbacks
from ginga.util.six.moves import map

from glue.core.message import (DataCollectionAddMessage,
                               DataCollectionDeleteMessage)
from glue.core.hub import HubListener

help_msg = sys.modules[__name__].__doc__


class GingaHubListener(Callbacks, HubListener):
    """
    Acts as a bridge between the Glue data collection hub and ginga callbacks.
    """

    def __init__(self, datasrc):
        super(GingaHubListener, self).__init__()

        self.datasrc = datasrc

        for cbname in ['data_in', 'data_out']:
            self.enable_callback(cbname)

    def connect_hub(self, hub):
        hub.subscribe(self, DataCollectionAddMessage,
                      self._data_added_cb)
        hub.subscribe(self, DataCollectionDeleteMessage,
                      self._data_removed_cb)

    def _data_added_cb(self, msg):
        data = msg.data
        name = data.label
        ids = data.component_ids()
        data_np = data[ids[0]]
        image = AstroImage.AstroImage(data_np=data_np)
        image.set(name=name)
        self.datasrc[name] = image
        self.make_callback('data_in', image)
    
    def _data_removed_cb(self, msg):
        data = msg.data
        image = self.datasrc.remove(name)
        self.make_callback('data_out', image)

    def get_data(self, name):
        return self.datasrc[name]
        
    
class Glue(GingaPlugin.GlobalPlugin):

    def __init__(self, fv):
        # superclass defines some variables for us, like logger
        super(Glue, self).__init__(fv)

        self.glue_app = None
        self.glue_hl = GingaHubListener(Datasrc(length=0))
        self.glue_hl.add_callback('data_in', self.data_added_cb)
        self.glue_hl.add_callback('data_out', self.data_removed_cb)

        self.data_names = []

    def build_gui(self, container):
        vbox = Widgets.VBox()

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
        b.start_glue.set_tooltip("Start a Glue session")
        b.stop_glue.add_callback('activated', lambda w: self.stop_glue_cb())
        
        b.put_data.add_callback('activated', lambda w: self.put_data_cb())
        b.get_data.add_callback('activated', lambda w: self.get_data_cb())

        # stretch
        vbox.add_widget(Widgets.Label(''), stretch=1)

        btns = Widgets.HBox()
        btns.set_spacing(4)
        btns.set_border_width(4)

        btn = Widgets.Button("Close")
        btn.add_callback('activated', lambda w: self.close())
        btns.add_widget(btn)
        btns.add_widget(Widgets.Label(''), stretch=1)
        vbox.add_widget(btns)

        container.add_widget(vbox, stretch=1)


    def put_data_cb(self):
        if self.glue_app is None:
            self.fv.show_error("No glue session running!")
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
        kwargs = { name: data_np }

        try:
            self.glue_app.add_data(**kwargs)
            self.glue_app.raise_()

        except Exception as e:
            self.fv.show_error("Error sending data to Glue: %s" % (str(e)))
            

    def get_data_cb(self):
        if self.glue_app is None:
            self.fv.show_error("No glue session running!")
            return
        
        #channel = self.fv.get_channel_on_demand('Glue')
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
        for name in self.data_names:
            self.w.dataitem.append_text(name)

        self.w.dataitem.set_index(0)

    def data_added_cb(self, hub, dataobj):
        self._adj_data_list()
        
    def data_removed_cb(self, hub, dataobj):
        self._adj_data_list()
            
    def start_glue_cb(self):
        self.glue_app = qglue()
        hub = self.glue_app.data_collection.hub
        if hub is not None:
            self.glue_hl.connect_hub(hub)

        # self.glue_app._create_terminal()
        self.glue_app.resize(1200, 800)
        self.glue_app.show()
        #self.glue_app.lower()

    def stop_glue_cb(self):
        if self.glue_app is None:
            return
        w, self.glue_app = self.glue_app, None
        w.deleteLater()

    def glue_new_data_cb(self, msg):
        print(dir(msg))

    def start(self):
        pass

    def stop(self):
        self.stop_glue_cb()

    def close(self):
        self.w.dataitem.clear()

        self.fv.stop_global_plugin(str(self))
        return True

    def __str__(self):
        return 'glue'


def qglue(**kwargs):
    """
    Quickly send python variables to Glue for visualization.
    The generic calling sequence is::
      qglue(label1=data1, label2=data2, ..., [links=links])
    The kewyords label1, label2, ... can be named anything besides ``links``
    data1, data2, ... can be in many formats:
      * A pandas data frame
      * A path to a file
      * A numpy array, or python list
      * A numpy rec array
      * A dictionary of numpy arrays with the same shape
      * An astropy Table
    ``Links`` is an optional list of link descriptions, each of which has
    the format: ([left_ids], [right_ids], forward, backward)
    Each ``left_id``/``right_id`` is a string naming a component in a dataset
    (i.e., ``data1.x``). ``forward`` and ``backward`` are functions which
    map quantities on the left to quantities on the right, and vice
    versa. `backward` is optional
    Examples::
        balls = {'kg': [1, 2, 3], 'radius_cm': [10, 15, 30]}
        cones = {'lbs': [5, 3, 3, 1]}
        def lb2kg(lb):
            return lb / 2.2
        def kg2lb(kg):
            return kg * 2.2
        links = [(['balls.kg'], ['cones.lbs'], lb2kg, kg2lb)]
        qglue(balls=balls, cones=cones, links=links)
    :returns: A :class:`~glue.app.qt.application.GlueApplication` object
    """
    from glue.core import DataCollection
    from glue.app.qt import GlueApplication

    links = kwargs.pop('links', None)

    dc = DataCollection()
    for label, data in kwargs.items():
        dc.extend(parse_data(data, label))

    if links is not None:
        dc.add_link(parse_links(dc, links))

    ga = GlueApplication(dc)
    return ga

#END
