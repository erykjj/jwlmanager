# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_windowtLaiAV.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

import os, sys
from res.ui_extras import CustomTreeWidget

from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect, QSize, Qt)
from PySide6.QtGui import (QAction, QActionGroup, QFont, QIcon)
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QMenu, QMenuBar, QPushButton, QSizePolicy, QSpacerItem, QStatusBar, QTreeWidgetItem, QVBoxLayout, QWidget)


class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(728, 795)
        MainWindow.setMinimumSize(QSize(728, 795))
        MainWindow.setMaximumSize(QSize(1600, 1200))
        MainWindow.setSizeIncrement(QSize(0, 0))
        icon = QIcon()
        icon.addFile(self.resource_path(f'res/icons/JWLManager.png'), QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setUnifiedTitleAndToolBarOnMac(False)
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionOpen.setProperty('icon_name', 'open')
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSave.setEnabled(False)
        self.actionSave.setProperty('icon_name', 'save')
        self.actionReindex = QAction(MainWindow)
        self.actionReindex.setObjectName(u"actionReindex")
        self.actionReindex.setEnabled(False)
        self.actionReindex.setProperty('icon_name', 'database')
        self.actionQuit = QAction(MainWindow)
        self.actionQuit.setObjectName(u"actionQuit")
        self.actionQuit.setProperty('icon_name', 'leave')
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        self.actionAbout.setProperty('icon_name', 'info')
        self.actionHelp = QAction(MainWindow)
        self.actionHelp.setObjectName(u"actionHelp")
        self.actionHelp.setEnabled(True)
        self.actionHelp.setProperty('icon_name', 'help')
        self.actionSave_As = QAction(MainWindow)
        self.actionSave_As.setObjectName(u"actionSave_As")
        self.actionSave_As.setEnabled(False)
        self.actionSave_As.setProperty('icon_name', 'save-as')
        self.actionExpand_All = QAction(MainWindow)
        self.actionExpand_All.setObjectName(u"actionExpand_All")
        self.actionExpand_All.setEnabled(False)
        self.actionExpand_All.setProperty('icon_name', 'expand')
        self.actionCollapse_All = QAction(MainWindow)
        self.actionCollapse_All.setObjectName(u"actionCollapse_All")
        self.actionCollapse_All.setEnabled(False)
        self.actionCollapse_All.setProperty('icon_name', 'collapse')
        self.actionSelect_All = QAction(MainWindow)
        self.actionSelect_All.setObjectName(u"actionSelect_All")
        self.actionSelect_All.setEnabled(False)
        self.actionSelect_All.setProperty('icon_name', 'double-tick')
        self.actionUnselect_All = QAction(MainWindow)
        self.actionUnselect_All.setObjectName(u"actionUnselect_All")
        self.actionUnselect_All.setEnabled(False)
        self.actionUnselect_All.setProperty('icon_name', 'unchecked')
        self.actionCode_Title = QAction(MainWindow)
        self.actionCode_Title.setObjectName(u"actionCode_Title")
        self.actionCode_Title.setCheckable(True)
        self.actionCode_Title.setChecked(False)
        self.actionShort_Title = QAction(MainWindow)
        self.actionShort_Title.setObjectName(u"actionShort_Title")
        self.actionShort_Title.setCheckable(True)
        self.actionShort_Title.setChecked(True)
        self.actionFull_Title = QAction(MainWindow)
        self.actionFull_Title.setObjectName(u"actionFull_Title")
        self.actionFull_Title.setCheckable(True)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionNew.setProperty('icon_name', 'add-file')
        self.actionObscure = QAction(MainWindow)
        self.actionObscure.setObjectName(u"actionObscure")
        self.actionObscure.setEnabled(False)
        self.actionObscure.setProperty('icon_name', 'invisible')
        self.actionEN = QAction(MainWindow)
        self.actionEN.setObjectName(u"actionEN")
        self.actionEN.setCheckable(True)
        self.actionEN.setChecked(False)
        self.actionES = QAction(MainWindow)
        self.actionES.setObjectName(u"actionES")
        self.actionES.setCheckable(True)
        self.actionDE = QAction(MainWindow)
        self.actionDE.setObjectName(u"actionDE")
        self.actionDE.setCheckable(True)
        self.actionFR = QAction(MainWindow)
        self.actionFR.setObjectName(u"actionFR")
        self.actionFR.setCheckable(True)
        self.actionPT = QAction(MainWindow)
        self.actionPT.setObjectName(u"actionPT")
        self.actionPT.setCheckable(True)
        self.actionIT = QAction(MainWindow)
        self.actionIT.setObjectName(u"actionIT")
        self.actionIT.setCheckable(True)
        self.actionRU = QAction(MainWindow)
        self.actionRU.setObjectName(u"actionRU")
        self.actionRU.setCheckable(True)
        self.actionSort = QAction(MainWindow)
        self.actionSort.setObjectName(u"actionSort")
        self.actionSort.setEnabled(False)
        self.actionSort.setProperty('icon_name', 'sort')
        self.actionPL = QAction(MainWindow)
        self.actionPL.setObjectName(u"actionPL")
        self.actionPL.setCheckable(True)
        self.actionUK = QAction(MainWindow)
        self.actionUK.setObjectName(u"actionUK")
        self.actionUK.setCheckable(True)
        self.actionUK.setEnabled(True)
        self.actionTheme = QAction(MainWindow)
        self.actionTheme.setObjectName(u"actionTheme")
        self.actionTheme.setProperty('icon_name', 'toggle')
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setMinimumSize(QSize(728, 747))
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame_info = QFrame(self.centralwidget)
        self.frame_info.setObjectName(u"frame_info")
        self.frame_info.setProperty('class', 'info')
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frame_info.sizePolicy().hasHeightForWidth())
        self.frame_info.setSizePolicy(sizePolicy1)
        self.frame_info.setMinimumSize(QSize(710, 75))
        self.frame_info.setMaximumSize(QSize(1600, 75))
        self.frame_info.setSizeIncrement(QSize(0, 0))
        self.frame_info.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_info.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_info)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.info = QWidget(self.frame_info)
        self.info.setObjectName(u"info")
        self.info.setMinimumSize(QSize(460, 60))
        self.info.setMaximumSize(QSize(460, 60))
        self.combo_grouping = QComboBox(self.info)
        self.combo_grouping.addItem("")
        self.combo_grouping.addItem("")
        self.combo_grouping.addItem("")
        self.combo_grouping.addItem("")
        self.combo_grouping.addItem("")
        self.combo_grouping.addItem("")
        self.combo_grouping.setObjectName(u"combo_grouping")
        self.combo_grouping.setEnabled(False)
        self.combo_grouping.setGeometry(QRect(320, 30, 140, 28))
        self.total = QLabel(self.info)
        self.total.setObjectName(u"total")
        self.total.setGeometry(QRect(110, 1, 60, 28))
        self.total.setTextFormat(Qt.TextFormat.MarkdownText)
        self.total.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.label_grouping = QLabel(self.info)
        self.label_grouping.setObjectName(u"label_grouping")
        self.label_grouping.setGeometry(QRect(180, 30, 140, 28))
        self.selected = QLabel(self.info)
        self.selected.setObjectName(u"selected")
        self.selected.setGeometry(QRect(110, 31, 60, 28))
        self.selected.setTextFormat(Qt.TextFormat.MarkdownText)
        self.selected.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.label_selected = QLabel(self.info)
        self.label_selected.setObjectName(u"label_selected")
        self.label_selected.setGeometry(QRect(0, 30, 110, 28))
        self.label_category = QLabel(self.info)
        self.label_category.setObjectName(u"label_category")
        self.label_category.setGeometry(QRect(180, 0, 140, 28))
        self.combo_category = QComboBox(self.info)
        self.combo_category.addItem("")
        self.combo_category.addItem("")
        self.combo_category.addItem("")
        self.combo_category.addItem("")
        self.combo_category.addItem("")
        self.combo_category.addItem("")
        self.combo_category.setObjectName(u"combo_category")
        self.combo_category.setEnabled(False)
        self.combo_category.setGeometry(QRect(320, 0, 140, 28))
        self.label_total = QLabel(self.info)
        self.label_total.setObjectName(u"label_total")
        self.label_total.setGeometry(QRect(0, 0, 110, 28))
        self.total.raise_()
        self.label_grouping.raise_()
        self.selected.raise_()
        self.label_selected.raise_()
        self.label_category.raise_()
        self.label_total.raise_()
        self.combo_category.raise_()
        self.combo_grouping.raise_()

        self.horizontalLayout.addWidget(self.info)

        self.horizontalSpacer = QSpacerItem(10, 10, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.buttons = QWidget(self.frame_info)
        self.buttons.setObjectName(u"buttons")
        self.buttons.setMinimumSize(QSize(175, 60))
        self.buttons.setMaximumSize(QSize(175, 60))
        self.button_import = QPushButton(self.buttons)
        self.button_import.setObjectName(u"button_import")
        self.button_import.setEnabled(False)
        self.button_import.setGeometry(QRect(90, 30, 85, 28))
        self.button_export = QPushButton(self.buttons)
        self.button_export.setObjectName(u"button_export")
        self.button_export.setEnabled(False)
        self.button_export.setGeometry(QRect(90, 0, 85, 28))
        self.button_delete = QPushButton(self.buttons)
        self.button_delete.setObjectName(u"button_delete")
        self.button_delete.setEnabled(False)
        self.button_delete.setGeometry(QRect(0, 30, 85, 28))
        self.button_add = QPushButton(self.buttons)
        self.button_add.setObjectName(u"button_add")
        self.button_add.setEnabled(True)
        self.button_add.setGeometry(QRect(0, 0, 85, 28))
        self.button_view = QPushButton(self.buttons)
        self.button_view.setObjectName(u"button_view")
        self.button_view.setEnabled(False)
        self.button_view.setGeometry(QRect(0, 0, 85, 28))
        self.button_import.setProperty('class', 'button')
        self.button_export.setProperty('class', 'button')
        self.button_delete.setProperty('class', 'button')
        self.button_add.setProperty('class', 'button')
        self.button_view.setProperty('class', 'button')

        self.horizontalLayout.addWidget(self.buttons)


        self.verticalLayout.addWidget(self.frame_info)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.treeWidget = CustomTreeWidget(self.centralwidget)
        font = QFont()
        font.setBold(True)
        self.treeWidget.headerItem().setText(0, "")
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setTextAlignment(1, Qt.AlignCenter);
        __qtreewidgetitem.setFont(1, font);
        __qtreewidgetitem.setTextAlignment(0, Qt.AlignCenter);
        __qtreewidgetitem.setFont(0, font);
        self.treeWidget.setHeaderItem(__qtreewidgetitem)
        self.treeWidget.setObjectName(u"treeWidget")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.treeWidget.sizePolicy().hasHeightForWidth())
        self.treeWidget.setSizePolicy(sizePolicy2)
        self.treeWidget.setMinimumSize(QSize(680, 641))
        self.treeWidget.setAlternatingRowColors(True)
        self.treeWidget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.treeWidget.setAllColumnsShowFocus(True)
        self.treeWidget.setColumnCount(2)
        self.treeWidget.header().setMinimumSectionSize(150)
        self.treeWidget.header().setDefaultSectionSize(500)
        self.treeWidget.header().setHighlightSections(False)
        self.treeWidget.header().setProperty(u"showSortIndicator", True)
        self.treeWidget.header().setStretchLastSection(True)

        self.gridLayout.addWidget(self.treeWidget, 0, 0, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 728, 32))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuFile.setToolTipsVisible(True)
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
        self.menuView.setToolTipsVisible(True)
        self.menuTitle_View = QMenu(self.menuView)
        self.menuTitle_View.setObjectName(u"menuTitle_View")
        self.menuTitle_View.setEnabled(False)
        self.menuTitle_View.setProperty('icon_name', 'list')
        self.menuTitle_View.setProperty('icon_name', 'list')
        self.menuTitle_View.setToolTipsVisible(True)
        self.menuLanguage = QMenu(self.menuView)
        self.menuLanguage.setObjectName(u"menuLanguage")
        self.menuLanguage.setProperty('icon_name', 'language')
        self.menuLanguage.setToolTipsVisible(True)
        self.menuUtilities = QMenu(self.menubar)
        self.menuUtilities.setObjectName(u"menuUtilities")
        self.menuUtilities.setToolTipsVisible(True)
        MainWindow.setMenuBar(self.menubar)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        self.statusBar.setSizeGripEnabled(False)
        MainWindow.setStatusBar(self.statusBar)
        self.label_grouping.setBuddy(self.combo_grouping)
        self.label_category.setBuddy(self.combo_category)
        QWidget.setTabOrder(self.combo_category, self.combo_grouping)
        QWidget.setTabOrder(self.combo_grouping, self.button_export)
        QWidget.setTabOrder(self.button_export, self.button_delete)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuUtilities.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSave_As)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menuHelp.addAction(self.actionHelp)
        self.menuHelp.addSeparator()
        self.menuHelp.addAction(self.actionAbout)
        self.menuView.addAction(self.actionTheme)
        self.menuView.addAction(self.menuLanguage.menuAction())
        self.menuView.addSeparator()
        self.menuView.addAction(self.actionExpand_All)
        self.menuView.addAction(self.actionCollapse_All)
        self.menuView.addSeparator()
        self.menuView.addAction(self.actionSelect_All)
        self.menuView.addAction(self.actionUnselect_All)
        self.menuView.addSeparator()
        self.menuView.addAction(self.menuTitle_View.menuAction())
        self.menuTitle_View.addAction(self.actionCode_Title)
        self.menuTitle_View.addAction(self.actionShort_Title)
        self.menuTitle_View.addAction(self.actionFull_Title)
        self.menuLanguage.addAction(self.actionEN)
        self.menuLanguage.addAction(self.actionDE)
        self.menuLanguage.addAction(self.actionES)
        self.menuLanguage.addAction(self.actionFR)
        self.menuLanguage.addAction(self.actionIT)
        self.menuLanguage.addAction(self.actionPL)
        self.menuLanguage.addAction(self.actionPT)
        self.menuLanguage.addAction(self.actionRU)
        self.menuLanguage.addAction(self.actionUK)
        self.langChoices = QActionGroup(self.menuLanguage)
        self.langChoices.addAction(self.actionEN)
        self.langChoices.addAction(self.actionDE)
        self.langChoices.addAction(self.actionES)
        self.langChoices.addAction(self.actionFR)
        self.langChoices.addAction(self.actionIT)
        self.langChoices.addAction(self.actionPL)
        self.langChoices.addAction(self.actionPT)
        self.langChoices.addAction(self.actionRU)
        self.titleChoices = QActionGroup(self.menuTitle_View)
        self.titleChoices.addAction(self.actionCode_Title)
        self.titleChoices.addAction(self.actionShort_Title)
        self.titleChoices.addAction(self.actionFull_Title)
        self.menuUtilities.addAction(self.actionObscure)
        self.menuUtilities.addAction(self.actionReindex)
        self.menuUtilities.addAction(self.actionSort)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"JWLManager", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"&Open\u2026", None))
        self.actionOpen.setToolTip(QCoreApplication.translate("MainWindow", u"Open an archive", None))
        self.actionOpen.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+O", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"&Save", None))
        self.actionSave.setToolTip(QCoreApplication.translate("MainWindow", u"Save archive", None))
        self.actionSave.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+S", None))
        self.actionReindex.setText(QCoreApplication.translate("MainWindow", u"&Reindex", None))
        self.actionReindex.setToolTip(QCoreApplication.translate("MainWindow", u"Optimize database", None))
        self.actionQuit.setText(QCoreApplication.translate("MainWindow", u"&Quit", None))
        self.actionQuit.setToolTip(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionQuit.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+Q", None))
        self.actionAbout.setText(QCoreApplication.translate("MainWindow", u"&About\u2026", None))
        self.actionAbout.setIconText(QCoreApplication.translate("MainWindow", u"About\u2026", None))
        self.actionHelp.setText(QCoreApplication.translate("MainWindow", u"&Help", None))
        self.actionSave_As.setText(QCoreApplication.translate("MainWindow", u"Save &As\u2026", None))
        self.actionSave_As.setToolTip(QCoreApplication.translate("MainWindow", u"Save archive as\u2026", None))
        self.actionSave_As.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+Alt+S", None))
        self.actionExpand_All.setText(QCoreApplication.translate("MainWindow", u"E&xpand All", None))
        self.actionExpand_All.setToolTip(QCoreApplication.translate("MainWindow", u"Expand all items", None))
        self.actionExpand_All.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+E", None))
        self.actionCollapse_All.setText(QCoreApplication.translate("MainWindow", u"&Collapse All", None))
        self.actionCollapse_All.setToolTip(QCoreApplication.translate("MainWindow", u"Collapse all items", None))
        self.actionCollapse_All.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+C", None))
        self.actionSelect_All.setText(QCoreApplication.translate("MainWindow", u"&Select All", None))
        self.actionSelect_All.setToolTip(QCoreApplication.translate("MainWindow", u"Select all items", None))
        self.actionSelect_All.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+A", None))
        self.actionUnselect_All.setText(QCoreApplication.translate("MainWindow", u"&Unselect All", None))
        self.actionUnselect_All.setToolTip(QCoreApplication.translate("MainWindow", u"Unselect all items", None))
        self.actionUnselect_All.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+Z", None))
        self.actionCode_Title.setText(QCoreApplication.translate("MainWindow", u"&Code", None))
        self.actionCode_Title.setToolTip(QCoreApplication.translate("MainWindow", u"Use publication code as title", None))
        self.actionShort_Title.setText(QCoreApplication.translate("MainWindow", u"&Short", None))
        self.actionShort_Title.setIconText(QCoreApplication.translate("MainWindow", u"Short", None))
        self.actionShort_Title.setToolTip(QCoreApplication.translate("MainWindow", u"Use short publication title", None))
        self.actionFull_Title.setText(QCoreApplication.translate("MainWindow", u"&Full", None))
        self.actionFull_Title.setIconText(QCoreApplication.translate("MainWindow", u"Full", None))
        self.actionFull_Title.setToolTip(QCoreApplication.translate("MainWindow", u"Use full publication title", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"&New", None))
        self.actionNew.setToolTip(QCoreApplication.translate("MainWindow", u"Create an empty archive", None))
        self.actionNew.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+N", None))
        self.actionObscure.setText(QCoreApplication.translate("MainWindow", u"&Mask", None))
        self.actionObscure.setToolTip(QCoreApplication.translate("MainWindow", u"Mask text data", None))
        self.actionEN.setText(QCoreApplication.translate("MainWindow", u"English", None))
        self.actionEN.setToolTip(QCoreApplication.translate("MainWindow", u"en", None))
        self.actionES.setText(QCoreApplication.translate("MainWindow", u"Espa\u00f1ol", None))
        self.actionES.setToolTip(QCoreApplication.translate("MainWindow", u"es", None))
        self.actionDE.setText(QCoreApplication.translate("MainWindow", u"Deutsch", None))
        self.actionDE.setToolTip(QCoreApplication.translate("MainWindow", u"de", None))
        self.actionFR.setText(QCoreApplication.translate("MainWindow", u"Fran\u00e7ais", None))
        self.actionFR.setToolTip(QCoreApplication.translate("MainWindow", u"fr", None))
        self.actionPT.setText(QCoreApplication.translate("MainWindow", u"Portugu\u00eas", None))
        self.actionPT.setToolTip(QCoreApplication.translate("MainWindow", u"pt", None))
        self.actionIT.setText(QCoreApplication.translate("MainWindow", u"Italiano", None))
        self.actionIT.setToolTip(QCoreApplication.translate("MainWindow", u"it", None))
        self.actionRU.setText(QCoreApplication.translate("MainWindow", u"P\u0443\u0441\u0441\u043a\u0438\u0439", None))
        self.actionRU.setToolTip(QCoreApplication.translate("MainWindow", u"ru", None))
        self.actionSort.setText(QCoreApplication.translate("MainWindow", u"&Sort", None))
        self.actionSort.setToolTip(QCoreApplication.translate("MainWindow", u"Sort Notes", None))
        self.actionPL.setText(QCoreApplication.translate("MainWindow", u"Polski", None))
        self.actionPL.setToolTip(QCoreApplication.translate("MainWindow", u"pl", None))
        self.actionUK.setText(QCoreApplication.translate("MainWindow", u"\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430", None))
        self.actionUK.setToolTip(QCoreApplication.translate("MainWindow", u"uk", None))
        self.actionTheme.setText(QCoreApplication.translate("MainWindow", u"&Theme", None))
        self.actionTheme.setToolTip(QCoreApplication.translate("MainWindow", u"Toggle theme", None))
        self.actionTheme.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+T", None))
        self.combo_grouping.setItemText(0, QCoreApplication.translate("MainWindow", u"Title", None))
        self.combo_grouping.setItemText(1, QCoreApplication.translate("MainWindow", u"Type", None))
        self.combo_grouping.setItemText(2, QCoreApplication.translate("MainWindow", u"Language", None))
        self.combo_grouping.setItemText(3, QCoreApplication.translate("MainWindow", u"Year", None))
        self.combo_grouping.setItemText(4, QCoreApplication.translate("MainWindow", u"Tag", None))
        self.combo_grouping.setItemText(5, QCoreApplication.translate("MainWindow", u"Color", None))

        self.combo_grouping.setToolTip("")
        self.total.setText("")
        self.label_grouping.setToolTip("")
        self.label_grouping.setText(QCoreApplication.translate("MainWindow", u"Grouping:", None))
        self.selected.setText("")
        self.label_selected.setText(QCoreApplication.translate("MainWindow", u"Selected:", None))
        self.label_category.setToolTip("")
        self.label_category.setText(QCoreApplication.translate("MainWindow", u"Category:", None))
        self.combo_category.setItemText(0, QCoreApplication.translate("MainWindow", u"Notes", None))
        self.combo_category.setItemText(1, QCoreApplication.translate("MainWindow", u"Highlights", None))
        self.combo_category.setItemText(2, QCoreApplication.translate("MainWindow", u"Favorites", None))
        self.combo_category.setItemText(3, QCoreApplication.translate("MainWindow", u"Bookmarks", None))
        self.combo_category.setItemText(4, QCoreApplication.translate("MainWindow", u"Annotations", None))
        self.combo_category.setItemText(5, QCoreApplication.translate("MainWindow", u"Playlists", None))

        self.combo_category.setToolTip("")
        self.label_total.setText(QCoreApplication.translate("MainWindow", u"Total:", None))
        self.button_import.setText(QCoreApplication.translate("MainWindow", u"Import", None))
        self.button_export.setText(QCoreApplication.translate("MainWindow", u"Export", None))
        self.button_delete.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.button_add.setText(QCoreApplication.translate("MainWindow", u"Add", None))
        self.button_view.setText(QCoreApplication.translate("MainWindow", u"View", None))
        ___qtreewidgetitem = self.treeWidget.headerItem()
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("MainWindow", u"Count", None));
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"&File", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"&Help", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", u"&View", None))
        self.menuTitle_View.setToolTip(QCoreApplication.translate("MainWindow", u"Title display format", None))
        self.menuTitle_View.setTitle(QCoreApplication.translate("MainWindow", u"Title &View", None))
        self.menuLanguage.setToolTip(QCoreApplication.translate("MainWindow", u"Switch language", None))
        self.menuLanguage.setTitle(QCoreApplication.translate("MainWindow", u"&Language", None))
        self.menuUtilities.setTitle(QCoreApplication.translate("MainWindow", u"&Utilities", None))

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath('.')
        return os.path.join(base_path, relative_path)
