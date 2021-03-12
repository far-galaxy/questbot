# -*- coding: utf-8 -*-

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import json
import math
import os
from sys import argv
from glob import glob


def check_duplicate(name, lst):
    num = 0
    for obj in lst:
        if obj[:len(name)] == name:
            num = int(obj[len(name):]) + 1   
    return name + str(num)

class Node():
    def __init__(self, position, tag, answer, out_nodes):
        self.position = position
        self.tag = tag
        self.answer = answer
        self.out_nodes = out_nodes
        self.width = 150
        self.header = 25
        

        self.moveTo(position)

    # Move node to position
    def moveTo(self, position):
        self.height = 25 * (len(self.out_nodes) + 2)
        self.position = position
        self.head = QRect(position, QSize(self.width - self.header, self.header))
        
        self.answer_rect = QRect(position.x(), position.y() + self.header, self.width, self.header)

        circleD = self.header - 10
        
        self.opt = {"rect": QRect(position.x() + self.width - self.header, position.y(), self.header, self.header), "selected": False}

        self.input_socket = {"rect": QRect(position.x() - circleD / 2, position.y() + 5, circleD, circleD), "selected": False}
        self.output_sockets = []

        for out in self.out_nodes:
            strY = position.y() + (len(self.output_sockets) + 3) * self.header
            circle = QRect(position.x() + self.width - circleD / 2, strY + 5, circleD, circleD)

            self.output_sockets.append({"rect": circle,
                                        "pos": QPoint(position.x() + self.width + circleD / 2, strY + self.header // 2),
                                        "goto": out,
                                        "selected": False,
                                        "connected": False})
    def moveDP(self, dp):
        self.position += dp
        self.update()
            
    def update(self):
        self.moveTo(self.position)


class Widget(QWidget):
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)

        # -----------------Title---------------------------
        self.title = 'QuestBot Constructor'
        self.setWindowTitle(self.title)
        # self.setWindowIcon(QIcon('icon.png'))
        self.resize(800, 600)
        #self.setFont(QFont("Calibri", 16, QFont.Normal))

        self.w = self.frameGeometry().width()
        self.h = self.frameGeometry().height()
        
        self.load_options()
        self.load_lp(self.lang)

        menubar = QMenuBar()

        #  File menu
        file_menu = menubar.addMenu('&' + self.lp["file"])
        
        new_file_menu = QAction(self.lp["new"], self)
        new_file_menu.setShortcut('Ctrl+N')
        new_file_menu.triggered.connect(self.new_file)        

        open_file_menu = QAction(self.lp["open"], self)
        open_file_menu.setShortcut('Ctrl+O')
        open_file_menu.triggered.connect(self.open_file)

        self.save_file_menu = QAction(self.lp["save"], self)
        self.save_file_menu.setShortcut('Ctrl+S')
        self.save_file_menu.triggered.connect(self.update_file)
        self.save_file_menu.setEnabled(False)
        
        save_as_menu = QAction(self.lp["save_as"], self)
        save_as_menu.triggered.connect(self.save_file)        
        
        self.recent_menu = QMenu(self.lp['recent'], self)
            #for i in recent_files:        
        
        self.exitAction = QAction('&'+self.lp['quit'], self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(self.quit)           

        file_menu.addAction(new_file_menu)
        file_menu.addAction(open_file_menu)
        file_menu.addAction(self.save_file_menu)
        file_menu.addAction(save_as_menu)
        file_menu.addMenu(self.recent_menu)
        file_menu.addSeparator()
        file_menu.addAction(self.exitAction)
        
        opt_menu = menubar.addAction('&'+self.lp['options'])
        opt_menu.triggered.connect(self.options_window) 
        opt_menu.setShortcut('F2')        

        #   New Node action
        new_node_menu = menubar.addAction('&New Node')
        new_node_menu.triggered.connect(self.new_node)

        #   Menu
        grid = QGridLayout()
        grid.setMenuBar(menubar)
        self.setLayout(grid)
        
        try:
            self.load_quest(argv[1])
            self.file = argv[1]
            self.setWindowTitle(argv[1] + ': ' + self.title)
        except IndexError:
            self.new_file(True)

        self.setMouseTracking(True)
        
        self.camera = QPoint(0, 0)
        
        #   Triggers
        self.nodeSelected = None
        self.isDragging = False
        self.socketSelected = None
        self.optSelected = None
        self.ghostLine = {"socket": None, "line": None}
        self.isCameraMoving = False
        self.mouse = QPoint(0,0)

    def mouseMoveEvent(self, event):
        pos = event.pos() - self.camera
        #self.mouse = event.pos()
        
        if self.isCameraMoving:
            self.camera = event.pos() - self.mouse
            self.setCursor(Qt.ClosedHandCursor)

        if not self.isDragging:
            isInHead = False
            isInOpt = False
            isInOutputSocket = False
            
            #    Detecting mouse over objects
            for number, node in enumerate(self.nodes):
                
                #    Header
                if node.head.contains(pos):
                    isInHead |= True
                    self.nodeSelected = number
                    
                #   Node options
                if node.opt["rect"].contains(pos):
                    isInOpt |= True
                    self.optSelected = number
                    
                #    Output socket
                for socket_number, out in enumerate(node.output_sockets):
                    if out["rect"].contains(pos):
                        isInOutputSocket |= True
                        self.socketSelected = [number, socket_number]
                        self.nodes[number].output_sockets[socket_number]["selected"] = True
                        self.update()
                    else:
                        self.nodes[number].output_sockets[socket_number]["selected"] = False
                        self.update()
            
            #TODO: fix cursor bug    
            if isInHead:
                self.setCursor(Qt.SizeAllCursor)
            elif isInOutputSocket or isInOpt:
                self.setCursor(Qt.PointingHandCursor)
            else:
                if not self.isCameraMoving:
                    self.setCursor(Qt.ArrowCursor)
                self.nodeSelected = None
                self.socketSelected = None
                self.optSelected = None

        #   Dragging objects
        elif not self.isCameraMoving:
            #    Node
            if self.nodeSelected != None:
                self.nodes[self.nodeSelected].moveTo(pos - self.dPos + self.camera)
                self.update()
                
            #    Output socket     
            elif self.socketSelected != None:
                socket = self.nodes[self.socketSelected[0]].output_sockets[self.socketSelected[1]]
                self.nodes[self.socketSelected[0]].out_nodes[socket["goto"]] = ""
                self.ghostLine["line"] = self.curve(socket["pos"] + self.camera, pos + self.camera)
                self.update()

                connected = False
                for node in self.nodes:
                    ind = [n.tag for n in self.nodes].index(node.tag)
                    if node.input_socket["rect"].contains(pos) and self.nodes[ind].tag != "start":
                        self.nodes[ind].input_socket["selected"] = True
                        self.ghostLine["socket"] = node.tag
                        connected = True
                    else:
                        self.nodes[ind].input_socket["selected"] = False

                    if not connected:
                        self.ghostLine["socket"] = None

    def mousePressEvent(self, event):
        if self.file != "" and self.check_changes():
            self.setWindowTitle(self.file + '*: ' + self.title) 
            self.save_file_menu.setEnabled(True)
            
        if event.button() == Qt.LeftButton:
            #   Node options
            if  self.optSelected != None:
                self.node_edit_window(self.nodes[self.optSelected])
                self.nodeSelected = None
                self.socketSelected = None
                self.optSelected = None                
            
            #   Start dragging
            if not self.isDragging:
                #   Node
                if self.nodeSelected != None:
                    self.isDragging = True
                    self.dPos = event.pos() - self.nodes[self.nodeSelected].position
                    
                
                #   Output socket
                elif self.socketSelected != None:
                    self.isDragging = True
            
            #   Stop dragging        
            elif self.isDragging:
                
                self.isDragging = False
                
                #  Connect nodes
                if self.socketSelected != None:
                    socket = self.nodes[self.socketSelected[0]].output_sockets[self.socketSelected[1]]
                    if self.ghostLine["socket"] != None:
                        self.nodes[self.socketSelected[0]].out_nodes[socket["goto"]] = self.ghostLine["socket"]
                        self.nodes[[n.tag for n in self.nodes].index(self.ghostLine["socket"])].input_socket["selected"] = False
                    self.ghostLine["line"] = None
                    self.ghostLine["socket"] = None
                    self.update()
                    
        elif event.button() == Qt.RightButton:
            if not self.isCameraMoving and not self.isDragging:
                self.mouse = event.pos() - self.camera
                self.isCameraMoving = True            
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.isCameraMoving = False
            
                    

    def keyPressEvent(self, e):

        if e.key() == Qt.Key_E:
            self.load_quest('quest.json')
            self.update()

        if e.key() == Qt.Key_S:
            self.save_quest()
            self.update()
            
        if e.key() == Qt.Key_Home:
            self.camera = QPoint(0, 0)
            self.update()
      

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(QFont("Calibri", 14, QFont.Bold))
        
        # Grid
        painter.setPen(QPen(Qt.darkGray, 1, Qt.SolidLine))
        for x in range(self.size().width() // 100):
            dx = x * 100 + (self.camera.x()%100)
            painter.drawLine(dx, 0, dx, self.size().height())
            
        for y in range(self.size().height() // 100):
            dy = y * 100 + (self.camera.y()%100)
            painter.drawLine(0, dy, self.size().width(), dy)
        
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))

        for node in self.nodes:
            self.nodes[self.nodes.index(node)].moveDP(self.camera)
            head = QPoint(node.position)

            # Header
            painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
            painter.drawRect(node.head)

            # Header text
            header_text_rect = QRect(head.x() + 15, head.y(), node.width, node.header)
            painter.setFont(QFont("Calibri", 14, QFont.Bold))
            header_text = self.short_text(node.tag, painter.font(), node.width - node.header)
            painter.drawText(header_text_rect, Qt.AlignLeft, header_text)

            # Header cirle (Node Input)
            circleD = node.header - 10
            if node.tag != "start":
                color = Qt.green if node.input_socket["selected"] and not self.isDragging else Qt.cyan
                painter.setBrush(QBrush(color, Qt.SolidPattern))                
                painter.drawEllipse(node.input_socket["rect"])
            
            # Node options
            color = Qt.green if node.opt["selected"] else Qt.cyan
            painter.setBrush(QBrush(color, Qt.SolidPattern))
            painter.drawRect(node.opt["rect"])

            # Main part
            painter.setBrush(QBrush(QColor(200, 200, 200, 255), Qt.SolidPattern))
            painter.drawRect(head.x(), head.y() + node.header, node.width, node.height)
            
            # Bot answer
            painter.setFont(QFont("Calibri", 14, QFont.Normal))
            answer_text = self.short_text("  " + node.answer, painter.font(), node.width)
            painter.drawText(node.answer_rect, Qt.AlignLeft, answer_text)

            # Node outputs
            for node_num, nodeOut in enumerate(node.out_nodes):

                # Output text
                strY = head.y() + (node.header * 3) + node_num * 25
                out_rect = QRect(head.x(), strY, node.width - circleD, 25)
                painter.setFont(QFont("Calibri", 14, QFont.Normal))
                out_text = self.short_text("  " + nodeOut, painter.font(), node.width)
                painter.drawText(out_rect, Qt.AlignRight, out_text)

                # Start position
                start = QPoint(head.x() + node.width, strY + circleD / 2 + 5)

                circleColor = Qt.red

                # Draw line if output is definited.
                if node.out_nodes[nodeOut] != "":
                    # End position
                    endInd = [n.tag for n in self.nodes].index(node.out_nodes[nodeOut])
                    end = QPoint(self.nodes[endInd].position) + self.camera
                    end += QPoint(-circleD / 2, circleD / 2 + 5)

                    painter.save()
                    painter.setPen(QPen(Qt.black, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                    painter.setBrush(QBrush(Qt.NoBrush))

                    path = self.curve(start, end)

                    painter.drawPath(path)

                    if self.ghostLine["line"] != None:
                        painter.drawPath(self.ghostLine["line"])

                    painter.restore()
                    painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))

                    circleColor = Qt.cyan

                # Draw cirlce of output socket.\
                # TODO: fix coloring while selecting
                socket = node.output_sockets[node_num]
                circleColor = Qt.green if socket["selected"] else circleColor
                painter.setBrush(QBrush(circleColor, Qt.SolidPattern))
                painter.drawEllipse(socket["rect"])

                
            self.nodes[self.nodes.index(node)].moveDP(-self.camera)
    
    def short_text(self, text, font, lenght):
        width = QFontMetrics(font).horizontalAdvance(text) 
        dl = math.ceil(width / len(text))
        out = text[:(lenght // dl - 2)] + ("..." if width > lenght else "")
        return out
    

    def curve(self, start, end):
        delta = end - start

        # Some magic to making curve.
        if delta.x() > 0:
            if delta.x() > abs(delta.y()):
                if delta.y() > 0:
                    arc_start = start.x() + (delta.x() - delta.y() * 2) // 2
                    first_arc = QRectF(arc_start, start.y(), delta.y(), delta.y())
                    second_arc = QRectF(arc_start + delta.y(), start.y(), delta.y(), delta.y())

                    path = QPainterPath()
                    path.moveTo(start)
                    path.lineTo(arc_start + delta.y() // 2, start.y())
                    path.arcTo(first_arc, 90, -90)
                    path.arcTo(second_arc, 180, 90)
                    path.lineTo(end)

                else:
                    arc_start = start.x() + (delta.x() + delta.y() * 2) // 2
                    first_arc = QRectF(arc_start, end.y(), -delta.y(), -delta.y())
                    second_arc = QRectF(arc_start - delta.y(), end.y(), -delta.y(), -delta.y())

                    path = QPainterPath()
                    path.moveTo(start)
                    path.lineTo(arc_start - delta.y() // 2, start.y())
                    path.arcTo(first_arc, -90, 90)
                    path.arcTo(second_arc, 180, -90)
                    path.lineTo(end)

            else:
                if delta.y() > 0:
                    first_arc = QRectF(start.x() - delta.x() / 2, start.y(), delta.x(), delta.x())
                    second_arc = QRectF(end.x() - delta.x() / 2, end.y() - delta.x(), delta.x(), delta.x())

                    path = QPainterPath()
                    path.moveTo(start)
                    path.arcTo(first_arc, 90, -90)
                    path.lineTo(start.x() + delta.x() / 2, end.y() - delta.x() / 2)
                    path.arcTo(second_arc, 180, 90)
                    path.lineTo(end)

                else:
                    first_arc = QRectF(start.x() - delta.x() // 2, start.y() - delta.x(), delta.x(), delta.x())
                    second_arc = QRectF(end.x() - delta.x() // 2, end.y(), delta.x(), delta.x())

                    path = QPainterPath()
                    path.moveTo(start)
                    path.arcTo(first_arc, -90, 90)
                    path.lineTo(start.x() + delta.x() / 2, end.y() + delta.x() / 2)
                    path.arcTo(second_arc, 180, -90)
                    path.lineTo(end)

        else:
            half_dy = delta.y() / 2
            flip = 1 if delta.y() > 0 else -1

            first_arc = QRectF(start.x() - half_dy / 2, start.y(), half_dy, half_dy)
            second_arc = QRectF(end.x() - half_dy / 2, end.y() - half_dy, half_dy, half_dy)

            path = QPainterPath()
            path.moveTo(start)
            path.arcTo(first_arc, 90, -180 * flip)
            path.lineTo(end.x(), start.y() + delta.y() / 2)
            path.arcTo(second_arc, 90, 180 * flip)

        return path
    
    def node_edit_window(self, node):
        node_window = Node_Editor(self, node)
        node_window.show()    

    def new_node(self):
        name = check_duplicate("node", [n.tag for n in self.nodes])
        self.nodes.append(Node(self.camera + self.mouse, name, "", {}))
        self.update()
        
        self.nodeSelected = len(self.nodes) - 1
        self.dPos = self.camera
        self.isDragging = True
        self.setCursor(Qt.SizeAllCursor)
        
    def new_file(self, startup = False):
        if startup or self.unsaved_message():  
            self.nodes = []  
            self.file = ""
            self.unidentified = ""
            self.quest = {"unidentified" : ""}
            self.save_file_menu.setEnabled(True)
            self.setWindowTitle(self.title)
            self.update()

    def open_file(self):
        if self.unsaved_message():    
            file = QFileDialog.getOpenFileName(self, self.lp["open_dialog"], os.path.abspath(""), "Quest (*.qbc)")
            self.load_quest(file[0])            

    def save_file(self):
        file = QFileDialog.getSaveFileName(self, self.lp["save_dialog"], os.path.abspath("quest.qbc"), "Quest (*.qbc)")
        self.save_quest(file[0])
        
    def update_file(self):
        if self.file != "":
            self.save_quest(self.file)
            self.setWindowTitle(self.file + ': ' + self.title) 
            self.save_file_menu.setEnabled(False)
        else:
            self.save_file()
        
    def load_lp(self, file):
        pth = os.path.abspath('data/' + file)
        f = open(pth, 'r', encoding="utf-8")
        self.lp = json.loads(f.read())
        f.close()

    def load_quest(self, file):
        if file != "":
            f = open(file, 'r', encoding="utf-8")
            self.quest = json.loads(f.read())
            f.close()
            
            self.file = file
            self.setWindowTitle(file + ': QuestBot Constructor')            

            self.nodes = []
            
            self.unidentified = self.quest["unidentified"]

            # Make nodes objects
            for node in self.quest:
                if node != "unidentified":
                    position = self.quest[node]["position"]
                    self.nodes.append(Node(QPoint(position[0], position[1]), node, self.quest[node]["bot_answer"], self.quest[node]["goto"]))

    def quest2json(self):
        quest = {}
        for node in self.nodes:
            quest[node.tag] = {"position": [node.position.x(), node.position.y()], "bot_answer": node.answer,  # self.quest[node.tag]["bot_answer"],
                               "goto": {}}
            for i in node.out_nodes:
                quest[node.tag]["goto"][i] = node.out_nodes[i]  
        quest["unidentified"] = self.unidentified
        return quest
     
    def check_changes(self):
        new = self.quest2json()
        return self.quest != new
        
    def unsaved_message(self):
        if self.check_changes():
            reply = QMessageBox.question(self, self.lp["warning"], 
                                         self.lp["unsaved"], 
                                         QMessageBox.Yes |
                                         QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:  
                if self.file == "":
                    self.save_file()
                else:
                    self.update_file()
                return False
                    
            elif reply == QMessageBox.No:        
                return True
                
        else:     
            return True
        
    def save_quest(self, file):
        if file != "":
            f = open(file, 'w', encoding="utf-8")
            quest = self.quest2json()
            f.write(str(quest).replace("'", '"'))
            
    def load_options(self):
        try:
            f = open("data/options.json", 'r', encoding="utf-8")
        except FileNotFoundError:
            f = open("data/options.json", 'w', encoding="utf-8")
            f.write('{"lang" : "english.lp"}')
            f.close()  
            f = open("data/options.json", 'r', encoding="utf-8")
            
        self.lang = json.loads(f.read())["lang"]
        f.close() 
        
    def set_option(self, param, value):
        f = open("data/options.json", 'r', encoding="utf-8")
        opts = json.loads(f.read())
        f.close()   
        opts[param] = value
        f = open("data/options.json", 'w', encoding="utf-8")
        f.write(str(opts).replace("'", '"'))
        f.close()          
            
    def options_window(self):
        opt_window = Options(self)
        opt_window.show()    
            
    def quit(self):
        if self.unsaved_message():
            qApp.quit()
            
    def closeEvent(self, event):
        if self.unsaved_message():
            event.accept()
        else:
            event.ignore()            

            
class Node_Editor(QDialog):
    def __init__(self, parent, node):
        super(Node_Editor, self).__init__(parent)
        self.parent = parent
        self.node = node
        
        self.string_height = 45
        self.out_offset = 4
        
        #-----------------Title---------------------------
        self.setWindowTitle("Node Edit")
        #self.setWindowIcon(QIcon('icon.png'))
        self.setFixedSize(300, (len(node.out_nodes) + self.out_offset) * self.string_height)
        
        self.setFont(QFont("Calibri", 14, QFont.Normal))  
        
        self.tag_name_ = QLabel("Tag:", self)
        self.tag_name = QLineEdit(self)
        self.tag_name.setText(self.node.tag)
        self.tag_name.textChanged[str].connect(self.change_tag)
        
        self.answer_ = QLabel("Answer:", self)
        self.answer = QLineEdit(self)
        self.answer.setText(self.node.answer)
        self.answer.textChanged[str].connect(self.change_answer)   
                
        self.lay = QVBoxLayout(self)
        
        hlay1 = QHBoxLayout()
        hlay1.addWidget(self.tag_name_)
        hlay1.addStretch()
        hlay1.addWidget(self.tag_name) 
        
        hlay2 = QHBoxLayout()
        hlay2.addWidget(self.answer_)
        hlay2.addStretch()
        hlay2.addWidget(self.answer)  
        
        self.del_node = QPushButton("Delete Node", self)
        self.del_node.clicked.connect(self.delete_node)
        
        if self.node.tag == "start":
            self.tag_name.setEnabled(False)
            self.del_node.setEnabled(False)
        
        self.lay.addWidget(self.del_node)
        self.lay.addLayout(hlay1) 
        self.lay.addLayout(hlay2) 
        self.lay.addWidget(QLabel("User ask:", self))
        
        self.out_line = []
        number = 0
        for out in self.node.out_nodes:
            self.add_out(number, out)           
            number += 1
            
        self.new_out = QPushButton("Add ask", self)
        self.new_out.clicked.connect(self.create_out)
        
        hlay3 = QHBoxLayout()
        hlay3.addStretch(2)  
        hlay3.addWidget(self.new_out)      
        self.lay.addLayout(hlay3) 
    
    def add_out(self, number, out): 
        self.out_line.append({#"name" : QLabel("User ask: ", self),
                              "edit" : QLineEdit(self),
                              "last_value" : out,
                              "delete" : QPushButton("-", self)})
        
        self.out_line[number]["edit"].setText(out)
        self.out_line[number]["edit"].textChanged[str].connect(self.change_out) 
        
        self.out_line[number]["delete"].clicked.connect(self.delete_out)
            
        hlay = QHBoxLayout()
        #hlay.addWidget(self.out_line[number]["name"])
        #hlay.addStretch()
        hlay.addWidget(self.out_line[number]["edit"])  
        hlay.addWidget(self.out_line[number]["delete"])  
        self.lay.addLayout(hlay)         
        
    def change_tag(self, text):
        if text != "" and not text in [n.tag for n in self.parent.nodes]:
            ind = [n.tag for n in self.parent.nodes].index(self.node.tag)
            old_tag = self.parent.nodes[ind].tag
            
            for number, node in enumerate(self.parent.nodes):
                for out in node.out_nodes:
                    if self.parent.nodes[number].out_nodes[out] == old_tag:
                        self.parent.nodes[number].out_nodes[out] = text
                        
            self.parent.nodes[ind].tag = text
            
    def change_answer(self, text):
        if text != "":
            ind = [n.answer for n in self.parent.nodes].index(self.node.answer)
            self.parent.nodes[ind].answer = text   
            
    def change_out(self, text):
        if not text in self.node.out_nodes:
            sender = self.sender()        
            ind = [i["edit"] for i in self.out_line].index(sender)
            input_node = self.node.out_nodes[self.out_line[ind]["last_value"]]
            temp = {}
            for i in self.node.out_nodes:
                if i == self.out_line[ind]["last_value"]:
                    temp[text] = input_node
                else:
                    temp[i] = self.node.out_nodes[i]
            self.node.out_nodes = temp
            self.out_line[ind]["last_value"] = text
                        

    def delete_out(self):
        sender = self.sender()        
        ind = [i["delete"] for i in self.out_line].index(sender)
        self.node.out_nodes.pop(self.out_line[ind]["last_value"])
        self.node.update()
        
        for i in self.out_line[ind]:
            if i != "last_value":
                self.out_line[ind][i].deleteLater()
        self.out_line.pop(ind)
        self.lay.removeItem(self.lay.takeAt(ind + self.out_offset))
        
        self.setFixedSize(300, (len(self.node.out_nodes) + self.out_offset) * self.string_height)
        
        self.update()
        
    def create_out(self):
        sender = self.sender()        
        sender.deleteLater()
        self.lay.removeItem(self.lay.takeAt(len(self.out_line) + self.out_offset))
        
        name = check_duplicate("ask", self.node.out_nodes)
                
        self.node.out_nodes[name] = ""
        self.node.update()
        self.add_out(len(self.out_line), name)
        
        self.new_out = QPushButton("Add ask", self)
        self.new_out.clicked.connect(self.create_out)
        
        hlay3 = QHBoxLayout()
        hlay3.addStretch(2)  
        hlay3.addWidget(self.new_out)      
        self.lay.addLayout(hlay3)   
        
        self.setFixedSize(300, (len(self.node.out_nodes) + self.out_offset) * self.string_height)
        
    def delete_node(self):        
        reply = QMessageBox.question(self, 'Warning', 
                                     "Are you sure you want to delete the node? ", 
                                     QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:        
            for number, node in enumerate(self.parent.nodes):
                for out in node.out_nodes:
                    if self.parent.nodes[number].out_nodes[out] == self.node.tag:
                        self.parent.nodes[number].out_nodes[out] = ""
                
            self.parent.nodes.pop(self.parent.nodes.index(self.node))
            self.parent.update()
            self.close()
            
class Options(QDialog):
    def __init__(self, parent=None):
        super(Options, self).__init__(parent)
        self.parent = parent
        self.lp = parent.lp
        
        langs = glob(os.path.abspath("data/"+"*.lp"))
        self.langs = langs
        
        #-----------------Title---------------------------
        self.setWindowTitle(self.lp['options'])
        #self.setWindowIcon(QIcon('icon.png'))
        self.setFixedSize(400, 300)
        
        #-----------------Language-----------------------
        self.lang_ = QLabel(self.lp['language'] + ":", self)
        self.lang_box = QComboBox(self)
        for i, file in enumerate(langs):
            f = open(file, 'r', encoding="utf-8")
            lp = json.loads(f.read())
            self.lang_box.addItem(QIcon('data/' + lp["icon"]), lp["name"], i)
            if parent.lang == file.split("\\")[-1]:
                self.lang_box.setCurrentIndex(i)
        self.lang_box.activated.connect(self.set_lang)
        
        lay = QVBoxLayout(self)
        
        hlay1 = QHBoxLayout()
        hlay1.addWidget(self.lang_)
        hlay1.addWidget(self.lang_box)      
        
        lay.addLayout(hlay1)

    def set_lang(self, number):
        for i, file in enumerate(self.langs):
            if i == number:
                self.parent.set_option("lang", file.split("\\")[-1])
                f = open(file, 'r', encoding="utf-8")
                lp = json.loads(f.read())                
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText(lp['lang_changed'])
                msg.setWindowTitle(lp['warning'])    
                msg.exec()                

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())
