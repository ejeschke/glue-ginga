from __future__ import absolute_import, division, print_function

import os
import sys

from ginga import cmap as ginga_cmap

from qtpy import QtGui, QtWidgets
from glue.config import viewer_tool
from glue.viewers.common.qt.tool import CheckableTool
from glue.utils import nonpartial
from glue.utils.qt import load_ui
from glue.plugins.tools.spectrum_tool.qt import SpectrumTool
from glue.plugins.tools.pv_slicer.qt import PVSlicerMode

from glue_ginga.qt.utils import cmap2pixmap, ginga_graphic_to_roi

# Find out location of ginga module so we can some of its icons
GINGA_HOME = os.path.split(sys.modules['ginga'].__file__)[0]
GINGA_ICON_DIR = os.path.join(GINGA_HOME, 'icons')

# add matplotlib colormaps
# TODO: glue menu seems extremely slow if we add them all
#ginga_cmap.add_matplotlib_cmaps(fail_on_import_error=False)


class GingaROIMode(CheckableTool):

    def opn_init(self, viewer, tag):
        """This method is called when the user clicks down to draw an object.
        It gets called with any previously drawn object that was kept (or None).
        """
        if tag is not None:
            try:
                # typical case for a ROI is delete any existing shape
                viewer.canvas.delete_object_by_tag(tag)
            except:
                pass

        return None

    def opn_exec(self, viewer, tag, obj):
        """This method gets called when the user finishes drawing an object
        and it has been added to the canvas.  `tag` is the tag of the object
        on the canvas and `obj` is the actual shape.
        """

        # typical case is we want to remove the shape we just drew
        # from the canvas because we will be replacing it with a ROI
        viewer.canvas.delete_object_by_tag(tag, redraw=False)

        roi = ginga_graphic_to_roi(obj)

        viewer.apply_roi(roi)


class GingaPathMode(GingaROIMode):
    pass


@viewer_tool
class RectangleROIMode(GingaROIMode):

    tool_id = 'ginga:rectangle'
    icon = 'glue_square'
    action_text = 'Rectangular ROI'
    tool_tip = 'Define a rectangular region of interest'

    def activate(self):
        self.viewer._set_roi_mode(self, 'rectangle', 'draw',
                                  color='cyan', linewidth=2, linestyle='dash',
                                  fill=True, fillcolor='yellow', fillalpha=0.5)

    def deactivate(self):
        self.viewer._set_roi_mode(None, 'rectangle', None)


@viewer_tool
class CircleROIMode(GingaROIMode):

    tool_id = 'ginga:circle'
    icon = 'glue_circle'
    action_text = 'Circular ROI'
    tool_tip = 'Define a circular region of interest'

    def activate(self):
        self.viewer._set_roi_mode(self, 'circle', 'draw',
                                  color='cyan', linewidth=2, linestyle='dash',
                                  fill=True, fillcolor='yellow', fillalpha=0.5)

    def deactivate(self):
        self.viewer._set_roi_mode(None, 'circle', None)


@viewer_tool
class PolygonROIMode(GingaROIMode):

    tool_id = 'ginga:polygon'
    icon = 'glue_lasso'
    action_text = 'Polygonal ROI'
    tool_tip = ('Define a polygon region of interest.\n'
                '  Click and drag to start the polygon;\n'
                '    "v" adds a vertex,\n'
                '    "z" deletes last added vertex.\n'
                '  Release button to finalize')
    status_tip = ('CLICK and DRAG to start polygon, press "v" to add a '
                  'polygon vertex, "z" to remove last added vertex')

    def activate(self):
        self.viewer._set_roi_mode(self, 'polygon', 'draw',
                                  color='cyan', linewidth=2, linestyle='dash',
                                  fill=True, fillcolor='yellow', fillalpha=0.5)

    def deactivate(self):
        self.viewer._set_roi_mode(None, 'polygon', None)


@viewer_tool
class LassoROIMode(GingaROIMode):

    tool_id = 'ginga:lasso'
    icon = 'glue_lasso'
    tool_tip = ('Lasso a region of interest\n'
                '  Click and drag in a lasso shape to select;\n'
                '  Release to finalize.')
    action_text = 'Polygonal ROI'
    status_tip = ('CLICK and DRAG to start lassoing')

    def activate(self):
        self.viewer._set_roi_mode(self, 'freepolygon', 'draw',
                                  color='cyan', linewidth=2, linestyle='dash',
                                  fill=True, fillcolor='yellow', fillalpha=0.5)

    def deactivate(self):
        self.viewer._set_roi_mode(None, 'freepolygon', None)


