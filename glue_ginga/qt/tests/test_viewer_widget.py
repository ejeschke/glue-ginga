from __future__ import absolute_import, division, print_function

import pytest

pytest.importorskip('ginga')

from glue.viewers.common.qt.tests.test_data_viewer import BaseTestDataViewer

from ..viewer_widget import GingaViewer


class TestGingaViewer(BaseTestDataViewer):
    ndim = 2
    widget_cls = GingaViewer
