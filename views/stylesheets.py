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

AnimatedCheckButton {
    border-radius: 2px;
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

dark_theme_styles = '''
#PageIndexButton {
    background-color: #505F69;
    border: 1px solid #32414B;
    color: #F0F0F0;
    border-radius: 4px;
    padding: 1px;
    outline: none;
}
#PageIndexButton:disabled {
  background-color: #32414B;
  border: 1px solid #32414B;
  color: #787878;
  border-radius: 4px;
  padding: 1px;
}
#PageIndexButton:hover {
    border: 1px solid #148CD2;
    color: #F0F0F0;
}
'''

themes = {
    'default': PageTab + QListViewItems,
    'dark': qds + QListViewItemsDark + PageTab + dark_theme_styles,
}