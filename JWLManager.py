#!/usr/bin/env python3

"""
  JWLManager:   Multi-platform GUI for managing JW Library files:
                view, delete, edit, merge (via export/import), etc.

  MIT License:  Copyright (c) 2025 Eryk J.

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

APP = 'JWLManager'
VERSION = 'v9.0.0'


from res.ui_main_window import Ui_MainWindow
from res.ui_extras import AboutBox, HelpBox, DataViewer, DropList, MergeDialog, ThemeManager, ViewerItem

from PySide6.QtCore import QEvent, QPoint, QSettings, QSize, Qt, QTimer,QTranslator
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QGridLayout, QLabel, QMainWindow, QMenu, QMessageBox, QProgressDialog, QPushButton, QTextEdit, QTreeWidgetItem, QTreeWidgetItemIterator, QVBoxLayout, QWidget

from collections import defaultdict
from datetime import datetime, timezone
from functools import partial
from glob import glob
from hashlib import sha256
from pathlib import Path
from PIL import Image
from platform import platform
from random import randint
from tempfile import mkdtemp
from time import time
from traceback import format_exception
from xlsxwriter import Workbook
from zipfile import ZipFile, ZIP_DEFLATED

import argparse, gettext, json, puremagic, os, regex, requests, shutil, sqlite3, sys, uuid
import polars as pl


PROJECT_PATH = Path(__file__).resolve().parent
TMP_PATH = mkdtemp(prefix='JWLManager_')
DB_NAME = 'userData.db'


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, archive=''):
        super().__init__()

        def center():
            qr = self.frameGeometry()
            cp = QWidget.screen(self).availableGeometry().center()
            qr.moveCenter(cp)
            return qr.topLeft()

        def connect_signals():
            self.actionQuit.triggered.connect(self.close)
            self.actionHelp.triggered.connect(self.help_box)
            self.actionAbout.triggered.connect(self.about_box)
            self.actionNew.triggered.connect(self.new_file)
            self.actionOpen.triggered.connect(self.load_file)
            self.actionMerge.triggered.connect(self.merge_file)
            self.actionQuit.triggered.connect(self.clean_up)
            self.actionSave.triggered.connect(self.save_file)
            self.actionSave_As.triggered.connect(self.save_as_file)
            self.actionClean.triggered.connect(self.clean_items)
            self.actionObscure.triggered.connect(self.obscure_items)
            self.actionSort.triggered.connect(self.sort_notes)
            self.actionExpand_All.triggered.connect(self.expand_all)
            self.actionCollapse_All.triggered.connect(self.collapse_all)
            self.actionSelect_All.triggered.connect(self.select_all)
            self.actionUnselect_All.triggered.connect(self.unselect_all)
            self.actionTheme.triggered.connect(self.toggle_theme)
            self.menuTitle_View.triggered.connect(self.change_title)
            self.menuLanguage.triggered.connect(self.change_language)
            self.combo_grouping.currentTextChanged.connect(lambda: self.regroup(False))
            self.combo_category.currentTextChanged.connect(self.switchboard)
            self.treeWidget.itemChanged.connect(self.tree_selection)
            self.treeWidget.doubleClicked.connect(self.double_clicked)
            self.button_export.clicked.connect(self.export_menu)
            self.button_import.clicked.connect(self.import_items)
            self.button_add.clicked.connect(self.add_items)
            self.button_delete.clicked.connect(self.delete_items)
            self.button_view.clicked.connect(self.data_viewer)
            self.button_color.clicked.connect(self.select_color)
            self.button_tag.clicked.connect(self.tag_notes)

        def set_vars():
            self.total.setText('')
            self.int_total = 0
            self.modified = False
            self.title_format = settings.value('JWLManager/title','short')
            options = { 'code': 0, 'short': 1, 'full': 2 }
            self.titleChoices.actions()[options[self.title_format]].setChecked(True)
            self.save_filename = ''
            self.current_archive = archive
            if not os.path.exists(self.current_archive):
                self.current_archive = ''
            self.working_dir = Path.home()
            self.lang = lang
            self.latest = None
            for item in self.menuLanguage.actions():
                if item.toolTip() not in available_languages.keys():
                    item.setVisible(False)
                if item.toolTip() == self.lang:
                    item.setChecked(True)
            self.current_data = []
            self.tree_cache = {}

        self.mode = settings.value('JWLManager/theme', 'light')
        self.format = settings.value('JWLManager/format', 'xlsx')
        self.setupUi(self)
        self.actionReindex.setVisible(False)
        self.combo_category.setCurrentIndex(int(settings.value('JWLManager/category', 0)))
        self.combo_category.view().setMinimumWidth(190)
        self.combo_grouping.setCurrentText(_('Type'))
        self.viewer_pos = settings.value('Viewer/position', QPoint(50, 25))
        self.viewer_size = settings.value('Viewer/size', QSize(755, 500))
        self.help_pos = settings.value('Help/position', QPoint(50, 50))
        self.help_size = settings.value('Help/size', QSize(350, 400))
        self.setAcceptDrops(True)
        self.status_label = QLabel()
        self.statusBar.addPermanentWidget(self.status_label, 0)
        self.statusBar.setStyleSheet('font-weight: bold;')
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.sortByColumn(int(settings.value('JWLManager/sort', 1)), settings.value('JWLManager/direction', Qt.DescendingOrder))
        self.treeWidget.setColumnWidth(0, int(settings.value('JWLManager/column1', 500)))
        self.treeWidget.setColumnWidth(1, int(settings.value('JWLManager/column2', 30)))
        self.treeWidget.setExpandsOnDoubleClick(False)
        self.resize(settings.value('Main_Window/size', QSize(680, 500)))
        self.move(settings.value('Main_Window/position', center()))
        self.viewer_window = QDialog(self)
        connect_signals()
        set_vars()
        self.about_window = AboutBox(self, app=APP, version=VERSION)
        self.help_window = HelpBox(_('Help'), self.help_size, self.help_pos)
        self.merge_window = MergeDialog(self)
        self.theme = ThemeManager()
        self.theme.set_theme(app, self.mode)
        self.theme.update_icons(self, self.mode)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_lockfile)
        self.timer.start(1000)
        if not (self.current_archive and self.load_file(self.current_archive)):
            self.current_archive = ''
            self.new_file()


    def check_file(self, file):
        self.timer.stop()
        if (self.current_archive == '') and (self.modified == False):
            self.load_file(file)
        else:
            self.raise_()
            self.activateWindow()
            self.merge_window.setWindowTitle(_('Open or Merge'))
            self.merge_window.archive.setText(Path(file).name)
            self.merge_window.label.setText(_('Open archive or merge with current?'))
            self.merge_window.open_button.setText(_('Open'))
            self.merge_window.merge_button.setText(_('Merge'))
            self.merge_window.exec()
            if self.merge_window.choice == 'open':
                self.load_file(file)
            else:
                self.merge_items(file)
        self.timer.start(1000)

    def check_lockfile(self):
        if os.path.exists(LOCK_FILE) and os.path.getsize(LOCK_FILE) > 0:
            with open(LOCK_FILE, 'r+') as lockfile:
                file = lockfile.read().strip()
                lockfile.seek(0)
                lockfile.truncate()
            if Path(file).suffix == '.jwlibrary':
                self.check_file(file)

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)

    def closeEvent(self, event):
        if self.modified:
            reply = QMessageBox.question(self, _('Exit'), _('Save before quitting?'), QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                if self.save_file() == False:
                     event.ignore()
                     return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        event.accept()
        self.clean_up()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        file = event.mimeData().urls()[0].toLocalFile()
        suffix = Path(file).suffix
        if suffix == '.jwlibrary':
            self.check_file(file)
        elif not self.combo_category.isEnabled():
            QMessageBox.warning(self, _('Error'), _('No archive has been opened!'), QMessageBox.Cancel)
        elif suffix == '.jwlplaylist':
            self.import_items(file, _('Playlists'))
        elif suffix == '.txt':
            with open(file, 'r', encoding='utf-8', errors='namereplace') as f:
                header = f.readline().strip()
            if header == r'{ANNOTATIONS}':
                self.import_items(file, _('Annotations'))
            elif header == r'{BOOKMARKS}':
                self.import_items(file, _('Bookmarks'))
            elif header == r'{FAVORITES}':
                self.import_items(file, _('Favorites'))
            elif header == r'{HIGHLIGHTS}':
                self.import_items(file, _('Highlights'))
            elif regex.search('{NOTES=', header):
                self.import_items(file, _('Notes'))
            else:
                QMessageBox.warning(self, _('Error'), _('File "{}" not recognized!').format(file), QMessageBox.Cancel)
        elif suffix == '.xlsx':
            annotations_columns = {'PUB', 'ISSUE', 'DOC', 'LABEL', 'VALUE'}
            notes_columns = {'CREATED', 'MODIFIED', 'TAGS', 'COLOR', 'RANGE', 'LANG', 'PUB', 'BK', 'CH', 'VS', 'ISSUE', 'DOC', 'BLOCK', 'HEADING', 'TITLE', 'NOTE'}
            df = pl.read_excel(engine='xlsx2csv', source=file)
            columns = set(df.columns)
            if  annotations_columns.issubset(columns):
                self.import_items(file, _('Annotations'))
            elif notes_columns.issubset(columns):
                self.import_items(file, _('Notes'))
            else:
                QMessageBox.warning(self, _('Error'), _('File "{}" not recognized!').format(file), QMessageBox.Cancel)
        else:
            QMessageBox.warning(self, _('Error'), _('File "{}" not recognized!').format(file), QMessageBox.Cancel)


    def help_box(self):
        help_file = 'HELP.md'
        if self.lang == 'de':
            help_file = 'HILFE.md'
        with open(f'{PROJECT_PATH}/res/{help_file}', encoding='utf-8') as f:
            self.help_window.help_text.setMarkdown(f.read())
        self.help_window.show()
        self.help_window.raise_()
        self.help_window.activateWindow()
        self.help_pos = self.help_window.pos()
        self.help_size = self.help_window.size()

    def about_box(self):

        def version_compare(version, release):
            for r, v in zip(release.strip('v').split('.'), version.strip('v').split('.')):
                if int(r) > int(v):
                    return True
                elif int(r) < int(v):
                    return None
            return False

        if not self.latest:
            url = 'https://api.github.com/repos/erykjj/jwlmanager/releases/latest'
            headers = { 'X-GitHub-Api-Version': '2022-11-28' }
            try:
                r = requests.get(url, headers=headers, timeout=5)
                self.latest = json.loads(r.content.decode('utf-8'))['name']
                comp = version_compare(VERSION, self.latest)
                if comp is None:
                    text = f'<div style="text-align:center;"><small>'+'Pre-release'+'</small></div>'
                elif comp:
                    text = f'<div style="text-align:center;"><a style="color:red; text-decoration:none;" href="https://github.com/erykjj/jwlmanager/releases/latest"><small><b>{self.latest.lstrip("v")} '+_('update available!')+'</b></small></a></div>'
                else:
                    text = f'<div style="text-align:center;"><small>'+_('Latest version')+'</small></div>'
            except:
                text = f'<div style="text-align:center;"><small><i>'+_('Error while checking for updates!')+'</u></small></div>'
            self.about_window.update_label.setText(text)
        self.about_window.exec()

    def crash_box(self, ex):
        tb_lines = format_exception(ex.__class__, ex, ex.__traceback__)
        tb_text = ''.join(tb_lines)
        dialog = QDialog(self)
        dialog.setMinimumSize(650, 375)
        dialog.setWindowTitle(_('Error!'))
        label1 = QLabel()
        label1.setText("<p style='text-align: left;'>"+_('Oops! Something went wrong…')+"</p></p><p style='text-align: left;'>"+_('Take note of what you were doing and')+" <a style='color: #666699;' href='https://github.com/erykjj/jwlmanager/issues'>"+_('inform the developer')+"</a>:</p>")
        label1.setOpenExternalLinks(True)
        text = QTextEdit()
        text.setReadOnly(True)
        archive = Path(self.current_archive).name if self.current_archive else _('NEW ARCHIVE')
        manifest = "\n".join([
            f"\n{archive}:",
            f"  name: {self.manifest['name']}",
            f"  creationDate: {self.manifest['creationDate']}",
            f"  lastModifiedDate: {self.manifest['userDataBackup']['lastModifiedDate']}",
            f"  deviceName: {self.manifest['userDataBackup']['deviceName']}",
            f"  schemaVersion: {self.manifest['userDataBackup']['schemaVersion']}"
        ])
        text.setText(f'{APP} {VERSION}\n{platform()}\n{manifest}\n\n{tb_text}')
        label2 = QLabel()
        label2.setText(_('The app will terminate.'))
        button = QDialogButtonBox(QDialogButtonBox.Abort)
        layout = QVBoxLayout(dialog)
        layout.addWidget(label1)
        layout.addWidget(text)
        layout.addWidget(label2)
        layout.addWidget(button)
        button.clicked.connect(dialog.close)
        dialog.exec()


    def toggle_theme(self):
        if self.mode == 'light':
            self.mode = 'dark'
        else:
            self.mode = 'light'
        self.theme.set_theme(app, self.mode)
        self.theme.update_icons(self, self.mode)

    def change_language(self):
        changed = False
        self.combo_grouping.blockSignals(True)
        self.combo_category.blockSignals(True)
        for item in self.langChoices.actions():
            if item.isChecked() and (self.lang != item.toolTip()):
                app.removeTranslator(translator[self.lang])
                self.lang = item.toolTip()
                changed = True
                break
        if changed:
            read_resources(self.lang)
            if self.lang not in translator.keys():
                translator[self.lang] = QTranslator()
                translator[self.lang].load(f'{PROJECT_PATH}/res/locales/UI/qt_{self.lang}.qm')
            app.installTranslator(translator[self.lang])
            app.processEvents()
            self.regroup(True)
        self.combo_grouping.blockSignals(False)
        self.combo_category.blockSignals(False)

    def change_title(self):
        changed = False
        options = ['code', 'short', 'full']
        counter = 0
        for item in self.titleChoices.actions():
            if item.isChecked() and (self.title_format != options[counter]):
                self.title_format = options[counter]
                changed = True
            counter += 1
        if changed:
            self.regroup(True)


    def expand_all(self):
        self.treeWidget.expandAll()

    def collapse_all(self):
        self.treeWidget.collapseAll()


    def right_clicked(self, item):
        if item.checkState(0) == Qt.Checked:
            item.setCheckState(0, Qt.Unchecked)
        else:
            item.setCheckState(0, Qt.Checked)

    def double_clicked(self, item):
        if self.treeWidget.isExpanded(item):
            self.treeWidget.setExpanded(item, False)
        else:
            self.treeWidget.expandRecursively(item, -1)


    def select_all(self):
        for item in QTreeWidgetItemIterator(self.treeWidget):
            item.value().setCheckState(0, Qt.Checked)

    def unselect_all(self):
        for item in QTreeWidgetItemIterator(self.treeWidget):
            item.value().setCheckState(0, Qt.Unchecked)

    def list_selected(self):
        selected = []
        it = QTreeWidgetItemIterator(self.treeWidget, QTreeWidgetItemIterator.Checked)
        for item in it:
            index = item.value()
            ids = self.leaves.get(index)
            if ids:
                selected.extend(ids)
        return selected

    def tree_selection(self):
        self.selected_items = len(self.list_selected())
        self.selected.setText(f'**{self.selected_items:,}**')
        self.button_delete.setEnabled(self.selected_items)
        self.button_view.setEnabled(self.selected_items and self.combo_category.currentText() in (_('Notes'), _('Annotations')))
        self.button_color.setEnabled(self.selected_items and self.combo_category.currentText() in (_('Notes'), _('Highlights')))
        self.button_tag.setEnabled(self.selected_items and self.combo_category.currentText() == _('Notes'))
        self.button_export.setEnabled(self.selected_items)


    def switchboard(self, selection, new_data=False):

        def disable_options(lst=[], add=False, exp=False, imp=False, view=False, col=False, tag=False):
            self.button_add.setVisible(add)
            self.button_view.setVisible(view)
            self.button_export.setVisible(exp)
            self.button_import.setEnabled(imp)
            self.button_import.setVisible(imp)
            self.button_color.setVisible(col)
            # self.button_tag.setVisible(tag)
            self.button_tag.setVisible(False)
            app.processEvents()
            for item in range(6):
                self.combo_grouping.model().item(item).setEnabled(True)
            for item in lst:
                self.combo_grouping.model().item(item).setEnabled(False)
                if self.combo_grouping.currentText() == self.combo_grouping.itemText(item):
                    self.combo_grouping.setCurrentText(_('Type'))

        self.combo_grouping.blockSignals(True)
        if self.combo_category.currentIndex() not in self.tree_cache:
            new = True
        else:
            new = False
        if selection == _('Notes'):
            if new:
                self.combo_grouping.setCurrentText(_('Type'))
            disable_options([], False, True, True, True, True, True)
        elif selection == _('Highlights'):
            if new:
                self.combo_grouping.setCurrentText(_('Type'))
            disable_options([4], False, True, True, False, True, False)
        elif selection == _('Bookmarks'):
            disable_options([4,5], False, True, True, False, False, False)
        elif selection == _('Annotations'):
            disable_options([2,4,5], False, True, True, True, False, False)
        elif selection == _('Favorites'):
            disable_options([4,5], True, True, True, False, False, False)
        elif selection == _('Playlists'):
            self.combo_grouping.setCurrentText(_('Title'))
            disable_options([1,2,3,4,5], True, True, True, False, False, False)
        self.regroup(new_data)
        self.combo_grouping.blockSignals(False)

    def regroup(self, new_data=False, message=None):

        def get_data():
            if cat in self.tree_cache and grp in self.tree_cache[cat]:
                cached_data = self.tree_cache[cat][grp]['data']
                self.current_data = cached_data
                return self.current_data

            if category == _('Bookmarks'):
                get_bookmarks()
            elif category == _('Favorites'):
                get_favorites()
            elif category == _('Highlights'):
                get_highlights()
            elif category == _('Notes'):
                get_notes()
            elif category == _('Annotations'):
                get_annotations()
            elif category == _('Playlists'):
                get_playlists()

            if cat not in self.tree_cache:
                self.tree_cache[cat] = {}
            self.tree_cache[cat][grp] = {'data': self.current_data}

            return self.current_data

        def process_code(code, issue):
            if code == 'ws' and issue == 0: # Worldwide Security book - same code as simplified Watchtower
                code = 'ws-'
            elif not code:
                code = ''
            elif regex.match(code_jwb, code):
                code = 'jwb-'
            yr = ''
            dated = regex.search(code_yr, code) # Year included in code
            if dated:
                prefix = dated.group(1)
                suffix = dated.group(2)
                if prefix not in {'bi', 'br', 'brg', 'kn', 'ks', 'pt', 'tp'}:
                    code = prefix
                    if int(suffix) >= 50:
                        yr = '19' + suffix
                    else:
                        yr = '20' + suffix
            return code, yr

        def process_color(col):
            return (_('Grey'), _('Yellow'), _('Green'), _('Blue'), _('Red'), _('Orange'), _('Purple'))[int(col)]

        def process_detail(symbol, book, chapter, issue, year):
            if symbol in {'Rbi8', 'bi10', 'bi12', 'bi22', 'bi7', 'by', 'int', 'nwt', 'nwtsty', 'rh', 'sbi1', 'sbi2'}: # Bible appendix notes, etc.
                detail1 = _('* OTHER *')
            else:
                detail1 = None
            if issue > 19000000:
                y = str(issue)[0:4]
                m = str(issue)[4:6]
                d = str(issue)[6:]
                if d == '00':
                    detail1 = f'{y}-{m}'
                else:
                    detail1 = f'{y}-{m}-{d}'
                if not year:
                    year = y
            if book and chapter:
                bk = str(book).rjust(2, '0') + f': {bible_books[book]}'
                detail1 = bk
                detail2 = _('Chap.') + str(chapter).rjust(4, ' ')
            else:
                detail2 = None
            if not detail1 and year:
                detail1 = year
            if not year:
                year = None
            return detail1, year, detail2

        def merge_df(df):
            pl.Config.set_tbl_cols(-1)
            df = df.join(publications, on='Symbol', how='left')
            df = df.with_columns([
                pl.col('Full').fill_null(pl.col('Symbol')),
                pl.col('Short').fill_null(pl.col('Symbol')),
                pl.col('Type').fill_null(_('Other')),
                pl.col('Year').fill_null(pl.col('Year_right')).fill_null(_('* NO YEAR *'))
            ])
            df = df.drop(['Year_right'])
            return df

        def get_annotations():
            lst = []
            for row in con.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, TextTag, l.BookNumber, l.ChapterNumber, l.Title FROM InputField JOIN Location l USING (LocationId);').fetchall():
                lng = lang_name.get(row[2], _('* NO LANGUAGE *'))
                code, year = process_code(row[1], row[3])
                detail1, year, detail2 = process_detail(row[1], row[5], row[6], row[3], year)
                item = row[0]
                rec = [item, lng, code, year, detail1, detail2]
                lst.append(rec)
            schema = {'Id': pl.Int64, 'Language': pl.Utf8, 'Symbol': pl.Utf8, 'Year': pl.Utf8, 'Detail1': pl.Utf8, 'Detail2': pl.Utf8}
            annotations = pl.DataFrame(lst, schema=schema, orient='row' )
            self.current_data = merge_df(annotations)

        def get_bookmarks():
            lst = []
            for row in con.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, BookmarkId, l.BookNumber, l.ChapterNumber, l.Title FROM Bookmark b JOIN Location l USING (LocationId);').fetchall():
                lng = lang_name.get(row[2], f'#{row[2]}')
                code, year = process_code(row[1], row[3])
                detail1, year, detail2 = process_detail(row[1], row[5], row[6], row[3], year)
                item = row[4]
                rec = [item, lng, code or _('* OTHER *'), year, detail1, detail2]
                lst.append(rec)
            schema = {'Id': pl.Int64, 'Language': pl.Utf8, 'Symbol': pl.Utf8, 'Year': pl.Utf8, 'Detail1': pl.Utf8, 'Detail2': pl.Utf8}
            bookmarks = pl.DataFrame(lst, schema=schema, orient='row' )
            self.current_data = merge_df(bookmarks)

        def get_favorites():
            lst = []
            for row in con.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, TagMapId FROM TagMap tm JOIN Location l USING (LocationId) WHERE tm.NoteId IS NULL ORDER BY tm.Position;').fetchall():
                lng = lang_name.get(row[2], f'#{row[2]}')
                code, year = process_code(row[1], row[3])
                detail1, year, detail2 = process_detail(row[1], None, None, row[3], year)
                item = row[4]
                rec = [item, lng, code or _('* OTHER *'), year, detail1, detail2]
                lst.append(rec)
            schema = {'Id': pl.Int64, 'Language': pl.Utf8, 'Symbol': pl.Utf8, 'Year': pl.Utf8, 'Detail1': pl.Utf8, 'Detail2': pl.Utf8}
            favorites = pl.DataFrame(lst, schema=schema, orient='row' )
            self.current_data = merge_df(favorites)

        def get_highlights():
            lst = []
            for row in con.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, b.BlockRangeId, u.UserMarkId, u.ColorIndex, l.BookNumber, l.ChapterNumber FROM UserMark u JOIN Location l USING (LocationId), BlockRange b USING (UserMarkId);').fetchall():
                lng = lang_name.get(row[2], f'#{row[2]}')
                code, year = process_code(row[1], row[3])
                detail1, year, detail2 = process_detail(row[1], row[7], row[8], row[3], year)
                col = process_color(row[6] or 0)
                item = row[4]
                rec = [item, lng, code, col, year, detail1, detail2]
                lst.append(rec)
            schema = {'Id': pl.Int64, 'Language': pl.Utf8, 'Symbol': pl.Utf8, 'Color': pl.Utf8, 'Year': pl.Utf8, 'Detail1': pl.Utf8, 'Detail2': pl.Utf8}
            highlights = pl.DataFrame(lst, schema=schema, orient='row' )
            self.current_data = merge_df(highlights)

        def get_notes():

            def load_independent():
                lst = []
                for row in con.execute("SELECT NoteId Id, ColorIndex Color, GROUP_CONCAT(Name, ' | ') Tags, substr(LastModified, 0, 11) Modified FROM (SELECT * FROM Note n LEFT JOIN TagMap tm USING (NoteId) LEFT JOIN Tag t USING (TagId) LEFT JOIN UserMark u USING (UserMarkId) ORDER BY t.Name) n WHERE n.BlockType = 0 AND LocationId IS NULL GROUP BY n.NoteId;").fetchall():
                    col = row[1] or 0
                    yr = row[3][0:4]
                    note = [row[0], _('* NO LANGUAGE *'), _('* OTHER *'), process_color(col), row[2] or _('* NO TAG *'), row[3] or '', yr, None, None, _('* OTHER *'), _('* OTHER *'), _('* INDEPENDENT *')]
                    lst.append(note)
                schema = {'Id': pl.Int64, 'Language': pl.Utf8, 'Symbol': pl.Utf8, 'Color': pl.Utf8, 'Tags': pl.Utf8, 'Modified': pl.Utf8, 'Year': pl.Utf8, 'Detail1': pl.Utf8, 'Detail2': pl.Utf8, 'Short': pl.Utf8, 'Full': pl.Utf8, 'Type': pl.Utf8}
                return pl.DataFrame(lst, schema=schema, orient='row' )

            lst = []
            for row in con.execute("SELECT NoteId Id, MepsLanguage Language, KeySymbol Symbol, IssueTagNumber Issue, BookNumber Book, ChapterNumber Chapter, ColorIndex Color, GROUP_CONCAT(Name, ' | ') Tags, substr(LastModified, 0, 11) Modified FROM (SELECT * FROM Note n JOIN Location l USING (LocationId) LEFT JOIN TagMap tm USING (NoteId) LEFT JOIN Tag t USING (TagId) LEFT JOIN UserMark u USING (UserMarkId) ORDER BY t.Name) n GROUP BY n.NoteId;").fetchall():
                lng = lang_name.get(row[1], f'#{row[1]}')

                code, year = process_code(row[2], row[3])
                detail1, year, detail2 = process_detail(row[2], row[4], row[5], row[3], year)
                col = process_color(row[6] or 0)
                note = [row[0], lng, code or _('* OTHER *'), col, row[7] or _('* NO TAG *'), row[8] or '', year, detail1, detail2]
                lst.append(note)
            schema = {'Id': pl.Int64, 'Language': pl.Utf8, 'Symbol': pl.Utf8, 'Color': pl.Utf8, 'Tags': pl.Utf8, 'Modified': pl.Utf8, 'Year': pl.Utf8, 'Detail1': pl.Utf8, 'Detail2': pl.Utf8}
            notes = pl.DataFrame(lst, schema=schema, orient='row')
            notes = merge_df(notes)
            i_notes = load_independent()
            self.current_data = pl.concat([i_notes, notes])

        def get_playlists():
            lst = []
            for row in con.execute('SELECT PlaylistItemId, Name, Position, Label FROM PlaylistItem JOIN TagMap USING ( PlaylistItemId ) JOIN Tag t USING ( TagId ) WHERE t.Type = 2 ORDER BY Name, Position;').fetchall():
                rec = [row[0], None, _('* OTHER *'), row[1], '', row[3]]
                lst.append(rec)
            schema = {'Id': pl.Int64, 'Language': pl.Utf8, 'Symbol': pl.Utf8, 'Tags': pl.Utf8, 'Year': pl.Utf8, 'Detail1': pl.Utf8}
            playlists = pl.DataFrame(lst, schema=schema, orient='row' )
            self.current_data = merge_df(playlists)

        def enable_options(enabled):
            self.menuLanguage.setEnabled(enabled)
            self.menuTitle_View.setEnabled(enabled)
            enabled = enabled and self.int_total
            self.button_import.setEnabled(enabled)
            self.combo_grouping.setEnabled(enabled)
            self.combo_category.setEnabled(enabled)
            self.actionMerge.setEnabled(enabled)
            self.actionObscure.setEnabled(enabled)
            self.actionSort.setEnabled(enabled)
            self.actionClean.setEnabled(enabled)
            self.actionExpand_All.setEnabled(enabled)
            self.actionCollapse_All.setEnabled(enabled)
            self.actionSelect_All.setEnabled(enabled)
            self.actionUnselect_All.setEnabled(enabled)

        def build_tree():

            def traverse(df, group_columns, parent_item):
                grouped = df.group_by(group_columns).agg(pl.col('Id')).to_dict(as_series=False)
                group_values = [grouped[col] for col in group_columns]
                id_lists = grouped['Id']
                tree = {'count': 0, 'data': defaultdict(list), 'items': {}}
                self.leaves = {}
                for i in range(len(group_values[0])):
                    values = [group_values[j][i] for j in range(len(group_columns))]
                    id_list = id_lists[i]
                    node = tree
                    current_parent = parent_item
                    for depth, value in enumerate(values):
                        if value is None:
                            node['data']['Id'].extend(id_list)
                            if 'item' in node:
                                self.leaves[node['item']] = node['data']['Id']
                            break
                        if value not in node['items']:
                            child_item = QTreeWidgetItem(current_parent)
                            child_item.setFlags(child_item.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
                            child_item.setCheckState(0, Qt.CheckState.Unchecked)
                            child_item.setText(0, str(value))
                            child_item.setData(1, Qt.ItemDataRole.DisplayRole, 0)
                            child_item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
                            if current_parent == self.treeWidget:
                                app.processEvents()
                            node['items'][value] = {'count': 0, 'data': defaultdict(list), 'items': {}, 'item': child_item}
                        node = node['items'][value]
                        current_parent = node['item']
                        node['count'] += len(id_list)
                        if depth == len(values) - 1:
                            node['data']['Id'].extend(id_list)
                            self.leaves[node['item']] = node['data']['Id']
                        node['item'].setData(1, Qt.ItemDataRole.DisplayRole, node['count'])
                return tree

            def rebuild_cached(tree, parent_item):

                def recurse(node, parent):
                    for value, child_node in node['items'].items():
                        child_item = QTreeWidgetItem(parent)
                        child_item.setFlags(child_item.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
                        child_item.setCheckState(0, Qt.CheckState.Unchecked)
                        child_item.setText(0, str(value))
                        child_item.setData(1, Qt.ItemDataRole.DisplayRole, child_node['count'])
                        child_item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
                        recurse(child_node, child_item)
                        if not child_node['items']:
                            self.leaves[child_item] = child_node['data']['Id']
                recurse(tree, parent_item)

            def define_views(category):
                if category == _('Bookmarks'):
                    views = {
                        _('Type'): ['Type', 'Title', 'Language', 'Detail1'],
                        _('Title'): ['Title', 'Language', 'Detail1', 'Detail2'],
                        _('Language'): ['Language', 'Title', 'Detail1', 'Detail2'],
                        _('Year'): ['Year', 'Title', 'Language', 'Detail1']
                    }
                elif category == _('Favorites'):
                    views = {
                        _('Type'): ['Type', 'Title', 'Language'],
                        _('Title'): ['Title', 'Language'],
                        _('Language'): ['Language', 'Title'],
                        _('Year'): ['Year', 'Title', 'Language']
                    }
                elif category == _('Playlists'):
                    views = {_('Title'): ['Tags', 'Detail1']}
                elif category == _('Highlights'):
                    views = {
                        _('Type'): ['Type', 'Title', 'Language', 'Detail1'],
                        _('Title'): ['Title', 'Language', 'Detail1', 'Detail2'],
                        _('Language'): ['Language', 'Title', 'Detail1', 'Detail2'],
                        _('Year'): ['Year', 'Title', 'Language', 'Detail1'],
                        _('Color'): ['Color', 'Title', 'Language', 'Detail1']
                    }
                elif category == _('Notes'):
                    views = {
                        _('Type'): ['Type', 'Title', 'Language', 'Detail1'],
                        _('Title'): ['Title', 'Language', 'Detail1', 'Detail2'],
                        _('Language'): ['Language', 'Title', 'Detail1', 'Detail2'],
                        _('Year'): ['Year', 'Title', 'Language', 'Detail1'],
                        _('Tag'): ['Tags', 'Title', 'Language', 'Detail1'],
                        _('Color'): ['Color', 'Title', 'Language', 'Detail1']
                    }
                elif category == _('Annotations'):
                    views = {
                        _('Type'): ['Type', 'Title', 'Detail1', 'Detail2'],
                        _('Title'): ['Title', 'Detail1', 'Detail2'],
                        _('Year'): ['Year', 'Title', 'Detail1', 'Detail2']
                    }
                return views

            self.current_data = self.tree_cache[cat][grp]['data']
            if self.title_format == 'code':
                title = 'Symbol'
            elif self.title_format == 'short':
                title = 'Short'
            else:
                title = 'Full'
            self.current_data = self.current_data.with_columns(pl.col(title).alias('Title'))
            self.tree_cache[cat][grp]['data'] = self.current_data

            self.int_total = self.current_data.shape[0]
            self.total.setText(f'**{self.int_total:,}**')
            views = define_views(category)

            if 'tree' in self.tree_cache[cat][grp]:
                tree = self.tree_cache[cat][grp]['tree']
                rebuild_cached(tree, self.treeWidget)
            else:
                tree = traverse(self.current_data, views[grouping], self.treeWidget)
                self.tree_cache[cat][grp]['tree'] = tree

        if new_data:
            self.tree_cache = {}
        if message:
            msg = message + '… '
        else:
            msg = ' '
        start = time()
        self.statusBar.showMessage(msg+_('Processing…'))
        enable_options(False)
        app.processEvents()
        category = self.combo_category.currentText()
        grouping = self.combo_grouping.currentText()
        cat = self.combo_category.currentIndex()
        grp = self.combo_grouping.currentIndex()
        code_yr = regex.compile(r'(.*?[^\d-])(\d{2}$)')
        code_jwb = regex.compile(r'jwb-\d+$')
        try:
            con = sqlite3.connect(f'{TMP_PATH}/{DB_NAME}')
            con.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF';")
            get_data()
            self.leaves = {}
            self.treeWidget.clear()
            self.treeWidget.repaint()
            build_tree()
            con.commit()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        delta = 4000 - (time()-start) * 1000
        if message and delta > 0:
            self.statusBar.showMessage(msg, delta)
        else:
            self.statusBar.showMessage('')
        enable_options(True)
        self.selected.setText('**0**')
        if self.combo_grouping.currentText() == _('Type'):
            self.treeWidget.expandToDepth(0)
        app.processEvents()


    def check_save(self):
        reply = QMessageBox.question(self, _('Save'), _('Save current archive?'), 
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
            QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.save_file()

    def new_file(self):
        if self.modified:
            self.check_save()
        self.status_label.setText('* '+_('NEW ARCHIVE')+' *  ')
        self.modified = False
        self.save_filename = ''
        self.current_archive = ''
        try:
            for f in glob(f'{TMP_PATH}/*', recursive=True):
                os.remove(f)
        except:
            pass
        with ZipFile(PROJECT_PATH / 'res/blank','r') as zipped:
            zipped.extractall(TMP_PATH)
        self.manifest = {
            'name': APP,
            'creationDate': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'version': 1,
            'type': 0,
            'userDataBackup': {
                'lastModifiedDate': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'deviceName': f'{APP}_{VERSION}',
                'databaseName': 'userData.db',
                'hash': '',
                'schemaVersion': 14 } }
        with open(f'{TMP_PATH}/manifest.json', 'w') as json_file:
                json.dump(self.manifest, json_file, indent=None, separators=(',', ':'))
        self.file_loaded()
        self.actionMerge.setEnabled(False)


    def merge_file(self):
        fname = QFileDialog.getOpenFileName(self, _('Open archive'), str(self.working_dir),_('JW Library archives')+' (*.jwlibrary)')
        if not fname[0]:
            return False
        self.merge_items(fname[0])

    def load_file(self, archive=''):
        if self.modified:
            self.check_save()
        if not archive:
            fname = QFileDialog.getOpenFileName(self, _('Open archive'), str(self.working_dir),_('JW Library archives')+' (*.jwlibrary)')
            if not fname[0]:
                return False
            archive = fname[0]
        self.current_archive = Path(archive)
        self.working_dir = Path(archive).parent
        self.status_label.setText(f'{Path(archive).stem}  ')
        self.actionSave.setEnabled(False)
        self.status_label.setStyleSheet('font: normal;')
        try:
            for f in glob(f'{TMP_PATH}/*', recursive=True):
                os.remove(f)
        except:
            pass
        try:
            with ZipFile(archive,'r') as zipped:
                zipped.extractall(TMP_PATH)
            with open(f'{TMP_PATH}/manifest.json', 'r') as json_file:
                self.manifest = json.load(json_file)
            self.file_loaded()
            return True
        except:
            return None

    def file_loaded(self):
        self.total.setText('**0**')
        self.selected.setText('**0**')
        self.unselect_all()
        self.modified = False
        try:
            self.viewer_window.close()
        except:
            pass
        self.switchboard(self.combo_category.currentText(), True)


    def save_file(self):
        if not self.save_filename:
            return self.save_as_file()
        else:
            self.zip_file()

    def save_as_file(self):
        fname = ()
        if not self.save_filename:
            now = datetime.now().strftime('%Y-%m-%d')
            fname = QFileDialog.getSaveFileName(self, _('Save archive'), f'{self.working_dir}/MODIFIED_{now}.jwlibrary', _('JW Library archives')+'(*.jwlibrary)')[0]
        else:
            fname = QFileDialog.getSaveFileName(self, _('Save archive'), self.save_filename, _('JW Library archives')+'(*.jwlibrary)')[0]
        if not fname:
            self.statusBar.showMessage(' '+_('NOT saved!'), 4000)
            return False
        elif Path(fname) == self.current_archive:
            reply = QMessageBox.critical(self, _('Save'), _("It's recommended to save under another name.\nAre you absolutely sure you want to replace the original?"),
              QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return self.save_file()
        if Path(fname).suffix != '.jwlibrary':
            fname += '.jwlibrary'
        self.save_filename = fname
        self.working_dir = Path(fname).parent
        self.current_archive = self.save_filename
        self.status_label.setText(f'{Path(fname).stem}  ')
        self.zip_file()

    def zip_file(self):

        def update_manifest():
            t = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            with open(f'{TMP_PATH}/manifest.json', 'r') as json_file:
                m = json.load(json_file)
            m['name'] = APP
            m['creationDate'] = t
            m['userDataBackup']['deviceName'] = f'{APP}_{VERSION}'
            m['userDataBackup']['lastModifiedDate'] = t
            m['userDataBackup']['databaseName'] = DB_NAME
            con = sqlite3.connect(f'{TMP_PATH}/{DB_NAME}')
            con.execute('UPDATE LastModified SET LastModified = ?;', (m['userDataBackup']['lastModifiedDate'],))
            con.commit()
            con.close()
            m['userDataBackup']['hash'] = sha256hash(f'{TMP_PATH}/{DB_NAME}')
            with open(f'{TMP_PATH}/manifest.json', 'w') as json_file:
                json.dump(m, json_file, indent=None, separators=(',', ':'))

        update_manifest()
        self.trim_db()
        try:
            with ZipFile(self.save_filename, 'w', compression=ZIP_DEFLATED) as newzip:
                files = os.listdir(TMP_PATH)
                for f in files:
                    newzip.write(f'{TMP_PATH}/{f}', f)
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        self.archive_saved()


    def archive_modified(self):
        self.modified = True
        self.actionSave.setEnabled(True)
        self.actionSave.setProperty('icon_name', 'save')
        self.status_label.setStyleSheet('font: italic;')
        self.button_delete.setEnabled(self.int_total)
        self.button_view.setEnabled(self.int_total)
        self.button_export.setEnabled(self.int_total)
        self.actionClean.setEnabled(self.actionClean.isEnabled() and self.int_total)
        self.actionObscure.setEnabled(self.actionObscure.isEnabled() and self.int_total)
        self.actionSort.setEnabled(self.actionSort.isEnabled() and self.int_total)
        self.actionExpand_All.setEnabled(self.actionExpand_All.isEnabled() and self.int_total)
        self.actionCollapse_All.setEnabled(self.actionCollapse_All.isEnabled() and self.int_total)
        self.actionSelect_All.setEnabled(self.actionSelect_All.isEnabled() and self.int_total)
        self.actionUnselect_All.setEnabled(self.actionUnselect_All.isEnabled() and self.int_total)

    def archive_saved(self):
        self.modified = False
        self.actionSave.setEnabled(False)
        self.save_filename = self.current_archive
        self.status_label.setStyleSheet('font: normal;')
        self.statusBar.showMessage(' '+_('Saved'), 4000)


    def export_menu(self):
        if self.combo_category.currentText() == _('Notes') or self.combo_category.currentText() == _('Annotations'):
            submenu = QMenu(self)
            italic_font = QFont()
            italic_font.setItalic(True)
            action1 = QAction(_('MS Excel file'), self)
            action1.setFont(italic_font)
            action2 = QAction(_('Custom text file'), self)
            action2.setFont(italic_font)
            action3 = QAction(_('Markdown files'), self)
            action3.setFont(italic_font)
            action1.triggered.connect(lambda: self.export_items('xlsx'))
            action2.triggered.connect(lambda: self.export_items('txt'))
            action3.triggered.connect(lambda: self.export_items('md'))
            submenu.addAction(action1)
            submenu.addAction(action2)
            submenu.addAction(action3)
            submenu.exec(self.button_export.mapToGlobal(self.button_export.rect().bottomLeft()))
        else:
            self.export_items('')

    def export_items(self, form, con=None):

        def process_issue(i):
            issue = str(i)
            yr = issue[0:4]
            m = issue[4:6]
            d = issue[6:]
            if d == '00':
                d = ''
            else:
                d = '-' + d
            return f'{yr}-{m}{d}'

        def export_file(category, form):
            now = datetime.now().strftime('%Y-%m-%d')
            if category == _('Highlights') or category == _('Bookmarks') or category == _('Favorites'):
                return QFileDialog.getSaveFileName(self, _('Export file'), f'{self.working_dir}/JWL_{category}_{now}.txt', _('Text files')+' (*.txt)')[0]
            elif category == _('Playlists'):
                fname = QFileDialog.getSaveFileName(self, _('Export file'), f'{self.working_dir}/JWL_{category}_{now}.jwlplaylist', _('JW Library playlists')+' (*.jwlplaylist)')[0]
                if Path(fname).suffix != '.jwlplaylist':
                    fname += '.jwlplaylist'
                return fname
            else:
                if form == 'xlsx':
                    fname = QFileDialog.getSaveFileName(self, _('Export file'), f'{self.working_dir}/JWL_{category}_{now}.xlsx', _('MS Excel files')+' (*.xlsx)')[0]
                    if Path(fname).suffix != '.xlsx':
                        fname += '.xlsx'
                    self.format = 'xlsx'
                    return fname
                elif form == 'txt':
                    fname = QFileDialog.getSaveFileName(self, _('Export file'), f'{self.working_dir}/JWL_{category}_{now}.txt', _('Text files')+' (*.txt)')[0]
                    if Path(fname).suffix != '.txt':
                        fname += '.txt'
                    self.format = 'txt'
                    return fname
                else:
                    return QFileDialog.getExistingDirectory(self, _('Export directory'), f'{self.working_dir}/', QFileDialog.ShowDirsOnly)

        def create_xlsx(fields, item_list, category=None):
            last_field = fields[-1]
            wb = Workbook(fname)
            wb.set_properties({'title': category, 'comments': _('Exported from')+f' {current_archive} '+_('by')+f' {APP} ({VERSION})\n'+_('on')+f" {datetime.now().strftime('%Y-%m-%d @ %H:%M:%S')}"})
            bold = wb.add_format({'bold': True})
            ws = wb.add_worksheet(APP)
            ws.write_row(row=0, col=0, cell_format=bold, data=fields)
            ws.autofilter(first_row=0, last_row=99999, first_col=0, last_col=len(fields)-1)
            for index, item in enumerate(item_list):
                row = map(lambda field_id: item.get(field_id, ''), fields)
                ws.write_row(row=index+1, col=0, data=row)
                ws.write_string(row=index+1, col=len(fields)-1, string=item_list[index][last_field].replace('\r', '\n')) # overwrite any that may have been formatted as URLs
            ws.freeze_panes(1, 0)
            ws.set_column(0, 2, 20)
            ws.set_column(3, len(fields)-1, 12)
            wb.close()

        def export_header(category):
            # Note: invisible char on first line to force UTF-8 encoding
            return category + '\n \n' + _('Exported from') + f' {current_archive}\n' + _('by') + f' {APP} ({VERSION}) ' + _('on') + f" {datetime.now().strftime('%Y-%m-%d @ %H:%M:%S')}\n" + '*'*76

        def export_annotations(fname):

            def get_annotations(all=False):
                item_list = []
                where = "WHERE Value <> '' AND Value IS NOT NULL"
                if not all:
                    where += f' AND LocationId IN {items}'
                sql = f'''
                    SELECT TextTag,
                        Value,
                        l.DocumentId doc,
                        l.IssueTagNumber,
                        l.KeySymbol,
                        CAST (TRIM(TextTag, 'abcdefghijklmnopqrstuvwxyz') AS INT) i
                    FROM InputField
                        LEFT JOIN
                        Location l USING (
                            LocationId
                        )
                    {where}
                    ORDER BY doc, i;
                    '''
                for row in con.execute(sql).fetchall():
                    item = {
                        'LABEL': row[0],
                        'VALUE': row[1].strip(),
                        'DOC': row[2],
                        'PUB': row[4]
                    }
                    if row[3] > 10000000:
                        item['ISSUE'] = row[3]
                    else:
                        item['ISSUE'] = None
                    item_list.append(item)
                return item_list

            if not fname:
                return get_annotations(True)
            item_list = get_annotations()
            if form == 'xlsx':
                fields = ['PUB', 'ISSUE', 'DOC', 'LABEL', 'VALUE']
                create_xlsx(fields, item_list, '{ANNOTATIONS}')
            elif form == 'txt':
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(export_header('{ANNOTATIONS}'))
                    for item in item_list:
                        iss = '{ISSUE='+str(item['ISSUE'])+'}' if item['ISSUE'] else ''
                        txt = '\n==={PUB='+item['PUB']+'}'+iss+'{DOC='+str(item['DOC'])+'}{LABEL='+item['LABEL']+'}===\n'+item['VALUE'].strip()
                        f.write(txt)
                    f.write('\n==={END}===')
            else: # 'md'
                for item in item_list:
                    iss = ''
                    pub = item['PUB']
                    fname = f'{self.working_dir}/{pub}/'
                    if item.get('ISSUE'):
                        iss = process_issue(item['ISSUE'])
                        fname += f'{iss}/'
                    fname += f"{item['DOC']}/"
                    fname += item['LABEL'] + '.md'
                    Path(fname).parent.mkdir(parents=True, exist_ok=True)
                    txt = f'---\npublication: {pub} {iss}'.strip()
                    txt += f"\ndocument: {item['DOC']}\nlabel: {item['LABEL']}\n---\n{item['VALUE'].strip()}\n"
                    with open(fname, 'w', encoding='utf-8') as f:
                        f.write(txt)
            return item_list

        def export_bookmarks(fname):
            if fname:
                where = f'WHERE BookmarkId IN {items}'
            else:
                where = ''
            item_list = []
            for row in con.execute(f'SELECT l.BookNumber, l.ChapterNumber, l.DocumentId, l.IssueTagNumber, l.KeySymbol, l.MepsLanguage, l.Type, Slot, REPLACE(b.Title, "|", "¦"), REPLACE(Snippet, "|", "¦"), BlockType, BlockIdentifier FROM Bookmark b LEFT JOIN Location l USING (LocationId) {where};').fetchall():
                item = '|'.join(str(x) if x is not None else 'None' for x in row)
                item_list.append(item)
            if fname:
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(export_header('{BOOKMARKS}'))
                    for item in item_list:
                        f.write(f'\n{item}')
            return item_list

        def export_favorites(fname):
            if fname:
                where = f'AND TagMapId IN {items}'
            else:
                where = ''
            item_list = []
            for row in con.execute(f"SELECT DocumentId, Track, IssueTagNumber, KeySymbol, MepsLanguage, Type FROM Location JOIN TagMap USING (LocationId) WHERE TagId = (SELECT TagId FROM Tag WHERE Type = 0 AND Name = 'Favorite') {where} ORDER BY Position;").fetchall():
                item = '|'.join(str(x) if x is not None else 'None' for x in row)
                item_list.append(item)
            if fname:
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(export_header('{FAVORITES}'))
                    for item in item_list:
                        f.write(f'\n{item}')
            return item_list

        def export_highlights(fname):
            if fname:
                where = f'WHERE BlockRangeId IN {items}'
            else:
                where = ''
            item_list = []
            for row in con.execute(f'SELECT b.BlockType, b.Identifier, b.StartToken, b.EndToken, u.ColorIndex, u.Version, l.BookNumber, l.ChapterNumber, l.DocumentId, l.IssueTagNumber, l.KeySymbol, l.MepsLanguage, l.Type FROM UserMark u JOIN Location l USING (LocationId), BlockRange b USING (UserMarkId) {where};').fetchall():
                item = '|'.join(str(x) if x is not None else 'None' for x in row)
                item_list.append(item)
            if fname:
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(export_header('{HIGHLIGHTS}'))
                    for item in item_list:
                        f.write(f'\n{item}')
            return item_list

        def export_notes(fname):

            def save_file(fname):
                record_modified = datetime.strptime(item['MODIFIED'][:19], '%Y-%m-%dT%H:%M:%S').timestamp()
                if os.path.exists(fname) and (os.stat(fname).st_mtime == record_modified):
                        return
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(txt)
                os.utime(fname, (record_modified, record_modified))

            def shorten_title(t):
                if not t:
                    return _('UNTITLED')
                t = regex.sub(r'(\d):+|:+', lambda m: f'{m.group(1)}.' if m.group(1) else '-', t)
                t = regex.sub(r'[^\w\s\-,().;]+', '', t)
                t = t.strip()
                if len(t) > 40:
                    m = regex.search(r'^(.{0,18}\w)\W', t)
                    if not m:
                        return t
                    left = m.group(1)
                    l = 33 - len(left)
                    m = regex.search(rf'\s(\w.{{0,{l}}})$', t)
                    if not m:
                        t = left + ' […]'
                    else:
                        t = left + ' […] ' + m.group(1)
                return t

            def get_notes(all=False):
                item_list = []
                if not all:
                    where = f'WHERE n.NoteId IN {items}'
                else:
                    where = ''
                sql = f'''
                    SELECT n.BlockType Type,
                        n.Title,
                        n.Content,
                        (
                            SELECT GROUP_CONCAT(t.Name, ' | ') 
                                FROM Note nt
                                    LEFT JOIN
                                    TagMap USING (
                                        NoteId
                                    )
                                    JOIN
                                    Tag t USING (
                                        TagId
                                    )
                                WHERE nt.NoteId = n.NoteId
                        ),
                        l.MepsLanguage,
                        l.BookNumber,
                        l.ChapterNumber,
                        n.BlockIdentifier,
                        l.DocumentId,
                        l.IssueTagNumber,
                        l.KeySymbol,
                        l.Title,
                        n.LastModified Date,
                        n.Created,
                        u.ColorIndex,
                        n.UserMarkId,
                        n.Guid
                    FROM Note n
                        LEFT JOIN
                        Location l USING (
                            LocationId
                        )
                        LEFT JOIN
                        UserMark u USING (
                            UserMarkId
                        )
                    {where} 
                    GROUP BY n.NoteId
                    ORDER BY Type, Date DESC;
                    '''
                for row in con.execute(sql).fetchall():
                    item = {
                        'TYPE': row[0],
                        'TITLE': row[1] or '',
                        'NOTE': row[2].strip() if row[2] else '',
                        'TAGS': row[3] or '',
                        'LANG': row[4],
                        'BK': row[5],
                        'CH': row[6],
                        'VS': row[7],
                        'BLOCK': row[7],
                        'DOC': row[8],
                        'PUB': row[10],
                        'HEADING': row[11] or '',
                        'MODIFIED': row[12][:19],
                        'CREATED': row[13][:19],
                        'COLOR': row[14] or 0,
                        'GUID': row[16]
                    }
                    item['RANGE'] = None
                    if row[15]:
                        rng = ''
                        for br in con.execute('SELECT Identifier, StartToken, EndToken FROM BlockRange WHERE UserMarkId = ? ORDER BY Identifier, StartToken;', (row[15],)).fetchall():
                            rng += f'{br[0]}:{br[1]}-{br[2]};'
                        rng = rng.strip(';')
                        if rng:
                            item['RANGE'] = rng
                    if 'T' not in item['MODIFIED']:
                        item['MODIFIED'] = item['MODIFIED'][:10] + 'T00:00:00'
                    if 'T' not in item['CREATED']:
                        item['CREATED'] = item['CREATED'][:10] + 'T00:00:00'
                    if row[9] and (row[9] > 10000000): # periodicals
                        item['ISSUE'] = row[9]
                    else:
                        item['ISSUE'] = None
                    if item['TYPE'] == 0 and not (item.get('BK') or item.get('DOC')): # independent note
                        item['BLOCK'] = None
                        item['VS'] = None
                        item['Link'] = None
                    else:
                        if item.get('BK'): # Bible note
                            if item.get('VS') is not None:
                                vs = str(item['VS']).zfill(3)
                                item['BLOCK'] = None
                            else:
                                vs = '000'
                            item['Reference'] = str(item['BK']).zfill(2) + str(item['CH']).zfill(3) + vs
                            item['Link'] = f"https://www.jw.org/finder?wtlocale={lang_symbol[item['LANG']]}&pub={item['PUB']}&bible={item['Reference']}"
                            if not item.get('HEADING'):
                                item['HEADING'] = f"{bible_books[item['BK']]} {item['CH']}"
                            elif item.get('VS') is not None and (':' not in item['HEADING']):
                                item['HEADING'] += f":{item['VS']}"
                        else: # publication note
                            item['VS'] = None
                            par = f"&par={item['BLOCK']}" if item.get('BLOCK') else ''
                            item['Link'] = f"https://www.jw.org/finder?wtlocale={lang_symbol[item['LANG']]}&docid={item['DOC']}{par}"
                    item_list.append(item)
                return item_list

            if not fname:
                return get_notes(True)
            item_list = get_notes()
            if form == 'xlsx':
                fields = ['CREATED', 'MODIFIED', 'TAGS', 'COLOR', 'RANGE', 'LANG', 'PUB', 'BK', 'CH', 'VS', 'Reference', 'ISSUE', 'DOC', 'BLOCK', 'HEADING', 'Link', 'TITLE', 'NOTE']
                create_xlsx(fields, item_list, '{NOTES=}')
            elif form == 'txt':
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(export_header('{NOTES=}'))
                    for item in item_list:
                        tags = item['TAGS'].replace(' | ', '|')
                        col = str(item['COLOR']) or '0'
                        rng = item['RANGE'] or ''
                        blk = '{BLOCK='+str(item['BLOCK'])+'}' if item.get('BLOCK') else ''
                        hdg = ('{HEADING='+item['HEADING']+'}') if item['HEADING'] != '' else ''
                        lng = str(item['LANG'])
                        txt = '\n==={CREATED='+item['CREATED']+'}{MODIFIED='+item['MODIFIED']+'}{TAGS='+tags+'}'
                        if item.get('BK'):
                            bk = str(item['BK'])
                            ch = str(item['CH'])
                            ref = '{Reference='+item['Reference']+'}' if item['Reference'] else ''
                            if item.get('VS') is not None:
                                vs = '{VS='+str(item['VS'])+'}'
                            else:
                                vs = ''
                            txt += '{LANG='+lng+'}{PUB='+item['PUB']+'}{BK='+bk+'}{CH='+ch+'}'+vs+blk+ref+hdg+'{COLOR='+col+'}'
                            if item.get('RANGE'):
                                txt += '{RANGE='+rng+'}'
                            if item.get('DOC'):
                                txt += '{DOC=0}'
                        elif item.get('DOC'):
                            doc = '{DOC='+str(item['DOC'])+'}' if item['DOC'] else ''
                            iss = '{ISSUE='+str(item['ISSUE'])+'}' if item['ISSUE'] else ''
                            txt += '{LANG='+lng+'}{PUB='+item['PUB']+'}'+iss+doc+blk+hdg+'{COLOR='+col+'}'
                            if item.get('RANGE'):
                                txt += '{RANGE='+rng+'}'
                        txt += '===\n'+item['TITLE']+'\n'+item['NOTE']
                        f.write(txt)
                    f.write('\n==={END}===')
            else: # 'md'
                group = self.combo_grouping.currentText()
                for item in item_list:
                    iss = ''
                    if item.get('PUB'):
                        pub = f"{item['PUB']}-{lang_symbol[item['LANG']]}"
                        lng = lang_name[item['LANG']]
                    else:
                        pub = None
                    fname = f'{self.working_dir}/'
                    if item['TYPE'] == 0 and not (item.get('BK') or item.get('DOC')):
                        fname += _('* INDEPENDENT *').strip('* ') + '/'
                    elif item.get('BK'):
                        fname += f"{pub}/{str(item['BK']).zfill(2)}_{bible_books[item['BK']]}/{str(item['CH']).zfill(3)}/"
                        if item.get('VS') is not None:
                            fname += str(item['VS']).zfill(3) + '_'
                    else:
                        fname += f'{pub}/'
                        if item.get('ISSUE'):
                            iss = process_issue(item['ISSUE'])
                            fname += f'{iss}/'
                        fname += f"{item['DOC']}/"
                        if item.get('BLOCK'):
                            fname += str(item['BLOCK']).zfill(3) + '_'
                    fname += shorten_title(item['TITLE']) + '_' + item['GUID'][:8] + '.md'
                    Path(fname).parent.mkdir(parents=True, exist_ok=True)
                    txt = f'---\ntitle: "' + item['TITLE'] + '"\n'
                    txt += f"created: {item['CREATED'][:19].replace('T', ' ')}\n"
                    txt += f"modified: {item['MODIFIED'][:19].replace('T', ' ')}\n"
                    if pub:
                        if group == _('Language'):
                            txt += f'language: "[[{lng}]]"\n'
                        else:
                            txt += f'language: "{lng}"\n'
                        txt += f'publication: "' + item['PUB'] + f' {iss}'.strip() + '"\n'
                    if item.get('DOC'):
                        txt += f'document: "[[' + str(item['DOC']) + ']]"\n'
                    elif item.get('Reference'):
                        txt += f'document: "[[' + item['Reference'] + ']]"\n'
                    if item.get('HEADING'):
                        txt += f'heading: "' + item['HEADING'] + '"\n'
                    if item.get('Link'):
                        txt += f"link: {item['Link']}\n"
                    if group == _('Color'):
                        txt += f'color: "[[' + str(item['COLOR']) + ']]"\n'
                    else:
                        txt += f'color: "' + str(item['COLOR']) + '"\n'
                    if item.get('TAGS'):
                        txt += 'tags:\n'
                        for t in item['TAGS'].split(' | '):
                            txt += f'  - "{t}"\n'
                    txt += f"guid: {item['GUID']}"
                    txt += f"\n---\n# {item['TITLE']}\n\n{item['NOTE'].strip()}\n"
                    save_file(fname)
            return item_list

        def export_playlist(fname):

            def playlist_export():
                expcon.execute('INSERT INTO Tag VALUES (?, ?, ?);', (1, 2, Path(fname).stem))

                rows = con.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="android_metadata";').fetchone()
                if rows:
                    lc = con.execute('SELECT locale FROM android_metadata;').fetchone()
                    expcon.execute('UPDATE android_metadata SET locale = ?;', (lc[0],))

                rows = con.execute(f'SELECT * FROM PlaylistItem WHERE PlaylistItemId IN {items};').fetchall()
                expcon.executemany('INSERT INTO PlaylistItem VALUES (?, ?, ?, ?, ?, ?, ?);', rows)
                item_list = []
                for row in rows:
                    item_list.append(row)

                rows = con.execute(f'SELECT * FROM PlaylistItemLocationMap WHERE PlaylistItemId IN {items};').fetchall()
                expcon.executemany('INSERT INTO PlaylistItemLocationMap VALUES (?, ?, ?, ?);', rows)

                rows = con.execute(f'SELECT * FROM PlaylistItemMarker WHERE PlaylistItemId IN {items};').fetchall()
                expcon.executemany('INSERT INTO PlaylistItemMarker VALUES (?, ?, ?, ?, ?, ?);', rows)

                rows = expcon.execute('SELECT PlaylistItemMarkerId FROM PlaylistItemMarker;').fetchall()
                pm = '(' + str([row[0] for row in rows]).strip('][') + ')'

                rows = con.execute(f'SELECT * FROM PlaylistItemMarkerBibleVerseMap WHERE PlaylistItemMarkerId IN {pm};').fetchall()
                expcon.executemany('INSERT INTO PlaylistItemMarkerBibleVerseMap VALUES (?, ?);', rows)

                rows = con.execute(f'SELECT * FROM PlaylistItemMarkerParagraphMap WHERE PlaylistItemMarkerId IN {pm};').fetchall()
                expcon.executemany('INSERT INTO PlaylistItemMarkerParagraphMap VALUES (?, ?, ?, ?);', rows)

                rows = con.execute(f'SELECT PlaylistItemId FROM TagMap WHERE PlaylistItemId IN {items} ORDER BY TagId, Position;').fetchall()
                pos = 0
                for row in rows:
                    expcon.execute('INSERT OR IGNORE INTO TagMap (PlaylistItemId, TagId, Position) VALUES (?, ?, ?);', (row[0], 1, pos))
                    pos += 1

                rows = con.execute(f'SELECT * FROM PlaylistItemIndependentMediaMap WHERE PlaylistItemId IN {items};').fetchall()
                expcon.executemany('INSERT INTO PlaylistItemIndependentMediaMap VALUES (?, ?, ?);', rows)

                rows = con.execute('SELECT * FROM PlaylistItemAccuracy;').fetchall()
                expcon.executemany('INSERT INTO PlaylistItemAccuracy VALUES (?, ?);', rows)

                rows = expcon.execute('SELECT ThumbnailFilePath FROM PlaylistItem WHERE ThumbnailFilePath IS NOT NULL;').fetchall()
                fp = '(' + str([row[0] for row in rows]).strip('][') + ')'

                rows = expcon.execute('SELECT IndependentMediaId FROM PlaylistItemIndependentMediaMap;').fetchall()
                mi = '(' + str([row[0] for row in rows]).strip('][') + ')'
                rows = con.execute(f'SELECT * FROM IndependentMedia WHERE FilePath IN {fp} OR IndependentMediaId IN {mi};').fetchall()
                expcon.executemany('INSERT INTO IndependentMedia VALUES (?, ?, ?, ?, ?);', rows)
                for f in rows:
                    shutil.copy2(TMP_PATH+'/'+f[2], playlist_path+'/'+f[2])

                rows = expcon.execute('SELECT LocationId FROM PlaylistItemLocationMap;').fetchall()
                lo = '('
                for row in rows:
                    lo += f'{row[0]}, '
                lo = lo.rstrip(', ') + ')'
                rows = con.execute(f'SELECT * FROM Location WHERE LocationId IN {lo};').fetchall()
                expcon.executemany('INSERT INTO Location VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);', rows)
                return item_list

            playlist_path = mkdtemp(prefix='JWLPlaylist_')
            with ZipFile(PROJECT_PATH / 'res/blank_playlist','r') as zipped:
                zipped.extractall(playlist_path)
            expcon = sqlite3.connect(f'{playlist_path}/userData.db')
            expcon.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF'; PRAGMA foreign_keys = 'OFF';")
            item_list = playlist_export()
            expcon.execute('INSERT INTO LastModified VALUES (?);', (datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),))
            expcon.executescript('PRAGMA foreign_keys = "ON"; VACUUM;')
            expcon.commit()
            expcon.close()
            m = {
                'name': APP,
                'creationDate': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'version': 1,
                'type': 1,
                'userDataBackup': {
                    'lastModifiedDate': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'deviceName': f'{APP}_{VERSION}',
                    'databaseName': 'userData.db',
                    'hash': sha256hash(f'{playlist_path}/userData.db'),
                    'schemaVersion': 14 } }
            with open(f'{playlist_path}/manifest.json', 'w') as json_file:
                    json.dump(m, json_file, indent=None, separators=(',', ':'))
            with ZipFile(fname, 'w', compression=ZIP_DEFLATED) as newzip:
                files = os.listdir(playlist_path)
                for f in files:
                    newzip.write(f'{playlist_path}/{f}', f)
            shutil.rmtree(playlist_path, ignore_errors=True)
            return item_list

        def export_all():
            items = {}
            functions = {
                'bookmarks': export_bookmarks,
                'highlights': export_highlights,
                'favorites': export_favorites,
                'annotations': export_annotations,
                'notes': export_notes }
            for item, func in functions.items():
                items[item] = func(None)
                self.progress_dialog.setValue(self.progress_dialog.value() + 1)
            return items

        if con: # coming from merge_items
            return export_all()
        category = self.combo_category.currentText()
        fname = export_file(category, form)
        if not fname:
            self.statusBar.showMessage(' '+_('NOT exported!'), 4000)
            return
        if form == 'md':
            self.working_dir = Path(fname)
        else:
            self.working_dir = Path(fname).parent
        current_archive = Path(self.current_archive).name if self.current_archive else _('NEW ARCHIVE')
        self.statusBar.showMessage(' '+_('Exporting. Please wait…'))
        app.processEvents()
        try:
            con = sqlite3.connect(f'{TMP_PATH}/{DB_NAME}')
            items = str(self.list_selected()).replace('[', '(').replace(']', ')')
            if category == _('Highlights'):
                item_list = export_highlights(fname)
            elif category == _('Favorites'):
                item_list = export_favorites(fname)
            elif category == _('Notes'):
                item_list = export_notes(fname)
            elif category == _('Annotations'):
                item_list = export_annotations(fname)
            elif category == _('Bookmarks'):
                item_list = export_bookmarks(fname)
            elif category == _('Playlists'):
                item_list = export_playlist(fname)
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        self.statusBar.showMessage(f' {len(item_list)} ' +_('items exported'), 4000)


    def import_items(self, file='', category='', item_list=None):

        def get_available_ids():
            available_ids = {}
            for table in {'Location', 'Bookmark', 'UserMark', 'Note', 'BlockRange', 'TagMap', 'PlaylistItem', 'IndependentMedia', 'Tag'}:
                expected = 1
                available = []
                for row in con.execute(f"SELECT {table}Id FROM {table} ORDER BY {table}Id").fetchall():
                    current = int(row[0])
                    while expected < current:
                        available.append(expected)
                        expected += 1
                    expected = current + 1
                available_ids[table] = available[::-1]
            return available_ids

        def import_annotations(item_list=None):

            def pre_import():
                line = import_file.readline()
                if regex.search('{ANNOTATIONS}', line):
                    return True
                else:
                    QMessageBox.critical(self, _('Error!'), _('Wrong import file format:\nMissing {ANNOTATIONS} tag line'), QMessageBox.Abort)
                    return False

            def read_text():

                def process_header(line):
                    attribs = {}
                    for (key, value) in regex.findall('{(.*?)=(.*?)}', line):
                        attribs[key] = value
                    return attribs

                count = 0
                items = []
                notes = import_file.read()
                for item in regex.finditer('^===({.*?})===\n(.*?)(?=\n==={)', notes, regex.S | regex.M):
                    try:
                        count += 1
                        header = item.group(1)
                        attribs = process_header(header)
                        attribs['VALUE'] = item.group(2)
                        items.append(attribs)
                    except:
                        QMessageBox.critical(self, _('Error!'), _('Annotations')+'\n\n'+_('Error on import!\n\nFaulting entry')+f' (#{count}):\n{header}', QMessageBox.Abort)
                        con.execute('ROLLBACK;')
                        return None
                schema = {'PUB': pl.Utf8, 'ISSUE': pl.Int64, 'DOC': pl.Int64, 'LABEL': pl.Utf8, 'VALUE': pl.Utf8}
                df = pl.DataFrame(items, schema=schema, orient='row' )
                return df

            def update_db(df):

                def add_location(attribs):
                    existing_id = con.execute('SELECT LocationId FROM Location WHERE DocumentId = ? AND IssueTagNumber = ? AND KeySymbol = ? AND MepsLanguage IS NULL AND Type = 0;', (attribs['DOC'], attribs['ISSUE'], attribs['PUB'])).fetchone()
                    if existing_id:
                        location_id = existing_id[0]
                    else:
                        if available_ids.get('Location'):
                            location_id = available_ids['Location'].pop()
                            con.execute('INSERT INTO Location (LocationId, DocumentId, IssueTagNumber, KeySymbol, MepsLanguage, Type) VALUES (?, ?, ?, ?, NULL, 0);', (location_id, attribs['DOC'], attribs['ISSUE'], attribs['PUB']))
                        else:
                            location_id = con.execute('INSERT INTO Location (DocumentId, IssueTagNumber, KeySymbol, MepsLanguage, Type) VALUES (?, ?, ?, NULL, 0);', (attribs['DOC'], attribs['ISSUE'], attribs['PUB'])).lastrowid
                    return location_id

                df = df.with_columns([
                    pl.col('ISSUE').fill_null(0),
                    pl.col('VALUE').fill_null('')
                ])
                count = 0
                for row in df.iter_rows(named=True):
                    try:
                        count += 1
                        location_id = add_location(row)
                        con.execute('INSERT INTO InputField (LocationId, TextTag, Value) VALUES (?, ?, ?) ON CONFLICT (LocationId, TextTag) DO UPDATE SET Value = excluded.Value;', (location_id, row['LABEL'], row['VALUE'].strip()))
                    except:
                        QMessageBox.critical(self, _('Error!'), _('Annotations')+'\n\n'+_('Error on import!\n\nFaulting entry')+f': #{count}', QMessageBox.Abort)
                        con.execute('ROLLBACK;')
                        return None
                return count

            if item_list:
                schema = {'PUB': pl.Utf8, 'ISSUE': pl.Int64, 'DOC': pl.Int64, 'LABEL': pl.Utf8, 'VALUE': pl.Utf8}
                df = pl.DataFrame(item_list, schema=schema, orient='row' )
                return update_db(df)
            if Path(file).suffix == '.txt':
                self.format = 'txt'
                with open(file, 'r', encoding='utf-8', errors='namereplace') as import_file:
                    if pre_import():
                        df = read_text()
                        if df.is_empty():
                            return None
                        count = update_db(df)
                    else:
                        count = 0
            else:
                self.format = 'xlsx'
                df = pl.read_excel(engine='xlsx2csv', source=file)
                count = update_db(df)
            return count

        def import_bookmarks(item_list=None):

            def pre_import():
                line = import_file.readline()
                if regex.search('{BOOKMARKS}', line):
                    return True
                else:
                    QMessageBox.critical(self, _('Error!'), _('Wrong import file format:\nMissing {BOOKMARKS} tag line'), QMessageBox.Abort)
                    return False

            def update_db():

                def add_scripture_location(attribs):
                    existing_id = con.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ?;', (attribs[4], attribs[5], attribs[0], attribs[1])).fetchone()
                    if existing_id:
                        location_id = existing_id[0]
                    else:
                        if available_ids.get('Location'):
                            location_id = available_ids['Location'].pop()
                            con.execute('INSERT INTO Location (LocationId, KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Type) VALUES (?, ?, ?, ?, ?, ?);', (location_id, attribs[4], attribs[5], attribs[0], attribs[1], attribs[6]))
                        else:
                            location_id = con.execute('INSERT INTO Location (KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Type) VALUES (?, ?, ?, ?, ?);', (attribs[4], attribs[5], attribs[0], attribs[1], attribs[6])).lastrowid
                    return location_id

                def add_publication_location(attribs):
                    existing_id = con.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = ?;', (attribs[4], attribs[5], attribs[3], attribs[2], attribs[6])).fetchone()
                    if existing_id:
                        location_id = existing_id[0]
                    else:
                        if available_ids.get('Location'):
                            location_id = available_ids['Location'].pop()
                            con.execute('INSERT INTO Location (LocationId, IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Type) VALUES (?, ?, ?, ?, ?, ?);', (location_id, attribs[3], attribs[4], attribs[5], attribs[2], attribs[6]))
                        else:
                            location_id = con.execute('INSERT INTO Location (IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Type) VALUES (?, ?, ?, ?, ?);', (attribs[3], attribs[4], attribs[5], attribs[2], attribs[6])).lastrowid
                    return location_id

                def add_bookmark(attribs, location_id):
                    existing_id = con.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND Type = 1 AND (BookNumber IS NULL OR BookNumber = 0) AND (ChapterNumber IS NULL OR ChapterNumber = 0) AND (DocumentId IS NULL OR DocumentId = 0)', (attribs[4], attribs[5])).fetchone()
                    if existing_id:
                        publication_id = existing_id[0]
                    else:
                        if available_ids.get('Location'):
                            publication_id = available_ids['Location'].pop()
                            con.execute('INSERT INTO Location (LocationId, KeySymbol, MepsLanguage, Type) VALUES (?, ?, ?, 1);', (publication_id, attribs[4], attribs[5]))
                        else:
                            publication_id = con.execute('INSERT INTO Location (KeySymbol, MepsLanguage, Type) VALUES (?, ?, 1);', (attribs[4], attribs[5])).lastrowid
                    existing_id = con.execute('SELECT BookmarkId FROM Bookmark WHERE PublicationLocationId = ? AND Slot = ?;', (publication_id, attribs[7])).fetchone()
                    if existing_id:
                        bookmark_id = existing_id[0]
                        con.execute('UPDATE Bookmark SET LocationId = ?, Title = ?, Snippet = ?, BlockType = ?, BlockIdentifier = ? WHERE BookmarkId = ?;', (location_id, attribs[8], attribs[9], attribs[10], attribs[11], bookmark_id))
                    else:
                        if available_ids.get('Bookmark'):
                            bookmark_id = available_ids['Bookmark'].pop()
                            con.execute('INSERT INTO Bookmark (BookmarkId, LocationId, PublicationLocationId, Slot, Title, Snippet, BlockType, BlockIdentifier) VALUES (?, ?, ?, ?, ?, ?, ?, ?);', (bookmark_id, location_id, publication_id, attribs[7], attribs[8], attribs[9], attribs[10], attribs[11]))
                        else:
                            con.execute('INSERT INTO Bookmark (LocationId, PublicationLocationId, Slot, Title, Snippet, BlockType, BlockIdentifier) VALUES (?, ?, ?, ?, ?, ?, ?);', (location_id, publication_id, attribs[7], attribs[8], attribs[9], attribs[10], attribs[11]))

                count = 0
                for line in import_file:
                    if '|' in line:
                        try:
                            count += 1
                            attribs = regex.split(r'\|', line.rstrip())
                            for i in [0,1,2,9,11]:
                                if attribs[i] == 'None':
                                    attribs[i] = None
                            if attribs[0]:
                                location_id = add_scripture_location(attribs)
                            else:
                                location_id = add_publication_location(attribs)
                            add_bookmark(attribs, location_id)
                        except:
                            QMessageBox.critical(self, _('Error!'), _('Bookmarks')+'\n\n'+_('Error on import!\n\nFaulting entry')+f' (#{count}):\n{line}', QMessageBox.Abort)
                            con.execute('ROLLBACK;')
                            return None
                return count

            if item_list:
                import_file = item_list
                return update_db()
            with open(file, 'r', encoding='utf-8') as import_file:
                if pre_import():
                    count = update_db()
                    if not count:
                        return None
                else:
                    count = 0
            return count

        def import_favorites(item_list=None):

            def pre_import():
                line = import_file.readline()
                if regex.search('{FAVORITES}', line):
                    return True
                else:
                    QMessageBox.critical(self, _('Error!'), _('Wrong import file format:\nMissing {FAVORITES} tag line'), QMessageBox.Abort)
                    return False

            def update_db():

                def tag_positions():
                    existing_id = con.execute('SELECT TagId FROM Tag WHERE Type = 0;').fetchone()
                    if existing_id:
                        tag_id = existing_id[0]
                    else:
                        if available_ids.get('Tag'):
                            tag_id = available_ids['Tag'].pop()
                            con.execute("INSERT INTO Tag (TagId, Type, Name) VALUES (?, 0, 'Favorite');", (tag_id,))
                        else:
                            tag_id = con.execute("INSERT INTO Tag (Type, Name) VALUES (0, 'Favorite');").lastrowid
                    position = con.execute('SELECT max(Position) FROM TagMap WHERE TagId = ?;', (tag_id,)).fetchone()
                    if position[0] != None:
                        return tag_id, position[0] + 1
                    else:
                        return tag_id, 0

                def get_current(tag_id):
                    favorite_list = []
                    for row in con.execute('SELECT DocumentId, Track, IssueTagNumber, KeySymbol, MepsLanguage, Type FROM Location JOIN TagMap USING (LocationId) WHERE TagId = ?;', (tag_id,)).fetchall():
                        item = '|'.join(str(x) if x is not None else 'None' for x in row)
                        favorite_list.append(item)
                    return favorite_list

                def add_publication_location(attribs):
                    con.execute('INSERT OR IGNORE INTO Location (DocumentId, Track, IssueTagNumber, KeySymbol, MepsLanguage, Type) VALUES (?, ?, ?, ?, ?, ?);', attribs)
                    conditions = []
                    params = []
                    columns = ['DocumentId', 'Track', 'IssueTagNumber', 'KeySymbol', 'MepsLanguage', 'Type']
                    for col, value in zip(columns, attribs):
                        if value is None:
                            conditions.append(f'{col} IS NULL')
                        else:
                            conditions.append(f'{col} = ?')
                            params.append(value)
                    sql = f"SELECT LocationId FROM Location WHERE {' AND '.join(conditions)};"
                    return con.execute(sql, params).fetchone()[0]

                tag_id, position = tag_positions()
                favorite_list = get_current(tag_id)
                count = 0
                for line in import_file:
                    if ('|' in line) and (line.strip() not in favorite_list):
                        try:
                            count += 1
                            attribs = regex.split(r'\|', line.rstrip())
                            attribs = [None if attr == 'None' else attr for attr in attribs]
                            location_id = add_publication_location(attribs)
                            if available_ids.get('TagMap'):
                                tagmap_id = available_ids['TagMap'].pop()
                                con.execute('INSERT INTO TagMap (TagMapId, LocationId, TagId, Position) VALUES (?, ?, ?, ?);', (tagmap_id, location_id, tag_id, position))
                            else:
                                con.execute('INSERT INTO TagMap (LocationId, TagId, Position) VALUES (?, ?, ?);', (location_id, tag_id, position))
                            position += 1
                        except:
                            QMessageBox.critical(self, _('Error!'), _('Favorites')+'\n\n'+_('Error on import!\n\nFaulting entry')+f' (#{count}):\n{line}', QMessageBox.Abort)
                            con.execute('ROLLBACK;')
                            return None
                return count

            if item_list:
                import_file = item_list
                return update_db()
            with open(file, 'r', encoding='utf-8') as import_file:
                if pre_import():
                    count = update_db()
                    if not count:
                        return None
                else:
                    count = 0
            return count

        def import_highlights(item_list=None):

            def pre_import():
                line = import_file.readline()
                if regex.search('{HIGHLIGHTS}', line):
                    return True
                else:
                    QMessageBox.critical(self, _('Error!'), _('Wrong import file format:\nMissing {HIGHLIGHTS} tag line'), QMessageBox.Abort)
                    return False

            def update_db():

                def add_scripture_location(attribs):
                    existing_id = con.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ?;', (attribs[10], attribs[11], attribs[6], attribs[7])).fetchone()
                    if existing_id:
                        location_id = existing_id[0]
                    else:
                        if available_ids.get('Location'):
                            location_id = available_ids['Location'].pop()
                            con.execute('INSERT INTO Location (LocationId, KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Type) VALUES (?, ?, ?, ?, ?, ?);', (location_id, attribs[10], attribs[11], attribs[6], attribs[7], attribs[12]))
                        else:
                            location_id = con.execute('INSERT INTO Location (KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Type) VALUES (?, ?, ?, ?, ?);', (attribs[10], attribs[11], attribs[6], attribs[7], attribs[12])).lastrowid
                    return location_id

                def add_publication_location(attribs):
                    existing_id = con.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = ?;', (attribs[10], attribs[11], attribs[9], attribs[8], attribs[12])).fetchone()
                    if existing_id:
                        location_id = existing_id[0]
                    else:
                        if available_ids.get('Location'):
                            location_id = available_ids['Location'].pop()
                            con.execute('INSERT INTO Location (LocationId, IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Type) VALUES (?, ?, ?, ?, ?, ?);', (location_id, attribs[9], attribs[10], attribs[11], attribs[8], attribs[12]))
                        else:
                            location_id = con.execute('INSERT INTO Location (IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Type) VALUES (?, ?, ?, ?, ?);', (attribs[9], attribs[10], attribs[11], attribs[8], attribs[12])).lastrowid
                    return location_id

                def add_usermark(attribs, location_id):
                    unique_id = uuid.uuid1()
                    if available_ids.get('UserMark'):
                        usermark_id = available_ids['UserMark'].pop()
                        con.execute(f"INSERT INTO UserMark (UserMarkId, ColorIndex, LocationId, StyleIndex, UserMarkGuid, Version) VALUES (?, ?, ?, 0, '{unique_id}', ?);", (usermark_id, attribs[4], location_id, attribs[5]))
                    else:
                        usermark_id = con.execute(f"INSERT INTO UserMark (ColorIndex, LocationId, StyleIndex, UserMarkGuid, Version) VALUES (?, ?, 0, '{unique_id}', ?);", (attribs[4], location_id, attribs[5])).lastrowid
                    rows = con.execute('SELECT * FROM BlockRange JOIN UserMark USING (UserMarkId) WHERE Identifier = ? AND LocationId = ?;', (attribs[1], location_id)).fetchall()
                    ns = int(attribs[2])
                    ne = int(attribs[3])
                    blocks = []
                    for row in rows:
                        cs = row[3]
                        ce = row[4]
                        if ce >= ns and ne >= cs:
                            ns = min(cs, ns)
                            ne = max(ce, ne)
                            blocks.append(row[0])
                    block = str(blocks).replace('[', '(').replace(']', ')')
                    con.execute(f'DELETE FROM BlockRange WHERE BlockRangeId IN {block};')
                    if available_ids.get('BlockRange'):
                        b_id = available_ids['BlockRange'].pop()
                        con.execute('INSERT INTO BlockRange (BlockRangeId, BlockType, Identifier, StartToken, EndToken, UserMarkId) VALUES (?, ?, ?, ?, ?, ?);', (b_id, attribs[0], attribs[1], ns, ne, usermark_id))
                    else:
                        con.execute('INSERT INTO BlockRange (BlockType, Identifier, StartToken, EndToken, UserMarkId) VALUES (?, ?, ?, ?, ?);', (attribs[0], attribs[1], ns, ne, usermark_id))

                count = 0
                for line in import_file:
                    if regex.match(r'^(\d+\|){6}', line):
                        try:
                            count += 1
                            attribs = regex.split(r'\|', line.rstrip().replace('None', ''))
                            if attribs[6]:
                                location_id = add_scripture_location(attribs)
                            else:
                                location_id = add_publication_location(attribs)
                            add_usermark(attribs, location_id)
                        except:
                            QMessageBox.critical(self, _('Error!'), _('Highlights')+'\n\n'+_('Error on import!\n\nFaulting entry')+f' (#{count}):\n{line}', QMessageBox.Abort)
                            con.execute('ROLLBACK;')
                            return None
                return count

            if item_list:
                import_file = item_list
                return update_db()
            with open(file, 'r', encoding='utf-8') as import_file:
                if pre_import():
                    count = update_db()
                    if not count:
                        return None
                else:
                    count = 0
            return count

        def import_notes(item_list=None):

            def pre_import():

                def delete_notes(title_char):
                    results = len(con.execute(f"SELECT NoteId FROM Note WHERE Title GLOB '{title_char}*';").fetchall())
                    if results < 1:
                        return
                    answer = QMessageBox.warning(self, _('Warning'), f'{results} '+_('notes starting with')+f' "{title_char}" '+_('WILL BE DELETED before importing.\n\nProceed with deletion? (NO to skip)'), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                    if answer == QMessageBox.Yes:
                        con.execute(f"DELETE FROM Note WHERE Title GLOB '{title_char}*';")

                line = import_file.readline()
                m = regex.search('{NOTES=(.?)}', line)
                if m:
                    if m.group(1) != '':
                        delete_notes(m.group(1))
                    return True
                else:
                    QMessageBox.critical(self, _('Error!'), _('Wrong import file format:\nMissing or malformed {NOTES=} attribute line'), QMessageBox.Abort)
                    return False

            def read_text():

                def process_header(line):
                    attribs = {}
                    for (key, value) in regex.findall('{(.*?)=(.*?)}', line):
                        attribs[key] = value
                    return attribs

                count = 0
                items = []
                notes = import_file.read()
                for item in regex.finditer('^===({.*?})===\n(.*?)(?=\n==={)', notes, regex.S | regex.M):
                    try:
                        count += 1
                        header = item.group(1)
                        attribs = process_header(header)
                        if item.group(2):
                            note = item.group(2).rstrip().split('\n')
                        else:
                            note = ['', '']
                        attribs['TITLE'] = note[0]
                        attribs['NOTE'] = '\n'.join(note[1:])
                        items.append(attribs)
                    except:
                        QMessageBox.critical(self, _('Error!'), _('Notes')+'\n\n'+_('Error on import!\n\nFaulting entry')+f' (#{count}):\n{header}', QMessageBox.Abort)
                        con.execute('ROLLBACK;')
                        return None
                schema = {'CREATED': pl.Utf8, 'MODIFIED': pl.Utf8, 'TAGS': pl.Utf8, 'COLOR': pl.Int64, 'RANGE': pl.Utf8, 'LANG': pl.Int64, 'PUB': pl.Utf8, 'BK': pl.Int64, 'CH': pl.Int64, 'VS': pl.Int64, 'ISSUE': pl.Int64, 'DOC': pl.Int64, 'BLOCK': pl.Int64, 'HEADING': pl.Utf8, 'TITLE': pl.Utf8, 'NOTE': pl.Utf8}
                df = pl.DataFrame(items, schema=schema, orient='row' )
                return df

            def update_db(df):

                def add_scripture_location(attribs):
                    existing_id = con.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ? AND Type = 0;', (attribs['PUB'], attribs['LANG'], attribs['BK'], attribs['CH'])).fetchone()
                    if existing_id:
                        location_id = existing_id[0]
                    else:
                        if available_ids.get('Location'):
                            location_id = available_ids['Location'].pop()
                            con.execute('INSERT INTO Location (LocationId, KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Title, Type) VALUES (?, ?, ?, ?, ?, ?, 0);', (location_id, attribs['PUB'], attribs['LANG'], attribs['BK'], attribs['CH'], attribs['HEADING']))
                        else:
                            location_id = con.execute('INSERT INTO Location (KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Title, Type) VALUES (?, ?, ?, ?, ?, 0);', (attribs['PUB'], attribs['LANG'], attribs['BK'], attribs['CH'], attribs['HEADING'])).lastrowid
                    if attribs.get('HEADING'):
                        attribs['HEADING'] = attribs['HEADING'].split(':')[0]
                        con.execute('UPDATE Location SET Title = ? WHERE LocationId = ?;', (attribs['HEADING'], location_id))
                    return location_id

                def add_publication_location(attribs):
                    existing_id = con.execute('SELECT LocationId from Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = 0;', (attribs['PUB'], attribs['LANG'], attribs['ISSUE'], attribs['DOC'])).fetchone()
                    if existing_id:
                        location_id = existing_id[0]
                    else:
                        if available_ids.get('Location'):
                            location_id = available_ids['Location'].pop()
                            con.execute('INSERT INTO Location (LocationId, IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Title, Type) VALUES (?, ?, ?, ?, ?, ?, 0);', (location_id, attribs['ISSUE'], attribs['PUB'], attribs['LANG'], attribs['DOC'], attribs['HEADING']))
                        else:
                            location_id = con.execute('INSERT INTO Location (IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Title, Type) VALUES (?, ?, ?, ?, ?, 0);', (attribs['ISSUE'], attribs['PUB'], attribs['LANG'], attribs['DOC'], attribs['HEADING'])).lastrowid
                    return location_id

                def add_usermark(attribs, location_id):
                    if int(attribs['COLOR']) == 0:
                        return None
                    if attribs['VS'] is not None:
                        block_type = 2
                        identifier = attribs['VS']
                    else:
                        block_type = 1
                        identifier = attribs['BLOCK']
                    unique_id = uuid.uuid1()
                    if available_ids.get('UserMark'):
                        usermark_id = available_ids['UserMark'].pop()
                        con.execute(f"INSERT INTO UserMark (UserMarkId, ColorIndex, LocationId, StyleIndex, UserMarkGuid, Version) VALUES (?, ?, ?, 0, '{unique_id}', 1);", (usermark_id, attribs['COLOR'], location_id))
                    else:
                        usermark_id = con.execute(f"INSERT INTO UserMark (ColorIndex, LocationId, StyleIndex, UserMarkGuid, Version) VALUES (?, ?, 0, '{unique_id}', 1);", (attribs['COLOR'], location_id)).lastrowid
                    if attribs['RANGE'] is None:
                        return usermark_id
                    for rng in attribs['RANGE'].split(';'):
                        if ':' in rng:
                            identifier, r = rng.split(':')
                        else:
                            r = rng
                        ns, ne = map(int, r.split('-'))
                        min_st = [ns]
                        max_et = [ne]
                        for row in con.execute('SELECT BlockRangeId, StartToken, EndToken FROM BlockRange JOIN UserMark USING (UserMarkId) WHERE LocationId = ? AND Identifier = ? AND StartToken <= ? AND EndToken >= ?', (location_id, identifier, ne, ns)).fetchall():
                            min_st.append(row[1])
                            max_et.append(row[2])
                            con.execute('DELETE FROM BlockRange WHERE BlockRangeId = ?;', (row[0],))
                        ns = min(min_st)
                        ne = max(max_et)
                        if available_ids.get('BlockRange'):
                            blockrange_id = available_ids['BlockRange'].pop()
                            con.execute('INSERT INTO BlockRange (BlockRangeId, BlockType, Identifier, StartToken, EndToken, UserMarkId) VALUES (?, ?, ?, ?, ?, ?);', (blockrange_id, block_type, identifier, ns, ne, usermark_id))
                        else:
                            con.execute('INSERT INTO BlockRange (BlockType, Identifier, StartToken, EndToken, UserMarkId) VALUES (?, ?, ?, ?, ?);', (block_type, identifier, ns, ne, usermark_id))
                    return usermark_id

                def update_note(attribs, location_id, block_type, usermark_id):

                    def process_tags(note_id, tags):
                        con.execute('DELETE FROM TagMap WHERE NoteId = ?;', (note_id,))
                        for tag in str(tags).split('|'):
                            tag = tag.strip()
                            if not tag:
                                continue
                            existing_id = con.execute('SELECT TagId from Tag WHERE Name = ?;', (tag,)).fetchone()
                            if existing_id:
                                tag_id = existing_id[0]
                            else:
                                if available_ids.get('Tag'):
                                    tag_id = available_ids['Tag'].pop()
                                    con.execute('INSERT INTO Tag (TagId, Type, Name) VALUES (?, 1, ?);', (tag_id, tag))
                                else:
                                    tag_id = con.execute('INSERT INTO Tag (Type, Name) VALUES (1, ?);', (tag,)).lastrowid
                            position = con.execute('SELECT ifnull(max(Position), -1) FROM TagMap WHERE TagId = ?;', (tag_id,)).fetchone()[0] + 1
                            con.execute('INSERT Into TagMap (NoteId, TagId, Position) VALUES (?, ?, ?);', (note_id, tag_id, position))

                    if attribs.get('TITLE'):
                        sql = 'TRIM(Title) = ?'
                        attrib = attribs['TITLE'].strip()
                    else:
                        sql = '(Title = "" OR Title IS NULL) AND TRIM(Content) = ?'
                        attrib = attribs['NOTE'].strip()
                    if location_id:
                        if attribs['BLOCK'] is not None:
                            blk = f"BlockIdentifier = {attribs['BLOCK']}"
                        else:
                            blk = 'BlockIdentifier IS NULL'
                        result = con.execute(f'SELECT NoteId, LastModified, Created FROM Note WHERE LocationId = ? AND {sql} AND {blk} AND BlockType = ?;', (location_id, attrib, block_type)).fetchone()
                    else:
                        result = con.execute(f'SELECT NoteId, LastModified, Created FROM Note WHERE {sql} AND BlockType = 0;', (attrib,)).fetchone()
                    if result:
                        note_id = result[0]
                        modified = attribs['MODIFIED'] if attribs['MODIFIED'] is not None else result[1]
                        created = attribs['CREATED'] if attribs['CREATED'] is not None else result[2]
                        created = created[:19] + 'Z'
                        modified = modified[:19] + 'Z'
                        con.execute('UPDATE Note SET UserMarkId = ?, Content = ?, LastModified = ?, Created = ? WHERE NoteId = ?;', (usermark_id, attribs['NOTE'], modified, created, note_id))
                    else:
                        unique_id = uuid.uuid1()
                        created = attribs['CREATED'] if attribs['CREATED'] is not None else (attribs['MODIFIED'] if attribs['MODIFIED'] is not None else datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
                        modified = attribs['MODIFIED'] if attribs['MODIFIED'] is not None else datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                        created = created[:19] + 'Z'
                        modified = modified[:19] + 'Z'
                        if available_ids.get('Note'):
                            note_id = available_ids['Note'].pop()
                            con.execute(f"INSERT INTO Note (NoteId, Guid, UserMarkId, LocationId, Title, Content, BlockType, BlockIdentifier, LastModified, Created) VALUES (?, '{unique_id}', ?, ?, ?, ?, ?, ?, ?, ?);", (note_id, usermark_id, location_id, attribs['TITLE'], attribs['NOTE'], block_type, attribs['BLOCK'], modified, created))
                        else:
                            note_id = con.execute(f"INSERT INTO Note (Guid, UserMarkId, LocationId, Title, Content, BlockType, BlockIdentifier, LastModified, Created) VALUES ('{unique_id}', ?, ?, ?, ?, ?, ?, ?, ?);", (usermark_id, location_id, attribs['TITLE'], attribs['NOTE'], block_type, attribs['BLOCK'], modified, created)).lastrowid
                    process_tags(note_id, attribs['TAGS'])

                df = df.with_columns([
                    pl.col('ISSUE').fill_null(0),
                    pl.col('COLOR').fill_null(0),
                    pl.col('TAGS').fill_null(''),
                    pl.col('TITLE').fill_null(''),
                    pl.col('NOTE').fill_null(''),
                    pl.col('HEADING').fill_null('')
                ])
                count = 0
                for row in df.iter_rows(named=True):
                    try:
                        count += 1
                        if row['BK'] is not None: # Bible note
                            location_id = add_scripture_location(row)
                            usermark_id = add_usermark(row, location_id)
                            if row['BLOCK'] is not None: # Bible book title
                                row['BLOCK'] = 1
                                block_type = 1
                            elif row['VS'] is not None: # regular note
                                block_type = 2
                                row['BLOCK'] = row['VS']
                            else: # top of chapter note
                                block_type = 0
                            update_note(row, location_id, block_type, usermark_id)
                        elif row['DOC'] is not None: # publication note
                            location_id = add_publication_location(row)
                            usermark_id = add_usermark(row, location_id)
                            block_type = 1 if row['BLOCK'] is not None else 0
                            update_note(row, location_id, block_type, usermark_id)
                        else: # independent note
                            update_note(row, None, 0, None)
                    except:
                        QMessageBox.critical(self, _('Error!'), _('Notes')+'\n\n'+_('Error on import!\n\nFaulting entry')+f': #{count}', QMessageBox.Abort)
                        con.execute('ROLLBACK;')
                        return None
                return count

            if item_list:
                schema = {'CREATED': pl.Utf8, 'MODIFIED': pl.Utf8, 'TAGS': pl.Utf8, 'COLOR': pl.Int64, 'RANGE': pl.Utf8, 'LANG': pl.Int64, 'PUB': pl.Utf8, 'BK': pl.Int64, 'CH': pl.Int64, 'VS': pl.Int64, 'ISSUE': pl.Int64, 'DOC': pl.Int64, 'BLOCK': pl.Int64, 'HEADING': pl.Utf8, 'TITLE': pl.Utf8, 'NOTE': pl.Utf8}
                df = pl.DataFrame(item_list, schema=schema, orient='row' )
                return update_db(df)
            if Path(file).suffix == '.txt':
                self.format = 'txt'
                with open(file, 'r', encoding='utf-8') as import_file:
                    if pre_import():
                        df = read_text()
                        if df.is_empty():
                            return None
                        count = update_db(df)
                    else:
                        count = 0
            else:
                self.format = 'xlsx'
                df = pl.read_excel(engine='xlsx2csv', source=file)
                count = update_db(df)
            return count

        def import_playlist(playlist_name):

            def update_db(playlist_name):

                def existing_media():
                    existing_fn = hashes[im_h]
                    if im_fp != existing_fn:
                        con.execute('UPDATE IndependentMedia SET OriginalFileName = ?, FilePath = ? WHERE Hash = ?;', (im_of, im_fp, im_h))
                        con.execute('UPDATE PlaylistItem SET ThumbnailFilePath = ? WHERE ThumbnailFilePath = ?;', (im_fp, existing_fn))
                        os.rename(os.path.join(TMP_PATH, existing_fn), os.path.join(TMP_PATH, im_fp))
                        hashes[im_h] = im_fp
                    return con.execute('SELECT IndependentMediaId FROM IndependentMedia WHERE Hash = ?;', (im_h,)).fetchone()[0]

                def add_media(im_imi, im_of, im_fp, im_mt, im_h):
                    tmp = im_fp
                    ext = 0
                    if im_h not in hashes:
                        while os.path.isfile(os.path.join(TMP_PATH, im_fp)):
                            ext += 1
                            im_fp = f'{tmp}_{ext}'
                        shutil.copy2(os.path.join(playlist_path, tmp), os.path.join(TMP_PATH, im_fp))
                        hashes[im_h] = im_fp
                    existing_id = con.execute('SELECT IndependentMediaId FROM IndependentMedia WHERE Hash = ?;', (im_h,)).fetchone()
                    if existing_id:
                        im_imi = existing_id[0]
                    else:
                        if available_ids.get('IndependentMedia'):
                            im_imi = available_ids['IndependentMedia'].pop()
                            con.execute('INSERT INTO IndependentMedia (IndependentMediaId, OriginalFileName, FilePath, MimeType, Hash) VALUES (?, ?, ?, ?, ?);', (im_imi, im_of, im_fp, im_mt, im_h))
                        else:
                            im_imi = con.execute('INSERT INTO IndependentMedia (OriginalFileName, FilePath, MimeType, Hash) VALUES (?, ?, ?, ?);', (im_of, im_fp, im_mt, im_h)).lastrowid
                    return im_imi

                def add_thumbnails(original_pii, pi_pii):
                    for row in impcon.execute('SELECT p.DurationTicks, i.IndependentMediaId, i.OriginalFilename, i.FilePath, i.MimeType, i.Hash FROM PlaylistItemIndependentMediaMap p LEFT JOIN IndependentMedia i USING (IndependentMediaId) WHERE p.PlaylistItemId = ?;', (original_pii,)).fetchall():
                        im_imi = add_media(*row[1:])
                        con.execute('INSERT INTO PlaylistItemIndependentMediaMap (PlaylistItemId, IndependentMediaId, DurationTicks) VALUES (?, ?, ?) ON CONFLICT(PlaylistItemId, IndependentMediaId) DO UPDATE SET DurationTicks = excluded.DurationTicks;', (pi_pii, im_imi, row[0]))

                def add_item():
                    con.execute('INSERT OR IGNORE INTO PlaylistItemAccuracy (Description) VALUES (?);', (pia_d,))
                    pia_piai = con.execute('SELECT PlaylistItemAccuracyId FROM PlaylistItemAccuracy WHERE Description = ?;', (pia_d,)).fetchone()[0]
                    existing_id = con.execute('SELECT PlaylistItemId FROM PlaylistItem WHERE Label = ? AND ThumbnailFilePath = ?;', (pi_l, im_fp)).fetchone()
                    if existing_id:
                        pi_pii = existing_id[0]
                    else:
                        if available_ids.get('PlaylistItem'):
                            pi_pii = available_ids['PlaylistItem'].pop()
                            con.execute('INSERT INTO PlaylistItem (PlaylistItemId, Label, StartTrimOffsetTicks, EndTrimOffsetTicks, Accuracy, EndAction, ThumbnailFilePath) VALUES (?, ?, ?, ?, ?, ?, ?);', (pi_pii, pi_l, pi_stot, pi_etot, pia_piai, pi_ea, im_fp))
                        else:
                            pi_pii = con.execute('INSERT INTO PlaylistItem (Label, StartTrimOffsetTicks, EndTrimOffsetTicks, Accuracy, EndAction, ThumbnailFilePath) VALUES (?, ?, ?, ?, ?, ?);', (pi_l, pi_stot, pi_etot, pia_piai, pi_ea, im_fp)).lastrowid
                    return pi_pii

                def add_tag():
                    if playlist not in tags:
                        if available_ids.get('Tag'):
                            t_ti = available_ids['Tag'].pop()
                            con.execute('INSERT INTO Tag (TagId, Type, Name) VALUES (?, 2, ?);', (t_ti, playlist))
                        else:
                            t_ti = con.execute('INSERT INTO Tag (Type, Name) VALUES (2, ?);', (playlist,)).lastrowid
                        tags[playlist] = t_ti
                        position = 0
                    else:
                        t_ti = tags.get(playlist)
                        position = con.execute('SELECT ifnull(max(Position), -1) FROM TagMap WHERE TagId = ?;', (t_ti,)).fetchone()[0] + 1
                    if available_ids.get('TagMap'):
                        tagmap_id = available_ids['TagMap'].pop()
                        con.execute('INSERT INTO TagMap (TagMapId, PlaylistItemId, TagId, Position) SELECT ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM TagMap WHERE TagMapId = ? AND PlaylistItemId = ? AND TagId = ? AND Position = ?);', (tagmap_id, pi_pii, t_ti, position, tagmap_id, pi_pii, t_ti, position))
                    else:
                        con.execute('INSERT INTO TagMap (PlaylistItemId, TagId, Position) SELECT ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM TagMap WHERE PlaylistItemId = ? AND TagId = ? AND Position = ?);', (pi_pii, t_ti, position, pi_pii, t_ti, position))

                def add_markers():
                    if not pim_stt:
                        return
                    existing_id = con.execute('SELECT PlaylistItemMarkerId FROM PlaylistItemMarker WHERE PlaylistItemId = ?;', (pi_pii)).fetchone()
                    if existing_id:
                        pim_pimi = existing_id[0]
                    else:
                        pim_pimi = con.execute('INSERT INTO PlaylistItemMarker (PlaylistItemId, Label, StarTimeTicks, DurationTicks, EndTransitionDurationTicks) VALUES (?, ?, ?, ?, ?);', (pi_pii, pim_l, pim_stt, pim_dt, pim_etdt)).lastrowid
                    if pimbvm_vi:
                        con.execute('INSERT INTO PlaylistItemMarkerBibleVerseMap (PlaylistItemMarkerId, VerseId) VALUES (?, ?) ON CONFLICT(PlaylistItemMarkerId, VerseId) DO UPDATE SET VerseId = excluded.VerseId;', (pim_pimi, pimbvm_vi))
                    if pimpm_mdi:
                        con.execute('INSERT INTO PlaylistItemMarkerParagraphMap (PlaylistItemMarkerId, MepsDocumentId, ParagraphIndex, MarkerIndexWithinParagraph) VALUES (?, ?, ?, ?) ON CONFLICT(PlaylistItemMarkerId, MepsDocumentId, ParagraphIndex, MarkerIndexWithinParagraph) DO UPDATE SET MepsDocumentId = excluded.MepsDocumentId, ParagraphIndex = excluded.ParagraphIndex, MarkerIndexWithinParagraph = excluded.MarkerIndexWithinParagraph;', (pim_pimi, pimpm_mdi, pimpm_pi, pimpm_miwp))

                def add_locations():
                    if not pilm_li:
                        return
                    if l_bn:
                        existing_id = con.execute('SELECT LocationId FROM Location WHERE BookNumber = ? AND ChapterNumber = ? AND KeySymbol = ? AND MepsLanguage = ?;', (l_bn, l_cn, l_ks, l_ml)).fetchone()
                        if existing_id:
                            l_li = existing_id[0]
                        else:
                            if available_ids.get('Location'):
                                l_li = available_ids['Location'].pop()
                                con.execute('INSERT INTO Location (LocationId, BookNumber, ChapterNumber, KeySymbol, MepsLanguage, Type, Title) VALUES (?, ?, ?, ?, ?, ?, ?);', (l_li, l_bn, l_cn, l_ks, l_ml, l_tp, l_t))
                            else:
                                l_li = con.execute('INSERT INTO Location (BookNumber, ChapterNumber, KeySymbol, MepsLanguage, Type, Title) VALUES (?, ?, ?, ?, ?, ?);', (l_bn, l_cn, l_ks, l_ml, l_tp, l_t)).lastrowid
                    else:
                        existing_id = con.execute('SELECT LocationId FROM Location WHERE Track = ? AND IssueTagNumber = ? AND KeySymbol = ? AND MepsLanguage = ? AND Type = ?;', (l_tr, l_itn, l_ks, l_ml, l_tp)).fetchone()
                        if existing_id:
                            l_li = existing_id[0]
                        else:
                            if available_ids.get('Location'):
                                l_li = available_ids['Location'].pop()
                                con.execute('INSERT INTO Location (LocationId, DocumentId, Track, IssueTagNumber, KeySymbol, MepsLanguage, Type, Title) VALUES (?, ?, ?, ?, ?, ?, ?, ?);', (l_li, l_di, l_tr, l_itn, l_ks, l_ml, l_tp, l_t))
                            else:
                                l_li = con.execute('INSERT INTO Location (DocumentId, Track, IssueTagNumber, KeySymbol, MepsLanguage, Type, Title) VALUES (?, ?, ?, ?, ?, ?, ?);', (l_di, l_tr, l_itn, l_ks, l_ml, l_tp, l_t)).lastrowid
                    con.execute('INSERT INTO PlaylistItemLocationMap (PlaylistItemId, LocationId, MajorMultimediaType, BaseDurationTicks) VALUES (?, ?, ?, ?) ON CONFLICT(PlaylistItemId, LocationId) DO UPDATE SET MajorMultimediaType = excluded.MajorMultimediaType, BaseDurationTicks = excluded.BaseDurationTicks;', (pi_pii, l_li, pilm_mmt, pilm_bdt))

                hashes = {}
                for row in con.execute('SELECT FilePath, Hash FROM IndependentMedia GROUP BY FilePath;').fetchall():
                    hashes[row[1]] = row[0]
                tags = {}
                for row in con.execute('SELECT TagId, Name FROM TagMap LEFT JOIN Tag USING (TagId) WHERE TYPE = 2 GROUP BY TagId;').fetchall():
                    tags[row[1]] = row[0]
                sql = 'SELECT * FROM PlaylistItem p LEFT JOIN PlaylistItemLocationMap USING (PlaylistItemId) LEFT JOIN Location USING (LocationId) LEFT JOIN PlaylistItemAccuracy a ON p.Accuracy = a.PlaylistItemAccuracyId LEFT JOIN TagMap USING (PlaylistItemId) LEFT JOIN Tag USING (TagId) JOIN IndependentMedia i ON i.FilePath = p.ThumbnailFilePath LEFT JOIN PlaylistItemMarker USING (PlaylistItemId) LEFT JOIN PlaylistItemMarkerBibleVerseMap USING (PlaylistItemMarkerId) LEFT JOIN PlaylistItemMarkerParagraphMap USING (PlaylistItemMarkerId)'
                count = 0
                for row in impcon.execute(sql).fetchall():
                    pi_pii, pi_l, pi_stot, pi_etot, _, pi_ea, _, pilm_li, pilm_mmt, pilm_bdt, l_bn, l_cn, l_di, l_tr, l_itn, l_ks, l_ml, l_tp, l_t, _, pia_d, _, _, _, _, _, _, t_n, im_imi, im_of, im_fp, im_mt, im_h, _, pim_l, pim_stt, pim_dt, pim_etdt, pimbvm_vi, pimpm_mdi, pimpm_pi, pimpm_miwp = row
                    playlist = playlist_name if playlist_name else t_n
                    if con.execute('SELECT * FROM PlaylistItem pi LEFT JOIN IndependentMedia im ON (pi.ThumbnailFilePath = im.FilePath) LEFT JOIN TagMap USING (PlaylistItemId) LEFT JOIN Tag USING (TagId) WHERE Name = ? AND Hash = ?;', (playlist, im_h)).fetchone():
                        continue
                    count += 1
                    if im_h in hashes:
                        im_imi = existing_media()
                    else:
                        im_imi = add_media(im_imi, im_of, im_fp, im_mt, im_h)
                    original_pii = pi_pii
                    pi_pii = add_item()
                    add_thumbnails(original_pii, pi_pii)
                    add_markers()
                    add_tag()
                    add_locations()
                return count

            playlist_path = mkdtemp(prefix='JWLPlaylist_')
            with ZipFile(file, 'r') as zipped:
                zipped.extractall(playlist_path)
            db = 'userData.db'
            impcon = sqlite3.connect(f'{playlist_path}/{db}')
            count = update_db(playlist_name)
            impcon.close()
            shutil.rmtree(playlist_path, ignore_errors=True)
            return count

        def import_all(items):
            try:
                count = import_bookmarks(items['bookmarks']) if items.get('bookmarks') else 0
                self.progress_dialog.setValue(self.progress_dialog.value() + 1)
                count += import_highlights(items['highlights']) if items.get('highlights') else 0
                self.progress_dialog.setValue(self.progress_dialog.value() + 1)
                count += import_favorites(items['favorites']) if items.get('favorites') else 0
                self.progress_dialog.setValue(self.progress_dialog.value() + 1)
                count += import_annotations(items['annotations']) if items.get('annotations') else 0
                self.progress_dialog.setValue(self.progress_dialog.value() + 1)
                count += import_notes(items['notes']) if items.get('notes') else 0
                self.progress_dialog.setValue(self.progress_dialog.value() + 1)
                count += import_playlist(None)
                self.progress_dialog.setValue(self.progress_dialog.value() + 1)
                return count
            except:
                self.progress_dialog.close()
                return None

        if item_list:
            try:
                con = sqlite3.connect(f'{TMP_PATH}/{DB_NAME}')
                con.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'MEMORY'; PRAGMA foreign_keys = 'OFF'; BEGIN;")
                available_ids = get_available_ids()
                count = import_all(item_list)
                con.execute("PRAGMA foreign_keys = 'ON';")
                con.commit()
                con.close()
            except Exception as ex:
                self.crash_box(ex)
                self.clean_up()
                sys.exit()
            return count
        if not file:
            category = self.combo_category.currentText()
            if category == _('Highlights') or category == _('Bookmarks') or category == _('Favorites'):
                flt = _('Text files')+' (*.txt)'
            elif category == _('Playlists'):
                flt = _('JW Library playlists')+' (*.jwlplaylist *.jwlibrary)'
            else:
                if self.format == 'xlsx':
                    flt = _('MS Excel files')+' (*.xlsx);;'+_('Text files')+' (*.txt)'
                else:
                    flt = _('Text files')+' (*.txt);;'+_('MS Excel files')+' (*.xlsx)'
            file = QFileDialog.getOpenFileName(self, _('Import file'), f'{self.working_dir}/', flt)[0]
            if not file:
                self.statusBar.showMessage(' '+_('NOT imported!'), 4000)
                return
        self.working_dir = Path(file).parent
        self.statusBar.showMessage(' '+_('Importing. Please wait…'))
        app.processEvents()
        try:
            con = sqlite3.connect(f'{TMP_PATH}/{DB_NAME}')
            con.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'MEMORY'; PRAGMA foreign_keys = 'OFF'; BEGIN;")
            available_ids = get_available_ids()
            if category == _('Annotations'):
                count = import_annotations()
            elif category == _('Bookmarks'):
                count = import_bookmarks()
            elif category == _('Favorites'):
                count = import_favorites()
            elif category == _('Highlights'):
                count = import_highlights()
            elif category == _('Notes'):
                count = import_notes()
            elif category == _('Playlists'):
                if Path(file).suffix == '.jwlplaylist':
                    playlist_name = Path(file).stem
                else:
                    playlist_name = None
                count = import_playlist(playlist_name)
            con.execute("PRAGMA foreign_keys = 'ON';")
            con.commit()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        if count == None:
            self.statusBar.showMessage(' '+_('NOT imported!'), 4000)
            return
        else:
            message = f' {category}: {count} '+_('items imported/updated')
            self.statusBar.showMessage(message, 4000)
        if count > 0:
            
            self.regroup(True, message)
            self.archive_modified()

    def merge_items(self, file=''):

        def init_progress():
            progress_dialog = QProgressDialog(_('Please wait…'), None, 0, 10, parent=self)
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setWindowTitle(_('Merging'))
            progress_dialog.setWindowFlag(Qt.FramelessWindowHint)
            progress_dialog.setModal(True)
            progress_dialog.setMinimumDuration(0)
            return progress_dialog

        self.statusBar.showMessage(' '+_('Merging. Please wait…'))
        app.processEvents()
        try:
            self.progress_dialog = init_progress()
            with ZipFile(file,'r') as zipped:
                zipped.extractall(f'{TMP_PATH}/merge')
            con = sqlite3.connect(f'{TMP_PATH}/merge/{DB_NAME}')
            items = self.export_items(form=None, con=con)
            count = self.import_items(item_list=items, file=file)
            con.close()
            shutil.rmtree(f'{TMP_PATH}/merge', ignore_errors=True)
        except Exception as ex:
            self.crash_box(ex)
            self.progress_dialog.close()
            self.clean_up()
            sys.exit()
        if count == None:
            self.statusBar.showMessage(' '+_('NOT merged!'), 4000)
            return
        else:
            message = f' {count} '+_('items merged')
            self.statusBar.showMessage(message, 4000)
        if count > 0:
            self.regroup(True, message)
            self.archive_modified()


    def data_viewer(self):

        def body_changed():
            if self.viewer_window.body.toPlainText() == self.note_item.body:
                self.viewer_window.body.setStyleSheet('font: normal;')
                self.body_modified = False
            else:
                self.viewer_window.body.setStyleSheet('font: italic;')
                self.body_modified = True
            update_editor_toolbar()

        def title_changed():
            if self.viewer_window.title.toPlainText() == self.note_item.title:
                self.viewer_window.title.setStyleSheet('font: bold; font-size: 20px;')
                self.title_modified = False
            else:
                self.viewer_window.title.setStyleSheet('font: bold italic; font-size: 20px;')
                self.title_modified = True
            update_editor_toolbar()

        def update_editor_toolbar():
            if self.title_modified or self.body_modified or self.color_modified:
                self.viewer_window.accept_action.setVisible(True)
            else:
                self.viewer_window.accept_action.setVisible(False)
            app.processEvents()

        def go_back():
            update_viewer_title()
            self.viewer_window.viewer_layout.setCurrentIndex(0)
            app.processEvents()
            self.title_modified = False
            self.body_modified = False
            self.color_modified = False

        def accept_change():
            self.note_item.title = self.viewer_window.title.toPlainText().strip()
            self.note_item.body = self.viewer_window.body.toPlainText().rstrip()
            self.note_item.update_note()
            color = self.viewer_window.title.property('note')
            self.note_item.color = self.colors[color]
            self.note_item.change_color()
            self.modified_list.append(self.note_item)
            update_viewer_toolbar()
            go_back()

        def apply_color(color):
            self.viewer_window.title.setProperty('note', color)
            self.viewer_window.body.setProperty('note', color)
            self.viewer_window.title.setStyleSheet(self.viewer_window.title.styleSheet())
            self.viewer_window.body.setStyleSheet(self.viewer_window.body.styleSheet())
            
        def change_color(action):
            color = action.data()
            apply_color(color)
            if color != self.note_color:
                self.color_modified = True
            else:
                self.color_modified = False
            update_editor_toolbar()

        def data_editor(counter):
            self.viewer_window.setWindowTitle(_('Data Editor'))
            self.note_item = self.viewer_items[counter]
            if self.note_item.meta:
                self.viewer_window.meta.setText(self.note_item.meta)
            else:
                self.viewer_window.meta.setHidden(True)
                self.viewer_window.title.setReadOnly(True)
            self.viewer_window.title.setPlainText(self.note_item.title)
            self.viewer_window.body.setPlainText(self.note_item.body)
            if self.note_item.indep is False:
                self.note_color = self.note_item.text_box.property('note')
                apply_color(self.note_color)
                self.viewer_window.color_actions[self.colors[self.note_color]].setChecked(True)
                self.viewer_window.color_action_group.setVisible(True)
            else:
                self.viewer_window.color_action_group.setVisible(False)

            app.processEvents()
            self.viewer_window.viewer_layout.setCurrentIndex(1)

        def update_viewer_toolbar():
            self.viewer_window.discard_action.setText(_('Discard changes and close'))
            self.viewer_window.confirm_action.setText(_('Confirm changes and close'))
            self.viewer_window.confirm_action.setToolTip('✔')
            self.viewer_window.discard_action.setToolTip('✗')
            self.viewer_window.confirm_action.setEnabled(True)
            self.viewer_window.discard_action.setEnabled(True)

        def update_viewer_title():
            self.viewer_window.setWindowTitle(_('Data Viewer') + f': {self.filtered}/{len(self.viewer_items) - len(self.deleted_list)} {self.combo_category.currentText()}')

        def delete_single_item(counter):

            def return_previous(row, col):
                col -= 1
                if col < 0:
                    col = 1
                    row -= 1
                return row, col

            self.note_item = self.viewer_items[counter]
            current_item = self.note_item.note_widget
            self.deleted_list.append(self.note_item)
            idx = self.viewer_window.grid_layout.indexOf(current_item)
            for item in current_item.parent().children():
                index = self.viewer_window.grid_layout.indexOf(item)
                if index < idx:
                    continue
                elif index == idx:
                    item.hide()
                else:
                    row, col, tmp, tmp  = self.viewer_window.grid_layout.getItemPosition(index)
                    row, col = return_previous(row, col)
                    self.viewer_window.grid_layout.addWidget(item, row, col)
            update_viewer_title()
            update_viewer_toolbar()
            app.processEvents()

        def filter_items():
            for item in self.viewer_items.values():
                if item in self.deleted_list:
                    continue
                if item.note_widget.isVisible():
                    if (self.viewer_window.filter_box.text().lower() not in item.title.lower()) and (self.viewer_window.filter_box.text().lower() not in item.body.lower()):
                        item.note_widget.setVisible(False)
                        self.filtered -= 1
                else:
                    if (self.viewer_window.filter_box.text().lower() in item.title.lower()) or (self.viewer_window.filter_box.text().lower() in item.body.lower()):
                        item.note_widget.setVisible(True)
                        self.filtered += 1
                app.processEvents()
            update_viewer_title()

        def update_db():

            def update_notes():
                for item in self.modified_list: # TODO: update item.color
                    con.execute('UPDATE Note SET Title = ?, Content = ?, LastModified = ? WHERE NoteId = ?;', (item.title, item.body, datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), item.idx))
                for item in self.deleted_list:
                    con.execute('DELETE FROM Note WHERE NoteId = ?;', (item.idx,))

            def update_annotations():
                for item in self.modified_list:
                    con.execute('UPDATE InputField SET Value = ? WHERE LocationId = ? AND TextTag = ?;', (item.body, item.idx, item.label))
                for item in self.deleted_list:
                    con.execute('DELETE FROM InputField WHERE LocationId = ? AND TextTag = ?;', (item.idx, item.label))

            try:
                con = sqlite3.connect(f'{TMP_PATH}/{DB_NAME}')
                con.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF'; PRAGMA foreign_keys = 'OFF'; BEGIN;")
                if category == _('Notes'):
                    update_notes()
                else:
                    update_annotations()
                con.execute("PRAGMA foreign_keys = 'ON';")
                con.commit()
                con.close()
            except Exception as ex:
                self.crash_box(ex)
                self.clean_up()
                sys.exit()
            viewer_closed()
            if len(self.deleted_list) > 0:
                message = f' {len(self.deleted_list)} '+_('items deleted')
                self.statusBar.showMessage(message, 4000)
                self.regroup(True, message)
            self.archive_modified()

        def viewer_closed():
            self.viewer_pos = self.viewer_window.pos()
            self.viewer_size = self.viewer_window.size()
            try:
                self.viewer_window.close()
            except:
                pass
            self.viewer_window = QDialog(self)
            self.activateWindow()

        def save_txt():
            fname = QFileDialog.getSaveFileName(self, _('Save') + ' TXT', f'{self.working_dir}/{category}.txt', _('Text files')+' (*.txt)')[0]
            if not fname:
                self.statusBar.showMessage(' '+_('NOT saved!'), 4000)
                return
            self.working_dir = Path(fname).parent
            txt = ''
            for item in self.viewer_items.values():
                if not item.note_widget.isVisible():
                    continue
                if category == _('Notes'):
                    txt += item.metadata + '\n---\n' + item.title + '\n\n' + item.body + '\n==========\n'
                else:
                    txt += item.metadata + '\n---\n' + item.body + '\n==========\n'
            with open(fname, 'w', encoding='utf-8') as txtfile:
                txtfile.write(txt)
            self.statusBar.showMessage(' '+_('Saved'), 4000)
            self.viewer_window.raise_()

        def clean_text(text):
            return regex.sub(r'\p{Z}', ' ', text.strip())

        def process_issue(i):
            issue = str(i)
            yr = issue[0:4]
            m = issue[4:6]
            d = issue[6:]
            if d == '00':
                d = ''
            else:
                d = '-' + d
            return f'{yr}-{m}{d}'

        def show_notes():

            def get_notes():
                item_list = []
                sql = f'''
                    SELECT n.BlockType Type,
                        n.Title,
                        n.Content,
                        (
                            SELECT GROUP_CONCAT(t.Name, ' | ') 
                                FROM Note nt
                                    LEFT JOIN
                                    TagMap USING (
                                        NoteId
                                    )
                                    JOIN
                                    Tag t USING (
                                        TagId
                                    )
                                WHERE nt.NoteId = n.NoteId
                        ),
                        l.MepsLanguage,
                        l.BookNumber,
                        l.ChapterNumber,
                        n.BlockIdentifier,
                        l.DocumentId,
                        l.IssueTagNumber,
                        l.KeySymbol,
                        l.Title,
                        n.LastModified Date,
                        u.ColorIndex,
                        b.StartToken,
                        b.EndToken,
                        n.NoteId,
                        n.Guid
                    FROM Note n
                        LEFT JOIN
                        Location l USING (
                            LocationId
                        )
                        LEFT JOIN
                        UserMark u USING (
                            UserMarkId
                        )
                        LEFT JOIN
                        TagMap USING (
                            NoteId
                        )
                        LEFT JOIN
                        Tag t USING (
                            TagId
                        )
                        LEFT JOIN
                        BlockRange b USING (
                            UserMarkId
                        )
                    WHERE n.NoteId IN {items} 
                    GROUP BY n.NoteId
                    ORDER BY Type, Date DESC;
                    '''
                for row in con.execute(sql).fetchall():
                    item = {
                        'TYPE': row[0],
                        'TITLE': row[1] or '',
                        'NOTE': row[2].strip() if row[2] else '',
                        'TAGS': row[3],
                        'BK': row[5],
                        'CH': row[6],
                        'VS': row[7],
                        'BLOCK': row[7],
                        'DOC': row[8],
                        'ISSUE': row[9] or '',
                        'PUB': row[10],
                        'HEADING': row[11],
                        'MODIFIED': row[12][:10],
                        'COLOR': row[13] or 0,
                        'ID': row[16],
                        'GUID': row[17]
                    }
                    try:
                        item['LANG'] = lang_symbol[row[4]]
                    except:
                        item['LANG'] = None
                    if row[14]:
                        item['RANGE'] = f'{row[14]}-{row[15]}'
                    else:
                        item['RANGE'] = None
                    if item['TYPE'] == 0 and not (item.get('BK') or item.get('DOC')): # independent note
                        item['Link'] = None
                    else: # attached note
                        if item.get('BK'): # Bible note
                            if item.get('VS') is not None:
                                vs = str(item['VS']).zfill(3)
                            else:
                                vs = '000'
                            script = str(item['BK']).zfill(2) + str(item['CH']).zfill(3) + vs
                            item['Link'] = f"https://www.jw.org/finder?wtlocale={item['LANG']}&pub={item['PUB']}&bible={script}"
                            if not item.get('HEADING'):
                                item['HEADING'] = f"{bible_books[item['BK']]} {item['CH']}"
                            elif item.get('VS') is not None and (':' not in item['HEADING']):
                                item['HEADING'] += f":{item['VS']}"
                        else: # publication note
                            par = f"&par={item['BLOCK']}" if item.get('BLOCK') else ''
                            item['Link'] = f"https://www.jw.org/finder?wtlocale={item['LANG']}&docid={item['DOC']}{par}"
                            if row[9] and (row[9] > 10000000):
                                item['ISSUE'] = process_issue(row[9])
                    item_list.append(item)
                return item_list

            counter = 1
            self.viewer_window.txt_action.setEnabled(False)
            self.viewer_window.setWindowTitle(_('Data Viewer') + ' — ' + _('Processing…'))
            for item in get_notes():
                metadata = f"title: {clean_text(item['TITLE'])}\n"
                metadata += f"date: {item['MODIFIED']}\n"
                if item.get('PUB'):
                    metadata += f"publication: {item['PUB']}-{item['LANG']} {item['ISSUE']}".strip() + '\n'
                    indep = False
                else:
                    indep = True
                if item.get('HEADING'):
                    metadata += f"document: {item['HEADING']}\n"
                if item.get('Link'):
                    metadata += f"link: {item['Link']}\n"
                metadata += f"color: {item['COLOR']}\n"
                if item.get('TAGS'):
                    metadata += f"tags: {item['TAGS']}\n"
                metadata += f"guid: {item['GUID']}"
                meta = ''
                if item['TAGS'] or item['PUB'] or item['Link']:
                    meta += f"<small><strong><tt>{item['MODIFIED']}"
                    if item['TAGS']:
                        meta += ' — {' + item['TAGS'] + '}'
                    if item['PUB']:
                        meta += f"<br><i>{item['PUB']}</i>-{item['LANG']} {item['ISSUE']}".strip()
                    if item['HEADING']:
                        meta += f" — {item['HEADING']}"
                    if item['Link']:
                        lnk = item['Link']
                        meta += f"<br>{lnk}"
                    meta += '</tt></strong></small>'
                note_box = ViewerItem(self, item['ID'], item['COLOR'], clean_text(item['TITLE']), clean_text(item['NOTE']), meta, metadata, indep)
                note_box.edit_button.clicked.connect(partial(data_editor, counter))
                note_box.delete_button.clicked.connect(partial(delete_single_item, counter))
                self.viewer_items[counter] = note_box
                row = int((counter+1) / 2) - 1
                col = (counter+1) % 2
                try:
                    self.viewer_window.grid_layout.setColumnStretch(col, 1)
                    self.viewer_window.grid_layout.addWidget(note_box.note_widget, row, col)
                    app.processEvents()
                except:
                    return
                counter += 1
            self.viewer_window.txt_action.setText('TXT')
            self.viewer_window.txt_action.setEnabled(True)

        def show_annotations():

            def get_annotations():
                item_list = []
                sql = f'''
                    SELECT TextTag,
                        Value,
                        l.DocumentId doc,
                        l.IssueTagNumber,
                        l.KeySymbol,
                        CAST (TRIM(TextTag, 'abcdefghijklmnopqrstuvwxyz') AS INT) i,
                        l.LocationId
                    FROM InputField
                        LEFT JOIN
                        Location l USING (
                            LocationId
                        )
                    WHERE LocationId IN {items}
                    ORDER BY doc, i;
                    '''
                for row in con.execute(sql).fetchall():
                    item = {
                        'LABEL': row[0],
                        'VALUE': row[1].strip() if row[1] else '',
                        'DOC': row[2],
                        'PUB': row[4],
                        'ID': row[6]
                    }
                    if row[3] > 10000000:
                        item['ISSUE'] = process_issue(row[3])
                    else:
                        item['ISSUE'] = ''
                    item_list.append(item)
                return item_list

            counter = 1
            self.viewer_window.txt_action.setEnabled(False)
            self.viewer_window.setWindowTitle(_('Data Viewer') + ' — ' + _('Processing…'))
            for item in get_annotations():
                metadata = f"publication: {item['PUB']} {item['ISSUE']}".strip()
                metadata += f"\ndocument: {item['DOC']}\n"
                metadata += f"label: {item['LABEL']}"
                title = f"{item['PUB']} {item['ISSUE']}\n{item['DOC']} — {item['LABEL']}"
                note_box = ViewerItem(self, item['ID'], 0, title, clean_text(item['VALUE']), None, metadata, True)
                note_box.label = item['LABEL']
                note_box.edit_button.clicked.connect(partial(data_editor, counter))
                note_box.delete_button.clicked.connect(partial(delete_single_item, counter))
                self.viewer_items[counter] = note_box
                row = int((counter+1) / 2) - 1
                col = (counter+1) % 2
                try:
                    self.viewer_window.grid_layout.setColumnStretch(col, 1)
                    self.viewer_window.grid_layout.addWidget(note_box.note_widget, row, col)
                    app.processEvents()
                except:
                    return
                counter += 1
            self.viewer_window.txt_action.setText('TXT')
            self.viewer_window.txt_action.setEnabled(True)

        def connect_signals():
            self.viewer_window.txt_action.triggered.connect(save_txt)
            self.viewer_window.finished.connect(viewer_closed)
            self.viewer_window.return_action.triggered.connect(go_back)
            self.viewer_window.accept_action.triggered.connect(accept_change)
            self.viewer_window.discard_action.triggered.connect(viewer_closed)
            self.viewer_window.confirm_action.triggered.connect(update_db)
            self.viewer_window.title.textChanged.connect(title_changed)
            self.viewer_window.body.textChanged.connect(body_changed)
            self.viewer_window.escape_pressed.connect(escape_pressed)
            self.viewer_window.filter_box.textChanged.connect(filter_items)
            self.viewer_window.color_action_group.triggered.connect(change_color)

        def escape_pressed():
            if self.viewer_window.viewer_layout.currentIndex() == 1:
                go_back()
            else:
                viewer_closed()

        selected = self.list_selected()
        self.filtered = len(selected)
        if len(selected) > 1500:
            QMessageBox.critical(self, _('Warning'), _('You are trying to preview {} items.\nPlease select a smaller subset.').format(len(selected)), QMessageBox.Cancel)
            return
        try:
            self.viewer_window.close()
        except:
            pass
        category = self.combo_category.currentText()
        self.viewer_items = {}
        self.deleted_list = []
        self.modified_list = []
        self.title_modified = False
        self.body_modified = False
        self.color_modified = False
        self.colors = {
            'grey': 0,
            'yellow': 1,
            'green': 2,
            'blue': 3,
            'red': 4,
            'orange': 5,
            'purple': 6 }
        self.viewer_window = DataViewer(self.viewer_size, self.viewer_pos)
        connect_signals()
        self.viewer_window.filter_box.setPlaceholderText(_('Filter')+' (Ctrl+F)')
        self.viewer_window.show()
        self.viewer_window.raise_()
        self.viewer_window.activateWindow()
        self.viewer_window.filter_box.setFocus()
        app.processEvents()
        try:
            con = sqlite3.connect(f'{TMP_PATH}/{DB_NAME}')
            items = str(selected).replace('[', '(').replace(']', ')')
            if category == _('Notes'):
                show_notes()
            else:
                show_annotations()
            update_viewer_title()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()


    def select_color(self):
        color_menu = QMenu(self.button_color)
        colors = {
            0: (_('Grey'), QColor('#808080')),
            1: (_('Yellow'), QColor('#FAD929')),
            2: (_('Green'), QColor('#81BD4F')),
            3: (_('Blue'), QColor('#5EB4EF')),
            4: (_('Red'), QColor('#DB5D8D')),
            5: (_('Orange'), QColor('#FF862E')),
            6: (_('Purple'), QColor('#7B57A7'))
        }
        for num, (name, color) in colors.items():
            pixmap = QPixmap(16, 16)
            pixmap.fill(color)
            icon = QIcon(pixmap)
            action = color_menu.addAction(icon, name)
            action.triggered.connect(lambda _, n=num: self.set_color(n))
        color_menu.exec(self.button_color.mapToGlobal(
            self.button_color.rect().bottomLeft()))

    def set_color(self, color):

        def colorize(cat):
            if cat == _('Highlights'):
                sql = f'SELECT UserMarkId FROM BlockRange WHERE BlockRangeId IN {items};'
            else:
                for row in con.execute(f'SELECT NoteId, LocationId FROM Note WHERE LocationId IS NOT NULL AND UserMarkId IS NULL AND NoteId IN {items};').fetchall():
                    unique_id = uuid.uuid1()
                    usermark_id = con.execute(f"INSERT INTO UserMark (ColorIndex, LocationId, StyleIndex, UserMarkGuid, Version) VALUES (?, ?, 0, '{unique_id}', 1);", (color, row[1])).lastrowid
                    con.execute('UPDATE Note SET UserMarkId = ? WHERE NoteId = ?;', (usermark_id, row[0]))
                sql = f'SELECT UserMarkId FROM Note WHERE UserMarkId IS NOT NULL AND NoteId IN {items};'
            rows = con.execute(sql).fetchall()
            ids = [x[0] for x in rows]
            lst = str(ids).replace('[', '(').replace(']', ')')
            con.execute(f'UPDATE UserMark SET ColorIndex = ? WHERE UserMarkId IN {lst};', (color,))
            return len(ids)

        category = self.combo_category.currentText()
        if category == _('Highlights') and color == 0:
            return
        reply = QMessageBox.warning(self, _('Delete'), _('Are you sure you want to change\n the COLOR of these {} items?').format(self.selected_items), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        self.statusBar.showMessage(' '+_('Modifying. Please wait…'))
        app.processEvents()
        try:
            con = sqlite3.connect(f'{TMP_PATH}/{DB_NAME}')
            con.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF'; PRAGMA foreign_keys = 'OFF'; BEGIN;")
            # items = self.list_selected()
            items = str(self.list_selected()).replace('[', '(').replace(']', ')')
            result = colorize(category)
            con.execute("PRAGMA foreign_keys = 'ON';")
            con.commit()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        message = f' {result} '+_('items modified')
        self.statusBar.showMessage(message, 4000)
        if result > 0:
            self.regroup(True, message)
            self.archive_modified()


    def tag_notes(self):
        return


    def add_items(self):

        def add_favorite():

            def add_dialog():

                def set_edition():
                    lng = language.currentText()
                    publication.clear()
                    filtered = favorites.filter(pl.col('Lang') == lng).select('Short')
                    publication.addItems(sorted(filtered['Short'].to_list()))

                dialog = QDialog(self)
                dialog.setWindowTitle(_('Add Favorite'))
                label = QLabel(dialog)
                label.setText(_('Select the language and Bible edition to add:'))

                language = QComboBox(dialog)
                language.addItem(' ')
                language.addItems(sorted(favorites['Lang'].unique()))
                language.setMaxVisibleItems(20)
                language.setStyleSheet('QComboBox { combobox-popup: 0; }')
                language.activated.connect(set_edition)
                publication = QComboBox(dialog)
                publication.setMinimumContentsLength(23)
                publication.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
                publication.setStyleSheet('QComboBox { combobox-popup: 0; }')

                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)

                layout = QVBoxLayout(dialog)
                layout.addWidget(label)
                form = QFormLayout()
                form.addRow(_('Language')+':', language)
                form.addRow(_('Edition')+':', publication)
                layout.addLayout(form)
                layout.addWidget(buttons)
                dialog.setWindowFlag(Qt.FramelessWindowHint)
                if dialog.exec():
                    return publication.currentText(), language.currentText()
                else:
                    return ' ', ' '

            def tag_positions():
                con.execute("INSERT INTO Tag (Type, Name) SELECT 0, 'Favorite' WHERE NOT EXISTS (SELECT 1 FROM Tag WHERE Type = 0 AND Name = 'Favorite');")
                tag_id = con.execute('SELECT TagId FROM Tag WHERE Type = 0;').fetchone()[0]
                position = con.execute('SELECT max(Position) FROM TagMap WHERE TagId = ?;', (tag_id,)).fetchone()
                if position[0] != None:
                    return tag_id, position[0] + 1
                else:
                    return tag_id, 0

            def add_location(symbol, language):
                con.execute('INSERT INTO Location (IssueTagNumber, KeySymbol, MepsLanguage, Type) SELECT 0, ?, ?, 1 WHERE NOT EXISTS (SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = 0 AND Type = 1);', (symbol, language, symbol, language))
                result = con.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = 0 AND Type = 1;', (symbol, language)).fetchone()
                return result[0]

            pub, lng = add_dialog()
            if pub == ' ' or lng == ' ':
                return False, ' '+_('Nothing added!')
            filtered = favorites.filter((pl.col('Short') == pub) & (pl.col('Lang') == lng))
            language = int(filtered['Language'].item())
            publication = filtered['Symbol'].item()
            location = add_location(publication, language)
            result = con.execute(f"SELECT TagMapId FROM TagMap WHERE LocationId = {location} AND TagId = (SELECT TagId FROM Tag WHERE Name = 'Favorite');").fetchone()
            if result:
                return False, ' '+_('Favorite for "{}" in {} already exists.').format(pub, lng)
            tag_id, position = tag_positions()
            con.execute('INSERT INTO TagMap (LocationId, TagId, Position) VALUES (?, ?, ?);', (location, tag_id, position))
            return 1, ' '+_('Added "{}" in {}').format(pub, lng)

        def add_images():

            def add_dialog():

                def select_files():
                    nonlocal files
                    dialog = QFileDialog(self, _('Select images'), f'{self.working_dir}/', _('Select images')+' (*)')
                    dialog.setFileMode(QFileDialog.ExistingFiles)
                    dialog.exec()
                    for f in dialog.selectedFiles():
                        self.working_dir = Path(f).parent
                        selected_files.add_file(f)

                def remove_files():
                    selected_files.clear_files()

                dialog = QDialog(self)
                dialog.resize(400, 450)
                dialog.setWindowTitle(_('Add Images'))

                label = QLabel(dialog)
                label.setText(_('Select existing playlist or type name of new one:'))

                lists = list(map(lambda x: x[0], con.execute('SELECT DISTINCT Name FROM Tag WHERE Type=2;').fetchall()))
                playlist = QComboBox(dialog)
                playlist.setEditable(True)
                playlist.addItems(sorted(lists))
                playlist.setMaxVisibleItems(20)

                get_files = QPushButton(dialog)
                get_files.setFixedSize(28, 28)
                get_files.setIcon(self.theme.icons['add'])
                get_files.clicked.connect(select_files)

                clear_files = QPushButton(dialog)
                clear_files.setFixedSize(28, 28)
                clear_files.setIcon(self.theme.icons['remove'])
                clear_files.clicked.connect(remove_files)

                selected_files = DropList()

                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)

                layout = QGridLayout(dialog)
                layout.addWidget(label, 0, 0, 1, 0)
                layout.addWidget(playlist, 1, 0, 1, 0)
                layout.addWidget(get_files, 3, 0)
                layout.addWidget(clear_files, 3, 1)
                layout.addWidget(selected_files, 2, 0, 1, 0)
                layout.addWidget(buttons, 3, 2)
                dialog.exec()
                files = []
                for f in selected_files.files: # filter out unique image files
                    try:
                        file_type = regex.search(r"mime_type='(image/.*?(\w+))'", str(puremagic.magic_file(f)[0]))
                        ext = Path(f).suffix.lstrip('.')
                        if not ext:
                            ext = file_type.group(2)
                        if ext in ['bmp', 'gif', 'heic', 'jpg', 'jpeg', 'png'] and f not in files:
                            files.append((f, file_type.group(1), ext))
                    except:
                        pass
                return playlist.currentText() or 'playlist', files

            def update_db(playlist, files):

                def check_name(file_name):
                    name = file_name
                    ext = 0
                    while name in current_files:
                        ext += 1
                        name = f'{file_name}_{ext}'
                    return name

                def check_label(label):
                    name = label
                    ext = 0
                    while name in current_labels:
                        ext += 1
                        name = f'{label} ({ext})'
                    return name

                def add_tag():
                    position = con.execute('SELECT ifnull(max(Position), -1) FROM TagMap WHERE TagId = ?;', (tag_id,)).fetchone()[0] + 1
                    con.execute('INSERT Into TagMap (PlaylistItemId, TagId, Position) VALUES (?, ?, ?);', (item_id, tag_id, position))

                try:
                    con.execute('INSERT INTO Tag (Type, Name) VALUES (2, ?);', (playlist,))
                    current_labels = []
                except:
                    tag_id = con.execute('SELECT TagId FROM Tag WHERE Name = ? AND Type = 2;', (playlist,)).fetchone()[0]
                    rows = con.execute('SELECT Label FROM PlaylistItem LEFT JOIN TagMap USING (PlaylistItemId) WHERE TagId = ?;', (tag_id,)).fetchall()
                    current_labels  = [x[0] for x in rows]

                rows = con.execute('SELECT * FROM IndependentMedia;').fetchall()
                current_files = [x[2] for x in rows]
                current_hashes = [x[4] for x in rows]

                result = 0
                for fl in files:
                    f = fl[0]
                    mime = fl[1]
                    ext = fl[2]
                    name = Path(f).name
                    hash256 = sha256hash(f)
                    if hash256 not in current_hashes:
                        current_hashes.append(hash256)
                        new_name = check_name(name)
                        current_files.append(new_name)
                        shutil.copy2(f, f'{TMP_PATH}/{new_name}')
                        media_id = con.execute('INSERT INTO IndependentMedia (OriginalFileName, FilePath, MimeType, Hash) VALUES (?, ?, ?, ?);', (name, new_name, mime, hash256)).lastrowid

                        unique_id = str(uuid.uuid1())
                        thumb_name = f'{unique_id}.{ext}'
                        shutil.copy2(f, f'{TMP_PATH}/{thumb_name}')
                        i = Image.open(f'{TMP_PATH}/{thumb_name}')
                        i.thumbnail((250, 250))
                        i.save(f'{TMP_PATH}/{thumb_name}')
                        thash = sha256hash(f'{TMP_PATH}/{thumb_name}')
                        con.execute('INSERT INTO IndependentMedia (OriginalFileName, FilePath, MimeType, Hash) VALUES (?, ?, ?, ?);', (name, thumb_name, mime, thash))

                    else: # file alread in archive
                        media_id, thumb_name = con.execute('SELECT IndependentMediaId, FilePath FROM IndependentMedia WHERE Hash = ?;', (hash256,)).fetchone()
                        if thumb_name != name:
                            thumb_name = con.execute('SELECT ThumbnailFilePath FROM PlaylistItemIndependentMediaMap JOIN PlaylistItem USING (PlaylistItemId) WHERE IndependentMediaId = ?;', (media_id,)).fetchone()[0]

                    result += 1
                    item_id = con.execute('INSERT INTO PlaylistItem (Label, Accuracy, EndAction, ThumbnailFilePath) VALUES (?, ?, ?, ?);', (check_label(name), 1, 1, thumb_name)).lastrowid
                    current_labels.append(name)
                    con.execute('INSERT INTO PlaylistItemIndependentMediaMap (PlaylistItemId, IndependentMediaId, DurationTicks) VALUES (?, ?, ?);', (item_id, media_id, 40000000))

                    add_tag()
                return result

            playlist, files = add_dialog()
            if len(files) == 0:
                return 0, ' '
            result = update_db(playlist, files)
            return result, f' {result} '+_('items added')

        category = self.combo_category.currentText()
        try:
            con = sqlite3.connect(f'{TMP_PATH}/{DB_NAME}')
            con.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF'; PRAGMA foreign_keys = 'OFF'; BEGIN;")
            if category == _('Favorites'):
                result, message = add_favorite()
            elif category == _('Playlists'):
                result, message = add_images()
            con.execute("PRAGMA foreign_keys = 'ON';")
            con.commit()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        if result > 0:
            self.statusBar.showMessage(message, 4000)
            self.regroup(True, message)
            self.archive_modified()

    def delete_items(self):

        def reorder_tags():
            for tag_id in con.execute('SELECT TagId FROM Tag').fetchall():
                pos = 1
                for tag_map in con.execute('SELECT TagMapId FROM TagMap WHERE TagId = ? ORDER BY Position;', (tag_id[0],)).fetchall():
                    con.execute('UPDATE TagMap SET Position = ? WHERE TagMapId = ?', (-pos, tag_map[0]))
                    pos += 1
            for tag_map in con.execute('SELECT TagMapId, Position FROM TagMap;').fetchall():
                con.execute('UPDATE TagMap SET Position = ? WHERE TagMapId = ?', (abs(tag_map[1])-1, tag_map[0]))
            con.execute('DELETE FROM Tag WHERE TagId > 0 AND TagId NOT IN ( SELECT TagId FROM TagMap );')

        def delete(table, field):
            return con.execute(f'DELETE FROM {table} WHERE {field} IN {items};').rowcount

        def delete_playlist_items():
            rows = con.execute(f'SELECT ThumbnailFilePath FROM PlaylistItem WHERE PlaylistItemId NOT IN {items};').fetchall()
            used_thumbs = [x[0] for x in rows]
            for f in con.execute(f'SELECT ThumbnailFilePath FROM PlaylistItem WHERE PlaylistItemId IN {items};').fetchall():
                if f[0] in used_thumbs: # used by other items; skip
                    continue
                con.execute('DELETE FROM IndependentMedia WHERE FilePath = ?;', f)
                try:
                    os.remove(TMP_PATH + '/' + f[0])
                except:
                    pass
            rows = con.execute(f'SELECT FilePath FROM IndependentMedia JOIN PlaylistItemIndependentMediaMap USING (IndependentMediaId) WHERE PlaylistItemId NOT IN {items};').fetchall()
            used_files = [x[0] for x in rows]
            for f in con.execute(f'SELECT FilePath FROM IndependentMedia JOIN PlaylistItemIndependentMediaMap USING (IndependentMediaId) WHERE PlaylistItemId IN {items};').fetchall():
                if f[0] in used_files: # used by other items; skip
                    continue
                con.execute('DELETE FROM IndependentMedia WHERE FilePath = ?;', f)
                try:
                    os.remove(TMP_PATH + '/' + f[0])
                except:
                    pass
            delete('PlaylistItemIndependentMediaMap', 'PlaylistItemId')
            delete('PlaylistItemLocationMap', 'PlaylistItemId')
            delete('TagMap', 'PlaylistItemId')

            con.execute(f'DELETE FROM PlaylistItemMarkerBibleVerseMap WHERE PlaylistItemMarkerId IN ( SELECT PlaylistItemMarkerId FROM PlaylistItemMarker WHERE PlaylistItemId IN {items});').fetchall()
            con.execute(f'DELETE FROM PlaylistItemMarkerParagraphMap WHERE PlaylistItemMarkerId IN ( SELECT PlaylistItemMarkerId FROM PlaylistItemMarker WHERE PlaylistItemId IN {items});').fetchall()
            delete('PlaylistItemMarker', 'PlaylistItemId')
            count = delete('PlaylistItem', 'PlaylistItemId')
            reorder_tags()
            return count

        def delete_items():
            if category == _('Bookmarks'):
                return delete('Bookmark', 'BookmarkId')
            elif category == _('Favorites'):
                return delete('TagMap', 'TagMapId')
            elif category == _('Highlights'):
                return delete('BlockRange', 'BlockRangeId')
            elif category == _('Notes'):
                count = delete('Note', 'NoteId')
                reorder_tags()
                return count
            elif category == _('Annotations'):
                return delete('InputField', 'LocationId')
            elif category == _('Playlists'):
                return delete_playlist_items()

        reply = QMessageBox.warning(self, _('Delete'), _('Are you sure you want to\nDELETE these {} items?').format(self.selected_items), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        self.statusBar.showMessage(' '+_('Deleting. Please wait…'))
        app.processEvents()
        category = self.combo_category.currentText()
        try:
            con = sqlite3.connect(f'{TMP_PATH}/{DB_NAME}')
            con.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF'; PRAGMA foreign_keys = 'OFF'; BEGIN;")
            items = str(self.list_selected()).replace('[', '(').replace(']', ')')
            result = delete_items()
            con.execute("PRAGMA foreign_keys = 'ON';")
            con.commit()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        if result > 0:
            message = f' {result} '+_('items deleted')
            self.statusBar.showMessage(message, 4000)
            self.regroup(True, message)
            self.archive_modified()


    def clean_items(self):

        def clean(txt):
            txt = regex.sub(spaces, ' ', txt)
            txt = regex.sub(joiners, '', txt)
            return txt.replace('\r', '\n')

        def clean_annotations():
            count = 0
            for value, item in con.execute('SELECT Value, TextTag FROM InputField;').fetchall():
                if regex.search(combined, value or ''):
                    count += 1
                    con.execute('UPDATE InputField SET Value = ? WHERE TextTag = ?;', (clean(value), item))
            return count

        def clean_notes():
            count = 0
            for title, content, item in con.execute('SELECT Title, Content, NoteId FROM Note;').fetchall():
                if regex.search(combined, (title or '') + (content or '')):
                    count += 1
                    if title:
                        title = clean(title)
                    if content:
                        content = clean(content)
                    con.execute('UPDATE Note SET Title = ?, Content = ? WHERE NoteId = ?;', (title, content, item))
            return count

        reply = QMessageBox.warning(self, _('Clean'), _('Are you sure you want to\nCLEAN the text fields?'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        self.statusBar.showMessage(' '+_('Cleaning. Please wait…'))
        app.processEvents()
        spaces = regex.compile(r'[\p{Zs}--\x20]', regex.V1)
        joiners = regex.compile(r'[\p{Zl}\p{Zp}]')
        combined = regex.compile(r'[[\p{Zl}\p{Zp}\p{Zs}]--[\x20]]', regex.V1)
        try:
            con = sqlite3.connect(f'{TMP_PATH}/{DB_NAME}')
            con.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF'; BEGIN;")
            result = clean_annotations()
            result += clean_notes()
            con.commit()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        message = f' {result} '+_('items cleaned')
        self.statusBar.showMessage(message, 4000)
        if result > 0:
            self.regroup(False, message)
            self.archive_modified()

    def obscure_items(self):

        def obscure_text(str):
            lst = list(words[randint(0,len(words)-1)])
            l = len(lst)
            i = 0
            s = ''
            for c in str:
                if m.match(c):
                    if c.isupper():
                        s += m.sub(lst[i].upper(), c)
                    else:
                        s += m.sub(lst[i], c)
                    i += 1
                    if i == l:
                        i = 0
                else:
                    s += c
            return s

        def obscure_locations():
            for title, item in con.execute('SELECT Title, LocationId FROM Location;').fetchall():
                if title:
                    title = obscure_text(title)
                    con.execute('UPDATE Location SET Title = ? WHERE LocationId = ?;', (title, item))

        def obscure_annotations():
            for content, item in con.execute('SELECT Value, TextTag FROM InputField;').fetchall():
                if content:
                    content = obscure_text(content)
                    con.execute('UPDATE InputField SET Value = ? WHERE TextTag = ?;', (content, item))

        def obscure_bookmarks():
            for title, content, item  in con.execute('SELECT Title, Snippet, BookmarkId FROM Bookmark;').fetchall():
                if title:
                    title = obscure_text(title)
                if content:
                    content = obscure_text(content)
                    con.execute('UPDATE Bookmark SET Title = ?, Snippet = ? WHERE BookmarkId = ?;', (title, content, item))
                else:
                    con.execute('UPDATE Bookmark SET Title = ? WHERE BookmarkId = ?;', (title, item))

        def obscure_notes():
            for title, content, item in con.execute('SELECT Title, Content, NoteId FROM Note;').fetchall():
                if title:
                    title = obscure_text(title)
                if content:
                    content = obscure_text(content)
                con.execute('UPDATE Note SET Title = ?, Content = ? WHERE NoteId = ?;', (title, content, item))

        reply = QMessageBox.warning(self, _('Mask'), _('Are you sure you want to\nMASK all text fields?'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        self.statusBar.showMessage(' '+_('Masking. Please wait…'))
        app.processEvents()
        words = ['obscured', 'yada', 'bla', 'gibberish', 'børk']
        m = regex.compile(r'\p{L}')
        try:
            con = sqlite3.connect(f'{TMP_PATH}/{DB_NAME}')
            con.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF'; BEGIN;")
            obscure_annotations()
            obscure_bookmarks()
            obscure_notes()
            obscure_locations()
            con.commit()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        message = ' '+_('Data masked')
        self.statusBar.showMessage(message, 4000)
        self.regroup(False, message)
        self.archive_modified()

    def sort_notes(self):

        def reorder():
            for tag_id in con.execute('SELECT TagId FROM Tag WHERE Type = 1;').fetchall():
                pos = 1
                for tag_map in con.execute('SELECT TagMapId FROM TagMap WHERE TagId = ? ORDER BY NoteId;', (tag_id[0],)).fetchall():
                    con.execute('UPDATE TagMap SET Position = ? WHERE TagMapId = ?', (-pos, tag_map[0]))
                    pos += 1
                for tag_map in con.execute('SELECT TagMapId, Position FROM TagMap WHERE TagId = ?', (tag_id[0],)).fetchall():
                    con.execute('UPDATE TagMap SET Position = ? WHERE TagMapId = ?', (abs(tag_map[1])-1, tag_map[0]))


        reply = QMessageBox.warning(self, _('Reorder'), _('All notes will be REORDERED.\nProceed?'), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.No:
            return
        self.statusBar.showMessage(' '+_('Reordering. Please wait…'))
        app.processEvents()
        try:
            con = sqlite3.connect(f'{TMP_PATH}/{DB_NAME}')
            con.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF'; BEGIN;")
            reorder()
            con.commit()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        message = ' '+_('Notes reordered')
        self.statusBar.showMessage(message, 4000)
        self.regroup(True, message)
        self.archive_modified()


    def trim_db(self):
        try:
            con = sqlite3.connect(f'{TMP_PATH}/{DB_NAME}')
            sql = """
                BEGIN;

                PRAGMA temp_store = 2;
                PRAGMA journal_mode = 'OFF';
                PRAGMA foreign_keys = 'OFF';

                -- Delete empty InputField and Note records
                DELETE FROM InputField WHERE COALESCE(Value, '') = '';
                DELETE FROM Note WHERE COALESCE(Title, '') = '' AND COALESCE(Content, '') = '';

                -- Delete orphaned TagMap records
                DELETE FROM TagMap WHERE
                    (NoteId IS NOT NULL AND NoteId NOT IN (SELECT NoteId FROM Note))
                    OR (PlaylistItemId IS NOT NULL AND PlaylistItemId NOT IN (SELECT PlaylistItemId FROM PlaylistItem));

                -- Delete unused Tags
                DELETE FROM Tag WHERE
                    TagId NOT IN (SELECT DISTINCT TagId FROM TagMap) AND Type > 0;

                -- Delete orphaned UserMark and BlockRange records
                DELETE FROM UserMark WHERE
                    LocationId NOT IN (SELECT LocationId FROM Location)
                    OR (UserMarkId NOT IN (SELECT UserMarkId FROM BlockRange)
                        AND UserMarkId NOT IN (SELECT UserMarkId FROM Note));
                DELETE FROM BlockRange WHERE UserMarkId NOT IN (SELECT UserMarkId FROM UserMark);

                -- Delete orphaned PlaylistItem and related records
                DELETE FROM PlaylistItem WHERE PlaylistItemId NOT IN (SELECT PlaylistItemId FROM TagMap);
                DELETE FROM PlaylistItemMarker WHERE PlaylistItemId NOT IN (SELECT PlaylistItemId FROM PlaylistItem);
                DELETE FROM PlaylistItemLocationMap WHERE PlaylistItemId NOT IN (SELECT PlaylistItemId FROM PlaylistItem);
                DELETE FROM PlaylistItemIndependentMediaMap WHERE PlaylistItemId NOT IN (SELECT PlaylistItemId FROM PlaylistItem);
                DELETE FROM PlaylistItemIndependentMediaMap WHERE IndependentMediaId NOT IN (SELECT IndependentMediaId FROM IndependentMedia);
                DELETE FROM PlaylistItemMarkerBibleVerseMap WHERE PlaylistItemMarkerId NOT IN (SELECT PlaylistItemMarkerId FROM PlaylistItemMarker);
                DELETE FROM PlaylistItemMarkerParagraphMap WHERE PlaylistItemMarkerId NOT IN (SELECT PlaylistItemMarkerId FROM PlaylistItemMarker);

                -- Delete unused Location records
                DELETE FROM Location WHERE
                    LocationId NOT IN (SELECT LocationId FROM UserMark)
                    AND LocationId NOT IN (SELECT LocationId FROM Note)
                    AND LocationId NOT IN (SELECT LocationId FROM TagMap)
                    AND LocationId NOT IN (SELECT LocationId FROM Bookmark)
                    AND LocationId NOT IN (SELECT PublicationLocationId FROM Bookmark)
                    AND LocationId NOT IN (SELECT LocationId FROM InputField)
                    AND LocationId NOT IN (SELECT LocationId FROM PlaylistItemLocationMap);

                -- Fix "missing" note links
                UPDATE Location SET Title = "" WHERE Title IS NULL;

                PRAGMA foreign_keys = 'ON';
                COMMIT;

                VACUUM;
                """
            con.executescript(sql)
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()


    def clean_up(self):
        try:
            self.viewer_window.close()
            self.help_window.close()
        except:
            pass
        shutil.rmtree(TMP_PATH, ignore_errors=True)
        settings.setValue('JWLManager/language', self.lang)
        settings.setValue('JWLManager/category', self.combo_category.currentIndex())
        settings.setValue('JWLManager/title', self.title_format)
        settings.setValue('JWLManager/theme', self.mode)
        settings.setValue('JWLManager/column1', self.treeWidget.columnWidth(0))
        settings.setValue('JWLManager/column2', self.treeWidget.columnWidth(1))
        settings.setValue('JWLManager/sort', self.treeWidget.sortColumn())
        settings.setValue('JWLManager/direction', self.treeWidget.header().sortIndicatorOrder())
        settings.setValue('JWLManager/format', self.format)
        settings.setValue('Main_Window/position', self.pos())
        settings.setValue('Main_Window/size', self.size())
        settings.setValue('Viewer/position', self.viewer_pos)
        settings.setValue('Viewer/size', self.viewer_size)
        settings.setValue('Help/position', self.help_pos)
        settings.setValue('Help/size', self.help_size)
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)


def set_settings_path():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        try:
            application_path = os.path.dirname(os.path.realpath(__file__))
        except NameError:
            application_path = os.getcwd()
    settings_path = application_path+'/'+APP+'.conf'
    global LOCK_FILE
    LOCK_FILE = application_path+'/'+'JWLManager.lock'
    if not os.path.exists(settings_path) and os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
    return QSettings(settings_path, QSettings.Format.IniFormat)

def write_lockfile(file):
    with open(LOCK_FILE, 'w') as lockfile:
        lockfile.write(file)

def get_language():
    global available_languages, tr
    available_languages = { # add/enable completed languages
        'de': 'German (Deutsch)',
        'en': 'English (default)',
        'es': 'Spanish (español)',
        'fr': 'French (français)',
        'it': 'Italian (italiano)',
        'pl': 'Polish (Polski)',
        'pt': 'Portuguese (Português)',
        'ru': 'Russian (Pусский)',
        'uk': 'Ukrainian (українська)'
        }
    tr = {}
    localedir = PROJECT_PATH / 'res/locales/'

    parser = argparse.ArgumentParser(description='Manage .jwlibrary backup archives')
    parser.add_argument('-v', '--version', action='version', version=f'{APP} {VERSION}', help='show version and exit')
    language_group = parser.add_argument_group('interface language', 'English by default')
    group = language_group.add_mutually_exclusive_group(required=False)
    parser.add_argument('archive', type=str, nargs='?', default=None, help='archive to open')
    for k in sorted(available_languages.keys()):
        group.add_argument(f'-{k}', action='store_true', help=available_languages[k])
        tr[k] = gettext.translation('messages', localedir, fallback=True, languages=[k])
    args = vars(parser.parse_args())
    lng = settings.value('JWLManager/language', 'en')
    for l in available_languages.keys():
        if args[l]:
            lng = l
            break
    if args['archive']:
        sys.argv.append(args['archive'])
    if os.path.exists(LOCK_FILE) and os.path.getsize(LOCK_FILE) == 0:
        print(LOCK_FILE)
        if len(sys.argv) > 1 and os.path.exists(sys.argv[-1]):
            write_lockfile(sys.argv[-1])
        sys.exit(0)
    else:
        write_lockfile('')
    return lng

def read_resources(lng):

    def load_bible_books(lng):
        for row in con.execute('SELECT Number, Name FROM BibleBooks WHERE Language = ?;', (lng,)).fetchall():
            bible_books[row[0]] = row[1]

    def load_languages():
        for row in con.execute('SELECT Language, Name, Code, Symbol FROM Languages;').fetchall():
            lang_name[row[0]] = row[1]
            lang_symbol[row[0]] = row[3]
            if row[2] == lng:
                ui_lang = row[0]
        return ui_lang

    global _, bible_books, favorites, lang_name, lang_symbol, publications

    _ = tr[lng].gettext
    lang_name = {}
    lang_symbol = {}
    bible_books = {}

    con = sqlite3.connect(PROJECT_PATH / 'res/resources.db')
    ui_lang = load_languages()
    load_bible_books(ui_lang)

    pubs = pl.read_database(f"SELECT Symbol, ShortTitle Short, Title 'Full', Year, [Group] Type FROM Publications p JOIN Types USING (Type, Language) WHERE Language = {ui_lang};", con)
    extras = pl.read_database(f"SELECT Symbol, ShortTitle Short, Title 'Full', Year, [Group] Type FROM Extras p JOIN Types USING (Type, Language) WHERE Language = {ui_lang};", con)

    publications = pl.concat([pubs, extras])
    favorites = pl.read_database("SELECT * FROM Favorites;", con)
    con.close()

def sha256hash(file: str) -> str:
    return sha256(open(file, "rb").read()).hexdigest()

if __name__ == "__main__":
    settings = set_settings_path()
    lang = get_language()
    read_resources(lang)
    app = QApplication(sys.argv)
    global translator
    translator = {}
    translator[lang] = QTranslator()
    translator[lang].load(f'{PROJECT_PATH}/res/locales/UI/qt_{lang}.qm')
    app.installTranslator(translator[lang])
    font = QFont()
    font.setPixelSize(16)
    app.setFont(font)
    app.setStyle('Fusion')
    win = Window(sys.argv[-1])
    win.show()
    sys.exit(app.exec())
