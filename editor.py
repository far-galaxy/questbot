# -*- coding: utf-8 -*-

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont, QPainter, QColor, QPen, QBrush, QPolygon, QPainterPath

import json
import math

class Node():
    def __init__ (self, position, tag, in_node, out_nodes):
        self.position = position
        self.tag = tag
        self.in_node = in_node
        self.out_nodes = out_nodes
        self.width = 150
        self.header = 25
        self.height = 25 * (len(out_nodes) + 1)
        
        self.moveTo(position)
        
        
        
    def moveTo(self, position):
        self.position = position
        self.head = QRect(position, QSize(self.width, self.header))
        
        circleD = self.header-10
        self.input_socket = QRect(position.x()-circleD/2, position.y()+5, circleD, circleD)
        
        self.output_sockets = []
        
        for out in self.out_nodes:
            strY = position.y() + (len(self.output_sockets) + 2) * self.header
            circle = QRect(position.x() + self.width - circleD/2, strY + 5, circleD, circleD)
            self.output_sockets.append({"rect":circle, "selected":False, "connected":False})        
    


class Widget(QWidget):
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        
        #-----------------Title---------------------------
        self.setWindowTitle('QuestBot Constructor')
        #self.setWindowIcon(QIcon('icon.png'))
        self.resize(800, 600)
        #self.setFont(QFont("Calibri", 16, QFont.Normal))
        
        self.w = self.frameGeometry().width()
        self.h = self.frameGeometry().height()   
        
        self.load_quest()
        
        self.setMouseTracking(True);
        self.Mpos = [0,0]
        self.nodeSelected = None
        self.isDragging = False
        
    def mouseMoveEvent(self, event):
        pos = event.pos()
        self.Mpos = [pos.x(), pos.y()]
        
        if not self.isDragging:
            isInHead = False
            isInOutputSocket = False
            number = 0
            for node in self.nodes:
                if node.head.contains(pos):
                    isInHead |= True
                    self.nodeSelected = number
                
                socket_number = 0
                for out in node.output_sockets:
                    if out["rect"].contains(pos):
                        isInOutputSocket |= True
                        self.nodes[number].output_sockets[socket_number]["selected"] = True
                        self.update()
                    else:
                        self.nodes[number].output_sockets[socket_number]["selected"] = False
                        self.update()
                    socket_number += 1
                number += 1
            if isInHead:
                self.setCursor(Qt.SizeAllCursor)
            elif isInOutputSocket:
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
                self.nodeSelected = None
            
            
                
        else:
            self.nodes[self.nodeSelected].moveTo(pos - self.dPos)
            self.update()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.nodeSelected != None and not self.isDragging:
                self.isDragging = True
                d = event.pos() - self.nodes[self.nodeSelected].position
                self.dPos = d
            elif self.isDragging:
                self.isDragging = False
                
        
    def keyPressEvent(self, e):
    
        if e.key() == Qt.Key_E: 
            self.load_quest()
            self.update()
        
    def paintEvent(self, event):    
        painter = QPainter(self)   
        painter.setFont(QFont("Calibri", 14, QFont.Bold))
        painter.setPen(QPen(Qt.black,  1, Qt.SolidLine))     
        
        for node in self.nodes:
            head = node.position
                   
            # Header
            painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
            #header = QRect(head, QSize(node.width, node.header))
            painter.drawRect(node.head)
                       
            # Header text
            header_text = QRect(head.x()+15, head.y(), node.width, node.header)
            painter.setFont(QFont("Calibri", 14, QFont.Bold))
            painter.drawText(header_text, Qt.AlignLeft, node.tag) 
            
            # Header cirle (Node Input)
            painter.setBrush(QBrush(Qt.cyan, Qt.SolidPattern))
            circleD = node.header-10
            painter.drawEllipse(node.input_socket)
            
            # Main part
            painter.setBrush(QBrush(QColor(200, 200, 200, 255), Qt.SolidPattern))
            painter.drawRect(head.x(), head.y() + node.header, node.width, node.height)            
            
            # Node outputs
            yNodeOut = 0
            for nodeOut in node.out_nodes:
                
                # Output text
                strY = head.y() + (node.header*2) + yNodeOut*25
                out_rect = QRect(head.x(), strY, node.width - circleD, 25)
                painter.setFont(QFont("Calibri", 14, QFont.Normal))
                painter.drawText(out_rect, Qt.AlignRight, nodeOut)
                
                # Start position
                start = QPoint(head.x() + node.width, strY + circleD/2 + 5)
                
                circleColor = Qt.red
                
                # Draw line if output is definited.
                if node.out_nodes[nodeOut] != "":                
                    # End position 
                    endInd = [n.tag for n in self.nodes].index(node.out_nodes[nodeOut])
                    end = QPoint(self.nodes[endInd].position)
                    end += QPoint(-circleD/2, circleD/2 + 5)
                    
                    painter.save()
                    painter.setPen(QPen(Qt.black,  2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                    painter.setBrush(QBrush(Qt.NoBrush))  
                    
                    path = self.curve(start, end)
                        
                    painter.drawPath(path) 

                    painter.restore()
                    painter.setPen(QPen(Qt.black,  1, Qt.SolidLine))
                    """
                    # Angle of line
                    angle = math.degrees(math.atan((yN-y0)/(xN-x0)))
                    
                    # Draw line.
                    painter.drawLine(start, end)
                    
                    # Arrow polygon
                    arrow = QPolygon(3)
                    arrow.putPoints(0, 0, 0)
                    arrow.putPoints(1, -10, 5)
                    arrow.putPoints(2, -10, -5)
                    
                    # Draw arrow. 
                    painter.save()       
                    painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
                    painter.translate(xN, yN)
                    painter.rotate(angle)               
                    painter.drawPolygon(arrow)
                    painter.setBrush(Qt.NoBrush)                
                    painter.restore()
                    """
                    
                    circleColor = Qt.cyan
                
                # Draw cirlce.
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
                    arc_start = start.x() + (delta.x() - delta.y()*2)//2
                    first_arc = QRectF(arc_start, start.y(), delta.y(), delta.y())
                    second_arc = QRectF(arc_start + delta.y(), start.y(), delta.y(), delta.y())
    
                    path = QPainterPath()
                    path.moveTo(start)
                    path.lineTo(arc_start + delta.y()//2, start.y())
                    path.arcTo(first_arc, 90, -90)
                    path.arcTo(second_arc, 180, 90)
                    path.lineTo(end)
    
                else:
                    arc_start = start.x() + (delta.x() + delta.y()*2)//2
                    first_arc = QRectF(arc_start, end.y(), -delta.y(), -delta.y())
                    second_arc = QRectF(arc_start - delta.y(), end.y(), -delta.y(), -delta.y())
    
                    path = QPainterPath()
                    path.moveTo(start)
                    path.lineTo(arc_start - delta.y()//2, start.y())
                    path.arcTo(first_arc, -90, 90)
                    path.arcTo(second_arc, 180, -90)
                    path.lineTo(end)
    
            else:
                if delta.y() > 0:
                    first_arc = QRectF(start.x() - delta.x()/2, start.y(), delta.x(), delta.x())
                    second_arc = QRectF(end.x() - delta.x()/2, end.y() - delta.x(), delta.x(), delta.x())
    
                    path = QPainterPath()
                    path.moveTo(start)
                    path.arcTo(first_arc, 90, -90)
                    path.lineTo(start.x() + delta.x()/2, end.y() - delta.x()/2)                                
                    path.arcTo(second_arc, 180, 90)
                    path.lineTo(end)
    
    
                else:
                    first_arc = QRectF(start.x() - delta.x()//2, start.y() - delta.x(), delta.x(), delta.x())
                    second_arc = QRectF(end.x() - delta.x()//2, end.y(), delta.x(), delta.x())
    
                    path = QPainterPath()
                    path.moveTo(start)
                    path.arcTo(first_arc, -90, 90)
                    path.lineTo(start.x() + delta.x()/2, end.y() + delta.x()/2)                                
                    path.arcTo(second_arc, 180, -90)
                    path.lineTo(end)
    
    
        else:
            half_dy = delta.y()/2
            flip = 1 if delta.y() > 0 else -1
    
            first_arc = QRectF(start.x() - half_dy/2, start.y(), half_dy, half_dy)
            second_arc = QRectF(end.x() - half_dy/2, end.y() - half_dy, half_dy, half_dy)
    
            path = QPainterPath()
            path.moveTo(start)
            path.arcTo(first_arc, 90, -180 * flip)
            path.lineTo(end.x(), start.y() + delta.y()/2)
            path.arcTo(second_arc, 90, 180 * flip)  
            
        return path
                
    def load_quest(self):
        f = open('quest.json', 'r', encoding="utf-8")
        self.quest = json.loads(f.read())
        f.close()
        
        self.nodes = []
        
        # Make nodes objects
        for node in self.quest:
            if node != "unidentified" and node != "help":
                position = self.quest[node]["position"]
                self.nodes.append(Node(QPoint(position[0], position[1]), node, "", self.quest[node]["goto"]))
            
    
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())