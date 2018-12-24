# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_main_view.ui',
# licensing of 'ui_main_view.ui' applies.
#
# Created: Mon Dec 24 02:06:52 2018
#      by: pyside2-uic  running on PySide2 5.12.0
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1120, 675)
        MainWindow.setStyleSheet("#sideBar{background-color: \"#232629\";}\n"
"\n"
"\n"
"#personalPreviousBtn, #socialPreviousBtn, #promotionsPreviousBtn, #updatesPreviousBtn, #sentPreviousBtn, #trashPreviousBtn {background: transparent; border: none;}\n"
"#personalPreviousBtn:hover, #socialPreviousBtn:hover, #promotionsPreviousBtn:hover, #updatesPreviousBtn:hover, #sentPreviousBtn:hover, #trashPreviousBtn:hover {background: \"#d9d9d9\";}\n"
"\n"
"#personalNextBtn, #socialNextBtn, #promotionsNextBtn, #updatesNextBtn, #sentNextBtn, #trashNextBtn {background: transparent; border: none;}\n"
"#personalNextBtn:hover, #socialNextBtn:hover,  #promotionsNextBtn:hover, #updatesNextBtn:hover, #sentNextBtn:hover, #trashNextBtn:hover {background: \"#d9d9d9\"}")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.sideBar = QtWidgets.QWidget(self.centralwidget)
        self.sideBar.setGeometry(QtCore.QRect(0, 0, 61, 673))
        self.sideBar.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.sideBar.setObjectName("sideBar")
        self.SideBarContainer = QtWidgets.QWidget(self.sideBar)
        self.SideBarContainer.setGeometry(QtCore.QRect(0, -5, 61, 679))
        self.SideBarContainer.setObjectName("SideBarContainer")
        self.sideBarLayout = QtWidgets.QVBoxLayout(self.SideBarContainer)
        self.sideBarLayout.setSpacing(10)
        self.sideBarLayout.setContentsMargins(0, 10, 0, 0)
        self.sideBarLayout.setObjectName("sideBarLayout")
        self.sideBarInbox = QtWidgets.QPushButton(self.SideBarContainer)
        self.sideBarInbox.setMinimumSize(QtCore.QSize(60, 60))
        self.sideBarInbox.setMaximumSize(QtCore.QSize(60, 60))
        self.sideBarInbox.setCursor(QtCore.Qt.PointingHandCursor)
        self.sideBarInbox.setStyleSheet("#sideBarInbox {background: transparent; border: none;}\n"
"#sideBarInbox:hover {background: \"#666666\";}")
        self.sideBarInbox.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/inbox_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.sideBarInbox.setIcon(icon)
        self.sideBarInbox.setIconSize(QtCore.QSize(50, 50))
        self.sideBarInbox.setObjectName("sideBarInbox")
        self.sideBarLayout.addWidget(self.sideBarInbox)
        self.sideBarSend = QtWidgets.QPushButton(self.SideBarContainer)
        self.sideBarSend.setMinimumSize(QtCore.QSize(60, 60))
        self.sideBarSend.setMaximumSize(QtCore.QSize(60, 60))
        self.sideBarSend.setCursor(QtCore.Qt.PointingHandCursor)
        self.sideBarSend.setStyleSheet("#sideBarSend {background: transparent; border: none;}\n"
"#sideBarSend:hover {background: \"#666666\";}")
        self.sideBarSend.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/images/send_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.sideBarSend.setIcon(icon1)
        self.sideBarSend.setIconSize(QtCore.QSize(50, 50))
        self.sideBarSend.setObjectName("sideBarSend")
        self.sideBarLayout.addWidget(self.sideBarSend)
        self.sideBarContacts = QtWidgets.QPushButton(self.SideBarContainer)
        self.sideBarContacts.setMinimumSize(QtCore.QSize(60, 60))
        self.sideBarContacts.setMaximumSize(QtCore.QSize(60, 60))
        self.sideBarContacts.setCursor(QtCore.Qt.PointingHandCursor)
        self.sideBarContacts.setStyleSheet("#sideBarContacts {background: transparent; border: none;}\n"
"#sideBarContacts:hover {background: \"#666666\";}")
        self.sideBarContacts.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/images/contacts_icon2.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.sideBarContacts.setIcon(icon2)
        self.sideBarContacts.setIconSize(QtCore.QSize(50, 50))
        self.sideBarContacts.setObjectName("sideBarContacts")
        self.sideBarLayout.addWidget(self.sideBarContacts)
        self.sideBarSent = QtWidgets.QPushButton(self.SideBarContainer)
        self.sideBarSent.setMinimumSize(QtCore.QSize(60, 60))
        self.sideBarSent.setMaximumSize(QtCore.QSize(60, 60))
        self.sideBarSent.setCursor(QtCore.Qt.PointingHandCursor)
        self.sideBarSent.setStyleSheet("#sideBarSent {background: transparent; border: none;}\n"
"#sideBarSent:hover {background: \"#666666\";}")
        self.sideBarSent.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/images/sent_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.sideBarSent.setIcon(icon3)
        self.sideBarSent.setIconSize(QtCore.QSize(50, 50))
        self.sideBarSent.setObjectName("sideBarSent")
        self.sideBarLayout.addWidget(self.sideBarSent)
        self.sideBarTrash = QtWidgets.QPushButton(self.SideBarContainer)
        self.sideBarTrash.setMinimumSize(QtCore.QSize(60, 60))
        self.sideBarTrash.setMaximumSize(QtCore.QSize(60, 60))
        self.sideBarTrash.setCursor(QtCore.Qt.PointingHandCursor)
        self.sideBarTrash.setStyleSheet("#sideBarTrash {background: transparent; border: none;}\n"
"#sideBarTrash:hover {background: \"#666666\";}")
        self.sideBarTrash.setText("")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/images/trash_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.sideBarTrash.setIcon(icon4)
        self.sideBarTrash.setIconSize(QtCore.QSize(50, 50))
        self.sideBarTrash.setObjectName("sideBarTrash")
        self.sideBarLayout.addWidget(self.sideBarTrash)
        self.sideBarSettings = QtWidgets.QPushButton(self.SideBarContainer)
        self.sideBarSettings.setMinimumSize(QtCore.QSize(60, 60))
        self.sideBarSettings.setMaximumSize(QtCore.QSize(60, 60))
        self.sideBarSettings.setCursor(QtCore.Qt.PointingHandCursor)
        self.sideBarSettings.setStyleSheet("#sideBarSettings {background: transparent; border: none;}\n"
"#sideBarSettings:hover {background: \"#666666\";}")
        self.sideBarSettings.setText("")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/images/options_button.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.sideBarSettings.setIcon(icon5)
        self.sideBarSettings.setIconSize(QtCore.QSize(50, 50))
        self.sideBarSettings.setObjectName("sideBarSettings")
        self.sideBarLayout.addWidget(self.sideBarSettings)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.sideBarLayout.addItem(spacerItem)
        self.stackedWidget = QtWidgets.QStackedWidget(self.centralwidget)
        self.stackedWidget.setGeometry(QtCore.QRect(72, 60, 1027, 607))
        self.stackedWidget.setObjectName("stackedWidget")
        self.page = QtWidgets.QWidget()
        self.page.setObjectName("page")
        self.tabWidget = QtWidgets.QTabWidget(self.page)
        self.tabWidget.setGeometry(QtCore.QRect(24, 12, 985, 583))
        self.tabWidget.setMinimumSize(QtCore.QSize(0, 0))
        self.tabWidget.setStyleSheet("")
        self.tabWidget.setTabPosition(QtWidgets.QTabWidget.North)
        self.tabWidget.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.personalDiv = QtWidgets.QVBoxLayout(self.tab)
        self.personalDiv.setObjectName("personalDiv")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.socialDiv = QtWidgets.QVBoxLayout(self.tab_2)
        self.socialDiv.setObjectName("socialDiv")
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.promotionsDiv = QtWidgets.QVBoxLayout(self.tab_3)
        self.promotionsDiv.setObjectName("promotionsDiv")
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QtWidgets.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.updatesDiv = QtWidgets.QVBoxLayout(self.tab_4)
        self.updatesDiv.setObjectName("updatesDiv")
        self.tabWidget.addTab(self.tab_4, "")
        self.stackedWidget.addWidget(self.page)
        self.page_2 = QtWidgets.QWidget()
        self.page_2.setObjectName("page_2")
        self.toLineEdit = QtWidgets.QLineEdit(self.page_2)
        self.toLineEdit.setGeometry(QtCore.QRect(48, 36, 409, 37))
        self.toLineEdit.setStyleSheet("#toTextEdit {border: 1px solid \"#aaaaaa\";}")
        self.toLineEdit.setObjectName("toLineEdit")
        self.subjectLineEdit = QtWidgets.QLineEdit(self.page_2)
        self.subjectLineEdit.setGeometry(QtCore.QRect(48, 78, 409, 37))
        self.subjectLineEdit.setStyleSheet("#subjectTextEdit {border: 1px solid \"#aaaaaa\";}")
        self.subjectLineEdit.setObjectName("subjectLineEdit")
        self.messageTextEdit = QtWidgets.QTextEdit(self.page_2)
        self.messageTextEdit.setGeometry(QtCore.QRect(48, 120, 949, 397))
        self.messageTextEdit.setStyleSheet("#messageTextEdit {border: 1px solid \"#aaaaaa\";}")
        self.messageTextEdit.setObjectName("messageTextEdit")
        self.chooseContactsBtn = QtWidgets.QPushButton(self.page_2)
        self.chooseContactsBtn.setGeometry(QtCore.QRect(462, 36, 30, 30))
        self.chooseContactsBtn.setCursor(QtCore.Qt.PointingHandCursor)
        self.chooseContactsBtn.setStyleSheet("#chooseContactsBtn {background: transparent; border: none;}\n"
"#chooseContactsBtn:hover {background: \"#b3b3b3\"; border-radius: 15px;}")
        self.chooseContactsBtn.setText("")
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/images/choose_contact_btn.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.chooseContactsBtn.setIcon(icon6)
        self.chooseContactsBtn.setIconSize(QtCore.QSize(32, 32))
        self.chooseContactsBtn.setObjectName("chooseContactsBtn")
        self.sendMessageBtn = QtWidgets.QPushButton(self.page_2)
        self.sendMessageBtn.setGeometry(QtCore.QRect(48, 534, 70, 40))
        self.sendMessageBtn.setCursor(QtCore.Qt.PointingHandCursor)
        self.sendMessageBtn.setStyleSheet("")
        self.sendMessageBtn.setObjectName("sendMessageBtn")
        self.stackedWidget.addWidget(self.page_2)
        self.page_4 = QtWidgets.QWidget()
        self.page_4.setObjectName("page_4")
        self.contactsAdd = QtWidgets.QPushButton(self.page_4)
        self.contactsAdd.setGeometry(QtCore.QRect(24, 510, 70, 40))
        self.contactsAdd.setCursor(QtCore.Qt.PointingHandCursor)
        self.contactsAdd.setFocusPolicy(QtCore.Qt.NoFocus)
        self.contactsAdd.setStyleSheet("")
        self.contactsAdd.setObjectName("contactsAdd")
        self.tabWidget_4 = QtWidgets.QTabWidget(self.page_4)
        self.tabWidget_4.setGeometry(QtCore.QRect(24, 16, 937, 481))
        self.tabWidget_4.setObjectName("tabWidget_4")
        self.tab_6 = QtWidgets.QWidget()
        self.tab_6.setObjectName("tab_6")
        self.contactsDiv = QtWidgets.QVBoxLayout(self.tab_6)
        self.contactsDiv.setObjectName("contactsDiv")
        self.tabWidget_4.addTab(self.tab_6, "")
        self.stackedWidget.addWidget(self.page_4)
        self.page_5 = QtWidgets.QWidget()
        self.page_5.setObjectName("page_5")
        self.tabWidget_2 = QtWidgets.QTabWidget(self.page_5)
        self.tabWidget_2.setGeometry(QtCore.QRect(24, 12, 985, 583))
        self.tabWidget_2.setObjectName("tabWidget_2")
        self.tab_5 = QtWidgets.QWidget()
        self.tab_5.setObjectName("tab_5")
        self.sentDiv = QtWidgets.QVBoxLayout(self.tab_5)
        self.sentDiv.setObjectName("sentDiv")
        self.tabWidget_2.addTab(self.tab_5, "")
        self.stackedWidget.addWidget(self.page_5)
        self.page_6 = QtWidgets.QWidget()
        self.page_6.setObjectName("page_6")
        self.tabWidget_3 = QtWidgets.QTabWidget(self.page_6)
        self.tabWidget_3.setGeometry(QtCore.QRect(24, 12, 985, 583))
        self.tabWidget_3.setObjectName("tabWidget_3")
        self.tab_7 = QtWidgets.QWidget()
        self.tab_7.setObjectName("tab_7")
        self.trashDiv = QtWidgets.QVBoxLayout(self.tab_7)
        self.trashDiv.setObjectName("trashDiv")
        self.tabWidget_3.addTab(self.tab_7, "")
        self.stackedWidget.addWidget(self.page_6)
        self.page_3 = QtWidgets.QWidget()
        self.page_3.setObjectName("page_3")
        self.containerQWebEngine = QtWidgets.QWidget(self.page_3)
        self.containerQWebEngine.setGeometry(QtCore.QRect(12, 18, 1001, 571))
        self.containerQWebEngine.setObjectName("containerQWebEngine")
        self.layoutQWebEngine = QtWidgets.QHBoxLayout(self.containerQWebEngine)
        self.layoutQWebEngine.setContentsMargins(0, 0, 0, 0)
        self.layoutQWebEngine.setObjectName("layoutQWebEngine")
        self.stackedWidget.addWidget(self.page_3)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        self.stackedWidget.setCurrentIndex(0)
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget_4.setCurrentIndex(0)
        self.tabWidget_2.setCurrentIndex(0)
        self.tabWidget_3.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "MainWindow", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtWidgets.QApplication.translate("MainWindow", "Personal", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtWidgets.QApplication.translate("MainWindow", "Social", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QtWidgets.QApplication.translate("MainWindow", "Promotions", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QtWidgets.QApplication.translate("MainWindow", "Updates", None, -1))
        self.toLineEdit.setPlaceholderText(QtWidgets.QApplication.translate("MainWindow", "To", None, -1))
        self.subjectLineEdit.setPlaceholderText(QtWidgets.QApplication.translate("MainWindow", "Subject", None, -1))
        self.sendMessageBtn.setText(QtWidgets.QApplication.translate("MainWindow", "Send", None, -1))
        self.contactsAdd.setText(QtWidgets.QApplication.translate("MainWindow", "Add", None, -1))
        self.tabWidget_4.setTabText(self.tabWidget_4.indexOf(self.tab_6), QtWidgets.QApplication.translate("MainWindow", "Contacts", None, -1))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_5), QtWidgets.QApplication.translate("MainWindow", "Sent", None, -1))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_7), QtWidgets.QApplication.translate("MainWindow", "Trash", None, -1))

from views.icons import icons_rc
