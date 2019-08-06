# -*- coding: utf-8 -*-
"""
Python K线模块,包含十字光标和鼠标键盘交互
Support By 量投科技(http://www.quantdo.com.cn/)
"""
import traceback
import talib as ta
import numpy as np
import pandas as pd
import os 
from functools import partial
from collections import deque

from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy import QtGui,QtCore
from uiCrosshair import Crosshair
from uiCustomMenu import  CustomMenu
import pyqtgraph as pg
from qtpy.QtGui  import  QPainter, QPainterPath, QPen, QColor, QPixmap, QIcon, QBrush, QCursor,QFont
import datetime as dt          

import json
import sys
from sys import path
path.append('F:\\vnpy-1.9.0\\examples\\CtaBacktesting')
reload(sys)
sys.setdefaultencoding('utf-8')          

#from runBacktesting_WH import calculateDailyResult_to_CSV as strategyDoubleMa_rb9999DailyResult
#from runBacktesting_WH import get_strategy_init_days as strategyDoubleMa_get_strategy_init_days
#from runBacktesting_WH import calculateDailyResult_init as strategyDoubleMa_calculateDailyResult_init


import importlib
import runBacktesting_ShortTermStrategy_RB          as STRB
import runBacktesting_ShortTermStrategy_Overhigh_RB as STOVRB
import runBacktesting_RB                            as DMARB
import runBacktesting_Volatility_RB                 as VRB
import runBacktesting_Volatility_RB_V1              as VRB1
import runBacktesting_WaiBaoDay_RB                  as WBDRB
# 字符串转换
#---------------------------------------------------------------------------------------
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

