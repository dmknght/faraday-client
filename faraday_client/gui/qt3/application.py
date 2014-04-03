#!/usr/bin/env python
'''
Faraday Penetration Test IDE - Community Version
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

'''
import os
try:
    import qt
except ImportError:
    print "[-] Python QT3 was not found in the system, please install it and try again"
    print "Check the deps file"
from gui.qt3.mainwindow import MainWindow
import model.guiapi

from config.configuration import getInstanceConfiguration
CONF = getInstanceConfiguration()


class GuiApp(qt.QApplication):

    def __init__(self, main_app, model_controller):
        qt.QApplication.__init__(self, [])
        model.guiapi.setMainApp(self)
        self._model_controller = model_controller

        self._main_window = MainWindow(CONF.getAppname(),
                                       main_app, self._model_controller)
        self.setMainWidget(self._main_window)

        self._splash_screen = qt.QSplashScreen(
            qt.QPixmap(os.path.join(CONF.getImagePath(), "splash2.png")),
            qt.Qt.WStyle_StaysOnTop)

    def getMainWindow(self):
        return self._main_window

    def run(self):
        self._main_window.createShellTab()
        self._main_window.showAll()

    def loadWorkspaces(self):
        self._main_window.getWorkspaceTreeView().loadAllWorkspaces()

    # def do_activate(self):
    #     self.main_window = MainWindow(self)

    # def do_startup(self):
    #     Gtk.Application.do_startup(self)

    def setSplashImage(self, ipath):
        pass

    def startSplashScreen(self):
        splash_timer = qt.QTimer.singleShot(1700, lambda *args: None)
        self._splash_screen.show()

    def stopSplashScreen(self):
        self._splash_screen.finish(self._main_window)

    def quit(self):
        elf._main_window.hide()
