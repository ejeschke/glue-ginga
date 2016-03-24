from glue.viewers.common.qt.data_viewer import DataViewer

class MyViewer(DataViewer):

    LABEL = "My example data viewer"

    def __init__(self, session, parent=None):
        super(MyViewer, self).__init__(session, parent=parent)
        # self.setCentralWidget(my_qt_widget)

    def add_data(self, data):
        return True
    