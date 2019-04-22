# coding: utf8

import System

from pyrevit import forms

import rpw

doc = rpw.revit.doc
uidoc = rpw.revit.uidoc

class FamilyPreview(forms.WPFWindow):
    def __init__(self):
        forms.WPFWindow.__init__(self, 'FamilyPreview.xaml')
        for el_id in uidoc.Selection.GetElementIds():
            el = doc.GetElement(el_id)
        ftype = doc.GetElement(el.GetTypeId())
        image = ftype.GetPreviewImage(System.Drawing.Size(96, 96))
        self.preview_img.Source = System.Windows.Interop.Imaging.CreateBitmapSourceFromHBitmap(
            image.GetHbitmap(),
            System.IntPtr.Zero,
            System.Windows.Int32Rect.Empty,
            System.Windows.Media.Imaging.BitmapSizeOptions.FromEmptyOptions()
        )


FamilyPreview().show_dialog()