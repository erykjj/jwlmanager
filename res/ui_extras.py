#!/usr/bin/env python3

"""
  JWLManager:   JWLEditor module - Qt classes for UI components

  MIT License:  Copyright (c) 2023 Eryk J.

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.
"""

from os import path
from datetime import datetime

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QStackedLayout, QTextEdit, QToolBar, QToolButton, QVBoxLayout, QWidget


_base_path = path.dirname(__file__)


class AboutBox(QDialog):
    def __init__(self, app, version):
        super().__init__()

        year = f'MIT ©{datetime.now().year}'
        owner = 'Eryk J.'
        web = 'https://github.com/erykjj/jwlmanager'
        contact = b'\x69\x6E\x66\x69\x6E\x69\x74\x69\x40\x69\x6E\x76\x65\x6E\x74\x61\x74\x69\x2E\x6F\x72\x67'.decode('utf-8')

        self.setStyleSheet("QDialog {border:2px solid #5b3c88}")
        layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        icon = QLabel(self)
        icon.setPixmap(QPixmap(_base_path+'/icons/project_72.png'))
        icon.setAlignment(Qt.AlignTop)
        left_layout.addWidget(icon)

        right_layout = QVBoxLayout()
        title_label = QLabel(self)
        text = f'<div style="text-align:center;"><h2><span style="color:#800080;">{app}</span></h2><p><small>{year} {owner}</small></p><h4>{version.lstrip("v")}</h4></div>'
        title_label.setText(text)

        self.update_label = QLabel(self)
        self.update_label.setText(text)
        self.update_label.setOpenExternalLinks(True)

        contact_label = QLabel(self)
        text = text = f'<div style="text-align:center;"><small><a style="color:#666699; text-decoration:none;" href="mail-to:{contact}"><em>{contact}</em></a><br><a style="color:#666699; text-decoration:none;" href="{web}">{web}</small></a></div>'
        contact_label.setText(text)
        contact_label.setOpenExternalLinks(True)

        right_layout.addWidget(title_label)
        right_layout.addWidget(self.update_label)
        right_layout.addWidget(contact_label)

        button = QDialogButtonBox(QDialogButtonBox.Ok)
        button.setFixedWidth(72)
        button.accepted.connect(self.accept)

        left_layout.addWidget(button)
        layout.addLayout(left_layout)
        layout.addLayout(right_layout)
        self.setWindowFlag(Qt.FramelessWindowHint)


class HelpBox(QDialog):
    def __init__(self, title):
        super().__init__()

        self.setWindowFlags(Qt.Window)
        self.setWindowIcon((QIcon(_base_path+'/icons/project_72.png')))
        self.setWindowTitle(title)
        self.resize(1020, 812)
        self.move(50, 50)
        self.setMinimumSize(300, 300)
        text = QTextEdit(self)
        text.setReadOnly(True)
        with open(_base_path+'/HELP.md', encoding='utf-8') as f:
            text.setMarkdown(f.read())
        layout = QHBoxLayout(self)
        layout.addWidget(text)
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.finished.connect(self.hide())


