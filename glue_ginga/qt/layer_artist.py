from __future__ import absolute_import, division, print_function

from time import time

import numpy as np
from ginga.misc import Bunch
from ginga.util import wcsmod
from ginga import AstroImage, BaseImage

from glue.external.echo import keep_in_sync, CallbackProperty
from glue.core.exceptions import IncompatibleAttribute
from glue.core.layer_artist import LayerArtistBase
from glue.utils import color2rgb
from glue.viewers.image.state import ImageLayerState, ImageSubsetLayerState

wcsmod.use('astropy')


class GingaLayerArtist(LayerArtistBase):

    zorder = CallbackProperty()
    visible = CallbackProperty()

    def __init__(self, viewer_state=None, layer=None, layer_state=None, canvas=None):

        super(GingaLayerArtist, self).__init__(layer)

        self._canvas = canvas

        self.layer = layer or layer_state.layer
        self.state = layer_state or self._layer_state_cls(viewer_state=viewer_state,
                                                          layer=self.layer)

        self._viewer_state = viewer_state

        # Should not be needed here? (i.e. should be in add_data/add_subset?)
        if self.state not in self._viewer_state.layers:
            self._viewer_state.layers.append(self.state)

        self.zorder = self.state.zorder
        self.visible = self.state.visible

        self._sync_zorder = keep_in_sync(self, 'zorder', self.state, 'zorder')
        self._sync_visible = keep_in_sync(self, 'visible', self.state, 'visible')

        self.state.add_global_callback(self.update)
        self._viewer_state.add_global_callback(self.update)

    def clear(self):
        self._canvas.delete_objects_by_tag([self._tag], redraw=True)

    def redraw(self, whence=0):
        self._canvas.redraw(whence=whence)

    def remove(self):
        self.clear()

    def __gluestate__(self, context):
        return dict(state=context.id(self.state))

    def update(self, **kwargs):
        try:
            canvas_img = self._canvas.get_object_by_tag(self._tag)
        except KeyError:
            pass
        else:
            canvas_img.set_zorder(self.state.zorder)


class GingaImageLayer(GingaLayerArtist):

    _layer_state_cls = ImageLayerState

    def __init__(self, viewer_state=None, layer=None, layer_state=None, canvas=None):

        super(GingaImageLayer, self).__init__(viewer_state=viewer_state, layer=layer,
                                              layer_state=layer_state, canvas=canvas)

        self._tag = '_image'
        self._img = DataImage(self.state)

    def _ensure_added(self):
        """
        Add artist to canvas if needed
        """
        try:
            self._canvas.get_object_by_tag(self._tag)
        except KeyError:
            self._canvas.set_image(self._img)

    def update(self, **kwargs):

        super(GingaImageLayer, self).update(**kwargs)

        if self.state.visible and self._img:
            self._ensure_added()
        elif not self.state.visible:
            self.clear()
            return

        self.redraw()


class GingaSubsetImageLayer(GingaLayerArtist):

    _layer_state_cls = ImageSubsetLayerState

    def __init__(self, viewer_state=None, layer=None, layer_state=None, canvas=None):

        super(GingaSubsetImageLayer, self).__init__(viewer_state=viewer_state, layer=layer,
                                                    layer_state=layer_state, canvas=canvas)

        self._tag = "layer%s_%s" % (layer.label, time())

        self._img = SubsetImage(self.state)

        # SubsetImages can't be added to canvases directly. Need
        # to wrap into a ginga canvas type.
        Image = self._canvas.get_draw_class('image')
        self._cimg = Image(0, 0, self._img, alpha=0.5, flipy=False)

    def _visible_changed(self, *args):
        if self.state.visible and self._cimg:
            self._canvas.add(self._cimg, tag=self._tag, redraw=True)
        elif not self.state.visible:
            self.clear()

    def _check_enabled(self):
        """
        Sync the enabled/disabled status, based on whether
        mask is computable
        """
        try:
            # Just try computing the subset for the first pixel
            view = tuple(0 for _ in self.layer.data.shape)
            self.layer.to_mask(view)
        except IncompatibleAttribute as exc:
            self.disable_invalid_attributes(*exc.args)
            return

        self.enable()

    def _ensure_added(self):
        """
        Add artist to canvas if needed
        """
        try:
            self._canvas.get_object_by_tag(self._tag)
        except KeyError:
            self._canvas.add(self._cimg, tag=self._tag, redraw=False)

    def update(self, **kwargs):

        super(GingaSubsetImageLayer, self).update(**kwargs)

        self._check_enabled()

        if self.state.visible and self._img:
            self._ensure_added()
        elif not self.state.visible:
            self.clear()
            return

        self.redraw(whence=0)