########################################################################
# 键盘鼠标功能
########################################################################
class KeyWraper(QWidget):
    """键盘鼠标功能支持的元类"""
    #初始化
    #----------------------------------------------------------------------
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setMouseTracking(True)

    #重载方法keyPressEvent(self,event),即按键按下事件方法
    #----------------------------------------------------------------------
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Up:
            self.onUp()
        elif event.key() == QtCore.Qt.Key_Down:
            self.onDown()
        elif event.key() == QtCore.Qt.Key_Left:
            self.onLeft()
        elif event.key() == QtCore.Qt.Key_Right:
            self.onRight()
        elif event.key() == QtCore.Qt.Key_PageUp:
            self.onPre()
        elif event.key() == QtCore.Qt.Key_PageDown:
            self.onNxt()

    #重载方法mousePressEvent(self,event),即鼠标点击事件方法
    #----------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.onRClick(event.pos())
        elif event.button() == QtCore.Qt.LeftButton:
            self.onLClick(event.pos())

    #重载方法mouseReleaseEvent(self,event),即鼠标点击事件方法
    #----------------------------------------------------------------------
    def mouseRelease(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.onRRelease(event.pos())
        elif event.button() == QtCore.Qt.LeftButton:
            self.onLRelease(event.pos())
        self.releaseMouse()

    #重载方法wheelEvent(self,event),即滚轮事件方法
    #----------------------------------------------------------------------
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0 :
            self.onUp()
        else:
            self.onDown()
            pass
        
        return

    #重载方法paintEvent(self,event),即拖动事件方法
    #----------------------------------------------------------------------
    def paintEvent(self, event):
        self.onPaint()

    # PgDown键
    #----------------------------------------------------------------------
    def onNxt(self):
        pass

    # PgUp键
    #----------------------------------------------------------------------
    def onPre(self):
        pass

    # 向上键和滚轮向上
    #----------------------------------------------------------------------
    def onUp(self):
        pass

    # 向下键和滚轮向下
    #----------------------------------------------------------------------
    def onDown(self):
        pass
    
    # 向左键
    #----------------------------------------------------------------------
    def onLeft(self):
        pass

    # 向右键
    #----------------------------------------------------------------------
    def onRight(self):
        pass

    # 鼠标左单击
    #----------------------------------------------------------------------
    def onLClick(self,pos):
        pass

    # 鼠标右单击
    #----------------------------------------------------------------------
    def onRClick(self,pos):
        pass

    # 鼠标左释放
    #----------------------------------------------------------------------
    def onLRelease(self,pos):
        pass

    # 鼠标右释放
    #----------------------------------------------------------------------
    def onRRelease(self,pos):
        pass

    # 画图
    #----------------------------------------------------------------------
    def onPaint(self):
        pass
  

########################################################################
# 选择缩放功能支持
########################################################################
class CustomViewBox(pg.ViewBox):
    #----------------------------------------------------------------------
    def __init__(self, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        # 拖动放大模式
        #self.setMouseMode(self.RectMode)
        
    ## 右键自适应
    #----------------------------------------------------------------------
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self.autoRange()


########################################################################
# 时间序列，横坐标支持
########################################################################
class MyStringAxis(pg.AxisItem):
    """时间序列横坐标支持"""
    
    # 初始化 
    #----------------------------------------------------------------------
    def __init__(self, xdict, *args, **kwargs):
        pg.AxisItem.__init__(self, *args, **kwargs)
        self.minVal = 0 
        self.maxVal = 0
        self.xdict  = xdict
        self.x_values = np.asarray(xdict.keys())
        self.x_strings = xdict.values()
        self.setPen(color=(255, 255, 255, 255), width=0.8)
        self.setStyle(tickFont = QFont("Roman times",10,QFont.Bold),autoExpandTextSpace=True)

    # 更新坐标映射表
    #----------------------------------------------------------------------
    def update_xdict(self, xdict):
        self.xdict.update(xdict)
        self.x_values  = np.asarray(self.xdict.keys())
        self.x_strings = self.xdict.values()

    # 将原始横坐标转换为时间字符串,第一个坐标包含日期
    #----------------------------------------------------------------------
    def tickStrings(self, values, scale, spacing):
        strings = []
        for v in values:
            vs = v * scale
            if vs in self.x_values:
                vstr = self.x_strings[np.abs(self.x_values-vs).argmin()]
                vstr = vstr.strftime('%Y-%m-%d')
            else:
                vstr = ""
            strings.append(vstr)
        return strings

########################################################################
# K线图形对象
########################################################################
class CandlestickItem(pg.GraphicsObject):
    """K线图形对象"""

    # 初始化
    #----------------------------------------------------------------------
    def __init__(self, data):
        """初始化"""
        pg.GraphicsObject.__init__(self)
        # 数据格式: [ (time, open, close, low, high),...]
        self.data = data
        # 只重画部分图形，大大提高界面更新速度
        self.rect = None
        self.picture = None
        self.setFlag(self.ItemUsesExtendedStyleOption)
        # 画笔和画刷
        w = 0.4
        self.offset   = 0
        self.low      = 0
        self.high     = 1
        self.picture  = QtGui.QPicture()
        self.pictures = []
        self.bPen     = pg.mkPen(color=(0, 240, 240, 255), width=w*2)
        self.bBrush   = pg.mkBrush((0, 240, 240, 255))
        self.rPen     = pg.mkPen(color=(255, 60, 60, 255), width=w*2)
        self.rBrush   = pg.mkBrush((255, 60, 60, 255))
        self.rBrush.setStyle(Qt.NoBrush)
        # 刷新K线
        self.generatePicture(self.data)          


    # 画K线
    #----------------------------------------------------------------------
    def generatePicture(self,data=None,redraw=False):
        """重新生成图形对象"""
        # 重画或者只更新最后一个K线
        if redraw:
            self.pictures = []
        elif self.pictures:
            self.pictures.pop()
        w = 0.4
        bPen   = self.bPen
        bBrush = self.bBrush
        rPen   = self.rPen
        rBrush = self.rBrush
        self.low,self.high = (np.min(data['low']),np.max(data['high'])) if len(data)>0 else (0,1)
        npic = len(self.pictures)
        for (t, open0, close0, low0, high0) in data:
            if t >= npic:
                picture = QtGui.QPicture()
                p = QtGui.QPainter(picture)
                # 下跌蓝色（实心）, 上涨红色（空心）
                pen,brush,pmin,pmax = (bPen,bBrush,close0,open0)\
                    if open0 > close0 else (rPen,rBrush,open0,close0)
                p.setPen(pen)  
                p.setBrush(brush)
                # 画K线方块和上下影线
                if open0 == close0:
                    p.drawLine(QtCore.QPointF(t-w,open0), QtCore.QPointF(t+w, close0))
                else:
                    p.drawRect(QtCore.QRectF(t-w, open0, w*2, close0-open0))
                if pmin  > low0:
                    p.drawLine(QtCore.QPointF(t,low0), QtCore.QPointF(t, pmin))
                if high0 > pmax:
                    p.drawLine(QtCore.QPointF(t,pmax), QtCore.QPointF(t, high0))
                p.end()
                self.pictures.append(picture)

    # 手动重画
    #----------------------------------------------------------------------
    def update(self):
        if not self.scene() is None:
            self.scene().update()

    # 自动重画
    #----------------------------------------------------------------------
    def paint(self, painter, opt, w):
        rect = opt.exposedRect
        xmin,xmax = (max(0,int(rect.left())),min(int(len(self.pictures)),int(rect.right())))
        if not self.rect == (rect.left(),rect.right()) or self.picture is None:
            self.rect = (rect.left(),rect.right())
            self.picture = self.createPic(xmin,xmax)
            self.picture.play(painter)
        elif not self.picture is None:
            self.picture.play(painter)

    # 缓存图片
    #----------------------------------------------------------------------
    def createPic(self,xmin,xmax):
        picture = QPicture()
        p = QPainter(picture)
        [pic.play(p) for pic in self.pictures[xmin:xmax]]
        p.end()
        return picture

    # 定义边界
    #----------------------------------------------------------------------
    def boundingRect(self):
        return QtCore.QRectF(0,self.low,len(self.pictures),(self.high-self.low))
    
    #----------------------------------------------------------------------
    def hide(self):
        self.parent.hide()
        pass
        
        

########################################################################
class KLineWidget(KeyWraper):
    """用于显示价格走势图"""

    # 窗口标识
    clsId = 0

    # 保存K线数据的列表和Numpy Array对象
    listBar  = []
    listVol  = []
    listHigh = []
    listLow  = []
    KLINE_DATE = []
    KLINE_OPEN = []
    KLINE_HIGH = []
    KLINE_LOW = []
    KLINE_SHORT_TERM_LOW = []
    KLINE_SHORT_TERM_HIGH = []
    KLINE_SHORT_TERM_LIST_ALL=[]
    KLINE_SHORT_TERM_LIST_FIRST=[]
    KLINE_SHORT_TERM_LIST_LIMIT=[]
    KLINE_WAIBAORI=[]    
    KLINE_GJR_BUY=[]    
    KLINE_GJR_SELL=[]    
    listClose  = []
    listSig  = []
    listOpenInterest = []
    arrows   = []
    KLINE_SHORT_TERM_LIST_ALL_arrows = []
    KLINE_SHORT_TERM_LIST_FIRST_arrows = []
    KLINE_SHORT_TERM_LIST_LIMIT_arrows = []
    KLINE_WAI_BAO_RI_arrows = []
    KLINE_GJR_BUY_arrows = []
    KLINE_GJR_SELL_arrows = []
    curves   = []
    KLINE_SHORT_TERM_LIST_ALL_curves = []
    KLINE_SHORT_TERM_LIST_FIRST_curves = []
    KLINE_SHORT_TERM_LIST_LIMIT_curves = []
    listSig_deal_DIRECTION  = []
    listSig_deal_OFFSET = []
    KLINE_CLOSE=[]
    start_date=[] #[20090327开始日期，列表的位置]
    end_date=[]   #[20181127结束日期，结束的位置]   
    KLINE_show           =True
    MA_SHORT_show        =False
    MA_LONG_show         =False
    listbarshow          =False
    SHORT_TERM_SHOW      =False    
    SHORT_TERM_SHOW_FIRST=False
    SHORT_TERM_SHOW_LIMIT=False
    SHORT_TERM_SHOW_ALL  =False
    WAIBAORI_SHOW        =False
    GJRBUY_SHOW          =False
    signal_show          =True     


    # 是否完成了历史数据的读取
    initCompleted = False
    
    #----------------------------------------------------------------------
    def __init__(self,parent=None):
        """Constructor"""
        self.parent = parent
        super(KLineWidget, self).__init__(parent)

        # 当前序号
        self.index    = None    # 下标
        self.countK   = 60      # 显示的Ｋ线范围

        KLineWidget.clsId += 1
        self.windowId = str(KLineWidget.clsId)

        # 缓存数据
        self.datas    = []
        self.listBar  = []
        self.listbarshow= True
        self.listVol  = []
        self.listHigh = []
        self.listLow  = []
        self.listSig  = []
        self.listOpenInterest = []
        self.arrows   = []
        self.curves   = []
        self.listSig_deal_DIRECTION  = []
        self.listSig_deal_OFFSET = []    
        self.KLINE_CLOSE=[]       
        self.MA_SHORT_real=[]
        self.MA_LONG_real=[]
        self.start_time=[]
        self.MA_SHORT_show=False
        self.MA_LONG_show=False  
        self.SHORT_TERM_SHOW=False
        self.SHORT_TERM_SHOW_FIRST=False
        self.SHORT_TERM_SHOW_LIMIT=False
        self.SHORT_TERM_SHOW_ALL=False
        self.signal_show=False
        self.cur_jsonname=u'json\\uiKLine_startpara.json'
        self.SP_signal='close'
        self.BP_signal='close'
        self.dailyresult_path = ''
        self.dailydata_path = ''     
        # 所有K线上信号图
        self.allColor = deque(['blue','green','yellow','white'])
        self.sigData  = {}
        self.sigColor = {}
        self.sigPlots = {}

        # 所副图上信号图
        self.allSubColor = deque(['blue','green','yellow','white'])
        self.subSigData  = {}
        self.subSigColor = {}
        self.subSigPlots = {}

        # 初始化完成
        self.initCompleted = False

        # 调用函数
        self.initUi()

        self.menu= CustomMenu(self)
    #----------------------------------------------------------------------
    #  初始化相关 
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(u'K线工具')
        # 主图
        self.pw = pg.PlotWidget()
        # 界面布局
        self.lay_KL = pg.GraphicsLayout(border=(100,100,100))
        self.lay_KL.setContentsMargins(10, 10, 10, 10)
        self.lay_KL.setSpacing(0)
        self.lay_KL.setBorder(color=(255, 0, 0, 255), width=0.8)
        self.lay_KL.setZValue(0)
        self.KLtitle = self.lay_KL.addLabel(u'')
        self.pw.setCentralItem(self.lay_KL)
        # 设置横坐标
        xdict = {}
        self.axisTime = MyStringAxis(xdict, orientation='bottom')
        # 初始化子图
        self.initplotKline()
        self.initplotVol()  
        self.initplotOI()
        # 注册十字光标
        self.crosshair = Crosshair(self.pw,self)
        # 设置界面
        self.vb = QVBoxLayout()
        self.vb.addWidget(self.pw)
        self.setLayout(self.vb)
        # 初始化完成
        self.initCompleted = True    

    #----------------------------------------------------------------------
    def makePI(self,name):
        """生成PlotItem对象"""
        vb = CustomViewBox()
        plotItem = pg.PlotItem(viewBox = vb, name=name ,axisItems={'bottom': self.axisTime})
        plotItem.setMenuEnabled(False)
        plotItem.setClipToView(True)
        plotItem.hideAxis('left')
        plotItem.showAxis('right')
        plotItem.setDownsampling(mode='peak')
        plotItem.setRange(xRange = (0,1),yRange = (0,1))
        plotItem.getAxis('right').setWidth(30)
        plotItem.getAxis('right').setStyle(tickFont = QFont("Roman times",10,QFont.Bold))
        plotItem.getAxis('right').setPen(color=(255, 0, 0, 255), width=0.8)
        plotItem.showGrid(True,True)
        plotItem.hideButtons()
        return plotItem

    #----------------------------------------------------------------------
    def initplotVol(self):
        """初始化成交量子图"""
        self.pwVol  = self.makePI('_'.join([self.windowId,'PlotVOL']))
        self.volume = CandlestickItem(self.listVol)
        self.pwVol.addItem(self.volume)
        
        
        self.pwVol.setMaximumHeight(50)
        self.pwVol.setXLink('_'.join([self.windowId,'PlotOI']))
        self.pwVol.hideAxis('bottom')

        self.lay_KL.nextRow()
        self.lay_KL.addItem(self.pwVol)

    #----------------------------------------------------------------------
    def initplotKline(self):
        """初始化K线子图以及指标子图"""
        self.pwKL = self.makePI('_'.join([self.windowId,'PlotKL']))
        self.candle = CandlestickItem(self.listBar)
        self.pwKL.addItem(self.candle)
        
        
        self.KLINEOI_CLOSE = pg.PlotCurveItem(pen=({'color': "w", 'width': 1})) 
        self.pwKL.addItem(self.KLINEOI_CLOSE)
        self.KLINEOI_CLOSE.hide()
        
        
              
        self.MA_SHORTOI = pg.PlotCurveItem(pen=({'color': "r", 'width': 1})) 
        self.pwKL.addItem(self.MA_SHORTOI)
        self.MA_SHORTOI.hide()        
        
        
        self.MA_LONGOI = pg.PlotCurveItem(pen=({'color': "r", 'width': 1,'dash':[3, 3, 3, 3]})) 
        self.pwKL.addItem(self.MA_LONGOI)
        self.MA_LONGOI.hide()                
               
        self.start_date_Line     = pg.InfiniteLine(angle=90, movable=False,pen=({'color': [255, 255, 255, 100], 'width': 0.5})) 
        self.pwKL.addItem(self.start_date_Line)
        
        self.end_date_Line     = pg.InfiniteLine(angle=90,movable=False,pen=({'color': [255, 255, 0, 100], 'width': 0.5})) 
        self.pwKL.addItem(self.end_date_Line)        
        
        self.pwKL.setMinimumHeight(350)
        self.pwKL.setXLink('_'.join([self.windowId,'PlotOI']))
        self.pwKL.hideAxis('bottom')

        self.lay_KL.nextRow()
        self.lay_KL.addItem(self.pwKL)

    #----------------------------------------------------------------------
    def initplotOI(self):
        """初始化持仓量子图"""
        self.pwOI = self.makePI('_'.join([self.windowId,'PlotOI']))
        self.curveOI = self.pwOI.plot()

        self.pwOI.setMaximumHeight(50)
        self.lay_KL.nextRow()
        self.lay_KL.addItem(self.pwOI)
        pass

    #----------------------------------------------------------------------
    def reinit(self,pingzhongname,filename,dailyresultname,jsonname):
        """更换品种，重新初始化"""
        # K线界面
        ui.loadKLineSetting(jsonname)
        ui.KLtitle.setText(pingzhongname+'   '+ui.StrategyName ,size='10pt',color='FFFF00')
        ui.loadData(pd.DataFrame.from_csv(filename))
        ui.loadData_listsig(pd.DataFrame.from_csv(dailyresultname))
        # 初始化界面显示
        self.SHORT_TERM_SHOW_ALL =False
        self.SHORT_TERM_SHOW_FIRST =False
        self.SHORT_TERM_SHOW_LIMIT =False
        ui.initIndicator(u'MA SHORT')
        ui.initIndicator(u'MA LONG')
        ui.initIndicator(u'KLINE')
        ui.initIndicator(u'SHORT TERM(First)')
        ui.initIndicator(u'SHORT TERM(All)')
        ui.initIndicator(u'SHORT TERM(Limit)')
        if ui.signal_show == True :
            ui.initIndicator(u'信号显示')
        else:
            ui.initIndicator(u'信号隐藏')
        ui.refreshAll()
    #----------------------------------------------------------------------
    #  画图相关 
    #----------------------------------------------------------------------
    def plotVol(self,redraw=False,xmin=0,xmax=-1):
        """重画成交量子图"""
        if self.initCompleted:
            self.volume.generatePicture(self.listVol[xmin:xmax],redraw)   # 画成交量子图

    #----------------------------------------------------------------------
    def plotKline(self,redraw=False,xmin=0,xmax=-1):
        """重画K线子图"""
        if self.initCompleted:
            self.candle.generatePicture(self.listBar[xmin:xmax],redraw)   # 画K线
            self.KLINEOI_CLOSE.setData(np.array(self.KLINE_CLOSE))        # 画收盘价曲线
            self.plotMark()                                               # 显示开平仓信号位置
            
    #----------------------------------------------------------------------   
    def plotMA_SHORT(self):
        """重画MA_SHORT """
        if self.initCompleted:
            self.MA_SHORTOI.setData(np.array(self.MA_SHORT_real))#画MA_SHORT            
            self.refresh()               
    #----------------------------------------------------------------------   
    def plotMA_LONG(self):
        """重画MA_LONG  """
        if self.initCompleted:
            self.MA_LONGOI.setData(np.array(self.MA_LONG_real))#画MA_LONG 
            self.refresh()           
    #----------------------------------------------------------------------   
    def plot_startdate(self,pos):
        """重画起始日期  """
        if self.initCompleted:
            self.start_date_Line.setPos(pos)     
    #----------------------------------------------------------------------   
    def plot_enddate(self,pos):
        """重画起始日期  """
        if self.initCompleted:
            self.end_date_Line.setPos(pos) 
    #----------------------------------------------------------------------
    def plotOI(self,xmin=0,xmax=-1):
        """重画持仓量子图"""
        if self.initCompleted:
            self.curveOI.setData(np.append(self.listOpenInterest[xmin:xmax],0), pen='w', name="OpenInterest")

    #----------------------------------------------------------------------
    def addSig(self,sig,main=True):
        """新增信号图"""
        if main:
            if sig in self.sigPlots:
                self.pwKL.removeItem(self.sigPlots[sig])
            self.sigPlots[sig] = self.pwKL.plot()
            self.sigColor[sig] = self.allColor[0]
            self.allColor.append(self.allColor.popleft())
        else:
            if sig in self.subSigPlots:
                self.pwOI.removeItem(self.subSigPlots[sig])
            self.subSigPlots[sig] = self.pwOI.plot()
            self.subSigColor[sig] = self.allSubColor[0]
            self.allSubColor.append(self.allSubColor.popleft())

    #----------------------------------------------------------------------
    def showSig(self,datas,main=True,clear=False):
        """刷新信号图"""
        if clear:
            self.clearSig(main)
            if datas and not main:
                sigDatas = np.array(datas.values()[0])
                self.listOpenInterest = sigDatas
                self.datas['openInterest'] = sigDatas
                self.plotOI(0,len(sigDatas))
        if main:
            for sig in datas:
                self.addSig(sig,main)
                self.sigData[sig] = datas[sig]
                self.sigPlots[sig].setData(np.append(datas[sig],0), pen=self.sigColor[sig][0], name=sig)
        else:
            for sig in datas:
                self.addSig(sig,main)
                self.subSigData[sig] = datas[sig]
                self.subSigPlots[sig].setData(np.append(datas[sig],0), pen=self.subSigColor[sig][0], name=sig)

    #----------------------------------------------------------------------
    def plotMark(self):
        """显示开平仓信号"""
        # 检查是否有数据
        if len(self.datas)==0:
            return
        for arrow in self.arrows:
            self.pwKL.removeItem(arrow)
        for curve in self.curves:
            self.pwKL.removeItem(curve)
        # 画买卖信号
        lastbk_x=-1  #上一个买开的x
        lastbk_y=-1  #上一个买开的y
        lastsk_x=-1  #上一个卖开的x
        lastsk_y=-1  #上一个卖开的y        
        for i in range(len(self.listSig_deal_DIRECTION)):
            # 无信号
            if   cmp(self.listSig_deal_DIRECTION[i] , '-')== 0 or cmp(self.listSig_deal_OFFSET[i] , '-') == 0:
                continue
            # 买开信号
            elif cmp(self.listSig_deal_DIRECTION[i] , '多')==0 and cmp(self.listSig_deal_OFFSET[i] , '开仓')==0 :
                arrow = pg.ArrowItem(pos=(i, self.datas[i]['low']), size=7,tipAngle=55,tailLen=3,tailWidth=4, angle=90, brush=(255, 0, 0),pen=({'color': "r", 'width': 1}))
                lastbk_x = i
                lastbk_y = self.datas[i]['close']
            # 卖平信号
            elif cmp(self.listSig_deal_DIRECTION[i] , '空')==0  and cmp(self.listSig_deal_OFFSET[i] , '平仓')==0 :
                arrow = pg.ArrowItem(pos=(i, self.datas[i]['high']),size=7,tipAngle=55,tailLen=3,tailWidth=4 ,angle=-90, brush=(0, 0, 0),pen=({'color': "g", 'width': 1}))
                if lastbk_x !=-1:
                    curve = pg.PlotCurveItem(x=np.array([lastbk_x,i]),y=np.array([lastbk_y,self.datas[i][self.SP_signal]]),name='duo',pen=({'color': "r", 'width': 3})) 
                    self.pwKL.addItem(curve)          
                    self.curves.append(curve)  
                    lastbk_x = -1
            # 卖开信号
            elif cmp(self.listSig_deal_DIRECTION[i] , '空')==0  and cmp(self.listSig_deal_OFFSET[i] , '开仓')==0 :
                arrow = pg.ArrowItem(pos=(i, self.datas[i]['high']),size=7,tipAngle=55,tailLen=3,tailWidth=4,angle=-90, brush=(0, 255, 0),pen=({'color': "g", 'width': 1}))
                lastsk_x = i
                lastsk_y = self.datas[i]['close']                
            # 买平信号
            elif cmp(self.listSig_deal_DIRECTION[i] , '多')==0  and cmp(self.listSig_deal_OFFSET[i] , '平仓')==0 :
                arrow = pg.ArrowItem(pos=(i, self.datas[i]['low']),size=7,tipAngle=55,tailLen=3,tailWidth=4 ,angle=90, brush=(0, 0, 0),pen=({'color': "r", 'width': 1}))
                if lastsk_x !=-1:
                    curve = pg.PlotCurveItem(x=np.array([lastsk_x,i]),y=np.array([lastsk_y,self.datas[i][self.BP_signal]]),pen=({'color': "g", 'width': 3})) 
                    self.pwKL.addItem(curve)          
                    self.curves.append(curve)  
                    lastsk_x = -1
            self.pwKL.addItem(arrow)
            self.arrows.append(arrow)                
    #----------------------------------------------------------------------
    def plotIndex_LIMIT (self):
        """画指标"""
        # 检查是否有数据
        if len(self.KLINE_SHORT_TERM_LIST_LIMIT)==0 :
            self.refresh()   
            return
        for arrow in self.KLINE_SHORT_TERM_LIST_LIMIT_arrows:
            self.pwKL.removeItem(arrow)      
        for curves in self.KLINE_SHORT_TERM_LIST_LIMIT_curves:
            self.pwKL.removeItem(curves)              
        for i in range(len(self.KLINE_SHORT_TERM_LIST_LIMIT)):
            if  self.KLINE_SHORT_TERM_LIST_LIMIT[i] == 1:
                arrow = pg.ArrowItem(pos=(i, self.datas[i]['low']), size=7,tipAngle=55,tailLen=3,tailWidth=4, angle=90, brush=(34, 139, 34),pen=({'color': "228B22", 'width': 1}))   
                self.pwKL.addItem(arrow)
                self.KLINE_SHORT_TERM_LIST_LIMIT_arrows.append(arrow)    
            if  self.KLINE_SHORT_TERM_LIST_LIMIT[i] == 2:  
                arrow = pg.ArrowItem(pos=(i, self.datas[i]['high']),size=7,tipAngle=55,tailLen=3,tailWidth=4 ,angle=-90, brush=(34, 139, 34),pen=({'color': "228B22", 'width': 1}))
                self.pwKL.addItem(arrow)
                self.KLINE_SHORT_TERM_LIST_LIMIT_arrows.append(arrow)   
        last_x=-1  #上一个x
        last_y=-1  #上一个y   
        last_v=-1
        for i in range(len(self.KLINE_SHORT_TERM_LIST_LIMIT)):
            if  self.KLINE_SHORT_TERM_LIST_LIMIT[i] != 0 :
                if    last_x!=-1 and last_y!=-1 and  last_v!=self.KLINE_SHORT_TERM_LIST_LIMIT[i] and\
                    ((last_v == 1 and self.KLINE_SHORT_TERM_LIST_LIMIT[i] == 2) and self.KLINE_LOW[last_x]<self.KLINE_HIGH[i]) or\
                    ((last_v == 2 and self.KLINE_SHORT_TERM_LIST_LIMIT[i] == 1) and self.KLINE_HIGH[last_x]>self.KLINE_LOW[i]):
                        curve = pg.PlotCurveItem(x=np.array([last_x,i]),y=np.array([last_y,self.datas[i]['low'] if self.KLINE_SHORT_TERM_LIST_LIMIT[i]==1 else self.datas[i]['high']]),name='duo',pen=({'color': "228B22", 'width': 1}))                 
                        self.pwKL.addItem(curve)          
                        self.KLINE_SHORT_TERM_LIST_LIMIT_curves.append(curve)    
                last_x =i
                if  self.KLINE_SHORT_TERM_LIST_LIMIT[i]  ==1 :  
                    last_y=self.datas[i]['low']     
                elif self.KLINE_SHORT_TERM_LIST_LIMIT[i] ==2 :  
                    last_y=self.datas[i]['high']   
                last_v=self.KLINE_SHORT_TERM_LIST_LIMIT[i]
                
    #----------------------------------------------------------------------
    def plotIndex_ALL (self):
        """画指标"""
        # 检查是否有数据
        if len(self.KLINE_SHORT_TERM_LIST_ALL)==0 :
            self.refresh()            
            return
        for arrow in self.KLINE_SHORT_TERM_LIST_ALL_arrows:
            self.pwKL.removeItem(arrow)     
        for curves in self.KLINE_SHORT_TERM_LIST_ALL_curves:
            self.pwKL.removeItem(curves)              
        for i in range(len(self.KLINE_SHORT_TERM_LIST_ALL)):
            if  self.KLINE_SHORT_TERM_LIST_ALL[i] == 1:
                arrow = pg.ArrowItem(pos=(i, self.datas[i]['low']), size=7,tipAngle=55,tailLen=3,tailWidth=4, angle=90, brush=(225, 0, 225),pen=({'color': "FF00FF", 'width': 1}))   
                self.pwKL.addItem(arrow)
                self.KLINE_SHORT_TERM_LIST_ALL_arrows.append(arrow)    
            if  self.KLINE_SHORT_TERM_LIST_ALL[i] == 2:  
                arrow = pg.ArrowItem(pos=(i, self.datas[i]['high']),size=7,tipAngle=55,tailLen=3,tailWidth=4 ,angle=-90, brush=(225, 0, 225),pen=({'color': "FF00FF", 'width': 1}))
                self.pwKL.addItem(arrow)
                self.KLINE_SHORT_TERM_LIST_ALL_arrows.append(arrow)   
        last_x=-1  #上一个x
        last_y=-1  #上一个y   
        last_v=-1
        for i in range(len(self.KLINE_SHORT_TERM_LIST_ALL)):
            if  self.KLINE_SHORT_TERM_LIST_ALL[i] != 0 :
                if    last_x!=- 1 and last_y!=-1                              and                                                \
                    ((last_v == 1 and self.KLINE_SHORT_TERM_LIST_ALL[i] == 2) and self.KLINE_LOW[last_x]<self.KLINE_HIGH[i]) or  \
                    ((last_v == 2 and self.KLINE_SHORT_TERM_LIST_ALL[i] == 1) and self.KLINE_HIGH[last_x]>self.KLINE_LOW[i]) or  \
                    ((last_v == 1 and self.KLINE_SHORT_TERM_LIST_ALL[i] == 1))                                                or  \
                    ((last_v == 2 and self.KLINE_SHORT_TERM_LIST_ALL[i] == 2))                                                    :
                        curve = pg.PlotCurveItem(x=np.array([last_x,i]),y=np.array([last_y,self.datas[i]['low'] if self.KLINE_SHORT_TERM_LIST_ALL[i]==1 else self.datas[i]['high']]),name='duo',pen=({'color': "FF00FF", 'width': 1}))                 
                        self.pwKL.addItem(curve)          
                        self.KLINE_SHORT_TERM_LIST_ALL_curves.append(curve)    
                last_x =i
                if  self.KLINE_SHORT_TERM_LIST_ALL[i]  ==1 :  
                    last_y=self.datas[i]['low']     
                elif self.KLINE_SHORT_TERM_LIST_ALL[i] ==2 :  
                    last_y=self.datas[i]['high']   
                last_v=self.KLINE_SHORT_TERM_LIST_ALL[i]                
    #----------------------------------------------------------------------
    def plotIndex_FIRST (self):
        """画指标"""
        # 检查是否有数据
        if len(self.KLINE_SHORT_TERM_LIST_FIRST)==0 :
            self.refresh()   
            return
        for arrow in self.KLINE_SHORT_TERM_LIST_FIRST_arrows:
            self.pwKL.removeItem(arrow)     
        for curves in self.KLINE_SHORT_TERM_LIST_FIRST_curves:
            self.pwKL.removeItem(curves)              
        for i in range(len(self.KLINE_SHORT_TERM_LIST_FIRST)):
            if  self.KLINE_SHORT_TERM_LIST_FIRST[i] == 1:
                arrow = pg.ArrowItem(pos=(i, self.datas[i]['low']), size=7,tipAngle=55,tailLen=3,tailWidth=4, angle=90, brush=(225, 255, 0),pen=({'color': "FFFF00", 'width': 1}))   
                self.pwKL.addItem(arrow)
                self.KLINE_SHORT_TERM_LIST_FIRST_arrows.append(arrow)    
            if  self.KLINE_SHORT_TERM_LIST_FIRST[i] == 2:  
                arrow = pg.ArrowItem(pos=(i, self.datas[i]['high']),size=7,tipAngle=55,tailLen=3,tailWidth=4 ,angle=-90, brush=(225, 255, 0),pen=({'color': "FFFF00", 'width': 1}))
                self.pwKL.addItem(arrow)
                self.KLINE_SHORT_TERM_LIST_FIRST_arrows.append(arrow)   
        last_x=-1  #上一个x
        last_y=-1  #上一个y   
        last_v=-1
        for i in range(len(self.KLINE_SHORT_TERM_LIST_FIRST)):
            if  self.KLINE_SHORT_TERM_LIST_FIRST[i] != 0 :
                if    last_x!=-1 and last_y!=-1 and  last_v!=self.KLINE_SHORT_TERM_LIST_FIRST[i] and\
                    ((last_v == 1 and self.KLINE_SHORT_TERM_LIST_FIRST[i] == 2) and self.KLINE_LOW[last_x]<self.KLINE_HIGH[i]) or\
                    ((last_v == 2 and self.KLINE_SHORT_TERM_LIST_FIRST[i] == 1) and self.KLINE_HIGH[last_x]>self.KLINE_LOW[i]):
                        curve = pg.PlotCurveItem(x=np.array([last_x,i]),y=np.array([last_y,self.datas[i]['low'] if self.KLINE_SHORT_TERM_LIST_FIRST[i]==1 else self.datas[i]['high']]),name='duo',pen=({'color': "FFFF00", 'width': 1}))                 
                        self.pwKL.addItem(curve)          
                        self.KLINE_SHORT_TERM_LIST_FIRST_curves.append(curve)    
                last_x =i
                if  self.KLINE_SHORT_TERM_LIST_FIRST[i]  ==1 :  
                    last_y=self.datas[i]['low']     
                elif self.KLINE_SHORT_TERM_LIST_FIRST[i] ==2 :  
                    last_y=self.datas[i]['high']   
                last_v=self.KLINE_SHORT_TERM_LIST_FIRST[i]
    #----------------------------------------------------------------------
    def plot_WAIBAORI(self):
        """画外包日箭头"""
        # 检查是否有数据
        if len(self.KLINE_WAIBAORI)==0 :
            self.refresh()            
            return
        for arrow in self.KLINE_WAI_BAO_RI_arrows:
            self.pwKL.removeItem(arrow)    
        for i in range(len(self.KLINE_WAIBAORI)):
            if  self.KLINE_WAIBAORI[i] == 1:
                arrow = pg.ArrowItem(pos=(i, self.datas[i]['low']-100), size=7,tipAngle=55,tailLen=3,tailWidth=4, angle=90, brush=(255, 255, 0),pen=({'color': "FF0000", 'width': 1}))   
                self.pwKL.addItem(arrow)
                self.KLINE_WAI_BAO_RI_arrows.append(arrow)     
    #----------------------------------------------------------------------
    def plot_GJR_BUY(self):
        """画攻击日买入箭头"""
        # 检查是否有数据
        if len(self.KLINE_GJR_BUY)==0 :
            self.refresh()            
            return
        for arrow in self.KLINE_GJR_BUY_arrows:
            self.pwKL.removeItem(arrow)    
        for i in range(len(self.KLINE_GJR_BUY)):
            if  self.KLINE_GJR_BUY[i] == 1:
                arrow = pg.ArrowItem(pos=(i, self.datas[i]['low']-50), size=7,tipAngle=55,tailLen=3,tailWidth=4, angle=90, brush=("B03060"),pen=({'color': "B03060", 'width': 1}))   
                self.pwKL.addItem(arrow)
                self.KLINE_GJR_BUY_arrows.append(arrow)    
    #----------------------------------------------------------------------
    def plot_GJR_SELL(self):
        """画攻击日卖出箭头"""
        # 检查是否有数据
        if len(self.KLINE_GJR_SELL)==0 :
            self.refresh()            
            return
        for arrow in self.KLINE_GJR_SELL_arrows:
            self.pwKL.removeItem(arrow)    
        for i in range(len(self.KLINE_GJR_SELL)):
            if  self.KLINE_GJR_SELL[i] == 1:
                arrow = pg.ArrowItem(pos=(i, self.datas[i]['high']+50), size=7,tipAngle=55,tailLen=3,tailWidth=4, angle=-90, brush=("C0FF3E"),pen=({'color': "C0FF3E", 'width': 1}))   
                self.pwKL.addItem(arrow)
                self.KLINE_GJR_SELL_arrows.append(arrow)    
    #----------------------------------------------------------------------
    def plot_after_runStrategy(self):
        """执行策略之后，根据显示状态重画其他指标"""
        if self.KLINE_show ==True:
            self.KLINEOI_CLOSE.hide()  
        else:
            self.KLINEOI_CLOSE.show()   
            
        if self.MA_LONG_show ==True:
            self.MA_LONGOI.show() 
        else:
            self.MA_LONGOI.hide()          
            
        if self.MA_SHORT_show ==True:
            self.MA_SHORTOI.show() 
        else:
            self.MA_SHORTOI.hide()   
                               
        if not self.SHORT_TERM_SHOW_FIRST :
            for arrow in self.KLINE_SHORT_TERM_LIST_FIRST_arrows:
                arrow.show()  
            for curve in self.KLINE_SHORT_TERM_LIST_FIRST_curves:
                curve.show()
        else:
            for arrow in self.KLINE_SHORT_TERM_LIST_FIRST_arrows:
                arrow.hide()  
            for curve in self.KLINE_SHORT_TERM_LIST_FIRST_curves:
                curve.hide()       
                
        if not self.SHORT_TERM_SHOW_LIMIT :
            for arrow in self.KLINE_SHORT_TERM_LIST_LIMIT_arrows:
                arrow.show()  
            for curve in self.KLINE_SHORT_TERM_LIST_LIMIT_curves:
                curve.show()
        else:
            for arrow in self.KLINE_SHORT_TERM_LIST_LIMIT_arrows:
                arrow.hide()  
            for curve in self.KLINE_SHORT_TERM_LIST_LIMIT_curves:
                curve.hide()       
                
        if not self.SHORT_TERM_SHOW_ALL :
            for arrow in self.KLINE_SHORT_TERM_LIST_ALL_arrows:
                arrow.show()  
            for curve in self.KLINE_SHORT_TERM_LIST_ALL_curves:
                curve.show()
        else:
            for arrow in self.KLINE_SHORT_TERM_LIST_ALL_arrows:
                arrow.hide()  
            for curve in self.KLINE_SHORT_TERM_LIST_ALL_curves:
                curve.hide()       
    
    #----------------------------------------------------------------------
    def updateAll(self):
        """
        手动更新所有K线图形，K线播放模式下需要
        """
        datas = self.datas
        self.volume.pictrue = None
        self.candle.pictrue = None
        self.volume.update()
        self.candle.update()
        def update(view,low,high):
            vRange = view.viewRange()
            xmin = max(0,int(vRange[0][0]))
            xmax = max(0,int(vRange[0][1]))
            try:
                xmax = min(xmax,len(datas)-1)
            except:
                xmax = xmax
            if len(datas)>0 and xmax > xmin:
                ymin = min(datas[xmin:xmax][low])
                ymax = max(datas[xmin:xmax][high])
                view.setRange(yRange = (ymin,ymax))
            else:
                view.setRange(yRange = (0,1))
        update(self.pwKL.getViewBox(),'low','high')
        update(self.pwVol.getViewBox(),'volume','volume')

    #----------------------------------------------------------------------
    def plotAll(self,redraw=True,xMin=0,xMax=-1):
        """
        重画所有界面
        redraw ：False=重画最后一根K线; True=重画所有
        xMin,xMax : 数据范围
        """
        xMax = len(self.datas)-1 if xMax < 0 else xMax
        #self.countK = xMax-xMin
        #self.index = int((xMax+xMin)/2)
        self.pwOI.setLimits(xMin=xMin,xMax=xMax)
        self.pwKL.setLimits(xMin=xMin,xMax=xMax)
        self.pwVol.setLimits(xMin=xMin,xMax=xMax)
        self.plotKline(redraw,xMin,xMax)                       # K线图
        self.plot_startdate(self.start_date[1])
        self.plot_enddate(self.end_date[1])
        self.plotVol(redraw,xMin,xMax)                         # K线副图，成交量
        self.plotOI(0,len(self.datas))                         # K线副图，持仓量
        self.refresh()

    
    #----------------------------------------------------------------------
    def restart_program(self):
        python = sys.executable
        os.execl(python, python, * sys.argv)
            
    #----------------------------------------------------------------------
    def refresh(self):
        """
        刷新三个子图的现实范围
        """   
        datas   = self.datas
        minutes = int(self.countK/2)
        xmin    = max(0,self.index-minutes)
        try:
            xmax    = min(xmin+2*minutes,len(self.datas)-1) if self.datas else xmin+2*minutes
        except:
            xmax    = xmin+2*minutes
        self.pwOI.setRange(xRange = (xmin,xmax))
        self.pwKL.setRange(xRange = (xmin,xmax))
        self.pwVol.setRange(xRange = (xmin,xmax))

    #----------------------------------------------------------------------
    #  快捷键与鼠标相关 
    #----------------------------------------------------------------------
    def onNxt(self):
        """跳转到下一个开平仓点"""
        if len(self.listSig)>0 and not self.index is None:
            datalen = len(self.listSig)
            if self.index < datalen-2 : self.index+=1
            while self.index < datalen-2 and cmp(self.listSig_deal_DIRECTION[self.index] , '-')== 0:
                self.index+=1
            self.refresh()
            x = self.index
            y = self.datas[x]['close']
            self.crosshair.signal.emit((x,y))

    #----------------------------------------------------------------------
    def onPre(self):
        """跳转到上一个开平仓点"""
        if  len(self.listSig)>0 and not self.index is None:
            if self.index > 0: self.index-=1
            while self.index > 0 and cmp(self.listSig_deal_DIRECTION[self.index] , '-')== 0:
                self.index-=1
            self.refresh()
            x = self.index
            y = self.datas[x]['close']
            self.crosshair.signal.emit((x,y))

    #----------------------------------------------------------------------
    def onDown(self):
        """放大显示区间"""
        self.countK = min(len(self.datas),int(self.countK*1.2)+1)
        self.refresh()
        if len(self.datas)>0:
            x = self.index-self.countK/2+2 if int(self.crosshair.xAxis)<self.index-self.countK/2+2 else int(self.crosshair.xAxis)
            x = self.index+self.countK/2-2 if x>self.index+self.countK/2-2 else x
            x = len(self.datas)-1 if x > len(self.datas)-1 else int(x)
            y = self.datas[x][2]
            self.crosshair.signal.emit((x,y))

    #----------------------------------------------------------------------
    def onUp(self):
        """缩小显示区间"""
        self.countK = max(3,int(self.countK/1.2)-1)
        self.refresh()
        if len(self.datas)>0:
            x = self.index-self.countK/2+2 if int(self.crosshair.xAxis)<self.index-self.countK/2+2 else int(self.crosshair.xAxis)
            x = self.index+self.countK/2-2 if x>self.index+self.countK/2-2 else x
            x = len(self.datas)-1 if x > len(self.datas)-1 else int(x)
            y = self.datas[x]['close']
            self.crosshair.signal.emit((x,y))

    #----------------------------------------------------------------------
    def onLeft(self):
        """向左移动"""
        if len(self.datas)>0 and int(self.crosshair.xAxis)>2:
            x = int(self.crosshair.xAxis)-1
            x = len(self.datas)-1 if x > len(self.datas)-1 else int(x)
            y = self.datas[x]['close']
            if x <= self.index-self.countK/2+2 and self.index>1:
                self.index -= 1
                self.refresh()
            self.crosshair.signal.emit((x,y))

    #----------------------------------------------------------------------
    def onRight(self):
        """向右移动"""
        if len(self.datas)>0 and int(self.crosshair.xAxis)<len(self.datas)-1:
            x = int(self.crosshair.xAxis)+1
            x = len(self.datas)-1 if x > len(self.datas)-1 else int(x)
            y = self.datas[x]['close']
            if x >= self.index+int(self.countK/2)-2:
                self.index += 1
                self.refresh()
            self.crosshair.signal.emit((x,y))
    #----------------------------------------------------------------------
    def onRClick(self,pos):
        self.menu.showContextMenu(pos)
        
    #----------------------------------------------------------------------
    #  右键菜单相关 
    #----------------------------------------------------------------------              
    def initIndicator(self,data):
        if cmp(data,   u'信号隐藏') == 0 :
            for arrow in self.arrows:
                arrow.hide()
            for curve in self.curves:
                curve.hide()
            self.signal_show=False
            klinesettings= self.load_json_file(self.cur_jsonname)
            for setting in klinesettings:
                setting['SIGNALSHOW']= (self.signal_show)
            self.rewrite_json_file(klinesettings,self.cur_jsonname)
        elif cmp(data, u'信号显示') == 0 :
            for arrow in self.arrows:
                arrow.show()  
            for curve in self.curves:
                curve.show()
            self.signal_show=True
            klinesettings= self.load_json_file(self.cur_jsonname)
            for setting in klinesettings:
                setting['SIGNALSHOW']= (self.signal_show)
            self.rewrite_json_file(klinesettings,self.cur_jsonname)
        elif cmp(data, u'KLINE') == 0 :
            if self.KLINE_show ==True:
                self.pwKL.removeItem(self.candle)        
                self.KLINEOI_CLOSE.show()  
                self.KLINE_show = False   
            else:
                self.pwKL.addItem(self.candle)
                self.KLINEOI_CLOSE.hide()       
                self.KLINE_show=True
            klinesettings= self.load_json_file(self.cur_jsonname)
            for setting in klinesettings:                
                setting['KLINESHOW']= not(self.KLINE_show)
            self.rewrite_json_file(klinesettings,self.cur_jsonname)
        elif cmp(data, u'MA SHORT') == 0 :
            '''
            if len(self.MA_SHORT_real) == 0:             
                self.MA_SHORT_real = ta.MA(np.array(self.KLINE_CLOSE), timeperiod=self.MA_SHORT_DAY, matype=0).tolist()
                self.crosshair.ma_s_values = self.MA_SHORT_real 
                self.plotMA_SHORT()
            '''
            if len(self.MA_SHORT_real) == 0:      
                if self.HYNAME == 'RB9999':
                    MA_SHORT_DAY= self.RB_PARALIST[13]  
                elif self.HYNAME == 'J9999':
                    MA_SHORT_DAY= self.J_PARALIST[13]
                self.MA_SHORT_real = ta.MA(np.array(self.KLINE_CLOSE), timeperiod=MA_SHORT_DAY, matype=0).tolist()
                self.crosshair.ma_s_values = self.MA_SHORT_real 
                self.plotMA_SHORT()                                               
            if self.MA_SHORT_show :
                self.MA_SHORTOI.hide() 
                self.MA_SHORT_show =False
            else:
                self.MA_SHORTOI.show() 
                self.MA_SHORT_show =True
            klinesettings= self.load_json_file(self.cur_jsonname)
            for setting in klinesettings:
                setting['MA_SHORT_SHOW']= not(self.MA_SHORT_show)
            self.rewrite_json_file(klinesettings,self.cur_jsonname)
        elif cmp(data, u'MA LONG') == 0 :
            '''
            if len(self.MA_LONG_real) == 0:
                self.MA_LONG_real = ta.MA(np.array(self.KLINE_CLOSE), timeperiod=self.MA_LONG_DAY, matype=0).tolist()
                self.crosshair.ma_l_values = self.MA_LONG_real 
                self.plotMA_LONG()
            '''
            if len(self.MA_LONG_real) == 0:
                if self.HYNAME == 'RB9999':
                    MA_LONG_DAY  = self.RB_PARALIST[13]
                    MA_BEFORE_DAY= self.RB_PARALIST[12]
                elif self.HYNAME == 'J9999':
                    MA_LONG_DAY  = self.J_PARALIST[13]
                    MA_BEFORE_DAY= self.J_PARALIST[12]
                MA_LONG_real = ta.MA(np.array(self.KLINE_CLOSE), timeperiod=MA_LONG_DAY, matype=0).tolist()
                data1 = pd.DataFrame({'a': MA_LONG_real}) 
                self.MA_LONG_real = np.array(data1.shift(periods=MA_BEFORE_DAY,axis=0).a).tolist()  
                self.crosshair.ma_l_values =self.MA_LONG_real              
                self.plotMA_LONG()                               
            if self.MA_LONG_show :
                self.MA_LONGOI.hide() 
                self.MA_LONG_show =False
            else:
                self.MA_LONGOI.show() 
                self.MA_LONG_show =True
            klinesettings= self.load_json_file(self.cur_jsonname)
            for setting in klinesettings:
                setting['MA_LONG_SHOW']= not(self.MA_LONG_show)
            self.rewrite_json_file(klinesettings,self.cur_jsonname)
        elif cmp(data, u'设为起始日期') == 0 :
            if self.crosshair.cur_date()[1] < self.end_date[1]:
                self.plot_startdate(self.crosshair.cur_date()[1])
                self.start_date = self.crosshair.cur_date()
                klinesettings= self.load_json_file(self.cur_jsonname)
                for setting in klinesettings:
                    setting['STARTDAY']= self.start_date[0]
                    setting['STARTPOS']= self.start_date[1]
                self.rewrite_json_file(klinesettings,self.cur_jsonname)
        elif cmp(data, u'设为结束日期') == 0 :
            if self.crosshair.cur_date()[1] > self.start_date[1]:
                self.plot_enddate(self.crosshair.cur_date()[1])
                self.end_date = self.crosshair.cur_date()
                klinesettings= self.load_json_file(self.cur_jsonname)
                for setting in klinesettings:
                    setting['ENDDAY']= self.end_date[0]
                    setting['ENDPOS']= self.end_date[1]
                self.rewrite_json_file(klinesettings,self.cur_jsonname)
        elif cmp(data, u'MA_螺纹空_PLUS') == 0 :
            reload(DMARB)
            engine  = DMARB.calculateDailyResult_init(self.HYCAPITAL,self.HYSIZE) 
            initday = DMARB.get_strategy_init_days(engine)  
            if self.start_date[1] < initday:
                initday = 0 
            DMARB.calculateDailyResult_to_CSV(engine,dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[self.start_date[1]-initday]['datetime'],)),'%Y%m%d'),self.start_date[1],dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[self.end_date[1]]['datetime'],)),'%Y%m%d'),self.end_date[1],os.path.abspath('.\\'+self.dailyresult_path),self.HYNAME) 
            self.clearSigData()
            self.loadData_listsig(pd.DataFrame.from_csv(self.dailyresult_path))
            self.BP_signal='close'            
            self.plotMark()   
            self.plot_after_runStrategy()    
            
            self.MA_SHORT_DAY  = DMARB.get_strategy_SK_A_LONG(engine)    
            self.MA_SHORT_real = ta.MA(np.array(self.KLINE_CLOSE), timeperiod=self.MA_SHORT_DAY, matype=0).tolist()
            self.crosshair.ma_s_values = self.MA_SHORT_real 
            self.plotMA_SHORT()
            self.MA_SHORTOI.show() 
            self.MA_SHORT_show =True  
            
            self.MA_LONG_DAY  = DMARB.get_strategy_SK_E_LONG(engine)    
            self.MA_LONG_real = ta.MA(np.array(self.KLINE_CLOSE), timeperiod=self.MA_LONG_DAY, matype=0).tolist()
            self.crosshair.ma_l_values = self.MA_LONG_real 
            self.plotMA_LONG()
            self.MA_LONGOI.show() 
            self.MA_LONG_show =True  
                        
            self.KLtitle.setText(self.HYNAME+'   '+'MA_螺纹空_PLUS' ,size='10pt',color='g')
            klinesettings= self.load_json_file()
            for setting in klinesettings:
                setting['MA_SHORT_SHOW']= not(self.MA_SHORT_show)
                setting['StrategyName']= 'MA_螺纹空_PLUS'
            self.rewrite_json_file(klinesettings)  
        elif cmp(data, u'SHORT TERM(Limit)') == 0 :
            if len(self.KLINE_SHORT_TERM_LIST_LIMIT) ==0:
                self.short_term_list_Limit()
                self.plotIndex_LIMIT()
            if self.SHORT_TERM_SHOW_LIMIT :
                for arrow in self.KLINE_SHORT_TERM_LIST_LIMIT_arrows:
                    arrow.show()  
                for curve in self.KLINE_SHORT_TERM_LIST_LIMIT_curves:
                    curve.show()
                self.SHORT_TERM_SHOW_LIMIT =False
            else:
                for arrow in self.KLINE_SHORT_TERM_LIST_LIMIT_arrows:
                    arrow.hide()  
                for curve in self.KLINE_SHORT_TERM_LIST_LIMIT_curves:
                    curve.hide()
                self.SHORT_TERM_SHOW_LIMIT =True             
        elif cmp(data, u'SHORT TERM(First)') == 0 :
            if len(self.KLINE_SHORT_TERM_LIST_FIRST) ==0:
                self.short_term_list_First()
                self.plotIndex_FIRST()
                index_settings= self.load_First_Index_Setting()
                for setting in index_settings:                
                    setting['SHORT_TERM_INDEX']= self.KLINE_SHORT_TERM_LIST_FIRST
                self.rewrite_First_Index_json_file(index_settings)      
            if self.SHORT_TERM_SHOW_FIRST :
                for arrow in self.KLINE_SHORT_TERM_LIST_FIRST_arrows:
                    arrow.show()  
                for curve in self.KLINE_SHORT_TERM_LIST_FIRST_curves:
                    curve.show()
                self.SHORT_TERM_SHOW_FIRST =False
            else:
                for arrow in self.KLINE_SHORT_TERM_LIST_FIRST_arrows:
                    arrow.hide()  
                for curve in self.KLINE_SHORT_TERM_LIST_FIRST_curves:
                    curve.hide()
                self.SHORT_TERM_SHOW_FIRST =True             
        elif cmp(data, u'SHORT TERM(All)') == 0 :
            if len(self.KLINE_SHORT_TERM_LIST_ALL) ==0:
                self.short_term_list_All()
                self.plotIndex_ALL()          
                index_settings= self.load_All_Index_Setting()
                for setting in index_settings:                
                    setting['SHORT_TERM_INDEX']= self.KLINE_SHORT_TERM_LIST_ALL
                self.rewrite_All_Index_json_file(index_settings)   
            if self.SHORT_TERM_SHOW_ALL :
                for arrow in self.KLINE_SHORT_TERM_LIST_ALL_arrows:
                    arrow.show()  
                for curve in self.KLINE_SHORT_TERM_LIST_ALL_curves:
                    curve.show()
                self.SHORT_TERM_SHOW_ALL =False
            else:
                for arrow in self.KLINE_SHORT_TERM_LIST_ALL_arrows:
                    arrow.hide()  
                for curve in self.KLINE_SHORT_TERM_LIST_ALL_curves:
                    curve.hide()
                self.SHORT_TERM_SHOW_ALL =True              
        elif cmp(data, u'SHORTTERM_螺纹_多') == 0 :             
            reload(STRB)
            engine=STRB.calculateDailyResult_init(True,self.HYCAPITAL,self.HYSIZE)            
            initday = STRB.get_strategy_init_days(engine)  
            if self.start_date[1] < initday:
                initday = 0 
            STRB.calculateDailyResult_to_CSV(engine,dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[self.start_date[1]-initday]['datetime'],)),'%Y%m%d') ,self.start_date[1],dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[self.end_date[1]]['datetime'],)),'%Y%m%d') ,self.end_date[1],os.path.abspath('.\\'+self.dailyresult_path),self.HYNAME,self.HYSTARTDATE)
            
            self.clearSigData()
            self.loadData_listsig(pd.DataFrame.from_csv(self.dailyresult_path))
            self.SP_signal='close'            
            self.plotMark()   
            self.plot_after_runStrategy()    
            self.MA_SHORT_DAY  = STRB.get_strategy_E_LONG(engine)    
            self.MA_SHORT_real = ta.MA(np.array(self.KLINE_CLOSE), timeperiod=self.MA_SHORT_DAY, matype=0).tolist()
            self.crosshair.ma_s_values = self.MA_SHORT_real 
            self.plotMA_SHORT()
            self.MA_SHORTOI.show() 
            self.MA_SHORT_show =True     
            self.KLtitle.setText(self.HYNAME+'   '+'SHORTTERM_螺纹_多' ,size='10pt',color='FF0000')
            klinesettings= self.load_json_file()
            for setting in klinesettings:
                setting['MA_SHORT_SHOW']= not(self.MA_SHORT_show)
                setting['StrategyName']= 'SHORTTERM_螺纹_多'
            self.rewrite_json_file(klinesettings)         
    
        elif cmp(data, u'SHORTTERM_螺纹_空') == 0 :             
            reload(STRB)
            engine=STRB.calculateDailyResult_init(False,self.HYCAPITAL,self.HYSIZE)            
            initday = STRB.get_strategy_init_days(engine)  
            if self.start_date[1] < initday:
                initday = 0 
            STRB.calculateDailyResult_to_CSV(engine,dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[self.start_date[1]-initday]['datetime'],)),'%Y%m%d') ,self.start_date[1],dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[self.end_date[1]]['datetime'],)),'%Y%m%d') ,self.end_date[1],os.path.abspath('.\\'+self.dailyresult_path),self.HYNAME,self.HYSTARTDATE)
            
            self.clearSigData()
            self.loadData_listsig(pd.DataFrame.from_csv(self.dailyresult_path))
            self.BP_signal='close'
            self.plotMark()   
            self.plot_after_runStrategy()    
            self.MA_SHORT_DAY  = STRB.get_strategy_SK_E_LONG(engine)    
            self.MA_SHORT_real = ta.MA(np.array(self.KLINE_CLOSE), timeperiod=self.MA_SHORT_DAY, matype=0).tolist()
            self.crosshair.ma_s_values = self.MA_SHORT_real 
            self.plotMA_SHORT()
            self.MA_SHORTOI.show() 
            self.MA_SHORT_show =True     
            self.KLtitle.setText(self.HYNAME+'   '+'SHORTTERM_螺纹_空' ,size='10pt',color='00FF00')
            klinesettings= self.load_json_file()
            for setting in klinesettings:
                setting['MA_SHORT_SHOW']= not(self.MA_SHORT_show)
                setting['StrategyName']= 'SHORTTERM_螺纹_空'
            self.rewrite_json_file(klinesettings)   
        elif cmp(data, u'VOLATILITY_螺纹_多')==0:
            reload(VRB)
            engine=VRB.calculateDailyResult_init(True,True,self.HYCAPITAL,self.HYSIZE)            
            initday = VRB.get_strategy_init_days(engine)  
            if self.start_date[1] < initday:
                initday = 0 
            VRB.calculateDailyResult_to_CSV(engine,dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[self.start_date[1]-initday]['datetime'],)),'%Y%m%d') ,self.start_date[1],dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[self.end_date[1]]['datetime'],)),'%Y%m%d') ,self.end_date[1],os.path.abspath('.\\'+self.dailyresult_path),self.HYNAME,self.HYSTARTDATE)
            
            self.clearSigData()
            self.loadData_listsig(pd.DataFrame.from_csv(self.dailyresult_path))
            self.SP_signal='close'            
            self.plotMark()   
            self.plot_after_runStrategy()    
            self.MA_SHORTOI.hide()    
            self.KLtitle.setText(self.HYNAME+'   '+'VOLATILITY_螺纹_多' ,size='10pt',color='FF0000')
            klinesettings= self.load_json_file()
            for setting in klinesettings:
                setting['MA_SHORT_SHOW']= not(self.MA_SHORT_show)
                setting['StrategyName']= 'VOLATILITY_螺纹_多'
            self.rewrite_json_file(klinesettings)   
            self.MA_LONGOI.hide() 
            self.MA_SHORTOI.hide()       
        elif cmp(data, u'VOLATILITY_螺纹_空')==0:
            reload(VRB)
            engine=VRB.calculateDailyResult_init(True,False,self.HYCAPITAL,self.HYSIZE)            
            initday = VRB.get_strategy_init_days(engine)  
            if self.start_date[1] < initday:
                initday = 0 
            VRB.calculateDailyResult_to_CSV(engine,dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[self.start_date[1]-initday]['datetime'],)),'%Y%m%d') ,self.start_date[1],dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[self.end_date[1]]['datetime'],)),'%Y%m%d') ,self.end_date[1],os.path.abspath('.\\'+self.dailyresult_path),self.HYNAME,self.HYSTARTDATE)
            
            self.clearSigData()
            self.loadData_listsig(pd.DataFrame.from_csv(self.dailyresult_path))
            self.BP_signal='close'        
            self.plotMark()   
            self.plot_after_runStrategy()    
            self.MA_SHORTOI.hide()    
            self.KLtitle.setText(self.HYNAME+'   '+'VOLATILITY_螺纹_空' ,size='10pt',color='00FF00')
            klinesettings= self.load_json_file()
            for setting in klinesettings:
                setting['MA_SHORT_SHOW']= not(self.MA_SHORT_show)
                setting['StrategyName']= 'VOLATILITY_螺纹_空'
            self.rewrite_json_file(klinesettings)   
            self.MA_LONGOI.hide() 
            self.MA_SHORTOI.hide()  
        elif cmp(data, u'VOLATILITY_螺纹_V1')==0:
            reload(VRB1)
            #self.loadKLineSetting()
            self.set_start_and_end_pos(pd.DataFrame.from_csv(self.dailydata_path))
            PARALIST=[]
            if self.HYNAME == 'RB9999':
                PARALIST= self.RB_PARALIST  
            elif self.HYNAME == 'J9999':
                PARALIST= self.J_PARALIST  
            
            engine=VRB1.calculateDailyResult_init(True,self.HYCAPITAL,self.HYSIZE,PARALIST)            
            initday = VRB1.get_strategy_init_days(engine)  
            if self.start_date[1] < initday:
                initday = 0 
            VRB1.calculateDailyResult_to_CSV(engine,\
                                             dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[self.start_date[1]]['datetime'],)),'%Y%m%d') ,\
                                             self.start_date[1],\
                                             dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[self.end_date[1]]['datetime'],)),'%Y%m%d') ,\
                                             self.end_date[1],\
                                             os.path.abspath('.\\'+self.dailyresult_path),\
                                             self.HYNAME,\
                                             self.HYSTARTDATE)
            self.clearSigData()
            self.loadData_listsig(pd.DataFrame.from_csv(self.dailyresult_path))
            self.BP_signal='close'        
            self.plotMark()   
            self.plot_after_runStrategy()    
            self.MA_SHORTOI.show()    
            self.MA_LONGOI.show()  
            self.KLtitle.setText(self.HYNAME+'   '+'VOLATILITY_螺纹_V1' ,size='10pt',color='FFA500')
            klinesettings= self.load_json_file()
            for setting in klinesettings:
                setting['MA_SHORT_SHOW']= not(self.MA_SHORT_show)
                setting['MA_LONG_SHOW']= not(self.MA_LONG_show)
                setting['StrategyName']= 'VOLATILITY_螺纹_V1'
            self.rewrite_json_file(klinesettings)   
            #self.MA_LONGOI.hide() 
            #self.MA_SHORTOI.hide()     
        elif cmp(data, u'外包日')==0:
            if len(self.KLINE_WAIBAORI) == 0 :
                self.WAI_BAO_RI()
                self.plot_WAIBAORI()  
            if self.WAIBAORI_SHOW :
                for arrow in self.KLINE_WAI_BAO_RI_arrows:
                    arrow.show()  
                self.WAIBAORI_SHOW =False
            else:
                for arrow in self.KLINE_WAI_BAO_RI_arrows:
                    arrow.hide()  
                self.WAIBAORI_SHOW =True       
            pass
        elif cmp(data, u'攻击日（买入）')==0:
            if len(self.KLINE_GJR_BUY) == 0 :
                self.GJR_BUY()
                self.plot_GJR_BUY()
            if self.GJRBUY_SHOW:
                for arrow in self.KLINE_GJR_BUY_arrows:
                    arrow.show()  
                self.GJRBUY_SHOW =False
            else:
                for arrow in self.KLINE_GJR_BUY_arrows:
                    arrow.hide()  
                self.GJRBUY_SHOW =True    
            pass
        elif cmp(data, u'攻击日（卖出）')==0:
            if len(self.KLINE_GJR_SELL) == 0 :
                self.GJR_SELL()
                self.plot_GJR_SELL()
            if self.GJRSELL_SHOW:
                for arrow in self.KLINE_GJR_SELL_arrows:
                    arrow.show()  
                self.GJRSELL_SHOW =False
            else:
                for arrow in self.KLINE_GJR_SELL_arrows:
                    arrow.hide()  
                self.GJRSELL_SHOW =True    
            pass
    
        elif cmp(data, u'外包日_螺纹_多')==0:
            reload(WBDRB)
            engine=WBDRB.calculateDailyResult_init(True,False)            
            initday = WBDRB.get_strategy_init_days(engine)  
            if self.start_date[1] < initday:
                initday = 0 
            WBDRB.calculateDailyResult_to_CSV(engine,\
                                            dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[self.start_date[1]-initday]['datetime'],)),'%Y%m%d') ,\
                                            self.start_date[1],\
                                            dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[self.end_date[1]]['datetime'],)),'%Y%m%d') ,\
                                            self.end_date[1],\
                                            os.path.abspath('.\\'+self.dailyresult_path),self.HYNAME)
            
            self.clearSigData()
            self.loadData_listsig(pd.DataFrame.from_csv(self.dailyresult_path))
            self.BP_signal='close'        
            self.plotMark()   
            self.plot_after_runStrategy()    
            self.MA_SHORTOI.hide()    
            self.KLtitle.setText(self.HYNAME+'   '+'外包日_螺纹_多' ,size='10pt',color='FF0000')
            klinesettings= self.load_json_file()
            for setting in klinesettings:
                setting['MA_SHORT_SHOW']= not(self.MA_SHORT_show)
                setting['StrategyName']= '外包日_螺纹_多'
            self.rewrite_json_file(klinesettings)   
            self.MA_LONGOI.hide() 
            self.MA_SHORTOI.hide()  
        elif cmp(data, u'RB9999')==0:
            klinesettings= self.load_json_file()
            for setting in klinesettings:
                setting['HYNAME']= 'RB9999'
                setting['HYSTARTDATE']= '20090327'
                setting['HYCAPITAL']= 30000
                setting['HYSIZE']= 10
                setting[u'RB_PARALIST']=[1400,0.7,0.9,1,1,500,1050,0.3,0.9,1,1,1000,365,20,0,0,0,0,0,0]
            self.rewrite_json_file(klinesettings)   
            self.restart_program()
        elif cmp(data, u'CU9999')==0:
            klinesettings= self.load_json_file()
            for setting in klinesettings:
                setting['HYNAME']= 'CU9999'
                setting['HYSTARTDATE']= '19960402'
                setting['HYCAPITAL']= 200000
                setting['HYSIZE']= 5
                para1=int(1400*(setting['HYCAPITAL']/30000.0))
                para2=int(500*(setting['HYCAPITAL']/30000.0))
                para3=int(1050*(setting['HYCAPITAL']/30000.0))
                para4=int(1000*(setting['HYCAPITAL']/30000.0))                
                setting[u'PARALIST']=[para1,0.7,0.9,1,1,para2,para3,0.3,0.9,1,1,para4,30,3,0,0,0,0,0,0]               
            self.rewrite_json_file(klinesettings)  
            self.restart_program()
        elif cmp(data, u'CF9999')==0:
            klinesettings= self.load_json_file()
            for setting in klinesettings:
                setting['HYNAME']= 'CF9999'
                setting['HYSTARTDATE']= '20040601'
                setting['HYCAPITAL']= 57000
                setting['HYSIZE']= 5
                para1=int(1400*(setting['HYCAPITAL']/30000.0))
                para2=int(500*(setting['HYCAPITAL']/30000.0))
                para3=int(1050*(setting['HYCAPITAL']/30000.0))
                para4=int(1000*(setting['HYCAPITAL']/30000.0))
                setting[u'PARALIST']=[para1,0.7,0.9,1,1,para2,para3,0.3,0.9,1,1,para4,365,20,0,0,0,0,0,0]    
            self.rewrite_json_file(klinesettings)  
            self.restart_program()
        elif cmp(data, u'C9999')==0:
            klinesettings= self.load_json_file()
            for setting in klinesettings:
                setting['HYNAME']= 'C9999'
                setting['HYSTARTDATE']= '20040922'
                setting['HYCAPITAL']= 12000
                setting['HYSIZE']= 10
                para1=int(1400*(setting['HYCAPITAL']/30000.0))
                para2=int(500*(setting['HYCAPITAL']/30000.0))
                para3=int(1050*(setting['HYCAPITAL']/30000.0))
                para4=int(1000*(setting['HYCAPITAL']/30000.0))
                setting[u'PARALIST']=[para1,0.7,0.9,1,1,para2,para3,0.3,0.9,1,1,para4,365,20,0,0,0,0,0,0]     
            self.rewrite_json_file(klinesettings)  
            self.restart_program()
        elif cmp(data, u'J9999')==0:
            klinesettings= self.load_json_file()
            for setting in klinesettings:
                setting['HYNAME']= 'J9999'
                setting['HYSTARTDATE']= '20110415'
                setting['HYCAPITAL']= 190000
                setting['HYSIZE']= 100
                para1=int(1400*(setting['HYCAPITAL']/30000.0))
                para2=int(500*(setting['HYCAPITAL']/30000.0))
                para3=int(1050*(setting['HYCAPITAL']/30000.0))
                para4=int(1000*(setting['HYCAPITAL']/30000.0))
                setting[u'J_PARALIST']=[para1,0.7,0.9,1,1,para2,para3,0.3,0.9,1,1,para4,365,20,0,0,0,0,0,0]     
            self.rewrite_json_file(klinesettings)  
            self.restart_program()
    
    #----------------------------------------------------------------------
    #  界面回调相关
    #----------------------------------------------------------------------
    def onPaint(self):
        """界面刷新回调"""
        view = self.pwKL.getViewBox()
        vRange = view.viewRange()
        xmin = max(0,int(vRange[0][0]))
        xmax = max(0,int(vRange[0][1]))
        self.index  = int((xmin+xmax)/2)+1

    #----------------------------------------------------------------------
    def resignData(self,datas):
        """更新数据，用于Y坐标自适应"""
        self.crosshair.datas = datas
        def viewXRangeChanged(low,high,self):
            vRange = self.viewRange()
            xmin = max(0,int(vRange[0][0]))
            xmax = max(0,int(vRange[0][1]))
            xmax = min(xmax,len(datas))
            if len(datas)>0 and xmax > xmin:
                ymin = min(datas[xmin:xmax][low])
                ymax = max(datas[xmin:xmax][high])
                ymin,ymax = (-1,1) if ymin==ymax else (ymin,ymax)
                self.setRange(yRange = (ymin,ymax))
            else:
                self.setRange(yRange = (0,1))

        view = self.pwKL.getViewBox()
        view.sigXRangeChanged.connect(partial(viewXRangeChanged,'low','high'))

        view = self.pwVol.getViewBox()
        view.sigXRangeChanged.connect(partial(viewXRangeChanged,'volume','volume'))

        view = self.pwOI.getViewBox()
        view.sigXRangeChanged.connect(partial(viewXRangeChanged,'openInterest','openInterest'))

    #----------------------------------------------------------------------
    #  数据相关
    #----------------------------------------------------------------------
    def clearData(self):
        """清空数据"""
        # 清空数据，重新画图
        '''
        self.time_index = []
        self.listBar = []
        self.listVol = []
        self.listLow = []
        self.listHigh = []
        self.listOpenInterest = []
        self.listSig = []
        self.listSig_deal_DIRECTION  = []
        self.listSig_deal_OFFSET = []
        self.sigData = {}
        self.datas = None
        self.MA_SHORT_real=[]
        self.MA_LONG_real=[]
        self.start_time=[]    
        '''
        self.listBar  = []
        self.listVol  = []
        self.listHigh = []
        self.listLow  = []
        self.KLINE_DATE = []
        self. KLINE_OPEN = []
        self.KLINE_HIGH = []
        self.KLINE_LOW = []
        self.KLINE_SHORT_TERM_LOW = []
        self.KLINE_SHORT_TERM_HIGH = []
        self.KLINE_SHORT_TERM_LIST_ALL=[]
        self.KLINE_SHORT_TERM_LIST_FIRST=[]
        self.KLINE_SHORT_TERM_LIST_LIMIT=[]
        self.listClose  = []
        self.listSig  = []
        self.listOpenInterest = []
        self.arrows   = []
        self.KLINE_SHORT_TERM_LIST_ALL_arrows = []
        self.KLINE_SHORT_TERM_LIST_FIRST_arrows = []
        self.KLINE_SHORT_TERM_LIST_LIMIT_arrows = []
        self.curves   = []
        self.KLINE_SHORT_TERM_LIST_ALL_curves = []
        self.KLINE_SHORT_TERM_LIST_FIRST_curves = []
        self.KLINE_SHORT_TERM_LIST_LIMIT_curves = []
        self.listSig_deal_DIRECTION  = []
        self.listSig_deal_OFFSET = []
        self.KLINE_CLOSE=[]
        self.MA_SHORT_real=[]
        self.MA_LONG_real=[]
        #self.start_date=[] #[20090327开始日期，列表的位置]
        #self.end_date=[]   #[20181127结束日期，结束的位置]   
        
    #----------------------------------------------------------------------
    def clearSigData(self):
        """清空信号数据"""
        # 清空数据，重新画图
        self.listSig_deal_DIRECTION  = []
        self.listSig_deal_OFFSET = []
        for arrow in self.arrows:
            self.pwKL.removeItem(arrow)
        for curve in self.curves:
            self.pwKL.removeItem(curve)        
        self.arrows   = []
        self.curves   = []        
    #----------------------------------------------------------------------
    def clearIndexData(self):
        """清除索引数据"""
        for arrow in self.KLINE_SHORT_TERM_LIST_ALL_arrows:
            self.pwKL.removeItem(arrow)
        for arrow in self.KLINE_SHORT_TERM_LIST_FIRST_arrows:
            self.pwKL.removeItem(arrow)
        for arrow in self.KLINE_SHORT_TERM_LIST_LIMIT_arrows:
            self.pwKL.removeItem(arrow)
        for arrow in self.KLINE_WAI_BAO_RI_arrows:
            self.pwKL.removeItem(arrow)
        for arrow in self.KLINE_GJR_BUY_arrows:
            self.pwKL.removeItem(arrow)
        for curve in self.KLINE_SHORT_TERM_LIST_ALL_curves:
            self.pwKL.removeItem(curve)    
        for curve in self.KLINE_SHORT_TERM_LIST_FIRST_curves:
            self.pwKL.removeItem(curve)  
        for curve in self.KLINE_SHORT_TERM_LIST_LIMIT_curves:
            self.pwKL.removeItem(curve)   
        self.KLINE_SHORT_TERM_LIST_ALL_arrows=[]
        self.KLINE_SHORT_TERM_LIST_FIRST_arrows=[]
        self.KLINE_SHORT_TERM_LIST_LIMIT_arrows=[]
        self.KLINE_WAI_BAO_RI_arrows=[]
        self.KLINE_GJR_BUY_arrows=[]
        self.KLINE_SHORT_TERM_LIST_ALL_curves=[]
        self.KLINE_SHORT_TERM_LIST_FIRST_curves=[]
        self.KLINE_SHORT_TERM_LIST_LIMIT_curves=[]
        self.KLINE_SHORT_TERM_LIST_ALL=[]
        self.KLINE_SHORT_TERM_LIST_FIRST=[]
        self.KLINE_SHORT_TERM_LIST_LIMIT=[]
        
    #----------------------------------------------------------------------
    def clearSig(self,main=True):
        """清空信号图形"""
        # 清空信号图
        if main:
            for sig in self.sigPlots:
                self.pwKL.removeItem(self.sigPlots[sig])
            self.sigData  = {}
            self.sigPlots = {}
        else:
            for sig in self.subSigPlots:
                self.pwOI.removeItem(self.subSigPlots[sig])
            self.subSigData  = {}
            self.subSigPlots = {}

    #----------------------------------------------------------------------
    def updateSig(self,sig):
        """刷新买卖信号"""
        self.listSig = sig
        self.plotMark()

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """
        新增K线数据,K线播放模式
        """
        # 是否需要更新K线
        newBar = False if len(self.datas)>0 and bar.datetime==self.datas[-1].datetime else True
        nrecords = len(self.datas) if newBar else len(self.datas)-1
        bar.openInterest = np.random.randint(0,3) if bar.openInterest==np.inf or bar.openInterest==-np.inf else bar.openInterest
        recordVol = (nrecords,abs(bar.volume),0,0,abs(bar.volume)) if bar.close < bar.open else (nrecords,0,abs(bar.volume),0,abs(bar.volume))

        if newBar and any(self.datas):
            self.datas.resize(nrecords+1,refcheck=0)
            self.listBar.resize(nrecords+1,refcheck=0)
            self.listVol.resize(nrecords+1,refcheck=0)
        elif any(self.datas):
            self.listLow.pop()
            self.listHigh.pop()
            self.listOpenInterest.pop()
        if any(self.datas):
            self.datas[-1]   = (bar.datetime, bar.open, bar.close, bar.low, bar.high, bar.volume, bar.openInterest)
            self.listBar[-1] = (nrecords, bar.open, bar.close, bar.low, bar.high)
            self.listVol[-1] = recordVol
        else:
            self.datas     = np.rec.array([(bar.datetime, bar.open, bar.close, bar.low, bar.high, bar.volume, bar.openInterest)],\
                                        names=('datetime','open','close','low','high','volume','openInterest'))
            self.listBar   = np.rec.array([(nrecords, bar.open, bar.close, bar.low, bar.high)],\
                                     names=('time_int','open','close','low','high'))
            self.listVol   = np.rec.array([recordVol],names=('time_int','open','close','low','high'))
            self.resignData(self.datas)

        self.axisTime.update_xdict({nrecords:bar.datetime})
        self.listLow.append(bar.low)
        self.listHigh.append(bar.high)
        self.listOpenInterest.append(bar.openInterest)
        self.resignData(self.datas)
        return newBar

    #----------------------------------------------------------------------
    def loadData(self, datas, sigs = None):
        """
        载入pandas.DataFrame数据
        datas : 数据格式，cols : datetime, open, close, low, high
        """
        # 设置中心点时间
        # 绑定数据，更新横坐标映射，更新Y轴自适应函数，更新十字光标映射
        datas['time_int'] = np.array(range(len(datas.index)))
        
        
        self.datas = datas[['open','close','low','high','volume','openInterest']].to_records()
        self.axisTime.xdict={}
        xdict = dict(enumerate(datas.index.tolist()))
        self.axisTime.update_xdict(xdict)
        self.resignData(self.datas)
        # 更新画图用到的数据
        self.listBar          = datas[['time_int','open','close','low','high']].to_records(False)
        self.listHigh         = list(datas['high'])
        self.listLow          = list(datas['low'])
        self.listOpenInterest = list(datas['openInterest'])
        self.listSig          = [0]*(len(self.datas)-1) if sigs is None else sigs
    
        self.KLINE_CLOSE = map(float, list(datas['close']))
        self.KLINE_OPEN = map(float, list(datas['open']))
        self.KLINE_HIGH = map(float, list(datas['high']))
        self.KLINE_LOW = map(float, list(datas['low']))
        self.KLINE_DATE = map(str, list(datas.index))
        #self.start_date  = [dt.datetime.strftime(pd.to_datetime(pd.to_datetime(self.datas[0]['datetime'])),'%Y%m%d') ,0]
        # 成交量颜色和涨跌同步，K线方向由涨跌决定
        datas0                = pd.DataFrame()
        datas0['open']        = datas.apply(lambda x:0 if x['close'] >= x['open'] else x['volume'],axis=1)  
        datas0['close']       = datas.apply(lambda x:0 if x['close'] <  x['open'] else x['volume'],axis=1) 
        datas0['low']         = 0
        datas0['high']        = datas['volume']
        datas0['time_int']    = np.array(range(len(datas.index)))
        self.listVol          = datas0[['time_int','open','close','low','high']].to_records(False)
    #----------------------------------------------------------------------
    def loadData_listsig(self, datas):    
        datas['deal_DIRECTION']=datas['deal_DIRECTION'].fillna('-')
        datas['deal_OFFSET']=datas['deal_OFFSET'].fillna('-')
        self.listSig_deal_DIRECTION  = datas['deal_DIRECTION'].tolist()
        if len(self.listSig_deal_DIRECTION) < len(self.KLINE_CLOSE):
            list1 = ['-' for i in range(len(self.KLINE_CLOSE)- len(self.listSig_deal_DIRECTION))]
            list1.extend(self.listSig_deal_DIRECTION)
            self.listSig_deal_DIRECTION = list1      
        self.listSig_deal_OFFSET = datas['deal_OFFSET'].tolist() 
        if len(self.listSig_deal_OFFSET) < len(self.KLINE_CLOSE):
            list1 = ['-' for i in range(len(self.KLINE_CLOSE)- len(self.listSig_deal_OFFSET))]
            list1.extend(self.listSig_deal_OFFSET)
            self.listSig_deal_OFFSET = list1
    #----------------------------------------------------------------------
    def refreshAll(self, redraw=True, update=False):
        """
        更新所有界面
        """
        # 调用画图函数
        self.index = len(self.datas)
        self.plotAll(redraw,0,len(self.datas))
        if not update:
            self.updateAll()
        self.crosshair.signal.emit((None,None))
    #----------------------------------------------------------------------
    def loadKLineSetting(self,jsonname=u'json\\uiKLine_startpara.json'):
        """"""
        try:
            with open(jsonname) as f:
                initsettings= json.load(f)
                f.close()
                self.start_date=[]
                for setting in initsettings:
                    self.start_date.append(setting[u'STARTDAY'])
                    #self.start_date.append(setting[u'STARTPOS'])
                    self.end_date.append(setting[u'ENDDAY'])
                    #self.end_date.append(setting[u'ENDPOS'])
                    self.MA_LONG_DAY        = setting[u'MA_LONG_DAY']
                    self.MA_SHORT_DAY       = setting[u'MA_SHORT_DAY']
                    self.MA_SHORT_show= setting[u'MA_SHORT_SHOW']
                    self.MA_LONG_show= setting[u'MA_LONG_SHOW']     
                    self.KLINE_show= setting[u'KLINESHOW']   
                    self.signal_show = setting[u'SIGNALSHOW']  
                    self.SHORT_TERM_SHOW_FIRST = setting[u'SHORT_TERM_SHOW_FIRST']  
                    self.WAIBAORI_SHOW = setting[u'WAIBAORI_SHOW']  
                    self.GJRBUY_SHOW = setting[u'GJRBUY_SHOW']  
                    self.GJRSELL_SHOW = setting[u'GJRSELL_SHOW']  
                    self.StrategyName    =setting[u'StrategyName']
                    self.HYNAME          =setting[u'HYNAME']
                    self.HYSTARTDATE     =setting[u'HYSTARTDATE']
                    self.HYCAPITAL       =setting[u'HYCAPITAL']
                    self.HYSIZE       =setting[u'HYSIZE']
                    self.RB_PARALIST=setting[u'RB_PARALIST']
                    self.J_PARALIST=setting[u'J_PARALIST']
                    self.dailyresult_path = "data\dailyresult\%s.csv" %(self.HYNAME)
                    self.dailydata_path = "data\dailydata\%s.csv" %(self.HYNAME)
        except :
            f.close()
            self.start_date.append("20090327")
            self.start_date.append(0)
            self.start_date.append("20090330")
            self.start_date.append(1)
            self.MA_LONG_DAY        = 22
            self.MA_SHORT_DAY       = 92
            self.MA_SHORT_show= True
            self.MA_LONG_show = True    
            self.KLINE_show= True
            self.signal_show=True
            self.WAIBAIRI_SHOW=True
            self.GJRBUY_SHOW=True
            self.GJRSELL_SHOW=True
            self.SHORT_TERM_SHOW_FIRST=True
            self.StrategyName    ='None'
            self.HYNAME          ='RB9999'
            self.HYSTARTDATE     ='00000000'
            self.HYCAPITAL       =100000
            self.HYSIZE          =10
            self.HY_BK_A_LOSS_SP       =0
            self.HY_BK_A_FLAOT_PROFIT_ALL       =0
            self.HY_SK_A_LOSS_SP       =0
            self.HY_SK_A_FLAOT_PROFIT_ALL       =0         
            self.RB_PARALIST=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            self.J_PARALIST=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            print "Error: josn没有找到文件或读取文件失败"        
        
    #----------------------------------------------------------------------
    def set_start_and_end_pos(self,datas):
        """根据开始与结束日期设置pos"""
        
        datas['time_int'] = np.array(range(len(datas.index)))
        #print (datas[(datas.index=="20201111")]['time_int'])
        #print (datas[(datas.index=="20190402")]['time_int'])
        if len(datas[(datas.index==self.start_date[0])]['time_int']) > 0:
            self.start_date.append(datas[(datas.index==self.start_date[0])]['time_int'][0])            
        else:
            self.start_date.append(0)
            
        if len(datas[(datas.index==self.end_date[0])]['time_int']) > 0:
            self.end_date.append(datas[(datas.index==self.end_date[0])]['time_int'][0])
        else:
            self.end_date.append(len(datas.index)-1)
        
                  
        
    #----------------------------------------------------------------------
    def rewrite_json_file(self,json_data,jsonname= u'json\\uiKLine_startpara.json'):
        with open(jsonname, 'w') as f:
            json.dump(json_data,f,indent=2)
        f.close()
    #----------------------------------------------------------------------
    def load_json_file(self,jsonname=u'json\\uiKLine_startpara.json'):
        try:
            with open(jsonname) as f:
                initsettings= json.load(f)
                f.close()      
        except:
            f.close()
            josndata = [ { u'STARTDAY' : '20090327', u'STARTPOS' : 0,u'STARTDAY' : '20090330', u'STARTPOS' : 1, u'MA_LONG_DAY' : 92, u'MA_SHORT_DAY' : 22, u'MA_SHORT_SHOW' : True,u'MA_LONG_SHOW':True,u'KLINESHOW':True,u'SIGNALSHOW':True,u'SHORT_TERM_SHOW_FIRST':True,'WAIBAORI_SHOW':True,'GJRBUY_SHOW':True,'GJRSELL_SHOW':True,u'StrategyName':'None',u'StrategyName':'RB9999',u'HYSTARTDATE':'00000000',u'HYSTARTDATE':100000,u'HYSIZE':10,\
                           u'RB_PARALIST':[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],u'J_PARALIST':[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]} ]                                            
            self.rewrite_json_file(josndata)
            with open(u'json\\uiKLine_startpara.json') as f:
                initsettings= json.load(f)
            f.close()               
        return initsettings
    #----------------------------------------------------------------------
    def load_First_Index_Setting(self):
        """把相关指标从json文件读取"""
        try:
            with open(u'json\\uiKLine_first_index.json') as f:
                index_settings= json.load(f)
                f.close()      
        except:
            f.close()
            josndata = [ { u'SHORT_TERM_INDEX' : [0,0]} ]
            self.rewrite_Index_json_file(josndata)
            with open(u'json\\uiKLine_first_index.json') as f:
                initsettings= json.load(f)
            f.close()               
        return index_settings
    
    def load_All_Index_Setting(self):
        """把相关指标从json文件读取"""
        try:
            with open(u'json\\uiKLine_all_index.json') as f:
                index_settings= json.load(f)
                f.close()      
        except:
            f.close()
            josndata = [ { u'SHORT_TERM_INDEX' : [0,0]} ]
            self.rewrite_Index_json_file(josndata)
            with open(u'json\\uiKLine_all_index.json') as f:
                initsettings= json.load(f)
            f.close()               
        return index_settings
    #----------------------------------------------------------------------
    def rewrite_First_Index_json_file(self,json_data):
        """把相关指标写入json文件"""
        with open(u'json\\uiKLine_first_index.json', 'w') as f:
            json.dump(json_data,f)
        f.close()
    def rewrite_All_Index_json_file(self,json_data):
        """把相关指标写入json文件"""
        with open(u'json\\uiKLine_all_index.json', 'w') as f:
            json.dump(json_data,f)
        f.close()
    #----------------------------------------------------------------------
    #  指标计算 
    #----------------------------------------------------------------------        
    #----------------------------------------------------------------------
    def calculate_low(self,kline_value):
        """计算低点"""
        '''伪代码
        xb = np.array([0,5,6,7,4,5,1,2,8,1])  # 原始              三个值的第1个
        xm = np.array([5,6,7,4,5,1,2,8,1,0])  # 左移一位后面补0    三个值的第2个
        xa = np.array([6,7,4,5,1,2,8,1,0,0]   # 左移二位后面补0    三个值的第3个
        result =      [F,F,F,T,F,T,F,F,F,F]   # result = np.logical_and(xm<xb,xm<xa)
        result =      [F,F,F,F,T,F,T,F,F,F,F] # result=np.insert(result,0,False) 
        result =      [F,F,F,F,T,F,T,F,F,F]   # result=np.delete(result,result.shape[0]-1) 
        
        '''  
        v_b = np.array(kline_value)         
        v_m = np.delete(v_b,0) 
        v_m = np.insert(v_m,v_m.shape[0],0) 
        v_a = np.delete(v_b,0)
        v_a = np.delete(v_a,0)
        v_a = np.insert(v_a,v_a.shape[0],0)   
        v_a = np.insert(v_a,v_a.shape[0],0)   
     
        result = np.logical_and(v_m<v_b,v_m<v_a)
        result=np.insert(result,0,False) 
        result=np.delete(result,result.shape[0]-1)   
        result[0]=False
        result[result.shape[0]-1]=False
        return result             
    #----------------------------------------------------------------------
    def calculate_high(self,kline_value):
        """计算高点"""
        '''伪代码
        xb = np.array([9,5,6,7,4,5,1,2,3,4])  # 原始              三个值的第1个
        xm = np.array([5,6,7,4,5,1,2,3,4,0])  # 左移一位后面补0    三个值的第2个
        xa = np.array([6,7,4,5,1,2,3,4,0,0])  # 左移二位后面补0    三个值的第3个
        result =      [F,F,T,F,T,F,F,F,T,F]   # result = np.logical_and(xm<xb,xm<xa)
                      [Y,Y,Y,Y,Y,Y,Y,Y,N,N]   # Y=有用 N=没用
        result =      [F,F,F,T,F,T,F,F,F,T,F] # result=np.insert(result,0,False) 
                      [N,Y,Y,Y,Y,Y,Y,Y,Y,N,N] # Y=有用 N=没用
        result =      [F,F,F,T,F,T,F,F,F,T]   # result=np.delete(result,result.shape[0]-1)  
                      [N,Y,Y,Y,Y,Y,Y,Y,Y,N]   # Y=有用 N=没用
        '''  
        v_b = np.array(kline_value)         
        v_m = np.delete(v_b,0) 
        v_m = np.insert(v_m,v_m.shape[0],0) 
        v_a = np.delete(v_b,0)
        v_a = np.delete(v_a,0)
        v_a = np.insert(v_a,v_a.shape[0],0)   
        v_a = np.insert(v_a,v_a.shape[0],0)   
        

        result = np.logical_and(v_m>v_b,v_m>v_a)
        result=np.insert(result,0,False) 
        result=np.delete(result,result.shape[0]-1) 
        result[0]=False
        result[result.shape[0]-1]=False
        return result     
    #----------------------------------------------------------------------        
    def short_term_low(self,kline_value_low,kline_value_high):
        '''短期低点'''      
        r_low= self.calculate_low(kline_value_low)
        r_high= self.calculate_low(kline_value_high)
        r = np.logical_and(r_low,r_high)  
        return r
    #----------------------------------------------------------------------        
    def short_term_high(self,kline_value_low,kline_value_high):
        '''短期高点'''      
        r_low= self.calculate_high(kline_value_low)
        r_high= self.calculate_high(kline_value_high)
        r = np.logical_and(r_low,r_high) 
        return r
    #----------------------------------------------------------------------  
    def short_term_list_Limit(self):
        '''短期低点列表 --- 选择连续点的最大和最小值'''
        self.KLINE_SHORT_TERM_LOW = self.short_term_low(self.KLINE_LOW,self.KLINE_HIGH)    
        self.KLINE_SHORT_TERM_HIGH = self.short_term_high(self.KLINE_LOW,self.KLINE_HIGH)     
        
        self.KLINE_SHORT_TERM_LOW = [1 if i==True else 0 for i in self.KLINE_SHORT_TERM_LOW] #[1= 低点 0=普通点]
        self.KLINE_SHORT_TERM_HIGH =[2 if i==True else 0 for i in self.KLINE_SHORT_TERM_HIGH]#[2= 高点 0=普通点]
        self.KLINE_SHORT_TERM_LIST_LIMIT = (np.array(self.KLINE_SHORT_TERM_LOW) + np.array(self.KLINE_SHORT_TERM_HIGH)).tolist()     
        lowmin_time_int = -1 
        lowmin          = -1
        highmax_time_int = -1 
        highmax          = -1    
        for i in range(0,len(self.KLINE_SHORT_TERM_LIST_LIMIT)):
            #1 获得当前点
            if self.KLINE_SHORT_TERM_LIST_LIMIT[i] ==  1 or self.KLINE_SHORT_TERM_LIST_LIMIT[i] ==  2:
                if   self.KLINE_SHORT_TERM_LIST_LIMIT[i] ==  1:
                    lowmin          = self.KLINE_LOW[i] 
                    lowmin_time_int = i
                elif self.KLINE_SHORT_TERM_LIST_LIMIT[i] ==  2:
                    highmax          = self.KLINE_HIGH[i] 
                    highmax_time_int = i
                #2 判断当前点是高或者低
                for j in range(i+1,len(self.KLINE_SHORT_TERM_LIST_LIMIT)):
                    #3 从当前点出发向后查找，需要知道下一个的高低点是不是同类型 
                    #->是同类型，则注重点放到最大值或者最小值上
                    #  和最大值比较 比最大值小置0，比最大值大把最大值置0
                    #  和最小值比较 同理
                    #->不是同类型，要遵循高点大于低点，低点小于高低的原则 不满足置0
                    if   self.KLINE_SHORT_TERM_LIST_LIMIT[j] ==  1 and self.KLINE_SHORT_TERM_LIST_LIMIT[i] == self.KLINE_SHORT_TERM_LIST_LIMIT[j]:
                        if self.KLINE_LOW[j] < lowmin:
                            self.KLINE_SHORT_TERM_LIST_LIMIT[lowmin_time_int]=0
                            lowmin = self.KLINE_LOW[j] 
                            lowmin_time_int = j
                        else:
                            self.KLINE_SHORT_TERM_LIST_LIMIT[j] = 0  
                    elif self.KLINE_SHORT_TERM_LIST_LIMIT[j] ==  2 and self.KLINE_SHORT_TERM_LIST_LIMIT[i] == self.KLINE_SHORT_TERM_LIST_LIMIT[j]:
                        if self.KLINE_HIGH[j] > highmax:
                            self.KLINE_SHORT_TERM_LIST_LIMIT[highmax_time_int]=0
                            highmax = self.KLINE_LOW[j] 
                            highmax_time_int = j
                        else:
                            self.KLINE_SHORT_TERM_LIST_LIMIT[j] = 0                         
                    if self.KLINE_SHORT_TERM_LIST_LIMIT[j] !=  0 and self.KLINE_SHORT_TERM_LIST_LIMIT[i] != self.KLINE_SHORT_TERM_LIST_LIMIT[j]:
                        if (self.KLINE_SHORT_TERM_LIST_LIMIT[i] == 1 and self.KLINE_LOW[i]  < self.KLINE_HIGH[j]) or  \
                           (self.KLINE_SHORT_TERM_LIST_LIMIT[i] == 2 and self.KLINE_HIGH[i] > self.KLINE_LOW[j]):
                            pass
                        else:
                            pass
                        lowmin_time_int  = -1 
                        lowmin           = -1
                        highmax_time_int = -1 
                        highmax          = -1   
                        i=j
                        break
            else:
                continue
    #----------------------------------------------------------------------  
    def short_term_list_First(self):
        '''短期低点列表 --- 选择连续点的第一个大值和小值'''
        self.KLINE_SHORT_TERM_LOW = self.short_term_low(self.KLINE_LOW,self.KLINE_HIGH)    
        self.KLINE_SHORT_TERM_HIGH = self.short_term_high(self.KLINE_LOW,self.KLINE_HIGH)     
        
        self.KLINE_SHORT_TERM_LOW = [1 if i==True else 0 for i in self.KLINE_SHORT_TERM_LOW] #[1= 低点 0=普通点]
        self.KLINE_SHORT_TERM_HIGH =[2 if i==True else 0 for i in self.KLINE_SHORT_TERM_HIGH]#[2= 高点 0=普通点]
        self.KLINE_SHORT_TERM_LIST_FIRST = (np.array(self.KLINE_SHORT_TERM_LOW) + np.array(self.KLINE_SHORT_TERM_HIGH)).tolist()    
        
        for i in range(0,len(self.KLINE_SHORT_TERM_LIST_FIRST)):
            #1 获得当前点
            if self.KLINE_SHORT_TERM_LIST_FIRST[i] ==  1 or self.KLINE_SHORT_TERM_LIST_FIRST[i] ==  2:
                #2 判断当前点是高或者低
                for j in range(i+1,len(self.KLINE_SHORT_TERM_LIST_FIRST)):
                    #3 从当前点出发向后查找，需要知道下一个的高低点是不是同类型 
                    #->是同类型，只保留第一个，其余置0全部
                    #->不是同类型，那也就是第一个点，保留。但是要遵循高点大于低点，低点小于高点的原则 不满足置0
                    if   self.KLINE_SHORT_TERM_LIST_FIRST[j] ==  1 and self.KLINE_SHORT_TERM_LIST_FIRST[i] == 1:
                        self.KLINE_SHORT_TERM_LIST_FIRST[j] = 0 
                        continue
                    elif self.KLINE_SHORT_TERM_LIST_FIRST[j] ==  2 and self.KLINE_SHORT_TERM_LIST_FIRST[i] == 2:
                        self.KLINE_SHORT_TERM_LIST_FIRST[j] = 0     
                        continue
                    elif self.KLINE_SHORT_TERM_LIST_FIRST[j] ==  1 and self.KLINE_SHORT_TERM_LIST_FIRST[i] == 2 :
                        if self.KLINE_LOW[j] > self.KLINE_HIGH[i] :
                            self.KLINE_SHORT_TERM_LIST_FIRST[j] = 0  
                        i=j
                        break
                    elif self.KLINE_SHORT_TERM_LIST_FIRST[j] ==  2 and self.KLINE_SHORT_TERM_LIST_FIRST[i] == 1 :
                        if self.KLINE_HIGH[j] < self.KLINE_LOW[i] :
                            self.KLINE_SHORT_TERM_LIST_FIRST[j] = 0  
                        i=j
                        break
                    else:
                        continue
            else:
                continue
            
    #----------------------------------------------------------------------  
    def short_term_list_All(self):
        '''短期低点列表 --- 选择 所有点'''
        self.KLINE_SHORT_TERM_LOW = self.short_term_low(self.KLINE_LOW,self.KLINE_HIGH)    
        self.KLINE_SHORT_TERM_HIGH = self.short_term_high(self.KLINE_LOW,self.KLINE_HIGH)     
        
        self.KLINE_SHORT_TERM_LOW      = [1 if i==True else 0 for i in self.KLINE_SHORT_TERM_LOW] #[1= 低点 0=普通点]
        self.KLINE_SHORT_TERM_HIGH     = [2 if i==True else 0 for i in self.KLINE_SHORT_TERM_HIGH]#[2= 高点 0=普通点]
        self.KLINE_SHORT_TERM_LIST_ALL = (np.array(self.KLINE_SHORT_TERM_LOW) + np.array(self.KLINE_SHORT_TERM_HIGH)).tolist()    
    #----------------------------------------------------------------------
    def WAI_BAO_RI(self):
        """获得外包日"""
        #[1= 外包日 0= 不是外包日]
        self.KLINE_WAIBAORI             = [1 if self.KLINE_LOW[i]   <  self.KLINE_LOW[i-1]    and \
                                                self.KLINE_HIGH[i]  >  self.KLINE_HIGH[i-1]   and \
                                                self.KLINE_CLOSE[i] <  self.KLINE_LOW[i-1]        \
                                           else 0 for i in range(1,len(self.KLINE_CLOSE))] 
        self.KLINE_WAIBAORI             = [0] + self.KLINE_WAIBAORI 
    #----------------------------------------------------------------------
    def GJR_BUY(self):
        """获得攻击日买入"""
        #[1= 攻击日 0= 不是攻击日]
        self.KLINE_GJR_BUY              = [1 if self.KLINE_LOW[i]    <  self.KLINE_LOW[i-1]    and \
                                                self.KLINE_LOW[i-1]  <  self.KLINE_LOW[i-1-1]  and \
                                                self.KLINE_HIGH[i]   <  self.KLINE_HIGH[i-1]   and \
                                                self.KLINE_HIGH[i-1] <  self.KLINE_HIGH[i-1-1] and \
                                                self.KLINE_CLOSE[i]  <  self.KLINE_CLOSE[i-1]  and \
                                                self.KLINE_CLOSE[i-1]<  self.KLINE_CLOSE[i-1-1]and \
                                                self.KLINE_CLOSE[i]  <  self.KLINE_LOW[i-1]        \
                                           else 0 for i in range(2,len(self.KLINE_CLOSE))] 
        self.KLINE_GJR_BUY             = [0,0] + self.KLINE_GJR_BUY 
    #----------------------------------------------------------------------
    def GJR_SELL(self):
        """获得攻击日卖出"""
        #[1= 攻击日 0= 不是攻击日]
        self.KLINE_GJR_SELL              =[1 if self.KLINE_LOW[i]    >  self.KLINE_LOW[i-1]    and \
                                                self.KLINE_LOW[i-1]  >  self.KLINE_LOW[i-1-1]  and \
                                                self.KLINE_HIGH[i]   >  self.KLINE_HIGH[i-1]   and \
                                                self.KLINE_HIGH[i-1] >  self.KLINE_HIGH[i-1-1] and \
                                                self.KLINE_CLOSE[i]  >  self.KLINE_CLOSE[i-1]  and \
                                                self.KLINE_CLOSE[i-1]>  self.KLINE_CLOSE[i-1-1]and \
                                                self.KLINE_CLOSE[i]  >  self.KLINE_HIGH[i-1]       \
                                           else 0 for i in range(2,len(self.KLINE_CLOSE))] 
        self.KLINE_GJR_SELL             = [0,0] + self.KLINE_GJR_SELL    
        
