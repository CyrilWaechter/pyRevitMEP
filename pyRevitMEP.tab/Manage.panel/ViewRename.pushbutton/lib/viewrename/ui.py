"""WinForms pattern editor for ViewRename.

pyRevit's forms module is unavailable under CPython, so the editor is built directly on
System.Windows.Forms via pythonnet. The window only reads the model; saves happen in
`config.py` after the modal dialog closes.

Each view class has a single RichTextBox holding the pattern; parameter references are
rendered as colored, bold inline tokens that can be dragged to another position (the
caret shows the landing point), double-clicked to select, and deleted like text.
"""

import clr

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import Color, Font, FontStyle
from System.Windows.Forms import (
    Button,
    Cursor,
    DragDropEffects,
    Form,
    FormBorderStyle,
    FormStartPosition,
    Keys,
    Label,
    ListView,
    ListViewItem,
    MessageBox,
    MessageBoxButtons,
    MouseButtons,
    RichTextBox,
    TabControl,
    TabPage,
    TextBox,
    Timer,
    View,
)

from . import CLASS_NAMES, DEFAULT_PATTERNS, apply, pattern, storage

KIND_COLORS = {
    "name": Color.FromArgb(210, 230, 255),
    "bip": Color.FromArgb(210, 245, 210),
    "guid": Color.FromArgb(255, 245, 200),
}


