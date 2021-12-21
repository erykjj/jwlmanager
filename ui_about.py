# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'aboutUezkMi.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.setWindowModality(Qt.NonModal)
        Dialog.resize(240, 149)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QSize(240, 100))
        Dialog.setMaximumSize(QSize(240, 170))
        icon1 = QIcon()
        icon1.addFile(u"icons/project_36.ico", QSize(), QIcon.Normal, QIcon.Off)
        Dialog.setWindowIcon(icon1)
        Dialog.setModal(False)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(97, 110, 100, 32))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.label_app = QLabel(Dialog)
        self.label_app.setObjectName(u"label_app")
        self.label_app.setGeometry(QRect(70, 20, 150, 31))
        font = QFont()
        font.setPointSize(13)
        self.label_app.setFont(font)
        self.label_app.setTextFormat(Qt.MarkdownText)
        self.label_app.setAlignment(Qt.AlignCenter)
        self.label_version = QLabel(Dialog)
        self.label_version.setObjectName(u"label_version")
        self.label_version.setGeometry(QRect(70, 60, 150, 31))
        self.label_version.setMaximumSize(QSize(241, 16777215))
        self.label_version.setTextFormat(Qt.MarkdownText)
        self.label_version.setAlignment(Qt.AlignCenter)
        self.label_copyright = QLabel(Dialog)
        self.label_copyright.setObjectName(u"label_copyright")
        self.label_copyright.setGeometry(QRect(70, 80, 150, 18))
        self.label_copyright.setMaximumSize(QSize(241, 16777215))
        font1 = QFont()
        font1.setPointSize(10)
        self.label_copyright.setFont(font1)
        self.label_copyright.setTextFormat(Qt.MarkdownText)
        self.label_copyright.setAlignment(Qt.AlignCenter)
        self.icon = QLabel(Dialog)
        self.icon.setObjectName(u"icon")
        self.icon.setGeometry(QRect(10, 20, 61, 71))
        self.icon.setAutoFillBackground(True)
        self.icon.setFrameShape(QFrame.NoFrame)
        self.icon.setFrameShadow(QFrame.Sunken)
        self.icon.setPixmap(QPixmap(u"icons/project_56.png"))
        self.icon.setScaledContents(False)
        self.icon.setAlignment(Qt.AlignCenter)
        self.icon.raise_()
        self.buttonBox.raise_()
        self.label_app.raise_()
        self.label_version.raise_()
        self.label_copyright.raise_()

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.close)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle("")
        self.label_app.setText("")
        self.label_version.setText("")
        self.label_copyright.setText("")
        self.icon.setText("")
    # retranslateUi

