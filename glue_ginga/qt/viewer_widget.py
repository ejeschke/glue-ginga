from __future__ import absolute_import, division, print_function

import os

from qtpy import QtWidgets, PYQT5

from ginga.misc import log
from ginga import toolkit

if PYQT5:
    toolkit.use('qt5')
else:
    toolkit.use('qt')

from ginga.gw import ColorBar
from ginga.gw import Readout

from ginga.qtw.ImageViewCanvasQt import ImageViewCanvas
from ginga.misc.Settings import SettingGroup
from ginga.Bindings import ImageViewBindings
from ginga.util.paths import ginga_home
from ginga import colors

from glue.viewers.common.qt.data_viewer_with_state import DataViewerWithState
from glue.viewers.common.qt.toolbar import BasicToolbar
from glue.viewers.image.state import ImageViewerState
from glue.viewers.image.qt.options_widget import ImageOptionsWidget
from glue.core.subset import roi_to_subset_state

# The following is to ensure that the mouse modes get registered
from glue_ginga.qt import mouse_modes  # noqa

from glue_ginga.qt.layer_artist import GingaImageLayer, GingaSubsetImageLayer

__all__ = ['GingaViewer']


class GingaViewer(DataViewerWithState):

    LABEL = "Ginga Viewer"

    _toolbar_cls = BasicToolbar
    _state_cls = ImageViewerState
    _options_cls = ImageOptionsWidget
    _data_artist_cls = GingaImageLayer
    _subset_artist_cls = GingaSubsetImageLayer

    # TODO: Add 'ginga:spectrum' back when spectrum mode is fixed.
    tools = ['ginga:rectangle', 'ginga:circle', 'ginga:polygon', 'ginga:lasso',
             'ginga:xrange', 'ginga:yrange', 'ginga:pan', 'ginga:freepan',
             'ginga:rotate', 'ginga:contrast', 'ginga:cuts', 'ginga:dist',
             'ginga:colormap', 'ginga:slicer']

    def __init__(self, session, parent=None):
        super(GingaViewer, self).__init__(session, parent)

        self.logger = log.get_logger(name='ginga', level=20,
                                     # switch commenting for debugging
                                     # null=True, log_stderr=False,
                                     null=False, log_stderr=True
                                     )

        # load binding preferences if available
        cfgfile = os.path.join(ginga_home, "bindings.cfg")
        bindprefs = SettingGroup(name='bindings', logger=self.logger,
                                 preffile=cfgfile)
        bindprefs.load(onError='silent')

        bd = ImageViewBindings(self.logger, settings=bindprefs)

        # make Ginga viewer
        self.viewer = ImageViewCanvas(self.logger, render='widget',
                                      bindings=bd)
        self.canvas = self.viewer

        # prevent widget from grabbing focus
        self.viewer.set_enter_focus(False)
        self.viewer.set_desired_size(300, 300)

        # enable interactive features
        bindings = self.viewer.get_bindings()
        bindings.enable_all(True)
        self.canvas.register_for_cursor_drawing(self.viewer)
        self.canvas.add_callback('draw-event', self._apply_roi_cb)
        self.canvas.add_callback('edit-event', self._update_roi_cb)
        self.canvas.add_callback('draw-down', self._clear_roi_cb)
        self.canvas.enable_draw(False)
        self.canvas.enable_edit(False)
        self.viewer.enable_autozoom('off')
        self.viewer.set_zoom_algorithm('rate')
        self.viewer.set_zoomrate(1.4)
        self.viewer.set_fg(*colors.lookup_color("#D0F0E0"))

        bm = self.viewer.get_bindmap()
        bm.add_callback('mode-set', self.mode_set_cb)
        self.mode_w = None
        self.mode_actns = {}

        # Create settings and set defaults
        settings = self.viewer.get_settings()
        self.settings = settings
        settings.getSetting('cuts').add_callback('set', self.cut_levels_cb)
        settings.set(autozoom='off', autocuts='override',
                     autocenter='override')

        # make color bar, with color maps shared from ginga canvas
        rgbmap = self.viewer.get_rgbmap()
        self.colorbar = ColorBar.ColorBar(self.logger)
        rgbmap.add_callback('changed', self.rgbmap_cb, self.viewer)
        self.colorbar.set_rgbmap(rgbmap)

        # make coordinates/value readout
        self.readout = Readout.Readout(-1, 20)
        self.roi_tag = None
        self.opn_obj = None

        topw = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.viewer.get_widget(), stretch=1)
        cbar_w = self.colorbar.get_widget()
        if not isinstance(cbar_w, QtWidgets.QWidget):
            # ginga wrapped widget
            cbar_w = cbar_w.get_widget()
        layout.addWidget(cbar_w, stretch=0)
        readout_w = self.readout.get_widget()
        if not isinstance(readout_w, QtWidgets.QWidget):
            # ginga wrapped widget
            readout_w = readout_w.get_widget()
        layout.addWidget(readout_w, stretch=0)
        topw.setLayout(layout)

        self._crosshair_id = '_crosshair'

        self.setCentralWidget(topw)

    def get_layer_artist(self, cls, layer=None, layer_state=None):
        if layer_state is not None and layer_state.viewer_state is None:
            layer_state.viewer_state = self.state
        return cls(layer=layer, layer_state=layer_state,
                   canvas=self.canvas, viewer_state=self.state)

    def match_colorbar(self, canvas, colorbar):
        rgbmap = self.viewer.get_rgbmap()
        loval, hival = self.viewer.get_cut_levels()
        colorbar.set_range(loval, hival)
        colorbar.set_rgbmap(rgbmap)

    def rgbmap_cb(self, rgbmap, canvas):
        self.match_colorbar(canvas, self.colorbar)

    def cut_levels_cb(self, setting, tup):
        (loval, hival) = tup
        self.colorbar.set_range(loval, hival)

    def _set_roi_mode(self, opn_obj, name, mode, **kwargs):
        self.opn_obj = opn_obj
        en_draw = (mode == 'draw')
        self.canvas.enable_draw(en_draw)
        self.canvas.set_draw_mode(mode)
        # XXX need better way of setting draw contexts
        self.canvas.draw_context = self
        self.canvas.set_drawtype(name, **kwargs)

    def _clear_roi_cb(self, canvas, *args):
        if self.opn_obj is not None:
            self.opn_obj.opn_init(self, self.roi_tag)
        else:
            try:
                self.canvas.delete_object_by_tag(self.roi_tag)
            except Exception:
                pass

    def _apply_roi_cb(self, canvas, tag):
        if self.canvas.draw_context is not self:
            return
        self.roi_tag = tag
        obj = self.canvas.get_object_by_tag(tag)

        if self.opn_obj is None:
            # delete outline
            self.canvas.delete_object(obj)
            self.roi_tag = None
            return

        self.opn_obj.opn_exec(self, tag, obj)

    def _update_roi_cb(self, canvas, obj):
        if self.canvas.draw_context is not self:
            return
        if self.opn_obj is None:
            return
        self.opn_obj.opn_update(self, obj)

    def mode_cb(self, modname, tf):
        """This method is called when a toggle button in the toolbar is pressed
        selecting one of the modes.
        """
        bm = self.viewer.get_bindmap()
        if not tf:
            bm.reset_mode(self.viewer)
            return
        bm.set_mode(modname, mode_type='locked')
        return True

    def mode_set_cb(self, bm, modname, mtype):
        """This method is called when a mode is selected in the viewer widget.
        NOTE: it may be called when mode_cb() is not called (for example, when
        a keypress initiates a mode); however, the converse is not true:
        calling mode_cb() will always result in this method also being
        called as a result.

        This logic is to insure that the toggle buttons are left in a sane
        state that reflects the current mode, however it was initiated.
        """
        if modname in self.mode_actns:
            if self.mode_w and (self.mode_w != self.mode_actns[modname]):
                self.mode_w.setChecked(False)
            self.mode_w = self.mode_actns[modname]
            self.mode_w.setChecked(True)
        elif self.mode_w:
            # keystroke turned on a mode for which we have no GUI button
            # and a GUI button is selected--unselect it
            self.mode_w.setChecked(False)
            self.mode_w = None
        return True

    def set_cmap(self, cmap):
        self.canvas.set_cmap(cmap)

    def show_crosshairs(self, x, y):
        self.clear_crosshairs()
        c = self.canvas.viewer.get_draw_class('point')(
            x, y, 6, color='red', style='plus')
        self.canvas.add(c, tag=self._crosshair_id, redraw=True)

    def clear_crosshairs(self):
        try:
            self.canvas.delete_objects_by_tag(
                [self._crosshair_id], redraw=False)
        except Exception:
            pass

    def apply_roi(self, roi, override_mode=None):

        subset_state = roi_to_subset_state(roi,
                                           x_att=self.state.x_att,
                                           y_att=self.state.y_att)

        self.apply_subset_state(subset_state, override_mode=override_mode)