@viewer_tool
class PathROIMode(GingaROIMode):

    tool_id = 'ginga:path'
    icon = 'glue_lasso'
    tool_tip = 'Define a path region of interest'
    tool_tip = ('Draw a path as a region of interest\n'
                '  "v" adds a vertex\n'
                '  "z" deletes last added vertex\n'
                '  release button to finalize')
    status_tip = ('CLICK and DRAG to start path, press "v" to add a '
                  'path vertex, "z" to remove last added vertex')

    def activate(self):
        self.viewer._set_roi_mode(self, 'path', 'draw',
                                  color='cyan', linewidth=2, linestyle='dash')

    def deactivate(self):
        self.viewer._set_roi_mode(None, 'path', None)


@viewer_tool
class HRangeMode(GingaROIMode):
    """
    Defines a Range ROI, accessible via the :meth:`~HRangeMode.roi` method.

    This class defines horizontal ranges
    """

    icon = 'glue_xrange_select'
    tool_id = 'ginga:xrange'
    action_text = 'X range'
    tool_tip = 'Select a range of x values'

    def activate(self):
        self.viewer._set_roi_mode(self, 'xrange', 'draw',
                                  fillcolor='cyan', fillalpha=0.5,
                                  linewidth=0)

    def deactivate(self):
        self.viewer._set_roi_mode(None, 'xrange', None)


@viewer_tool
class VRangeMode(GingaROIMode):
    """
    Defines a Range ROI, accessible via the :meth:`~VRangeMode.roi` method.

    This class defines vertical ranges.
    """

    icon = 'glue_yrange_select'
    tool_id = 'ginga:yrange'
    action_text = 'Y range'
    tool_tip = 'Select a range of y values'

    def activate(self):
        self.viewer._set_roi_mode(self, 'yrange', 'draw',
                                  fillcolor='cyan', fillalpha=0.5,
                                  linewidth=0)

    def deactivate(self):
        self.viewer._set_roi_mode(None, 'yrange', None)


@viewer_tool
class PickMode(GingaROIMode):
    """
    Defines a PointROI.

    Defines single point selections.
    """

    icon = 'glue_yrange_select'
    tool_id = 'ginga:pick'
    action_text = 'Pick'
    tool_tip = 'Select a single item'

    def activate(self):
        self.viewer._set_roi_mode(self, 'point', 'draw')

    def deactivate(self):
        self.viewer._set_roi_mode(None, 'point', None)


@viewer_tool
class PanMode(CheckableTool):

    tool_id = 'ginga:pan'
    icon = 'glue_move'
    tool_tip = ('Pan the image by dragging left button\n'
               '   zoom by dragging right button')
    status_tip = 'CLICK and DRAG (left btn) to pan, (right btn) to zoom '

    def activate(self):
        self.viewer.mode_cb('pan', True)

    def deactivate(self):
        self.viewer.mode_cb('pan', False)


@viewer_tool
class FreePanMode(CheckableTool):

    tool_id = 'ginga:freepan'
    icon = os.path.join(GINGA_ICON_DIR, 'hand_48.png')
    tool_tip = ('Zoom in and set pan by clicking left btn\n'
                '  zoom out and set pan by clicking right btn\n'
                '  click and drag middle btn to pan freely')
    status_tip = 'CLICK to zoom and set pan (in == left btn, out == right btn)'

    def activate(self):
        self.viewer.mode_cb('freepan', True)

    def deactivate(self):
        self.viewer.mode_cb('freepan', False)


@viewer_tool
class RotateMode(CheckableTool):

    tool_id = 'ginga:rotate'
    icon = os.path.join(GINGA_ICON_DIR, 'rotate_48.png')
    tool_tip = 'Click and drag to rotate the image about the pan position'
    status_tip = 'Click and drag to rotate the image about the pan position'

    def activate(self):
        self.viewer.mode_cb('rotate', True)

    def deactivate(self):
        self.viewer.mode_cb('rotate', False)


@viewer_tool
class ContrastMode(CheckableTool):

    tool_id = 'ginga:contrast'
    icon = 'glue_contrast'
    tool_tip = ('Adjust bias/contrast of the image, ds9-style\n'
                '  CLICK and DRAG: horizontally to set bias (shift colormap),\n'
                '    vertically to set contrast (stretch colormap).\n'
                '  CLICK right btn to restore to normal (colormap)')

    def activate(self):
        self.viewer.mode_cb('contrast', True)

    def deactivate(self):
        self.viewer.mode_cb('contrast', False)

    # TODO: uncomment when we have updated Ginga to version that contains
    # the restore_contrast() method

    ## def menu_actions(self):
    ##     result = []

    ##     a = QtWidgets.QAction("Restore", None)
    ##     a.triggered.connect(nonpartial(self.restore_cb))
    ##     result.append(a)

    ##     return result

    def restore_cb(self):
        gviewer = self.viewer.viewer
        gviewer.restore_contrast()


