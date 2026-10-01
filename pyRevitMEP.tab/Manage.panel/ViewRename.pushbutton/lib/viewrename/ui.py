"""WinForms pattern editor for ViewRename.

pyRevit's forms module is unavailable under CPython, so the editor is built directly on
System.Windows.Forms via pythonnet. The window only reads the model; saves happen in
`config.py` after the modal dialog closes.

Patterns are edited as a sequence of chips: literal text is kept in small text boxes and
parameter references are colored chips that can be inserted at the caret or removed.
"""

import clr

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import Color, Font, FontStyle, Point
from System.Windows.Forms import (
    BorderStyle,
    Button,
    Cursor,
    Cursors,
    DragDropEffects,
    FlatStyle,
    FlowLayoutPanel,
    Form,
    FormBorderStyle,
    FormStartPosition,
    Label,
    ListView,
    ListViewItem,
    MessageBox,
    MessageBoxButtons,
    MouseButtons,
    Padding,
    Panel,
    TabControl,
    TabPage,
    TextBox,
    Timer,
    ToolTip,
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
        self._chip_areas = {}
        self._focused_boxes = {}
        self._parameter_lists = {}
        self._search_boxes = {}
        self._parameters = {}
        self._samples = {}
        self._primary_labels = {}
        self._secondary_labels = {}
        self._error_labels = {}
        self._tooltip = ToolTip()
        self._dragged_chip = None

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

        area = FlowLayoutPanel()
        area.SetBounds(10, 15, 850, 110)
        area.AutoScroll = True
        area.WrapContents = True
        area.BorderStyle = BorderStyle.FixedSingle
        area.Padding = Padding(4)
        area.AllowDrop = True
        area.DragEnter += self._area_drag_enter
        area.DragOver += self._area_drag_enter
        area.DragDrop += lambda sender, args: self._area_drag_drop(class_name, sender, args)
        tab.Controls.Add(area)
        self._chip_areas[class_name] = area

        text = stored.get(class_name) or DEFAULT_PATTERNS.get(class_name, "")
        for kind, value in pattern.tokenize(text):
            if kind == "text":
                self._add_text_box(class_name, value)
            else:
                area.Controls.Add(self._make_chip(class_name, kind, value))

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
            area.Enabled = False
            search.Enabled = False
            list_view.Enabled = False
            insert.Enabled = False

        self._update_preview(class_name)
        return tab

    def _add_text_box(self, class_name, text):
        box = TextBox()
        box.Text = text
        box.Width = _text_width(text)
        box.TextChanged += lambda sender, args: self._text_changed(class_name, box)
        box.Enter += lambda sender, args: self._focused_boxes.__setitem__(class_name, box)
        self._enable_drop(class_name, box)
        self._chip_areas[class_name].Controls.Add(box)
        return box

    def _enable_drop(self, class_name, control):
        control.AllowDrop = True
        control.DragEnter += self._area_drag_enter
        control.DragOver += self._area_drag_enter
        control.DragDrop += lambda sender, args: self._area_drag_drop(class_name, sender, args)

    def _make_chip(self, class_name, kind, value):
        chip = Panel()
        chip.Tag = value
        chip.BackColor = KIND_COLORS.get(kind, Color.LightGray)
        chip.Height = 24
        chip.Margin = Padding(2)
        chip.Cursor = Cursors.SizeAll

        display = self._chip_label(class_name, kind, value)
        label = Label()
        label.Text = display
        label.AutoSize = False
        label.Width = _text_width(display)
        label.Height = 18
        label.Location = Point(4, 3)
        chip.Controls.Add(label)

        remove = Button()
        remove.Text = "x"
        remove.FlatStyle = FlatStyle.Flat
        remove.Width = 20
        remove.Height = 20
        remove.Location = Point(label.Width + 8, 2)
        remove.Click += lambda sender, args: self._remove_chip(class_name, chip)
        chip.Controls.Add(remove)

        chip.Width = label.Width + remove.Width + 16
        self._tooltip.SetToolTip(chip, value)
        self._tooltip.SetToolTip(label, value)
        chip.MouseDown += lambda sender, args: self._chip_mouse_down(chip, sender, args)
        label.MouseDown += lambda sender, args: self._chip_mouse_down(chip, sender, args)
        self._enable_drop(class_name, chip)
        self._enable_drop(class_name, label)
        self._enable_drop(class_name, remove)
        return chip

    def _chip_label(self, class_name, kind, value):
        argument = _reference_argument(value)
        sample = self._samples.get(class_name)
        if sample is not None:
            resolver = apply.ViewResolver(sample, use_definition_name=True)
            if kind == "name":
                resolved = resolver.by_name(argument)
            elif kind == "bip":
                resolved = resolver.by_bip(argument)
            else:
                resolved = resolver.by_guid(argument)
            if resolved:
                return resolved
        if kind == "guid" and len(argument) > 12:
            return argument[:8] + "..."
        return argument

    def _chip_mouse_down(self, chip, sender, args):
        if args.Button == MouseButtons.Left:
            self._dragged_chip = chip
            chip.DoDragDrop(chip, DragDropEffects.Move)

    def _area_drag_enter(self, sender, args):
        if self._dragged_chip is not None:
            args.Effect = DragDropEffects.Move

    def _area_drag_drop(self, class_name, sender, args):
        chip = self._dragged_chip
        self._dragged_chip = None
        area = self._chip_areas[class_name]
        if chip is None or chip.Parent != area:
            return
        client = area.PointToClient(Cursor.Position)
        index = len(area.Controls)
        for position, control in enumerate(area.Controls):
            if client.Y < control.Top + control.Height // 2:
                index = position
                break
            if client.Y <= control.Bottom and client.X < control.Left + control.Width // 2:
                index = position
                break
        current = area.Controls.GetChildIndex(chip)
        if current < index:
            index -= 1
        area.Controls.SetChildIndex(chip, index)

    # ------------------------------------------------------------------ editing

    def _text_changed(self, class_name, box):
        box.Width = _text_width(box.Text)
        self._update_preview(class_name)

    def _remove_chip(self, class_name, chip):
        self._chip_areas[class_name].Controls.Remove(chip)
        self._update_preview(class_name)

    def _insert_selected(self, class_name):
        list_view = self._parameter_lists[class_name]
        if list_view.SelectedItems.Count == 0:
            return
        reference = _parameter_reference(list_view.SelectedItems[0].Tag)
        self._insert_reference(class_name, reference)

    def _insert_reference(self, class_name, reference):
        area = self._chip_areas[class_name]
        chip = self._make_chip(class_name, _kind_for_reference(reference), reference)
        box = self._focused_boxes.get(class_name)
        if box is not None and box.Parent == area:
            caret = box.SelectionStart
            before, after = box.Text[:caret], box.Text[caret:]
            box.Text = before
            index = area.Controls.GetChildIndex(box)
            area.Controls.Add(chip)
            area.Controls.SetChildIndex(chip, index + 1)
            new_box = self._add_text_box(class_name, after)
            area.Controls.SetChildIndex(new_box, index + 2)
            self._focused_boxes[class_name] = new_box
        else:
            area.Controls.Add(chip)
        self._update_preview(class_name)

    def _serialize(self, class_name):
        parts = []
        for control in self._chip_areas[class_name].Controls:
            if isinstance(control, TextBox):
                parts.append(control.Text)
            elif control.Tag:
                parts.append(control.Tag)
        return "".join(parts)

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
        text = self._serialize(class_name)
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
            text = self._serialize(class_name).strip()
            if text:
                patterns[class_name] = text
        return patterns

    def _save(self, action):
        for class_name in CLASS_NAMES:
            errors = pattern.validate_pattern(self._serialize(class_name))
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


def _text_width(text):
    return max(30, 8 * len(text) + 16)


def _reference_argument(reference):
    start = reference.find("(")
    end = reference.rfind(")")
    if start == -1 or end <= start:
        return reference
    argument = reference[start + 1 : end].strip()
    if len(argument) >= 2 and argument[0] in ("'", '"') and argument[-1] == argument[0]:
        argument = argument[1:-1]
    return argument


def _kind_for_reference(reference):
    if reference.startswith("name("):
        return "name"
    if reference.startswith("bip("):
        return "bip"
    return "guid"


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
    chip_count = sum(len(area.Controls) for area in editor._chip_areas.values())
    return f"UI-SMOKE-OK tabs={len(editor._chip_areas)} controls={chip_count}"
