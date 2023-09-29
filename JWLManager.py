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
VERSION = 'v3.0.0-beta3'

import argparse, csv, gettext, json, os, regex, shutil, sqlite3, sys, uuid
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
    global available_languages
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
    global tr
    tr = {}
    localedir = PROJECT_PATH / 'res/locales/'

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
        base_path = PROJECT_PATH 
    return os.path.join(base_path, relative_path)

def read_res(lng):

    def load_books(lng):
        for row in cur.execute(f"SELECT Number, Name FROM BibleBooks WHERE Language = {lng};").fetchall():
            books[row[0]] = row[1]

    def load_languages():
        for row in cur.execute('SELECT Language, Name, Code, Symbol FROM Languages;').fetchall():
            lang_by_num[row[0]] = (row[1], row[3])
            lang_by_sym[row[3]] = row[0]
            if row[2] == lng:
                ui_lang = row[0]
        return ui_lang

    def load_pubs(lng):
        types = {}
        for row in cur.execute(f"SELECT Type, [Group] FROM Types WHERE Language = {lng};").fetchall():
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
        favs['Lang'] = favs['Language'].map(lang_by_num)
        pubs = pubs[pubs['Language'] == lng]
        pubs = pubs.drop(['Language', 'Favorite'], axis=1) # Delete columns
        return favs, pubs

    global _, books, favorites, lang_by_num, lang_by_sym, publications
    _ = tr[lng].gettext
    lang_by_num = {}
    lang_by_sym = {}
    books = {}
    con = sqlite3.connect(PROJECT_PATH / 'res/resources.db')
    cur = con.cursor()
    ui_lang = load_languages()
    load_books(ui_lang)
    favorites, publications = load_pubs(ui_lang)
    cur.close()
    con.close()

PROJECT_PATH = Path(__file__).resolve().parent
tmp_path = mkdtemp(prefix='JWLManager_')
db_name = 'userData.db'

lang = get_language()
read_res(lang)


#### Main app classes

