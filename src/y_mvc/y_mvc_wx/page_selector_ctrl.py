'''
Created on 31 Mar 2013

@author: Dave Wilson
'''

import wx
from wxAnyThread import anythread
from wx.lib.intctrl import IntCtrl
from y_mvc import ymvc


def createBtn(parent, pSizer, label, tipText, handler, updateHandler=None):
    font = wx.Font(11, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Webdings')
    ctrl = wx.Button(parent, label=label, size=(23, 23))
    ctrl.SetFont(font)
    ctrl.SetToolTipString(tipText)
    pSizer.Add(ctrl, 0, flag=wx.ALIGN_CENTER)
    ctrl.Bind(wx.EVT_BUTTON, handler)
    if updateHandler:
        ctrl.Bind(wx.EVT_UPDATE_UI, updateHandler)
    return ctrl


def createCtrlPageNo(parent, pSizer, handler):
    ctrl = IntCtrl(parent, value=1, size=(70, -1), min=1, max=1, limited=True,
                   allow_none=True,
                    style=wx.TE_CENTER | wx.TE_PROCESS_ENTER | wx.BORDER_THEME)
    ctrl.SetToolTipString("Enter page number")
    pSizer.Add(ctrl, 0, border=1, flag=wx.ALL | wx.ALIGN_CENTER)
    ctrl.Bind(wx.EVT_TEXT_ENTER, handler)
    return ctrl


class PageSelectorCtrl(wx.Panel):

    def __init__(self, *args, **kwargs):
        super(PageSelectorCtrl, self).__init__(*args, **kwargs)
        self.view = ymvc.View(self)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        createBtn(self, sizer, "9", "Show first page", self.onBtnFirst)
        createBtn(self, sizer, "7", "Show previous page", self.onBtnPrevious,
                                                    self.onBtnPreviousUpdate)
        self.ctrlPageNo = createCtrlPageNo(self, sizer, self.onPageNo)
        createBtn(self, sizer, "8", "Show next page", self.onBtnNext,
                                                        self.onBtnNextUpdate)
        createBtn(self, sizer, ":", "Show last page", self.onBtnLast)

        self.ctrlDetails = wx.StaticText(self, label="Page")

        sizer.Add(self.ctrlDetails, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 4)
        self.SetSizer(sizer)
        self.Fit()

    def onBtnFirst(self, event):
        self.setPageNo(1)
        self.view.notifyKw(pageNo=self.getPageNo())
        event.Skip()

    def onBtnPrevious(self, event):
        if self.getPageNo() > 1:
            self.setPageNo(self.getPageNo() - 1)
            self.view.notifyKw(pageNo=self.getPageNo())
        event.Skip()

    def onBtnPreviousUpdate(self, event):
        if not self.IsEnabled():
            event.Skip()
        event.Enable(False if self.getPageNo() == 1 else True)

    def onPageNo(self, event):
        self.setPageNo(int(event.String))
        self.view.notifyKw(pageNo=self.getPageNo())
#        event.Skip()

    def onBtnNext(self, event):
        if self.getPageNo() < self.getlastPageNo():
            self.setPageNo(self.getPageNo() + 1)
            self.view.notifyKw(pageNo=self.getPageNo())
        event.Skip()

    def onBtnNextUpdate(self, event):
        if not self.IsEnabled():
            event.Skip()
        condition = self.getPageNo() == self.getlastPageNo()
        event.Enable(False if condition else True)

    def onBtnLast(self, event):
        self.setPageNo(self.getlastPageNo())
        self.view.notifyKw(pageNo=self.getPageNo())
        event.Skip()

    def getPageNo(self):
        return self.ctrlPageNo.GetValue() or 1

    def getlastPageNo(self):
        return self.ctrlPageNo.GetMax()

    @anythread
    def setPageNo(self, value):
        self.ctrlPageNo.ChangeValue(value)

    @anythread
    def setLastPageNo(self, value):
        self.ctrlPageNo.SetMax(value)

    @anythread
    def setPageDetails(self, pageDetails):
        self.ctrlDetails.SetLabel(pageDetails)
        self.GetParent().Layout()


class PageSelectorController(ymvc.Controller):
    def __init__(self, gui, pageSelectorModel):
        super(PageSelectorController, self).__init__(gui)
        self.pageSelectorModel = pageSelectorModel

        self.gui.view.bind(self.onViewPageNo)

        self.pageSelectorModel.bind(self.onpageSelectorModelLastPageNo)
        self.pageSelectorModel.bind(self.onpageSelectorModelPageNo)
        self.pageSelectorModel.bind(self.onpageSelectorModelPageDetails)

    @ymvc.onNotifyKw('pageNo')
    def onViewPageNo(self, pageNo):
        self.pageSelectorModel.notifyKw(requestPageNo=pageNo)

    @ymvc.onAttr('pageNo')
    def onpageSelectorModelPageNo(self, pageNo):
        self.gui.setPageNo(pageNo)

    @ymvc.onAttr('lastPageNo')
    def onpageSelectorModelLastPageNo(self, lastPageNo):
        self.gui.setLastPageNo(lastPageNo)

    @ymvc.onAttr('pageDetails')
    def onpageSelectorModelPageDetails(self, pageDetails):
        self.gui.setPageDetails(pageDetails)


class GetRecordsTestModel(ymvc.Model):
    def __init__(self, pageSelectorModel):
        super(GetRecordsTestModel, self).__init__()
        self.pageSelectorModel = pageSelectorModel
        self.numRecords = 2500
        self.onPageSelectorModelRequestPageNo(1)

        pageSelectorModel.bind(self.onPageSelectorModelRequestPageNo)
        pageSelectorModel.bind(self.onPageSelectorModelLimitOffset)

    @ymvc.onNotifyKw('requestPageNo')
    def onPageSelectorModelRequestPageNo(self, requestPageNo):
        self.pageSelectorModel.numRecords = self.numRecords
        self.pageSelectorModel.pageNo = requestPageNo

    @ymvc.onNotifyKw('limit', 'offset')
    def onPageSelectorModelLimitOffset(self, limit, offset):
        print 'Requested database records limit: {}, offset: {}'.format(limit,
                                                                        offset)

if __name__ == '__main__':
    from y_mvc.models.page_selector_model import PageSelectorModel
    pageSelectorModel = PageSelectorModel()
    getRecordsTestModel = GetRecordsTestModel(pageSelectorModel)
    wxapp = wx.App(None)
    frame = wx.Frame(None, title="Testing PageDetails Panel")
    pageSelectorCtrl = PageSelectorCtrl(frame)
    pageSelectorCtrl.view.setController(PageSelectorController,
                                        pageSelectorModel)
    fSizer = wx.BoxSizer(wx.VERTICAL)
    fSizer.Add(pageSelectorCtrl)
    frame.SetSizer(fSizer)
    frame.Layout()
    frame.Show()
    wxapp.MainLoop()
