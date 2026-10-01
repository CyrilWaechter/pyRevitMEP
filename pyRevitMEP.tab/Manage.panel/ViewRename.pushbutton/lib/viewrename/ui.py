"""WinForms pattern editor for ViewRename.

pyRevit's forms module is unavailable under CPython, so the editor is built directly on
System.Windows.Forms via pythonnet. The window only reads the model; saves happen in
`config.py` after the modal dialog closes.

Each view class has a single RichTextBox holding the pattern. Parameter references are
shown as `[Parameter Name]` and rendered as colored, bold inline tokens that can be
dragged to another position (the caret snaps to token boundaries and shows the landing
point), double-clicked to select, and deleted like text. On save the tokens are
converted back to the canonical `name(...)` / `bip(...)` / `Guid('...')` syntax.
"""

import re

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
    "unknown": Color.FromArgb(255, 220, 220),
}

BRACKET_RE = re.compile(r"\[([^\[\]]+)\]")


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
        self._label_refs = {class_name: {} for class_name in CLASS_NAMES}
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
        raw = stored.get(class_name) or DEFAULT_PATTERNS.get(class_name, "")
        box.Text = self._display(class_name, raw)
        box.TextChanged += lambda sender, args: self._text_changed(class_name)
        box.MouseDown += lambda sender, args: self._pattern_mouse_down(class_name, sender, args)
        box.DoubleClick += lambda sender, args: self._pattern_double_click(class_name, sender, args)
        box.DragEnter += lambda sender, args: self._pattern_drag_over(class_name, sender, args)
        box.DragOver += lambda sender, args: self._pattern_drag_over(class_name, sender, args)
        box.DragDrop += lambda sender, args: self._pattern_drag_drop(class_name, sender, args)
        box.KeyDown += lambda sender, args: self._pattern_key_down(class_name, sender, args)
        box.KeyPress += lambda sender, args: self._pattern_key_press(class_name, sender, args)
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

    # ------------------------------------------------------------------ display/canonical

    def _display(self, class_name, text):
        sample = self._samples.get(class_name)
        parts = []
        position = 0
        for start, end, _kind, value in pattern.reference_matches(text):
            parts.append(text[position:start])
            parameter = _resolve_reference(sample, value)
            if parameter is None:
                parts.append(value)
            else:
                label = parameter.Definition.Name
                self._label_refs[class_name].setdefault(label, value)
                parts.append("[" + label + "]")
            position = end
        parts.append(text[position:])
        return "".join(parts)

    def _canonical(self, class_name, text):
        sample = self._samples.get(class_name)

        def replace(match):
            label = match.group(1)
            reference = self._label_refs[class_name].get(label)
            if reference is None:
                parameter = _find_parameter(sample, label)
                if parameter is None:
                    return match.group(0)
                reference = _parameter_reference(parameter)
                self._label_refs[class_name][label] = reference
            return reference

        return BRACKET_RE.sub(replace, text)

    def _token_ranges(self, class_name):
        text = self._pattern_boxes[class_name].Text
        ranges = []
        for start, end, kind, _value in pattern.reference_matches(text):
            ranges.append((start, end, kind))
        for match in BRACKET_RE.finditer(text):
            ranges.append((match.start(), match.end(), self._bracket_kind(class_name, match.group(1))))
        ranges.sort()
        return ranges

    def _bracket_kind(self, class_name, name):
        parameter = _find_parameter(self._samples.get(class_name), name)
        if parameter is None:
            return "unknown"
        return _parameter_kind(parameter)

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

    def _pattern_key_down(self, class_name, sender, args):
        box = self._pattern_boxes[class_name]
        if args.KeyCode == Keys.Enter:
            args.SuppressKeyPress = True
            return
        if args.KeyCode == Keys.Delete:
            token = self._token_at(class_name, box.SelectionStart, include_start=True, include_end=False)
            if token is not None:
                self._delete_token(class_name, token)
                args.SuppressKeyPress = True
            return
        if args.KeyCode == Keys.Back:
            token = self._token_at(class_name, box.SelectionStart, include_start=False, include_end=True)
            if token is not None:
                self._delete_token(class_name, token)
                args.SuppressKeyPress = True

    def _pattern_key_press(self, class_name, sender, args):
        if ord(args.KeyChar) < 32:
            return
        box = self._pattern_boxes[class_name]
        index = box.SelectionStart
        snapped = self._snap_to_token_boundary(class_name, index)
        if snapped != index:
            box.SelectionStart = snapped
            box.SelectionLength = 0

    def _token_at(self, class_name, index, include_start, include_end):
        for start, end, _kind in self._token_ranges(class_name):
            if (include_start and start <= index < end) or (include_end and start < index <= end):
                return (start, end)
        return None

    def _delete_token(self, class_name, token):
        start, end = token
        box = self._pattern_boxes[class_name]
        text = box.Text
        box.Text = text[:start] + text[end:]
        box.SelectionStart = start
        box.SelectionLength = 0

    def _snap_to_token_boundary(self, class_name, index):
        for start, end, _kind in self._token_ranges(class_name):
            if start < index < end:
                return start if index - start <= end - index else end
        return index

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
        index = box.GetCharIndexFromPosition(box.PointToClient(Cursor.Position))
        box.SelectionStart = self._snap_to_token_boundary(class_name, index)
        box.SelectionLength = 0
        args.Effect = DragDropEffects.Move

    def _pattern_drag_drop(self, class_name, sender, args):
        dragged = self._dragged_token
        self._dragged_token = None
        if dragged is None or dragged[0] != class_name:
            return
        _cls, start, end = dragged
        box = self._pattern_boxes[class_name]
        index = box.GetCharIndexFromPosition(box.PointToClient(Cursor.Position))
        target = self._snap_to_token_boundary(class_name, index)
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
        parameter = list_view.SelectedItems[0].Tag
        label = parameter.Definition.Name
        self._label_refs[class_name].setdefault(label, _parameter_reference(parameter))
        self._insert_token(class_name, "[" + label + "]")

    def _insert_token(self, class_name, text):
        box = self._pattern_boxes[class_name]
        box.SelectionStart = self._snap_to_token_boundary(class_name, box.SelectionStart)
        box.SelectionLength = 0
        box.SelectedText = text
        box.SelectionStart += len(text)
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

    def _validation_errors(self, class_name):
        text = self._pattern_boxes[class_name].Text
        errors = pattern.validate_pattern(self._canonical(class_name, text))
        sample = self._samples.get(class_name)
        if sample is not None:
            for match in BRACKET_RE.finditer(text):
                label = match.group(1)
                if label not in self._label_refs[class_name] and _find_parameter(sample, label) is None:
                    errors.append(f"Unknown parameter: {label}")
        return errors

    def _update_preview(self, class_name):
        text = self._canonical(class_name, self._pattern_boxes[class_name].Text)
        self._error_labels[class_name].Text = " | ".join(self._validation_errors(class_name))
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
            text = self._canonical(class_name, self._pattern_boxes[class_name].Text).strip()
            if text:
                patterns[class_name] = text
        return patterns

    def _save(self, action):
        for class_name in CLASS_NAMES:
            errors = self._validation_errors(class_name)
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


