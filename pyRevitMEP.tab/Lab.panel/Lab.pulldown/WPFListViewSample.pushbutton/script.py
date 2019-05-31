# coding: utf8

import os
import wpf
from System.Windows import Window
from System.Collections.Generic import List
from System.Collections.ObjectModel import ObservableCollection

xaml_path = os.path.join(os.path.dirname(__file__), 'script.xaml')

class Test():
    def __init__(self, name):
        self.name = name

class MainWindow(Window):
    def __init__(self):
        Window.__init__(self)
        wpf.LoadComponent(self, xaml_path)
        items = List[object]()
        items.Add(Test("Cyril"))
        self.item_list.ItemsSource = items


main_window = MainWindow()
main_window.ShowDialog()
