#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File:           JWLManager

Description:    Manage .jwlibrary backup archives

MIT License     Copyright (c) 2021 Eryk J.

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

VERSION = 'v0.0.10'

import os
import re
import sqlite3
import sys
import uuid

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from datetime import datetime
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from zipfile import ZipFile, ZIP_DEFLATED

# GUI definition
from ui_main_window import Ui_MainWindow


PROJECT_PATH = Path(__file__).resolve().parent
APP = Path(__file__).stem


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.status_label = QLabel("No archive selected  ")
        self.status_label.setStyleSheet("font: italic;")
        self.status_label.setStyleSheet("color:  grey;")
        self.statusBar.addPermanentWidget(self.status_label, 0)
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.sortByColumn(1, Qt.DescendingOrder)
        self.treeWidget.setExpandsOnDoubleClick(False)
        self.treeWidget.setColumnWidth(0, 500)
        self.treeWidget.setColumnWidth(1, 30)

        self.set_vars()
        self.read_res()
        self.center()
        self.connect_signals()

    def set_vars(self):
        self.total.setText('')
        self.modified = False
        self.title_format = 'short'
        self.grouped = True
        self.save_filename = ""
        self.current_archive = ""
        self.working_dir = Path.home()
        # self.button_add.hide()
        self.button_add.setVisible(False)

    def read_res(self):
        self.publications = {}
        self.languages = {}
        con = sqlite3.connect(PROJECT_PATH / 'res/resources.db')
        cur = con.cursor()
        for row in cur.execute("SELECT * FROM Publications;"):
            self.publications[row[0]] = row[1:]
        for row in cur.execute("SELECT * FROM Languages;"):
            self.languages[row[0]] = row[1:]
        con.close()

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)


    def center(self):
        qr = self.frameGeometry()
        cp = QWidget.screen(self).availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def connect_signals(self):
        self.actionQuit.triggered.connect(self.close)
        self.actionHelp.triggered.connect(self.help)
        self.actionAbout.triggered.connect(self.about)
        self.actionNew.triggered.connect(self.new_file)
        self.actionOpen.triggered.connect(self.load_file)
        self.actionQuit.triggered.connect(self.clean_up)
        self.actionSave.triggered.connect(self.save_file)
        self.actionSave_As.triggered.connect(self.save_as_file)
        self.actionReindex.triggered.connect(self.reindex)
        self.actionExpand_All.triggered.connect(self.expand_all)
        self.actionCollapse_All.triggered.connect(self.collapse_all)
        self.actionSelect_All.triggered.connect(self.select_all)
        self.actionUnselect_All.triggered.connect(self.unselect_all)
        self.actionCode_Title.triggered.connect(self.code_view)
        self.actionShort_Title.triggered.connect(self.short_view)
        self.actionFull_Title.triggered.connect(self.full_view)
        self.actionGrouped.triggered.connect(self.grouping)
        self.combo_category.currentTextChanged.connect(self.switchboard)
        self.combo_grouping.currentTextChanged.connect(self.regroup)
        self.treeWidget.itemChanged.connect(self.tree_selection)
        self.treeWidget.doubleClicked.connect(self.double_clicked)
        self.button_export.clicked.connect(self.export)
        self.button_delete.clicked.connect(self.delete)
        self.button_import.clicked.connect(self.import_file)


    def expand_all(self):
        self.treeWidget.expandAll()

    def collapse_all(self):
        self.treeWidget.collapseAll()

    def select_all(self):
        for item in QTreeWidgetItemIterator(self.treeWidget):
            item.value().setCheckState(0, Qt.Checked)

    def unselect_all(self):
        for item in QTreeWidgetItemIterator(self.treeWidget):
            item.value().setCheckState(0, Qt.Unchecked)


    def double_clicked(self, item):
        if self.treeWidget.isExpanded(item):
            self.treeWidget.setExpanded(item, False)
        else:
            self.treeWidget.expandRecursively(item, -1)


    def code_view(self):
        if self.title_format == 'code':
            return
        self.actionShort_Title.setChecked(False)
        self.actionFull_Title.setChecked(False)
        self.title_format = 'code'
        self.regroup()

    def short_view(self):
        if self.title_format == 'short':
            return
        self.actionCode_Title.setChecked(False)
        self.actionFull_Title.setChecked(False)
        self.title_format = 'short'
        self.regroup()

    def full_view(self):
        if self.title_format == 'full':
            return
        self.actionShort_Title.setChecked(False)
        self.actionCode_Title.setChecked(False)
        self.title_format = 'full'
        self.regroup()


    def grouping(self):
        self.grouped = not self.grouped
        self.regroup()


    def switchboard(self, selection):
        self.combo_grouping.setCurrentText('Publication')
        if selection == "Notes":
            self.disable_options([], False, True, True)
        elif selection == "Highlights":
            self.disable_options([3], False, True, True)
        elif selection == "Bookmarks":
            self.disable_options([3,4], False, False, False)
        elif selection == "Annotations":
            self.disable_options([3,4], False, True, True)
        elif selection == "Favorites":
            self.disable_options([3,4], True, False, False)
        self.regroup()

    def disable_options(self, list=[], add=False, exp=False, imp=False):
        self.button_add.setVisible(add)
        self.button_export.setVisible(exp)
        self.button_import.setEnabled(imp)
        self.button_import.setVisible(imp)
        for item in range(5):
            self.combo_grouping.model().item(item).setEnabled(True)
        for item in list:
            self.combo_grouping.model().item(item).setEnabled(False)

    def regroup(self):
        tree = BuildTree(self.treeWidget, self.publications, self.languages,
                          self.combo_category.currentText(),
                          self.combo_grouping.currentText(), self.title_format,
                          self.grouped)
        self.leaves = tree.leaves
        self.total.setText(f"**{tree.total:,}**")


    def help(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("README")
        dialog.setMinimumSize(800, 800)
        text = QTextEdit(dialog)
        text.setReadOnly(True)
        text.setMarkdown(open(self.resource_path('README.md')).read())
        layout = QHBoxLayout(dialog)
        layout.addWidget(text)
        dialog.setLayout(layout)
        dialog.show()

    def about(self):
        dialog = QMessageBox(self, self, "", "", QMessageBox.Ok)
        text = f"""
            <h2 style="text-align: center;"><span style="color: #800080;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;JWLManager</span></h2>
            <h4 style="text-align: center;">&nbsp;&nbsp;&nbsp;{VERSION}</h4>
            <p style="text-align: center;"><em>&nbsp;&nbsp;&nbsp;&copy;2022 Eryk J.</em></p>
            <p style="text-align: center;"><span style="color: #666699;"><a style="color: #666699;" href="https://gitlab.com/erykj/jwlmanager">https://gitlab.com/erykj/jwlmanager</a></span></p>
                """
        dialog.setText(text)
        label = QLabel(dialog)
        label.setPixmap(self.resource_path('icons/project_72.png'))
        label.setGeometry(10,12,72,72)  
        dialog.setWindowFlag(Qt.FramelessWindowHint)
        dialog.exec()


    def new_file(self):
        if self.modified:
            reply = QMessageBox.question(self, 'Save', 'Save current archive?', 
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
                QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return
        self.status_label.setStyleSheet("color:  black;")
        self.status_label.setText("* NEW ARCHIVE *  ")
        with ZipFile(self.resource_path("res/blank.jwlibrary"),"r") as zipped:
            zipped.extractall(tmp_path)
        file = open(f"{tmp_path}/manifest.json", 'w')
        text = r'{"name":"UserDataBackup","creationDate":"' + datetime.now().strftime("%Y-%m-%d") + r'","version":1,"type":0,"userDataBackup":{"userMarkCount":0,"lastModifiedDate":"' + datetime.now().strftime("%Y-%m-%dT%H:%M") + r'","deviceName":"JWLManager","databaseName":"userData.db","hash":"","schemaVersion":8}}'
        file.write(text)
        file.close
        self.file_loaded()

    def load_file(self):
        if self.modified:
            reply = QMessageBox.question(self, 'Save', 'Save current archive?', 
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
                QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return
        fname = QFileDialog.getOpenFileName(self, 'Open archive', 
                str(self.working_dir),"JW Library archives (*.jwlibrary)")
        if fname[0] == "":
            return
        self.current_archive = Path(fname[0])
        self.working_dir = Path(fname[0]).parent
        self.status_label.setStyleSheet("color:  black;")
        self.status_label.setText(f"{Path(fname[0]).stem}  ")
        with ZipFile(fname[0],"r") as zipped:
            zipped.extractall(tmp_path)
        self.file_loaded()

    def file_loaded(self):
        self.actionReindex.setEnabled(True)
        self.combo_grouping.setEnabled(True)
        self.combo_category.setEnabled(True)
        self.actionSave_As.setEnabled(True)
        self.actionCollapse_All.setEnabled(True)
        self.actionExpand_All.setEnabled(True)
        self.actionSelect_All.setEnabled(True)
        self.actionUnselect_All.setEnabled(True)
        self.actionGrouped.setEnabled(True)
        self.menuTitle_View.setEnabled(True)
        self.switchboard(self.combo_category.currentText())


    def trim_db(self):
        con = sqlite3.connect(f"{tmp_path}/userData.db")
        cur = con.cursor()
        sql = """
            PRAGMA temp_store = 2;
            PRAGMA journal_mode = 'OFF';
            PRAGMA foreign_keys = 'OFF';
            BEGIN;
            DELETE FROM Note WHERE (Title IS NULL OR Title = '')
              AND (Content IS NULL OR Content = '');
            DELETE FROM Location WHERE LocationId NOT IN
              (SELECT LocationId FROM UserMark) AND LocationId NOT IN
              (SELECT LocationId FROM Note WHERE LocationId IS NOT NULL)
              AND LocationId NOT IN (SELECT LocationId FROM TagMap
              WHERE LocationId IS NOT NULL) AND LocationId NOT IN
              (SELECT LocationId FROM Bookmark) AND LocationId NOT IN 
              (SELECT PublicationLocationId FROM Bookmark)
              AND LocationId NOT IN (SELECT LocationId FROM InputField);
            DELETE FROM UserMark WHERE UserMarkId NOT IN (SELECT UserMarkId
              FROM BlockRange) AND LocationId NOT IN
              (SELECT LocationId FROM Location);
            DELETE FROM BlockRange WHERE UserMarkId NOT IN
              (SELECT UserMarkId FROM UserMark);
            DELETE FROM TagMap WHERE NoteId IS NOT NULL AND NoteId
              NOT IN (SELECT NoteId FROM Note);
            DELETE FROM Tag WHERE TagId NOT IN (SELECT TagId FROM TagMap);
            PRAGMA foreign_keys = 'ON';
            COMMIT;
            VACUUM;"""
        cur.executescript(sql)
        con.close()
        self.archive_modified()


    def save_file(self):
        if self.save_filename == '':
            return self.save_as_file()
        else:
            self.zipfile()

    def save_as_file(self):
        fname = ()
        if self.save_filename == '':
            now = datetime.now().strftime("%Y-%m-%d")
            fname = QFileDialog.getSaveFileName(self, 'Save archive',
                        f"{self.working_dir}/MODIFIED_{now}.jwlibrary",
                        "JW Library archives (*.jwlibrary)")
        else:
            fname = QFileDialog.getSaveFileName(self, 'Save archive',
                        self.save_filename, "JW Library archives (*.jwlibrary)")
        if fname[0] == '':
            self.statusBar.showMessage(" NOT saved!", 3500)
            return False
        elif Path(fname[0]) == self.current_archive:
            reply = QMessageBox.critical(self, 'Save', "It's recommended to save under another name.\nAre you absolutely sure you want to replace the original?",
              QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return self.save_file()
        self.save_filename = fname[0]
        self.status_label.setText(f"{Path(fname[0]).stem}  ")
        self.zipfile()

    def zipfile(self):
        with ZipFile(self.save_filename, "w", compression=ZIP_DEFLATED) as newzip:
            newzip.write(f"{tmp_path}/manifest.json", "manifest.json")
            newzip.write(f"{tmp_path}/userData.db", "userData.db")
        self.archive_saved()


    def archive_modified(self):
        self.modified = True
        self.actionSave.setEnabled(True)
        self.actionSave_As.setEnabled(True)
        self.status_label.setStyleSheet("font: italic;")

    def archive_saved(self):
        self.modified = False
        self.actionSave.setEnabled(False)
        self.status_label.setStyleSheet("font: normal;")
        self.statusBar.showMessage(" Saved", 3500)


    def tree_selection(self):
        self.selected_items = 0
        it = QTreeWidgetItemIterator(self.treeWidget,
                  QTreeWidgetItemIterator.Checked)
        for item in it:
            index = item.value().data(0, Qt.UserRole)
            if index in self.leaves:
                self.selected_items += len(self.leaves[index])
        self.selected.setText(f"**{self.selected_items:,}**")
        self.button_delete.setEnabled(self.selected_items)
        self.button_export.setEnabled(self.selected_items and self.combo_category.currentText() in ('Notes', 'Highlights', 'Annotations'))


    def export(self):
        reply = QMessageBox.question(self, 'Export',
                f"{self.selected_items} items will be EXPORTED. Proceed?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.No:
            return
        selected = []
        it = QTreeWidgetItemIterator(self.treeWidget,
                  QTreeWidgetItemIterator.Checked)
        for item in it:
            index = item.value().data(0, Qt.UserRole)
            if index in self.leaves:
                for id in self.leaves[index]:
                    selected.append(id)
        fname = self.export_file()
        if fname[0] == '':
            self.statusBar.showMessage(" NOT exported!", 3500)
            return
        ExportItems(self.combo_category.currentText(), selected, fname[0],
            Path(self.current_archive).stem)
        self.statusBar.showMessage("Items exported", 3500)

    def export_file(self):
        fname = ()
        now = datetime.now().strftime("%Y-%m-%d")
        fname = QFileDialog.getSaveFileName(self, 'Export file',
                    f"{self.working_dir}/JWL_{self.combo_category.currentText()}_{now}.txt",
                    "Text files (*.txt)")
        return fname


    def import_file(self):
        reply = QMessageBox.warning(self, 'Import',
                "Make sure your import file is properly formatted.\n\nImporting will modify the archive. Proceed?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        fname = QFileDialog.getOpenFileName(self, 'Import file', f"{self.working_dir}/", "Import files (*.txt)")
        if fname[0] == "":
            self.statusBar.showMessage(" NOT imported!", 3500)
            return
        self.working_dir = Path(fname[0]).parent
        self.statusBar.showMessage(" Importing. Please wait...")
        app.processEvents()
        if self.combo_category.currentText() == 'Annotations':
            count = ImportAnnotations(fname[0]).count
        elif self.combo_category.currentText() == 'Highlights':
            count = ImportHighlights(fname[0]).count
        elif self.combo_category.currentText() == 'Notes':
            count = ImportNotes(fname[0]).count
        if not count:
            self.statusBar.showMessage(" NOT imported!", 3500)
            return
        self.trim_db()
        self.statusBar.showMessage(f" {count} items imported/updated", 3500)
        self.archive_modified()
        self.regroup()
        self.tree_selection()


    def delete(self):
        reply = QMessageBox.warning(self, 'Delete',
                f"Are you sure you want to\nDELETE these {self.selected_items} items?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        selected = []
        it = QTreeWidgetItemIterator(self.treeWidget,
                  QTreeWidgetItemIterator.Checked)
        for item in it:
            index = item.value().data(0, Qt.UserRole)
            if index in self.leaves:
                for id in self.leaves[index]:
                    selected.append(id)
        result = DeleteItems(self.combo_category.currentText(), selected).result
        self.statusBar.showMessage(f" {result} items deleted", 3500)
        self.trim_db()
        self.regroup()
        self.tree_selection()


    def closeEvent(self, event):
        if self.modified:
            reply = QMessageBox.question(self, 'Exit', 'Save before quitting?', QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
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
        rmtree(tmp_path, ignore_errors=True)


    def reindex(self):
        reply = QMessageBox.information(self, 'Reindex',
                'This may take a few seconds. Proceed?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.No:
            return
        self.trim_db()
        self.pd = QProgressDialog("Please be patient...", None, 0, 14, self)
        self.pd.setWindowModality(Qt.WindowModal)
        self.pd.setWindowTitle('Reindexing')
        self.pd.setWindowFlag(Qt.FramelessWindowHint)
        self.pd.setModal(True)
        self.pd.setMinimumDuration(0)
        self.statusBar.showMessage(" Reindexing. Please wait...")
        app.processEvents()
        Reindex(self.pd)
        self.statusBar.showMessage(" Reindexed successfully", 3500)
        self.archive_modified()
        self.regroup()


class BuildTree():
    def __init__(self, tree, publications, languages, category='Note', grouping='Publication', title='code', grouped=True):
        self.tree = tree
        self.tree.clear()
        self.category = category
        self.grouping = grouping
        self.grouped = grouped
        self.publications = publications
        self.languages = languages
        self.title_format = title
        self.nodes = {}
        self.leaves = {}
        self.total = 0
        con = sqlite3.connect(f"{tmp_path}/userData.db")
        self.cur = con.cursor()
        self.cur.executescript("PRAGMA temp_store = 2; \
                                PRAGMA journal_mode = 'OFF';")
        self.build_tree()
        con.commit()
        con.close()


    def build_tree(self):
        if self.category == "Bookmarks":
            self.get_bookmarks()
        elif self.category == "Favorites":
            self.get_favorites()
        elif self.category == "Highlights":
            self.get_highlights()
        elif self.category == "Notes":
            self.get_notes()
        elif self.category == "Annotations":
            self.get_annotations()

    def get_annotations(self):
        sql = "SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, TextTag, '', 0 FROM InputField JOIN Location l USING (LocationId);"
        for row in self.cur.execute(sql):
            item = row[4]
            publication = self.process_name(row[1] or 'MEDIA')
            language = self.process_language(row[2])
            issue = self.process_issue(row[3])
            tag = (row[5] or "* UN-TAGGED *", None)
            color = (('Grey', 'Yellow', 'Green', 'Blue', 'Purple', 'Red', 'Orange')[row[6] or 0], None)
            self.build_index(publication, language, issue, tag, color, item)

    def get_bookmarks(self):
        sql = "SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, PublicationLocationId, '', 0 FROM Bookmark b JOIN Location l USING (LocationId) GROUP BY b.PublicationLocationId;"
        for row in self.cur.execute(sql):
            item = row[4]
            publication = self.process_name(row[1] or 'MEDIA')
            language = self.process_language(row[2])
            issue = self.process_issue(row[3])
            tag = (row[5] or "* UN-TAGGED *", None)
            color = (('Grey', 'Yellow', 'Green', 'Blue', 'Purple', 'Red', 'Orange')[row[6] or 0], None)
            self.build_index(publication, language, issue, tag, color, item)

    def get_favorites(self):
        sql = "SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, TagMapId, 'Favorite', 0 FROM TagMap tm JOIN Location l USING (LocationId) WHERE tm.NoteId IS NULL order by tm.Position;"
        for row in self.cur.execute(sql):
            item = row[4]
            publication = self.process_name(row[1] or 'MEDIA')
            language = self.process_language(row[2])
            issue = self.process_issue(row[3])
            tag = (row[5] or "* UN-TAGGED *", None)
            color = (('Grey', 'Yellow', 'Green', 'Blue', 'Purple', 'Red', 'Orange')[row[6] or 0], None)
            self.build_index(publication, language, issue, tag, color, item)

    def get_highlights(self):
        sql = "SELECT LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, UserMarkId, '', ColorIndex FROM UserMark JOIN Location l USING (LocationId);"
        for row in self.cur.execute(sql):
            item = row[4]
            publication = self.process_name(row[1] or 'MEDIA')
            language = self.process_language(row[2])
            issue = self.process_issue(row[3])
            tag = (row[5] or "* UN-TAGGED *", None)
            color = (('Grey', 'Yellow', 'Green', 'Blue', 'Purple', 'Red', 'Orange')[row[6] or 0], None)
            self.build_index(publication, language, issue, tag, color, item)

    def get_notes(self):
        sql = "SELECT 0, 0, '', '', NoteId, GROUP_CONCAT(t.Name), 0 FROM Note n JOIN TagMap tm USING (NoteId) JOIN Tag t USING (TagId) WHERE n.BlockType = 0 GROUP BY n.NoteId;" # independent
        for row in self.cur.execute(sql):
            item = row[4]
            publication = ("Other", "* INDEPENDENT *", None, None)
            language = ("* MULTI-LANGUAGE *", None)
            issue = (None, None)
            tag = (row[5] or "* UN-TAGGED *", None)
            color = ('Grey', None)
            self.build_index(publication, language, issue, tag, color, item)

        sql = "SELECT l.LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, NoteId, GROUP_CONCAT(t.Name), u.ColorIndex FROM Note n JOIN Location l USING (LocationId) LEFT JOIN TagMap tm USING (NoteId) LEFT JOIN Tag t USING (TagId) LEFT JOIN UserMark u USING (UserMarkId) GROUP BY n.NoteId;" # other
        for row in self.cur.execute(sql):
            item = row[4]
            publication = self.process_name(row[1] or '* MEDIA *')
            language = self.process_language(row[2])
            issue = self.process_issue(row[3])
            tag = (row[5] or "* UN-TAGGED *", None)
            color = (('Grey', 'Yellow', 'Green', 'Blue', 'Purple', 'Red', 'Orange')[row[6] or 0], None)
            self.build_index(publication, language, issue, tag, color, item)


    def process_name(self, name):
        group, name, tip, year = self.check_name(name)
        if tip:
            return (group, name, tip, year)
        stripped = re.search('(.*?)(?!-)(\d+$)', name)
        if stripped:
            prefix = stripped.group(1)
            suffix = stripped.group(2)
            name = prefix
            group, name, tip, year = self.check_name(name)
            if not year:
                if int(suffix) >= 50:
                    year = '19' + suffix
                else:
                    year = '20' + suffix
        if not tip:
            tip = '?'
        return (group, name, tip, year)

    def check_name(self, name):
        tip = ''
        group = ''
        year = ''
        if name in self.publications.keys():
            group = self.publications[name][3]
            if self.title_format == 'code':
                tip = self.publications[name][0]
            elif self.title_format == 'short':
                tip = name
                name = self.publications[name][0]
            else:
                tip = name
                name = self.publications[name][1]
        return group, name, tip, year

    def process_language(self, lang):
        if lang in self.languages.keys():
            name = self.languages[lang][0]
            tip = self.languages[lang][1]
        else:
            name = f"Language #{lang}"
            tip = None
        return (name, tip)

    def process_issue(self, doc):
        if doc:
            y = str(doc)[0:4]
            m = str(doc)[4:6]
            mo = ('Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'June', 'July',
                  'Aug.', 'Sep.', 'Oct.', 'Nov.', 'Dec.')[int(m)-1]
            d = str(doc)[6:]
            if d == '00':
                name = f"{y}-{m}"
                tip = f"{mo}, {y}"
            else:
                name = f"{y}-{m}-{d}"
                tip = f"{mo} {int(d)}, {y}"
            return (name, tip)
        else:
            return ('', '')


    def build_index(self, publication, language, issue, tag, color, item):
        self.total += 1
        index = ''
        parent = self.tree
        if publication[3] and not issue[0]:
            issue = (publication[3], '')
        group = (publication[0], '')
        publication = (publication[1], publication[2])
        if self.grouping == "Publication":
            if self.grouped:
                levels = (group, publication, language, issue)
            else:
                levels = (publication, language, issue)
        elif self.grouping == "Language":
            levels = (language, publication, issue)
        elif self.grouping == "Tag":
            levels = (tag, publication, language, issue)
        elif self.grouping == "Color":
            levels = (color, publication, language, issue)
        elif self.grouping == "Year":
            if issue[0]:
                year = (issue[0][:4], '')
            else:
                year = ('* NO DATE *', '')
            if year[0] == issue[0]:
                issue = ('', '')
            levels = (year, publication, language, issue)
        for level in levels:
            if level[0]:
                index += f".{level[0]}"
                parent = self.check_node(parent, level, index)
        self.leaves[index].append(item)
        parent.setData(0, Qt.UserRole, index)

    def check_node(self, parent, data, index):
        if index not in self.nodes:
            parent = self.nodes[index] = self.add_node(parent, data)
            self.leaves[index] = []
        else:
            parent = self.nodes[index]
        parent.setData(1, Qt.DisplayRole, parent.data(1, Qt.DisplayRole) + 1)
        return parent

    def add_node(self, parent, data):
        child = QTreeWidgetItem(parent)
        child.setFlags(child.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
        child.setText(0, data[0])
        if data[1]:
            child.setToolTip(0, f"          {data[1]}")
        child.setCheckState(0, Qt.Unchecked)
        child.setData(1, Qt.DisplayRole, 0)
        child.setTextAlignment(1, Qt.AlignCenter)
        return child


class DeleteItems():
    def __init__(self, category='Note', items=[]):
        self.category = category
        self.items = str(items).replace('[', '(').replace(']', ')')

        con = sqlite3.connect(f"{tmp_path}/userData.db")
        self.cur = con.cursor()
        self.cur.executescript("PRAGMA temp_store = 2; \
                                PRAGMA journal_mode = 'OFF'; \
                                PRAGMA foreign_keys = 'OFF';")
        self.result = self.delete_items()
        self.cur.execute("PRAGMA foreign_keys = 'ON';")
        con.commit()
        con.close()

    def delete_items(self):
        if self.category == "Bookmarks":
            return self.delete_bookmarks()
        elif self.category == "Favorites":
            return self.delete_favorites()
        elif self.category == "Highlights":
            return self.delete_highlights()
        elif self.category == "Notes":
            return self.delete_notes()
        elif self.category == "Annotations":
            return self.delete_annotations()

    def delete_annotations(self):
        sql = f"DELETE FROM InputField WHERE TextTag IN {self.items};"
        return self.cur.execute(sql).rowcount

    def delete_bookmarks(self):
        sql = f"DELETE FROM Bookmark WHERE PublicationLocationId IN {self.items};"
        return self.cur.execute(sql).rowcount

    def delete_favorites(self):
        sql = f"DELETE FROM TagMap WHERE TagMapId IN {self.items};"
        return self.cur.execute(sql).rowcount

    def delete_highlights(self):
        sql = f"DELETE FROM UserMark WHERE UserMarkId IN {self.items};"
        return self.cur.execute(sql).rowcount

    def delete_notes(self):
        sql = f"DELETE FROM Note WHERE NoteId IN {self.items};"
        return self.cur.execute(sql).rowcount


class ExportItems():
    def __init__(self, category='Note', items=[], fname='', current_archive=''):
        self.category = category
        self.items = str(items).replace('[', '(').replace(']', ')')
        self.current_archive = current_archive
        con = sqlite3.connect(f"{tmp_path}/userData.db")
        self.cur = con.cursor()
        self.export_file = open(fname, 'w')
        self.export_items()
        self.export_file.close
        con.close()

    def export_items(self):
        if self.category == "Highlights":
            return self.export_highlights()
        elif self.category == "Notes":
            return self.export_notes()
        elif self.category == "Annotations":
            return self.export_annotations()

    def export_notes(self):
        self.export_note_header()
        self.export_bible()
        self.export_publications()
        self.export_independent()
        self.export_file.write('\n==={END}===')

    def export_note_header(self):
        self.export_file.write('\n'.join(['{TITLE=}\n',
            'MODIFY FIELD ABOVE BEFORE RE-IMPORTING',
            'LEAVE {TITLE=} (empty) IF YOU DON\'T WANT TO DELETE ANY NOTES WHILE IMPORTING\n',
            'EACH NOTE STARTS WITH HEADER INDICATING CATEGORY, ETC.',
            'BE CAREFUL WHEN MODIFYING THE ATTRIBUTES\n',
            'LINE AFTER HEADER IS NOTE TITLE',
            'REST IS NOTE BODY; CAN BE MULTI-LINE AND IS TERMINATED BY NEXT NOTE HEADER\n',
            'SEPARATE TAGS WITH "," (commas)',
            'OR LEAVE EMPTY IF NO TAG: {TAGS=bible,notes} OR {TAGS=}']))
        self.export_file.write(f"\n\nExported from {self.current_archive}\nby {APP} ({VERSION}) on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}\n\n")
        self.export_file.write('*' * 79)

    def export_bible(self):
        for row in self.cur.execute(f"SELECT l.MepsLanguage, l.KeySymbol, l.BookNumber,  l.ChapterNumber, n.BlockIdentifier, u.ColorIndex,  n.Title, n.Content, GROUP_CONCAT(t.Name) FROM Note n  JOIN Location l USING (LocationId) LEFT JOIN TagMap tm USING (NoteId) LEFT JOIN Tag t USING (TagId) LEFT JOIN UserMark u USING (UserMarkId)  WHERE n.BlockType = 2 AND NoteId IN {self.items} GROUP BY n.NoteId;"):
            color = str(row[5] or 0)
            tags = row[8] or ''
            txt = "\n==={CAT=BIBLE}{LANG="+str(row[0])+"}{ED="+str(row[1])\
                +"}{BK="+str(row[2])+"}{CH="+str(row[3])+"}{VER="+str(row[4])\
                +"}{COLOR="+color+"}{TAGS="+tags+"}===\n"+row[6]+"\n"+row[7].rstrip()
            self.export_file.write(txt)

    def export_publications(self):
        for row in self.cur.execute(f"SELECT l.MepsLanguage, l.KeySymbol, l.IssueTagNumber, l.DocumentId, n.BlockIdentifier, u.ColorIndex, n.Title, n.Content, GROUP_CONCAT(t.Name) FROM Note n JOIN Location l USING (LocationId) LEFT JOIN TagMap tm USING (NoteId) LEFT JOIN Tag t USING (TagId) LEFT JOIN UserMark u USING (UserMarkId) WHERE n.BlockType = 1 AND NoteId IN {self.items} GROUP BY n.NoteId;"):
            color = str(row[5] or 0)
            tags = row[8] or ''
            txt = "\n==={CAT=PUBLICATION}{LANG="+str(row[0])+"}{PUB="\
                    +str(row[1])+"}{ISSUE="+str(row[2])+"}{DOC="+str(row[3])\
                    +"}{BLOCK="+str(row[4])+"}{COLOR="+color+"}{TAGS="+tags\
                    +"}===\n"+row[6]+"\n"+row[7].rstrip()
            self.export_file.write(txt)

    def export_independent(self):
        for row in self.cur.execute(f"SELECT n.Title, n.Content, GROUP_CONCAT(t.Name) FROM Note n JOIN TagMap tm USING (NoteId) JOIN Tag t USING (TagId) WHERE n.BlockType = 0 AND NoteId IN {self.items} GROUP BY n.NoteId;"):
            tags = row[2] or ''
            txt = "\n==={CAT=INDEPENDENT}{TAGS="+tags\
                    +"}===\n"+row[0]+"\n"+row[1].rstrip()
            self.export_file.write(txt)


    def export_highlights(self):
        self.export_highlight_header()
        for row in self.cur.execute(f"SELECT b.BlockType, b.Identifier, b.StartToken, b.EndToken, u.ColorIndex, u.Version, l.BookNumber, l.ChapterNumber, l.DocumentId, l.IssueTagNumber, l.KeySymbol, l.MepsLanguage, l.Type FROM BlockRange b JOIN UserMark u USING(UserMarkId) JOIN Location l USING (LocationId) WHERE UserMarkId IN {self.items};"):
            self.export_file.write(f"\n{row[0]}")
            for item in range(1,13):
                self.export_file.write(f",{row[item]}")

    def export_highlight_header(self):
        self.export_file.write('{HIGHLIGHTS}\n\nTHIS FILE IS NOT MEANT TO BE MODIFIED MANUALLY\nYOU CAN USE IT TO BACKUP/TRANSFER/MERGE SELECTED HIGHLIGHTS\n\nFIELDS: BlockRange.BlockType, BlockRange.Identifier, BlockRange.StartToken,\n        BlockRange.EndToken, UserMark.ColorIndex, UserMark.Version,\n        Location.BookNumber, Location.ChapterNumber, Location.DocumentId,\n        Location.IssueTagNumber, Location.KeySymbol, Location.MepsLanguage,\n        Location.Type')
        self.export_file.write(f"\n\nExported from {self.current_archive}\nby {APP} ({VERSION}) on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}\n\n")
        self.export_file.write('*' * 79)


    def export_annotations(self):
        self.export_annotations_header()
        for row in self.cur.execute(f"SELECT l.DocumentId, l.IssueTagNumber, l.KeySymbol, l.MepsLanguage, l.Type, TextTag, Value FROM InputField JOIN Location l USING (LocationId) WHERE TextTag IN {self.items};"):
            self.export_file.write(f"\n{row[0]}")
            for item in range(1,7):
                string = str(row[item]).replace("\n", r"\n")
                self.export_file.write(f",{string}")

    def export_annotations_header(self):
        self.export_file.write('{ANNOTATIONS}\n\nTHIS FILE IS NOT MEANT TO BE MODIFIED MANUALLY\nYOU CAN USE IT TO BACKUP/TRANSFER/MERGE SELECTED ANNOTATIONS\n\nFIELDS: Location.DocumentId, Location.IssueTagNumber, Location.KeySymbol,\n        Location.MepsLanguage, Location.Type, InputField.TextTag,\n        InputField.Value')
        self.export_file.write(f"\n\nExported from {self.current_archive}\nby {APP} ({VERSION}) on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}\n\n")
        self.export_file.write('*' * 79)


class ImportAnnotations():
    def __init__(self, fname=''):
        # self.app = self
        con = sqlite3.connect(f"{tmp_path}/userData.db")
        self.cur = con.cursor()
        self.import_file = open(fname, 'r')
        if self.pre_import():
            self.count = self.import_items()
        else:
            self.count = 0
        self.import_file.close
        con.close()

    def pre_import(self):
        line = self.import_file.readline()
        if re.search('{ANNOTATIONS}', line):
            return True
        else:
            QMessageBox.critical(None, 'Error!', 'Wrong import file format:\nMissing {ANNOTATIONS} tag line', QMessageBox.Abort)
            return False

    def import_items(self):
        count = 0
        while not re.match("\*\*\*\*\*", self.import_file.readline()):
            pass
        self.cur.execute("BEGIN;")
        for line in self.import_file.readlines():
            try:
                count += 1
                attribs = re.split(',', line.rstrip(), 6)
                location_id = self.add_location(attribs)
                value = attribs[6].replace(r"\n", "\n")
                if self.cur.execute(f"SELECT * FROM InputField WHERE LocationId = {location_id} AND TextTag = '{attribs[5]}';").fetchone():
                    self.cur.execute(f"UPDATE InputField SET Value = '{value}' WHERE LocationId = {location_id} AND TextTag = '{attribs[5]}'")
                else:
                    self.cur.execute(f"INSERT INTO InputField (LocationId, TextTag, Value) VALUES ({location_id}, '{attribs[5]}', '{value}');")
            except:
                QMessageBox.critical(None, 'Error!', f'Error on import!\nFaulting entry #{count}:\n{attribs}', QMessageBox.Abort)
                self.cur.execute("ROLLBACK;")
                return 0
        self.cur.execute("COMMIT;")
        return count

    def add_location(self, attribs):
        # Add new location if it doesn't already exist
        self.cur.execute(f"INSERT INTO Location (DocumentId, IssueTagNumber, KeySymbol, MepsLanguage, Type) SELECT {int(attribs[0])}, {int(attribs[1])}, '{attribs[2]}', {int(attribs[3])}, {int(attribs[4])} WHERE NOT EXISTS ( SELECT 1 FROM Location WHERE DocumentId = {int(attribs[0])} AND IssueTagNumber = {int(attribs[1])} AND KeySymbol = '{attribs[2]}' AND MepsLanguage = {int(attribs[3])} AND Type = {int(attribs[4])});")
        result = self.cur.execute(f"SELECT LocationId FROM Location WHERE DocumentId = {int(attribs[0])} AND IssueTagNumber = {int(attribs[1])} AND KeySymbol = '{attribs[2]}' AND MepsLanguage = {int(attribs[3])} AND Type = {int(attribs[4])};").fetchone()
        return result[0]


class ImportHighlights():
    def __init__(self, fname=''):
        con = sqlite3.connect(f"{tmp_path}/userData.db")
        self.cur = con.cursor()
        self.import_file = open(fname, 'r')
        if self.pre_import():
            self.count = self.import_items()
        else:
            self.count = 0
        self.import_file.close
        con.close()

    def pre_import(self):
        line = self.import_file.readline()
        if re.search('{HIGHLIGHTS}', line):
            return True
        else:
            QMessageBox.critical(None, 'Error!', 'Wrong import file format:\nMissing {HIGHLIGHTS} tag line', QMessageBox.Abort)
            return False

    def import_items(self):
        count = 0
        while not re.match("\*\*\*\*\*", self.import_file.readline()):
            pass
        self.cur.execute("BEGIN;")
        for line in self.import_file.readlines():
            try:
                count += 1
                attribs = re.split(',', line.rstrip().replace("None", ""))
                if attribs[6]:
                    location_id = self.add_scripture_location(attribs)
                else:
                    location_id = self.add_publication_location(attribs)
                self.import_highlight(attribs, location_id)
            except:
                QMessageBox.critical(None, 'Error!', f'Error on import!\nFaulting entry #{count}:\n{attribs}', QMessageBox.Abort)
                self.cur.execute("ROLLBACK;")
                return 0
        self.cur.execute("COMMIT;")
        return count

    def add_scripture_location(self, attribs):
        # Add new location if it doesn't already exist
        self.cur.execute(f"INSERT INTO Location ( KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Type ) SELECT '{attribs[10]}', {int(attribs[11])}, {int(attribs[6])}, {int(attribs[7])}, {int(attribs[12])} WHERE NOT EXISTS ( SELECT 1 FROM Location WHERE KeySymbol = '{attribs[10]}' AND MepsLanguage = {int(attribs[11])} AND BookNumber = {int(attribs[6])} AND ChapterNumber = {int(attribs[7])} );")
        result = self.cur.execute(f"SELECT LocationId FROM Location WHERE KeySymbol = '{attribs[10]}' AND MepsLanguage = {int(attribs[11])} AND BookNumber = {int(attribs[6])} AND ChapterNumber = {int(attribs[7])};").fetchone()
        return result[0]

    def add_publication_location(self, attribs):
        # Add new location if it doesn't already exist
        self.cur.execute(f"INSERT INTO Location ( IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Type ) SELECT {int(attribs[9])}, '{attribs[10]}', {int(attribs[11])}, {int(attribs[8])}, {int(attribs[12])} WHERE NOT EXISTS ( SELECT 1 FROM Location WHERE KeySymbol = '{attribs[10]}' AND MepsLanguage = {int(attribs[11])} AND IssueTagNumber = {int(attribs[9])} AND DocumentId = {int(attribs[8])} AND Type = {int(attribs[12])});")
        result = self.cur.execute(f"SELECT LocationId FROM Location WHERE KeySymbol = '{attribs[10]}' AND MepsLanguage = {int(attribs[11])} AND IssueTagNumber = {int(attribs[9])} AND DocumentId = {int(attribs[8])} AND Type = {int(attribs[12])};").fetchone()
        return result[0]

    def add_usermark(self, attribs, location_id):
        unique_id = uuid.uuid1()
        self.cur.execute(f"INSERT INTO UserMark ( ColorIndex, LocationId, StyleIndex, UserMarkGuid, Version ) SELECT {int(attribs[4])}, {location_id}, 0, '{unique_id}', {int(attribs[5])};")
        result = self.cur.execute(f"SELECT UserMarkId FROM UserMark WHERE UserMarkGuid = '{unique_id}';").fetchone()
        return result[0]

    def import_highlight(self, attribs, location_id):
        usermark_id = self.add_usermark(attribs, location_id)
        result = self.cur.execute(f"SELECT * FROM BlockRange join UserMark USING (UserMarkId) where Identifier = {int(attribs[1])} AND LocationId = {location_id};")
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
        self.cur.execute(f"INSERT INTO BlockRange (BlockType, Identifier, StartToken, EndToken, UserMarkId) VALUES ({int(attribs[0])}, {int(attribs[1])}, {ns}, {ne}, {usermark_id});")
        return


class ImportNotes():
    def __init__(self, fname=''):
        # self.app = self
        con = sqlite3.connect(f"{tmp_path}/userData.db")
        self.cur = con.cursor()
        self.import_file = open(fname, 'r')
        if self.pre_import():
            self.count = self.import_items()
        else:
            self.count = 0
        self.import_file.close
        con.close()

    def pre_import(self):
        line = self.import_file.readline()
        m = re.search('\{TITLE=(.?)\}', line)
        if m:
            title_char = m.group(1) or ''
        else:
            QMessageBox.critical(None, 'Error!', 'Wrong import file format:\nMissing or malformed {TITLE=} attribute line', QMessageBox.Abort)
            return False
        if title_char:
            self.delete_notes(title_char)
        return True

    def delete_notes(self, title_char):
        results = len(self.cur.execute(f"SELECT NoteId FROM Note WHERE Title GLOB '{title_char}*';").fetchall())
        if results < 1:
            return 0
        answer = QMessageBox.warning(None, 'Warning', f"{results} notes starting with \"{title_char}\"\nWILL BE DELETED before importing\nProceed with deletion? (NO to skip)", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if answer == "No":
          return 0
        sql = f"""
            PRAGMA foreign_keys = 'OFF';
            DELETE FROM Note WHERE Title GLOB '{title_char}*';"""
        results = self.cur.executescript(sql)
        sql = """
            DELETE FROM TagMap WHERE NoteId NOT IN (SELECT NoteId FROM Note);
            DELETE FROM Tag WHERE TagId NOT IN (SELECT TagId FROM TagMap);
            PRAGMA foreign_keys = 'ON';"""
        self.cur.executescript(sql)
        return results

    def import_items(self):
        count = 0
        self.cur.execute("BEGIN;")
        notes = self.import_file.read().replace("'", "''")
        for item in re.finditer('===(\{.*?\})===\n(.*?)\n(.*?)(?=\n===\{)', notes, re.S):
            try:
                count += 1
                attribs = self.process_header(item.group(1))
                title = item.group(2)
                note = item.group(3)
                if attribs['CAT'] == 'BIBLE':
                    self.import_bible(attribs, title, note)
                elif attribs['CAT'] == 'PUBLICATION':
                    self.import_publication(attribs, title, note)
                elif attribs['CAT'] == 'INDEPENDENT':
                    self.import_independent(attribs, title, note)
                else:
                    QMessageBox.critical(None, 'Error!', f'Wrong import file format:\nMalformed header:\n{attribs}', QMessageBox.Abort)
                    return 0
            except:
                QMessageBox.critical(None, 'Error!', f'Error on import!\nFaulting entry #{count}:\n{attribs}', QMessageBox.Abort)
                self.cur.execute("ROLLBACK;")
                return 0
        self.cur.execute("COMMIT;")
        return count

    def process_header(self, line):
        attribs = {}
        for (key, value) in re.findall('{(.*?)=(.*?)}', line):
            attribs[key] = value
        return attribs


    def process_tags(self, note_id, tags):
        # Remove tags related to note - it'll be re-tagged
        self.cur.execute(f"DELETE FROM TagMap WHERE NoteId = {note_id};")
        for tag in tags.split(','):
            # Strip off leading and trailing spaces
            tag = tag.strip()
            if not tag:
                continue
            # Add new tag if it doesn't already exist
            self.cur.execute(f"INSERT INTO Tag ( Type, Name ) SELECT 1, '{tag}' WHERE NOT EXISTS ( SELECT 1 FROM Tag WHERE Name = '{tag}' );")
            tag_id = self.cur.execute(f"SELECT TagId from Tag WHERE Name = '{tag}';").fetchone()[0]
            # Get next available position
            position = self.cur.execute(f"SELECT ifnull(max(Position), -1) FROM TagMap WHERE TagId = {tag_id};").fetchone()[0] + 1
            # Add new tag marker if needed
            self.cur.execute(f"INSERT Into TagMap (NoteId, TagId, Position) SELECT {note_id}, {tag_id}, {position} WHERE NOT EXISTS ( SELECT 1 FROM TagMap WHERE NoteId = {note_id} AND TagId = {tag_id});")

    def add_usermark(self, attribs, location_id):
        # Add new usermark for specified color if it doesn't already exist
        unique_id = uuid.uuid1()
        self.cur.execute(f"INSERT INTO UserMark ( ColorIndex, LocationId, StyleIndex, UserMarkGuid, Version ) SELECT {attribs['COLOR']}, {location_id}, 0, '{unique_id}', 1 WHERE NOT EXISTS ( SELECT 1 FROM UserMark WHERE ColorIndex = {attribs['COLOR']} AND LocationId = {location_id} AND Version = 1 );")
        result = self.cur.execute(f"SELECT UserMarkId from UserMark WHERE ColorIndex = {attribs['COLOR']} AND LocationId = {location_id} AND Version = 1;").fetchone()
        return result[0]


    def add_bible_location(self, attribs):
        # Add new location for the whole Bible if it doesn't already exist
        self.cur.execute(f"INSERT INTO Location ( IssueTagNumber, KeySymbol, MepsLanguage, Type ) SELECT 0, '{attribs['ED']}', {attribs['LANG']}, 1 WHERE NOT EXISTS ( SELECT 1 FROM Location WHERE KeySymbol = '{attribs['ED']}' AND MepsLanguage = {attribs['LANG']} AND IssueTagNumber = 0 AND Type = 1 );")
        result = self.cur.execute(f"SELECT LocationId from Location WHERE KeySymbol = '{attribs['ED']}' AND MepsLanguage = {attribs['LANG']} AND IssueTagNumber = 0 AND Type = 1;").fetchone()
        return result[0]

    def add_scripture_location(self, attribs):
        # Add new scripture location if it doesn't already exist
        self.cur.execute(f"INSERT INTO Location ( KeySymbol, MepsLanguage, BookNumber, ChapterNumber, Type ) SELECT '{attribs['ED']}', {attribs['LANG']}, {attribs['BK']}, {attribs['CH']}, 0 WHERE NOT EXISTS ( SELECT 1 FROM Location WHERE KeySymbol = '{attribs['ED']}' AND MepsLanguage = {attribs['LANG']} AND BookNumber = {attribs['BK']} AND ChapterNumber = {attribs['CH']} );")
        result = self.cur.execute(f"SELECT LocationId FROM Location WHERE KeySymbol = '{attribs['ED']}' AND MepsLanguage = {attribs['LANG']} AND BookNumber = {attribs['BK']} AND ChapterNumber = {attribs['CH']};").fetchone()
        return result[0]

    def import_bible(self, attribs, title, note):
        location_bible = self.add_bible_location(attribs)
        location_scripture = self.add_scripture_location(attribs)
        usermark_id = self.add_usermark(attribs, location_bible)
        result = self.cur.execute(f"SELECT Guid FROM Note WHERE LocationId = {location_scripture} AND Title = '{title}' AND BlockIdentifier = {attribs['VER']};").fetchone()
        if result:
            # Note with this title at that location already exists
            unique_id = result[0]
            # Update the note
            sql = f"UPDATE Note SET UserMarkId = {usermark_id}, Content = '{note}' WHERE Guid = '{unique_id}';"
        else:
            # Note is new...
            unique_id = uuid.uuid1()
            # Add new note
            sql = f"INSERT Into Note (Guid, UserMarkId, LocationId, Title, Content, BlockType, BlockIdentifier) VALUES ('{unique_id}', {usermark_id}, {location_scripture}, '{title}', '{note}', 2, {attribs['VER']});"
        self.cur.execute(sql)
        # Get id of note
        note_id = self.cur.execute(f"SELECT NoteId from Note WHERE Guid = '{unique_id}';").fetchone()[0]
        self.process_tags(note_id, attribs['TAGS'])


    def add_publication_location(self, attribs):
        # Add new location if it doesn't already exist
        # Note: added Type 0 to queries - different from jwl-admin!!!
        self.cur.execute(f"INSERT INTO Location ( IssueTagNumber, KeySymbol, MepsLanguage, DocumentId, Type ) SELECT {attribs['ISSUE']}, '{attribs['PUB']}', {attribs['LANG']}, {attribs['DOC']}, 0 WHERE NOT EXISTS ( SELECT 1 FROM Location WHERE KeySymbol = '{attribs['PUB']}' AND MepsLanguage = {attribs['LANG']} AND IssueTagNumber = {attribs['ISSUE']} AND DocumentId = {attribs['DOC']} AND Type = 0);")
        result = self.cur.execute(f"SELECT LocationId from Location WHERE KeySymbol = '{attribs['PUB']}' AND MepsLanguage = {attribs['LANG']} AND IssueTagNumber = {attribs['ISSUE']} AND DocumentId = {attribs['DOC']} AND Type = 0;").fetchone()
        return result[0]

    def import_publication(self, attribs, title, note):
        location_id = self.add_publication_location(attribs)
        usermark_id = self.add_usermark(attribs, location_id)
        result = self.cur.execute(f"SELECT Guid FROM Note WHERE LocationId = {location_id} AND Title = '{title}' AND BlockIdentifier = {attribs['BLOCK']};").fetchone()
        if result:
            # Note with this title at that location already exists
            unique_id = result[0]
            # Update the note
            sql = f"UPDATE Note SET UserMarkId = {usermark_id}, Content = '{note}' WHERE Guid = '{unique_id}';"
        else:
            # Note is new...
            unique_id = uuid.uuid1()
            # Add new note
            sql = f"INSERT INTO Note (Guid, UserMarkId, LocationId, Title, Content, BlockType, BlockIdentifier) VALUES ('{unique_id}', {usermark_id}, {location_id}, '{title}', '{note}', 1, {attribs['BLOCK']});"
        self.cur.execute(sql)
        # Get id of note
        note_id = self.cur.execute(f"SELECT NoteId from Note WHERE Guid = '{unique_id}';").fetchone()[0]
        self.process_tags(note_id, attribs['TAGS'])


    def import_independent(self, attribs, title, note):
        result = self.cur.execute(f"SELECT Guid FROM Note WHERE Title = '{title}' AND BlockType = 0;").fetchone()
        if result:
            # Note with this title already exists
            unique_id = result[0]
            # Update the note
            sql = f"UPDATE Note SET Content = '{note}' WHERE Guid = '{unique_id}';"
        else:
            # Note is new...
            unique_id = uuid.uuid1()
            # Add new note
            sql = f"INSERT Into Note (Guid, Title, Content, BlockType) VALUES ('{unique_id}', '{title}', '{note}', 0);"
        self.cur.execute(sql)
        # Get id of note
        note_id = self.cur.execute(f"SELECT NoteId from Note WHERE Guid = '{unique_id}';").fetchone()[0]
        self.process_tags(note_id, attribs['TAGS'])


class Reindex():
    def __init__(self, progress):
        self.progress = progress
        con = sqlite3.connect(f"{tmp_path}/userData.db")
        self.cur = con.cursor()
        self.cur.executescript("PRAGMA temp_store = 2; \
                                PRAGMA journal_mode = 'OFF'; \
                                PRAGMA foreign_keys = 'OFF'; \
                                BEGIN;")
        self.reindex_notes()
        self.reindex_highlights()
        self.reindex_tags()
        self.reindex_ranges()
        self.reindex_locations()
        self.cur.execute('PRAGMA foreign_keys = "ON";')
        con.commit()
        con.close()

    def make_table(self, table):
        sql = f"""
            CREATE TABLE CrossReference (Old INTEGER, New INTEGER PRIMARY KEY AUTOINCREMENT);
            INSERT INTO CrossReference (Old) SELECT {table}Id FROM {table};"""
        self.cur.executescript(sql)

    def update_table(self, table, field):
        app.processEvents()
        sql = f"""
            UPDATE {table} SET {field} = (SELECT New - 999999 FROM CrossReference WHERE CrossReference.Old = {table}.{field});
            UPDATE {table} SET {field} = {field} + 999999;"""
        self.cur.executescript(sql)
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
        self.update_table('PlaylistMedia', 'LocationId')
        self.drop_table()


if __name__ == "__main__":
    tmp_path = mkdtemp(prefix='JWLManager_')
    app = QApplication(sys.argv)

    font = QFont();
    font.setPixelSize(16);
    app.setFont(font);

    win = Window()
    win.show()
    sys.exit(app.exec_())
