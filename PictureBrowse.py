#!/usr/bin/python3
#-*- coding:utf-8 -*-


import os
import sys
import fnmatch
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *



class SearchFiles:
    
    def __init__(self):
        
        pass
        
    def searchFiles(self, path, filterext = "*.png"):
        
        filepaths = []
        
        for dirpath, dirnames, filenames in os.walk(path): 
            for filename in filenames:
                if fnmatch.fnmatch(filename, filterext):  
                    filepath = os.path.join(dirpath, filename)
                    filepaths.append(filepath)
                    
        return filepaths



class ImageView(QGraphicsView):
    
    rectChanged = pyqtSignal(QRect)

    def __init__(self, parent = None):
        
        super().__init__(parent = parent)
        
        self.zoom_times = 0
        self.max_zoom_times = 50
        self.is_enable_drag = False
        self.factor = 1.1

        # 创建场景
        self.graphics_scene = QGraphicsScene()

        # 图片
        self.pixmap = QPixmap()
        self.pixmap_item = QGraphicsPixmapItem()
        self.display_image = QImage()
        self.display_image_size = self.display_image.size()

        # 初始化小部件
        self.__initWidget()
        

    def __initWidget(self):
        
        # 隐藏滚动条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 以鼠标所在位置为锚点进行缩放
        self.setTransformationAnchor(self.AnchorUnderMouse)

        # 平滑缩放
        self.pixmap_item.setTransformationMode(Qt.SmoothTransformation)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        # 设置场景
        self.graphics_scene.addItem(self.pixmap_item)
        self.setScene(self.graphics_scene)
        

    def wheelEvent(self, e: QWheelEvent):
        
        """ 滚动鼠标滚轮缩放图片 """
        if e.angleDelta().y() > 0:
            self.zoomIn()
        else:
            self.zoomOut()
            
        self.rectChanged.emit(self.geometry())

    def resizeEvent(self, e):
        
        """ 缩放图片 """
        super().resizeEvent(e)

        if self.zoom_times > 0:
            return

        # 调整图片大小
        ratio = self.__getScaleRatio()
        self.display_image_size = self.display_image.size() * ratio
        if ratio < 1:
            self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        else:
            self.resetTransform()
            

    def setImage(self, filename):
        
        """ 设置显示的图片 """
        self.resetTransform()

        # 刷新图片
        try:
            self.display_image.load(filename)
        except:
            QMessageBox.warning(self, "警告提示", "加载图片文件失败！")
            
        self.updateImage()
        

    def resetTransform(self):
        
        """ 重置变换 """
        super().resetTransform()
        self.__setDragEnabled(False)
        self.zoom_times = 0
        self.rectChanged.emit(self.geometry())
        

    def __isEnableDrag(self):
        
        """ 根据图片的尺寸决定是否启动拖拽功能 """
        v = self.verticalScrollBar().maximum() > 0
        h = self.horizontalScrollBar().maximum() > 0
        
        return v or h

    def __setDragEnabled(self, is_enabled : bool):
        
        """ 设置拖拽是否启动 """
        if self.is_enable_drag != is_enabled:
            self.is_enable_drag = is_enabled
            self.setDragMode(self.ScrollHandDrag if is_enabled else self.NoDrag)
        

    def __getScaleRatio(self):
        
        """ 获取显示的图像和原始图像的缩放比例 """
        if not self.display_image or self.display_image.isNull():
            return 1

        img_width = self.display_image.width()
        img_height = self.display_image.height()
        min_width = min(1, self.width() / img_width)
        min_height = min(1, self.height() / img_height)
        
        return min(min_width, min_height)

    def fitInView(self, item : QGraphicsItem, mode = Qt.KeepAspectRatio):
        
        """ 缩放场景使其适应窗口大小 """
        super().fitInView(item, mode)
        self.display_image_size = self.__getScaleRatio() * self.display_image.size()
        self.zoom_times = 0
        self.rectChanged.emit(self.geometry())

    def fitIn(self, mode = Qt.KeepAspectRatio):
        
        self.fitInView(self.pixmap_item)
        
    def zoomTimes(self):
        
        return self.zoom_times
    
    def maxZoomTimes(self):
        
        return self.max_zoom_times

    def zoomIn(self, view_anchor = QGraphicsView.AnchorUnderMouse):
        
        """ 放大图像 """
        if self.zoom_times == self.max_zoom_times:
            return

        self.setTransformationAnchor(view_anchor)

        self.zoom_times += 1
        self.scale(self.factor, self.factor)
        self.__setDragEnabled(self.__isEnableDrag())

        # 还原 anchor
        self.setTransformationAnchor(self.AnchorUnderMouse)

    def zoomOut(self, view_anchor = QGraphicsView.AnchorUnderMouse):
        
        """ 缩小图像 """
        if self.zoom_times == 0 and not self.__isEnableDrag():
            return

        self.zoom_times -= 1
        self.setTransformationAnchor(view_anchor)

        # 原始图像的大小
        image_width = self.display_image.width()
        image_height = self.display_image.height()

        # 实际显示的图像宽度
        display_width = image_width * self.factor ** self.zoom_times
        display_height = image_height * self.factor ** self.zoom_times

        if image_width > self.width() or image_height > self.height():
            # 在窗口尺寸小于原始图像时禁止继续缩小图像比窗口还小
            if display_width <= self.width() and display_height <= self.height():
                self.fitInView(self.pixmap_item)
            else:
                self.scale(1 / self.factor, 1 / self.factor)
        else:
            # 在窗口尺寸大于图像时不允许缩小的比原始图像小
            if display_width <= image_width:
                self.resetTransform()
            else:
                self.scale(1 / self.factor, 1 / self.factor)

        self.__setDragEnabled(self.__isEnableDrag())

        # 还原 anchor
        self.setTransformationAnchor(self.AnchorUnderMouse)
        
        
    def zoomInOut(self, zoom_times, view_anchor = QGraphicsView.AnchorViewCenter):
        
        """ 缩放图像 """
        if zoom_times < 0 or zoom_times > self.max_zoom_times or self.zoom_times == zoom_times:
            return
        
        old_zoom_times = self.zoom_times
        self.zoom_times = zoom_times
        self.setTransformationAnchor(view_anchor)
         
        if zoom_times > old_zoom_times:
            # 放大图像
            factor = self.factor ** (zoom_times - old_zoom_times)
            self.scale(factor, factor)
        elif zoom_times < old_zoom_times:
            # 原始图像的大小
            image_width = self.display_image.width()
            image_height = self.display_image.height()
    
            # 实际显示的图像宽度
            display_width = image_width * self.factor ** self.zoom_times
            display_height = image_height * self.factor ** self.zoom_times
            
            # 缩小图像
            factor = self.factor ** (old_zoom_times - zoom_times)
            if image_width > self.width() or image_height > self.height():
                # 在窗口尺寸小于原始图像时禁止继续缩小图像比窗口还小
                if display_width <= self.width() and display_height <= self.height():
                    self.fitInView(self.pixmap_item)
                else:
                    self.scale(1 / factor, 1 / factor)
            else:
                # 在窗口尺寸大于图像时不允许缩小的比原始图像小
                if display_width <= image_width:
                    self.resetTransform()
                else:
                    self.scale(1 / factor, 1 / factor)

        # 还原 anchor
        self.setTransformationAnchor(self.AnchorUnderMouse)
            

    def leftRotate(self, angle = 90):
        
        if self.display_image:
            transform = QTransform()
            transform.rotate(-angle)
            self.display_image = self.display_image.transformed(transform)
        
        self.updateImage()
        
    
    def rightRotate(self, angle = 90):
        
        if self.display_image:
            transform = QTransform()
            transform.rotate(angle)
            self.display_image = self.display_image.transformed(transform)
        
        self.updateImage()
        
    
    def emptyImage(self):
        
        """ 设置显示的图片 """
        self.resetTransform()

        # 刷新图片
        self.display_image = QImage()        
        self.updateImage()
        
        
    def updateImage(self):
        
        # 刷新图片
        self.pixmap = QPixmap(self.display_image)
        self.pixmap_item.setPixmap(self.pixmap)

        # 调整图片大小
        self.setSceneRect(QRectF(self.display_image.rect()))
        ratio = self.__getScaleRatio()
        self.display_image_size = self.display_image.size() * ratio
        if ratio < 1:
            self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
    
    
    def save(self, filename):
        
        if self.display_image:
            self.display_image.save(filename)
            return True
        
        return False
    