class PatternEditor:
    def __init__(self, doc):
        self.doc = doc
        self.action = None
        self.patterns = {}
        self._pattern_boxes = {}
        self._parameter_lists = {}
        self._search_boxes = {}
        self._parameters = {}
        self._samples = {}
        self._primary_labels = {}
        self._secondary_labels = {}
        self._error_labels = {}
        self._dragged_token = None

        stored = storage.read_patterns(doc)

        self.form = Form()
        self.form.Text = "ViewRename patterns"
        self.form.StartPosition = FormStartPosition.CenterScreen
        self.form.TopMost = True
        self.form.FormBorderStyle = FormBorderStyle.FixedDialog
        self.form.MaximizeBox = False
        self.form.MinimizeBox = False
        self.form.Width = 920
        self.form.Height = 720

        tabs = TabControl()
        tabs.SetBounds(10, 10, 890, 620)
        for class_name in CLASS_NAMES:
            tabs.TabPages.Add(self._build_tab(class_name, stored))
        self.form.Controls.Add(tabs)

        save_model = Button()
        save_model.Text = "Save to model"
        save_model.SetBounds(10, 640, 140, 30)
        save_model.Click += lambda sender, args: self._save("model")
        self.form.Controls.Add(save_model)

        save_config = Button()
        save_config.Text = "Save to config"
        save_config.SetBounds(160, 640, 140, 30)
        save_config.Click += lambda sender, args: self._save("config")
        self.form.Controls.Add(save_config)

        close = Button()
        close.Text = "Close"
        close.SetBounds(760, 640, 140, 30)
        close.Click += lambda sender, args: self.form.Close()
        self.form.Controls.Add(close)

    # ------------------------------------------------------------------ building

    def _build_tab(self, class_name, stored):
        sample = _find_sample_view(self.doc, class_name)
        self._samples[class_name] = sample
        tab = TabPage(class_name)

        box = RichTextBox()
        box.SetBounds(10, 15, 850, 110)
        box.Multiline = True
        box.AllowDrop = True
        box.Text = stored.get(class_name) or DEFAULT_PATTERNS.get(class_name, "")
        box.TextChanged += lambda sender, args: self._text_changed(class_name)
        box.MouseDown += lambda sender, args: self._pattern_mouse_down(class_name, sender, args)
        box.DoubleClick += lambda sender, args: self._pattern_double_click(class_name, sender, args)
        box.DragEnter += lambda sender, args: self._pattern_drag_over(class_name, sender, args)
        box.DragOver += lambda sender, args: self._pattern_drag_over(class_name, sender, args)
        box.DragDrop += lambda sender, args: self._pattern_drag_drop(class_name, sender, args)
        box.KeyDown += lambda sender, args: self._pattern_key_down(sender, args)
        tab.Controls.Add(box)
        self._pattern_boxes[class_name] = box

        primary = Label()
        primary.SetBounds(10, 135, 850, 20)
        primary.Font = Font(primary.Font, FontStyle.Bold)
        primary.ForeColor = Color.Blue
        tab.Controls.Add(primary)
        self._primary_labels[class_name] = primary

        secondary = Label()
        secondary.SetBounds(10, 157, 850, 20)
        secondary.ForeColor = Color.Gray
        tab.Controls.Add(secondary)
        self._secondary_labels[class_name] = secondary

        error = Label()
        error.SetBounds(10, 179, 850, 20)
        error.ForeColor = Color.Red
        tab.Controls.Add(error)
        self._error_labels[class_name] = error

        note = Label()
        note.SetBounds(10, 201, 850, 20)
        note.ForeColor = Color.DarkRed
        if sample is None:
            note.Text = f"No {class_name} view in this document"
        tab.Controls.Add(note)

        search = TextBox()
        search.SetBounds(10, 225, 300, 25)
        search.TextChanged += lambda sender, args: self._fill_parameter_list(class_name)
        tab.Controls.Add(search)
        self._search_boxes[class_name] = search

        list_view = ListView()
        list_view.SetBounds(10, 255, 850, 280)
        list_view.View = View.Details
        list_view.FullRowSelect = True
        list_view.Columns.Add("Name", 420)
        list_view.Columns.Add("Built-in", 280)
        list_view.Columns.Add("GUID", 140)
        list_view.DoubleClick += lambda sender, args: self._insert_selected(class_name)
        tab.Controls.Add(list_view)
        self._parameter_lists[class_name] = list_view

        if sample is None:
            self._parameters[class_name] = []
        else:
            self._parameters[class_name] = sorted(sample.Parameters, key=lambda item: item.Definition.Name)
        self._fill_parameter_list(class_name)

        insert = Button()
        insert.Text = "Insert selected parameter"
        insert.SetBounds(10, 545, 220, 30)
        insert.Click += lambda sender, args: self._insert_selected(class_name)
        tab.Controls.Add(insert)

        if sample is None:
            box.Enabled = False
            search.Enabled = False
            list_view.Enabled = False
            insert.Enabled = False

        self._apply_styles(class_name)
        self._update_preview(class_name)
        return tab

    # ------------------------------------------------------------------ tokens

    def _token_ranges(self, class_name):
        text = self._pattern_boxes[class_name].Text
        ranges = []
        position = 0
        for kind, value in pattern.tokenize(text):
            if kind != "text":
                ranges.append((position, position + len(value), kind))
            position += len(value)
        return ranges

    def _apply_styles(self, class_name):
        box = self._pattern_boxes[class_name]
        caret = box.SelectionStart
        length = box.SelectionLength
        box.SelectAll()
        box.SelectionBackColor = Color.White
        box.SelectionFont = Font(box.Font, FontStyle.Regular)
        for start, end, kind in self._token_ranges(class_name):
            box.Select(start, end - start)
            box.SelectionBackColor = KIND_COLORS.get(kind, Color.LightGray)
            box.SelectionFont = Font(box.Font, FontStyle.Bold)
        box.Select(caret, length)

    def _text_changed(self, class_name):
        self._apply_styles(class_name)
        self._update_preview(class_name)

    def _pattern_key_down(self, sender, args):
        if args.KeyCode == Keys.Enter:
            args.SuppressKeyPress = True

    def _pattern_mouse_down(self, class_name, sender, args):
        if args.Button != MouseButtons.Left:
            return
        box = self._pattern_boxes[class_name]
        index = box.GetCharIndexFromPosition(args.Location)
        for start, end, _kind in self._token_ranges(class_name):
            if start <= index < end:
                self._dragged_token = (class_name, start, end)
                box.DoDragDrop(box, DragDropEffects.Move)
                return

    def _pattern_double_click(self, class_name, sender, args):
        box = self._pattern_boxes[class_name]
        index = box.GetCharIndexFromPosition(args.Location)
        for start, end, _kind in self._token_ranges(class_name):
            if start <= index < end:
                box.Select(start, end - start)
                return

    def _pattern_drag_over(self, class_name, sender, args):
        if self._dragged_token is None:
            return
        box = self._pattern_boxes[class_name]
        box.SelectionStart = box.GetCharIndexFromPosition(box.PointToClient(Cursor.Position))
        box.SelectionLength = 0
        args.Effect = DragDropEffects.Move

    def _pattern_drag_drop(self, class_name, sender, args):
        dragged = self._dragged_token
        self._dragged_token = None
        if dragged is None or dragged[0] != class_name:
            return
        _cls, start, end = dragged
        box = self._pattern_boxes[class_name]
        target = box.GetCharIndexFromPosition(box.PointToClient(Cursor.Position))
        if start < target < end:
            return
        text = box.Text
        token = text[start:end]
        moved = text[:start] + text[end:]
        if target > end:
            target -= end - start
        box.Text = moved[:target] + token + moved[target:]
        box.SelectionStart = target + len(token)
        box.SelectionLength = 0

    def _insert_selected(self, class_name):
        list_view = self._parameter_lists[class_name]
        if list_view.SelectedItems.Count == 0:
            return
        self._insert_reference(class_name, _parameter_reference(list_view.SelectedItems[0].Tag))

    def _insert_reference(self, class_name, reference):
        box = self._pattern_boxes[class_name]
        box.SelectedText = reference
        box.SelectionStart += len(reference)
        box.SelectionLength = 0
        self._apply_styles(class_name)
        self._update_preview(class_name)

    # ------------------------------------------------------------------ list and preview

    def _fill_parameter_list(self, class_name):
        filter_text = self._search_boxes[class_name].Text.lower()
        list_view = self._parameter_lists[class_name]
        list_view.Items.Clear()
        for parameter in self._parameters.get(class_name, []):
            name = parameter.Definition.Name
            bip = parameter.Definition.BuiltInParameter.ToString()
            guid = str(parameter.GUID) if parameter.IsShared else ""
            if (
                filter_text
                and filter_text not in name.lower()
                and filter_text not in bip.lower()
                and filter_text not in guid.lower()
            ):
                continue
            item = ListViewItem(name)
            item.SubItems.Add(bip)
            item.SubItems.Add(guid)
            item.Tag = parameter
            list_view.Items.Add(item)

    def _update_preview(self, class_name):
        text = self._pattern_boxes[class_name].Text
        errors = pattern.validate_pattern(text)
        self._error_labels[class_name].Text = " | ".join(errors)
        sample = self._samples.get(class_name)
        if sample is None:
            return
        self._primary_labels[class_name].Text = pattern.apply_pattern(text, apply.ViewResolver(sample))
        self._secondary_labels[class_name].Text = pattern.apply_pattern(
            text, apply.ViewResolver(sample, use_definition_name=True)
        )

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
    """Dev aid: build the editor, auto-close it, and report tabs and token counts."""
    editor = PatternEditor(doc)
    timer = Timer()
    timer.Interval = 1200
    timer.Tick += lambda sender, args: editor.form.Close()
    timer.Start()
    editor.show()
    tokens = sum(len(editor._token_ranges(class_name)) for class_name in CLASS_NAMES)
    return f"UI-SMOKE-OK tabs={len(editor._pattern_boxes)} tokens={tokens}"
