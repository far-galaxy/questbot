# -*- coding: utf-8 -*-

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import json
import math
import os

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
        self.setWindowTitle('QuestBot Constructor')
        # self.setWindowIcon(QIcon('icon.png'))
        self.resize(800, 600)
        #self.setFont(QFont("Calibri", 16, QFont.Normal))

        self.w = self.frameGeometry().width()
        self.h = self.frameGeometry().height()

        menubar = QMenuBar()

        #  File menu
        file_menu = menubar.addMenu('&File')

        open_file_menu = QAction('Open', self)
        open_file_menu.setShortcut('Ctrl+O')
        open_file_menu.triggered.connect(self.open_file)

        save_file_menu = QAction('Save', self)
        save_file_menu.setShortcut('Ctrl+S')
        save_file_menu.triggered.connect(self.save_file)

        file_menu.addAction(open_file_menu)
        file_menu.addAction(save_file_menu)

        #   New Node action
        new_node_menu = menubar.addAction('&New Node')
        new_node_menu.triggered.connect(self.new_node)

        #   Menu
        grid = QGridLayout()
        grid.setMenuBar(menubar)
        self.setLayout(grid)

        self.load_quest('quest.json')

        self.setMouseTracking(True)
        
        self.camera = QPoint(20, 0)
        
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

        if not self.isDragging:
            isInHead = False
            isInOpt = False
            isInOutputSocket = False
            number = 0
            
            #    Detecting mouse over objects
            for node in self.nodes:
                
                #    Header
                if node.head.contains(pos):
                    isInHead |= True
                    self.nodeSelected = number
                    
                #   Node options
                if node.opt["rect"].contains(pos):
                    isInOpt |= True
                    self.optSelected = number
                    
                #    Output socket
                socket_number = 0
                for out in node.output_sockets:
                    if out["rect"].contains(pos):
                        isInOutputSocket |= True
                        self.socketSelected = [number, socket_number]
                        self.nodes[number].output_sockets[socket_number]["selected"] = True
                        self.update()
                    else:
                        self.nodes[number].output_sockets[socket_number]["selected"] = False
                        self.update()
                    socket_number += 1
                number += 1
                
            if isInHead:
                self.setCursor(Qt.SizeAllCursor)
            elif isInOutputSocket or isInOpt:
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
                self.nodeSelected = None
                self.socketSelected = None
                self.optSelected = None

        #   Dragging objects
        else:
            #    Node
            if self.nodeSelected != None:
                self.nodes[self.nodeSelected].moveTo(pos - self.dPos)
                self.update()
                
            #    Output socket     
            elif self.socketSelected != None:
                socket = self.nodes[self.socketSelected[0]].output_sockets[self.socketSelected[1]]
                self.nodes[self.socketSelected[0]].out_nodes[socket["goto"]] = ""
                self.ghostLine["line"] = self.curve(socket["pos"], pos)
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
                    
        elif event.button() == Qt.MiddleButton:
            if not self.isCameraMoving:
                self.mouse = event.pos() - self.camera
                print(self.mouse.x(), self.mouse.y())
                self.isCameraMoving = True            
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.isCameraMoving = False
            
                    

    def keyPressEvent(self, e):

        if e.key() == Qt.Key_E:
            self.load_quest('quest.json')
            self.update()

        if e.key() == Qt.Key_S:
            self.save_quest()
            self.update()
            
        if e.key() == Qt.Key_Q and self.nodeSelected != None:
            self.node_edit_window(self.nodes[self.nodeSelected])
      

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(QFont("Calibri", 14, QFont.Bold))
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
                color = Qt.green if node.input_socket["selected"] and self.isDragging else Qt.cyan
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
            yNodeOut = 0
            for nodeOut in node.out_nodes:

                # Output text
                strY = head.y() + (node.header * 3) + yNodeOut * 25
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

                # Draw cirlce of output socket.
                socket = node.output_sockets[yNodeOut]
                circleColor = Qt.green if socket["selected"] else circleColor
                painter.setBrush(QBrush(circleColor, Qt.SolidPattern))
                painter.drawEllipse(socket["rect"])

                yNodeOut += 1
                
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
        self.nodes.append(Node(QPoint(100, 100), name, "", {}))
        self.update()
        
        self.nodeSelected = len(self.nodes) - 1
        self.dPos = QPoint(0, 0)
        self.isDragging = True
        self.setCursor(Qt.SizeAllCursor)

    def open_file(self):
        file = QFileDialog.getOpenFileName(self, 'Open Quest File', os.path.abspath(""), "Quest (*.json)")
        self.load_quest(file[0])

    def save_file(self):
        file = QFileDialog.getSaveFileName(self, 'Save Quest File', os.path.abspath("quest.json"), "Quest (*.json)")
        self.save_quest(file[0])

    def load_quest(self, file):
        if file != "":
            f = open(file, 'r', encoding="utf-8")
            self.quest = json.loads(f.read())
            f.close()

            self.nodes = []

            # Make nodes objects
            for node in self.quest:
                if node != "unidentified" and node != "help":
                    position = self.quest[node]["position"]
                    self.nodes.append(Node(QPoint(position[0], position[1]), node, self.quest[node]["bot_answer"], self.quest[node]["goto"]))

    def save_quest(self, file):
        if file != "":
            f = open(file, 'w', encoding="utf-8")
            quest = {}
            for node in self.nodes:
                quest[node.tag] = {"position": [node.position.x(), node.position.y()], "bot_answer": node.answer,  # self.quest[node.tag]["bot_answer"],
                                   "goto": {}}
                for i in node.out_nodes:
                    quest[node.tag]["goto"][i] = node.out_nodes[i]
            print(quest)
            f.write(str(quest).replace("'", '"'))

            
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
            
            number = 0
            for node in self.parent.nodes:
                for out in node.out_nodes:
                    if self.parent.nodes[number].out_nodes[out] == old_tag:
                        self.parent.nodes[number].out_nodes[out] = text
                number += 1
                        
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
            number = 0
            for node in self.parent.nodes:
                for out in node.out_nodes:
                    if self.parent.nodes[number].out_nodes[out] == self.node.tag:
                        self.parent.nodes[number].out_nodes[out] = ""
                number += 1 
                
            self.parent.nodes.pop(self.parent.nodes.index(self.node))
            self.parent.update()
            self.close()
        

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())
