#!/usr/bin/env python3

"""
  File:           JWLEditor module

  MIT License     Copyright (c) 2023 Eryk J.

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

import os, sys
from datetime import datetime

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QStackedLayout, QTextEdit, QToolBar, QToolButton, QVBoxLayout, QWidget


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


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
        icon.setPixmap(QPixmap(resource_path('res/icons/project_72.png')))
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


class DataViewer(QDialog):
    def __init__(self, size, pos):
        super().__init__()

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.Window)
        self.setWindowIcon((QIcon(resource_path('res/icons/project_72.png'))))
        self.setMinimumSize(750, 846)
        self.resize(size)
        self.move(pos)

        self.viewer_layout = QStackedLayout(self)
        self.viewer = QFrame()
        self.editor = QFrame()
        
        self.viewer_layout.addWidget(self.viewer)
        self.viewer_layout.addWidget(self.editor)

        self.create_viewer()
        self.create_editor()

        self.viewer_layout.setCurrentIndex(0)
        self.setLayout(self.viewer_layout)
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)

    def create_viewer(self):
        tool_button = QToolButton()
        tool_button.setMaximumWidth(60)
        tool_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.button_TXT = QAction('TXT')
        self.button_TXT.setIcon(QPixmap(resource_path('res/icons/icons8-save-64grey.png')))
        tool_button.setDefaultAction(self.button_TXT)

        toolbar = QToolBar(self)
        toolbar.setFixedHeight(30)
        toolbar.addWidget(tool_button)

        self.grid_layout = QGridLayout()
        self.grid_layout.setAlignment(Qt.AlignTop)
        grid_box = QFrame()
        grid_box.setFrameShape(QFrame.NoFrame)
        grid_box.sizePolicy().setVerticalPolicy(QSizePolicy.MinimumExpanding)
        grid_box.setLayout(self.grid_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidget(grid_box)
        scroll_area.setWidgetResizable(True)

        layout = QVBoxLayout(self.viewer)
        layout.addWidget(toolbar)
        layout.addWidget(scroll_area)

    def create_editor(self):
        return_button = QToolButton()
        return_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.return_action = QAction('Original')
        self.return_action.setIcon(QPixmap(resource_path('res/icons/icons8-return-50.png')))
        return_button.setDefaultAction(self.return_action)

        delete_button = QToolButton()
        delete_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.delete_action = QAction('Original')
        self.delete_action.setIcon(QPixmap(resource_path('res/icons/icons8-delete-64.png')))
        delete_button.setDefaultAction(self.delete_action)

        toolbar = QToolBar(self.editor)
        toolbar.setFixedHeight(30)
        toolbar.addWidget(return_button)
        toolbar.addWidget(delete_button)

        self.title = QPlainTextEdit(self.editor) # set read-only on Annotations
        self.title.setMaximumHeight(70)
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


class ViewerItem(QWidget):
    def __init__(self, i, idx, color, text, meta):
        super().__init__()
        self.idx = idx
        self.color = color
        self.text = text
        self.meta = meta
        self.body = ''
        self.title = ''

        self.note_widget = QFrame()
        self.note_widget.setFixedHeight(250)
        self.note_widget.setFrameShape(QFrame.Panel)
        self.note_widget.setStyleSheet(f"background-color: {color}")

        text_box = QTextEdit(self.note_widget)
        text_box.setReadOnly(True)
        text_box.setContentsMargins(1, 1, 1, 2)
        text_box.setFrameShape(QFrame.NoFrame)
        text_box.setStyleSheet('color: #3d3d5c;')
        text_box.sizePolicy().setHorizontalPolicy(QSizePolicy.MinimumExpanding)
        text_box.setText(text)

        if self.meta:
            meta_box = QLabel(self.note_widget)
            meta_box.setWordWrap(True)
            meta_box.setContentsMargins(1, 2, 1, 0)
            meta_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            meta_box.setStyleSheet('color: #7575a3;')
            meta_box.setTextFormat(Qt.RichText)
            meta_box.setText(meta)

        self.delete_button = QPushButton(text=str(i), parent=self.note_widget)
        self.delete_button.setLayoutDirection(Qt.RightToLeft)
        self.delete_button.setIcon(QPixmap(resource_path('res/icons/icons8-delete-64.png')))
        self.delete_button.setIconSize(QSize(24, 24))
        self.delete_button.setStyleSheet("QPushButton { background-color: transparent; font-size: 1px; border: 0px; color: transparent; }")

        self.expand_button = QPushButton(text=str(i), parent=self.note_widget)
        self.expand_button.setLayoutDirection(Qt.RightToLeft)
        self.expand_button.setIcon(QPixmap(resource_path('res/icons/icons8-expand-30.png')))
        self.expand_button.setIconSize(QSize(22, 22))
        self.expand_button.setStyleSheet("QPushButton { background-color: transparent; font-size: 1px; border: 0px; color: transparent; }")

        layout = QGridLayout(self.note_widget)
        layout.addWidget(text_box, 0 , 0, 1, 0)
        
        if self.meta:
            layout.addWidget(meta_box, 1, 0)
            button_layout = QVBoxLayout()
            button_layout.addWidget(self.delete_button, Qt.AlignmentFlag.AlignRight)
            button_layout.addWidget(self.expand_button, Qt.AlignmentFlag.AlignRight)
            button_frame = QFrame()
            button_frame.setLayout(button_layout)
            layout.addWidget(button_frame, 1, 1, Qt.AlignmentFlag.AlignRight)
        else:
            button_layout = QHBoxLayout()
            button_layout.addWidget(self.delete_button)
            button_layout.addWidget(self.expand_button)
            button_frame = QFrame()
            button_frame.setLayout(button_layout)
            layout.addWidget(button_frame, 1, 0)
