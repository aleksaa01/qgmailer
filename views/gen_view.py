# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_main_view.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1120, 675)
        MainWindow.setStyleSheet("#sideBar{background-color: \"#404040\";}\n"
"\n"
"QTabBar::tab { height: 40px; width: 150px; }\n"
"QTabBar::tab::label{ font-size: 14px; font-weight: bold; }\n"
"QTabBar::tab:top { color: \"#eff0f1\"; border: 1px solid \"#76797C\"; background-color: \"#31363b\"; border-bottom: 1px transparent \"black\"; border-top-left-radius: 5px; border-top-right-radius: 5px; }\n"
"QTabBar::tab:top:hover { color: \"#eff0f1\"; border: 1px solid \"#76797C\"; background-color: \"#666666\"; border-bottom: 1px transparent \"black\"; border-top-left-radius: 5px; border-top-right-radius: 5px; }\n"
"QTabBar::tab:top:selected{ background-color: \"#23262a\";}\n"
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
        self.sideBar.setGeometry(QtCore.QRect(0, 1, 61, 673))
        self.sideBar.setObjectName("sideBar")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.sideBar)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, -5, 77, 679))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_4.setContentsMargins(0, 10, 0, 0)
        self.verticalLayout_4.setSpacing(10)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.sideBarInbox = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.sideBarInbox.setMinimumSize(QtCore.QSize(60, 60))
        self.sideBarInbox.setMaximumSize(QtCore.QSize(60, 60))
        self.sideBarInbox.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.sideBarInbox.setStyleSheet("#sideBarInbox {background: transparent; border: none;}\n"
"#sideBarInbox:hover {background: \"#666666\";}")
        self.sideBarInbox.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/inbox_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.sideBarInbox.setIcon(icon)
        self.sideBarInbox.setIconSize(QtCore.QSize(50, 50))
        self.sideBarInbox.setObjectName("sideBarInbox")
        self.verticalLayout_4.addWidget(self.sideBarInbox)
        self.sideBarSend = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.sideBarSend.setMinimumSize(QtCore.QSize(60, 60))
        self.sideBarSend.setMaximumSize(QtCore.QSize(60, 60))
        self.sideBarSend.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.sideBarSend.setStyleSheet("#sideBarSend {background: transparent; border: none;}\n"
"#sideBarSend:hover {background: \"#666666\";}")
        self.sideBarSend.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/images/send_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.sideBarSend.setIcon(icon1)
        self.sideBarSend.setIconSize(QtCore.QSize(50, 50))
        self.sideBarSend.setObjectName("sideBarSend")
        self.verticalLayout_4.addWidget(self.sideBarSend)
        self.sideBarContacts = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.sideBarContacts.setMinimumSize(QtCore.QSize(60, 60))
        self.sideBarContacts.setMaximumSize(QtCore.QSize(60, 60))
        self.sideBarContacts.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.sideBarContacts.setStyleSheet("#sideBarContacts {background: transparent; border: none;}\n"
"#sideBarContacts:hover {background: \"#666666\";}")
        self.sideBarContacts.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/images/contacts_icon2.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.sideBarContacts.setIcon(icon2)
        self.sideBarContacts.setIconSize(QtCore.QSize(50, 50))
        self.sideBarContacts.setObjectName("sideBarContacts")
        self.verticalLayout_4.addWidget(self.sideBarContacts)
        self.sideBarSent = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.sideBarSent.setMinimumSize(QtCore.QSize(60, 60))
        self.sideBarSent.setMaximumSize(QtCore.QSize(60, 60))
        self.sideBarSent.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.sideBarSent.setStyleSheet("#sideBarSent {background: transparent; border: none;}\n"
"#sideBarSent:hover {background: \"#666666\";}")
        self.sideBarSent.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/images/sent_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.sideBarSent.setIcon(icon3)
        self.sideBarSent.setIconSize(QtCore.QSize(50, 50))
        self.sideBarSent.setObjectName("sideBarSent")
        self.verticalLayout_4.addWidget(self.sideBarSent)
        self.sideBarTrash = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.sideBarTrash.setMinimumSize(QtCore.QSize(60, 60))
        self.sideBarTrash.setMaximumSize(QtCore.QSize(60, 60))
        self.sideBarTrash.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.sideBarTrash.setStyleSheet("#sideBarTrash {background: transparent; border: none;}\n"
"#sideBarTrash:hover {background: \"#666666\";}")
        self.sideBarTrash.setText("")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/images/trash_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.sideBarTrash.setIcon(icon4)
        self.sideBarTrash.setIconSize(QtCore.QSize(50, 50))
        self.sideBarTrash.setObjectName("sideBarTrash")
        self.verticalLayout_4.addWidget(self.sideBarTrash)
        self.sideBarSettings = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.sideBarSettings.setMinimumSize(QtCore.QSize(60, 60))
        self.sideBarSettings.setMaximumSize(QtCore.QSize(60, 60))
        self.sideBarSettings.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.sideBarSettings.setStyleSheet("#sideBarSettings {background: transparent; border: none;}\n"
"#sideBarSettings:hover {background: \"#666666\";}")
        self.sideBarSettings.setText("")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/images/options_button.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.sideBarSettings.setIcon(icon5)
        self.sideBarSettings.setIconSize(QtCore.QSize(50, 50))
        self.sideBarSettings.setObjectName("sideBarSettings")
        self.verticalLayout_4.addWidget(self.sideBarSettings)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem)
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
        self.chooseContactsBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.chooseContactsBtn.setStyleSheet("#chooseContactsBtn {background: transparent; border: none;}\n"
"#chooseContactsBtn:hover {background: \"#b3b3b3\"; border-radius: 15px;}")
        self.chooseContactsBtn.setText("")
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/images/choose_contact_btn.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.chooseContactsBtn.setIcon(icon6)
        self.chooseContactsBtn.setIconSize(QtCore.QSize(32, 32))
        self.chooseContactsBtn.setObjectName("chooseContactsBtn")
        self.sendMessageBtn = QtWidgets.QPushButton(self.page_2)
        self.sendMessageBtn.setGeometry(QtCore.QRect(48, 534, 67, 37))
        self.sendMessageBtn.setStyleSheet("#sendMessageBtn {background: \"#d9d9d9\"; border: none; border-radius: 5px;}\n"
"#sendMessageBtn:hover {background: \"#cccccc\";}\n"
"#sendMessageBtn:pressed {background: \"#b3b3b3\"; border-radius: 10px;}")
        self.sendMessageBtn.setObjectName("sendMessageBtn")
        self.stackedWidget.addWidget(self.page_2)
        self.page_4 = QtWidgets.QWidget()
        self.page_4.setObjectName("page_4")
        self.contactsListWidget = QtWidgets.QListWidget(self.page_4)
        self.contactsListWidget.setGeometry(QtCore.QRect(24, 12, 979, 481))
        self.contactsListWidget.setObjectName("contactsListWidget")
        self.contactsForm = QtWidgets.QWidget(self.page_4)
        self.contactsForm.setGeometry(QtCore.QRect(324, 120, 385, 217))
        self.contactsForm.setStyleSheet("background-color: \"white\";")
        self.contactsForm.setObjectName("contactsForm")
        self.contactsFormName = QtWidgets.QLineEdit(self.contactsForm)
        self.contactsFormName.setGeometry(QtCore.QRect(18, 48, 355, 25))
        self.contactsFormName.setObjectName("contactsFormName")
        self.contactsFormEmail = QtWidgets.QLineEdit(self.contactsForm)
        self.contactsFormEmail.setGeometry(QtCore.QRect(18, 120, 355, 25))
        self.contactsFormEmail.setObjectName("contactsFormEmail")
        self.nameIcon = QtWidgets.QLabel(self.contactsForm)
        self.nameIcon.setGeometry(QtCore.QRect(18, 18, 25, 25))
        self.nameIcon.setText("")
        self.nameIcon.setPixmap(QtGui.QPixmap(":/images/name_icon.png"))
        self.nameIcon.setScaledContents(True)
        self.nameIcon.setObjectName("nameIcon")
        self.emailIcon = QtWidgets.QLabel(self.contactsForm)
        self.emailIcon.setGeometry(QtCore.QRect(18, 90, 25, 25))
        self.emailIcon.setText("")
        self.emailIcon.setPixmap(QtGui.QPixmap(":/images/email_icon.png"))
        self.emailIcon.setScaledContents(True)
        self.emailIcon.setObjectName("emailIcon")
        self.contactsFormOk = QtWidgets.QPushButton(self.contactsForm)
        self.contactsFormOk.setGeometry(QtCore.QRect(18, 168, 55, 31))
        self.contactsFormOk.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.contactsFormOk.setFocusPolicy(QtCore.Qt.NoFocus)
        self.contactsFormOk.setStyleSheet("#contactsFormOk {background: \"#d9d9d9\"; border: none; border-radius: 5px;}\n"
"#contactsFormOk:hover {background: \"#cccccc\";}\n"
"#contactsFormOk:pressed {background: \"#b3b3b3\"; border-radius: 10px;}")
        self.contactsFormOk.setObjectName("contactsFormOk")
        self.contactsAdd = QtWidgets.QPushButton(self.page_4)
        self.contactsAdd.setGeometry(QtCore.QRect(24, 510, 55, 31))
        self.contactsAdd.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.contactsAdd.setFocusPolicy(QtCore.Qt.NoFocus)
        self.contactsAdd.setStyleSheet("#contactsAdd {background: \"#d9d9d9\"; border: none; border-radius: 5px;}\n"
"#contactsAdd:hover {background: \"#cccccc\";}\n"
"#contactsAdd:pressed {background: \"#b3b3b3\"; border-radius: 10px;}")
        self.contactsAdd.setObjectName("contactsAdd")
        self.stackedWidget.addWidget(self.page_4)
        self.page_5 = QtWidgets.QWidget()
        self.page_5.setObjectName("page_5")
        self.tabWidget_2 = QtWidgets.QTabWidget(self.page_5)
        self.tabWidget_2.setGeometry(QtCore.QRect(24, 12, 985, 583))
        self.tabWidget_2.setObjectName("tabWidget_2")
        self.tab_5 = QtWidgets.QWidget()
        self.tab_5.setObjectName("tab_5")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.tab_5)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.sentContainer = QtWidgets.QWidget(self.tab_5)
        self.sentContainer.setObjectName("sentContainer")
        self.verticalLayout_5.addWidget(self.sentContainer)
        self.tabWidget_2.addTab(self.tab_5, "")
        self.stackedWidget.addWidget(self.page_5)
        self.page_6 = QtWidgets.QWidget()
        self.page_6.setObjectName("page_6")
        self.tabWidget_3 = QtWidgets.QTabWidget(self.page_6)
        self.tabWidget_3.setGeometry(QtCore.QRect(24, 12, 985, 583))
        self.tabWidget_3.setObjectName("tabWidget_3")
        self.tab_7 = QtWidgets.QWidget()
        self.tab_7.setObjectName("tab_7")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.tab_7)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.trashContainer = QtWidgets.QWidget(self.tab_7)
        self.trashContainer.setObjectName("trashContainer")
        self.verticalLayout_8.addWidget(self.trashContainer)
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
        self.tabWidget_2.setCurrentIndex(0)
        self.tabWidget_3.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Personal"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Social"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("MainWindow", "Promotions"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), _translate("MainWindow", "Updates"))
        self.toLineEdit.setPlaceholderText(_translate("MainWindow", "To"))
        self.subjectLineEdit.setPlaceholderText(_translate("MainWindow", "Subject"))
        self.sendMessageBtn.setText(_translate("MainWindow", "Send"))
        self.contactsFormName.setPlaceholderText(_translate("MainWindow", "Name"))
        self.contactsFormEmail.setPlaceholderText(_translate("MainWindow", "Email"))
        self.contactsFormOk.setText(_translate("MainWindow", "OK"))
        self.contactsAdd.setText(_translate("MainWindow", "Add"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_5), _translate("MainWindow", "Sent"))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_7), _translate("MainWindow", "Trash"))

from views.icons import icons_rc
