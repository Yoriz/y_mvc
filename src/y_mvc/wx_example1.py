'''
Created on 28 Mar 2013

@author: Dave Wilson
'''

from wxAnyThread import anythread
from y_mvc.y_mvc_wx.text_ctrl import TextChangeCtrl, EVT_TEXT_CHANGE
import re
import wx
import ymvc


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)
        self.view = ymvc.View(self)

        panel = wx.Panel(self)
        self.labelAttr1 = wx.StaticText(panel)
        self.textAttr1 = TextChangeCtrl(panel)
        self.labelAttr2 = wx.StaticText(panel)
        self.textAttr2 = TextChangeCtrl(panel)
        self.btnOpen = wx.Button(panel, wx.ID_OPEN)

        fGridSizer = wx.FlexGridSizer(cols=2, vgap=7, hgap=4)
        fGridSizer.Add(self.textAttr1, flag=wx.ALIGN_CENTER_VERTICAL)
        fGridSizer.Add(self.labelAttr1, flag=wx.ALIGN_CENTER_VERTICAL)
        fGridSizer.Add(self.textAttr2, flag=wx.ALIGN_CENTER_VERTICAL)
        fGridSizer.Add(self.labelAttr2, flag=wx.ALIGN_CENTER_VERTICAL)

        pSizer = wx.BoxSizer(wx.VERTICAL)
        pSizer.Add(fGridSizer, 0, wx.ALIGN_CENTER | wx.ALL, 7)
        pSizer.Add(self.btnOpen, 0, wx.ALIGN_CENTER | wx.ALL, 7)

        fSizer = wx.BoxSizer(wx.VERTICAL)
        fSizer.Add(panel, 1, wx.EXPAND)

        panel.SetSizer(pSizer)
        self.SetSizer(fSizer)
        self.Layout()

        self.textAttr1.checkIsValid = lambda text: text != ''
        self.textAttr1.checkCharAcceptable = self.textCharAcceptable

        self.textAttr1.Bind(EVT_TEXT_CHANGE,
            lambda event: self.view.notifyKw(attr1=event.String))

        self.textAttr2.Bind(EVT_TEXT_CHANGE,
            lambda event: self.view.notifyKw(attr2=event.String))

        self.btnOpen.Bind(wx.EVT_BUTTON, lambda _: self.view.notify('Open'))

    def textCharAcceptable(self, char):
        return re.search(r'[A-Za-z ]', char)

    @anythread
    def setAttr1(self, attr1):
        self.labelAttr1.SetLabel(attr1)
        self.SetTitle(attr1)
        self.textAttr1.ChangeValue(attr1)

    @anythread
    def setAttr2(self, attr2):
        self.labelAttr2.SetLabel(attr2)
        self.textAttr2.ChangeValue(attr2)

    @anythread
    def createFrame2(self):
        frame = Frame2(None)
        frame.Show()
        return frame


class Frame2(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(Frame2, self).__init__(*args, **kwargs)
        self.view = ymvc.View(self)

        panel = wx.Panel(self)
        self.labelAttr1 = wx.StaticText(panel, label='Change Attr1')
        self.textAttr1 = TextChangeCtrl(panel)
        self.labelAttr2 = wx.StaticText(panel, label='Change Attr2')
        self.textAttr2 = TextChangeCtrl(panel)

        fGridSizer = wx.FlexGridSizer(cols=2, vgap=7, hgap=4)
        fGridSizer.Add(self.labelAttr1, flag=wx.ALIGN_CENTER_VERTICAL)
        fGridSizer.Add(self.textAttr1, flag=wx.ALIGN_CENTER_VERTICAL)
        fGridSizer.Add(self.labelAttr2, flag=wx.ALIGN_CENTER_VERTICAL)
        fGridSizer.Add(self.textAttr2, flag=wx.ALIGN_CENTER_VERTICAL)

        pSizer = wx.BoxSizer(wx.VERTICAL)
        pSizer.Add(fGridSizer, 0, wx.ALIGN_CENTER | wx.ALL, 7)

        fSizer = wx.BoxSizer(wx.VERTICAL)
        fSizer.Add(panel, 1, wx.EXPAND)

        panel.SetSizer(pSizer)
        self.SetSizer(fSizer)
        self.Fit()
        self.Layout()

        self.textAttr1.checkIsValid = lambda text: text != ''
        self.textAttr1.checkCharAcceptable = self.textCharAcceptable

        self.textAttr1.Bind(EVT_TEXT_CHANGE,
            lambda event: self.view.notifyKw(attr1=event.String))

        self.textAttr2.Bind(EVT_TEXT_CHANGE,
            lambda event: self.view.notifyKw(attr2=event.String))

    def textCharAcceptable(self, char):
        return re.search(r'[A-Za-z ]', char)

    @anythread
    def setAttr1(self, attr1):
        self.SetTitle(attr1)
        self.textAttr1.ChangeValue(attr1)

    @anythread
    def setAttr2(self, attr2):
        self.textAttr2.ChangeValue(attr2)


class MainFrameController(ymvc.Controller):
    def __init__(self, gui, attrModel):
        super(MainFrameController, self).__init__(gui)
        self.attrModel = attrModel
        self.gui.view.bind(self.onViewAttr1)
        self.gui.view.bind(self.onViewAttr2)
        self.gui.view.bind(self.onOpen)
        self.attrModel.bind(self.onAttrModelAttr1)
        self.attrModel.bind(self.onAttrModelAttr2)

    @ymvc.onNotifyKw('attr1')
    def onViewAttr1(self, attr1):
        self.attrModel.attr1 = attr1

    @ymvc.onNotifyKw('attr2')
    def onViewAttr2(self, attr2):
        self.attrModel.attr2 = attr2

    @ymvc.onNotify('Open')
    def onOpen(self):
        frame2 = self.gui.createFrame2()
        frame2.view.setController(MainFrameController, attrModel)

    @ymvc.onAttr('attr1')
    def onAttrModelAttr1(self, attr1):
        self.gui.setAttr1(attr1)

    @ymvc.onAttr('attr2')
    def onAttrModelAttr2(self, attr2):
        self.gui.setAttr2(attr2)


class AttrModel(ymvc.Model):

    def __init__(self, attr1='', attr2=''):
        super(AttrModel, self).__init__('attr1', 'attr2')
        self.attr1 = attr1
        self.attr2 = attr2

    @property
    def attr1(self):
        return self._attr1

    @attr1.setter
    def attr1(self, value):
        self._attr1 = value.title()[:16]


if __name__ == '__main__':

    attrModel = AttrModel('Attr1', 'Attr2')

    wxapp = wx.App(False)
    mainFrame = MainFrame(None)
    mainFrame.view.setController(MainFrameController, attrModel)
    mainFrame.Show()
    wxapp.MainLoop()
