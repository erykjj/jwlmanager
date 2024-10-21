#!/usr/bin/env python3

"""
  JWLManager:   Multi-platform GUI for managing JW Library files:
                view, delete, edit, merge (via export/import), etc.

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

APP = 'JWLManager'
VERSION = 'v5.1.0'


from res.ui_main_window import Ui_MainWindow
from res.ui_extras import CustomTreeWidget, AboutBox, HelpBox, DataViewer, ViewerItem, DropList

from PySide6.QtCore import QEvent, QPoint, QSettings, QSize, Qt, QTranslator
from PySide6.QtGui import QAction, QFont, QMouseEvent, QPixmap
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QGridLayout, QLabel, QMainWindow, QMenu, QMessageBox, QProgressDialog, QPushButton, QTextEdit, QTreeWidgetItem, QTreeWidgetItemIterator, QVBoxLayout, QWidget)

from datetime import datetime, timezone
from filehash import FileHash
from functools import partial
from pathlib import Path
from PIL import Image
from platform import platform
from random import randint
from tempfile import mkdtemp
from time import time
from traceback import format_exception
from xlsxwriter import Workbook
from zipfile import ZipFile, ZIP_DEFLATED

import argparse, gettext, glob, json, puremagic, os, regex, requests, shutil, sqlite3, sys, uuid
import pandas as pd


#### Initial language setting based on passed arguments
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
        # 'zh': 'Chinese (中文)',
        }
    tr = {}
    localedir = project_path / 'res/locales/'

    parser = argparse.ArgumentParser(description='Manage .jwlibrary backup archives')
    parser.add_argument('-v', '--version', action='version', version=f'{APP} {VERSION}', help='show version and exit')
    language_group = parser.add_argument_group('interface language', 'English by default')
    group = language_group.add_mutually_exclusive_group(required=False)
    for k in sorted(available_languages.keys()):
        group.add_argument(f'-{k}', action='store_true', help=available_languages[k])
        tr[k] = gettext.translation('messages', localedir, fallback=True, languages=[k])
    args = vars(parser.parse_args())

    lng = settings.value('JWLManager/language', 'en')
    for l in args.keys():
        if args[l]:
            lng = l
    return lng

def read_resources(lng):

    def load_bible_books(lng):
        for row in con.execute(f'SELECT Number, Name FROM BibleBooks WHERE Language = {lng};').fetchall():
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
    con = sqlite3.connect(project_path / 'res/resources.db')
    ui_lang = load_languages()
    load_bible_books(ui_lang)
    pubs = pd.read_sql_query(f"SELECT Symbol, ShortTitle Short, Title 'Full', Year, [Group] Type FROM Publications p JOIN Types USING (Type, Language) WHERE Language = {ui_lang};", con)
    extras = pd.read_sql_query(f"SELECT Symbol, ShortTitle Short, Title 'Full', Year, [Group] Type FROM Extras p JOIN Types USING (Type, Language) WHERE Language = {ui_lang};", con)
    publications = pd.concat([pubs, extras], ignore_index=True)
    favorites = pd.read_sql_query("SELECT * FROM Favorites;", con)
    con.close()

def set_settings_path():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        try:
            application_path = os.path.dirname(os.path.realpath(__file__))
        except NameError:
            application_path = os.getcwd()
    return QSettings(application_path+'/'+APP+'.conf', QSettings.Format.IniFormat)

project_path = Path(__file__).resolve().parent
tmp_path = mkdtemp(prefix='JWLManager_')
db_name = 'userData.db'
settings = set_settings_path()
lang = get_language()
read_resources(lang)

#### Main app
class Window(QMainWindow, Ui_MainWindow):
    def __init__(self):
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
            self.actionQuit.triggered.connect(self.clean_up)
            self.actionSave.triggered.connect(self.save_file)
            self.actionSave_As.triggered.connect(self.save_as_file)
            self.actionObscure.triggered.connect(self.obscure_items)
            self.actionReindex.triggered.connect(self.reindex_db)
            self.actionSort.triggered.connect(self.sort_notes)
            self.actionExpand_All.triggered.connect(self.expand_all)
            self.actionCollapse_All.triggered.connect(self.collapse_all)
            self.actionSelect_All.triggered.connect(self.select_all)
            self.actionUnselect_All.triggered.connect(self.unselect_all)
            self.menuTitle_View.triggered.connect(self.change_title)
            self.menuLanguage.triggered.connect(self.change_language)
            self.combo_grouping.currentTextChanged.connect(self.regroup)
            self.combo_category.currentTextChanged.connect(self.switchboard)
            self.treeWidget.itemChanged.connect(self.tree_selection)
            self.treeWidget.doubleClicked.connect(self.double_clicked)
            self.button_export.clicked.connect(self.export_menu)
            self.button_import.clicked.connect(self.import_items)
            self.button_add.clicked.connect(self.add_items)
            self.button_delete.clicked.connect(self.delete_items)
            self.button_view.clicked.connect(self.data_viewer)

        def set_vars():
            self.total.setText('')
            self.int_total = 0
            self.modified = False
            self.title_format = settings.value('JWLManager/title','short')
            options = { 'code': 0, 'short': 1, 'full': 2 }
            self.titleChoices.actions()[options[self.title_format]].setChecked(True)
            self.save_filename = ''
            self.current_archive = settings.value('JWLManager/archive', '')
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

        self.setupUi(self)
        self.combo_category.setCurrentIndex(int(settings.value('JWLManager/category', 0)))
        self.combo_grouping.setCurrentText(_('Type'))
        self.viewer_pos = settings.value('Viewer/position', QPoint(50, 25))
        self.viewer_size = settings.value('Viewer/size', QSize(755, 500))
        self.help_pos = settings.value('Help/position', QPoint(50, 50))
        self.help_size = settings.value('Help/size', QSize(350, 400))
        self.setAcceptDrops(True)
        self.status_label = QLabel()
        self.statusBar.addPermanentWidget(self.status_label, 0)
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.sortByColumn(int(settings.value('JWLManager/sort', 1)), settings.value('JWLManager/direction', Qt.DescendingOrder))
        self.treeWidget.setColumnWidth(0, int(settings.value('JWLManager/column1', 500)))
        self.treeWidget.setColumnWidth(1, int(settings.value('JWLManager/column2', 30)))
        self.treeWidget.setExpandsOnDoubleClick(False)
        self.button_add.setVisible(False)
        self.resize(settings.value('Main_Window/size', QSize(680, 500)))
        self.move(settings.value('Main_Window/position', center()))
        self.viewer_window = QDialog(self)
        connect_signals()
        set_vars()
        self.about_window = AboutBox(APP, VERSION)
        self.help_window = HelpBox(_('Help'),self.help_size, self.help_pos)
        self.load_file(self.current_archive) if self.current_archive else self.new_file()


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
            self.load_file(file)
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
            elif header == r'{HIGHLIGHTS}':
                self.import_items(file, _('Highlights'))
            elif regex.search('{NOTES=', header):
                self.import_items(file, _('Notes'))
            else:
                QMessageBox.warning(self, _('Error'), _('File "{}" not recognized!').format(file), QMessageBox.Cancel)
        else:
            QMessageBox.warning(self, _('Error'), _('File "{}" not recognized!').format(file), QMessageBox.Cancel)


    def help_box(self):
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
        text.setText(f'{APP} {VERSION}\n{platform()}\n\n{tb_text}')
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


    def change_language(self):
        changed = False
        self.combo_grouping.blockSignals(True)
        for item in self.langChoices.actions():
            if item.isChecked() and (self.lang != item.toolTip()):
                app.removeTranslator(translator[self.lang])
                self.lang = item.toolTip()
                changed = True
        if not changed:
            return
        read_resources(self.lang)
        if self.lang not in translator.keys():
            translator[self.lang] = QTranslator()
            translator[self.lang].load(f'{project_path}/res/locales/UI/qt_{self.lang}.qm')
        app.installTranslator(translator[self.lang])
        app.processEvents()
        self.combo_grouping.blockSignals(False)

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

    def tree_selection(self):
        self.selected_items = len(self.list_selected())
        self.selected.setText(f'**{self.selected_items:,}**')
        self.button_delete.setEnabled(self.selected_items)
        self.button_view.setEnabled(self.selected_items and self.combo_category.currentText() in (_('Notes'), _('Annotations')))
        self.button_export.setEnabled(self.selected_items and self.combo_category.currentText() in (_('Notes'), _('Highlights'), _('Annotations'), _('Playlists'), _('Bookmarks')))

    def list_selected(self):
        selected = []
        it = QTreeWidgetItemIterator(self.treeWidget, QTreeWidgetItemIterator.Checked)
        for item in it:
            index = item.value()
            for i in self.leaves.get(index):
                selected.append(i)
        return selected


    def switchboard(self, selection):

        def disable_options(lst=[], add=False, exp=False, imp=False, view=False):
            self.button_add.setVisible(add)
            self.button_view.setVisible(view)
            self.button_export.setVisible(exp)
            self.button_import.setEnabled(imp)
            self.button_import.setVisible(imp)
            app.processEvents()
            for item in range(6):
                self.combo_grouping.model().item(item).setEnabled(True)
            for item in lst:
                self.combo_grouping.model().item(item).setEnabled(False)
                if self.combo_grouping.currentText() == self.combo_grouping.itemText(item):
                    self.combo_grouping.setCurrentText(_('Type'))

        self.combo_grouping.blockSignals(True)
        if selection == _('Notes'):
            self.combo_grouping.setCurrentText(_('Type'))
            disable_options([], False, True, True, True)
        elif selection == _('Highlights'):
            # self.combo_grouping.setCurrentText(_('Type'))
            disable_options([4], False, True, True, False)
        elif selection == _('Bookmarks'):
            disable_options([4,5], False, True, True, False)
        elif selection == _('Annotations'):
            disable_options([2,4,5], False, True, True, True)
        elif selection == _('Favorites'):
            disable_options([4,5], True, False, False, False)
        elif selection == _('Playlists'):
            self.combo_grouping.setCurrentText(_('Title'))
            disable_options([1,2,3,4,5], True, True, True, False)
        self.regroup()
        self.combo_grouping.blockSignals(False)

    def regroup(self, same_data=False, message=None):

        def get_data():
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

        def process_code(code, issue):
            if code == 'ws' and issue == 0: # Worldwide Security book - same code as simplified Watchtower
                code = 'ws-'
            elif not code:
                code = ''
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
                year = _('* YEAR UNCERTAIN *')
            return detail1, year, detail2


        def merge_df(df):
            df = pd.merge(df, publications, how='left', on=['Symbol'], sort=False)
            df['Full'] = df['Full'].fillna(df['Symbol'])
            df['Short'] = df['Short'].fillna(df['Symbol'])
            df['Type'] = df[['Type']].fillna(_('Other'))
            df['Year'] = df['Year_y'].fillna(df['Year_x']).fillna(_('* NO YEAR *'))
            df = df.drop(['Year_x', 'Year_y'], axis=1)
            df['Year'] = df['Year'].astype(str).str.replace('.0', '',regex=False)
            return df


        def get_annotations():
            lst = []
            for row in con.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, TextTag, l.BookNumber, l.ChapterNumber, l.Title FROM InputField JOIN Location l USING (LocationId);').fetchall():
                lng = lang_name.get(row[2], _('* NO LANGUAGE *'))
                code, year = process_code(row[1], row[3])
                detail1, year, detail2 = process_detail(row[1], row[5], row[6], row[3], year)
                item = row[0]
                rec = [ item, lng, code, year, detail1, detail2 ]
                lst.append(rec)
            annotations = pd.DataFrame(lst, columns=[ 'Id', 'Language', 'Symbol', 'Year', 'Detail1', 'Detail2' ])
            self.current_data = merge_df(annotations)

        def get_bookmarks():
            lst = []
            for row in con.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, BookmarkId, l.BookNumber, l.ChapterNumber, l.Title FROM Bookmark b JOIN Location l USING (LocationId);').fetchall():
                lng = lang_name.get(row[2], f'#{row[2]}')
                code, year = process_code(row[1], row[3])
                detail1, year, detail2 = process_detail(row[1], row[5], row[6], row[3], year)
                item = row[4]
                rec = [ item, lng, code or _('* OTHER *'), year, detail1, detail2 ]
                lst.append(rec)
            bookmarks = pd.DataFrame(lst, columns=[ 'Id', 'Language', 'Symbol', 'Year', 'Detail1', 'Detail2' ])
            self.current_data = merge_df(bookmarks)

        def get_favorites():
            lst = []
            for row in con.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, TagMapId FROM TagMap tm JOIN Location l USING (LocationId) WHERE tm.NoteId IS NULL ORDER BY tm.Position;').fetchall():
                lng = lang_name.get(row[2], f'#{row[2]}')
                code, year = process_code(row[1], row[3])
                detail1, year, detail2 = process_detail(row[1], None, None, row[3], year)
                item = row[4]
                rec = [ item, lng, code or _('* OTHER *'), year, detail1, detail2 ]
                lst.append(rec)
            favorites = pd.DataFrame(lst, columns=[ 'Id', 'Language', 'Symbol','Year', 'Detail1', 'Detail2' ])
            self.current_data = merge_df(favorites)

        def get_highlights():
            lst = []
            for row in con.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, b.BlockRangeId, u.UserMarkId, u.ColorIndex, l.BookNumber, l.ChapterNumber FROM UserMark u JOIN Location l USING (LocationId), BlockRange b USING (UserMarkId);').fetchall():
                lng = lang_name.get(row[2], f'#{row[2]}')
                code, year = process_code(row[1], row[3])
                detail1, year, detail2 = process_detail(row[1], row[7], row[8], row[3], year)
                col = process_color(row[6] or 0)
                item = row[4]
                rec = [ item, lng, code, col, year, detail1, detail2 ]
                lst.append(rec)
            highlights = pd.DataFrame(lst, columns=[ 'Id', 'Language', 'Symbol', 'Color', 'Year', 'Detail1', 'Detail2' ])
            self.current_data = merge_df(highlights)

        def get_notes():

            def load_independent():
                lst = []
                for row in con.execute("SELECT NoteId Id, ColorIndex Color, GROUP_CONCAT(Name, ' | ') Tags, substr(LastModified, 0, 11) Modified FROM (SELECT * FROM Note n LEFT JOIN TagMap tm USING (NoteId) LEFT JOIN Tag t USING (TagId) LEFT JOIN UserMark u USING (UserMarkId) ORDER BY t.Name) n WHERE n.BlockType = 0 AND LocationId IS NULL GROUP BY n.NoteId;").fetchall():
                    col = row[1] or 0
                    yr = row[3][0:4]
                    note = [ row[0], _('* NO LANGUAGE *'), _('* OTHER *'), process_color(col), row[2] or _('* NO TAG *'), row[3] or '', yr, None, _('* OTHER *'), _('* OTHER *'), _('* INDEPENDENT *') ]
                    lst.append(note)
                return pd.DataFrame(lst, columns=['Id', 'Language', 'Symbol', 'Color', 'Tags', 'Modified', 'Year', 'Detail1',  'Short', 'Full', 'Type'])

            lst = []
            for row in con.execute("SELECT NoteId Id, MepsLanguage Language, KeySymbol Symbol, IssueTagNumber Issue, BookNumber Book, ChapterNumber Chapter, ColorIndex Color, GROUP_CONCAT(Name, ' | ') Tags, substr(LastModified, 0, 11) Modified FROM (SELECT * FROM Note n JOIN Location l USING (LocationId) LEFT JOIN TagMap tm USING (NoteId) LEFT JOIN Tag t USING (TagId) LEFT JOIN UserMark u USING (UserMarkId) ORDER BY t.Name) n GROUP BY n.NoteId;").fetchall():
                lng = lang_name.get(row[1], f'#{row[1]}')

                code, year = process_code(row[2], row[3])
                detail1, year, detail2 = process_detail(row[2], row[4], row[5], row[3], year)
                col = process_color(row[6] or 0)
                note = [ row[0], lng, code or _('* OTHER *'), col, row[7] or _('* NO TAG *'), row[8] or '', year, detail1, detail2 ]
                lst.append(note)
            notes = pd.DataFrame(lst, columns=[ 'Id', 'Language', 'Symbol', 'Color', 'Tags', 'Modified', 'Year', 'Detail1', 'Detail2' ])
            notes = merge_df(notes)
            i_notes = load_independent()
            notes = pd.concat([i_notes, notes], axis=0, ignore_index=True)
            self.current_data = notes

        def get_playlists():
            lst = []
            for row in con.execute('SELECT PlaylistItemId, Name, Position, Label FROM PlaylistItem JOIN TagMap USING ( PlaylistItemId ) JOIN Tag t USING ( TagId ) WHERE t.Type = 2 ORDER BY Name, Position;').fetchall():
                rec = [ row[0], None, _('* OTHER *'), row[1], '', row[3] ]
                lst.append(rec)
            playlists = pd.DataFrame(lst, columns=['Id', 'Language', 'Symbol',  'Tags', 'Year', 'Detail1'])
            self.current_data = merge_df(playlists)


        def enable_options(enabled):
            self.button_import.setEnabled(enabled)
            self.combo_grouping.setEnabled(enabled)
            self.combo_category.setEnabled(enabled)
            self.actionReindex.setEnabled(enabled)
            self.actionObscure.setEnabled(enabled)
            self.actionSort.setEnabled(enabled)
            self.actionExpand_All.setEnabled(enabled)
            self.actionCollapse_All.setEnabled(enabled)
            self.actionSelect_All.setEnabled(enabled)
            self.actionUnselect_All.setEnabled(enabled)
            self.menuTitle_View.setEnabled(enabled)
            self.menuLanguage.setEnabled(enabled)

        def build_tree():

            def add_node(parent, label, data):
                child = QTreeWidgetItem(parent)
                child.setFlags(child.flags() | Qt.ItemIsAutoTristate | Qt.ItemIsUserCheckable)
                child.setCheckState(0, Qt.Unchecked)
                child.setText(0, str(label))
                child.setData(1, Qt.DisplayRole, data)
                child.setTextAlignment(1, Qt.AlignCenter)
                return child

            def traverse(df, idx, parent):
                if len(idx) > 0:
                    filter = idx[0]
                    for i, df in df.groupby(filter):
                        app.processEvents()
                        self.leaves[parent] = []
                        child = add_node(parent, i, df.shape[0])
                        self.leaves[child] = df['Id'].to_list()
                        traverse(df, idx[1:], child)

            def define_views(category):
                if category == _('Bookmarks'):
                    views = {
                        _('Type'): [ 'Type', 'Title', 'Language', 'Detail1' ],
                        _('Title'): [ 'Title', 'Language', 'Detail1', 'Detail2' ],
                        _('Language'): [ 'Language', 'Title', 'Detail1', 'Detail2' ],
                        _('Year'): [ 'Year', 'Title', 'Language', 'Detail1' ] }
                elif category == _('Favorites'):
                    views = {
                        _('Type'): [ 'Type', 'Title', 'Language' ],
                        _('Title'): [ 'Title', 'Language' ],
                        _('Language'): [ 'Language', 'Title' ],
                        _('Year'): [ 'Year', 'Title', 'Language' ] }
                elif category == _('Playlists'):
                    views = { _('Title'): [ 'Tags', 'Detail1' ], }
                elif category == _('Highlights'):
                    views = {
                        _('Type'): [ 'Type', 'Title', 'Language', 'Detail1' ],
                        _('Title'): [ 'Title', 'Language', 'Detail1', 'Detail2' ],
                        _('Language'): [ 'Language', 'Title', 'Detail1', 'Detail2' ],
                        _('Year'): [ 'Year', 'Title', 'Language', 'Detail1' ],
                        _('Color'): [ 'Color', 'Title', 'Language', 'Detail1' ] }
                elif category == _('Notes'):
                    views = {
                        _('Type'): [ 'Type', 'Title', 'Language', 'Detail1' ],
                        _('Title'): [ 'Title', 'Language', 'Detail1', 'Detail2' ],
                        _('Language'): [ 'Language', 'Title', 'Detail1', 'Detail2' ],
                        _('Year'): [ 'Year', 'Title', 'Language', 'Detail1' ],
                        _('Tag'): [ 'Tags', 'Title', 'Language', 'Detail1' ],
                        _('Color'): [ 'Color', 'Title', 'Language', 'Detail1' ] }
                elif category == _('Annotations'):
                    views = {
                        _('Type'): [ 'Type', 'Title', 'Detail1', 'Detail2' ],
                        _('Title'): [ 'Title', 'Detail1', 'Detail2' ],
                        _('Year'): [ 'Year', 'Title', 'Detail1', 'Detail2' ] }
                return views

            if self.title_format == 'code':
                title = 'Symbol'
            elif self.title_format == 'short':
                title = 'Short'
            else:
                title = 'Full'
            self.current_data['Title'] = self.current_data[title]
            views = define_views(category)
            self.int_total = self.current_data.shape[0]
            self.total.setText(f'**{self.int_total:,}**')
            filters = views[grouping]
            traverse(self.current_data, filters, self.treeWidget)


        if same_data is not True:
            same_data = False
        if message:
            msg = message + '… '
        else:
            msg = ' '
        self.statusBar.showMessage(msg+_('Processing…'))
        enable_options(False)
        app.processEvents()
        category = self.combo_category.currentText()
        grouping = self.combo_grouping.currentText()
        code_yr = regex.compile(r'(.*?[^\d-])(\d{2}$)')
        start = time()
        try:
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
            con.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF';")
            if not same_data:
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
        delta = 3500 - (time()-start) * 1000
        if message:
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
        # elif reply == QMessageBox.Cancel:
        #     return

    def new_file(self):
        if self.modified:
            self.check_save()
        self.status_label.setStyleSheet('color: black;')
        self.status_label.setText('* '+_('NEW ARCHIVE')+' *  ')
        self.modified = False
        self.save_filename = ''
        self.current_archive = ''
        global db_name
        try:
            for f in glob.glob(f'{tmp_path}/*', recursive=True):
                os.remove(f)
        except:
            pass
        db_name = 'userData.db'
        with ZipFile(project_path / 'res/blank','r') as zipped:
            zipped.extractall(tmp_path)
        m = {
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
        with open(f'{tmp_path}/manifest.json', 'w') as json_file:
                json.dump(m, json_file, indent=None, separators=(',', ':'))
        self.file_loaded()


    def load_file(self, archive = ''):
        if self.modified:
            self.check_save()
        if not archive:
            fname = QFileDialog.getOpenFileName(self, _('Open archive'), str(self.working_dir),_('JW Library archives')+' (*.jwlibrary)')
            if fname[0] == '':
                return
            archive = fname[0]
        self.current_archive = Path(archive)
        self.working_dir = Path(archive).parent
        self.status_label.setStyleSheet('color: black;')
        self.status_label.setText(f'{Path(archive).stem}  ')
        global db_name
        try:
            for f in glob.glob(f'{tmp_path}/*', recursive=True):
                os.remove(f)
        except:
            pass
        with ZipFile(archive,'r') as zipped:
            zipped.extractall(tmp_path)
        db_name = 'userData.db'
        self.file_loaded()

    def file_loaded(self):
        self.actionReindex.setEnabled(True)
        self.actionObscure.setEnabled(True)
        self.actionSort.setEnabled(True)
        self.combo_grouping.setEnabled(True)
        self.combo_category.setEnabled(True)
        self.actionSave.setEnabled(False)
        self.actionSave_As.setEnabled(True)
        self.actionCollapse_All.setEnabled(True)
        self.actionExpand_All.setEnabled(True)
        self.actionSelect_All.setEnabled(True)
        self.actionUnselect_All.setEnabled(True)
        self.menuTitle_View.setEnabled(True)
        self.total.setText('**0**')
        self.selected.setText('**0**')
        try:
            self.viewer_window.close()
        except:
            pass
        self.switchboard(self.combo_category.currentText())


    def save_file(self):
        if self.save_filename == '':
            return self.save_as_file()
        else:
            self.zip_file()

    def save_as_file(self):
        fname = ()
        if self.save_filename == '':
            now = datetime.now().strftime('%Y-%m-%d')
            fname = QFileDialog.getSaveFileName(self, _('Save archive'), f'{self.working_dir}/MODIFIED_{now}.jwlibrary', _('JW Library archives')+'(*.jwlibrary)')
        else:
            fname = QFileDialog.getSaveFileName(self, _('Save archive'), self.save_filename, _('JW Library archives')+'(*.jwlibrary)')
        if fname[0] == '':
            self.statusBar.showMessage(' '+_('NOT saved!'), 3500)
            return False
        elif Path(fname[0]) == self.current_archive:
            reply = QMessageBox.critical(self, _('Save'), _("It's recommended to save under another name.\nAre you absolutely sure you want to replace the original?"),
              QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return self.save_file()
        self.save_filename = fname[0]
        self.working_dir = Path(fname[0]).parent
        self.status_label.setText(f'{Path(fname[0]).stem}  ')
        self.zip_file()

    def zip_file(self):

        def update_manifest():
            with open(f'{tmp_path}/manifest.json', 'r') as json_file:
                m = json.load(json_file)
            m['name'] = APP
            m['creationDate'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            m['userDataBackup']['deviceName'] = f'{APP}_{VERSION}'
            m['userDataBackup']['lastModifiedDate'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            sha256hash = FileHash('sha256')
            m['userDataBackup']['hash'] = sha256hash.hash_file(f'{tmp_path}/{db_name}')
            m['userDataBackup']['databaseName'] = db_name
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
            con.execute('UPDATE LastModified SET LastModified = ?;', (m['userDataBackup']['lastModifiedDate'],))
            con.commit()
            con.close()
            with open(f'{tmp_path}/manifest.json', 'w') as json_file:
                json.dump(m, json_file, indent=None, separators=(',', ':'))

        update_manifest()
        with ZipFile(self.save_filename, 'w', compression=ZIP_DEFLATED) as newzip:
            files = os.listdir(tmp_path)
            for f in files:
                newzip.write(f'{tmp_path}/{f}', f)
        self.archive_saved()


    def archive_modified(self):
        self.modified = True
        self.actionSave.setEnabled(True)
        self.actionSave_As.setEnabled(True)
        self.status_label.setStyleSheet('font: italic;')

    def archive_saved(self):
        self.modified = False
        self.actionSave.setEnabled(False)
        self.status_label.setStyleSheet('font: normal;')
        self.statusBar.showMessage(' '+_('Saved'), 3500)


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

    def export_items(self, form):

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

        def shorten_title(t):
            if t == '':
                return _('UNTITLED')
            t = regex.sub(r'[^-\w\s\(\):,;]+', '', t) # strip off punctuation
            t = t.strip()
            if len(t) > 40:
                m = regex.search(r'^(.{0,18}\w)\W', t)
                if not m:
                    return t[0:40]
                left = m.group(1)
                l = 33 - len(left)
                m = regex.search(f'\s(\w.{{0,{l}}})$', t)
                right = m.group(1)
                t = left + ' […] ' + right
            return t

        def unique_filename(f):
            if not os.path.exists(f):
                return f
            base, ext = os.path.splitext(f)
            c = 1
            while os.path.exists(f):
                f = f"{base}~{c}{ext}"
                c += 1
            return f

        def export_file(category, form):
            now = datetime.now().strftime('%Y-%m-%d')
            if category == _('Highlights') or category == _('Bookmarks'):
                return QFileDialog.getSaveFileName(self, _('Export file'), f'{self.working_dir}/JWL_{category}_{now}.txt', _('Text files')+' (*.txt)')[0]
            elif category == _('Playlists'):
                return QFileDialog.getSaveFileName(self, _('Export file'), f'{self.working_dir}/JWL_{category}_{now}.jwlplaylist', _('JW Library playlists')+' (*.jwlplaylist)')[0]
            else:
                if form == 'xlsx': 
                    return QFileDialog.getSaveFileName(self, _('Export file'), f'{self.working_dir}/JWL_{category}_{now}.xlsx', _('MS Excel files')+' (*.xlsx)')[0]
                elif form == 'txt':
                    return QFileDialog.getSaveFileName(self, _('Export file'), f'{self.working_dir}/JWL_{category}_{now}.txt', _('Text files')+' (*.txt)')[0]
                else:
                    return QFileDialog.getExistingDirectory(self, _('Export directory'), f'{self.working_dir}/', QFileDialog.ShowDirsOnly)

        def create_xlsx(fields):
            last_field = fields[-1]
            wb = Workbook(fname)
            wb.set_properties({'comments': _('Exported from')+f' {current_archive} '+_('by')+f' {APP} ({VERSION})\n'+_('on')+f" {datetime.now().strftime('%Y-%m-%d @ %H:%M:%S')}"})
            bold = wb.add_format({'bold': True})
            ws = wb.add_worksheet(APP)
            ws.write_row(row=0, col=0, cell_format=bold, data=fields)
            ws.autofilter(first_row=0, last_row=99999, first_col=0, last_col=len(fields)-1)
            for index, item in enumerate(item_list):
                row = map(lambda field_id: item.get(field_id, ''), fields)
                ws.write_row(row=index+1, col=0, data=row)
                ws.write_string(row=index+1, col=len(fields)-1, string=item_list[index][last_field]) # overwrite any that may have been formatted as URLs
            ws.freeze_panes(1, 0)
            ws.set_column(0, 2, 20)
            ws.set_column(3, len(fields)-1, 12)
            wb.close()

        def export_header(category):
            # Note: invisible char on first line to force UTF-8 encoding
            return category + '\n \n' + _('Exported from') + f' {current_archive}\n' + _('by') + f' {APP} ({VERSION}) ' + _('on') + f" {datetime.now().strftime('%Y-%m-%d @ %H:%M:%S')}\n" + '*'*76

        def export_annotations(fname):

            def get_annotations():
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
                    WHERE LocationId IN {items}
                    ORDER BY doc, i;
                    '''
                for row in con.execute(sql).fetchall():
                    item = {
                        'LABEL': row[0],
                        'VALUE': row[1].rstrip() if row[1] else '* '+_('NO TEXT')+' *',
                        'DOC': row[2],
                        'PUB': row[4]
                    }
                    if row[3] > 10000000:
                        item['ISSUE'] = row[3]
                    else:
                        item['ISSUE'] = None
                    item_list.append(item)

            get_annotations()
            if form == 'xlsx':
                fields = ['PUB', 'ISSUE', 'DOC', 'LABEL', 'VALUE']
                create_xlsx(fields)
            elif form == 'txt':
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(export_header('{ANNOTATIONS}'))
                    for item in item_list:
                        iss = '{ISSUE='+str(item['ISSUE'])+'}' if item['ISSUE'] else ''
                        txt = '\n==={PUB='+item['PUB']+'}'+iss+'{DOC='+str(item['DOC'])+'}{LABEL='+item['LABEL']+'}===\n'+item['VALUE']
                        f.write(txt)
                    f.write('\n==={END}===')
            else: # 'md'
                for item in item_list:
                    iss = ''
                    pub = item['PUB']
                    fname = f'{self.working_dir}/{pub}/'
                    if item.get('ISSUE'):
                        iss = process_issue(item['ISSUE'])
                        fname += f"{iss}/"
                    fname += f"{item['DOC']}/"
                    fname += item['LABEL'] + '.md'
                    Path(fname).parent.mkdir(parents=True, exist_ok=True)
                    txt = f"---\npublication: {pub} {iss}".strip()
                    txt += f"\ndocument: {item['DOC']}\nlabel: {item['LABEL']}\n---\n{item['VALUE'].strip()}\n"
                    with open(fname, 'w', encoding='utf-8') as f:
                        f.write(txt)

        def export_bookmarks(fname):
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(export_header('{BOOKMARKS}'))
                for row in con.execute(f'SELECT l.BookNumber, l.ChapterNumber, l.DocumentId, l.IssueTagNumber, l.KeySymbol, l.MepsLanguage, l.Type, Slot, b.Title, Snippet, BlockType, BlockIdentifier FROM Bookmark b LEFT JOIN Location l USING (LocationId) WHERE BookmarkId IN {items};').fetchall():
                    f.write(f'\n{row[0]}')
                    for item in range(1,12):
                        f.write(f'|{row[item]}')
                    item_list.append(None)

        def export_highlights(fname):
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(export_header('{HIGHLIGHTS}'))
                for row in con.execute(f'SELECT b.BlockType, b.Identifier, b.StartToken, b.EndToken, u.ColorIndex, u.Version, l.BookNumber, l.ChapterNumber, l.DocumentId, l.IssueTagNumber, l.KeySymbol, l.MepsLanguage, l.Type FROM UserMark u JOIN Location l USING (LocationId), BlockRange b USING (UserMarkId) WHERE BlockRangeId IN {items};').fetchall():
                    f.write(f'\n{row[0]}')
                    for item in range(1,13):
                        f.write(f',{row[item]}')
                    item_list.append(None)

        def export_notes(fname):

            def get_notes():
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
                        b.StartToken,
                        b.EndToken,
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
                        'NOTE': row[2].rstrip() if row[2] else '',
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
                        'GUID': row[17]
                    }
                    if row[15]:
                        item['RANGE'] = f'{row[15]}-{row[16]}'
                    else:
                        item['RANGE'] = None
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
                            if item.get('VS'):
                                vs = str(item['VS']).zfill(3)
                                item['BLOCK'] = None
                            else:
                                vs = '000'
                            item['Reference'] = str(item['BK']).zfill(2) + str(item['CH']).zfill(3) + vs
                            item['Link'] = f"https://www.jw.org/finder?wtlocale={item['LANG']}&pub={item['PUB']}&bible={item['Reference']}"
                            if not item.get('HEADING'):
                                item['HEADING'] = f"{bible_books[item['BK']]} {item['CH']}"
                            elif item.get('VS') and (':' not in item['HEADING']):
                                item['HEADING'] += f":{item['VS']}"
                        else: # publication note
                            item['VS'] = None
                            par = f"&par={item['BLOCK']}" if item.get('BLOCK') else ''
                            item['Link'] = f"https://www.jw.org/finder?wtlocale={item['LANG']}&docid={item['DOC']}{par}"
                    item_list.append(item)

            get_notes()
            if form == 'xlsx':
                fields = ['CREATED', 'MODIFIED', 'TAGS', 'COLOR', 'RANGE', 'LANG', 'PUB', 'BK', 'CH', 'VS', 'Reference', 'ISSUE', 'DOC', 'BLOCK', 'HEADING', 'Link', 'TITLE', 'NOTE']
                create_xlsx(fields)
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
                            if item.get('VS'):
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
                for item in item_list:
                    iss = ''
                    if item.get('PUB'):
                        pub = f"{item['PUB']}-{lang_symbol[item['LANG']]}"
                    else:
                        pub = None
                    fname = f'{self.working_dir}/'
                    if item['TYPE'] == 0 and not (item.get('BK') or item.get('DOC')):
                        fname += _('* INDEPENDENT *').strip('* ') + '/'
                    elif item.get('BK'):
                        fname += f"{pub}/{str(item['BK']).zfill(2)}_{bible_books[item['BK']]}/{str(item['CH']).zfill(3)}/"
                        if item.get('VS'):
                            fname += str(item['VS']).zfill(3) + '_'
                    else:
                        fname += f"{pub}/"
                        if item.get('ISSUE'):
                            iss = process_issue(item['ISSUE'])
                            fname += f"{iss}/"
                        fname += f"{item['DOC']}/"
                        if item.get('BLOCK'):
                            fname += str(item['BLOCK']).zfill(3) + '_'
                    fname += shorten_title(item['TITLE']) + '_' + item['GUID'][:8] + '.md'
                    fname = unique_filename(fname)
                    Path(fname).parent.mkdir(parents=True, exist_ok=True)

                    txt = f"---\ntitle: {item['TITLE']}\n"
                    txt += f"date: {item['MODIFIED'][:10]}\n"
                    if pub:
                        txt += f"publication: {pub} {iss}".strip() + '\n'
                    if item.get('HEADING'):
                        txt += f"document: {item['HEADING']}\n"
                    if item.get('Link'):
                        txt += f"link: {item['Link']}\n"
                    txt += f"color: {item['COLOR']}\n"
                    if item.get('TAGS'):
                        txt += 'tags:\n'
                        for t in item['TAGS'].split(' | '):
                            txt += f'  - {t}\n'
                    txt += f"guid: {item['GUID']}"
                    txt += f"\n---\n# {item['TITLE']}\n\n{item['NOTE'].strip()}\n"
                    with open(fname, 'x', encoding='utf-8') as f:
                        f.write(txt)


        def export_playlist(fname):

            def playlist_export():
                expcon.execute('INSERT INTO Tag VALUES (?, ?, ?);', (1, 2, Path(fname).stem))

                rows = con.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="android_metadata";').fetchone()
                if rows:
                    lc = con.execute('SELECT locale FROM android_metadata;').fetchone()
                    expcon.execute('UPDATE android_metadata SET locale = ?;', (lc[0],))

                rows = con.execute(f'SELECT * FROM PlaylistItem WHERE PlaylistItemId IN {items};').fetchall()
                expcon.executemany('INSERT INTO PlaylistItem VALUES (?, ?, ?, ?, ?, ?, ?);', rows)
                for row in rows:
                    item_list.append(row)

                rows = con.execute(f'SELECT * FROM PlaylistItemLocationMap WHERE PlaylistItemId IN {items};').fetchall()
                expcon.executemany('INSERT INTO PlaylistItemLocationMap VALUES (?, ?, ?, ?);', rows)

                rows = con.execute(f'SELECT * FROM PlaylistItemMarker WHERE PlaylistItemId IN {items};').fetchall()
                expcon.executemany('INSERT INTO PlaylistItemMarker VALUES (?, ?, ?, ?, ?, ?);', rows)

                rows = expcon.execute(f'SELECT PlaylistItemMarkerId FROM PlaylistItemMarker;').fetchall()
                pm = '(' + str([row[0] for row in rows]).strip('][') + ')'

                rows = con.execute(f'SELECT * FROM PlaylistItemMarkerBibleVerseMap WHERE PlaylistItemMarkerId IN {pm};').fetchall()
                expcon.executemany('INSERT INTO PlaylistItemMarkerBibleVerseMap VALUES (?, ?);', rows)

                rows = con.execute(f'SELECT * FROM PlaylistItemMarkerParagraphMap WHERE PlaylistItemMarkerId IN {pm};').fetchall()
                expcon.executemany('INSERT INTO PlaylistItemMarkerParagraphMap VALUES (?, ?, ?, ?);', rows)

                rows = con.execute(f'SELECT PlaylistItemId FROM TagMap WHERE PlaylistItemId IN {items} ORDER BY TagId, Position;').fetchall()
                pos = 0
                for row in rows:
                    expcon.execute('INSERT INTO TagMap (PlaylistItemId, TagId, Position) VALUES (?, ?, ?);', (row[0], 1, pos))
                    pos += 1

                rows = con.execute(f'SELECT * FROM PlaylistItemIndependentMediaMap WHERE PlaylistItemId IN {items};').fetchall()
                expcon.executemany('INSERT INTO PlaylistItemIndependentMediaMap VALUES (?, ?, ?);', rows)

                rows = con.execute(f'SELECT * FROM PlaylistItemAccuracy;').fetchall()
                expcon.executemany('INSERT INTO PlaylistItemAccuracy VALUES (?, ?);', rows)

                rows = expcon.execute(f'SELECT ThumbnailFilePath FROM PlaylistItem WHERE ThumbnailFilePath IS NOT NULL;').fetchall()
                fp = '(' + str([row[0] for row in rows]).strip('][') + ')'

                rows = expcon.execute(f'SELECT IndependentMediaId FROM PlaylistItemIndependentMediaMap;').fetchall()
                mi = '(' + str([row[0] for row in rows]).strip('][') + ')'
                rows = con.execute(f'SELECT * FROM IndependentMedia WHERE FilePath IN {fp} OR IndependentMediaId IN {mi};').fetchall()
                expcon.executemany('INSERT INTO IndependentMedia VALUES (?, ?, ?, ?, ?);', rows)
                for f in rows:
                    shutil.copy2(tmp_path+'/'+f[2], playlist_path+'/'+f[2])

                rows = expcon.execute(f'SELECT LocationId FROM PlaylistItemLocationMap;').fetchall()
                lo = '('
                for row in rows:
                    lo += f'{row[0]}, '
                lo = lo.rstrip(', ') + ')'
                rows = con.execute(f'SELECT * FROM Location WHERE LocationId IN {lo};').fetchall()
                expcon.executemany('INSERT INTO Location VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);', rows)

            playlist_path = mkdtemp(prefix='JWLPlaylist_')
            with ZipFile(project_path / 'res/blank_playlist','r') as zipped:
                zipped.extractall(playlist_path)
            expcon = sqlite3.connect(f'{playlist_path}/userData.db')
            expcon.executescript('PRAGMA temp_store = 2; PRAGMA journal_mode = "OFF"; PRAGMA foreign_keys = "OFF";')
            playlist_export()
            self.reindex_db(expcon, playlist_path)
            expcon.execute('INSERT INTO LastModified VALUES (?);', (datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),))
            expcon.executescript('PRAGMA foreign_keys = "ON"; VACUUM;')
            expcon.commit()
            expcon.close()
            sha256hash = FileHash('sha256')
            m = {
                'name': APP,
                'creationDate': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'version': 1,
                'type': 1,
                'userDataBackup': {
                    'lastModifiedDate': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'deviceName': f'{APP}_{VERSION}',
                    'databaseName': 'userData.db',
                    'hash': sha256hash.hash_file(f'{playlist_path}/userData.db'),
                    'schemaVersion': 14 } }
            with open(f'{playlist_path}/manifest.json', 'w') as json_file:
                    json.dump(m, json_file, indent=None, separators=(',', ':'))
            with ZipFile(fname, 'w', compression=ZIP_DEFLATED) as newzip:
                files = os.listdir(playlist_path)
                for f in files:
                    newzip.write(f'{playlist_path}/{f}', f)
            shutil.rmtree(playlist_path, ignore_errors=True)

        category = self.combo_category.currentText()
        fname = export_file(category, form)
        if fname == '':
            self.statusBar.showMessage(' '+_('NOT exported!'), 3500)
            return
        if form == 'md':
            self.working_dir = Path(fname)
        else:
            self.working_dir = Path(fname).parent
        current_archive = self.current_archive.name if self.current_archive else _('NEW ARCHIVE')
        item_list = []
        try:
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
            items = str(self.list_selected()).replace('[', '(').replace(']', ')')
            if category == _('Highlights'):
                export_highlights(fname)
            elif category == _('Notes'):
                export_notes(fname)
            elif category == _('Annotations'):
                export_annotations(fname)
            elif category == _('Bookmarks'):
                export_bookmarks(fname)
            elif category == _('Playlists'):
                export_playlist(fname)
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        self.statusBar.showMessage(f' {len(item_list)} ' +_('items exported'), 3500)

    def import_items(self, file='', category = ''):

        def import_annotations():

            def pre_import():
                line = import_file.readline()
                if regex.search('{ANNOTATIONS}', line):
                    return True
                else:
                    QMessageBox.critical(None, _('Error!'), _('Wrong import file format:\nMissing {ANNOTATIONS} tag line'), QMessageBox.Abort)
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
                        QMessageBox.critical(None, _('Error!'), _('Error on import!\n\nFaulting entry')+f' (#{count}):\n{header}', QMessageBox.Abort)
                        con.execute('ROLLBACK;')
                        return 0
                df = pd.DataFrame(items, columns=['PUB', 'ISSUE', 'DOC', 'LABEL', 'VALUE'])
                return df

            def update_db(df):

                def add_location(attribs):
                    con.execute(f'INSERT INTO Location (DocumentId, IssueTagNumber, KeySymbol, MepsLanguage, Type) SELECT ?, ?, ?, NULL, 0 WHERE NOT EXISTS (SELECT 1 FROM Location WHERE DocumentId = ? AND IssueTagNumber = ? AND KeySymbol = ? AND MepsLanguage IS NULL AND Type = 0);', (attribs['DOC'], attribs['ISSUE'], attribs['PUB'], attribs['DOC'], attribs['ISSUE'], attribs['PUB']))
                    result = con.execute(f'SELECT LocationId FROM Location WHERE DocumentId = ? AND IssueTagNumber = ? AND KeySymbol = ? AND MepsLanguage IS NULL AND Type = 0;', (attribs['DOC'], attribs['ISSUE'], attribs['PUB'])).fetchone()
                    return result[0]

                df.fillna({'ISSUE': 0}, inplace=True)
                df.fillna({'VALUE': ''}, inplace=True)
                count = 0
                for i, row in df.iterrows():
                    try:
                        count += 1
                        location_id = add_location(row)
                        if con.execute(f'SELECT * FROM InputField WHERE LocationId = ? AND TextTag = ?;', (location_id, row['LABEL'])).fetchone():
                            con.execute(f'UPDATE InputField SET Value = ? WHERE LocationId = ? AND TextTag = ?;', (row['VALUE'], location_id, row['LABEL']))
                        else:
                            con.execute(f'INSERT INTO InputField (LocationId, TextTag, Value) VALUES (?, ?, ?);', (location_id,row['LABEL'], row['VALUE']))
                    except:
                        QMessageBox.critical(None, _('Error!'), _('Error on import!\n\nFaulting entry')+f': #{count}', QMessageBox.Abort)
                        con.execute('ROLLBACK;')
                        return 0
                return count

            if Path(file).suffix == '.txt':
                with open(file, 'r', encoding='utf-8', errors='namereplace') as import_file:
                    if pre_import():
                        df = read_text()
                        count = update_db(df)
                    else:
                        count = 0
            else:
                df = pd.read_excel(file)
                count = update_db(df)
            return count

        def import_bookmarks():

            def pre_import():
                line = import_file.readline()
                if regex.search('{BOOKMARKS}', line):
                    return True
                else:
                    QMessageBox.critical(None, _('Error!'), _('Wrong import file format:\nMissing {BOOKMARKS} tag line'), QMessageBox.Abort)
                    return False

            def update_db():

                def add_scripture_location(attribs):
                    con.execute('INSERT INTO Location (KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Type) SELECT ?, ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ?);', (attribs[4], attribs[5], attribs[0], attribs[1], attribs[6], attribs[4], attribs[5], attribs[0], attribs[1]))
                    result = con.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ?;', (attribs[4], attribs[5], attribs[0], attribs[1])).fetchone()
                    return result[0]

                def add_publication_location(attribs):
                    con.execute('INSERT INTO Location (IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Type) SELECT ?, ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = ?);', (attribs[3], attribs[4], attribs[5], attribs[2], attribs[6], attribs[4], attribs[5], attribs[3], attribs[2], attribs[6]))
                    result = con.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = ?;', (attribs[4], attribs[5], attribs[3], attribs[2], attribs[6])).fetchone()
                    return result[0]

                def add_bookmark(attribs, location_id):
                    con.execute('INSERT INTO Location (KeySymbol, MepsLanguage,Type) SELECT ?, ?, 1 WHERE NOT EXISTS (SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber IS NULL AND DocumentId IS NULL);', (attribs[4], attribs[5], attribs[4], attribs[5]))
                    publication_id = con.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber IS NULL AND DocumentID IS NULL;', (attribs[4], attribs[5])).fetchone()[0]
                    try:
                        con.execute(f'INSERT INTO Bookmark (LocationId, PublicationLocationId, Slot, Title, Snippet, BlockType, BlockIdentifier) VALUES (?, ?, ?, ?, ?, ?, ?);', (location_id, publication_id, attribs[7], attribs[8], attribs[9], attribs[10], attribs[11]))
                    except:
                        con.execute(f"UPDATE Bookmark SET LocationId = ?, Title = ?, Snippet = ?, BlockType = ?, BlockIdentifier = ? WHERE PublicationLocationId = ? AND Slot = ?;", (location_id, attribs[8], attribs[9], attribs[10], attribs[11], publication_id, attribs[7]))

                count = 0
                for line in import_file:
                    if '|' in line:
                        try:
                            count += 1
                            attribs = regex.split('\|', line.rstrip())
                            for i in [0,1,2,9,11]:
                                if attribs[i] == 'None':
                                    attribs[i] = None
                            if attribs[0]:
                                location_id = add_scripture_location(attribs)
                            else:
                                location_id = add_publication_location(attribs)
                            add_bookmark(attribs, location_id)
                        except:
                            QMessageBox.critical(None, _('Error!'), _('Error on import!\n\nFaulting entry')+f' (#{count}):\n{line}', QMessageBox.Abort)
                            con.execute('ROLLBACK;')
                            return 0
                return count

            with open(file, 'r') as import_file:
                if pre_import():
                    count = update_db()
                else:
                    count = 0
            return count

        def import_highlights():

            def pre_import():
                line = import_file.readline()
                if regex.search('{HIGHLIGHTS}', line):
                    return True
                else:
                    QMessageBox.critical(None, _('Error!'), _('Wrong import file format:\nMissing {HIGHLIGHTS} tag line'), QMessageBox.Abort)
                    return False

            def update_db():

                def add_scripture_location(attribs):
                    con.execute('INSERT INTO Location (KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Type) SELECT ?, ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ?);', (attribs[10], attribs[11], attribs[6], attribs[7], attribs[12], attribs[10], attribs[11], attribs[6], attribs[7]))
                    result = con.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ?;', (attribs[10], attribs[11], attribs[6], attribs[7])).fetchone()
                    return result[0]

                def add_publication_location(attribs):
                    con.execute('INSERT INTO Location (IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Type) SELECT ?, ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = ?);', (attribs[9], attribs[10], attribs[11], attribs[8], attribs[12], attribs[10], attribs[11], attribs[9], attribs[8], attribs[12]))
                    result = con.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = ?;', (attribs[10], attribs[11], attribs[9], attribs[8], attribs[12])).fetchone()
                    return result[0]

                def add_usermark(attribs, location_id):
                    unique_id = uuid.uuid1()
                    con.execute(f"INSERT INTO UserMark (ColorIndex, LocationId, StyleIndex, UserMarkGuid, Version) VALUES (?, ?, 0, '{unique_id}', ?);", (attribs[4], location_id, attribs[5]))
                    usermark_id = con.execute(f"SELECT UserMarkId FROM UserMark WHERE UserMarkGuid = '{unique_id}';").fetchone()[0]
                    result = con.execute(f'SELECT * FROM BlockRange JOIN UserMark USING (UserMarkId) WHERE Identifier = {attribs[1]} AND LocationId = {location_id};')
                    ns = int(attribs[2])
                    ne = int(attribs[3])
                    blocks = []
                    for row in result.fetchall():
                        cs = row[3]
                        ce = row[4]
                        if ce >= ns and ne >= cs:
                            ns = min(cs, ns)
                            ne = max(ce, ne)
                            blocks.append(row[0])
                    block = str(blocks).replace('[', '(').replace(']', ')')
                    con.execute(f'DELETE FROM BlockRange WHERE BlockRangeId IN {block};')
                    con.execute(f'INSERT INTO BlockRange (BlockType, Identifier, StartToken, EndToken, UserMarkId) VALUES (?, ?, ?, ?, ?);', (attribs[0], attribs[1], ns, ne, usermark_id))

                count = 0
                for line in import_file:
                    if regex.match(r'^(\d+,){6}', line):
                        try:
                            count += 1
                            attribs = regex.split(',', line.rstrip().replace('None', ''))
                            if attribs[6]:
                                location_id = add_scripture_location(attribs)
                            else:
                                location_id = add_publication_location(attribs)
                            add_usermark(attribs, location_id)
                        except:
                            QMessageBox.critical(None, _('Error!'), _('Error on import!\n\nFaulting entry')+f' (#{count}):\n{line}', QMessageBox.Abort)
                            con.execute('ROLLBACK;')
                            return 0
                return count

            with open(file, 'r') as import_file:
                if pre_import():
                    count = update_db()
                else:
                    count = 0
            return count

        def import_notes():

            def pre_import():

                def delete_notes(title_char):
                    results = len(con.execute(f"SELECT NoteId FROM Note WHERE Title GLOB '{title_char}*';").fetchall())
                    if results < 1:
                        return
                    answer = QMessageBox.warning(None, _('Warning'), f'{results} '+_('notes starting with')+f' "{title_char}" '+_('WILL BE DELETED before importing.\n\nProceed with deletion? (NO to skip)'), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                    if answer == QMessageBox.Yes:
                        con.execute(f"DELETE FROM Note WHERE Title GLOB '{title_char}*';")

                line = import_file.readline()
                m = regex.search('{NOTES=(.?)}', line)
                if m:
                    if m.group(1) != '':
                        delete_notes(m.group(1))
                    return True
                else:
                    QMessageBox.critical(None, _('Error!'), _('Wrong import file format:\nMissing or malformed {NOTES=} attribute line'), QMessageBox.Abort)
                    return False

            def read_text():

                def process_header(line):
                    attribs = {}
                    for (key, value) in regex.findall('{(.*?)=(.*?)}', line):
                        attribs[key] = value
                    attribs['HEADING'] = attribs.get('HEADING') or None
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
                            note = item.group(2).strip().split('\n')
                        else:
                            note = ['', '']
                        attribs['TITLE'] = note[0]
                        attribs['NOTE'] = '\n'.join(note[1:])
                        items.append(attribs)
                    except:
                        QMessageBox.critical(None, _('Error!'), _('Error on import!\n\nFaulting entry')+f' (#{count}):\n{header}', QMessageBox.Abort)
                        con.execute('ROLLBACK;')
                        return 0
                df = pd.DataFrame(items, columns=['CREATED', 'MODIFIED', 'TAGS', 'COLOR', 'RANGE', 'LANG', 'PUB', 'BK', 'CH', 'VS', 'ISSUE', 'DOC', 'BLOCK', 'HEADING', 'TITLE', 'NOTE'])
                return df

            def update_db(df):

                def add_scripture_location(attribs):
                    con.execute('INSERT INTO Location (KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Title, Type) SELECT ?, ?, ?, ?, ?, 0 WHERE NOT EXISTS (SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ?);', (attribs['PUB'], attribs['LANG'], attribs['BK'], attribs['CH'], attribs['HEADING'], attribs['PUB'], attribs['LANG'], attribs['BK'], attribs['CH']))
                    result = con.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ?;', (attribs['PUB'], attribs['LANG'], attribs['BK'], attribs['CH'])).fetchone()[0]
                    if attribs['HEADING']:
                        con.execute('UPDATE Location SET Title = ? WHERE LocationId = ?;', (attribs['HEADING'], result))
                    return result

                def add_publication_location(attribs):
                    con.execute('INSERT INTO Location (IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Title, Type) SELECT ?, ?, ?, ?, ?, 0 WHERE NOT EXISTS (SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = 0);', (attribs['ISSUE'], attribs['PUB'], attribs['LANG'], attribs['DOC'], attribs['HEADING'], attribs['PUB'], attribs['LANG'], attribs['ISSUE'], attribs['DOC']))
                    result = con.execute('SELECT LocationId from Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = 0;', (attribs['PUB'], attribs['LANG'], attribs['ISSUE'], attribs['DOC'])).fetchone()
                    return result[0]

                def add_usermark(attribs, location_id):
                    if int(attribs['COLOR']) == 0:
                        return None
                    if pd.notna(attribs['VS']):
                        block_type = 2
                        identifier = attribs['VS']
                    else:
                        block_type = 1
                        identifier = attribs['BLOCK']
                    if pd.notna(attribs['RANGE']):
                        ns, ne = str(attribs['RANGE']).split('-')
                        fields = f' AND StartToken = {int(ns)} AND EndToken = {int(ne)}'
                    else:
                        fields = ''
                    result = con.execute(f"SELECT UserMarkId FROM UserMark JOIN BlockRange USING (UserMarkId) WHERE ColorIndex = ? AND LocationId = ? AND Identifier = ? {fields};", (attribs['COLOR'], location_id, identifier)).fetchone()
                    if result:
                        usermark_id = result[0]
                    else:
                        unique_id = uuid.uuid1()
                        con.execute(f"INSERT INTO UserMark (ColorIndex, LocationId, StyleIndex, UserMarkGuid, Version) VALUES (?, ?, 0, '{unique_id}', 1);", (attribs['COLOR'], location_id))
                        usermark_id = con.execute(f"SELECT UserMarkId FROM UserMark WHERE UserMarkGuid = '{unique_id}';").fetchone()[0]
                    try:
                        con.execute(f'INSERT INTO BlockRange (BlockType, Identifier, StartToken, EndToken, UserMarkId) VALUES (?, ?, ?, ?, ?);', (block_type, identifier, ns, ne, usermark_id))
                    except:
                        pass
                    return usermark_id

                def update_note(attribs, location_id, block_type, usermark_id):

                    def process_tags(note_id, tags):
                        con.execute(f'DELETE FROM TagMap WHERE NoteId = {note_id};')
                        for tag in str(tags).split('|'):
                            tag = tag.strip()
                            if not tag:
                                continue
                            con.execute('INSERT INTO Tag (Type, Name) SELECT 1, ? WHERE NOT EXISTS (SELECT 1 FROM Tag WHERE Name = ?);', (tag, tag))
                            tag_id = con.execute('SELECT TagId from Tag WHERE Name = ?;', (tag,)).fetchone()[0]
                            position = con.execute(f'SELECT ifnull(max(Position), -1) FROM TagMap WHERE TagId = {tag_id};').fetchone()[0] + 1
                            con.execute('INSERT Into TagMap (NoteId, TagId, Position) VALUES (?, ?, ?);', (note_id, tag_id, position))

                    if location_id:
                        result = con.execute('SELECT Guid, LastModified, Created FROM Note WHERE LocationId = ? AND Title = ? AND BlockIdentifier = ? AND BlockType = ?;', (location_id, attribs['TITLE'], attribs['BLOCK'], block_type)).fetchone()
                    else:
                        result = con.execute('SELECT Guid, LastModified, Created FROM Note WHERE Title = ? AND BlockType = 0;', (attribs['TITLE'],)).fetchone()
                    if result:
                        unique_id = result[0]
                        modified = attribs['MODIFIED'] if pd.notnull(attribs['MODIFIED']) else result[1]
                        created = attribs['CREATED'] if pd.notnull(attribs['CREATED']) else result[2]
                        con.execute(f"UPDATE Note SET UserMarkId = ?, Content = ?, LastModified = ?, Created = ? WHERE Guid = '{unique_id}';", (usermark_id, attribs['NOTE'], modified, created))
                    else:
                        unique_id = uuid.uuid1()
                        created = attribs['CREATED'] if pd.notnull(attribs['CREATED']) else (attribs['MODIFIED'] if pd.notnull(attribs['MODIFIED']) else datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S'))
                        modified = attribs['MODIFIED'] if pd.notnull(attribs['MODIFIED']) else datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
                        con.execute(f"INSERT INTO Note (Guid, UserMarkId, LocationId, Title, Content, BlockType, BlockIdentifier, LastModified, Created) VALUES ('{unique_id}', ?, ?, ?, ?, ?, ?, ?, ?);", (usermark_id, location_id, attribs['TITLE'], attribs['NOTE'], block_type, attribs['BLOCK'], modified, created))
                    note_id = con.execute(f"SELECT NoteId from Note WHERE Guid = '{unique_id}';").fetchone()[0]
                    process_tags(note_id, attribs['TAGS'])

                df.fillna({'ISSUE': 0}, inplace=True)
                df.fillna({'COLOR': 0}, inplace=True)
                df.fillna({'TAGS': ''}, inplace=True)
                df.fillna({'TITLE': ''}, inplace=True)
                df.fillna({'NOTE': ''}, inplace=True)
                count = 0
                for i, row in df.iterrows():
                    try:
                        count += 1
                        if pd.notna(row['BK']): # Bible note
                            location_id = add_scripture_location(row)
                            usermark_id = add_usermark(row, location_id)
                            if pd.notna(row['BLOCK']): # Bible book title
                                row['BLOCK'] = 1
                                block_type = 1
                            elif pd.notna(row['VS']): # regular note
                                block_type = 2
                                row['BLOCK'] = row['VS']
                            else: # top of chapter note
                                block_type = 0
                            update_note(row, location_id, block_type, usermark_id)
                        elif pd.notna(row['DOC']): # publication note
                            location_id = add_publication_location(row)
                            usermark_id = add_usermark(row, location_id)
                            block_type = 1 if pd.notna(row['BLOCK']) else 0
                            update_note(row, location_id, block_type, usermark_id)
                        else: # independent note
                            update_note(row, None, 0, None)
                    except:
                        QMessageBox.critical(None, _('Error!'), _('Error on import!\n\nFaulting entry')+f': #{count}', QMessageBox.Abort)
                        con.execute('ROLLBACK;')
                        return 0
                return count

            if Path(file).suffix == '.txt':
                with open(file, 'r', encoding='utf-8', errors='namereplace') as import_file:
                    if pre_import():
                        df = read_text()
                        count = update_db(df)
                    else:
                        count = 0
            else:
                df = pd.read_excel(file)
                count = update_db(df)
            return count

        def import_playlist(): 

            def update_db():

                def check_label(tag, label):
                    name = label
                    ext = 0
                    while name in current_labels[tag]:
                        ext += 1
                        name = f'{label} ({ext})'
                    current_labels[tag].append(name)
                    return name

                def add_media(rec):
                    fn = rec[1]
                    if rec[-1] in current_hashes and fn == current_media[current_hashes.index(rec[-1])][2] and rec[-1] == current_media[current_hashes.index(rec[-1])][4]: # exact same file (name and hash) already exists
                        return fn, current_media[current_hashes.index(rec[-1])][0]
                    ext = 0
                    while os.path.isfile(tmp_path + '/' + fn):
                        ext += 1
                        fn = f'{rec[1]}_{ext}'
                    shutil.copy2(playlist_path + '/' + rec[1], tmp_path + '/' + fn)
                    rec[1] = fn
                    current_media.append(fn)
                    current_hashes.append(rec[-1])
                    media_id = con.execute('INSERT INTO IndependentMedia (OriginalFileName, FilePath, MimeType, Hash) VALUES (?, ?, ?, ?);', rec).lastrowid
                    return rec[1], media_id

                def add_tag(tag_id, item_id):
                    position = con.execute(f'SELECT ifnull(max(Position), -1) FROM TagMap WHERE TagId = {tag_id};').fetchone()[0] + 1
                    con.execute('INSERT Into TagMap (PlaylistItemId, TagId, Position) VALUES (?, ?, ?);', (item_id, tag_id, position))

                def add_markers(current_item):
                    for row in impcon.execute('SELECT * FROM PlaylistItemMarker WHERE PlaylistItemId = ?;', (current_item,)).fetchall():
                        marker_id = con.execute('INSERT INTO PlaylistItemMarker (PlaylistItemId, Label, StartTimeTicks, DurationTicks, EndTransitionDurationTicks) VALUES (?, ?, ?, ?, ?);', ([item_id] + list(row[2:6]))).lastrowid
                        for i in impcon.execute('SELECT VerseId FROM PlaylistItemMarkerBibleVerseMap WHERE PlaylistItemMarkerId = ?;', (row[0],)).fetchall():
                            con.execute('INSERT INTO PlaylistItemMarkerBibleVerseMap (PlaylistItemMarkerId, VerseId) VALUES (?, ?);', (marker_id, i[0]))
                        for i in impcon.execute('SELECT * FROM PlaylistItemMarkerParagraphMap WHERE PlaylistItemMarkerId = ?;', (row[0],)).fetchall():
                            con.execute('INSERT INTO PlaylistItemMarkerParagraphMap (PlaylistItemMarkerId, MepsDocumentId, ParagraphIndex, MarkerIndexWithinParagraph) VALUES (?, ?, ?, ?);', ([marker_id] + list(i[1:4])))

                def add_locations(current_item):
                    for row in impcon.execute('SELECT * FROM PlaylistItemLocationMap LEFT JOIN Location USING (LocationID) WHERE PlaylistItemId = ?;', (current_item,)).fetchall():
                        bk, ch, doc, tk, iss, key, ln, tp, ti = row[4:13]
                        if bk:
                            try:
                                location_id = con.execute('INSERT INTO Location (BookNumber, ChapterNumber, KeySymbol, MepsLanguage, Type, Title) VALUES (?, ?, ?, ?, ?, ?);', (bk, ch, key, ln, tp, ti)).lastrowid
                            except:
                                location_id = con.execute('SELECT LocationId FROM Location WHERE BookNumber = ? AND ChapterNumber = ? AND KeySymbol = ? AND MepsLanguage = ?;', (bk, ch, key, ln)).fetchone()[0]
                        else:
                            try:
                                location_id = con.execute('INSERT INTO Location (DocumentId, Track, IssueTagNumber, KeySymbol, MepsLanguage, Type, Title) VALUES (?, ?, ?, ?, ?, ?, ?);', (doc, tk, iss, key, ln, tp, ti)).lastrowid
                            except:
                                location_id = con.execute('SELECT LocationId FROM Location WHERE Track = ? AND IssueTagNumber = ? AND KeySymbol = ? AND MepsLanguage = ? AND Type = ?;', (tk, iss, key, ln, tp)).fetchone()[0]
                        con.execute('INSERT INTO PlaylistItemLocationMap (PlaylistItemId, LocationId, MajorMultimediaType, BaseDurationTicks) VALUES (?, ?, ?, ?);', (item_id, location_id, row[2], row[3]))

                current_media = con.execute('SELECT * FROM IndependentMedia;').fetchall()
                current_hashes = [x[4] for x in current_media]
                current_labels = {}
                tags = {}
                for t in impcon.execute('SELECT Name FROM Tag WHERE Type = 2;').fetchall():
                    tag = t[0]
                    try:
                        tag_id = con.execute('SELECT TagId FROM Tag WHERE Type = 2 AND Name = ?;', (tag,)).fetchone()[0]
                        rows = con.execute('SELECT Label FROM PlaylistItem LEFT JOIN TagMap USING (PlaylistItemId) WHERE TagId = ?;', (tag_id,)).fetchall()
                        current_labels[tag] = [x[0] for x in rows]
                    except:
                        con.execute('INSERT INTO Tag (Type, Name) SELECT 2, ?;', (tag,))
                        tag_id = con.execute('SELECT TagId FROM Tag WHERE Type = 2 AND Name = ?;', (tag,)).fetchone()[0]
                        current_labels[tag] = []
                    tags[tag] = tag_id

                rows = impcon.execute('SELECT * FROM PlaylistItem pi LEFT JOIN IndependentMedia im ON (pi.ThumbnailFilePath = im.FilePath) LEFT JOIN TagMap USING (PlaylistItemId) LEFT JOIN Tag USING (TagId) ORDER BY Position;').fetchall()
                for row in rows:
                    tag = row[18]
                    tag_id = tags[tag]
                    item_rec = list(row[1:7])
                    item_rec[0] = check_label(tag, item_rec[0])
                    item_rec[5], media_id = add_media(list(row[8:12]))
                    item_id = con.execute('INSERT INTO PlaylistItem (Label, StartTrimOffsetTicks, EndTrimOffsetTicks, Accuracy, EndAction, ThumbnailFilePath) VALUES (?, ?, ?, ?, ?, ?);', (item_rec)).lastrowid
                    for i in impcon.execute('SELECT * FROM PlaylistItemIndependentMediaMap LEFT JOIN IndependentMedia USING (IndependentMediaId) WHERE PlaylistItemId = ?;', (row[0],)).fetchall():
                        rec, media_id = add_media(list(i[3:7]))
                        con.execute('INSERT OR REPLACE INTO PlaylistItemIndependentMediaMap (PlaylistItemId, IndependentMediaId, DurationTicks) VALUES (?, ?, ?);', (item_id, media_id, i[2]))
                    add_tag(tag_id, item_id)
                    add_markers(row[0])
                    add_locations(row[0])
                return len(rows)

            playlist_path = mkdtemp(prefix='JWLPlaylist_')
            with ZipFile(file, 'r') as zipped:
                zipped.extractall(playlist_path)
            db = 'userData.db'
            impcon = sqlite3.connect(f'{playlist_path}/{db}')
            count = update_db()
            impcon.close()
            shutil.rmtree(playlist_path, ignore_errors=True)
            return count

        if not file:
            category = self.combo_category.currentText()
            if category == _('Highlights') or category == _('Bookmarks'):
                flt = _('Text files')+' (*.txt)'
            elif category == _('Playlists'):
                flt = _('JW Library playlists')+' (*.jwlplaylist *.jwlibrary)'
            else:
                flt = _('MS Excel files')+' (*.xlsx);;'+_('Text files')+' (*.txt)'
            file = QFileDialog.getOpenFileName(self, _('Import file'), f'{self.working_dir}/', flt)[0]
            if file == '':
                self.statusBar.showMessage(' '+_('NOT imported!'), 3500)
                return
        self.working_dir = Path(file).parent
        self.statusBar.showMessage(' '+_('Importing. Please wait…'))
        app.processEvents()
        try:
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
            con.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'MEMORY'; PRAGMA foreign_keys = 'OFF'; BEGIN;")
            if category == _('Annotations'):
                count = import_annotations()
            elif category == _('Bookmarks'):
                count = import_bookmarks()
            elif category == _('Highlights'):
                count = import_highlights()
            elif category == _('Notes'):
                count = import_notes()
            elif category == _('Playlists'):
                count = import_playlist()
            con.execute("PRAGMA foreign_keys = 'ON';")
            con.commit()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        if not count:
            self.statusBar.showMessage(' '+_('NOT imported!'), 3500)
            return
        message = f' {category}: {count} '+_('items imported/updated')
        self.statusBar.showMessage(message, 3500)
        self.archive_modified()
        self.trim_db()
        self.regroup(False, message)


    def data_viewer(self):

        def body_changed():
            if self.viewer_window.body.toPlainText() == self.note_item.body:
                self.viewer_window.body.setStyleSheet('font: normal; color: #3d3d5c;')
                self.body_modified = False
            else:
                self.viewer_window.body.setStyleSheet('font: italic; color: #3d3d5c;')
                self.body_modified = True
            update_editor_toolbar()

        def title_changed():
            if self.viewer_window.title.toPlainText() == self.note_item.title:
                self.viewer_window.title.setStyleSheet('font: bold; color: #3d3d5c; font-size: 20px;')
                self.title_modified = False
            else:
                self.viewer_window.title.setStyleSheet('font: bold italic; color: #3d3d5c; font-size: 20px;')
                self.title_modified = True
            update_editor_toolbar()

        def update_editor_toolbar():
            if self.title_modified or self.body_modified:
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

        def accept_change():
            self.note_item.title = self.viewer_window.title.toPlainText().strip()
            self.note_item.body = self.viewer_window.body.toPlainText().rstrip()
            self.note_item.update_note()
            self.modified_list.append(self.note_item)
            update_viewer_toolbar()
            go_back()

        def data_editor(counter):
            self.viewer_window.setWindowTitle(_('Data Editor'))
            self.note_item = self.viewer_items[counter]
            self.viewer_window.title.setPlainText(self.note_item.title)
            if self.note_item.meta:
                self.viewer_window.meta.setText(self.note_item.meta)
            else:
                self.viewer_window.meta.setHidden(True)
                self.viewer_window.title.setReadOnly(True)
            self.viewer_window.body.setPlainText(self.note_item.body)
            self.viewer_window.editor.setStyleSheet(f"background-color: {self.note_item.color}")
            self.viewer_window.viewer_layout.setCurrentIndex(1)
            app.processEvents()

        def update_viewer_toolbar():
            self.viewer_window.discard_action.setText(_('Discard changes and close'))
            self.viewer_window.confirm_action.setText(_('Confirm changes and close'))
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
                for item in self.modified_list:
                    con.execute('UPDATE Note SET Title = ?, Content = ?, LastModified = ? WHERE NoteId = ?;', (item.title, item.body, datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S'), item.idx))
                for item in self.deleted_list:
                    con.execute(f'DELETE FROM Note WHERE NoteId = {item.idx};')

            def update_annotations():
                for item in self.modified_list:
                    con.execute('UPDATE InputField SET Value = ? WHERE LocationId = ? AND TextTag = ?;', (item.body, item.idx, item.label))
                for item in self.deleted_list:
                    con.execute('DELETE FROM InputField WHERE LocationId = ? AND TextTag = ?;', (item.idx, item.label))

            try:
                con = sqlite3.connect(f'{tmp_path}/{db_name}')
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
                self.statusBar.showMessage(message, 3500)
                self.trim_db()
                self.regroup(False, message)
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
            if fname == '':
                self.statusBar.showMessage(' '+_('NOT saved!'), 3500)
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
            self.statusBar.showMessage(' '+_('Saved'), 3500)
            self.viewer_window.raise_()

        def clean_text(text):
            return regex.sub(r'\p{Z}', ' ', text)

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
                        'NOTE': row[2].rstrip() if row[2] else '',
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
                            if item.get('VS'):
                                vs = str(item['VS']).zfill(3)
                            else:
                                vs = '000'
                            script = str(item['BK']).zfill(2) + str(item['CH']).zfill(3) + vs
                            item['Link'] = f"https://www.jw.org/finder?wtlocale={item['LANG']}&pub={item['PUB']}&bible={script}"
                            if not item.get('HEADING'):
                                item['HEADING'] = f"{bible_books[item['BK']]} {item['CH']}"
                            elif item.get('VS') and (':' not in item['HEADING']):
                                item['HEADING'] += f":{item['VS']}"
                        else: # publication note
                            par = f"&par={item['BLOCK']}" if item.get('BLOCK') else ''
                            item['Link'] = f"https://www.jw.org/finder?wtlocale={item['LANG']}&docid={item['DOC']}{par}"
                            if row[9] and (row[9] > 10000000):
                                item['ISSUE'] = process_issue(row[9])
                    item_list.append(item)
                return item_list

            clrs = ['#f1f1f1', '#fffce6', '#effbe6', '#e6f7ff', '#ffe6f0', '#fff0e6', '#f1eafa']
            counter = 1
            self.viewer_window.txt_action.setEnabled(False)
            self.viewer_window.setWindowTitle(_('Data Viewer') + ' — ' + _('Processing…'))
            for item in get_notes():
                metadata = f"title: {clean_text(item['TITLE'])}\n"
                metadata += f"date: {item['MODIFIED']}\n"
                if item.get('PUB'):
                    metadata += f"publication: {item['PUB']}-{item['LANG']} {item['ISSUE']}".strip() + '\n'
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
                        meta += f"<br><a href='{lnk}' style='color: #7575a3; text-decoration: none'>{lnk}</a>"
                    meta += '</tt></strong></small>'
                note_box = ViewerItem(item['ID'], clrs[item['COLOR']], clean_text(item['TITLE']), clean_text(item['NOTE']), meta, metadata)
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
                        'VALUE': row[1].rstrip() if row[1] else '',
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
                note_box = ViewerItem(item['ID'], '#f1f1f1', title, clean_text(item['VALUE']), None, metadata)
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
        self.viewer_window = DataViewer(self.viewer_size, self.viewer_pos)
        connect_signals()
        self.viewer_window.filter_box.setPlaceholderText(_('Filter'))
        self.viewer_window.show()
        self.viewer_window.raise_()
        self.viewer_window.activateWindow()
        self.viewer_window.filter_box.setFocus()
        app.processEvents()
        try:
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
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


    def add_items(self):

        def add_favorite():

            def add_dialog():

                def set_edition():
                    lng = language.currentText()
                    publication.clear()
                    publication.addItems(sorted(favorites.loc[favorites['Lang'] == lng]['Short']))

                dialog = QDialog()
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
                position = con.execute(f'SELECT max(Position) FROM TagMap WHERE TagId = {tag_id};').fetchone()
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
            language = int(favorites.loc[(favorites.Short == pub) & (favorites.Lang == lng), 'Language'].values[0])
            publication = favorites.loc[(favorites.Short == pub) & (favorites.Lang == lng), 'Symbol'].values[0]
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

                dialog = QDialog()
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
                get_files.setFixedSize(26, 26)
                get_files.setIcon(QPixmap(f'{project_path}/res/icons/icons8-add-file-64.png'))
                get_files.clicked.connect(select_files)

                clear_files = QPushButton(dialog)
                clear_files.setFixedSize(26, 26)
                clear_files.setIcon(QPixmap(f'{project_path}/res/icons/icons8-delete-64.png'))
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
                    position = con.execute(f'SELECT ifnull(max(Position), -1) FROM TagMap WHERE TagId = {tag_id};').fetchone()[0] + 1
                    con.execute('INSERT Into TagMap (PlaylistItemId, TagId, Position) VALUES (?, ?, ?);', (item_id, tag_id, position))

                # get/create tag; get all labels associated with it
                try:
                    tag_id = con.execute('SELECT TagId FROM Tag WHERE Name = ? and Type = 2;', (playlist,)).fetchone()[0]
                    rows = con.execute('SELECT Label FROM PlaylistItem LEFT JOIN TagMap USING (PlaylistItemId) WHERE TagId = ?;', (tag_id,)).fetchall()
                    current_labels  = [x[0] for x in rows]
                except:
                    con.execute('INSERT INTO Tag (Type, Name) SELECT 2, ?;', (playlist,))
                    tag_id = con.execute('SELECT TagId FROM Tag WHERE Type = 2 AND Name = ?;', (playlist,)).fetchone()[0]
                    current_labels = []

                rows = con.execute('SELECT * FROM IndependentMedia;').fetchall()
                current_files = [x[2] for x in rows]
                current_hashes = [x[4] for x in rows]

                sha256hash = FileHash('sha256')
                result = 0
                for fl in files:
                    f = fl[0]
                    mime = fl[1]
                    ext = fl[2]
                    name = Path(f).name
                    hash256 = sha256hash.hash_file(f)
                    if hash256 not in current_hashes: # new file to be added
                        # add original file with non-clashing file name
                        current_hashes.append(hash256)
                        new_name = check_name(name)
                        current_files.append(new_name)
                        shutil.copy2(f, f'{tmp_path}/{new_name}')
                        media_id = con.execute('INSERT INTO IndependentMedia (OriginalFileName, FilePath, MimeType, Hash) VALUES (?, ?, ?, ?);', (name, new_name, mime, hash256)).lastrowid

                        # generate and add thumbnail file
                        unique_id = str(uuid.uuid1())
                        thumb_name = f'{unique_id}.{ext}'
                        shutil.copy2(f, f'{tmp_path}/{thumb_name}')
                        i = Image.open(f'{tmp_path}/{thumb_name}')
                        i.thumbnail((250, 250))
                        i.save(f'{tmp_path}/{thumb_name}')
                        thash = sha256hash.hash_file(f'{tmp_path}/{thumb_name}')
                        con.execute('INSERT INTO IndependentMedia (OriginalFileName, FilePath, MimeType, Hash) VALUES (?, ?, ?, ?);', (name, thumb_name, mime, thash))

                    else: # file alread in archive
                        media_id, thumb_name = con.execute('SELECT IndependentMediaId, FilePath FROM IndependentMedia WHERE Hash = ?;', (hash256,)).fetchone()
                        if thumb_name != name:
                            thumb_name = con.execute('SELECT ThumbnailFilePath FROM PlaylistItemIndependentMediaMap JOIN PlaylistItem USING (PlaylistItemId) WHERE IndependentMediaId = ?;', (media_id,)).fetchone()[0]

                    result += 1
                    item_id = con.execute('INSERT INTO PlaylistItem (Label, StartTrimOffsetTicks, EndTrimOffsetTicks, Accuracy, EndAction, ThumbnailFilePath) VALUES (?, ?, ?, ?, ?, ?);', (check_label(name), None, None, 1, 1, thumb_name)).lastrowid
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
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
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
            self.statusBar.showMessage(message, 3500)
            self.archive_modified()
            self.trim_db()
            self.regroup(False, message)

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
                    os.remove(tmp_path + '/' + f[0])
                except:
                    pass
            rows = con.execute(f'SELECT FilePath FROM IndependentMedia JOIN PlaylistItemIndependentMediaMap USING (IndependentMediaId) WHERE PlaylistItemId NOT IN {items};').fetchall()
            used_files = [x[0] for x in rows]
            for f in con.execute(f'SELECT FilePath FROM IndependentMedia JOIN PlaylistItemIndependentMediaMap USING (IndependentMediaId) WHERE PlaylistItemId IN {items};').fetchall():
                if f[0] in used_files: # used by other items; skip
                    continue
                con.execute('DELETE FROM IndependentMedia WHERE FilePath = ?;', f)
                try:
                    os.remove(tmp_path + '/' + f[0])
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
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
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
            self.statusBar.showMessage(message, 3500)
            self.archive_modified()
            self.trim_db()
            self.regroup(False, message)


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
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
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
        self.statusBar.showMessage(message, 3500)
        self.archive_modified()
        self.trim_db()
        self.regroup(False, message)

    def reindex_db(self, con=None, pth=None):

        def init_progress():
            pd = QProgressDialog(_('Please wait…'), None, 0, 28, parent=self)
            pd.setWindowModality(Qt.WindowModal)
            pd.setWindowTitle(_('Reindexing'))
            pd.setWindowFlag(Qt.FramelessWindowHint)
            pd.setModal(True)
            pd.setMinimumDuration(0)
            return pd

        def make_table(table):
            con.executescript(f'CREATE TABLE CrossReference (Old INTEGER, New INTEGER PRIMARY KEY AUTOINCREMENT); INSERT INTO CrossReference (Old) SELECT {table}Id FROM {table} ORDER BY {table}Id;')

        def update_table(table, field):
            app.processEvents()
            con.executescript(f'UPDATE {table} SET {field} = (SELECT -New FROM CrossReference WHERE CrossReference.Old = {table}.{field}); UPDATE {table} SET {field} = abs({field});')
            if self.interactive:
                progress_dialog.setValue(progress_dialog.value() + 1)

        def reindex_notes():
            make_table('Note')
            update_table('Note', 'NoteId')
            update_table('TagMap', 'NoteId')
            con.execute('DROP TABLE CrossReference;')

        def reindex_bookmarks():
            make_table('Bookmark')
            update_table('Bookmark', 'BookmarkId')
            con.execute('DROP TABLE CrossReference;')

        def reindex_highlights():
            make_table('UserMark')
            update_table('UserMark', 'UserMarkId')
            update_table('Note', 'UserMarkId')
            update_table('BlockRange', 'UserMarkId')
            con.execute('DROP TABLE CrossReference;')
            make_table('BlockRange')
            update_table('BlockRange', 'BlockRangeId')
            con.execute('DROP TABLE CrossReference;')

        def reindex_playlists():

            def clean_media():
                thumbs = list(map(lambda x: x[0], con.execute('SELECT ThumbnailFilePath FROM PlaylistItem;').fetchall()))
                ind = list(map(lambda x: x[0], con.execute('SELECT FilePath FROM IndependentMedia JOIN PlaylistItemIndependentMediaMap USING (IndependentMediaId)').fetchall()))
                ind = ind + ['userData.db', 'manifest.json', 'default_thumbnail.png']
                for file in glob.glob(pth + '/*'):
                    f = Path(file).name
                    if (f not in thumbs) and (f not in ind):
                        try:
                            os.remove(pth + '/' + f)
                        except:
                            pass
                if self.interactive:
                    progress_dialog.setValue(progress_dialog.value() + 1)

            con.execute('DELETE FROM TagMap WHERE PlaylistItemId NOT IN ( SELECT PlaylistItemId FROM PlaylistItem );')
            make_table('PlaylistItem')
            update_table('PlaylistItem', 'PlaylistItemId')
            update_table('PlaylistItemIndependentMediaMap', 'PlaylistItemId')
            update_table('PlaylistItemLocationMap', 'PlaylistItemId')
            update_table('PlaylistItemMarker', 'PlaylistItemId')
            update_table('TagMap', 'PlaylistItemId')
            con.execute('DROP TABLE CrossReference;')

            con.execute('DELETE FROM PlaylistItemIndependentMediaMap WHERE IndependentMediaId NOT IN ( SELECT IndependentMediaId FROM IndependentMedia );')
            make_table('IndependentMedia')
            update_table('IndependentMedia', 'IndependentMediaId')
            update_table('PlaylistItemIndependentMediaMap','IndependentMediaId')
            con.execute('DROP TABLE CrossReference;')

            con.execute('DELETE FROM PlaylistItemMarkerBibleVerseMap WHERE PlaylistItemMarkerId NOT IN ( SELECT PlaylistItemMarkerId FROM PlaylistItemMarker );')
            con.execute('DELETE FROM PlaylistItemMarkerParagraphMap WHERE PlaylistItemMarkerId NOT IN ( SELECT PlaylistItemMarkerId FROM PlaylistItemMarker );')
            make_table('PlaylistItemMarker')
            update_table('PlaylistItemMarker', 'PlaylistItemMarkerId')
            update_table('PlaylistItemMarkerBibleVerseMap', 'PlaylistItemMarkerId')
            update_table('PlaylistItemMarkerParagraphMap', 'PlaylistItemMarkerId')
            con.execute('DROP TABLE CrossReference;')

            clean_media()

        def reindex_tags():
            make_table('TagMap')
            update_table('TagMap', 'TagMapId')
            con.execute('DROP TABLE CrossReference;')
            make_table('Tag')
            update_table('Tag', 'TagId')
            update_table('TagMap', 'TagId')
            con.execute('DROP TABLE CrossReference;')

        def reindex_locations():
            make_table('Location')
            update_table('Location', 'LocationId')
            update_table('Note', 'LocationId')
            update_table('InputField', 'LocationId')
            update_table('UserMark', 'LocationId')
            update_table('Bookmark', 'LocationId')
            update_table('Bookmark', 'PublicationLocationId')
            update_table('TagMap', 'LocationId')
            update_table('PlaylistItemLocationMap', 'LocationId')
            con.execute('DROP TABLE CrossReference;')

        self.interactive = False
        if not con:
            self.interactive = True
            reply = QMessageBox.information(self, _('Reindex'), _('This may take a few seconds.\nProceed?'), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.No:
                return
            self.statusBar.showMessage(' '+_('Reindexing. Please wait…'))
            app.processEvents()
            progress_dialog = init_progress()
            self.trim_db()
        if not pth:
            pth = tmp_path
        try:
            if self.interactive:
                con = sqlite3.connect(f'{pth}/{db_name}')
            con.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF'; PRAGMA foreign_keys = 'OFF'; BEGIN;")
            reindex_notes()
            reindex_tags()
            reindex_playlists()
            reindex_highlights()
            reindex_bookmarks()
            reindex_locations()
            con.executescript("PRAGMA foreign_keys = 'ON'; VACUUM;")
            con.commit()
            if self.interactive:
                con.close()
            else:
                self.trim_db(con)
        except Exception as ex:
            self.crash_box(ex)
            self.progress_dialog.close()
            self.clean_up()
            sys.exit()
        if self.interactive:
            message = ' '+_('Reindexed successfully')
            self.statusBar.showMessage(message, 3500)
            self.archive_modified()
            self.regroup(False, message)

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
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
            con.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF'; BEGIN;")
            reorder()
            con.commit()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        message = ' '+_('Notes reordered')
        self.statusBar.showMessage(message, 3500)
        self.archive_modified()
        self.trim_db()
        self.regroup(False, message)


    def trim_db(self, connection=None):
        try:
            if not connection:
                con = sqlite3.connect(f'{tmp_path}/{db_name}')
            else:
                con = connection
            sql = """
                PRAGMA temp_store = 2;
                PRAGMA journal_mode = 'OFF';
                PRAGMA foreign_keys = 'OFF';

                DELETE FROM Note WHERE (Title IS NULL OR Title = '')
                AND (Content IS NULL OR Content = '');

                DELETE FROM TagMap WHERE NoteId IS NOT NULL AND NoteId
                NOT IN (SELECT NoteId FROM Note);
                DELETE FROM Tag WHERE TagId NOT IN (SELECT DISTINCT TagId FROM TagMap) AND Type > 0;

                DELETE FROM BlockRange WHERE UserMarkId NOT IN
                (SELECT UserMarkId FROM UserMark);
                DELETE FROM UserMark WHERE UserMarkId NOT IN
                (SELECT UserMarkId FROM BlockRange) AND UserMarkId NOT IN
                (SELECT UserMarkId FROM Note WHERE UserMarkId NOT NULL);

                DELETE FROM Location WHERE LocationId NOT IN
                (SELECT LocationId FROM UserMark) AND LocationId NOT IN
                (SELECT LocationId FROM Note WHERE LocationId IS NOT NULL)
                AND LocationId NOT IN (SELECT LocationId FROM TagMap
                WHERE LocationId IS NOT NULL) AND LocationId NOT IN
                (SELECT LocationId FROM Bookmark) AND LocationId NOT IN 
                (SELECT PublicationLocationId FROM Bookmark)
                AND LocationId NOT IN (SELECT LocationId FROM InputField)
                AND LocationId NOT IN (SELECT LocationId FROM PlaylistItemLocationMap);

                DELETE FROM UserMark WHERE LocationId NOT IN
                (SELECT LocationId FROM Location);

                DELETE FROM PlaylistItem WHERE PlaylistItemId NOT IN
                (SELECT PlaylistItemId FROM TagMap
                WHERE PlaylistItemId IS NOT NULL);
                DELETE FROM PlaylistItemIndependentMediaMap WHERE PlaylistItemId NOT IN
                (SELECT PlaylistItemId FROM PlaylistItem);
                DELETE FROM PlaylistItemLocationMap WHERE PlaylistItemId NOT IN
                (SELECT PlaylistItemId FROM PlaylistItem);
                DELETE FROM PlaylistItemMarker WHERE PlaylistItemId NOT IN
                (SELECT PlaylistItemId FROM PlaylistItem);

                PRAGMA foreign_keys = 'ON';
                VACUUM;
                """
            con.executescript(sql)
            con.commit()
            if not con:
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
        shutil.rmtree(tmp_path, ignore_errors=True)
        settings.setValue('JWLManager/language', self.lang)
        settings.setValue('JWLManager/category', self.combo_category.currentIndex())
        settings.setValue('JWLManager/title', self.title_format)
        settings.setValue('JWLManager/column1', self.treeWidget.columnWidth(0))
        settings.setValue('JWLManager/column2', self.treeWidget.columnWidth(1))
        settings.setValue('JWLManager/sort', self.treeWidget.sortColumn())
        settings.setValue('JWLManager/direction', self.treeWidget.header().sortIndicatorOrder())
        settings.setValue('JWLManager/archive', self.current_archive)
        settings.setValue('Main_Window/position', self.pos())
        settings.setValue('Main_Window/size', self.size())
        settings.setValue('Viewer/position', self.viewer_pos)
        settings.setValue('Viewer/size', self.viewer_size)
        settings.setValue('Help/position', self.help_pos)
        settings.setValue('Help/size', self.help_size)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    global translator
    translator = {}
    translator[lang] = QTranslator()
    translator[lang].load(f'{project_path}/res/locales/UI/qt_{lang}.qm')
    app.installTranslator(translator[lang])
    font = QFont()
    font.setPixelSize(16)
    app.setFont(font)
    win = Window()
    win.show()
    sys.exit(app.exec())
