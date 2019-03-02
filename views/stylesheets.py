import qdarkstyle

qds = qdarkstyle.load_stylesheet_pyqt5() + 'QLabel { border: none; }'


PageTab = '''
QTabBar::tab {
    height: 40px;
    width: 150px;
}

QTabBar::tab::label {
    font-size: 14px;
    font-weight: bold;
}

QTabBar::tab:top {
    color: #eff0f1;
    border: 1px solid #76797C;
    background-color: #31363b;
    border-bottom: 1px transparent black;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}

QTabBar::tab:top:!selected:hover {
    color: #eff0f1;
    border: 1px solid #76797C;
    border-bottom: 1px solid #3375a3;
    background-color: #515a61;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}

QTabBar::tab:top:selected {
    background-color: #23262a;
}
'''

QListViewItems = '''
QListView::item {
    color: black;
    padding: 8px;
    margin: 2px;
    border: 1px solid grey;
    font-weight: bold;
    font-size: 14px;
}

QListView::item:hover {
    background: #d9d9d9;
    border: 1px solid #1a1a1a;
    border-radius: 3px;
}
'''


QListViewItemsDark = '''
QListView::item {
    color: white;
    padding: 8px;
    margin: 2px;
    border: 1px solid grey;
    font-weight: bold;
    font-size: 14px;
}

QListView::item:hover {
    border: 1px solid #66b3ff;
    border-radius: 3px;
}
'''

QListViewItemsOrange = '''
QListView::item {
    background-color: transparent;
    color: white;
    padding: 8px;
    margin: 2px;
    border: 1px solid grey;
    font-weight: bold;
    font-size: 14px;
}

QListView::item:!selected:hover {
    background-color: #cc6600;
    color: white;
    border: 1px solid #ffff00;
    border-radius: 3px;
}

QListView::item:selected:active, QListView::item:selected:!active {
    background-color: #e67300;
    border: 1px solid #e67300;
}
'''

SideBarOrange = '''
#SideBarContainer {
    background-color: #e67300;
}

QPushButton:hover {
    background-color: #cc6600;
    border-radius: 6px;
    border: 1px solid black;
}

QPushButton:pressed {
    border: 1px solid #d9d9d9;
    border-radius: 10px;
}
'''

PageTabOrange = '''
QTabBar::tab {
    height: 40px;
    width: 150px;
}

QTabBar::tab::label {
    font-size: 14px;
    font-weight: bold;
}

QTabBar::tab:top {
    color: #eff0f1;
    border: 1px solid #76797C;
    background-color: #e67300;
    border-bottom: 1px transparent black;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}

QTabBar::tab:top:!selected:hover {
    color: #eff0f1;
    border: 1px solid #76797C;
    background-color: #b35900;
    border-bottom: 1px transparent black;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}

QTabBar::tab:top:selected {
    background-color: #23262a;
}
'''

themes = {
    'default': PageTab + QListViewItems,
    'dark': qds + QListViewItemsDark + PageTab,
    'dark-orange': qds + QListViewItemsOrange + SideBarOrange + PageTabOrange
}