"""WinForms pattern editor for ViewRename.

pyRevit's forms module is unavailable under CPython, so the editor is built directly on
System.Windows.Forms via pythonnet. The window only reads the model; saves happen in
`config.py` after the modal dialog closes.
"""

import clr

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import Color, Font, FontStyle
from System.Windows.Forms import (
    Button,
    Form,
    FormBorderStyle,
    FormStartPosition,
    Label,
    ListView,
    ListViewItem,
    MessageBox,
    MessageBoxButtons,
    TabControl,
    TabPage,
    TextBox,
    Timer,
    View,
)

from . import CLASS_NAMES, apply, pattern, storage

DEFAULT_PATTERNS = {
    "ViewPlan": (
        "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_PE_bip(PLAN_VIEW_LEVEL)_bip(VIEWER_VOLUME_OF_INTEREST_CROP)"
    ),
    "View3D": "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_3D",
    "ViewSection": "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_CP",
}


class PatternEditor:
    def __init__(self, doc):
        self.doc = doc
        self.action = None
        self.patterns = {}
        self._pattern_boxes = {}
        self._primary_labels = {}
        self._secondary_labels = {}
        self._error_labels = {}
        self._samples = {}

        stored = storage.read_patterns(doc)

        self.form = Form()
        self.form.Text = "ViewRename patterns"
        self.form.StartPosition = FormStartPosition.CenterScreen
        self.form.TopMost = True
        self.form.FormBorderStyle = FormBorderStyle.FixedDialog
        self.form.MaximizeBox = False
        self.form.MinimizeBox = False
        self.form.Width = 920
        self.form.Height = 680

        tabs = TabControl()
        tabs.SetBounds(10, 10, 890, 580)
        for class_name in CLASS_NAMES:
            tabs.TabPages.Add(self._build_tab(class_name, stored))
        self.form.Controls.Add(tabs)

        save_model = Button()
        save_model.Text = "Save to model"
        save_model.SetBounds(10, 600, 140, 30)
        save_model.Click += lambda sender, args: self._save("model")
        self.form.Controls.Add(save_model)

        save_config = Button()
        save_config.Text = "Save to config"
        save_config.SetBounds(160, 600, 140, 30)
        save_config.Click += lambda sender, args: self._save("config")
        self.form.Controls.Add(save_config)

        close = Button()
        close.Text = "Close"
        close.SetBounds(760, 600, 140, 30)
        close.Click += lambda sender, args: self.form.Close()
        self.form.Controls.Add(close)

    def _build_tab(self, class_name, stored):
        sample = _find_sample_view(self.doc, class_name)
        self._samples[class_name] = sample
        tab = TabPage(class_name)

        box = TextBox()
        box.SetBounds(10, 15, 850, 25)
        box.Text = stored.get(class_name) or DEFAULT_PATTERNS.get(class_name, "")
        box.TextChanged += lambda sender, args: self._update_preview(class_name)
        tab.Controls.Add(box)
        self._pattern_boxes[class_name] = box

        primary = Label()
        primary.SetBounds(10, 50, 850, 20)
        primary.Font = Font(primary.Font, FontStyle.Bold)
        primary.ForeColor = Color.Blue
        tab.Controls.Add(primary)
        self._primary_labels[class_name] = primary

        secondary = Label()
        secondary.SetBounds(10, 72, 850, 20)
        secondary.ForeColor = Color.Gray
        tab.Controls.Add(secondary)
        self._secondary_labels[class_name] = secondary

        error = Label()
        error.SetBounds(10, 94, 850, 20)
        error.ForeColor = Color.Red
        tab.Controls.Add(error)
        self._error_labels[class_name] = error

        note = Label()
        note.SetBounds(10, 116, 850, 20)
        note.ForeColor = Color.DarkRed
        if sample is None:
            note.Text = f"No {class_name} view in this document"
        tab.Controls.Add(note)

        list_view = ListView()
        list_view.SetBounds(10, 140, 850, 350)
        list_view.View = View.Details
        list_view.FullRowSelect = True
        list_view.Columns.Add("Name", 420)
        list_view.Columns.Add("Built-in", 280)
        list_view.Columns.Add("GUID", 140)
        if sample is None:
            list_view.Enabled = False
        else:
            for parameter in sorted(sample.Parameters, key=lambda item: item.Definition.Name):
                item = ListViewItem(parameter.Definition.Name)
                item.SubItems.Add(parameter.Definition.BuiltInParameter.ToString())
                item.SubItems.Add(str(parameter.GUID) if parameter.IsShared else "")
                item.Tag = parameter
                list_view.Items.Add(item)
        tab.Controls.Add(list_view)

        insert = Button()
        insert.Text = "Insert at cursor"
        insert.SetBounds(10, 500, 200, 30)
        insert.Click += lambda sender, args: self._insert_parameter(class_name, list_view)
        if sample is None:
            insert.Enabled = False
            box.Enabled = False
        tab.Controls.Add(insert)

        self._update_preview(class_name)
        return tab

    def _update_preview(self, class_name):
        box = self._pattern_boxes[class_name]
        errors = pattern.validate_pattern(box.Text)
        self._error_labels[class_name].Text = " | ".join(errors)
        sample = self._samples.get(class_name)
        if sample is None:
            return
        self._primary_labels[class_name].Text = pattern.apply_pattern(box.Text, apply.ViewResolver(sample))
        self._secondary_labels[class_name].Text = pattern.apply_pattern(
            box.Text, apply.ViewResolver(sample, use_definition_name=True)
        )

    def _insert_parameter(self, class_name, list_view):
        if list_view.SelectedItems.Count == 0:
            return
        parameter = list_view.SelectedItems[0].Tag
        self._pattern_boxes[class_name].SelectedText = _parameter_reference(parameter)

    def _collect_patterns(self):
        patterns = {}
        for class_name in CLASS_NAMES:
            text = self._pattern_boxes[class_name].Text.strip()
            if text:
                patterns[class_name] = text
        return patterns

    def _save(self, action):
        for class_name in CLASS_NAMES:
            errors = pattern.validate_pattern(self._pattern_boxes[class_name].Text)
            if errors:
                MessageBox.Show(
                    f"{class_name}: {'; '.join(errors)}",
                    "Invalid pattern",
                    MessageBoxButtons.OK,
                )
                return
        self.patterns = self._collect_patterns()
        self.action = action
        self.form.Close()

    def show(self):
        self.form.ShowDialog()


def _find_sample_view(doc, class_name):
    from Autodesk.Revit import DB

    view_class = getattr(DB, class_name, None)
    if view_class is None:
        return None
    for view in DB.FilteredElementCollector(doc).OfClass(view_class):
        if not view.IsTemplate:
            return view
    return None


def _parameter_reference(parameter):
    from Autodesk.Revit.DB import BuiltInParameter

    if parameter.IsShared:
        return f"Guid('{parameter.GUID}')"
    if parameter.Definition.BuiltInParameter != BuiltInParameter.INVALID:
        return f"bip({parameter.Definition.BuiltInParameter.ToString()})"
    return f"name({parameter.Definition.Name})"


def show_editor(doc):
    """Show the modal editor; return (action, patterns) with action in model/config/None."""
    editor = PatternEditor(doc)
    editor.show()
    return editor.action, editor.patterns


def run_smoke(doc):
    """Dev aid: build the editor, auto-close it, and report the tab count."""
    editor = PatternEditor(doc)
    timer = Timer()
    timer.Interval = 1200
    timer.Tick += lambda sender, args: editor.form.Close()
    timer.Start()
    editor.show()
    return f"UI-SMOKE-OK tabs={len(editor._pattern_boxes)}"