def _find_parameter(sample, name):
    if sample is None:
        return None
    parameters = sample.GetParameters(name)
    if not parameters:
        return None
    return parameters[0]


def _resolve_reference(sample, reference):
    if sample is None:
        return None
    kind = _kind_for_reference(reference)
    argument = _reference_argument(reference)
    try:
        if kind == "name":
            return _find_parameter(sample, argument)
        if kind == "bip":
            from Autodesk.Revit.DB import BuiltInParameter

            bip = getattr(BuiltInParameter, argument, None)
            if bip is None:
                return None
            return sample.get_Parameter(bip)
        from System import Guid

        return sample.get_Parameter(Guid.Parse(argument))
    except Exception:  # noqa: BLE001 - unresolved references keep their raw syntax
        return None


def _parameter_kind(parameter):
    from Autodesk.Revit.DB import BuiltInParameter

    if parameter.IsShared:
        return "guid"
    if parameter.Definition.BuiltInParameter != BuiltInParameter.INVALID:
        return "bip"
    return "name"


def _parameter_reference(parameter):
    kind = _parameter_kind(parameter)
    if kind == "guid":
        return f"Guid('{parameter.GUID}')"
    if kind == "bip":
        return f"bip({parameter.Definition.BuiltInParameter.ToString()})"
    return f"name({parameter.Definition.Name})"


def _kind_for_reference(reference):
    if reference.startswith("name("):
        return "name"
    if reference.startswith("bip("):
        return "bip"
    return "guid"


def _reference_argument(reference):
    start = reference.find("(")
    end = reference.rfind(")")
    if start == -1 or end <= start:
        return reference
    argument = reference[start + 1 : end].strip()
    if len(argument) >= 2 and argument[0] in ("'", '"') and argument[-1] == argument[0]:
        argument = argument[1:-1]
    return argument


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