class PictureBrowseFrame(QWidget):
    
    def __init__(self):
        
        super().__init__()
        
        self.filename = None
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            self.filename = sys.argv[1]
        
        self.__initWidget()
        
    def __initWidget(self):
        
        self.title = "图片浏览"
        self.setWindowTitle(self.title)
        self.resize(860, 800)
        self.setAcceptDrops(True)
        
        self.image_view = ImageView(self)
        self.image_view.setAcceptDrops(False)
        if self.filename:
            self.image_view.setImage(self.filename)
        
        self.btn_zoom_inout = QPushButton("放大/缩小", self)
        self.btn_fit_in = QPushButton("自适应", self)
        self.btn_fullscreen = QPushButton("全屏", self)
        self.btn_prev = QPushButton("上一个", self)
        self.btn_next = QPushButton("下一个", self)
        self.btn_left_rotate = QPushButton("左旋转", self)
        self.btn_right_rotate = QPushButton("右旋转", self)
        self.btn_save = QPushButton("保存", self)
        self.btn_remove = QPushButton("删除", self)

        self.slider_zoom = QSlider(Qt.Vertical, self)
        self.slider_zoom.setRange(0, self.image_view.maxZoomTimes())
        self.slider_zoom.setValue(self.image_view.zoomTimes())
        self.slider_zoom.setFixedSize(20, 100)
        self.slider_zoom.hide()
        
        self.btn_zoom_inout.setFixedSize(106, 30)
        self.btn_fit_in.setFixedSize(60, 30)
        self.btn_prev.setFixedSize(60, 30)
        self.btn_fullscreen.setFixedSize(50, 30)
        self.btn_next.setFixedSize(60, 30)
        self.btn_left_rotate.setFixedSize(60, 30)
        self.btn_right_rotate.setFixedSize(60, 30)
        self.btn_save.setFixedSize(50, 30)
        self.btn_remove.setFixedSize(50, 30)
    
        layout = QVBoxLayout()
        layout1 = QVBoxLayout()
        layout2 = QHBoxLayout()
   
        layout1.addWidget(self.image_view)
        layout2.addWidget(self.btn_zoom_inout)
        layout2.addWidget(self.btn_fit_in)
        layout2.addWidget(self.btn_fullscreen)
        layout2.addWidget(self.btn_prev)
        layout2.addWidget(self.btn_next)
        layout2.addWidget(self.btn_left_rotate)
        layout2.addWidget(self.btn_right_rotate)
        layout2.addWidget(self.btn_save)
        layout2.addWidget(self.btn_remove)
        
        self.bottom = QWidget(self)
        self.bottom.setFixedWidth(680)
        self.bottom.setLayout(layout2)
        
        layout.addLayout(layout1)
        layout.addWidget(self.bottom, 0, Qt.AlignHCenter)
        
        self.setLayout(layout)

        self.btn_zoom_inout.clicked.connect(self.slotClickedZoomInout)
        self.btn_fit_in.clicked.connect(self.slotClickedFitIn)
        self.btn_fullscreen.clicked.connect(self.slotClickedFullscreen)
        self.btn_prev.clicked.connect(self.slotClickedPrev)
        self.btn_next.clicked.connect(self.slotClickedNext)
        self.btn_left_rotate.clicked.connect(self.slotClickedLeftRotate)
        self.btn_right_rotate.clicked.connect(self.slotClickedRightRotate)
        self.btn_save.clicked.connect(self.slotClickedSave)
        self.btn_remove.clicked.connect(self.slotClickedRemove)
        
        self.slider_zoom.valueChanged.connect(self.slotChangeZoomInout)
        self.image_view.rectChanged.connect(self.slotChangeViewRect)
        
        self.updateButton()


    def dragEnterEvent(self, evt):
        
        if evt.mimeData().hasText():
            evt.accept()
        else:
            evt.ignore()
        
    def dropEvent(self, evt):
        
        filepath = evt.mimeData().text()
        filename = filepath.replace('file:///', '')
        self.filename = filename.replace('/', '\\')
        
        path = os.path.dirname(self.filename)
        extname = os.path.splitext(self.filename)[1]
        search = SearchFiles()
        self.filepaths = search.searchFiles(path, "*" + extname)
        if self.filepaths and len(self.filepaths) > 1:
            try:
                self.pathindex = self.filepaths.index(self.filename)
            except:
                self.pathindex = 0
                print("find error")
            
            
        self.setWindowTitle(self.title + " - " + self.filename)
        self.image_view.setImage(self.filename)
        self.updateButton()

        
    def keyPressEvent(self, evt):
        
        if evt.key() == Qt.Key_F12:
            self.showFullScreen()
            self.btn_fullscreen.setText("正常")
        elif evt.key() == Qt.Key_Escape:
            self.showNormal()
            self.btn_fullscreen.setText("全屏")
            
            
    def resizeEvent(self, a0):
        
        if not self.slider_zoom.isHidden():
            pos = self.bottom.mapToParent(self.btn_zoom_inout.pos())
            pos_x = pos.x() + int((self.btn_zoom_inout.width() - self.slider_zoom.width() ) / 2)
            pos_y = pos.y() - self.slider_zoom.height() - 10 
            self.slider_zoom.move(pos_x, pos_y)
          
    def slotChangeViewRect(self, rect):
        
        if self.image_view:
            zoom_times = self.image_view.zoomTimes()
            self.slider_zoom.setValue(zoom_times)
        
    def slotChangeZoomInout(self, val):
        
        if self.image_view:
            self.image_view.zoomInOut(val)
             
        
    def slotClickedZoomInout(self, evt):
        
        if self.slider_zoom.isHidden():
            pos = self.bottom.mapToParent(self.btn_zoom_inout.pos())
            pos_x = pos.x() + int((self.btn_zoom_inout.width() - self.slider_zoom.width() ) / 2)
            pos_y = pos.y() - self.slider_zoom.height() - 10 
            self.slider_zoom.move(pos_x, pos_y)
            self.slider_zoom.show()
        else:
            self.slider_zoom.hide()
            
                
    def slotClickedFitIn(self, evt):
        
        if self.image_view:
            self.image_view.fitIn()
                
    def slotClickedFullscreen(self, evt):
        
        if not self.isFullScreen():
            self.showFullScreen()
            self.btn_fullscreen.setText("正常")
        else:
            self.showNormal()
            self.btn_fullscreen.setText("全屏")
           
    def updateButton(self):
       
        if hasattr(self, 'filepaths') and len(self.filepaths) > 0:
            file_count = len(self.filepaths)
            if file_count == 1:
                self.btn_prev.setEnabled(True)
                self.btn_next.setEnabled(True)
            else:
                if self.pathindex == 0:   
                    self.btn_prev.setEnabled(False)
                    self.btn_next.setEnabled(True)
                elif self.pathindex == file_count - 1:
                    
                    self.btn_prev.setEnabled(True)
                    self.btn_next.setEnabled(False)
                else:
                    self.btn_prev.setEnabled(True)
                    self.btn_next.setEnabled(True)
        else:
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)        
    
    def slotClickedPrev(self, evt):
        
        if hasattr(self, 'filepaths') and len(self.filepaths) > 0:
            if self.pathindex > 0 and self.pathindex < len(self.filepaths):
                self.pathindex -= 1
                self.filename = self.filepaths[self.pathindex]
                self.setWindowTitle(self.title + " - " + self.filename)
                self.image_view.setImage(self.filename)
                
        self.updateButton()
     
    
    def slotClickedNext(self, evt):
        
        if hasattr(self, 'filepaths') and len(self.filepaths) > 0:
            if self.pathindex >= 0 and self.pathindex < len(self.filepaths) - 1:
                self.pathindex += 1
                self.filename = self.filepaths[self.pathindex]
                self.setWindowTitle(self.title + " - " + self.filename)
                self.image_view.setImage(self.filename)
                
        self.updateButton()
  
    
    def slotClickedLeftRotate(self, evt):
        
        if self.image_view:
            self.image_view.leftRotate()
    
    def slotClickedRightRotate(self, evt):
        
        if self.image_view:
            self.image_view.rightRotate()
    
    def slotClickedSave(self, evt):
        
        if self.filename:       
            self.image_view.save(self.filename)
        else:         
            QMessageBox.warning(self, "警告提示", "请先打开图片在保存该图片！")
            
    def slotClickedRemove(self, evt):
        
        if self.filename:
            os.remove(self.filename)
            self.filename = None
            
            if hasattr(self, 'filepaths') and len(self.filepaths) > 0:
                if self.pathindex >= 0 and self.pathindex < len(self.filepaths): 
                    del self.filepaths[self.pathindex]
                    
                    if self.pathindex < len(self.filepaths):
                        self.filename = self.filepaths[self.pathindex]
                        self.setWindowTitle(self.title + " - " + self.filename)
                        self.image_view.setImage(self.filename) 
                    else:   
                        if self.pathindex >= len(self.filepaths):
                            self.pathindex -= 1
                            if self.pathindex >= 0:
                                self.filename = self.filepaths[self.pathindex]
                                self.setWindowTitle(self.title + " - " + self.filename)
                                self.image_view.setImage(self.filename)
            
            if not self.filename:
                self.image_view.emptyImage()
                
            self.updateButton()
        else:
            QMessageBox.warning(self, "警告提示", "您还没有打开过图片，不能删除操作！")
                    
   


if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    frame = PictureBrowseFrame()
    frame.show()
    
    code = app.exec_()
    sys.exit(code)