def forbidden(*args):
    raise ValueError("Forbidden")


class DataImage(AstroImage.AstroImage):
    """
    A Ginga image subclass to interface with Glue Data objects
    """

    get_data = _get_data = copy_data = set_data = get_array = transfer = forbidden

    def __init__(self, layer_state, **kwargs):
        """
        Parameters
        ----------
        ...
        kwargs : dict
            Extra kwargs are passed to the superclass
        """
        self.layer_state = layer_state
        super(DataImage, self).__init__(**kwargs)

    @property
    def shape(self):
        """
        The shape of the 2D view into the data
        """
        return self.layer_state.get_sliced_data_shape()

    def _get_fast_data(self):
        return self._slice((slice(None, None, 10), slice(None, None, 10)))

    def _slice(self, view):
        """
        Extract a view from the 2D image.
        """
        return self.layer_state.get_sliced_data(view=view, use_cache=False)


class SubsetImage(BaseImage.BaseImage):
    """
    A Ginga image subclass to interface with Glue subset objects
    """
    get_data = _get_data = copy_data = set_data = get_array = transfer = forbidden

    def __init__(self, layer_state=None, **kwargs):
        """
        Parameters
        ----------
        ...
        kwargs : dict
            Extra kwargs are passed to the ginga superclass
        """
        self.layer_state = layer_state

        # NOTE: BaseImage accesses shape property--we need above items
        # defined because we override shape()
        super(SubsetImage, self).__init__(**kwargs)
        self.order = 'RGBA'

    @property
    def shape(self):
        """
        Shape of the 2D view into the subset mask
        """
        return self.layer_state.get_sliced_data_shape()

    def _rgb_from_mask(self, mask):
        """
        Turn a boolean mask into a 4-channel RGBA image
        """
        r, g, b = color2rgb(self.layer_state.color)
        ones = mask * 0 + 255
        alpha = mask * 127
        result = np.dstack((ones * r, ones * g, ones * b, alpha)).astype(np.uint8)
        return result

    def _get_fast_data(self):
        return self._slice((slice(None, None, 10), slice(None, None, 10)))

    def _calc_order(self, order):
        # Override base class because it invokes a glue forbidden method to
        # access the data type of the image--we can instead assume RGBA
        self.order = 'RGBA'

    def _slice(self, view):
        """
        Extract a view from the 2D subset mask.
        """
        try:
            return self._rgb_from_mask(self.layer_state.get_sliced_data(view=view, use_cache=False))
        except IncompatibleAttribute:
            return np.zeros(self.shape + (4,))

    def _set_minmax(self):
        # we already know the data bounds
        self.minval = 0
        self.maxval = 256
        self.minval_noinf = self.minval
        self.maxval_noinf = self.maxval

    def get_scaled_cutout2(self, p1, p2, scales, method=None, logger=None):
        # override this function from ginga.BaseImage to force method='view',
        # because Glue needs to work solely with slices
        return super(SubsetImage, self).get_scaled_cutout2(p1, p2, scales,
                                                           method='view',
                                                           logger=logger)