@viewer_tool
class CutsMode(CheckableTool):

    tool_id = 'ginga:cuts'
    icon = os.path.join(GINGA_ICON_DIR, 'cuts_48.png')
    tool_tip = ('Set low and high cut levels of the image interactively\n'
                '  CLICK and DRAG: horizontally to set high cut level,\n'
                '    vertically to set low cut level;\n'
                '    (hold SHIFT to set only low level;\n'
                '     CTRL (Command on Mac) to set only high)\n'
                '  CLICK right button to restore to auto cut levels.\n'
                '  SCROLL to increase/decrease contrast by cut levels;\n'
                '    hold CTRL down to use finer granularity')
    status_tip = ('CLICK and DRAG to set cut levels; horizontally to set low'
                  ' cut level, vertically to set high cut level')

    def activate(self):
        self.viewer.mode_cb('cuts', True)

    def deactivate(self):
        self.viewer.mode_cb('cuts', False)

    def get_vmin_vmax(self):
        gviewer = self.viewer.viewer
        return gviewer.get_cut_levels()

    def set_vmin_vmax(self, vmin, vmax):
        gviewer = self.viewer.viewer
        gviewer.cut_levels(vmin, vmax)

    def do_autocuts(self):
        gviewer = self.viewer.viewer
        gviewer.auto_levels()

    def set_autocuts(self, name):
        gviewer = self.viewer.viewer
        gviewer.set_autocut_params(name)

    def choose_vmin_vmax(self):
        # Following example of glue matplotlib viewer
        from glue.viewers.common.qt import mouse_mode
        dialog = load_ui('contrastlimits.ui', None,
                         directory=os.path.dirname(mouse_mode.__file__))
        v = QtGui.QDoubleValidator()
        dialog.vmin.setValidator(v)
        dialog.vmax.setValidator(v)

        vmin, vmax = self.get_vmin_vmax()
        if vmin is not None:
            dialog.vmin.setText(str(vmin))
        if vmax is not None:
            dialog.vmax.setText(str(vmax))

        def _apply():
            try:
                vmin = float(dialog.vmin.text())
                vmax = float(dialog.vmax.text())
                self.set_vmin_vmax(vmin, vmax)
            except ValueError:
                pass

        bb = dialog.buttonBox
        bb.button(bb.Apply).clicked.connect(_apply)
        dialog.accepted.connect(_apply)
        dialog.show()
        dialog.raise_()
        dialog.exec_()

    def menu_actions(self):
        from ginga.AutoCuts import get_autocuts_names
        result = []

        a = QtWidgets.QAction("autocuts", None)
        a.triggered.connect(nonpartial(self.do_autocuts))
        result.append(a)

        rng = QtWidgets.QAction("Set cuts...", None)
        rng.triggered.connect(nonpartial(self.choose_vmin_vmax))
        result.append(rng)

        a = QtWidgets.QAction("", None)
        a.setSeparator(True)
        result.append(a)

        names = list(get_autocuts_names())
        if 'clip' in names:
            # not relevant to glue
            names.remove('clip')

        for name in names:
            a = QtWidgets.QAction(name, None)
            a.triggered.connect(nonpartial(self.set_autocuts, name))
            result.append(a)

        ## rng = QtWidgets.QAction("Set params...", None)
        ## #rng.triggered.connect(nonpartial(self.choose_vmin_vmax))
        ## result.append(rng)

        return result


@viewer_tool
class DistributionMode(CheckableTool):

    tool_id = 'ginga:dist'
    icon = os.path.join(GINGA_ICON_DIR, 'histogram_48.png')
    tool_tip = ('Adjust value distribution of the image')

    def activate(self):
        self.viewer.mode_cb('dist', True)

    def deactivate(self):
        self.viewer.mode_cb('dist', False)

    def set_dist(self, name):
        gviewer = self.viewer.viewer
        gviewer.set_color_algorithm(name)

    def menu_actions(self):
        from ginga.ColorDist import get_dist_names
        result = []

        for algname in get_dist_names():
            a = QtWidgets.QAction(algname, None)
            a.triggered.connect(nonpartial(self.set_dist, algname))
            result.append(a)

        return result


class ColormapAction(QtWidgets.QAction):

    def __init__(self, label, cmap, parent):
        super(ColormapAction, self).__init__(label, parent)
        self.cmap = cmap
        pm = cmap2pixmap(cmap)
        self.setIcon(QtGui.QIcon(pm))


