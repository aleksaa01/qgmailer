import qdarkstyle

qds = qdarkstyle.load_stylesheet_pyqt5()



PagedEmailList_STYLESHEET = qds + '''
QListView::item {
    color: "white";
    padding: 8px;
    margin: 2px;
    border: 1px solid grey;
    font-weight: bold;
    font-size: 14px;
}
QListView::item:hover {
    background-color: "#31363b";
    color: "white";
    border: 1px solid #66b3ff;
}
'''

themes = {
    'default': '',
    'dark': PagedEmailList_STYLESHEET
}