class Window(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setAcceptDrops(True)
        self.status_label = QLabel()
        self.statusBar.addPermanentWidget(self.status_label, 0)
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.sortByColumn(1, Qt.DescendingOrder)
        self.treeWidget.setExpandsOnDoubleClick(False)
        self.treeWidget.setColumnWidth(0, 500)
        self.treeWidget.setColumnWidth(1, 30)
        self.button_add.setVisible(False)
        self.set_vars()
        self.center()
        self.init_windows()
        self.connect_signals()
        self.new_file()

    def set_vars(self):
        self.total.setText('')
        self.int_total = 0
        self.modified = False
        self.title_format = 'short'
        self.save_filename = ''
        self.current_archive = ''
        self.working_dir = Path.home()
        self.lang = lang
        for item in self.menuLanguage.actions():
            if item.toolTip() not in available_languages.keys():
                item.setVisible(False)
            if item.toolTip() == self.lang:
                item.setChecked(True)
        self.current_data = []


    def center(self):
        qr = self.frameGeometry()
        cp = QWidget.screen(self).availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def init_windows(self):

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
            text.setMarkdown(open(self.resource_path('res/HELP.md'), encoding='utf-8').read())
            layout = QHBoxLayout(self.help_window)
            layout.addWidget(text)
            self.help_window.setLayout(layout)

        def init_viewer():
            self.viewer_window = QDialog(self)
            self.viewer_window.setWindowFlags(Qt.Window)
            self.viewer_window.setWindowIcon((QIcon(self.resource_path('res/icons/project_72.png'))))
            self.viewer_window.setWindowTitle(_('Data Viewer'))
            self.viewer_window.resize(640, 812)
            self.viewer_window.move(50, 50)
            self.viewer_window.setMinimumSize(500, 500)
            self.viewer_text = QTextEdit(self.viewer_window)
            toolbar = QToolBar()
            self.button_CSV = QAction('CSV', toolbar)
            self.button_TXT = QAction('TXT', toolbar)
            self.button_XLS = QAction('MS Excel', toolbar)
            toolbar.addAction(self.button_CSV)
            toolbar.addAction(self.button_TXT)
            toolbar.addAction(self.button_XLS)
            layout = QVBoxLayout(self.viewer_window)
            layout.addWidget(toolbar)
            layout.addWidget(self.viewer_text)
            self.viewer_window.setLayout(layout)

        init_help()
        init_viewer()


    def connect_signals(self):
        self.actionQuit.triggered.connect(self.close)
        self.actionHelp.triggered.connect(self.help_box)
        self.actionAbout.triggered.connect(self.about_box)
        self.actionNew.triggered.connect(self.new_file)
        self.actionOpen.triggered.connect(self.load_file)
        self.actionQuit.triggered.connect(self.clean_up)
        self.actionSave.triggered.connect(self.save_file)
        self.actionSave_As.triggered.connect(self.save_as_file)
        self.actionObscure.triggered.connect(self.obscure)
        self.actionReindex.triggered.connect(self.reindex)
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
        self.button_export.clicked.connect(self.export)
        self.button_import.clicked.connect(self.import_file)
        self.button_add.clicked.connect(self.add_favorite)
        self.button_delete.clicked.connect(self.delete)
        self.button_view.clicked.connect(self.view)
        self.button_CSV.triggered.connect(self.export_csv)
        self.button_XLS.triggered.connect(self.export_xlsx)
        self.button_TXT.triggered.connect(self.export_txt)

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
        super().changeEvent(event)


    def change_language(self):
        changed = False
        for item in self.langChoices.actions():
            if item.isChecked() and (self.lang != item.toolTip()):
                app.removeTranslator(translator[self.lang])
                self.lang = item.toolTip()
                changed = True
        if not changed:
            return
        read_res(self.lang)
        if self.lang not in translator.keys():
            translator[self.lang] = QTranslator()
            translator[self.lang].load(resource_path(f'res/locales/UI/qt_{self.lang}.qm'))
        app.installTranslator(translator[self.lang])
        app.processEvents()

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


    def switchboard(self, selection):
        if selection == _('Notes'):
            self.disable_options([], False, True, True, True)
        elif selection == _('Highlights'):
            self.disable_options([4], False, True, True, False)
        elif selection == _('Bookmarks'):
            self.disable_options([4,5], False, False, False, False)
        elif selection == _('Annotations'):
            self.disable_options([2,4,5], False, True, True, True)
        elif selection == _('Favorites'):
            self.disable_options([4,5], True, False, False, False)
        self.regroup()

    def disable_options(self, lst=[], add=False, exp=False, imp=False, view=False):
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
                self.combo_grouping.setCurrentText(_('Title'))
        self.combo_grouping.blockSignals(False)

    def regroup(self, changed=False, message=''):
        if not changed:
            self.current_data = []
        if message:
            msg = message + '… '
        else:
            msg = ' '
        self.statusBar.showMessage(msg+_('Processing…'))
        app.processEvents()
        start = time()
        tree = ConstructTree(self, self.treeWidget, books, publications, lang_by_num, self.combo_category.currentText(), self.combo_grouping.currentText(), self.title_format, self.current_data)
        delta = 3500 - (time()-start) * 1000
        if message:
            self.statusBar.showMessage(msg, delta)
        else:
            self.statusBar.showMessage('')
        app.processEvents()
        if tree.aborted:
            self.clean_up()
            sys.exit()
        self.leaves = tree.leaves
        self.current_data = tree.current
        self.int_total = tree.total
        self.total.setText(f'**{tree.total:,}**')
        self.selected.setText('**0**')

    def tree_selection(self):

        def recurse(parent):
            for i in range(parent.childCount()):
                child = parent.child(i)
                grand_children = child.childCount()
                if grand_children > 0:
                    recurse(child)
                else: 
                    if child.checkState(0) == Qt.Checked:
                        checked_leaves.append(child)

        checked_leaves = []
        self.selected_items = 0
        recurse(self.treeWidget.invisibleRootItem())
        for item in checked_leaves:
            self.selected_items += len(self.leaves[item])
        self.selected.setText(f'**{self.selected_items:,}**')
        self.button_delete.setEnabled(self.selected_items)
        self.button_view.setEnabled(self.selected_items and self.combo_category.currentText() in (_('Notes'), _('Annotations')))
        self.button_export.setEnabled(self.selected_items and self.combo_category.currentText() in (_('Notes'), _('Highlights'), _('Annotations')))


    def help_box(self):
        self.help_window.setWindowState((self.help_window.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.help_window.finished.connect(self.help_window.hide())
        self.help_window.show()
        self.help_window.raise_()
        self.help_window.activateWindow()

    def about_box(self):
        year = f'MIT ©{datetime.now().year}'
        owner = 'Eryk J.'
        web = 'https://github.com/erykjj/jwlmanager'
        contact = b'\x69\x6E\x66\x69\x6E\x69\x74\x69\x40\x69\x6E\x76\x65\x6E\x74\x61\x74\x69\x2E\x6F\x72\x67'.decode('utf-8')
        text = f'<h2 style="text-align: center;"><span style="color: #800080;">{APP}</span></h2><h4 style="text-align: center;">{VERSION}</h4><p style="text-align: center;"><small>{year} {owner}</small></p><p style="text-align: center;"><a href="mail-to:{contact}"><em>{contact}</em></a></p><p style="text-align: center;"><span style="color: #666699;"><a style="color: #666699;" href="{web}"><small>{web}</small></a></span></p>'
        dialog = QDialog(self)
        outer = QVBoxLayout()
        top = QHBoxLayout()
        icon = QLabel(dialog)
        icon.setPixmap(QPixmap(self.resource_path('res/icons/project_72.png')))
        icon.setGeometry(12,12,72,72)
        icon.setAlignment(Qt.AlignTop)
        top.addWidget(icon)
        label = QLabel(dialog)
        label.setText(text)
        label.setOpenExternalLinks(True)
        top.addWidget(label)
        button = QDialogButtonBox(QDialogButtonBox.Ok)
        button.accepted.connect(dialog.accept)
        bottom = QHBoxLayout()
        bottom.addWidget(button)
        outer.addLayout(top)
        outer.addLayout(bottom)
        dialog.setLayout(outer)
        dialog.setWindowFlag(Qt.FramelessWindowHint)
        dialog.exec()


    def new_file(self):
        if self.modified:
            reply = QMessageBox.question(self, _('Save'), _('Save current archive?'), 
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
                QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return
        self.status_label.setStyleSheet('color: black;')
        self.status_label.setText('* '+_('NEW ARCHIVE')+' *  ')
        global db_name
        try:
            os.remove(f'{tmp_path}/manifest.json')
            os.remove(f'{tmp_path}/{db_name}')
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
            reply = QMessageBox.question(self, _('Save'), _('Save current archive?'), QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return
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
        self.actionSave_As.setEnabled(True)
        self.actionCollapse_All.setEnabled(True)
        self.actionExpand_All.setEnabled(True)
        self.actionSelect_All.setEnabled(True)
        self.actionUnselect_All.setEnabled(True)
        self.menuTitle_View.setEnabled(True)
        self.selected.setText('**0**')
        self.switchboard(self.combo_category.currentText())


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
                self.import_file(file, _('Annotations'))
            elif header == r'{HIGHLIGHTS}':
                self.import_file(file, _('Highlights'))
            elif regex.search('{TITLE=', header):
                self.import_file(file, _('Notes'))
            else:
                QMessageBox.warning(self, _('Error'), _('File "{}" not recognized!').format(file), QMessageBox.Cancel)
        else:
            QMessageBox.warning(self, _('Error'), _('File "{}" not recognized!').format(file), QMessageBox.Cancel)


    def save_file(self):
        if self.save_filename == '':
            return self.save_as_file()
        else:
            self.zipfile()

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
        self.zipfile()

    def zipfile(self):

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


    def export(self):

        def export_file():
            fname = ()
            now = datetime.now().strftime('%Y-%m-%d')
            fname = QFileDialog.getSaveFileName(self, _('Export file'), f'{self.working_dir}/JWL_{self.combo_category.currentText()}_{now}.txt', _('Text files')+' (*.txt)')
            return fname

        reply = QMessageBox.question(self, _('Export'), f'{self.selected_items} '+_('items will be EXPORTED. Proceed?'), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.No:
            return
        selected = []
        it = QTreeWidgetItemIterator(self.treeWidget, QTreeWidgetItemIterator.Checked)
        for item in it:
            index = item.value()
            if index in self.leaves:
                for i in self.leaves[index]:
                    selected.append(i)
        fname = export_file()
        if fname[0] == '':
            self.statusBar.showMessage(' '+_('NOT exported!'), 3500)
            return
        self.working_dir = Path(fname[0]).parent
        fn = ExportItems(self.combo_category.currentText(), selected, fname[0],
            Path(self.current_archive).stem)
        if fn.aborted:
            self.clean_up()
            sys.exit()
        self.statusBar.showMessage(' '+_('Items exported'), 3500)

    def import_file(self, file='', category = ''):
        reply = QMessageBox.warning(self, _('Import'), _('Make sure your import file is UTF-8 encoded and properly formatted.\n\nImporting will modify the archive. Proceed?'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        if not file:
            fname = QFileDialog.getOpenFileName(self, _('Import file'), f'{self.working_dir}/', _('Import files')+' (*.txt *.xlsx)')
            if fname[0] == '':
                self.statusBar.showMessage(' '+_('NOT imported!'), 3500)
                return
            file = fname[0]
            category = self.combo_category.currentText()
        self.working_dir = Path(file).parent
        self.statusBar.showMessage(' '+_('Importing. Please wait…'))
        app.processEvents()
        if category == _('Annotations'):
            fn = ImportAnnotations(file)
        elif category == _('Highlights'):
            fn = ImportHighlights(file)
        elif category == _('Notes'):
            fn = ImportNotes(file, lang_by_sym)
        if fn.aborted:
            self.clean_up()
            sys.exit()
        if not fn.count:
            self.statusBar.showMessage(' '+_('NOT imported!'), 3500)
            return
        self.trim_db()
        message = f' {fn.count} '+_('items imported/updated')
        self.statusBar.showMessage(message, 3500)
        self.archive_modified()
        self.regroup(False, message)
        self.tree_selection()


    def view(self):
        selected = []
        it = QTreeWidgetItemIterator(self.treeWidget, QTreeWidgetItemIterator.Checked)
        for item in it:
            index = item.value()
            if index in self.leaves:
                for i in self.leaves[index]:
                    selected.append(i)
        if len(selected) > 2000:
            QMessageBox.critical(self, _('Warning'), _('You are trying to preview {} items.\nPlease select a smaller subset.').format(len(selected)), QMessageBox.Cancel)
            return
        fn = PreviewItems(self.combo_category.currentText(), selected, books, lang_by_num)
        if fn.aborted:
            self.clean_up()
            sys.exit()
        self.data_viewer_txt = fn.txt
        self.data_viewer_dict = fn.item_list
        self.viewer_text.setHtml(fn.html)
        self.viewer_window.setWindowTitle(_('Data Viewer')+f': {len(selected)} {self.combo_category.currentText()}')
        self.viewer_window.setWindowState((self.viewer_window.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.viewer_window.finished.connect(self.viewer_window.hide())
        self.viewer_window.show()
        self.viewer_window.raise_()
        self.viewer_window.activateWindow()

    def export_csv(self):

        def export_file():
            fname = ()
            fname = QFileDialog.getSaveFileName(self, _('Save') + ' CSV', f'{self.working_dir}/{self.combo_category.currentText()}.csv', _('Text files')+' (*.csv)')
            return fname[0]

        fname = export_file()
        if fname == '':
            self.statusBar.showMessage(' '+_('NOT saved!'), 3500)
            return
        if 'value' in self.data_viewer_dict[0].keys():
            fields = ['source', 'document', 'tag', 'value']
        else:
            fields = ['type', 'color', 'tags', 'language', 'source', 'book', 'chapter', 'block', 'document', 'reference', 'link', 'date', 'title', 'content']
        with open(fname, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.data_viewer_dict)
            self.statusBar.showMessage(' '+_('Saved'), 3500)

    def export_txt(self):

        def export_file():
            fname = ()
            fname = QFileDialog.getSaveFileName(self, _('Save') + ' TXT', f'{self.working_dir}/{self.combo_category.currentText()}.txt', _('Text files')+' (*.txt)')
            return fname[0]

        fname = export_file()
        if fname == '':
            self.statusBar.showMessage(' '+_('NOT saved!'), 3500)
            return
        with open(fname, 'w', encoding='utf-8') as txtfile:
            txtfile.write(self.data_viewer_txt)
            self.statusBar.showMessage(' '+_('Saved'), 3500)

    def export_xlsx(self):

        def export_file():
            fname = ()
            fname = QFileDialog.getSaveFileName(self, _('Save') + ' XLSX', f'{self.working_dir}/{self.combo_category.currentText()}.xlsx', _('MS Excel files')+' (*.xlsx)')
            return fname[0]

        fname = export_file()
        if fname == '':
            self.statusBar.showMessage(' '+_('NOT saved!'), 3500)
            return
        if 'value' in self.data_viewer_dict[0].keys():
            fields = ['source', 'document', 'tag', 'value']
        else:
            fields = ['CREATED', 'MODIFIED', 'TAGS', 'COLOR', 'RANGE', 'LANG', 'PUB', 'BK', 'CH', 'VS', 'ISSUE', 'DOC', 'BLOCK', 'HEADING', 'LINK', 'TITLE', 'NOTE']
        with Workbook(fname) as workbook:
            if self.current_archive != '':
                name = self.current_archive.name
            else:
                name = _('NEW ARCHIVE')
            workbook.set_properties({'comments': _('Exported from')+f' {name} '+_('by')+f' {APP} ({VERSION})\n'+_('on')+f" {datetime.now().strftime('%Y-%m-%d @ %H:%M:%S')}"})
            bold = workbook.add_format({'bold': True})
            worksheet = workbook.add_worksheet(APP)
            worksheet.write_row(row=0, col=0, cell_format=bold, data=fields)
            worksheet.autofilter(first_row=0, last_row=99999, first_col=0, last_col=len(fields)-1)
            for index, item in enumerate(self.data_viewer_dict):
                row = map(lambda field_id: item.get(field_id, ''), fields)
                worksheet.write_row(row=index+1, col=0, data=row)
                worksheet.write_string(row=index+1, col=len(fields)-1, string=self.data_viewer_dict[index]['NOTE']) # overwrite any that may have been formatted as URLs
            # worksheet.autofit()
            worksheet.freeze_panes(1, 0)
            # worksheet.set_column(len(fields)-4, len(fields)-1, 20)
            worksheet.set_column(0, len(fields)-1, 20)


    def add_favorite(self):
        fn = AddFavorites(favorites)
        if fn.aborted:
            self.clean_up()
            sys.exit()
        text = fn.message
        self.statusBar.showMessage(text[1], 3500)
        if text[0]:
            self.archive_modified()
            self.regroup(False, text[1])
            self.tree_selection()

    def delete(self):
        reply = QMessageBox.warning(self, _('Delete'), _('Are you sure you want to\nDELETE these {} items?').format(self.selected_items), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        self.statusBar.showMessage(' '+_('Deleting. Please wait…'))
        app.processEvents()
        selected = []
        it = QTreeWidgetItemIterator(self.treeWidget, QTreeWidgetItemIterator.Checked)
        for item in it:
            index = item.value()
            if index in self.leaves:
                for i in self.leaves[index]:
                    selected.append(i)
        fn = DeleteItems(self.combo_category.currentText(), selected)
        if fn.aborted:
            self.clean_up()
            sys.exit()
        message = f' {fn.result} '+_('items deleted')
        self.statusBar.showMessage(message, 3500)
        self.trim_db()
        self.regroup(False, message)
        self.tree_selection()


    def obscure(self):
        reply = QMessageBox.warning(self, _('Mask'), _('Are you sure you want to\nMASK all text fields?'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        self.statusBar.showMessage(' '+_('Masking. Please wait…'))
        app.processEvents()
        fn = ObscureItems()
        if fn.aborted:
            self.clean_up()
            sys.exit()
        message = ' '+_('Data masked')
        self.statusBar.showMessage(message, 3500)
        self.archive_modified()
        self.regroup(False, message)


    def reindex(self):
        reply = QMessageBox.information(self, _('Reindex'), _('This may take a few seconds.\nProceed?'), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.No:
            return
        self.trim_db()
        self.pd = QProgressDialog(_('Please wait…'), None, 0, 14, self)
        self.pd.setWindowModality(Qt.WindowModal)
        self.pd.setWindowTitle('Reindexing')
        self.pd.setWindowFlag(Qt.FramelessWindowHint)
        self.pd.setModal(True)
        self.pd.setMinimumDuration(0)
        self.statusBar.showMessage(' '+_('Reindexing. Please wait…'))
        app.processEvents()
        fn = Reindex(self.pd)
        if fn.aborted:
            self.clean_up()
            sys.exit()
        message = ' '+_('Reindexed successfully')
        self.statusBar.showMessage(message, 3500)
        self.archive_modified()
        self.regroup(False, message)

    def trim_db(self):
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
        self.archive_modified()


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

    def clean_up(self):
       shutil.rmtree(tmp_path, ignore_errors=True)


class ConstructTree():
    def __init__(self, window, tree, books, publications, languages, category=_('Notes'), grouping=_('Title'), title='code', current=[]):
        self.tree = tree
        self.window = window
        self.category = category
        self.grouping = grouping
        self.publications = publications
        self.languages = languages
        self.books = books
        self.title_format = title
        self.total = 0
        self.aborted = False
        self.code_yr = regex.compile(r'(.*?[^\d-])(\d{2}$)')
        try:
            if len(current) > 0:
                self.current = current
            else:
                self.current = pd.DataFrame()
                self.get_data()
            self.leaves = {}
            tree.setUpdatesEnabled(False)
            self.tree.clear()
            self.build_tree()
            tree.setUpdatesEnabled(True)
            tree.repaint()
        except Exception as ex:
            DebugInfo(ex)
            self.aborted = True


    def get_data(self):
        con = sqlite3.connect(f'{tmp_path}/{db_name}')
        self.cur = con.cursor()
        self.cur.executescript("PRAGMA temp_store = 2; \
                                PRAGMA journal_mode = 'OFF';")
        if self.category == _('Bookmarks'):
            self.get_bookmarks()
        elif self.category == _('Favorites'):
            self.get_favorites()
        elif self.category == _('Highlights'):
            self.get_highlights()
        elif self.category == _('Notes'):
            self.get_notes()
        elif self.category == _('Annotations'):
            self.get_annotations()
        con.commit()
        self.cur.close()
        con.close()


    def process_code(self, code, issue):
        if code == 'ws' and issue == 0: # Worldwide Security book - same code as simplified Watchtower
            code = 'ws-'
        elif not code:
            code = ''
        yr = ''
        dated = regex.search(self.code_yr, code) # Year included in code
        if dated:
            prefix = dated.group(1)
            suffix = dated.group(2)
            if prefix not in ('bi', 'br', 'brg', 'kn', 'ks', 'pt', 'tp'):
                code = prefix
                if int(suffix) >= 50:
                    yr = '19' + suffix
                else:
                    yr = '20' + suffix
        return code, yr

    def process_color(self, col):
        return (_('Grey'), _('Yellow'), _('Green'), _('Blue'), _('Red'), _('Orange'), _('Purple'))[int(col)]

    def process_detail(self, symbol, book, chapter, issue, year):
        if symbol in ('Rbi8', 'bi10', 'bi12', 'bi22', 'bi7', 'by', 'int', 'nwt', 'nwtsty', 'rh', 'sbi1', 'sbi2'): # Bible appendix notes, etc.
            detail = _('* OTHER *')
        else:
            detail = None
        if issue > 19000000:
            y = str(issue)[0:4]
            m = str(issue)[4:6]
            d = str(issue)[6:]
            if d == '00':
                detail = f'{y}-{m}'
            else:
                detail = f'{y}-{m}-{d}'
            if not year:
                year = y
        if book and chapter:
            bk = str(book).rjust(2, '0') + f': {self.books[book]}'
            detail = 'Bk. ' + bk
        if not detail and year:
            detail = year
        if not year:
            year = _('* YEAR UNCERTAIN *')
        return detail, year


    def merge_df(self, df):
        df = pd.merge(df, self.publications, how='left', on=['Symbol'], sort=False)
        df['Full'] = df['Full'].fillna(df['Symbol'])
        df['Short'] = df['Short'].fillna(df['Symbol'])
        df['Type'] = df[['Type']].fillna(_('Other'))
        df['Year'] = df['Year_y'].fillna(df['Year_x']).fillna(_('* NO YEAR *'))
        df = df.drop(['Year_x', 'Year_y'], axis=1)
        df['Year'] = df['Year'].astype(str).str.replace('.0', '',regex=False)
        return df


    def get_annotations(self):
        lst = []
        for row in self.cur.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, TextTag, l.BookNumber, l.ChapterNumber, l.Title FROM InputField JOIN Location l USING ( LocationId );'):
            if row[2] in self.languages.keys():
                lng = self.languages[row[2]][0]
            else:
                lng = _('* NO LANGUAGE *')
            code, year = self.process_code(row[1], row[3])
            detail, year = self.process_detail(row[1], row[5], row[6], row[3], year)
            item = row[0]
            rec = [ item, lng, code, year, detail ]
            lst.append(rec)
        annotations = pd.DataFrame(lst, columns=[ 'Id', 'Language', 'Symbol', 'Year', 'Detail' ])
        self.current = self.merge_df(annotations)

    def get_bookmarks(self):
        lst = []
        for row in self.cur.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, BookmarkId, l.BookNumber, l.ChapterNumber, l.Title FROM Bookmark b JOIN Location l USING ( LocationId );'):
            if row[2] in self.languages.keys():
                lng = self.languages[row[2]][0]
            else:
                lng = f'#{row[2]}'
            code, year = self.process_code(row[1], row[3])
            detail, year = self.process_detail(row[1], row[5], row[6], row[3], year)
            item = row[4]
            rec = [ item, lng, code or _('* OTHER *'), year, detail ]
            lst.append(rec)
        bookmarks = pd.DataFrame(lst, columns=[ 'Id', 'Language', 'Symbol', 'Year', 'Detail' ])
        self.current = self.merge_df(bookmarks)

    def get_favorites(self):
        lst = []
        for row in self.cur.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, TagMapId FROM TagMap tm JOIN Location l USING ( LocationId ) WHERE tm.NoteId IS NULL ORDER BY tm.Position;'):
            if row[2] in self.languages.keys():
                lng = self.languages[row[2]][0]
            else:
                lng = f'#{row[2]}'
            code, year = self.process_code(row[1], row[3])
            detail, year = self.process_detail(row[1], None, None, row[3], year)
            item = row[4]
            rec = [ item, lng, code, year, detail ]
            lst.append(rec)
        favorites = pd.DataFrame(lst, columns=[ 'Id', 'Language', 'Symbol','Year', 'Detail' ])
        self.current = self.merge_df(favorites)

    def get_highlights(self):
        lst = []
        for row in self.cur.execute('SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, b.BlockRangeId, u.UserMarkId, u.ColorIndex, l.BookNumber, l.ChapterNumber FROM UserMark u JOIN Location l USING ( LocationId ), BlockRange b USING ( UserMarkId );'):
            if row[2] in self.languages.keys():
                lng = self.languages[row[2]][0]
            else:
                lng = f'#{row[2]}'
            code, year = self.process_code(row[1], row[3])
            detail, year = self.process_detail(row[1], row[7], row[8], row[3], year)
            col = self.process_color(row[6] or 0)
            item = row[4]
            rec = [ item, lng, code, col, year, detail ]
            lst.append(rec)
        highlights = pd.DataFrame(lst, columns=[ 'Id', 'Language', 'Symbol', 'Color', 'Year', 'Detail' ])
        self.current = self.merge_df(highlights)

    def get_notes(self):

        def load_independent():
            lst = []
            for row in self.cur.execute("SELECT NoteId Id, ColorIndex Color, GROUP_CONCAT(Name, ' | ') Tags, substr(LastModified, 0, 11) Modified FROM ( SELECT * FROM Note n LEFT JOIN TagMap tm USING ( NoteId ) LEFT JOIN Tag t USING ( TagId ) LEFT JOIN UserMark u USING ( UserMarkId ) ORDER BY t.Name ) n WHERE n.BlockType = 0 GROUP BY n.NoteId;"):
                col = row[1] or 0
                yr = row[3][0:4]
                note = [ row[0], _('* NO LANGUAGE *'), _('* OTHER *'), self.process_color(col), row[2] or _('* NO TAG *'), row[3] or '', yr, None, _('* OTHER *'), _('* OTHER *'), _('* INDEPENDENT *') ]
                lst.append(note)
            return pd.DataFrame(lst, columns=['Id', 'Language', 'Symbol', 'Color', 'Tags', 'Modified', 'Year', 'Detail',  'Short', 'Full', 'Type'])

        lst = []
        for row in self.cur.execute("SELECT NoteId Id, MepsLanguage Language, KeySymbol Symbol, IssueTagNumber Issue, BookNumber Book, ChapterNumber Chapter, ColorIndex Color, GROUP_CONCAT(Name, ' | ') Tags, substr(LastModified, 0, 11) Modified FROM ( SELECT * FROM Note n JOIN Location l USING ( LocationId ) LEFT JOIN TagMap tm USING ( NoteId ) LEFT JOIN Tag t USING ( TagId ) LEFT JOIN UserMark u USING ( UserMarkId ) ORDER BY t.Name ) n GROUP BY n.NoteId;"):
            if row[1] in self.languages.keys():
                lng = self.languages[row[1]][0]
            else:
                lng = f'#{row[1]}'

            code, year = self.process_code(row[2], row[3])
            detail, year = self.process_detail(row[2], row[4], row[5], row[3], year)
            col = self.process_color(row[6] or 0)
            note = [ row[0], lng, code or _('* OTHER *'), col, row[7] or _('* NO TAG *'), row[8] or '', year, detail ]
            lst.append(note)
        notes = pd.DataFrame(lst, columns=[ 'Id', 'Language', 'Symbol', 'Color', 'Tags', 'Modified', 'Year', 'Detail' ])
        notes = self.merge_df(notes)
        i_notes = load_independent()
        notes = pd.concat([i_notes, notes], axis=0, ignore_index=True)
        self.current = notes


    def build_tree(self):

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
                    self.leaves[parent] = []
                    child = add_node(parent, i, df.shape[0])
                    self.leaves[child] = df['Id'].to_list()
                    traverse(df, idx[1:], child)

        if self.title_format == 'code':
            title = 'Symbol'
        elif self.title_format == 'short':
            title = 'Short'
        else:
            title = 'Full'
        if self.current.shape[0] == 0:
            return
        self.current['Title'] = self.current[title]

        views = {
            _('Type'): [ 'Type', 'Title', 'Language' ],
            _('Title'): [ 'Title', 'Language', 'Detail' ],
            _('Language'): [ 'Language', 'Title', 'Detail' ],
            _('Year'): [ 'Year', 'Title', 'Language' ],
            _('Tag'): [ 'Tags', 'Title', 'Language' ],
            _('Color'): [ 'Color', 'Title', 'Language' ] }

        self.total = self.current.shape[0]
        filters = views[self.grouping]
        traverse(self.current, filters, self.tree)


class AddFavorites():
    def __init__(self, favorites):
        self.favorites = favorites
        self.message = (0, '')
        con = sqlite3.connect(f'{tmp_path}/{db_name}')
        self.cur = con.cursor()
        self.cur.executescript("PRAGMA temp_store = 2; \
                                PRAGMA journal_mode = 'OFF'; \
                                PRAGMA foreign_keys = 'OFF'; \
                                BEGIN;")
        self.aborted = False
        try:
            self.add_favorite()
            self.cur.execute("PRAGMA foreign_keys = 'ON';")
            con.commit()
        except Exception as ex:
            DebugInfo(ex)
            self.aborted = True
        self.cur.close()
        con.close()

    def add_dialog(self):

        def set_edition():
            lng = language.currentText()
            publication.clear()
            publication.addItems(sorted(self.favorites.loc[self.favorites['Lang'] == lng]['Short']))

        dialog = QDialog()
        dialog.setWindowTitle(_('Add Favorite'))
        label = QLabel(dialog)
        label.setText(_('Select the language and Bible edition to add:'))

        language = QComboBox(dialog)
        language.addItem(' ')
        language.addItems(sorted(self.favorites['Lang'].unique()))
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

        layout = QVBoxLayout()
        layout.addWidget(label)
        form = QFormLayout()
        form.addRow(_('Language')+':', language)
        form.addRow(_('Edition')+':', publication)
        layout.addLayout(form)
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        dialog.setWindowFlag(Qt.FramelessWindowHint)
        if dialog.exec():
            return publication.currentText(), language.currentText()
        else:
            return ' ', ' '

    def tag_positions(self):
      self.cur.execute("INSERT INTO Tag ( Type, Name ) SELECT 0, 'Favorite' WHERE NOT EXISTS ( SELECT 1 FROM Tag WHERE Type = 0 AND Name = 'Favorite' );")
      tag_id = self.cur.execute('SELECT TagId FROM Tag WHERE Type = 0;').fetchone()[0]
      position = self.cur.execute(f"SELECT max(Position) FROM TagMap WHERE TagId = {tag_id};").fetchone()
      if position[0] != None:
          return tag_id, position[0] + 1
      else:
          return tag_id, 0

    def add_location(self, symbol, language):
      self.cur.execute(f"INSERT INTO Location ( IssueTagNumber, KeySymbol, MepsLanguage, Type ) SELECT 0, '{symbol}', {language}, 1 WHERE NOT EXISTS ( SELECT 1 FROM Location WHERE KeySymbol = '{symbol}' AND MepsLanguage = {language} AND IssueTagNumber = 0 AND Type = 1 );")
      result = self.cur.execute(f"SELECT LocationId FROM Location WHERE KeySymbol = '{symbol}' AND MepsLanguage = {language} AND IssueTagNumber = 0 AND Type = 1;").fetchone()
      return result[0]

    def add_favorite(self):
        pub, lng = self.add_dialog()
        if pub == ' ' or lng == ' ':
            self.message = (0, ' '+_('Nothing added!'))
            return
        language = favorites.loc[(favorites.Short == pub) & (favorites.Lang == lng), 'Language'].values[0]
        publication = favorites.loc[(favorites.Short == pub) & (favorites.Lang == lng), 'Symbol'].values[0]
        location = self.add_location(publication, language)
        result = self.cur.execute(f"SELECT TagMapId FROM TagMap WHERE LocationId = {location} AND TagId = (SELECT TagId FROM Tag WHERE Name = 'Favorite');").fetchone()
        if result:
            self.message = (0, ' '+_('Favorite for "{}" in {} already exists.').format(pub, lng))
            return
        tag_id, position = self.tag_positions()
        self.cur.execute(f"INSERT INTO TagMap ( LocationId, TagId, Position ) VALUES ( {location}, {tag_id}, {position} );")
        self.message = (1, ' '+_('Added "{}" in {}').format(pub, lng))
        return 1


class DeleteItems():
    def __init__(self, category=_('Notes'), items=[]):
        self.category = category
        con = sqlite3.connect(f'{tmp_path}/{db_name}')
        self.cur = con.cursor()
        self.cur.executescript("PRAGMA temp_store = 2; \
                                PRAGMA journal_mode = 'OFF'; \
                                PRAGMA foreign_keys = 'OFF'; \
                                BEGIN;")
        self.aborted = False
        try:
            self.items = str(items).replace('[', '(').replace(']', ')')
            self.result = self.delete_items()
            self.cur.execute("PRAGMA foreign_keys = 'ON';")
            con.commit()
        except Exception as ex:
            DebugInfo(ex)
            self.aborted = True
        self.cur.close()
        con.close()

    def delete_items(self):
        if self.category == _('Bookmarks'):
            return self.delete('Bookmark', 'BookmarkId')
        elif self.category == _('Favorites'):
            return self.delete('TagMap', 'TagMapId')
        elif self.category == _('Highlights'):
            return self.delete('BlockRange', 'BlockRangeId')
        elif self.category == _('Notes'):
            return self.delete('Note', 'NoteId')
        elif self.category == _('Annotations'):
            return self.delete('InputField', 'LocationId')

    def delete(self, table, field):
        return self.cur.execute(f"DELETE FROM {table} WHERE {field} IN {self.items};").rowcount


class ExportItems():
    def __init__(self, category=_('Notes'), items=[], fname='', current_archive=''):
        self.category = category
        self.current_archive = current_archive
        con = sqlite3.connect(f'{tmp_path}/{db_name}')
        self.cur = con.cursor()
        self.aborted = False
        try:
            self.items = str(items).replace('[', '(').replace(']', ')')
            self.export_file = open(fname, 'w', encoding='utf-8')
            self.export_items()
            self.export_file.close
        except Exception as ex:
            DebugInfo(ex)
            self.aborted = True
        self.cur.close()
        con.close()

    def export_items(self):
        if self.category == _('Highlights'):
            return self.export_highlights()
        elif self.category == _('Notes'):
            return self.export_notes()
        elif self.category == _('Annotations'):
            return self.export_annotations()

    def export_notes(self):
        if self.cur.execute("SELECT * FROM pragma_table_info('Note') WHERE name = 'Created';").fetchone():
            columns = ', n.Created' # JW Library v14+ has an extra column
        else:
            columns = ''

        self.export_note_header()
        self.export_bible(columns)
        self.export_publications(columns)
        self.export_independent(columns)
        self.export_file.write('\n==={END}===')

    def export_note_header(self):
        # Note: added invisible char on first line to force UTF-8 encoding
        self.export_file.write('\n'.join(['{TITLE=}\n ',
            _('MODIFY FIELD ABOVE BEFORE RE-IMPORTING'),
            _('LEAVE {TITLE=} (empty) IF YOU DON\'T WANT TO DELETE ANY NOTES WHILE IMPORTING\n'),
            _('EACH NOTE STARTS WITH HEADER INDICATING CATEGORY, ETC.'),
            _('BE CAREFUL WHEN MODIFYING THE ATTRIBUTES\n'),
            _('LINE AFTER HEADER IS NOTE TITLE'),
            _('REST IS NOTE BODY; CAN BE MULTI-LINE AND IS TERMINATED BY NEXT NOTE HEADER\n'),
            _('SEPARATE TAGS WITH "|"'),
            _('OR LEAVE EMPTY IF NO TAG: {TAGS=bible|notes} OR {TAGS=}\n'),
            _('FILE SHOULD TERMINATE WITH "==={END}==="\n'),
            _('ENSURE YOUR FILE IS ENCODED AS UTF-8 (UNICODE)')]))
        self.export_file.write('\n\n'+_('Exported from')+f' {self.current_archive}\n'+_('by')+f' {APP} ({VERSION}) '+_('on')+f" {datetime.now().strftime('%Y-%m-%d @ %H:%M:%S')}\n\n")
        self.export_file.write('*' * 79)

    def export_bible(self, columns):
        # regular Bible (book, chapter and verse)
        for row in self.cur.execute(f"SELECT l.MepsLanguage, l.KeySymbol, l.BookNumber, l.ChapterNumber, n.BlockIdentifier, u.ColorIndex, n.Title, n.Content, GROUP_CONCAT(t.Name, '|'), n.LastModified, b.StartToken, b.EndToken, l.Title {columns} FROM Note n JOIN Location l USING ( LocationId ) LEFT JOIN TagMap tm USING ( NoteId ) LEFT JOIN Tag t USING ( TagId ) LEFT JOIN UserMark u USING ( UserMarkId ) LEFT JOIN BlockRange b USING ( UserMarkId ) WHERE n.BlockType = 2 AND NoteId IN {self.items} GROUP BY n.NoteId;"):
            color = str(row[5] or 0)
            title = row[6] or ''
            content = row[7] or ''
            tags = row[8] or ''
            if row[10] != None:
                rng = '{RANGE='+f'{row[10]}-{row[11]}'+'}'
            else:
                rng = ''
            if row[12]:
                pub_title = row[12]
            else:
                pub_title = ''
            if columns != '':
                created = '{CREATED='+row[13][:10]+'}'
            else:
                created = ''
            txt = '\n==={CAT=BIBLE}{LANG='+str(row[0])+'}{ED='+str(row[1])+'}{BK='+str(row[2])+'}{CH='+str(row[3])+'}{VER='+str(row[4])+'}{TITLE='+pub_title+'}{COLOR='+color+'}'+rng+'{TAGS='+tags+'}'+created+'{MODIFIED='+row[9][:10]+'}===\n'+title+'\n'+content.rstrip()
            self.export_file.write(txt)

        # note in book header - similar to a publication
        for row in self.cur.execute(f"SELECT l.MepsLanguage, l.KeySymbol, l.BookNumber, l.ChapterNumber, n.BlockIdentifier, u.ColorIndex, n.Title, n.Content, GROUP_CONCAT(t.Name, '|'), n.LastModified, b.StartToken, b.EndToken, l.Title {columns} FROM Note n JOIN Location l USING (LocationId) LEFT JOIN TagMap tm USING (NoteId) LEFT JOIN Tag t USING (TagId) LEFT JOIN UserMark u USING (UserMarkId) LEFT JOIN BlockRange b USING ( UserMarkId ) WHERE n.BlockType =1 AND l.BookNumber IS NOT NULL AND NoteId IN {self.items} GROUP BY n.NoteId;"):
            color = str(row[5] or 0)
            title = row[6] or ''
            content = row[7] or ''
            tags = row[8] or ''
            if row[10] != None:
                rng = '{RANGE='+f'{row[10]}-{row[11]}'+'}'
            else:
                rng = ''
            if row[12]:
                pub_title = row[12]
            else:
                pub_title = ''
            if columns != '':
                created = '{CREATED='+row[13][:10]+'}'
            else:
                created = ''
            txt = '\n==={CAT=BIBLE}{LANG='+str(row[0])+'}{ED='+str(row[1])+'}{BK='+str(row[2])+'}{CH='+str(row[3])+'}{VER='+str(row[4])+'}{DOC=0}{TITLE='+pub_title+'}{COLOR='+color+'}'+rng+'{TAGS='+tags+'}'+created+'{MODIFIED='+row[9][:10]+'}===\n'+title+'\n'+content.rstrip()
            self.export_file.write(txt)

    def export_publications(self, columns):
        for row in self.cur.execute(f"SELECT l.MepsLanguage, l.KeySymbol, l.IssueTagNumber, l.DocumentId, n.BlockIdentifier, u.ColorIndex, n.Title, n.Content, GROUP_CONCAT(t.Name, '|'), n.LastModified, b.StartToken, b.EndToken, l.Title {columns} FROM Note n JOIN Location l USING ( LocationId ) LEFT JOIN TagMap tm USING ( NoteId ) LEFT JOIN Tag t USING ( TagId ) LEFT JOIN UserMark u USING ( UserMarkId ) LEFT JOIN BlockRange b USING ( UserMarkId ) WHERE n.BlockType = 1 AND l.BookNumber IS NULL AND NoteId IN {self.items} GROUP BY n.NoteId;"):
            color = str(row[5] or 0)
            title = row[6] or ''
            content = row[7] or ''
            tags = row[8] or ''
            if row[10] != None:
                rng = '{RANGE='+f'{row[10]}-{row[11]}'+'}'
            else:
                rng = ''
            if row[12]:
                pub_title = row[12]
            else:
                pub_title = ''
            if columns != '':
                created = '{CREATED='+row[13][:10]+'}'
            else:
                created = ''
            txt = '\n==={CAT=PUBLICATION}{LANG='+str(row[0])+'}{PUB='+str(row[1])+'}{ISSUE='+str(row[2])+'}{DOC='+str(row[3])+'}{BLOCK='+str(row[4])+'}{TITLE='+pub_title+'}{COLOR='+color+'}'+rng+'{TAGS='+tags+'}'+created+'{MODIFIED='+row[9][:10]+'}===\n'+title+'\n'+content.rstrip()
            self.export_file.write(txt)

    def export_independent(self, columns):
        for row in self.cur.execute(f"SELECT n.Title, n.Content, GROUP_CONCAT(t.Name, '|'), n.LastModified {columns} FROM Note n LEFT JOIN TagMap tm USING (NoteId) LEFT JOIN Tag t USING (TagId) WHERE n.BlockType = 0 AND NoteId IN {self.items} GROUP BY n.NoteId;"):
            tags = row[2] or ''
            if columns != '':
                created = '{CREATED='+row[4][:10]+'}'
            else:
                created = ''
            txt = '\n==={CAT=INDEPENDENT}{TAGS='+tags+'}'+created+'{MODIFIED='+row[3][:10]+'}===\n'+(row[0] or '')+'\n'+(row[1] or '').rstrip()
            self.export_file.write(txt)


    def export_highlights(self):
        self.export_highlight_header()
        for row in self.cur.execute(f"SELECT b.BlockType, b.Identifier, b.StartToken, b.EndToken, u.ColorIndex, u.Version, l.BookNumber, l.ChapterNumber, l.DocumentId, l.IssueTagNumber, l.KeySymbol, l.MepsLanguage, l.Type FROM UserMark u JOIN Location l USING ( LocationId ), BlockRange b USING ( UserMarkId ) WHERE BlockRangeId IN {self.items};"):
            self.export_file.write(f'\n{row[0]}')
            for item in range(1,13):
                self.export_file.write(f',{row[item]}')

    def export_highlight_header(self):
        self.export_file.write('{HIGHLIGHTS}\n \nTHIS FILE IS NOT MEANT TO BE MODIFIED MANUALLY\nYOU CAN USE IT TO BACKUP/TRANSFER/MERGE SELECTED HIGHLIGHTS\n\nFIELDS: BlockRange.BlockType, BlockRange.Identifier, BlockRange.StartToken,\n        BlockRange.EndToken, UserMark.ColorIndex, UserMark.Version,\n        Location.BookNumber, Location.ChapterNumber, Location.DocumentId,\n        Location.IssueTagNumber, Location.KeySymbol, Location.MepsLanguage,\n        Location.Type')
        self.export_file.write('\n\n'+_('Exported from')+f' {self.current_archive}\n'+_('by')+f' {APP} ({VERSION}) '+_('on')+f" {datetime.now().strftime('%Y-%m-%d @ %H:%M:%S')}\n\n")
        self.export_file.write('*' * 79)


    def export_annotations(self):
        self.export_annotations_header()
        for row in self.cur.execute(f"SELECT l.DocumentId, l.IssueTagNumber, l.KeySymbol, TextTag, Value FROM InputField JOIN Location l USING (LocationId) WHERE l.LocationId IN {self.items};"):
            self.export_file.write(f'\n{row[0]}')
            for item in range(1,5):
                string = str(row[item]).replace('\n', r'\n')
                self.export_file.write(f',{string}')

    def export_annotations_header(self):
        self.export_file.write('{ANNOTATIONS}\n \nENSURE YOUR FILE IS ENCODED AS UTF-8 (UNICODE)\n\nTHIS FILE IS NOT MEANT TO BE MODIFIED MANUALLY\nYOU CAN USE IT TO BACKUP/TRANSFER/MERGE SELECTED ANNOTATIONS\n\nFIELDS: Location.DocumentId, Location.IssueTagNumber,\n        Location.KeySymbol, InputField.TextTag,\n        InputField.Value')
        self.export_file.write('\n\n'+_('Exported from')+f' {self.current_archive}\n'+_('by')+f' {APP} ({VERSION}) '+_('on')+f" {datetime.now().strftime('%Y-%m-%d @ %H:%M:%S')}\n\n")
        self.export_file.write('*' * 79)


class ImportAnnotations():
    def __init__(self, fname=''):
        con = sqlite3.connect(f'{tmp_path}/{db_name}')
        self.cur = con.cursor()
        self.cur.executescript("PRAGMA temp_store = 2; \
                                PRAGMA journal_mode = 'MEMORY'; \
                                PRAGMA foreign_keys = 'OFF'; \
                                BEGIN;")
        self.aborted = False
        try:
            self.import_file = open(fname, 'r', encoding='utf-8', errors='namereplace')
            if self.pre_import():
                self.count = self.import_items()
            else:
                self.count = 0
            self.import_file.close
            self.cur.execute("PRAGMA foreign_keys = 'ON';")
            con.commit()
        except Exception as ex:
            DebugInfo(ex)
            self.aborted = True
        self.cur.close()
        con.close()

    def pre_import(self):
        line = self.import_file.readline()
        if regex.search('{ANNOTATIONS}', line):
            return True
        else:
            QMessageBox.critical(None, _('Error!'), _('Wrong import file format:\nMissing {ANNOTATIONS} tag line'), QMessageBox.Abort)
            return False

    def import_items(self):
        count = 0
        for line in self.import_file:
            if regex.match(r'^\d+,\d+,\w+,', line):
                try:
                    count += 1
                    attribs = regex.split(',', line.rstrip(), 4)
                    location_id = self.add_location(attribs)
                    value = attribs[4].replace(r'\n', '\n')
                    if self.cur.execute(f"SELECT * FROM InputField WHERE LocationId = ? AND TextTag = ?;", (location_id, attribs[3])).fetchone():
                        self.cur.execute(f"UPDATE InputField SET Value = ? WHERE LocationId = ? AND TextTag = ?;", (value, location_id, attribs[3]))
                    else:
                        self.cur.execute(f"INSERT INTO InputField (LocationId, TextTag, Value) VALUES ( ?, ?, ? );", (location_id,attribs[3], value))
                except:
                    QMessageBox.critical(None, _('Error!'), _('Error on import!\n\nFaulting entry')+f' (#{count}):\n{line}', QMessageBox.Abort)
                    self.cur.execute('ROLLBACK;')
                    return 0
        return count

    def add_location(self, attribs):
        self.cur.execute(f"INSERT INTO Location (DocumentId, IssueTagNumber, KeySymbol, MepsLanguage, Type) SELECT ?, ?, ?, NULL, 0 WHERE NOT EXISTS ( SELECT 1 FROM Location WHERE DocumentId = ? AND IssueTagNumber = ? AND KeySymbol = ? AND MepsLanguage IS NULL AND Type = 0);", (attribs[0], attribs[1], attribs[2], attribs[0], attribs[1], attribs[2]))
        result = self.cur.execute(f"SELECT LocationId FROM Location WHERE DocumentId = ? AND IssueTagNumber = ? AND KeySymbol = ? AND MepsLanguage IS NULL AND Type = 0;", (attribs[0], attribs[1], attribs[2])).fetchone()
        return result[0]

class ImportHighlights():
    def __init__(self, fname=''):
        con = sqlite3.connect(f'{tmp_path}/{db_name}')
        self.cur = con.cursor()
        self.cur.executescript("PRAGMA temp_store = 2; \
                                PRAGMA journal_mode = 'MEMORY'; \
                                PRAGMA foreign_keys = 'OFF'; \
                                BEGIN;")
        self.aborted = False
        try:
            self.import_file = open(fname, 'r')
            if self.pre_import():
                self.count = self.import_items()
            else:
                self.count = 0
            self.import_file.close
            self.cur.execute("PRAGMA foreign_keys = 'ON';")
            con.commit()
        except Exception as ex:
            DebugInfo(ex)
            self.aborted = True
        self.cur.close()
        con.close()

    def pre_import(self):
        line = self.import_file.readline()
        if regex.search('{HIGHLIGHTS}', line):
            return True
        else:
            QMessageBox.critical(None, _('Error!'), _('Wrong import file format:\nMissing {HIGHLIGHTS} tag line'), QMessageBox.Abort)
            return False

    def import_items(self):
        count = 0
        for line in self.import_file:
            if regex.match(r'^(\d+,){6}', line):
                try:
                    count += 1
                    attribs = regex.split(',', line.rstrip().replace('None', ''))
                    if attribs[6]:
                        location_id = self.add_scripture_location(attribs)
                    else:
                        location_id = self.add_publication_location(attribs)
                    self.import_highlight(attribs, location_id)
                except:
                    QMessageBox.critical(None, _('Error!'), _('Error on import!\n\nFaulting entry')+f' (#{count}):\n{line}', QMessageBox.Abort)
                    self.cur.execute('ROLLBACK;')
                    return 0
        return count

    def add_scripture_location(self, attribs):
        self.cur.execute(f"INSERT INTO Location ( KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Type ) SELECT '{attribs[10]}', {attribs[11]}, {attribs[6]}, {attribs[7]}, {attribs[12]} WHERE NOT EXISTS ( SELECT 1 FROM Location WHERE KeySymbol = '{attribs[10]}' AND MepsLanguage = {attribs[11]} AND BookNumber = {attribs[6]} AND ChapterNumber = {attribs[7]} );")
        result = self.cur.execute(f"SELECT LocationId FROM Location WHERE KeySymbol = '{attribs[10]}' AND MepsLanguage = {attribs[11]} AND BookNumber = {attribs[6]} AND ChapterNumber = {attribs[7]};").fetchone()
        return result[0]

    def add_publication_location(self, attribs):
        self.cur.execute(f"INSERT INTO Location ( IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Type ) SELECT {attribs[9]}, '{attribs[10]}', {attribs[11]}, {attribs[8]}, {attribs[12]} WHERE NOT EXISTS ( SELECT 1 FROM Location WHERE KeySymbol = '{attribs[10]}' AND MepsLanguage = {attribs[11]} AND IssueTagNumber = {attribs[9]} AND DocumentId = {attribs[8]} AND Type = {attribs[12]});")
        result = self.cur.execute(f"SELECT LocationId FROM Location WHERE KeySymbol = '{attribs[10]}' AND MepsLanguage = {attribs[11]} AND IssueTagNumber = {attribs[9]} AND DocumentId = {attribs[8]} AND Type = {attribs[12]};").fetchone()
        return result[0]

    def add_usermark(self, attribs, location_id):
        unique_id = uuid.uuid1()
        self.cur.execute(f"INSERT INTO UserMark ( ColorIndex, LocationId, StyleIndex, UserMarkGuid, Version ) VALUES ( {attribs[4]}, {location_id}, 0, '{unique_id}', {attribs[5]} );")
        result = self.cur.execute(f"SELECT UserMarkId FROM UserMark WHERE UserMarkGuid = '{unique_id}';").fetchone()
        return result[0]

    def import_highlight(self, attribs, location_id):
        usermark_id = self.add_usermark(attribs, location_id)
        result = self.cur.execute(f"SELECT * FROM BlockRange JOIN UserMark USING (UserMarkId) WHERE Identifier = {attribs[1]} AND LocationId = {location_id};")
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
        self.cur.execute(f"DELETE FROM BlockRange WHERE BlockRangeId IN {block};")
        self.cur.execute(f"INSERT INTO BlockRange (BlockType, Identifier, StartToken, EndToken, UserMarkId) VALUES ( ?, ?, ?, ?, ? );", (attribs[0], attribs[1], ns, ne, usermark_id))
        return

# class ImportNotes():
#     def __init__(self, fname=''):
#         con = sqlite3.connect(f'{tmp_path}/{db_name}')
#         self.cur = con.cursor()
#         self.cur.executescript("PRAGMA temp_store = 2; \
#                                 PRAGMA journal_mode = 'MEMORY'; \
#                                 PRAGMA foreign_keys = 'OFF'; \
#                                 BEGIN;")
#         self.aborted = False
#         try:
#             self.import_file = open(fname, 'r', encoding='utf-8', errors='namereplace')
#             if self.pre_import():
#                 self.count = self.import_items()
#             else:
#                 self.count = 0
#             self.import_file.close
#             self.cur.execute("PRAGMA foreign_keys = 'ON';")
#             con.commit()
#         except Exception as ex:
#             DebugInfo(ex)
#             self.aborted = True
#         self.cur.close()
#         con.close()

#     def pre_import(self):
#         line = self.import_file.readline()
#         m = regex.search('{TITLE=(.?)}', line)
#         if m:
#             title_char = m.group(1) or ''
#         else:
#             QMessageBox.critical(None, _('Error!'), _('Wrong import file format:\nMissing or malformed {TITLE=} attribute line'), QMessageBox.Abort)
#             return False
#         if title_char:
#             self.delete_notes(title_char)
#         return True

#     def delete_notes(self, title_char):
#         results = len(self.cur.execute(f"SELECT NoteId FROM Note WHERE Title GLOB '{title_char}*';").fetchall())
#         if results < 1:
#             return 0
#         answer = QMessageBox.warning(None, _('Warning'), f'{results} '+_('notes starting with')+f' "{title_char}" '+_('WILL BE DELETED before importing.\n\nProceed with deletion? (NO to skip)'), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
#         if answer == 'No':
#           return 0
#         results = self.cur.execute(f"DELETE FROM Note WHERE Title GLOB '{title_char}*';")
#         return results

#     def import_items(self):
#         count = 0
#         notes = self.import_file.read().replace("'", "''")
#         for item in regex.finditer('^===({.*?})===\n(.*?)\n(.*?)(?=\n==={)', notes, regex.S | regex.M):
#             try:
#                 count += 1
#                 header = item.group(1)
#                 title = item.group(2)
#                 note = item.group(3)
#                 attribs = self.process_header(header)
#                 if attribs['CAT'] == 'BIBLE':
#                     self.import_bible(attribs, title, note)
#                 elif attribs['CAT'] == 'PUBLICATION':
#                     self.import_publication(attribs, title, note)
#                 elif attribs['CAT'] == 'INDEPENDENT':
#                     self.import_independent(attribs, title, note)
#                 else:
#                     QMessageBox.critical(None, _('Error!'), _('Wrong import file format:\nMalformed header')+f':\n{attribs}', QMessageBox.Abort)
#                     return 0
#             except:
#                 QMessageBox.critical(None, _('Error!'), _('Error on import!\n\nFaulting entry')+f' (#{count}):\n{header}', QMessageBox.Abort)
#                 self.cur.execute('ROLLBACK;')
#                 return 0
#         return count

#     def process_header(self, line):
#         attribs = {}
#         for (key, value) in regex.findall('{(.*?)=(.*?)}', line):
#             attribs[key] = value
#         attribs['TITLE'] = attribs.get('TITLE') or None
#         return attribs

#     def process_tags(self, note_id, tags):
#         self.cur.execute(f"DELETE FROM TagMap WHERE NoteId = {note_id};")
#         for tag in tags.split('|'):
#             tag = tag.strip()
#             if not tag:
#                 continue
#             self.cur.execute(f"INSERT INTO Tag ( Type, Name ) SELECT 1, '{tag}' WHERE NOT EXISTS ( SELECT 1 FROM Tag WHERE Name = '{tag}' );")
#             tag_id = self.cur.execute(f"SELECT TagId from Tag WHERE Name = '{tag}';").fetchone()[0]
#             position = self.cur.execute(f"SELECT ifnull(max(Position), -1) FROM TagMap WHERE TagId = {tag_id};").fetchone()[0] + 1
#             self.cur.execute(f"INSERT Into TagMap (NoteId, TagId, Position) SELECT {note_id}, {tag_id}, {position} WHERE NOT EXISTS ( SELECT 1 FROM TagMap WHERE NoteId = {note_id} AND TagId = {tag_id});")

#     def add_usermark(self, attribs, location_id):
#         if 'COLOR' in attribs.keys():
#             color = attribs['COLOR']
#         if color == '0':
#             return 'NULL'
#         if 'VER' in attribs.keys():
#             block_type = 2
#             identifier = attribs['VER']
#         else:
#             block_type = 1
#             identifier = attribs['BLOCK']
#         if 'RANGE' in attribs.keys():
#             ns, ne = attribs['RANGE'].split('-')
#             fields = f' AND StartToken = {int(ns)} AND EndToken = {int(ne)}'
#         else:
#             fields = ''
#         result = self.cur.execute(f"SELECT UserMarkId FROM UserMark JOIN BlockRange USING (UserMarkId) WHERE ColorIndex = {color} AND LocationId = {location_id} AND Identifier = {identifier}{fields};").fetchone()
#         if result:
#             usermark_id = result[0]
#         else:
#             unique_id = uuid.uuid1()
#             self.cur.execute(f"INSERT INTO UserMark ( ColorIndex, LocationId, StyleIndex, UserMarkGuid, Version ) VALUES ( {color}, {location_id}, 0, '{unique_id}', 1 );")
#             usermark_id = self.cur.execute(f"SELECT UserMarkId FROM UserMark WHERE UserMarkGuid = '{unique_id}';").fetchone()[0]
#         try:
#             self.cur.execute(f"INSERT INTO BlockRange ( BlockType, Identifier, StartToken, EndToken, UserMarkId ) VALUES ( ?, ?, ?, ?, ? );", (block_type, identifier, ns, ne, usermark_id))
#         except:
#             pass
#         return usermark_id

#     def add_scripture_location(self, attribs):
#         self.cur.execute(f"INSERT INTO Location ( KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Title, Type ) SELECT '{attribs['ED']}', {attribs['LANG']}, {attribs['BK']}, {attribs['CH']}, '{attribs['TITLE']}', 0 WHERE NOT EXISTS ( SELECT 1 FROM Location WHERE KeySymbol = '{attribs['ED']}' AND MepsLanguage = {attribs['LANG']} AND BookNumber = {attribs['BK']} AND ChapterNumber = {attribs['CH']} );")
#         result = self.cur.execute(f"SELECT LocationId FROM Location WHERE KeySymbol = '{attribs['ED']}' AND MepsLanguage = {attribs['LANG']} AND BookNumber = {attribs['BK']} AND ChapterNumber = {attribs['CH']};").fetchone()
#         return result[0]

#     def import_bible(self, attribs, title, note):
#         location_scripture = self.add_scripture_location(attribs)
#         usermark_id = self.add_usermark(attribs, location_scripture)
#         block_type = 2
#         try:
#             block_type = int(attribs['DOC']) * 0 + 1 # special case of Bible note in book header, etc.
#         except:
#             pass
#         result = self.cur.execute(f"SELECT Guid, LastModified FROM Note WHERE LocationId = {location_scripture} AND Title = '{title}' AND BlockIdentifier = {attribs['VER']} AND BlockType = {block_type};").fetchone()
#         if result:
#             unique_id = result[0]
#             modified = attribs.get('MODIFIED') or attribs.get('DATE') or result[1]
#             created = attribs.get('CREATED') or attribs.get('DATE') or result[2]
#             sql = f"UPDATE Note SET UserMarkId = {usermark_id}, Content = '{note}', LastModified = '{modified}', Created = '{created}' WHERE Guid = '{unique_id}';"
#         else:
#             unique_id = uuid.uuid1()
#             created = attribs.get('CREATED') or attribs.get('DATE') or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
#             modified = attribs.get('MODIFIED') or attribs.get('DATE') or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
#             sql = f"INSERT INTO Note (Guid, UserMarkId, LocationId, Title, Content, BlockType, BlockIdentifier, LastModified, Created) VALUES ('{unique_id}', {usermark_id}, {location_scripture}, '{title}', '{note}', {block_type}, {attribs['VER']}, '{modified}', '{created}' );"
#         self.cur.execute(sql)
#         note_id = self.cur.execute(f"SELECT NoteId from Note WHERE Guid = '{unique_id}';").fetchone()[0]
#         self.process_tags(note_id, attribs.get('TAGS'))


#     def add_publication_location(self, attribs):
#         self.cur.execute(f"INSERT INTO Location ( IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Title, Type ) SELECT {attribs['ISSUE']}, '{attribs['PUB']}', {attribs['LANG']}, {attribs['DOC']}, '{attribs['TITLE']}', 0 WHERE NOT EXISTS ( SELECT 1 FROM Location WHERE KeySymbol = '{attribs['PUB']}' AND MepsLanguage = {attribs['LANG']} AND IssueTagNumber = {attribs['ISSUE']} AND DocumentId = {attribs['DOC']} AND Type = 0);")
#         result = self.cur.execute(f"SELECT LocationId from Location WHERE KeySymbol = '{attribs['PUB']}' AND MepsLanguage = {attribs['LANG']} AND IssueTagNumber = {attribs['ISSUE']} AND DocumentId = {attribs['DOC']} AND Type = 0;").fetchone()
#         return result[0]

#     def import_publication(self, attribs, title, note):
#         location_id = self.add_publication_location(attribs)
#         usermark_id = self.add_usermark(attribs, location_id)
#         result = self.cur.execute(f"SELECT Guid, LastModified FROM Note WHERE LocationId = {location_id} AND Title = '{title}' AND BlockIdentifier = {attribs['BLOCK']};").fetchone()
#         if result:
#             unique_id = result[0]
#             modified = attribs.get('MODIFIED') or attribs.get('DATE') or result[1]
#             created = attribs.get('CREATED') or attribs.get('DATE') or result[2]
#             sql = f"UPDATE Note SET UserMarkId = {usermark_id}, Content = '{note}', LastModified = '{modified}', Created = '{created}' WHERE Guid = '{unique_id}';"
#         else:
#             created = attribs.get('CREATED') or attribs.get('DATE') or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
#             modified = attribs.get('MODIFIED') or attribs.get('DATE') or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
#             unique_id = uuid.uuid1()
#             sql = f"INSERT INTO Note (Guid, UserMarkId, LocationId, Title, Content, BlockType, BlockIdentifier, LastModified, Created) VALUES ( '{unique_id}', {usermark_id}, {location_id}, '{title}', '{note}', 1, {attribs['BLOCK']}, '{modified}', '{created}' );"
#         self.cur.execute(sql)
#         note_id = self.cur.execute(f"SELECT NoteId from Note WHERE Guid = '{unique_id}';").fetchone()[0]
#         self.process_tags(note_id, attribs.get('TAGS'))


#     def import_independent(self, attribs, title, note):
#         if not title:
#             result = self.cur.execute(f"SELECT Guid, LastModified FROM Note WHERE Title IS NULL AND Content = '{note}' AND BlockType = 0;").fetchone()
#         else:
#             result = self.cur.execute(f"SELECT Guid, LastModified, Created FROM Note WHERE Title = '{title}' AND Content = '{note}' AND BlockType = 0;").fetchone()
#         if result:
#             unique_id = result[0]
#             modified = attribs.get('MODIFIED') or attribs.get('DATE') or result[1]
#             created = attribs.get('CREATED') or attribs.get('DATE') or result[2]
#             sql = f"UPDATE Note SET Content = '{note}', LastModified = '{modified}', Created = '{created}' WHERE Guid = '{unique_id}';"
#         else:
#             created = attribs.get('CREATED') or attribs.get('DATE') or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
#             modified = attribs.get('MODIFIED') or attribs.get('DATE') or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
#             unique_id = uuid.uuid1()
#             if not title:
#                 sql = f"INSERT INTO Note (Guid, Content, BlockType, LastModified, Created) VALUES ( '{unique_id}', '{note}', 0, '{modified}', '{created}' );"
#             else:
#                 sql = f"INSERT INTO Note (Guid, Title, Content, BlockType, LastModified, Created) VALUES ( '{unique_id}', '{title}', '{note}', 0, '{modified}', '{created}' );"
#         self.cur.execute(sql)
#         note_id = self.cur.execute(f"SELECT NoteId from Note WHERE Guid = '{unique_id}';").fetchone()[0]
#         self.process_tags(note_id, attribs.get('TAGS'))

class ImportNotes():
    def __init__(self, fname, languages):
        con = sqlite3.connect(f'{tmp_path}/{db_name}')
        self.cur = con.cursor()
        self.cur.executescript("PRAGMA temp_store = 2; \
                                PRAGMA journal_mode = 'MEMORY'; \
                                PRAGMA foreign_keys = 'OFF'; \
                                BEGIN;")
        self.aborted = False
        self.languages = languages
        try:
            df = pd.read_excel(fname)
            self.count = self.import_items(df)
            self.cur.execute("PRAGMA foreign_keys = 'ON';")
            con.commit()
        except Exception as ex:
            DebugInfo(ex)
            self.aborted = True
        self.cur.close()
        con.close()

    def import_items(self, df):
        df['ISSUE'].fillna(0, inplace=True)
        df['TAGS'].fillna('', inplace=True)
        df['COLOR'].fillna(0, inplace=True)
        count = 0
        for i, row in df.iterrows():
            count += 1
            if pd.notna(row['BK']):
                self.import_bible(row)
            elif pd.notna(row['DOC']):
                self.import_publication(row)
            else:
                self.import_independent(row)
        return count


    def process_tags(self, note_id, tags):
        self.cur.execute(f"DELETE FROM TagMap WHERE NoteId = {note_id};")
        for tag in str(tags).split('|'):
            tag = tag.strip()
            if not tag:
                continue
            self.cur.execute('INSERT INTO Tag ( Type, Name ) SELECT 1, ? WHERE NOT EXISTS ( SELECT 1 FROM Tag WHERE Name = ? );', (tag, tag))
            tag_id = self.cur.execute(f"SELECT TagId from Tag WHERE Name = '{tag}';").fetchone()[0]
            position = self.cur.execute(f"SELECT ifnull(max(Position), -1) FROM TagMap WHERE TagId = {tag_id};").fetchone()[0] + 1
            self.cur.execute('INSERT Into TagMap (NoteId, TagId, Position) SELECT ?, ?, ? WHERE NOT EXISTS ( SELECT 1 FROM TagMap WHERE NoteId = ? AND TagId = ? );', (note_id, tag_id, position, note_id, tag_id))

    def add_usermark(self, attribs, location_id):
        if attribs['COLOR'] == 0:
            return 'NULL'
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
        result = self.cur.execute(f"SELECT UserMarkId FROM UserMark JOIN BlockRange USING (UserMarkId) WHERE ColorIndex = {attribs['COLOR']} AND LocationId = {location_id} AND Identifier = {identifier}{fields};").fetchone()
        if result:
            usermark_id = result[0]
        else:
            unique_id = uuid.uuid1()
            self.cur.execute(f"INSERT INTO UserMark ( ColorIndex, LocationId, StyleIndex, UserMarkGuid, Version ) VALUES ( {attribs['COLOR']}, {location_id}, 0, '{unique_id}', 1 );")
            usermark_id = self.cur.execute(f"SELECT UserMarkId FROM UserMark WHERE UserMarkGuid = '{unique_id}';").fetchone()[0]
        try:
            self.cur.execute(f"INSERT INTO BlockRange ( BlockType, Identifier, StartToken, EndToken, UserMarkId ) VALUES ( ?, ?, ?, ?, ? );", (block_type, identifier, ns, ne, usermark_id))
        except:
            pass
        return usermark_id

    def add_scripture_location(self, attribs):
        lng = self.languages[attribs['LANG']]
        self.cur.execute('INSERT INTO Location ( KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Title, Type ) SELECT ?, ?, ?, ?, ?, 0 WHERE NOT EXISTS ( SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ? );', (attribs['PUB'], lng, attribs['BK'], attribs['CH'], attribs['HEADING'], attribs['PUB'], lng, attribs['BK'], attribs['CH']))
        result = self.cur.execute('SELECT LocationId FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND BookNumber = ? AND ChapterNumber = ?;', (attribs['PUB'], lng, attribs['BK'], attribs['CH'])).fetchone()
        return result[0]

    def import_bible(self, attribs):
        location_scripture = self.add_scripture_location(attribs)
        usermark_id = self.add_usermark(attribs, location_scripture)
        block_type = 2
        try:
            block_type = int(attribs['DOC']) * 0 + 1 # special case of Bible note in book header, etc.
        except:
            pass
        result = self.cur.execute('SELECT Guid, LastModified FROM Note WHERE LocationId = ? AND Title = ? AND BlockIdentifier = ? AND BlockType = ?;', (location_scripture, attribs['TITLE'], attribs['VS'], block_type)).fetchone()
        if result:
            unique_id = result[0]
            modified = attribs['MODIFIED'] or result[1]
            created = attribs['CREATED'] or result[2]
            sql = f"UPDATE Note SET UserMarkId = {usermark_id}, Content = '{attribs['NOTE']}', LastModified = '{modified}', Created = '{created}' WHERE Guid = '{unique_id}';"
        else:
            unique_id = uuid.uuid1()
            created = attribs['CREATED'] or attribs['MODIFIED'] or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            modified = attribs['MODIFIED'] or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            sql = f"INSERT INTO Note (Guid, UserMarkId, LocationId, Title, Content, BlockType, BlockIdentifier, LastModified, Created) VALUES ('{unique_id}', {usermark_id}, {location_scripture}, '{attribs['TITLE']}', '{attribs['NOTE']}', {block_type}, {attribs['VS']}, '{modified}', '{created}' );"
        self.cur.execute(sql)
        note_id = self.cur.execute(f"SELECT NoteId from Note WHERE Guid = '{unique_id}';").fetchone()[0]
        self.process_tags(note_id, attribs['TAGS'])


    def add_publication_location(self, attribs):
        lng = self.languages[attribs['LANG']]
        issue = int(str(attribs['ISSUE']).replace('-', '').ljust(8, '0'))
        self.cur.execute('INSERT INTO Location ( IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Title, Type ) SELECT ?, ?, ?, ?, ?, 0 WHERE NOT EXISTS ( SELECT 1 FROM Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = 0);', (issue, attribs['PUB'], lng, attribs['DOC'], attribs['HEADING'], attribs['PUB'], lng, issue, attribs['DOC']))
        result = self.cur.execute('SELECT LocationId from Location WHERE KeySymbol = ? AND MepsLanguage = ? AND IssueTagNumber = ? AND DocumentId = ? AND Type = 0;', (attribs['PUB'], lng, issue, attribs['DOC'])).fetchone()
        return result[0]

    def import_publication(self, attribs):
        location_id = self.add_publication_location(attribs)
        usermark_id = self.add_usermark(attribs, location_id)
        result = self.cur.execute('SELECT Guid, LastModified FROM Note WHERE LocationId = ? AND Title = ? AND BlockIdentifier = ?;', (location_id, attribs['TITLE'], attribs['BLOCK'])).fetchone()
        if result:
            unique_id = result[0]
            modified = attribs['MODIFIED'] or result[1]
            created = attribs['CREATED'] or result[2]
            sql = f"UPDATE Note SET UserMarkId = {usermark_id}, Content = '{attribs['NOTE']}', LastModified = '{modified}', Created = '{created}' WHERE Guid = '{unique_id}';"
        else:
            created = attribs['CREATED'] or attribs['MODIFIED'] or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            modified = attribs['MODIFIED'] or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            unique_id = uuid.uuid1()
            sql = f"INSERT INTO Note (Guid, UserMarkId, LocationId, Title, Content, BlockType, BlockIdentifier, LastModified, Created) VALUES ( '{unique_id}', {usermark_id}, {location_id}, '{attribs['TITLE']}', '{attribs['NOTE']}', 1, {attribs['BLOCK']}, '{modified}', '{created}' );"
        self.cur.execute(sql)
        note_id = self.cur.execute(f"SELECT NoteId from Note WHERE Guid = '{unique_id}';").fetchone()[0]
        self.process_tags(note_id, attribs['TAGS'])


    def import_independent(self, attribs):
        result = self.cur.execute(f'SELECT Guid, LastModified, Created FROM Note WHERE Title = ? AND Content = ? AND BlockType = 0;', (attribs['TITLE'], attribs['NOTE'])).fetchone()
        if result:
            unique_id = result[0]
            modified = attribs['MODIFIED'] or result[1]
            created = attribs['CREATED'] or result[2]
            sql = f"UPDATE Note SET Content = '{attribs['NOTE']}', LastModified = '{modified}', Created = '{created}' WHERE Guid = '{unique_id}';"
        else:
            created = attribs['CREATED'] or attribs['MODIFIED'] or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            modified = attribs['MODIFIED'] or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            unique_id = uuid.uuid1()
            sql = f"INSERT INTO Note (Guid, Title, Content, BlockType, LastModified, Created) VALUES ( '{unique_id}', '{attribs['TITLE']}', '{attribs['NOTE']}', 0, '{modified}', '{created}' );"
        self.cur.execute(sql)
        note_id = self.cur.execute(f"SELECT NoteId from Note WHERE Guid = '{unique_id}';").fetchone()[0]
        self.process_tags(note_id, attribs['TAGS'])


class PreviewItems():
    def __init__(self, category, items, books, languages):
        self.category = category
        con = sqlite3.connect(f'{tmp_path}/{db_name}')
        self.cur = con.cursor()
        self.books = books
        self.languages = languages
        self.aborted = False
        self.html = ''
        self.txt = ''
        self.item_list = []
        try:
            self.items = str(items).replace('[', '(').replace(']', ')')
            if self.category == _('Notes'):
                self.get_notes()
                self.show_notes()
            else:
                self.get_annotations()
                self.show_annotations()
        except Exception as ex:
            DebugInfo(ex)
            self.aborted = True
        self.cur.close()
        con.close()


    def get_notes(self):
        sql = f'''
            SELECT n.BlockType Type,
                n.Title,
                n.Content,
                GROUP_CONCAT(t.Name, ' | '),
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
            WHERE n.NoteId IN {self.items} 
            GROUP BY n.NoteId
            ORDER BY Type, Date DESC;
            '''
        for row in self.cur.execute(sql):
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
                'ISSUE': None,
                'PUB': row[10],
                'HEADING': row[11],
                'MODIFIED': row[12][:19].replace('T', ' '),
                'CREATED': row[13][:19].replace('T', ' '),
                'COLOR': row[14] or 0
            }
            try:
                item['LANG'] = self.languages[row[4]][1]
            except:
                item['LANG'] = None
            if row[15]:
                item['RANGE'] = f'{row[15]}-{row[16]}'
            else:
                item['RANGE'] = None
            if item['TYPE'] == 1 and item['DOC']:
                if item['BLOCK']:
                    par = f"&par={item['BLOCK']}"
                    item['VS'] = None
                else:
                    par = ''
                item['LINK'] = f"https://www.jw.org/finder?wtlocale={item['LANG']}&docid={item['DOC']}{par}"
                if row[9] > 10000000:
                    issue = str(row[9])
                    yr = issue[0:4]
                    m = issue[4:6]
                    d = issue[6:]
                    if d == '00':
                        d = ''
                    else:
                        d = '-' + d
                    item['ISSUE'] = f'{yr}-{m}{d}'
                else:
                    item['ISSUE'] = ''
            elif item['TYPE'] == 2:
                item['BLOCK'] = None
                script = str(item['BK']).zfill(2) + str(item['CH']).zfill(3) + str(item['VS']).zfill(3)
                if not item['HEADING']:
                    item['HEADING'] = f"{self.books[item['BK']]} {item['CH']}"
                item['LINK'] = f"https://www.jw.org/finder?wtlocale={item['LANG']}&pub={item['PUB']}&bible={script}"
            else:
                item['LINK'] = None
            self.item_list.append(item)

    def show_notes(self):
        clrs = ['#f1f1f1', '#fffce6', '#effbe6', '#e6f7ff', '#ffe6f0', '#fff0e6', '#f1eafa']
        for item in self.item_list:
            cl = f"style='background-color: {clrs[item['COLOR']]};'"
            self.html += f"<div {cl}><b><u>{item['TITLE']}</u></b>"
            self.txt += item['TITLE']
            if item['NOTE']:
                self.html += '<br>' + item['NOTE'].replace('\n', '<br>')
                self.txt += '\n' + item['NOTE']
            if item['TAGS'] or item['PUB'] or item['LINK']:
                self.html += f"<br><small><strong><tt>__________<br>{item['MODIFIED']}"
                self.txt += '\n__________\n' + item['MODIFIED']
                if item['TAGS']:
                    self.html += '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color: #768fb8">{' + item['TAGS'] + '}</span>'
                    self.txt += '\n{' + item['TAGS'] + '}'
                if item['PUB']:
                    self.html += f"<br><i>{item['PUB']}</i>-{item['LANG']} {item['ISSUE']}"
                    self.txt += f"\n{item['PUB']}-{item['LANG']} {item['ISSUE']}"
                if item['HEADING']:
                    self.html += f"&nbsp;&mdash;&nbsp;{item['HEADING']}"
                    self.txt += ' — ' + item['HEADING']
                if item['LINK']:
                    lnk = item['LINK']
                    self.html += f"<br><a href='{lnk}'>{lnk}</a>"
                    self.txt += '\n' + lnk
                self.html += '</tt></strong></small>'
            self.html += '</div><hr>'
            self.txt += '\n==========\n'


    def get_annotations(self):
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
            WHERE LocationId IN {self.items}
            ORDER BY doc, i;
            '''
        for row in self.cur.execute(sql):
            item = {
                'tag': row[0],
                'value': row[1].rstrip() or '* '+_('NO TEXT')+' *',
                'document': row[2],
                'issue': row[3] or 0,
                'symbol': row[4],
                'source': row[4]
            }
            if item['issue'] > 10000000:
                issue = str(item['issue'])
                yr = issue[0:4]
                m = issue[4:6]
                d = issue[6:]
                if d == '00':
                    d = ''
                else:
                    d = '-' + d
                item['source'] += f' {yr}-{m}{d}'
            self.item_list.append(item)

    def show_annotations(self):
        for item in self.item_list:
            self.html += f"<div style='background-color: #f1f1f1;'><tt><b><u>{item['source']}&nbsp;&mdash;&nbsp;{item['document']}&nbsp;&mdash;&nbsp;{item['tag']}</u></b></tt><br>{item['value']}</div><hr>".replace('\\n', '<br>')
            self.txt += f"{item['source']} — {item['document']} — {item['tag']}\n{item['value']}\n==========\n".replace('\\n', '\n')


class ObscureItems():
    def __init__(self):
        con = sqlite3.connect(f'{tmp_path}/{db_name}')
        self.cur = con.cursor()
        self.cur.executescript("PRAGMA temp_store = 2; \
                                PRAGMA journal_mode = 'OFF'; \
                                BEGIN;")
        self.words = ['obscured', 'yada', 'bla', 'gibberish', 'børk']
        self.m = regex.compile(r'\p{L}')
        self.aborted = False
        try:
            self.obscure_annotations()
            self.obscure_bookmarks()
            self.obscure_notes()
            self.obscure_locations()
            con.commit()
        except Exception as ex:
            DebugInfo(ex)
            self.aborted = True
        self.cur.close()
        con.close()

    def obscure_text(self, str):
        lst = list(self.words[randint(0,len(self.words)-1)])
        l = len(lst)
        i = 0
        s = ''
        for c in str:
            if self.m.match(c):
                if c.isupper():
                    s += self.m.sub(lst[i].upper(), c)
                else:
                    s += self.m.sub(lst[i], c)
                i += 1
                if i == l:
                    i = 0
            else:
                s += c
        return s

    def obscure_locations(self):
        rows = self.cur.execute(f"SELECT Title, LocationId FROM Location;").fetchall()
        for row in rows:
            title, item = row
            if title:
                title = self.obscure_text(title).replace("'", "''")
                self.cur.execute(f"UPDATE Location SET Title = '{title}' WHERE LocationId = {item};")

    def obscure_annotations(self):
        rows = self.cur.execute(f"SELECT Value, TextTag FROM InputField;").fetchall()
        for row in rows:
            content, item = row
            if content:
                content = self.obscure_text(content).replace("'", "''")
                self.cur.execute(f"UPDATE InputField SET Value = '{content}' WHERE TextTag = '{item}';")

    def obscure_bookmarks(self):
        rows = self.cur.execute(f"SELECT Title, Snippet, BookmarkId FROM Bookmark;").fetchall()
        for row in rows:
            title, content, item = row
            if title:
                title = self.obscure_text(title).replace("'", "''")
            if content:
                content = self.obscure_text(content).replace("'", "''")
                self.cur.execute(f"UPDATE Bookmark SET Title = '{title}', Snippet = '{content}' WHERE BookmarkId = {item};")
            else:
                self.cur.execute(f"UPDATE Bookmark SET Title = '{title}' WHERE BookmarkId = {item};")

    def obscure_notes(self):
        rows = self.cur.execute(f"SELECT Title, Content, NoteId FROM Note;").fetchall()
        for row in rows:
            title, content, item = row
            if title:
                title = self.obscure_text(title).replace("'", "''")
            if content:
                content = self.obscure_text(content).replace("'", "''")
            self.cur.execute(f"UPDATE Note SET Title = '{title}', Content = '{content}' WHERE NoteId = {item};")


class Reindex():
    def __init__(self, progress):
        self.progress = progress
        con = sqlite3.connect(f'{tmp_path}/{db_name}')
        self.cur = con.cursor()
        self.cur.executescript("PRAGMA temp_store = 2; \
                                PRAGMA journal_mode = 'OFF'; \
                                PRAGMA foreign_keys = 'OFF'; \
                                BEGIN;")
        self.aborted = False
        try:
            self.reindex_notes()
            self.reindex_highlights()
            self.reindex_tags()
            self.reindex_ranges()
            self.reindex_locations()
            self.cur.executescript("PRAGMA foreign_keys = 'ON'; \
                                    VACUUM;")
            con.commit()
        except Exception as ex:
            DebugInfo(ex)
            self.aborted = True
            self.progress.close()
        self.cur.close()
        con.close()

    def make_table(self, table):
        self.cur.executescript(f"CREATE TABLE CrossReference (Old INTEGER, New INTEGER PRIMARY KEY AUTOINCREMENT); INSERT INTO CrossReference (Old) SELECT {table}Id FROM {table};")

    def update_table(self, table, field):
        app.processEvents()
        self.cur.executescript(f"UPDATE {table} SET {field} = (SELECT -New FROM CrossReference WHERE CrossReference.Old = {table}.{field}); UPDATE {table} SET {field} = abs({field});")
        self.progress.setValue(self.progress.value() + 1)

    def drop_table(self):
        self.cur.execute('DROP TABLE CrossReference;')

    def reindex_notes(self):
        self.make_table('Note')
        self.update_table('Note', 'NoteId')
        self.update_table('TagMap', 'NoteId')
        self.drop_table()

    def reindex_highlights(self):
        self.make_table('UserMark')
        self.update_table('UserMark', 'UserMarkId')
        self.update_table('Note', 'UserMarkId')
        self.update_table('BlockRange', 'UserMarkId')
        self.drop_table()

    def reindex_tags(self):
        self.make_table('TagMap')
        self.update_table('TagMap', 'TagMapId')
        self.drop_table()

    def reindex_ranges(self):
        self.make_table('BlockRange')
        self.update_table('BlockRange', 'BlockRangeId')
        self.drop_table()

    def reindex_locations(self):
        self.make_table('Location')
        self.update_table('Location', 'LocationId')
        self.update_table('Note', 'LocationId')
        self.update_table('InputField', 'LocationId')
        self.update_table('UserMark', 'LocationId')
        self.update_table('Bookmark', 'LocationId')
        self.update_table('Bookmark', 'PublicationLocationId')
        self.update_table('TagMap', 'LocationId')
        self.update_table('PlaylistItemLocationMap', 'LocationId')
        self.drop_table()


class DebugInfo():
    def __init__(self, ex):
        tb_lines = format_exception(ex.__class__, ex, ex.__traceback__)
        tb_text = ''.join(tb_lines)
        dialog = QDialog()
        dialog.setMinimumSize(650, 375)
        dialog.setWindowTitle(_('Error!'))
        label1 = QLabel()
        label1.setText("<p style='text-align: left;'>"+_('Oops! Something went wrong…')+"</p></p><p style='text-align: left;'>"+_('Take note of what you were doing and')+" <a style='color: #666699;' href='https://gitlab.com/erykj/jwlmanager/-/issues'>"+_('inform the developer')+"</a>:</p>")
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
        dialog.setLayout(layout)
        button.clicked.connect(dialog.close)
        dialog.exec()

#### Main app initialization

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
