from .version import __version__  # noqa


def setup():

    try:
        import ginga  # noqa
    except ImportError:
        raise ImportError("ginga is required")

    from .qt import mouse_modes  # noqa
    from .qt.viewer_widget import GingaViewer
    from glue.config import qt_client
    qt_client.add(GingaViewer)
