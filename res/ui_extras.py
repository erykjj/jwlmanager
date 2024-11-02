#!/usr/bin/env python3

"""
  JWLManager module with Qt classes for UI components

  MIT License:  Copyright (c) 2024 Eryk J.

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
from glob import glob
from datetime import datetime

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QStackedLayout, QTextEdit, QTreeWidget, QToolBar, QToolButton, QVBoxLayout, QWidget

_base_path = path.dirname(__file__)


class CustomTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent.parent() if parent else None

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            item = self.itemAt(event.pos())
            if item:
                if self.parent_window:
                    self.parent_window.right_clicked(item)
        else:
            super().mousePressEvent(event) 


class AboutBox(QDialog):
    def __init__(self, parent, app, version):
        super().__init__(parent)

        year = f'MIT ©{datetime.now().year}'
        owner = 'Eryk J.'
        web = 'https://github.com/erykjj/jwlmanager'
        contact = b'\x69\x6E\x66\x69\x6E\x69\x74\x69\x40\x69\x6E\x76\x65\x6E\x74\x61\x74\x69\x2E\x6F\x72\x67'.decode('utf-8')

        self.setStyleSheet("QDialog {border:2px solid #5b3c88}")
        layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        icon = QLabel(self)
        icon.setPixmap(QPixmap(_base_path+'/icons/JWLManager.png'))
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
        button.setFixedWidth(80)
        button.accepted.connect(self.accept)

        left_layout.addWidget(button)
        layout.addLayout(left_layout)
        layout.addLayout(right_layout)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowIcon(QPixmap(_base_path+'/icons/JWLManager.png'))


class HelpBox(QDialog):
    def __init__(self, title, size, pos):
        super().__init__()

        self.setWindowFlags(Qt.Window)
        self.setWindowIcon((QIcon(_base_path+'/icons/JWLManager.png')))
        self.setWindowTitle(title)
        self.setMinimumSize(300, 300)
        self.resize(size)
        self.move(pos)
        text = QTextEdit(self)
        text.setReadOnly(True)
        with open(_base_path+'/HELP.md', encoding='utf-8') as f:
            text.setMarkdown(f.read())
        layout = QHBoxLayout(self)
        layout.addWidget(text)
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.finished.connect(self.hide())


class ThemeManager:
    def __init__(self):
        self.all_icons = self._load_icons()
        self.qss = self._load_qss()

    def _load_qss(self):
        qss = {'light': {}, 'dark': {}}
        for theme in qss.keys():
            with open(_base_path + f'/{theme}.qss', 'r') as f:
                qss[theme] = f.read()
        return qss

    def _load_icons(self):
        icons = {'light': {}, 'dark': {}, 'universal': {}}
        for f in glob('*.png', root_dir=_base_path + f'/icons'):
            name = path.splitext(f)[0]
            icons['universal'][name] = QIcon(_base_path + f'/icons/{f}')
        for theme in ['light', 'dark']:
            for f in glob('*.png', root_dir=_base_path + f'/icons/{theme}'):
                name = path.splitext(f)[0]
                icons[theme][name] = QIcon(_base_path + f'/icons/{theme}/{f}')
        return icons

    def update_icons(self, widget, theme):
        self.icons = {**self.all_icons[theme], **self.all_icons['universal']}
        if hasattr(widget, 'icon') and callable(getattr(widget, 'icon')):
            icon_name = widget.property('icon_name')
            if icon_name and icon_name in self.icons.keys():
                widget.setIcon(self.icons[icon_name])
        for action in widget.actions():
            icon_name = action.property('icon_name')
            if icon_name and icon_name in self.icons.keys():
                action.setIcon(self.icons[icon_name])
        for child in widget.findChildren(QWidget):
            self.update_icons(child, theme)

    def set_theme(self, app, theme):
        app.setStyleSheet(self.qss[theme])


class DropList(QListWidget):
    def __init__(self):
        super(DropList, self).__init__()
        self.setAcceptDrops(True)
        self.files = []

    def add_file(self, f):
        self.addItem(f)
        self.files.append(f)

    def clear_files(self):
        self.files = []
        self.clear()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        md = event.mimeData()
        if md.hasUrls():
            for url in md.urls():
                f = url.toLocalFile()
                self.files.append(f)
                self.addItem(f)
            event.acceptProposedAction()


class DataViewer(QDialog):
    escape_pressed = Signal()

    def __init__(self, size, pos):
        super().__init__()

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.Window)
        self.setWindowIcon((QIcon(_base_path+'/icons/JWLManager.png')))
        self.setMinimumSize(755, 500)
        self.resize(size)
        self.move(pos)

        self.setStyleSheet("""
            QToolTip {
                color: black;
                background-color: white;
                border: 1px solid #aaaaaa;
            }""")

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
        txt_button.setStyleSheet('color: #177c26; font: bold;') # TODO: change the color to more 'universal'
        self.txt_action = QAction('')
        self.txt_action.setToolTip('⇣')
        self.txt_action.setIcon(QPixmap(_base_path+f'/icons/download.png'))
        txt_button.setDefaultAction(self.txt_action)

        discard_button = QToolButton()
        discard_button.setStyleSheet('color: #3f54aa; font: bold;') # TODO: change the color to more 'universal'
        self.discard_action = QAction()
        self.discard_action.setDisabled(True)
        discard_button.setDefaultAction(self.discard_action)

        confirm_button = QToolButton()
        confirm_button.setStyleSheet('color: #c80b0b; font: bold;')
        self.confirm_action = QAction()
        self.confirm_action.setDisabled(True)
        confirm_button.setDefaultAction(self.confirm_action)

        spacer = QWidget()
        spacer.setFixedHeight(1)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.filter_box = QLineEdit()
        self.filter_box.sizePolicy().setHorizontalPolicy(QSizePolicy.Maximum)
        self.filter_box.setClearButtonEnabled(True)
        self.filter_box.setMaximumWidth(250)

        toolbar = QToolBar(viewer)
        toolbar.setFixedHeight(30)
        toolbar.addWidget(txt_button)
        toolbar.addWidget(discard_button)
        toolbar.addWidget(confirm_button)
        toolbar.addWidget(spacer)
        toolbar.addWidget(self.filter_box)

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
        self.return_button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.return_action = QAction()
        self.return_action.setIcon(QPixmap(_base_path+f'/icons/return.png'))
        self.return_button.setDefaultAction(self.return_action)

        self.accept_button = QToolButton()
        self.accept_button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.accept_action = QAction()
        self.accept_action.setIcon(QPixmap(_base_path+f'/icons/accept.png'))
        self.accept_button.setDefaultAction(self.accept_action)
        self.accept_action.setVisible(False)

        toolbar = QToolBar(self.editor)
        toolbar.setFixedHeight(32)
        toolbar.addWidget(self.return_button)
        toolbar.addWidget(self.accept_button)

        self.title = QPlainTextEdit(self.editor)
        self.title.setMaximumHeight(60)
        self.title.setContentsMargins(5, 0, 5, 0)
        self.title.setStyleSheet('font: bold; font-size: 20px;')

        self.body = QPlainTextEdit(self.editor)
        self.body.setStyleSheet('font: normal;')

        self.meta = QLabel(self.editor)
        self.meta.setFixedHeight(80)
        self.meta.setContentsMargins(5, 0, 5, 0)
        self.meta.setStyleSheet('color: #7575a3;')

        layout = QVBoxLayout(self.editor)
        layout.addWidget(toolbar)
        layout.addWidget(self.title)
        layout.addWidget(self.body)
        layout.addWidget(self.meta)
        self.viewer_layout.addWidget(self.editor)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.escape_pressed.emit()


class ViewerItem(QWidget):
    def __init__(self, parent, idx, color, title, body, meta, metadata):
        super().__init__(parent)
        classes = {
            0: 'grey-note',
            1: 'yellow-note',
            2: 'green-note',
            3: 'blue-note',
            4: 'red-note',
            5: 'orange-note',
            6: 'purple-note' }
        self.idx = idx
        self.label = None
        self.body = body
        self.title = title
        self.meta = meta
        self.metadata= metadata
        theme = parent.theme

        self.note_widget = QFrame()
        self.note_widget.setFixedHeight(250)
        self.note_widget.setFrameShape(QFrame.Panel)

        self.text_box = QTextEdit(self.note_widget)
        self.text_box.setReadOnly(True)
        self.text_box.setFrameStyle(QFrame.NoFrame)
        self.text_box.sizePolicy().setHorizontalPolicy(QSizePolicy.MinimumExpanding)
        self.text_box.setProperty('class', classes[color])
        self.update_note()

        separator = QFrame()
        separator.setContentsMargins(2, 0, 2, 0)
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet('color: #7575a3;')
        separator.setProperty('class', classes[color])

        if self.meta:
            self.meta_box = QLabel(self.note_widget)
            self.meta_box.setContentsMargins(5, 0, 0, 0)
            self.meta_box.setFixedHeight(78)
            self.meta_box.setWordWrap(True)
            self.meta_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.meta_box.setStyleSheet('color: #7575a3;')
            self.meta_box.setTextFormat(Qt.RichText)
            self.meta_box.setText(meta)
            self.meta_box.setProperty('class', classes[color])

        self.delete_button = QPushButton()
        self.delete_button.setIcon(theme.icons['delete'])
        self.delete_button.setIconSize(QSize(28, 28))
        self.delete_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.delete_button.setStyleSheet('border: 0px;')
        self.delete_button.setProperty('class', classes[color])

        self.edit_button = QPushButton()
        self.edit_button.setIcon(theme.icons['edit'])
        self.edit_button.setIconSize(QSize(24, 24))
        self.edit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.edit_button.setStyleSheet('border: 0px;')
        self.edit_button.setProperty('class', classes[color])

        layout = QGridLayout(self.note_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text_box, 0 , 0, 1, 0)
        layout.addWidget(separator, 1, 0, 1, 0)

        if self.meta:
            layout.addWidget(self.meta_box, 2, 0)
            button_layout = QVBoxLayout()
            button_layout.setSpacing(0)
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_layout.addWidget(self.delete_button)
            button_layout.addWidget(self.edit_button)
            button_frame = QFrame()
            button_frame.setMaximumWidth(50)
            button_frame.setLayout(button_layout)
            button_frame.setStyleSheet('border: none;')
            layout.addWidget(button_frame, 2, 1, Qt.AlignmentFlag.AlignRight)
        else:
            button_layout = QHBoxLayout()
            button_layout.setSpacing(0)
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_layout.addWidget(self.delete_button)
            button_layout.addWidget(self.edit_button)
            button_frame = QFrame()
            button_frame.setLayout(button_layout)
            button_frame.setStyleSheet('border: none;')
            layout.addWidget(button_frame, 2, 0)

    def update_note(self):
        txt = '<h3><b>' + self.title + '</b></h3>' + self.body
        self.text_box.setText(txt.replace('\n', '<br>'))
