#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File:           JWL Manager

Description:    Manage .jwlibrary backup archives

MIT License     Copyright (c) 2022 Eryk J.

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

# TODO
# Update README
# Implemet adding Bible favorite
# Add filter field


VERSION = 'v0.0.7'

import re
import sqlite3
import sys

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from csv import DictReader
from datetime import datetime
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from zipfile import ZipFile, ZIP_DEFLATED

# GUI definition
from ui_main_window import Ui_MainWindow
from ui_about import Ui_Dialog


# General style sheet
# FONT = '"Verdana", "Noto Sans Cond", "Arial", "Helvetica", "sans-serif"'
FONT = '"Arial", "Helvetica", "sans-serif"'
FONT_SIZE = 10 # 10 is ok on Windows; small on linux
FONT_STYLE = f"font-family: {FONT}; font: {FONT_SIZE}pt;"


# Maybe this should be in a resource CSV?
LANGUAGES = { 0:'English', 1:'Spanish', 2:'German', 3:'French', 4:'Italian',
              5:'Portuguese', 6:'Dutch', 7:'Japanese', 14:'Arabic', 53:'Czech',
              54:'Danish', 62:'Estonian', 67:'Finnish', 72:'Greek', 85:'Hindi', 
              89:'Hungarian', 184:'Norwegian', 198:'Polish', 200:'Punjabi',
              202:'Romanian', 207:'Russian', 230:'Swedish', 231:'Tagalog', 
              253:'Ukrainian', 279:'Chinese', 285:'Latvian' }