class DataViewer(QDialog):
    def __init__(self, size, pos):
        super().__init__()

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.Window)
        self.setWindowIcon((QIcon(_base_path+'/icons/project_72.png')))
        self.setMinimumSize(755, 845)
        self.resize(size)
        self.move(pos)

        self.viewer_layout = QStackedLayout(self)
        self._create_viewer()
        self._create_editor()
        self.viewer_layout.setCurrentIndex(0)
        self.setLayout(self.viewer_layout)
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)

    def _create_viewer(self):
        viewer = QFrame()

        txt_button = QToolButton()
        txt_button.setMaximumWidth(60)
        txt_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        txt_button.setStyleSheet('color: #177c26; font: bold;')
        self.txt_action = QAction('TXT')
        self.txt_action.setToolTip('⇣')
        self.txt_action.setIcon(QPixmap(_base_path+'/icons/icons8-save-64grey.png'))
        txt_button.setDefaultAction(self.txt_action)

        discard_button = QToolButton()
        discard_button.setStyleSheet('color: #3f54aa; font: bold;')
        self.discard_action = QAction('')
        self.discard_action.setToolTip('✗')
        self.discard_action.setDisabled(True)
        discard_button.setDefaultAction(self.discard_action)

        confirm_button = QToolButton()
        confirm_button.setStyleSheet('color: #c80b0b; font: bold;')
        self.confirm_action = QAction('')
        self.confirm_action.setToolTip('✔')
        self.confirm_action.setDisabled(True)
        confirm_button.setDefaultAction(self.confirm_action)

        toolbar = QToolBar(viewer)
        toolbar.setFixedHeight(30)
        toolbar.addWidget(txt_button)
        toolbar.addWidget(discard_button)
        toolbar.addWidget(confirm_button)

        self.grid_layout = QGridLayout(viewer)
        self.grid_layout.setAlignment(Qt.AlignTop)
        grid_box = QFrame()
        grid_box.setFrameShape(QFrame.NoFrame)
        grid_box.sizePolicy().setVerticalPolicy(QSizePolicy.MinimumExpanding)
        grid_box.setLayout(self.grid_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidget(grid_box)
        scroll_area.setWidgetResizable(True)

        layout = QVBoxLayout(viewer)
        layout.addWidget(toolbar)
        layout.addWidget(scroll_area)
        self.viewer_layout.addWidget(viewer)

    def _create_editor(self):
        self.editor = QFrame()

        self.return_button = QToolButton()
        self.return_button.setToolButtonStyle(Qt.ToolButtonIconOnly) #Qt.ToolButtonTextBesideIcon
        self.return_action = QAction()
        self.return_action.setIcon(QPixmap(_base_path+'/icons/icons8-left-return.png'))
        self.return_button.setDefaultAction(self.return_action)

        self.accept_button = QToolButton()
        self.accept_button.setToolButtonStyle(Qt.ToolButtonIconOnly) #Qt.ToolButtonTextBesideIcon
        self.accept_action = QAction()
        self.accept_action.setIcon(QPixmap(_base_path+'/icons/icons8-accept-64green.png'))
        self.accept_button.setDefaultAction(self.accept_action)
        self.accept_action.setVisible(False)

        toolbar = QToolBar(self.editor)
        toolbar.setFixedHeight(32)
        toolbar.addWidget(self.return_button)
        toolbar.addWidget(self.accept_button)

        self.title = QPlainTextEdit(self.editor)
        self.title.setMaximumHeight(60)
        self.title.setStyleSheet('font: bold; color: #3d3d5c; font-size: 20px;')

        self.body = QPlainTextEdit(self.editor)
        self.body.setStyleSheet('font: normal; color: #3d3d5c;')

        self.meta = QLabel(self.editor)
        self.meta.setFixedHeight(80)
        self.meta.setStyleSheet('color: #7575a3;')

        layout = QVBoxLayout(self.editor)
        layout.addWidget(toolbar)
        layout.addWidget(self.title)
        layout.addWidget(self.body)
        layout.addWidget(self.meta)
        self.viewer_layout.addWidget(self.editor)


class ViewerItem(QWidget):
    def __init__(self, idx, color, text, meta):
        super().__init__()
        self.idx = idx
        self.label = None
        self.color = color
        self.text = text
        self.meta = meta
        self.body = ''
        self.title = ''
        self.meta_text = ''

        self.note_widget = QFrame()
        self.note_widget.setFixedHeight(250)
        self.note_widget.setFrameShape(QFrame.Panel)
        self.note_widget.setStyleSheet(f"background-color: {color}")

        self.text_box = QTextEdit(self.note_widget)
        self.text_box.setReadOnly(True)
        self.text_box.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.text_box.setStyleSheet('color: #3d3d5c;')
        self.text_box.sizePolicy().setHorizontalPolicy(QSizePolicy.MinimumExpanding)
        self.text_box.setText(text)

        if self.meta:
            meta_box = QLabel(self.note_widget)
            meta_box.setFixedHeight(75)
            meta_box.setWordWrap(True)
            meta_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            meta_box.setStyleSheet('color: #7575a3;')
            meta_box.setTextFormat(Qt.RichText)
            meta_box.setText(meta)

        self.delete_button = QPushButton()
        self.delete_button.setIcon(QPixmap(_base_path+'/icons/icons8-delete-64red.png'))
        self.delete_button.setIconSize(QSize(24, 24))
        self.delete_button.setStyleSheet("QPushButton { background-color: transparent; font-size: 1px; border: 0px; color: transparent; }")

        self.edit_button = QPushButton()
        self.edit_button.setIcon(QPixmap(_base_path+'/icons/icons8-edit-64blue.png'))
        self.edit_button.setIconSize(QSize(22, 22))
        self.edit_button.setStyleSheet("QPushButton { background-color: transparent; font-size: 1px; border: 0px; color: transparent; }")

        layout = QGridLayout(self.note_widget)
        layout.addWidget(self.text_box, 0 , 0, 1, 0)
        
        if self.meta:
            layout.addWidget(meta_box, 1, 0)
            button_layout = QVBoxLayout()
            button_layout.addWidget(self.delete_button)
            button_layout.addWidget(self.edit_button)
            button_frame = QFrame()
            button_frame.setMaximumWidth(50)
            button_frame.setLayout(button_layout)
            layout.addWidget(button_frame, 1, 1, Qt.AlignmentFlag.AlignRight)
        else:
            button_layout = QHBoxLayout()
            button_layout.addWidget(self.delete_button)
            button_layout.addWidget(self.edit_button)
            button_frame = QFrame()
            button_frame.setLayout(button_layout)
            layout.addWidget(button_frame, 1, 0)