########################################################################
# 功能测试
########################################################################
import sys
if __name__ == '__main__':     
    app = QApplication(sys.argv)
    # 界面设置
    cfgfile = QtCore.QFile('css.qss')
    cfgfile.open(QtCore.QFile.ReadOnly)
    styleSheet = cfgfile.readAll()
    styleSheet = unicode(styleSheet, encoding='utf8')
    app.setStyleSheet(styleSheet)
    # K线界面
    ui = KLineWidget()
    ui.show()
    ui.loadKLineSetting()
    ui.set_start_and_end_pos(pd.DataFrame.from_csv(ui.dailydata_path))
    ui.KLtitle.setText(ui.HYNAME+'   '+ui.StrategyName ,size='10pt',color='FFFF00')
    ui.loadData(pd.DataFrame.from_csv(ui.dailydata_path))
    ui.loadData_listsig(pd.DataFrame.from_csv(ui.dailyresult_path))
    ui.refreshAll()
    # 初始化界面显示
    ui.initIndicator(u'MA SHORT')
    ui.initIndicator(u'MA LONG')
    ui.initIndicator(u'KLINE')
    ui.initIndicator(u'SHORT TERM(First)')
    ui.initIndicator(u'SHORT TERM(All)')
    ui.initIndicator(u'SHORT TERM(Limit)')
    ui.initIndicator(u'外包日')
    ui.initIndicator(u'攻击日（买入）')
    ui.initIndicator(u'攻击日（卖出）')
    if ui.signal_show == True :
        ui.initIndicator(u'信号显示')
    else:
        ui.initIndicator(u'信号隐藏')
    app.exec_()
