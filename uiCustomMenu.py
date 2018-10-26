# encoding: UTF-8
from vnpy.trader.uiQt import QtGui, QtWidgets, QtCore, BASIC_FONT
from qtpy.QtCore import Qt,QRect
from functools import partial
from qtpy.QtWidgets import QApplication, QWidget,QPushButton,QMenu
from qtpy.QtGui  import  QPainter, QPainterPath, QPen, QColor, QPixmap, QIcon, QBrush, QCursor
from vnpy.trader import vtText
from vnpy.event import Event
import qdarkstyle #Qt黑色主题
import sys
class CustomMenu( QtWidgets.QPushButton):
    """合约管理组件"""
    signal = QtCore.Signal(type(Event()))
    # ----------------------------------------------------------------------
    def __init__(self,parent):
        """Constructor"""
        super(CustomMenu, self).__init__()
        self.parent=parent

        # self.initUi()
        self.initMenu()
    #-----------------------------------------------------------------------
    def initMenu(self):
        self.setStyleSheet("QMenu{background:purple;}"
                           "QMenu{border:1px solid lightgray;}"
                           "QMenu{border-color:green;}"
                           "QMenu::item{padding:0px 20px 0px 15px;}"
                           "QMenu::item{height:30px;}"
                           "QMenu::item{color:blue;}"
                           "QMenu::item{background:white;}"
                           "QMenu::item{margin:1px 0px 0px 0px;}"

                           "QMenu::item:selected:enabled{background:lightgray;}"
                           "QMenu::item:selected:enabled{color:blue;}"
                           "QMenu::item:selected:!enabled{background:transparent;}"

                           "QMenu::separator{height:50px;}"
                           "QMenu::separator{width:1px;}"
                           "QMenu::separator{background:white;}"
                           "QMenu::separator{margin:1px 1px 1px 1px;}"

                           "QMenu#menu{background:white;}"
                           "QMenu#menu{border:1px solid lightgray;}"
                           "QMenu#menu::item{padding:0px 20px 0px 15px;}"
                           "QMenu#menu::item{height:15px;}"
                           "QMenu#menu::item:selected:enabled{background:lightgray;}"
                           "QMenu#menu::item:selected:enabled{color:white;}"
                           "QMenu#menu::item:selected:!enabled{background:transparent;}"
                           "QMenu#menu::separator{height:1px;}"
                           "QMenu#menu::separator{background:lightgray;}"
                           "QMenu#menu::separator{margin:2px 0px 2px 0px;}"
                           "QMenu#menu::indicator {padding:5px;}"
                           )
        self.color = QColor(Qt.gray)
        self.opacity = 1.0
        ''''''' 创建右键菜单 '''
        # 必须将ContextMenuPolicy设置为Qt.CustomContextMenu
        # 否则无法使用customContextMenuRequested信号
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        # 创建QMenu
        self.contextMenu = QMenu(self)
        self.trendMenu=self.contextMenu.addMenu(u"k线形态")
        self.swingMenu = self.contextMenu.addMenu(u"技术指标")
        self.amountMenu = self.contextMenu.addMenu(u"策略研究")
        # 添加二级菜单

        #趋势分析指标
        self.actionSAR= self.trendMenu.addAction(u'k线')
        self.actionSAR.triggered.connect(lambda: self.parent.initIndicator(u"KLINE"))

        self.actionMA = self.trendMenu.addAction(u'信号隐藏')
        self.actionMA.triggered.connect(lambda: self.parent.initIndicator(u"信号隐藏"))

        self.actionMA = self.trendMenu.addAction(u'信号显示')
        self.actionMA.triggered.connect(lambda: self.parent.initIndicator(u"信号显示"))

        #摆动分析
        self.actionCCI = self.swingMenu.addAction(u'MA SHORT')
        self.actionCCI.triggered.connect(lambda: self.parent.initIndicator(u"MA SHORT"))
        self.actionROC = self.swingMenu.addAction(u'MA LONG')
        self.actionROC.triggered.connect(lambda: self.parent.initIndicator(u"MA LONG"))
        self.actionSHORTTERM = self.swingMenu.addAction(u'SHORT TERM')
        self.actionSHORTTERM.triggered.connect(lambda: self.parent.initIndicator(u"SHORT TERM"))
        
        ##设为起始日期
        self.actionOPI = self.amountMenu.addAction(u'设为起始日期')
        self.actionOPI.triggered.connect(lambda: self.parent.initIndicator(u"设为起始日期"))        

        ##量仓分析
        self.actionOPI = self.amountMenu.addAction(u'MA_螺纹多_PLUS')
        self.actionOPI.triggered.connect(lambda: self.parent.initIndicator(u"MA_螺纹多_PLUS"))

        ##成交量分析
        self.actionVOL = self.amountMenu.addAction(u'SHORTTERM_螺纹')
        self.actionVOL.triggered.connect(lambda: self.parent.initIndicator(u"SHORTTERM_螺纹"))

        #self.contextMenu.exec_(QCursor.pos())  # 在鼠标位置显示
        #添加二级菜单



    def showContextMenu(self, pos):
        '''''
        右键点击时调用的函数
        '''
        # 菜单显示前，将它移动到鼠标点击的位置
        # self.contextMenu.move(self.pos() + pos)
        self.contextMenu.show()
        self.contextMenu.exec_(QCursor.pos())
        