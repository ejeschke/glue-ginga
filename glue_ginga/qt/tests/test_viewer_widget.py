import os
import pytest

pytest.importorskip('ginga')

from glue.viewers.common.qt.tests.test_data_viewer import BaseTestDataViewer  # noqa
from ..viewer_widget import GingaViewer  # noqa


@pytest.mark.skipif(os.environ.get('CONTINUOUS_INTEGRATION', False) == 'true',
                    reason="too interative for CI")
class TestGingaViewer(BaseTestDataViewer):
    ndim = 2
    widget_cls = GingaViewer
