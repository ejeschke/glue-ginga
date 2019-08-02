from __future__ import absolute_import, division, print_function

import pytest

pytest.importorskip('ginga')

import os

import numpy as np
from mock import MagicMock, patch

from glue.core import Data, DataCollection
from glue.app.qt import GlueApplication

from glue.core.tests.util import simple_session
from glue.utils.qt import process_events

from ..viewer_widget import GingaViewer


class TestGingaViewer:
    ndim = 2
    widget_cls = GingaViewer

    ndim = 1

    @pytest.mark.skipif(os.environ.get('CONTINUOUS_INTEGRATION', False),
                        reason="too interative for CI")
    def test_unregister_on_close(self):
        session = simple_session()
        hub = session.hub

        w = self.widget_cls(session)
        w.register_to_hub(hub)
        with patch.object(w, 'unregister') as unregister:
            w.close()
        unregister.assert_called_once_with(hub)

    def test_single_draw_call_on_create(self):
        d = Data(x=np.random.random((2,) * self.ndim))
        dc = DataCollection([d])
        app = GlueApplication(dc)

        try:
            from glue.viewers.matplotlib.qt.widget import MplCanvas
            draw = MplCanvas.draw
            MplCanvas.draw = MagicMock()

            app.new_data_viewer(self.widget_cls, data=d)

            # each Canvas instance gives at most 1 draw call
            selfs = [c[0][0] for c in MplCanvas.draw.call_arg_list]
            assert len(set(selfs)) == len(selfs)
        finally:
            MplCanvas.draw = draw
        app.close()

    def test_close_on_last_layer_remove(self):

        # regression test for 391

        d1 = Data(x=np.random.random((2,) * self.ndim))
        d2 = Data(y=np.random.random((2,) * self.ndim))
        dc = DataCollection([d1, d2])
        app = GlueApplication(dc)
        w = app.new_data_viewer(self.widget_cls, data=d1)
        w.add_data(d2)
        process_events()
        assert len(app.viewers[0]) == 1
        dc.remove(d1)
        process_events()
        assert len(app.viewers[0]) == 1
        dc.remove(d2)
        process_events()
        assert len(app.viewers[0]) == 0
        app.close()

    def test_viewer_size(self, tmpdir):

        # regression test for #781
        # viewers were not restored with the right size

        d1 = Data(x=np.random.random((2,) * self.ndim))
        d2 = Data(x=np.random.random((2,) * self.ndim))
        dc = DataCollection([d1, d2])
        app = GlueApplication(dc)
        w = app.new_data_viewer(self.widget_cls, data=d1)
        w.viewer_size = (300, 400)

        filename = tmpdir.join('session.glu').strpath
        app.save_session(filename, include_data=True)

        app2 = GlueApplication.restore_session(filename)

        for viewer in app2.viewers:
            assert viewer[0].viewer_size == (300, 400)

        app.close()
        app2.close()