@viewer_tool
class ColormapMode(CheckableTool):

    icon = 'glue_rainbow'
    tool_id = 'ginga:colormap'
    action_text = 'Set color map'
    tool_tip = 'Set the color map used for the image'

    def activate(self):
        self.viewer.mode_cb('cmap', True)

    def deactivate(self):
        self.viewer.mode_cb('cmap', False)

    def menu_actions(self):
        acts = []
        for label in ginga_cmap.get_names():
            cmap = ginga_cmap.get_cmap(label)
            a = ColormapAction(label, cmap, self.viewer)
            a.triggered.connect(nonpartial(self.viewer.set_cmap, cmap))
            acts.append(a)
        return acts


@viewer_tool
class GingaSpectrumMode(GingaROIMode):

    icon = 'glue_spectrum'
    tool_id = 'ginga:spectrum'
    action_text = 'Spectrum'
    tool_tip = 'Extract a spectrum from the selection'

    def __init__(self, viewer, **kwargs):
        super(GingaSpectrumMode, self).__init__(viewer, **kwargs)

        self._shape_obj = None
        self._shape = 'rectangle'

        self.viewer.state.add_callback('reference_data', self._display_data_hook)

        self._tool = SpectrumTool(self.viewer, self)
        #self._move_callback = self._tool._move_profile

    def _display_data_hook(self, data):
        if data is not None:
            self.enabled = data.ndim == 3

    def menu_actions(self):

        result = []

        a = QtWidgets.QAction('Rectangle', None)
        a.triggered.connect(nonpartial(self.set_roi_tool, 'rectangle'))
        result.append(a)

        a = QtWidgets.QAction('Circle', None)
        a.triggered.connect(nonpartial(self.set_roi_tool, 'circle'))
        result.append(a)

        a = QtWidgets.QAction('Lasso', None)
        a.triggered.connect(nonpartial(self.set_roi_tool, 'freepolygon'))
        result.append(a)

        a = QtWidgets.QAction('Polygon', None)
        a.triggered.connect(nonpartial(self.set_roi_tool, 'polygon'))
        result.append(a)

        return result

    def set_roi_tool(self, mode):
        self._shape = mode
        self.viewer._set_roi_mode(self, mode, 'draw',
                                  color='red', linewidth=2, linestyle='solid',
                                  fill=False, alpha=1.0)

    def activate(self):
        self.set_roi_tool(self._shape)

    def deactivate(self):
        self.clear()
        self.viewer._set_roi_mode(None, self._shape, None)

    def opn_init(self, viewer, tag):
        self.clear()

    def opn_exec(self, viewer, tag, obj):
        self.clear()
        self._shape_obj = obj

        roi = ginga_graphic_to_roi(obj)
        self._tool._update_from_roi(roi)

    def clear(self):
        if self._shape_obj is not None:
            try:
                self.viewer.canvas.delete_object(self._shape_obj)
            except:
                pass
            self._shape_obj = None

    def close(self):
        self.clear()
        self._tool.close()
        return super(GingaSpectrumMode, self).close()


@viewer_tool
class GingaPVSlicerMode(GingaROIMode):

    icon = 'glue_slice'
    tool_id = 'ginga:slicer'
    action_text = 'Slice Extraction'
    tool_tip = 'Extract a slice from an arbitrary path'

    def __init__(self, viewer, **kwargs):
        super(GingaPVSlicerMode, self).__init__(viewer, **kwargs)

        self._path_obj = None
        self._shape = 'freepath'

        self.viewer.state.add_callback('reference_data', self._display_data_hook)
        self._slice_widget = None

    def _display_data_hook(self, data):
        if data is not None:
            self.enabled = data.ndim == 3

    def menu_actions(self):

        result = []

        a = QtWidgets.QAction('Freepath', None)
        a.triggered.connect(nonpartial(self.set_roi_tool, 'freepath'))
        result.append(a)

        a = QtWidgets.QAction('Path', None)
        a.triggered.connect(nonpartial(self.set_roi_tool, 'path'))
        result.append(a)

        return result

    def set_roi_tool(self, mode):
        self._shape = mode
        self.viewer._set_roi_mode(self, mode, 'draw',
                                  color='red', linewidth=2, linestyle='solid',
                                  fill=False, alpha=1.0)

    def _clear_path(self):
        if self._path_obj is not None:
            try:
                self.viewer.canvas.delete_object(self._path_obj)
            except:
                pass
            self._path_obj = None

    def activate(self):
        self.set_roi_tool(self._shape)

    def deactivate(self):
        self._clear_path()
        self.viewer._set_roi_mode(None, self._shape, None)

    _build_from_vertices = PVSlicerMode._build_from_vertices

    def opn_init(self, viewer, tag):
        self._clear_path()

    def opn_exec(self, viewer, tag, obj):
        self._clear_path()
        self._path_obj = obj

        vx, vy = zip(*obj.points)
        self._build_from_vertices(vx, vy)
