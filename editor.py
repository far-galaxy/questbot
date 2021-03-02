# -*- coding: utf-8 -*-

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont, QPainter, QColor, QPen, QBrush, QPolygon, QPainterPath

import json
import math
import os


class Node():
    def __init__(self, position, tag, answer, out_nodes):
        self.position = position
        self.tag = tag
        self.answer = answer
        self.out_nodes = out_nodes
        self.width = 150
        self.header = 25
        self.height = 25 * (len(out_nodes) + 1)

        self.moveTo(position)

    # Move node to position
    def moveTo(self, position):
        self.position = position
        self.head = QRect(position, QSize(self.width - self.header, self.header))

        circleD = self.header - 10
        
        self.opt = {"rect": QRect(position.x() + self.width - self.header, position.y(), self.header, self.header), "selected": False}

        self.input_socket = {"rect": QRect(position.x() - circleD / 2, position.y() + 5, circleD, circleD), "selected": False}
        self.output_sockets = []

        for out in self.out_nodes:
            strY = position.y() + (len(self.output_sockets) + 2) * self.header
            circle = QRect(position.x() + self.width - circleD / 2, strY + 5, circleD, circleD)

            self.output_sockets.append({"rect": circle,
                                        "pos": QPoint(position.x() + self.width + circleD / 2, strY + self.header // 2),
                                        "goto": out,
                                        "selected": False,
                                        "connected": False})


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
        
        #   Triggers
        self.nodeSelected = None
        self.isDragging = False
        self.socketSelected = None
        self.optSelected = None
        self.ghostLine = {"socket": None, "line": None}

    def mouseMoveEvent(self, event):
        pos = event.pos()

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
                    if node.input_socket["rect"].contains(pos):
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
                    d = event.pos() - self.nodes[self.nodeSelected].position
                    self.dPos = d
                    
                
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
                    self.ghostLine["line"] = None
                    self.ghostLine["socket"] = None
                    self.update()

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
            head = node.position

            # Header
            painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
            painter.drawRect(node.head)

            # Header text
            header_text = QRect(head.x() + 15, head.y(), node.width, node.header)
            painter.setFont(QFont("Calibri", 14, QFont.Bold))
            painter.drawText(header_text, Qt.AlignLeft, node.tag)

            # Header cirle (Node Input)
            color = Qt.green if node.input_socket["selected"] and self.isDragging else Qt.cyan
            painter.setBrush(QBrush(color, Qt.SolidPattern))
            circleD = node.header - 10
            painter.drawEllipse(node.input_socket["rect"])
            
            # Node options
            color = Qt.green if node.opt["selected"] else Qt.cyan
            painter.setBrush(QBrush(color, Qt.SolidPattern))
            painter.drawRect(node.opt["rect"])

            # Main part
            painter.setBrush(QBrush(QColor(200, 200, 200, 255), Qt.SolidPattern))
            painter.drawRect(head.x(), head.y() + node.header, node.width, node.height)

            # Node outputs
            yNodeOut = 0
            for nodeOut in node.out_nodes:

                # Output text
                strY = head.y() + (node.header * 2) + yNodeOut * 25
                out_rect = QRect(head.x(), strY, node.width - circleD, 25)
                painter.setFont(QFont("Calibri", 14, QFont.Normal))
                painter.drawText(out_rect, Qt.AlignRight, nodeOut)

                # Start position
                start = QPoint(head.x() + node.width, strY + circleD / 2 + 5)

                circleColor = Qt.red

                # Draw line if output is definited.
                if node.out_nodes[nodeOut] != "":
                    # End position
                    endInd = [n.tag for n in self.nodes].index(node.out_nodes[nodeOut])
                    end = QPoint(self.nodes[endInd].position)
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
        self.nodes.append(Node(QPoint(100, 100), "node", "", {}))
        self.update()

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
        
        #-----------------Title---------------------------
        self.setWindowTitle("Node Edit")
        #self.setWindowIcon(QIcon('icon.png'))
        self.setFixedSize(400, 300)
        
        self.setFont(QFont("Calibri", 14, QFont.Normal))  
        
        self.tag_name_ = QLabel("Tag:", self)
        self.tag_name = QLineEdit(self)
        self.tag_name.setText(node.tag)
        self.tag_name.textChanged[str].connect(self.change_tag)
        
        lay = QVBoxLayout(self)
        
        hlay1 = QHBoxLayout()
        hlay1.addWidget(self.tag_name_)
        hlay1.addWidget(self.tag_name) 
        
        lay.addLayout(hlay1) 
        
    def change_tag(self, text):
        if text != "":
            ind = [n.tag for n in self.parent.nodes].index(self.node.tag)
            old_tag = self.parent.nodes[ind].tag
            
            number = 0
            for node in self.parent.nodes:
                for out in node.out_nodes:
                    if self.parent.nodes[number].out_nodes[out] == old_tag:
                        self.parent.nodes[number].out_nodes[out] = text
                number += 1
                        
            self.parent.nodes[ind].tag = text
                        
            
        


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())