PROJECT_PATH = Path(__file__).resolve().parent
APP = Path(__file__).stem


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        # self.setStyleSheet(FONT_STYLE) # disabled with method 2
        self.statusBar.setFont(QFont(FONT_STYLE, italic=False))
        self.status_label = QLabel("No archive selected  ")
        self.status_label.setStyleSheet(f"{FONT_STYLE}; color:  grey;")
        self.status_label.setStyleSheet("color:  grey;")
        self.statusBar.addPermanentWidget(self.status_label, 0)
        self.treeWidget.sortByColumn(1, Qt.DescendingOrder)
        self.treeWidget.setExpandsOnDoubleClick(False)

        self.set_vars()
        self.read_csv()
        self.center()
        self.connect_signals()

    def set_vars(self):
        self.total.setText('')
        self.modified = False
        self.title_format = 'code'
        self.save_filename = ""
        self.current_archive = ""
        self.working_dir = Path.home()

    def read_csv(self):
        self.publications = {}
        with open(PROJECT_PATH / 'res/Publications.csv', newline='', 
                  encoding='utf-8-sig') as csvfile:
          reader = DictReader(csvfile, delimiter='\t')
          for row in reader:
              self.publications[row['Symbol']] = (row['Short'], row['Full'])

    def center(self):
        qr = self.frameGeometry()
        cp = QWidget.screen(self).availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def connect_signals(self):
        self.actionQuit.triggered.connect(self.close)
        self.actionHelp.triggered.connect(self.help)
        self.actionAbout.triggered.connect(self.about)
        self.actionOpen.triggered.connect(self.load_file)
        self.actionQuit.triggered.connect(self.clean_up)
        self.actionSave.triggered.connect(self.save_file)
        self.actionSave_As.triggered.connect(self.save_as_file)
        self.actionImport.triggered.connect(self.import_file)
        self.actionReindex.triggered.connect(self.re_index)
        self.actionExpand_All.triggered.connect(self.expand_all)
        self.actionCollapse_All.triggered.connect(self.collapse_all)
        self.actionSelect_All.triggered.connect(self.select_all)
        self.actionUnselect_All.triggered.connect(self.unselect_all)
        self.actionCode_Title.triggered.connect(self.code_view)
        self.actionShort_Title.triggered.connect(self.short_view)
        self.actionFull_Title.triggered.connect(self.full_view)
        self.combo_category.currentTextChanged.connect(self.switchboard)
        self.combo_grouping.currentTextChanged.connect(self.regroup)
        self.treeWidget.itemChanged.connect(self.tree_selection)
        self.treeWidget.doubleClicked.connect(self.double_clicked)
        self.button_export.clicked.connect(self.export)
        self.button_delete.clicked.connect(self.delete)


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


    def switchboard(self, selection):
        self.combo_grouping.setCurrentText('Publication')
        if selection == "Notes":
            self.disable_options()
        elif selection == "Highlights":
            self.disable_options([3])
        elif selection == "Bookmarks":
            self.disable_options([3,4])
        elif selection == "Annotations":
            self.disable_options([3,4])
        elif selection == "Favorites":
            self.disable_options([3,4])
        self.regroup()

    def disable_options(self, list=[]):
        for item in range(5):
            self.combo_grouping.model().item(item).setEnabled(True)
        for item in list:
            self.combo_grouping.model().item(item).setEnabled(False)

    def regroup(self):
        tree = BuildTree(self.treeWidget, self.publications,
                          self.combo_category.currentText(),
                          self.combo_grouping.currentText(), self.title_format)
        self.leaves = tree.leaves
        self.total.setText(f"**{tree.total:,}**")


    def help(self):
        QMessageBox.information(self, 'Help',
                'Please have a look\nat the README file.',
                QMessageBox.Ok)

    def about(self):
        dialog = AboutDialog(self)
        dialog.exec()


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
        self.status_label.setStyleSheet(f"font: {FONT_SIZE}pt; color:  black;")
        self.status_label.setText(f"{Path(fname[0]).stem}  ")
        with ZipFile(fname[0],"r") as zipped:
            zipped.extractall(tmp_path)
        self.actionImport.setEnabled(True)
        self.actionReindex.setEnabled(True)
        self.combo_grouping.setEnabled(True)
        self.combo_category.setEnabled(True)
        self.actionCollapse_All.setEnabled(True)
        self.actionExpand_All.setEnabled(True)
        self.actionSelect_All.setEnabled(True)
        self.actionUnselect_All.setEnabled(True)
        self.menuTitle_View.setEnabled(True)
        self.switchboard(self.combo_category.currentText())

    def trim_db(self):
        con = sqlite3.connect(f"{tmp_path}/userData.db")
        cur = con.cursor()
        sql = """
            PRAGMA temp_store = 2;
            PRAGMA journal_mode = 'OFF';
            PRAGMA foreign_keys = 'OFF';
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
            DELETE FROM BlockRange WHERE UserMarkId NOT IN
              (SELECT UserMarkId FROM UserMark);
            DELETE FROM TagMap WHERE NoteId IS NOT NULL AND NoteId
              NOT IN (SELECT NoteId FROM Note);
            DELETE FROM Tag WHERE TagId NOT IN (SELECT TagId FROM TagMap);
            PRAGMA foreign_keys = 'ON';
            VACUUM;"""
        cur.executescript(sql)
        con.commit()
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
        self.status_label.setStyleSheet(f"font: {FONT_SIZE}pt; font: italic;")

    def archive_saved(self):
        self.modified = False
        self.actionSave.setEnabled(False)
        self.status_label.setStyleSheet(f"font: {FONT_SIZE}pt; font: normal;")
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
                f"{self.selected_items} items will be EXPORTED.\nProceed?",
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
                    f"{self.working_dir}/EXPORT_{self.combo_category.currentText()}_{now}.txt",
                    "Text files (*.txt)")
        return fname


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


    def import_file(self):
        fname = QFileDialog.getOpenFileName(self, 'Import file', '.',
                                            "Import files (*.txt)")
        if fname[0] == "":
            return
        self.statusBar.showMessage(" Imported", 3500)
        self.archive_modified()


    def re_index(self):
        reply = QMessageBox.information(self, 'Re-index',
                'This may take a few seconds.\nProceed?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.No:
            return
        self.trim_db()
        self.pd = QProgressDialog("Please wait...", None, 0, 14, self)
        self.pd.setWindowModality(Qt.WindowModal)
        self.pd.setWindowTitle('Re-indexing')
        self.pd.setWindowFlag(Qt.FramelessWindowHint)
        self.pd.setModal(True)
        self.pd.setMinimumDuration(0)
        Reindex(self.pd)
        self.statusBar.showMessage(" Reindexed successfully", 3500)
        self.archive_modified()
        self.regroup()


class BuildTree():
    def __init__(self, tree, publications, category='Note', grouping='Publication', title='code'):
        self.tree = tree
        self.tree.clear()
        self.category = category
        self.grouping = grouping
        self.publications = publications
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
        self.tree.setColumnWidth(0, 400)
        self.tree.setColumnWidth(1, 40)
        self.tree.setSortingEnabled(True)


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
            publication = ("* INDEPENDENT *", None, None)
            language = ("* MULTI-LANGUAGE *", None)
            issue = (None, None)
            tag = (row[5] or "* UN-TAGGED *", None)
            color = ('Grey', None)
            self.build_index(publication, language, issue, tag, color, item)

        sql = "SELECT l.LocationId, l.KeySymbol, l.MepsLanguage, l.IssueTagNumber, NoteId, GROUP_CONCAT(t.Name), u.ColorIndex FROM Note n JOIN Location l USING (LocationId) LEFT JOIN TagMap tm USING (NoteId) LEFT JOIN Tag t USING (TagId) LEFT JOIN UserMark u USING (UserMarkId) GROUP BY n.NoteId;" # other
        for row in self.cur.execute(sql):
            item = row[4]
            publication = self.process_name(row[1] or 'MEDIA')
            language = self.process_language(row[2])
            issue = self.process_issue(row[3])
            tag = (row[5] or "* UN-TAGGED *", None)
            color = (('Grey', 'Yellow', 'Green', 'Blue', 'Purple', 'Red', 'Orange')[row[6] or 0], None)
            self.build_index(publication, language, issue, tag, color, item)


    def process_name(self, name):
        year = ''
        name, tip = self.check_name(name)
        if tip:
            return (name, tip, year)
        stripped = re.search('(.*?)(?!-)(\d+$)', name)
        if stripped:
            prefix = stripped.group(1)
            suffix = stripped.group(2)
            if prefix != 'kn':
                name = prefix
                year = '20' + suffix
        name, tip = self.check_name(name)
        if not tip:
            tip = '?'
        return (name, tip, year)

    def check_name(self, name):
        tip = ''
        if name in self.publications.keys():
            if self.title_format == 'code':
                tip = self.publications[name][0]
            elif self.title_format == 'short':
                tip = name
                name = self.publications[name][0]
            else:
                tip = name
                name = self.publications[name][1]
        return name, tip

    def process_language(self, lang):
        if lang in LANGUAGES.keys():
            name = LANGUAGES[lang]
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
        if publication[2] and not issue[0]:
            issue = (publication[2], '')
        if self.grouping == "Publication":
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
        sql = f"""SELECT l.MepsLanguage, l.KeySymbol, l.BookNumber,
                    l.ChapterNumber, n.BlockIdentifier, u.ColorIndex,
                    n.Title, n.Content, GROUP_CONCAT(t.Name) FROM Note n
                    JOIN Location l USING (LocationId) LEFT JOIN TagMap tm
                    USING (NoteId) LEFT JOIN Tag t USING (TagId)
                    LEFT JOIN UserMark u USING (UserMarkId)
                    WHERE n.BlockType = 2 AND NoteId IN {self.items}
                    GROUP BY n.NoteId;"""
        for row in self.cur.execute(sql):
            color = str(row[5] or 0)
            tags = row[8] or ''
            txt = "\n==={CAT=BIBLE}{LANG="+str(row[0])+"}{ED="+str(row[1])\
                +"}{BK="+str(row[2])+"}{CH="+str(row[3])+"}{VER="+str(row[4])\
                +"}{COLOR="+color+"}{TAGS="+tags+"}===\n"+row[6]+"\n"+row[7].rstrip()
            self.export_file.write(txt)

    def export_publications(self):
        sql = f"""SELECT l.MepsLanguage, l.KeySymbol, l.IssueTagNumber,
                    l.DocumentId, n.BlockIdentifier, u.ColorIndex,
                    n.Title, n.Content, GROUP_CONCAT(t.Name) FROM Note n
                    JOIN Location l USING (LocationId) LEFT JOIN TagMap tm
                    USING (NoteId) LEFT JOIN Tag t USING (TagId)
                    LEFT JOIN UserMark u USING (UserMarkId)
                    WHERE n.BlockType = 1 AND NoteId IN {self.items}
                    GROUP BY n.NoteId;"""
        for row in self.cur.execute(sql):
            color = str(row[5] or 0)
            tags = row[8] or ''
            txt = "\n==={CAT=PUBLICATION}{LANG="+str(row[0])+"}{PUB="\
                    +str(row[1])+"}{ISSUE="+str(row[2])+"}{DOC="+str(row[3])\
                    +"}{BLOCK="+str(row[4])+"}{COLOR="+color+"}{TAGS="+tags\
                    +"}===\n"+row[6]+"\n"+row[7].rstrip()
            self.export_file.write(txt)

    def export_independent(self):
        sql = f"""SELECT n.Title, n.Content, GROUP_CONCAT(t.Name)
                    FROM Note n JOIN TagMap tm USING (NoteId)
                    JOIN Tag t USING (TagId) WHERE n.BlockType = 0
                    AND NoteId IN {self.items} GROUP BY n.NoteId;"""
        for row in self.cur.execute(sql):
            tags = row[2] or ''
            txt = "\n==={CAT=INDEPENDENT}{TAGS="+tags\
                    +"}===\n"+row[0]+"\n"+row[1].rstrip()
            self.export_file.write(txt)


    def export_highlights(self):
        self.export_highlight_header()
        sql = f"""SELECT b.BlockType, b.Identifier, b.StartToken, b.EndToken,
                u.ColorIndex, u.StyleIndex, u.Version, l.BookNumber,
                l.ChapterNumber, l.DocumentId, l.Track, l.IssueTagNumber,
                l.KeySymbol, l.MepsLanguage, l.Type FROM BlockRange b
                JOIN UserMark u USING(UserMarkId) JOIN Location l
                USING (LocationId) WHERE UserMarkId IN {self.items};"""
        for row in self.cur.execute(sql):
            self.export_file.write(f"\n{row[0]}")
            for item in range(1,15):
                self.export_file.write(f",{row[item]}")

    def export_highlight_header(self):
        self.export_file.write('THIS FILE IS NOT MEANT TO BE MODIFIED MANUALLY\nYOU CAN USE IT TO BACKUP/TRANSFER/MERGE SELECTED HIGHLIGHTS\n\nFIELDS: BlockRange.BlockType, BlockRange.Identifier, BlockRange.StartToken,\n        BlockRange.EndToken, UserMark.ColorIndex, UserMark.StyleIndex,\n        UserMark.Version, Location.BookNumber, Location.ChapterNumber,\n        Location.DocumentId, Location.Track, Location.IssueTagNumber,\n        Location.KeySymbol, Location.MepsLanguage, Location.Type')
        self.export_file.write(f"\n\nExported from {self.current_archive}\nby {APP} ({VERSION}) on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}\n\n")
        self.export_file.write('*' * 79)


    def export_annotations(self):
        self.export_annotations_header()
        sql = f"""SELECT l.BookNumber, l.ChapterNumber, l.DocumentId, l.Track, l.IssueTagNumber, l.KeySymbol, l.MepsLanguage, l.Type, TextTag, Value FROM InputField JOIN Location l USING (LocationId) WHERE TextTag IN {self.items};"""
        for row in self.cur.execute(sql):
            self.export_file.write(f"\n{row[0]}")
            for item in range(1,10):
                self.export_file.write(f",{row[item]}")

    def export_annotations_header(self):
        self.export_file.write('THIS FILE IS NOT MEANT TO BE MODIFIED MANUALLY\nYOU CAN USE IT TO BACKUP/TRANSFER/MERGE SELECTED ANNOTATIONS\n\nFIELDS: Location.BookNumber, Location.ChapterNumber, Location.DocumentId,\n        Location.Track, Location.IssueTagNumber, Location.KeySymbol,\n        Location.MepsLanguage, Location.Type, InputField.TextTag,\n        InputField.Value')
        self.export_file.write(f"\n\nExported from {self.current_archive}\nby {APP} ({VERSION}) on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}\n\n")
        self.export_file.write('*' * 79)


class Reindex():
    def __init__(self, progress):
        self.progress = progress
        con = sqlite3.connect(f"{tmp_path}/userData.db")
        self.cur = con.cursor()
        self.cur.executescript("PRAGMA temp_store = 2; \
                                PRAGMA journal_mode = 'OFF'; \
                                PRAGMA foreign_keys = 'OFF';")
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


class AboutDialog(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(f"About {APP}")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.label_app.setText("**JWL Manager**")
        self.label_version.setText(VERSION)
        self.label_copyright.setText('*©2022 Eryk J.*')
        self.label_copyright.setVisible(False)


if __name__ == "__main__":
    tmp_path = mkdtemp(prefix='JWLManager_')
    # QApplication.setAttribute(Qt.AA_Use96Dpi) # method 1 with font setting above
    app = QApplication(sys.argv)

    font = QFont(); # method 2 with font setting disabled
    font.setPixelSize(16);
    app.setFont(font);

    win = Window()
    win.show()
    sys.exit(app.exec_())
