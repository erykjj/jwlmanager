#!/usr/bin/env python3

"""
  File:           JWLManager

  Description:    Manage .jwlibrary backup archives

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

APP = 'JWLManager'
VERSION = 'v3.1.0'


import argparse, gettext, glob, json, os, regex, requests, shutil, sqlite3, sys, uuid
import pandas as pd

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from datetime import datetime, timezone
from filehash import FileHash
from pathlib import Path
from platform import platform
from random import randint
from tempfile import mkdtemp
from time import time
from traceback import format_exception
from xlsxwriter import Workbook
from zipfile import ZipFile, ZIP_DEFLATED

from res.ui_main_window import Ui_MainWindow


#### Initial language setting based on passed arguments
def get_language():
    global available_languages, tr
    available_languages = { # add/enable completed languages
        # 'de': 'German (Deutsch)',
        'en': 'English (default)',
        'es': 'Spanish (español)',
        'fr': 'French (français)',
        'it': 'Italian (italiano)',
        # 'pl': 'Polish (Polski)',
        'pt': 'Portuguese (Português)',
        # 'ru': 'Russian (pусский)',
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

    lng = 'en'
    for l in args.keys():
        if args[l]:
            lng = l
    return lng

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = project_path 
    return os.path.join(base_path, relative_path)

def read_resources(lng):

    def load_bible_books(lng):
        for row in cur.execute(f'SELECT Number, Name FROM BibleBooks WHERE Language = {lng};').fetchall():
            bible_books[row[0]] = row[1]

    def load_languages():
        for row in cur.execute('SELECT Language, Name, Code, Symbol FROM Languages;').fetchall():
            lang_name[row[0]] = row[1]
            lang_symbol[row[0]] = row[3]
            if row[2] == lng:
                ui_lang = row[0]
        return ui_lang

    def load_pubs(lng):
        types = {}
        for row in cur.execute(f'SELECT Type, [Group] FROM Types WHERE Language = {lng};').fetchall():
            types[row[0]] = row[1]
        lst = []
        for row in cur.execute("SELECT Language, Symbol, ShortTitle Short, Title 'Full', Year, Type, Favorite FROM Publications;").fetchall():
            note = [ int(row[0]), row[1], row[2], row[3], row[4], types[row[5]], row[6] ]
            lst.append(note)
        for row in cur.execute(f"SELECT Language, Symbol, ShortTitle Short, Title 'Full', Year, Type, Favorite FROM Extras WHERE Language = {lng};").fetchall():
            note = [ int(row[0]), row[1], row[2], row[3], row[4], types[row[5]], row[6] ]
            lst.append(note)
        pubs = pd.DataFrame(lst, columns=['Language', 'Symbol', 'Short', 'Full', 'Year', 'Type', 'Favorite'])
        favs = pubs[pubs['Favorite'] == 1]
        favs = favs.drop(['Full', 'Year', 'Type', 'Favorite'], axis=1)
        favs['Lang'] = favs['Language'].map(lang_name)
        pubs = pubs[pubs['Language'] == lng]
        pubs = pubs.drop(['Language', 'Favorite'], axis=1)
        return favs, pubs

    global _, bible_books, favorites, lang_name, lang_symbol, publications
    _ = tr[lng].gettext
    lang_name = {}
    lang_symbol = {}
    bible_books = {}
    con = sqlite3.connect(project_path / 'res/resources.db')
    cur = con.cursor()
    ui_lang = load_languages()
    load_bible_books(ui_lang)
    favorites, publications = load_pubs(ui_lang)
    cur.close()
    con.close()

project_path = Path(__file__).resolve().parent
tmp_path = mkdtemp(prefix='JWLManager_')
db_name = 'userData.db'
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

        def init_about():
                year = f'MIT ©{datetime.now().year}'
                owner = 'Eryk J.'
                web = 'https://github.com/erykjj/jwlmanager'
                contact = b'\x69\x6E\x66\x69\x6E\x69\x74\x69\x40\x69\x6E\x76\x65\x6E\x74\x61\x74\x69\x2E\x6F\x72\x67'.decode('utf-8')

                self.about_window = QDialog(self)
                self.about_window.setStyleSheet("QDialog {border:2px solid #5b3c88}")
                layout = QHBoxLayout(self.about_window)
                left_layout = QVBoxLayout()
                icon = QLabel(self.about_window)
                icon.setPixmap(QPixmap(self.resource_path('res/icons/project_72.png')))
                icon.setGeometry(12,12,72,72)
                icon.setAlignment(Qt.AlignTop)
                left_layout.addWidget(icon)

                right_layout = QVBoxLayout()
                title_label = QLabel(self.about_window)
                text = f'<div style="text-align:center;"><h2><span style="color:#800080;">{APP}</span></h2><p><small>{year} {owner}</small></p><h4>{VERSION.lstrip("v")}</h4></div>'
                title_label.setText(text)

                self.update_label = QLabel(self.about_window)
                text = '<div style="text-align:center;"><small><i>'+_('Checking for updates…') +'</i></small></div>'
                self.update_label.setText(text)
                self.update_label.setOpenExternalLinks(True)

                contact_label = QLabel(self.about_window)
                text = text = f'<div style="text-align:center;"><small><a style="color:#666699; text-decoration:none;" href="mail-to:{contact}"><em>{contact}</em></a><br><a style="color:#666699; text-decoration:none;" href="{web}">{web}</small></a></div>'
                contact_label.setText(text)
                contact_label.setOpenExternalLinks(True)

                right_layout.addWidget(title_label)
                right_layout.addWidget(self.update_label)
                right_layout.addWidget(contact_label)

                button = QDialogButtonBox(QDialogButtonBox.Ok)
                button.setFixedWidth(72)
                button.accepted.connect(self.about_window.accept)

                left_layout.addWidget(button)
                layout.addLayout(left_layout)
                layout.addLayout(right_layout)
                self.about_window.setWindowFlag(Qt.FramelessWindowHint)

        def init_help():
            self.help_window = QDialog(self)
            self.help_window.setWindowFlags(Qt.Window)
            self.help_window.setWindowIcon((QIcon(self.resource_path('res/icons/project_72.png'))))
            self.help_window.setWindowTitle(_('Help'))
            self.help_window.resize(1020, 812)
            self.help_window.move(50, 50)
            self.help_window.setMinimumSize(300, 300)
            text = QTextEdit(self.help_window)
            text.setReadOnly(True)
            with open(self.resource_path('res/HELP.md'), encoding='utf-8') as f:
                text.setMarkdown(f.read())
            layout = QHBoxLayout(self.help_window)
            layout.addWidget(text)
            self.help_window.setWindowState((self.help_window.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
            self.help_window.finished.connect(self.help_window.hide())

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
            self.button_export.clicked.connect(self.export_items)
            self.button_import.clicked.connect(self.import_items)
            self.button_add.clicked.connect(self.add_favorite)
            self.button_delete.clicked.connect(self.delete_items)
            self.button_view.clicked.connect(self.data_viewer)

        def set_vars():
            self.total.setText('')
            self.int_total = 0
            self.modified = False
            self.title_format = 'short'
            self.save_filename = ''
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
        self.settings = QSettings(f'{project_path}/settings', QSettings.Format.IniFormat)
        self.viewer_pos = self.settings.value('Viewer/pos', QPoint(50, 50))
        self.viewer_size = self.settings.value('Viewer/size', QSize(698, 846))
        self.setAcceptDrops(True)
        self.combo_grouping.setCurrentText(_('Type'))
        self.status_label = QLabel()
        self.statusBar.addPermanentWidget(self.status_label, 0)
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.sortByColumn(1, Qt.DescendingOrder)
        self.treeWidget.setExpandsOnDoubleClick(False)
        self.treeWidget.setColumnWidth(0, 500)
        self.treeWidget.setColumnWidth(1, 30)
        self.button_add.setVisible(False)
        self.resize(self.settings.value('Main_Window/size', QSize(680, 641)))
        self.move(self.settings.value('Main_Window/pos', center()))
        self.viewer_window = QDialog(self)
        connect_signals()
        set_vars()
        init_about()
        init_help()
        self.new_file()


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
        if suffix == '.jwlibrary' or suffix == '.jwlplaylist':
            self.load_file(file)
        elif not self.combo_category.isEnabled():
            QMessageBox.warning(self, _('Error'), _('No archive has been opened!'), QMessageBox.Cancel)
        elif suffix == '.txt':
            with open(file, 'r', encoding='utf-8', errors='namereplace') as f:
                header = f.readline().strip()
            if header == r'{ANNOTATIONS}':
                self.import_items(file, _('Annotations'))
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

    def about_box(self):
        if not self.latest:
            url = 'https://api.github.com/repos/erykjj/jwlmanager/releases/latest'
            headers = { 'X-GitHub-Api-Version': '2022-11-28' }
            try:
                r = requests.get(url, headers=headers, timeout=5)
                self.latest = json.loads(r.content.decode('utf-8'))['name']
                if self.latest != VERSION:
                    text = f'<div style="text-align:center;"><a style="color:red; text-decoration:none;" href="https://github.com/erykjj/jwlmanager/releases/latest"><small><b>{self.latest.lstrip("v")} '+_('update available!')+'</b></small></a></div>'
                else:
                    text = f'<div style="text-align:center;"><small>'+_('Latest version')+'</small></div>'
            except:
                text = f'<div style="text-align:center;"><small><i>'+_('Error while checking for updates!')+'</u></small></div>'
            self.update_label.setText(text)
        self.about_window.exec()

    def crash_box(self, ex):
        tb_lines = format_exception(ex.__class__, ex, ex.__traceback__)
        tb_text = ''.join(tb_lines)
        dialog = QDialog()
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
            translator[self.lang].load(resource_path(f'res/locales/UI/qt_{self.lang}.qm'))
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
        self.button_export.setEnabled(self.selected_items and self.combo_category.currentText() in (_('Notes'), _('Highlights'), _('Annotations')))

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
            self.combo_grouping.blockSignals(True)
            for item in range(6):
                self.combo_grouping.model().item(item).setEnabled(True)
            for item in lst:
                self.combo_grouping.model().item(item).setEnabled(False)
                if self.combo_grouping.currentText() == self.combo_grouping.itemText(item):
                    self.combo_grouping.setCurrentText(_('Type'))
            self.combo_grouping.blockSignals(False)

        if selection == _('Notes'):
            disable_options([], False, True, True, True)
        elif selection == _('Highlights'):
            disable_options([4], False, True, True, False)
        elif selection == _('Bookmarks'):
            disable_options([4,5], False, False, False, False)
        elif selection == _('Annotations'):
            disable_options([2,4,5], False, True, True, True)
        elif selection == _('Favorites'):
            disable_options([4,5], True, False, False, False)
        self.regroup()

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
            for row in cur.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, TextTag, l.BookNumber, l.ChapterNumber, l.Title FROM InputField JOIN Location l USING (LocationId);'):
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
            for row in cur.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, BookmarkId, l.BookNumber, l.ChapterNumber, l.Title FROM Bookmark b JOIN Location l USING (LocationId);'):
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
            for row in cur.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, TagMapId FROM TagMap tm JOIN Location l USING (LocationId) WHERE tm.NoteId IS NULL ORDER BY tm.Position;'):
                lng = lang_name.get(row[2], f'#{row[2]}')
                code, year = process_code(row[1], row[3])
                detail1, year, detail2 = process_detail(row[1], None, None, row[3], year)
                item = row[4]
                rec = [ item, lng, code, year, detail1, detail2 ]
                lst.append(rec)
            favorites = pd.DataFrame(lst, columns=[ 'Id', 'Language', 'Symbol','Year', 'Detail1', 'Detail2' ])
            self.current_data = merge_df(favorites)

        def get_highlights():
            lst = []
            for row in cur.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, b.BlockRangeId, u.UserMarkId, u.ColorIndex, l.BookNumber, l.ChapterNumber FROM UserMark u JOIN Location l USING (LocationId), BlockRange b USING (UserMarkId);'):
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
                for row in cur.execute("SELECT NoteId Id, ColorIndex Color, GROUP_CONCAT(Name, ' | ') Tags, substr(LastModified, 0, 11) Modified FROM (SELECT * FROM Note n LEFT JOIN TagMap tm USING (NoteId) LEFT JOIN Tag t USING (TagId) LEFT JOIN UserMark u USING (UserMarkId) ORDER BY t.Name) n WHERE n.BlockType = 0 AND LocationId IS NULL GROUP BY n.NoteId;"):
                    col = row[1] or 0
                    yr = row[3][0:4]
                    note = [ row[0], _('* NO LANGUAGE *'), _('* OTHER *'), process_color(col), row[2] or _('* NO TAG *'), row[3] or '', yr, None, _('* OTHER *'), _('* OTHER *'), _('* INDEPENDENT *') ]
                    lst.append(note)
                return pd.DataFrame(lst, columns=['Id', 'Language', 'Symbol', 'Color', 'Tags', 'Modified', 'Year', 'Detail1',  'Short', 'Full', 'Type'])

            lst = []
            for row in cur.execute("SELECT NoteId Id, MepsLanguage Language, KeySymbol Symbol, IssueTagNumber Issue, BookNumber Book, ChapterNumber Chapter, ColorIndex Color, GROUP_CONCAT(Name, ' | ') Tags, substr(LastModified, 0, 11) Modified FROM (SELECT * FROM Note n JOIN Location l USING (LocationId) LEFT JOIN TagMap tm USING (NoteId) LEFT JOIN Tag t USING (TagId) LEFT JOIN UserMark u USING (UserMarkId) ORDER BY t.Name) n GROUP BY n.NoteId;"):
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

        def enable_options(enabled):
            self.combo_grouping.setEnabled(enabled)
            self.combo_category.setEnabled(enabled)
            self.actionReindex.setEnabled(enabled)
            self.actionObscure.setEnabled(enabled)
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
            if self.current_data.shape[0] == 0:
                return
            self.current_data['Title'] = self.current_data[title]
            views = define_views(category)
            self.int_total = self.current_data.shape[0]
            self.total.setText(f'**{self.int_total:,}**')
            filters = views[grouping]
            traverse(self.current_data, filters, self.treeWidget)

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
            cur = con.cursor()
            cur.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF';")
            if not same_data:
                self.current_data = []
                get_data()
            self.leaves = {}
            self.treeWidget.clear()
            self.treeWidget.repaint()
            build_tree()
            con.commit()
            cur.close()
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
        elif reply == QMessageBox.Cancel:
            return

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
        with ZipFile(self.resource_path('res/blank'),'r') as zipped:
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
                'schemaVersion': 13 } }
        with open(f'{tmp_path}/manifest.json', 'w') as json_file:
                json.dump(m, json_file, indent=None, separators=(',', ':'))
        self.file_loaded()

    def load_file(self, archive = ''):
        if self.modified:
            self.check_save()
        if not archive:
            fname = QFileDialog.getOpenFileName(self, _('Open archive'), str(self.working_dir),_('JW Library archives')+' (*.jwlibrary *.jwlplaylist)')
            if fname[0] == '':
                return
            archive = fname[0]
        self.current_archive = Path(archive)
        self.working_dir = Path(archive).parent
        self.status_label.setStyleSheet('color: black;')
        self.status_label.setText(f'{Path(archive).stem}  ')
        global db_name
        try:
            os.remove(f'{tmp_path}/manifest.json')
            os.remove(f'{tmp_path}/{db_name}')
        except:
            pass
        with ZipFile(archive,'r') as zipped:
            zipped.extractall(tmp_path)
        if os.path.exists(f'{tmp_path}/user_data.db'):
            db_name = 'user_data.db' # iPhone & iPad backups
        else:
            db_name = 'userData.db' # Windows & Android
        self.file_loaded()

    def file_loaded(self):
        self.actionReindex.setEnabled(True)
        self.actionObscure.setEnabled(True)
        self.combo_grouping.setEnabled(True)
        self.combo_category.setEnabled(True)
        self.actionSave.setEnabled(False)
        self.actionSave_As.setEnabled(True)
        self.actionCollapse_All.setEnabled(True)
        self.actionExpand_All.setEnabled(True)
        self.actionSelect_All.setEnabled(True)
        self.actionUnselect_All.setEnabled(True)
        self.menuTitle_View.setEnabled(True)
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
            with open(f'{tmp_path}/manifest.json', 'w') as json_file:
                json.dump(m, json_file, indent=None, separators=(',', ':'))
            return

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


    def export_items(self):

        def export_file():
            now = datetime.now().strftime('%Y-%m-%d')
            if self.combo_category.currentText() == _('Highlights'):
                return QFileDialog.getSaveFileName(self, _('Export file'), f'{self.working_dir}/JWL_{category}_{now}.txt', _('Text files')+' (*.txt)')[0]
            else:
                return QFileDialog.getSaveFileName(self, _('Export file'), f'{self.working_dir}/JWL_{category}_{now}.xlsx', _('MS Excel files')+' (*.xlsx);;'+_('Text files')+' (*.txt)')[0]

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

        def export_annotations():

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
                for row in cur.execute(sql):
                    item = {
                        'LABEL': row[0],
                        'VALUE': row[1] or '* '+_('NO TEXT')+' *',
                        'DOC': row[2],
                        'PUB': row[4]
                    }
                    item['VALUE'] = item['VALUE'].rstrip()
                    if row[3] > 10000000:
                        item['ISSUE'] = row[3]
                    else:
                        item['ISSUE'] = None
                    item_list.append(item)

            get_annotations()
            if xlsx:
                fields = ['PUB', 'ISSUE', 'DOC', 'LABEL', 'VALUE']
                create_xlsx(fields)
            else:
                with open(fname, 'w', encoding='utf-8') as file:
                    file.write(export_header('{ANNOTATIONS}'))
                    for row in item_list:
                        iss = '{ISSUE='+str(row['ISSUE'])+'}' if row['ISSUE'] else ''
                        txt = '\n==={PUB='+row['PUB']+'}'+iss+'{DOC='+str(row['DOC'])+'}{LABEL='+row['LABEL']+'}===\n'+row['VALUE']
                        file.write(txt)
                    file.write('\n==={END}===')

        def export_highlights():
            with open(fname, 'w', encoding='utf-8') as file:
                file.write(export_header('{HIGHLIGHTS}'))
                for row in cur.execute(f'SELECT b.BlockType, b.Identifier, b.StartToken, b.EndToken, u.ColorIndex, u.Version, l.BookNumber, l.ChapterNumber, l.DocumentId, l.IssueTagNumber, l.KeySymbol, l.MepsLanguage, l.Type FROM UserMark u JOIN Location l USING (LocationId), BlockRange b USING (UserMarkId) WHERE BlockRangeId IN {items};'):
                    file.write(f'\n{row[0]}')
                    for item in range(1,13):
                        file.write(f',{row[item]}')
                    item_list.append(None)

        def export_notes():

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
                        b.EndToken
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
                for row in cur.execute(sql):
                    item = {
                        'TYPE': row[0],
                        'TITLE': row[1],
                        'NOTE': row[2] or '',
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
                        'COLOR': row[14] or 0
                    }
                    item['NOTE'] = item['NOTE'].rstrip()
                    if row[15]:
                        item['RANGE'] = f'{row[15]}-{row[16]}'
                    else:
                        item['RANGE'] = None
                    if 'T' not in item['MODIFIED']:
                        item['MODIFIED'] = item['MODIFIED'][:10] + 'T00:00:00'
                    if 'T' not in item['CREATED']:
                        item['CREATED'] = item['CREATED'][:10] + 'T00:00:00'
                    if item['TYPE'] == 1 and item['DOC']:
                        if item['BLOCK']:
                            par = f"&par={item['BLOCK']}"
                            item['VS'] = None
                        else:
                            par = ''
                        item['Link'] = f"https://www.jw.org/finder?wtlocale={item['LANG']}&docid={item['DOC']}{par}"
                        if row[9] > 10000000:
                            item['ISSUE'] = row[9]
                        else:
                            item['ISSUE'] = None
                    elif item['TYPE'] > 0 or (item['TYPE'] == 0 and item['PUB'] != None):
                        if not item['VS']:
                            item['VS'] = 0
                        item['Reference'] = str(item['BK']).zfill(2) + str(item['CH']).zfill(3) + str(item['VS']).zfill(3)
                        if item['TYPE'] == 1: # Note in Bible book name
                            item['VS'] = None
                        else:
                            item['BLOCK'] = None
                        if not item['HEADING']:
                            item['HEADING'] = f"{bible_books[item['BK']]} {item['CH']}"
                        elif ':' in item['HEADING']:
                            item['HEADING'] = regex.match(r'(.*?):', item['HEADING']).group(1)
                        item['Link'] = f"https://www.jw.org/finder?wtlocale={item['LANG']}&pub={item['PUB']}&bible={item['Reference']}"
                    else:
                        item['Link'] = None
                    item_list.append(item)

            get_notes()
            if xlsx:
                fields = ['CREATED', 'MODIFIED', 'TAGS', 'COLOR', 'RANGE', 'LANG', 'PUB', 'BK', 'CH', 'VS', 'Reference', 'ISSUE', 'DOC', 'BLOCK', 'HEADING', 'Link', 'TITLE', 'NOTE']
                create_xlsx(fields)
            else:
                with open(fname, 'w', encoding='utf-8') as file:
                    file.write(export_header('{NOTES=}'))
                    for row in item_list:
                        tags = row['TAGS'].replace(' | ', '|')
                        col = str(row['COLOR']) or '0'
                        rng = row['RANGE'] or ''
                        hdg = ('{HEADING='+row['HEADING']+'}') if row['HEADING'] != '' else ''
                        lng = str(row['LANG'])
                        txt = '\n==={CREATED='+row['CREATED']+'}{MODIFIED='+row['MODIFIED']+'}{TAGS='+tags+'}'
                        if row.get('BK'):
                            bk = str(row['BK'])
                            ch = str(row['CH'])
                            if row.get('VS'):
                                vs = '{VS='+str(row['VS'])+'}'
                            else:
                                vs = ''
                            if row.get('BLOCK'):
                                blk = '{BLOCK='+str(row['BLOCK'])+'}'
                            else:
                                blk = ''
                            txt += '{LANG='+lng+'}{PUB='+row['PUB']+'}{BK='+bk+'}{CH='+ch+'}'+vs+blk+'{Reference='+row['Reference']+'}'+hdg+'{COLOR='+col+'}'
                            if row.get('RANGE'):
                                txt += '{RANGE='+rng+'}'
                            if row.get('DOC'):
                                txt += '{DOC=0}'
                        elif row.get('DOC'):
                            doc = str(row['DOC']) or ''
                            iss = '{ISSUE='+str(row['ISSUE'])+'}' if row['ISSUE'] else ''
                            blk = str(row['BLOCK']) or ''
                            txt += '{LANG='+lng+'}{PUB='+row['PUB']+'}'+iss+'{DOC='+doc+'}{BLOCK='+blk+'}'+hdg+'{COLOR='+col+'}'
                            if row.get('RANGE'):
                                txt += '{RANGE='+rng+'}'
                        txt += '===\n'+row['TITLE']+'\n'+row['NOTE']
                        file.write(txt)
                    file.write('\n==={END}===')

        category = self.combo_category.currentText()
        fname = export_file()
        if fname == '':
            self.statusBar.showMessage(' '+_('NOT exported!'), 3500)
            return
        current_archive = Path(fname).name
        item_list = []
        if Path(fname).suffix == '.xlsx':
            xlsx = True
        else:
            xlsx = False
        try:
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
            cur = con.cursor()
            items = str(self.list_selected()).replace('[', '(').replace(']', ')')
            if category == _('Highlights'):
                export_highlights()
            elif category == _('Notes'):
                export_notes()
            elif category == _('Annotations'):
                export_annotations()
            cur.close()
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
                        cur.execute('ROLLBACK;')
                        return 0
                df = pd.DataFrame(items, columns=['PUB', 'ISSUE', 'DOC', 'LABEL', 'VALUE'])
                return df

            def update_db(df):

                def add_location(attribs):
                    cur.execute(f'INSERT INTO Location (DocumentId, IssueTagNumber, KeySymbol, MepsLanguage, Type) SELECT ?, ?, ?, NULL, 0 WHERE NOT EXISTS (SELECT 1 FROM Location WHERE DocumentId = ? AND IssueTagNumber = ? AND KeySymbol = ? AND MepsLanguage IS NULL AND Type = 0);', (attribs['DOC'], attribs['ISSUE'], attribs['PUB'], attribs['DOC'], attribs['ISSUE'], attribs['PUB']))
                    result = cur.execute(f'SELECT LocationId FROM Location WHERE DocumentId = ? AND IssueTagNumber = ? AND KeySymbol = ? AND MepsLanguage IS NULL AND Type = 0;', (attribs['DOC'], attribs['ISSUE'], attribs['PUB'])).fetchone()
                    return result[0]

                df['ISSUE'].fillna(0, inplace=True)
                count = 0
                for i, row in df.iterrows():
                    try:
                        count += 1
                        location_id = add_location(row)
                        if cur.execute(f'SELECT * FROM InputField WHERE LocationId = ? AND TextTag = ?;', (location_id, row['LABEL'])).fetchone():
                            cur.execute(f'UPDATE InputField SET Value = ? WHERE LocationId = ? AND TextTag = ?;', (row['VALUE'], location_id, row['LABEL']))
                        else:
                            cur.execute(f'INSERT INTO InputField (LocationId, TextTag, Value) VALUES (?, ?, ?);', (location_id,row['LABEL'], row['VALUE']))
                    except:
                        QMessageBox.critical(None, _('Error!'), _('Error on import!\n\nFaulting entry')+f': #{count}', QMessageBox.Abort)
                        cur.execute('ROLLBACK;')
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
                    cur.execute('INSERT INTO Location (KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Type) SELECT ?, ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ?);', (attribs[10], attribs[11], attribs[6], attribs[7], attribs[12], attribs[10], attribs[11], attribs[6], attribs[7]))
                    result = cur.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ?;', (attribs[10], attribs[11], attribs[6], attribs[7])).fetchone()
                    return result[0]

                def add_publication_location(attribs):
                    cur.execute('INSERT INTO Location (IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Type) SELECT ?, ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = ?);', (attribs[9], attribs[10], attribs[11], attribs[8], attribs[12], attribs[10], attribs[11], attribs[9], attribs[8], attribs[12]))
                    result = cur.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = ?;', (attribs[10], attribs[11], attribs[9], attribs[8], attribs[12])).fetchone()
                    return result[0]

                def add_usermark(attribs, location_id):
                    unique_id = uuid.uuid1()
                    cur.execute(f"INSERT INTO UserMark (ColorIndex, LocationId, StyleIndex, UserMarkGuid, Version) VALUES (?, ?, 0, '{unique_id}', ?);", (attribs[4], location_id, attribs[5]))
                    usermark_id = cur.execute(f"SELECT UserMarkId FROM UserMark WHERE UserMarkGuid = '{unique_id}';").fetchone()[0]
                    result = cur.execute(f'SELECT * FROM BlockRange JOIN UserMark USING (UserMarkId) WHERE Identifier = {attribs[1]} AND LocationId = {location_id};')
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
                    cur.execute(f'DELETE FROM BlockRange WHERE BlockRangeId IN {block};')
                    cur.execute(f'INSERT INTO BlockRange (BlockType, Identifier, StartToken, EndToken, UserMarkId) VALUES (?, ?, ?, ?, ?);', (attribs[0], attribs[1], ns, ne, usermark_id))
                    return

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
                            cur.execute('ROLLBACK;')
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
                    results = len(cur.execute(f"SELECT NoteId FROM Note WHERE Title GLOB '{title_char}*';").fetchall())
                    if results < 1:
                        return
                    answer = QMessageBox.warning(None, _('Warning'), f'{results} '+_('notes starting with')+f' "{title_char}" '+_('WILL BE DELETED before importing.\n\nProceed with deletion? (NO to skip)'), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                    if answer == QMessageBox.Yes:
                        cur.execute(f"DELETE FROM Note WHERE Title GLOB '{title_char}*';")

                line = import_file.readline()
                m = regex.search('{NOTES=(.?)}', line)
                if m:
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
                        cur.execute('ROLLBACK;')
                        return 0
                df = pd.DataFrame(items, columns=['CREATED', 'MODIFIED', 'TAGS', 'COLOR', 'RANGE', 'LANG', 'PUB', 'BK', 'CH', 'VS', 'ISSUE', 'DOC', 'BLOCK', 'HEADING', 'TITLE', 'NOTE'])
                return df

            def update_db(df):

                def add_scripture_location(attribs):
                    cur.execute('INSERT INTO Location (KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Title, Type) SELECT ?, ?, ?, ?, ?, 0 WHERE NOT EXISTS (SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ?);', (attribs['PUB'], attribs['LANG'], attribs['BK'], attribs['CH'], attribs['HEADING'], attribs['PUB'], attribs['LANG'], attribs['BK'], attribs['CH']))
                    result = cur.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ?;', (attribs['PUB'], attribs['LANG'], attribs['BK'], attribs['CH'])).fetchone()[0]
                    if attribs['HEADING']:
                        cur.execute('UPDATE Location SET Title = ? WHERE LocationId = ?;', (attribs['HEADING'], result))
                    return result

                def add_publication_location(attribs):
                    cur.execute('INSERT INTO Location (IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Title, Type) SELECT ?, ?, ?, ?, ?, 0 WHERE NOT EXISTS (SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = 0);', (attribs['ISSUE'], attribs['PUB'], attribs['LANG'], attribs['DOC'], attribs['HEADING'], attribs['PUB'], attribs['LANG'], attribs['ISSUE'], attribs['DOC']))
                    result = cur.execute('SELECT LocationId from Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = 0;', (attribs['PUB'], attribs['LANG'], attribs['ISSUE'], attribs['DOC'])).fetchone()
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
                    result = cur.execute(f"SELECT UserMarkId FROM UserMark JOIN BlockRange USING (UserMarkId) WHERE ColorIndex = ? AND LocationId = ? AND Identifier = ? {fields};", (attribs['COLOR'], location_id, identifier)).fetchone()
                    if result:
                        usermark_id = result[0]
                    else:
                        unique_id = uuid.uuid1()
                        cur.execute(f"INSERT INTO UserMark (ColorIndex, LocationId, StyleIndex, UserMarkGuid, Version) VALUES (?, ?, 0, '{unique_id}', 1);", (attribs['COLOR'], location_id))
                        usermark_id = cur.execute(f"SELECT UserMarkId FROM UserMark WHERE UserMarkGuid = '{unique_id}';").fetchone()[0]
                    try:
                        cur.execute(f'INSERT INTO BlockRange (BlockType, Identifier, StartToken, EndToken, UserMarkId) VALUES (?, ?, ?, ?, ?);', (block_type, identifier, ns, ne, usermark_id))
                    except:
                        pass
                    return usermark_id

                def update_note(attribs, location_id, block_type, usermark_id):

                    def process_tags(note_id, tags):
                        cur.execute(f'DELETE FROM TagMap WHERE NoteId = {note_id};')
                        for tag in str(tags).split('|'):
                            tag = tag.strip()
                            if not tag:
                                continue
                            cur.execute('INSERT INTO Tag (Type, Name) SELECT 1, ? WHERE NOT EXISTS (SELECT 1 FROM Tag WHERE Name = ?);', (tag, tag))
                            tag_id = cur.execute('SELECT TagId from Tag WHERE Name = ?;', (tag,)).fetchone()[0]
                            position = cur.execute(f'SELECT ifnull(max(Position), -1) FROM TagMap WHERE TagId = {tag_id};').fetchone()[0] + 1
                            cur.execute('INSERT Into TagMap (NoteId, TagId, Position) VALUES (?, ?, ?);', (note_id, tag_id, position))

                    if location_id:
                        result = cur.execute('SELECT Guid, LastModified, Created FROM Note WHERE LocationId = ? AND Title = ? AND BlockIdentifier = ? AND BlockType = ?;', (location_id, attribs['TITLE'], attribs['BLOCK'], block_type)).fetchone()
                    else:
                        result = cur.execute('SELECT Guid, LastModified, Created FROM Note WHERE Title = ? AND BlockType = 0;', (attribs['TITLE'],)).fetchone()
                    if result:
                        unique_id = result[0]
                        modified = attribs['MODIFIED'] if pd.notnull(attribs['MODIFIED']) else result[1]
                        created = attribs['CREATED'] if pd.notnull(attribs['CREATED']) else result[2]
                        cur.execute(f"UPDATE Note SET UserMarkId = ?, Content = ?, LastModified = ?, Created = ? WHERE Guid = '{unique_id}';", (usermark_id, attribs['NOTE'], modified, created))
                    else:
                        unique_id = uuid.uuid1()
                        created = attribs['CREATED'] if pd.notnull(attribs['CREATED']) else (attribs['MODIFIED'] if pd.notnull(attribs['MODIFIED']) else datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S'))
                        modified = attribs['MODIFIED'] if pd.notnull(attribs['MODIFIED']) else datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
                        cur.execute(f"INSERT INTO Note (Guid, UserMarkId, LocationId, Title, Content, BlockType, BlockIdentifier, LastModified, Created) VALUES ('{unique_id}', ?, ?, ?, ?, ?, ?, ?, ?);", (usermark_id, location_id, attribs['TITLE'], attribs['NOTE'], block_type, attribs['BLOCK'], modified, created))
                    note_id = cur.execute(f"SELECT NoteId from Note WHERE Guid = '{unique_id}';").fetchone()[0]
                    process_tags(note_id, attribs['TAGS'])

                df['ISSUE'].fillna(0, inplace=True)
                df['TAGS'].fillna('', inplace=True)
                df['TITLE'].fillna('', inplace=True)
                df['NOTE'].fillna('', inplace=True)
                df['COLOR'].fillna(0, inplace=True)
                count = 0
                for i, row in df.iterrows():
                    try:
                        count += 1
                        if pd.notna(row['BK']):
                            location_id = add_scripture_location(row)
                            usermark_id = add_usermark(row, location_id)
                            if pd.notna(row['BLOCK']): # Bible book title
                                block_type = 1
                            elif pd.notna(row['VS']):
                                block_type = 2
                                row['BLOCK'] = row['VS']
                            else:
                                block_type = 0
                            update_note(row, location_id, block_type, usermark_id)
                        elif pd.notna(row['DOC']):
                            location_id = add_publication_location(row)
                            usermark_id = add_usermark(row, location_id)
                            update_note(row, location_id, 1, usermark_id)
                        else:
                            update_note(row, None, 0, None)
                    except:
                        QMessageBox.critical(None, _('Error!'), _('Error on import!\n\nFaulting entry')+f': #{count}', QMessageBox.Abort)
                        cur.execute('ROLLBACK;')
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

        if not file:
            category = self.combo_category.currentText()
            if category == _('Highlights'):
                flt = _('Text files')+' (*.txt)'
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
            cur = con.cursor()
            cur.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'MEMORY'; PRAGMA foreign_keys = 'OFF'; BEGIN;")
            if category == _('Annotations'):
                count = import_annotations()
            elif category == _('Highlights'):
                count = import_highlights()
            elif category == _('Notes'):
                count = import_notes()
            cur.execute("PRAGMA foreign_keys = 'ON';")
            con.commit()
            cur.close()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        if not count:
            self.statusBar.showMessage(' '+_('NOT imported!'), 3500)
            return
        message = f' {count} '+_('items imported/updated')
        self.statusBar.showMessage(message, 3500)
        self.archive_modified()
        self.trim_db()
        self.regroup(False, message)


    def data_editor(self):
        item = int(self.sender().text())
        widget = self.viewer_items[item]
        print(item, widget.text) # testing

    def data_viewer(self):

        def init_viewer():
            window = QDialog(self)
            window.setAttribute(Qt.WA_DeleteOnClose)
            window.setWindowFlags(Qt.Window)
            window.setWindowIcon((QIcon(resource_path('res/icons/project_72.png'))))
            window.setWindowTitle(_('Data Viewer'))
            window.setMinimumSize(698, 846)
            window.resize(self.viewer_size)
            window.move(self.viewer_pos)

            layout = QVBoxLayout(window)
            toolbar = QToolBar(window)
            self.button_TXT = QAction('TXT', toolbar)
            self.button_TXT.triggered.connect(save_txt)
            toolbar.addAction(self.button_TXT)
            layout.addWidget(toolbar)

            self.grid_layout = QGridLayout()
            self.grid_layout.setAlignment(Qt.AlignTop)
            grid_box = QFrame()
            grid_box.setFrameShape(QFrame.NoFrame)
            grid_box.sizePolicy().setVerticalPolicy(QSizePolicy.MinimumExpanding)
            grid_box.setLayout(self.grid_layout)
            scroll_area = QScrollArea()
            scroll_area.setWidget(grid_box)
            scroll_area.setWidgetResizable(True)
            layout.addWidget(scroll_area)

            window.setWindowState((window.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
            window.finished.connect(viewer_closed)
            window.show()
            window.raise_()
            window.activateWindow()
            app.processEvents()
            return window

        def viewer_closed():
            self.viewer_pos = self.viewer_window.pos()
            self.viewer_size = self.viewer_window.size()
            try:
                self.viewer_window.close()
            except:
                pass

        def save_txt():
            fname = QFileDialog.getSaveFileName(self, _('Save') + ' TXT', f'{self.working_dir}/{category}.txt', _('Text files')+' (*.txt)')[0]
            if fname == '':
                self.statusBar.showMessage(' '+_('NOT saved!'), 3500)
                return
            with open(fname, 'w', encoding='utf-8') as txtfile:
                txtfile.write(self.data_viewer_txt)
                self.statusBar.showMessage(' '+_('Saved'), 3500)

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
                        n.NoteId
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
                for row in cur.execute(sql):
                    item = {
                        'TYPE': row[0],
                        'TITLE': row[1] or '* '+_('NO TITLE')+' *',
                        'NOTE': row[2].rstrip() or '',
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
                        'ID': row[16]
                    }
                    try:
                        item['LANG'] = lang_symbol[row[4]]
                    except:
                        item['LANG'] = None
                    if row[14]:
                        item['RANGE'] = f'{row[14]}-{row[15]}'
                    else:
                        item['RANGE'] = None
                    if item['TYPE'] == 1 and item['DOC']:
                        if item['BLOCK']:
                            par = f"&par={item['BLOCK']}"
                            item['VS'] = None
                        else:
                            par = ''
                        item['Link'] = f"https://www.jw.org/finder?wtlocale={item['LANG']}&docid={item['DOC']}{par}"
                        if row[9] > 10000000:
                            item['ISSUE'] = process_issue(row[9])
                    elif item['TYPE'] == 2:
                        item['BLOCK'] = None
                        if not item['HEADING']:
                            item['HEADING'] = f"{bible_books[item['BK']]} {item['CH']}:{item['VS']}"
                        elif ':' not in item['HEADING']:
                            item['HEADING'] += f":{item['VS']}"
                        script = str(item['BK']).zfill(2) + str(item['CH']).zfill(3) + str(item['VS']).zfill(3)
                        item['Link'] = f"https://www.jw.org/finder?wtlocale={item['LANG']}&pub={item['PUB']}&bible={script}"
                    else:
                        item['Link'] = None
                    item_list.append(item)

            get_notes()
            nonlocal txt
            clrs = ['#f1f1f1', '#fffce6', '#effbe6', '#e6f7ff', '#ffe6f0', '#fff0e6', '#f1eafa']
            counter = 1
            for item in item_list:
                note_text = f"<h3><b>{item['TITLE']}</b></h3>"
                txt += item['TITLE']
                if item['NOTE']:
                    note_text += item['NOTE'].replace('\n', '<br>')
                    txt += '\n' + item['NOTE']
                note_meta = ''
                if item['TAGS'] or item['PUB'] or item['Link']:
                    # note_meta += f"<hr width='90%'><small><strong><tt>{item['MODIFIED']}"
                    note_meta += f"<small><strong><tt>{item['MODIFIED']}"
                    txt += '\n__________\n' + item['MODIFIED']
                    if item['TAGS']:
                        note_meta += '&nbsp;&nbsp;&nbsp;{' + item['TAGS'] + '}'
                        txt += '\n{' + item['TAGS'] + '}'
                    if item['PUB']:
                        note_meta += f"<br><i>{item['PUB']}</i>-{item['LANG']} {item['ISSUE']}".strip()
                        txt += f"\n{item['PUB']}-{item['LANG']} {item['ISSUE']}".rstrip()
                    if item['HEADING']:
                        note_meta += f"&nbsp;&mdash;&nbsp;{item['HEADING']}"
                        txt += ' — ' + item['HEADING']
                    if item['Link']:
                        lnk = item['Link']
                        note_meta += f"<br><a href='{lnk}' style='color: #7575a3; text-decoration: none'>{lnk}</a>"
                        txt += '\n' + lnk
                    note_meta += '</tt></strong></small>'
                txt += '\n==========\n'
                note_box = ViewerItem(counter, item['ID'], clrs[item['COLOR']], note_text, note_meta)
                self.viewer_items[counter] = note_box
                note_box.expand_button.clicked.connect(self.data_editor)
                row = int((counter+1) / 2) - 1
                col = (counter+1) % 2
                try:
                    self.grid_layout.setColumnStretch(col, 1)
                    self.grid_layout.addWidget(note_box.item, row, col)
                    app.processEvents()
                except:
                    return
                counter += 1

        def show_annotations():

            def get_annotations():
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
                for row in cur.execute(sql):
                    item = {
                        'LABEL': row[0],
                        'VALUE': row[1].rstrip() or '* '+_('NO TEXT')+' *',
                        'DOC': row[2],
                        'PUB': row[4],
                        'ID': row[6]
                    }
                    if row[3] > 10000000:
                        item['ISSUE'] = process_issue(row[3])
                    else:
                        item['ISSUE'] = ''
                    item_list.append(item)

            get_annotations()
            nonlocal txt
            counter = 1
            for item in item_list:
                note_text = f"<h3><b><i>{item['PUB']}</i> {item['ISSUE']}</b></h3><h4>{item['DOC']}&nbsp;&mdash;&nbsp;{item['LABEL']}</h4>" + item['VALUE'].replace('\n', '<br>')
                note_meta = None
                note_box = ViewerItem(counter, item['ID'], '#f1f1f1', note_text, note_meta)
                self.viewer_items[counter] = note_box
                note_box.expand_button.clicked.connect(self.data_editor)
                row = int((counter+1) / 2) - 1
                col = (counter+1) % 2
                try:
                    self.grid_layout.setColumnStretch(col, 1)
                    self.grid_layout.addWidget(note_box.item, row, col)
                    app.processEvents()
                except:
                    return
                counter += 1
                txt += f"{item['PUB']} {item['ISSUE']} — {item['DOC']} — {item['LABEL']}\n{item['VALUE']}\n==========\n"

        selected = self.list_selected()
        if len(selected) > 1500:
            QMessageBox.critical(self, _('Warning'), _('You are trying to preview {} items.\nPlease select a smaller subset.').format(len(selected)), QMessageBox.Cancel)
            return
        try:
            self.viewer_window.close()
        except:
            pass
        category = self.combo_category.currentText()
        self.viewer_items = {}
        self.viewer_window = init_viewer()
        txt = ''
        item_list = []
        try:
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
            cur = con.cursor()
            items = str(selected).replace('[', '(').replace(']', ')')
            if category == _('Notes'):
                show_notes()
            else:
                show_annotations()
            cur.close()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        self.data_viewer_txt = txt
        self.data_viewer_dict = item_list
        try:
            self.viewer_window.setWindowTitle(_('Data Viewer')+f': {len(selected)} {category}')
        except:
            pass
        app.processEvents()


    def add_favorite(self):

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
            cur.execute("INSERT INTO Tag (Type, Name) SELECT 0, 'Favorite' WHERE NOT EXISTS (SELECT 1 FROM Tag WHERE Type = 0 AND Name = 'Favorite');")
            tag_id = cur.execute('SELECT TagId FROM Tag WHERE Type = 0;').fetchone()[0]
            position = cur.execute(f'SELECT max(Position) FROM TagMap WHERE TagId = {tag_id};').fetchone()
            if position[0] != None:
                return tag_id, position[0] + 1
            else:
                return tag_id, 0

        def add_location(symbol, language):
            cur.execute('INSERT INTO Location (IssueTagNumber, KeySymbol, MepsLanguage, Type) SELECT 0, ?, ?, 1 WHERE NOT EXISTS (SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = 0 AND Type = 1);', (symbol, language, symbol, language))
            result = cur.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = 0 AND Type = 1;', (symbol, language)).fetchone()
            return result[0]

        def add_favorite():
            pub, lng = add_dialog()
            if pub == ' ' or lng == ' ':
                return False, ' '+_('Nothing added!')
            language = int(favorites.loc[(favorites.Short == pub) & (favorites.Lang == lng), 'Language'].values[0])
            publication = favorites.loc[(favorites.Short == pub) & (favorites.Lang == lng), 'Symbol'].values[0]
            location = add_location(publication, language)
            result = cur.execute(f"SELECT TagMapId FROM TagMap WHERE LocationId = {location} AND TagId = (SELECT TagId FROM Tag WHERE Name = 'Favorite');").fetchone()
            if result:
                return False, ' '+_('Favorite for "{}" in {} already exists.').format(pub, lng)
            tag_id, position = tag_positions()
            cur.execute('INSERT INTO TagMap (LocationId, TagId, Position) VALUES (?, ?, ?);', (location, tag_id, position))
            return True, ' '+_('Added "{}" in {}').format(pub, lng)

        con = sqlite3.connect(f'{tmp_path}/{db_name}')
        cur = con.cursor()
        cur.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF'; PRAGMA foreign_keys = 'OFF'; BEGIN;")
        try:
            result, message = add_favorite()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()
        cur.execute("PRAGMA foreign_keys = 'ON';")
        con.commit()
        cur.close()
        con.close()
        self.statusBar.showMessage(message, 3500)
        if result:
            self.archive_modified()
            self.regroup(False, message)

    def delete_items(self):

        def delete(table, field):
            return cur.execute(f'DELETE FROM {table} WHERE {field} IN {items};').rowcount

        def delete_items():
            if category == _('Bookmarks'):
                return delete('Bookmark', 'BookmarkId')
            elif category == _('Favorites'):
                return delete('TagMap', 'TagMapId')
            elif category == _('Highlights'):
                return delete('BlockRange', 'BlockRangeId')
            elif category == _('Notes'):
                return delete('Note', 'NoteId')
            elif category == _('Annotations'):
                return delete('InputField', 'LocationId')

        reply = QMessageBox.warning(self, _('Delete'), _('Are you sure you want to\nDELETE these {} items?').format(self.selected_items), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        self.statusBar.showMessage(' '+_('Deleting. Please wait…'))
        app.processEvents()
        category = self.combo_category.currentText()
        try:
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
            cur = con.cursor()
            cur.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF'; PRAGMA foreign_keys = 'OFF'; BEGIN;")
            items = str(self.list_selected()).replace('[', '(').replace(']', ')')
            result = delete_items()
            cur.execute("PRAGMA foreign_keys = 'ON';")
            con.commit()
            cur.close()
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
            for title, item in cur.execute('SELECT Title, LocationId FROM Location;').fetchall():
                if title:
                    title = obscure_text(title)
                    cur.execute('UPDATE Location SET Title = ? WHERE LocationId = ?;', (title, item))

        def obscure_annotations():
            for content, item in cur.execute('SELECT Value, TextTag FROM InputField;').fetchall():
                if content:
                    content = obscure_text(content)
                    cur.execute('UPDATE InputField SET Value = ? WHERE TextTag = ?;', (content, item))

        def obscure_bookmarks():
            for title, content, item  in cur.execute('SELECT Title, Snippet, BookmarkId FROM Bookmark;').fetchall():
                if title:
                    title = obscure_text(title)
                if content:
                    content = obscure_text(content)
                    cur.execute('UPDATE Bookmark SET Title = ?, Snippet = ? WHERE BookmarkId = ?;', (title, content, item))
                else:
                    cur.execute('UPDATE Bookmark SET Title = ? WHERE BookmarkId = ?;', (title, item))

        def obscure_notes():
            for title, content, item in cur.execute('SELECT Title, Content, NoteId FROM Note;').fetchall():
                if title:
                    title = obscure_text(title)
                if content:
                    content = obscure_text(content)
                cur.execute('UPDATE Note SET Title = ?, Content = ? WHERE NoteId = ?;', (title, content, item))

        reply = QMessageBox.warning(self, _('Mask'), _('Are you sure you want to\nMASK all text fields?'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        self.statusBar.showMessage(' '+_('Masking. Please wait…'))
        app.processEvents()
        words = ['obscured', 'yada', 'bla', 'gibberish', 'børk']
        m = regex.compile(r'\p{L}')
        try:
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
            cur = con.cursor()
            cur.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF'; BEGIN;")
            obscure_annotations()
            obscure_bookmarks()
            obscure_notes()
            obscure_locations()
            con.commit()
            cur.close()
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


    def reindex_db(self):

        def init_progress():
            pd = QProgressDialog(_('Please wait…'), None, 0, 14)
            pd.setWindowModality(Qt.WindowModal)
            pd.setWindowTitle('Reindexing')
            pd.setWindowFlag(Qt.FramelessWindowHint)
            pd.setModal(True)
            pd.setMinimumDuration(0)
            return pd

        def make_table(table):
            cur.executescript(f'CREATE TABLE CrossReference (Old INTEGER, New INTEGER PRIMARY KEY AUTOINCREMENT); INSERT INTO CrossReference (Old) SELECT {table}Id FROM {table};')

        def update_table(table, field):
            app.processEvents()
            cur.executescript(f'UPDATE {table} SET {field} = (SELECT -New FROM CrossReference WHERE CrossReference.Old = {table}.{field}); UPDATE {table} SET {field} = abs({field});')
            progress_dialog.setValue(progress_dialog.value() + 1)

        def reindex_notes():
            make_table('Note')
            update_table('Note', 'NoteId')
            update_table('TagMap', 'NoteId')
            cur.execute('DROP TABLE CrossReference;')

        def reindex_highlights():
            make_table('UserMark')
            update_table('UserMark', 'UserMarkId')
            update_table('Note', 'UserMarkId')
            update_table('BlockRange', 'UserMarkId')
            cur.execute('DROP TABLE CrossReference;')

        def reindex_tags():
            make_table('TagMap')
            update_table('TagMap', 'TagMapId')
            cur.execute('DROP TABLE CrossReference;')

        def reindex_ranges():
            make_table('BlockRange')
            update_table('BlockRange', 'BlockRangeId')
            cur.execute('DROP TABLE CrossReference;')

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
            cur.execute('DROP TABLE CrossReference;')

        reply = QMessageBox.information(self, _('Reindex'), _('This may take a few seconds.\nProceed?'), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.No:
            return
        self.trim_db()
        self.statusBar.showMessage(' '+_('Reindexing. Please wait…'))
        app.processEvents()
        progress_dialog = init_progress()
        try:
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
            cur = con.cursor()
            cur.executescript("PRAGMA temp_store = 2; PRAGMA journal_mode = 'OFF'; PRAGMA foreign_keys = 'OFF'; BEGIN;")
            reindex_notes()
            reindex_highlights()
            reindex_tags()
            reindex_ranges()
            reindex_locations()
            cur.executescript("PRAGMA foreign_keys = 'ON'; VACUUM;")
            con.commit()
            cur.close()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.progress_dialog.close()
            self.clean_up()
            sys.exit()
        message = ' '+_('Reindexed successfully')
        self.statusBar.showMessage(message, 3500)
        self.archive_modified()
        self.regroup(False, message)

    def trim_db(self):
        try:
            con = sqlite3.connect(f'{tmp_path}/{db_name}')
            cur = con.cursor()
            sql = """
                PRAGMA temp_store = 2;
                PRAGMA journal_mode = 'OFF';
                PRAGMA foreign_keys = 'OFF';

                DELETE FROM Note WHERE (Title IS NULL OR Title = '')
                AND (Content IS NULL OR Content = '');

                DELETE FROM TagMap WHERE NoteId IS NOT NULL AND NoteId
                NOT IN (SELECT NoteId FROM Note);
                DELETE FROM Tag WHERE TagId NOT IN (SELECT TagId FROM TagMap);

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

                PRAGMA foreign_keys = 'ON';
                VACUUM;
                """
            cur.executescript(sql)
            con.commit()
            cur.close()
            con.close()
        except Exception as ex:
            self.crash_box(ex)
            self.clean_up()
            sys.exit()


    def clean_up(self):
        shutil.rmtree(tmp_path, ignore_errors=True)
        self.settings.setValue('Main_Window/pos', self.pos())
        self.settings.setValue('Main_Window/size', self.size())
        self.settings.setValue('Viewer/pos', self.viewer_pos)
        self.settings.setValue('Viewer/size', self.viewer_size)


class ViewerItem(QWidget):
    def __init__(self, i, idx, color, text, meta):
        super().__init__()
        self.idx = idx
        self.text = text
        self.meta = meta

        self.item = QFrame()
        self.item.setFixedHeight(250)
        self.item.setFrameShape(QFrame.Panel)
        self.item.setStyleSheet(f"background-color: {color}")

        text_box = QTextEdit(self.item)
        text_box.setReadOnly(True)
        text_box.setContentsMargins(1, 1, 1, 2)
        text_box.setFrameShape(QFrame.NoFrame)
        palette = text_box.palette()
        palette.setColor(text_box.foregroundRole(), '#3d3d5c')
        text_box.setPalette(palette)
        text_box.sizePolicy().setHorizontalPolicy(QSizePolicy.MinimumExpanding)
        text_box.setText(text)

        if self.meta:
            meta_box = QLabel(self.item)
            meta_box.setWordWrap(True)
            meta_box.setContentsMargins(1, 2, 1, 1)
            meta_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            palette = meta_box.palette()
            palette.setColor(meta_box.foregroundRole(), '#7575a3')
            meta_box.setPalette(palette)
            meta_box.setTextFormat(Qt.RichText)
            meta_box.setText(meta)

        self.expand_button = QPushButton(text=str(i), parent=self.item)
        self.expand_button.setFixedSize(30, 30)
        self.expand_button.setContentsMargins(0, 0, 0, 0)
        self.expand_button.setIcon(QPixmap(resource_path('res/icons/icons8-expand-30.png')))
        self.expand_button.setIconSize(QSize(24, 24))
        self.expand_button.setStyleSheet("QPushButton { background-color: transparent; font-size: 1px; border: 0px; color: transparent; }")


        layout = QGridLayout(self.item)
        layout.setSpacing(0)
        layout.addWidget(text_box, 0 , 0, 1, 0)
        if self.meta:
            layout.addWidget(meta_box, 1, 0)
        layout.addWidget(self.expand_button, 1 , 1, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    global translator
    translator = {}
    translator[lang] = QTranslator()
    translator[lang].load(resource_path(f'res/locales/UI/qt_{lang}.qm'))
    app.installTranslator(translator[lang])
    font = QFont()
    font.setPixelSize(16)
    app.setFont(font)
    win = Window()
    win.show()
    sys.exit(app.exec())
