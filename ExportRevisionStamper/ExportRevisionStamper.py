"""Fusion 360 add-in: stamps the current design revision onto exported
STEP/STL/3MF filenames and records every export to a local handoff log.

This file is the Fusion-facing glue. The actual filename/log logic lives in
lib/naming.py and lib/handoff_log.py so it can be unit tested outside Fusion.
"""
import datetime
import os
import traceback

import adsk.core
import adsk.fusion

from .lib import config as cfg
from .lib import handoff_log
from .lib import naming

_app = None
_ui = None
_handlers = []

_CMD_ID = "exportRevisionStamperCmd"
_CMD_NAME = "Export w/ Revision Stamp"
_CMD_TOOLTIP = "Export STEP/STL/3MF with the design's revision stamped into the filename, and log the handoff."
_PANEL_ID = "SolidScriptsAddinsPanel"

_FORMATS = ["STEP", "STL", "3MF"]


def _get_version_and_modified_flag(document: "adsk.core.Document"):
    """Return (version_number, is_modified). version_number falls back to 1
    for documents that have never been saved to the cloud (no DataFile yet)."""
    version_number = 1
    try:
        data_file = document.dataFile
        if data_file is not None:
            version_number = data_file.versionNumber
    except RuntimeError:
        # dataFile raises if the document was never saved to a Fusion project.
        pass
    return version_number, document.isModified


def _build_command_inputs(command: "adsk.core.Command"):
    settings = cfg.load()
    inputs = command.commandInputs

    format_input = inputs.addDropDownCommandInput(
        "formatDropdown", "Export Format", adsk.core.DropDownStyles.TextListDropDownStyle
    )
    for fmt in _FORMATS:
        format_input.listItems.add(fmt, fmt == _FORMATS[0])

    inputs.addStringValueInput("templateInput", "Filename Template", settings["template"])

    folder_input = inputs.addStringValueInput("folderInput", "Output Folder", settings["last_folder"])
    folder_input.isReadOnly = True
    inputs.addBoolValueInput("browseFolderButton", "Browse Output Folder...", False, "", False)

    inputs.addStringValueInput("vendorNoteInput", "Vendor / Note (optional)", "")

    preview_input = inputs.addTextBoxCommandInput("previewText", "Preview", "", 2, True)
    preview_input.isFullWidth = True

    _update_preview(command)


def _current_design_fields(command: "adsk.core.Command"):
    design = adsk.fusion.Design.cast(_app.activeProduct)
    document = _app.activeDocument
    root = design.rootComponent
    version_number, is_modified = _get_version_and_modified_flag(document)

    inputs = command.commandInputs
    fmt = inputs.itemById("formatDropdown").selectedItem.name
    template = inputs.itemById("templateInput").value
    note = inputs.itemById("vendorNoteInput").value
    ext = {"STEP": "step", "STL": "stl", "3MF": "3mf"}[fmt]

    return {
        "design": design,
        "root": root,
        "document": document,
        "version_number": version_number,
        "is_modified": is_modified,
        "format": fmt,
        "template": template,
        "note": note,
        "ext": ext,
    }


def _render_filename(fields: dict) -> str:
    today = datetime.date.today().strftime("%Y%m%d")
    return naming.render_template(
        fields["template"],
        name=fields["root"].name,
        version=fields["version_number"],
        date=today,
        ext=fields["ext"],
        note=fields["note"],
    )


def _update_preview(command: "adsk.core.Command"):
    try:
        fields = _current_design_fields(command)
        filename = _render_filename(fields)
        preview = command.commandInputs.itemById("previewText")
        modified_note = " (unsaved changes — will not match stamped revision!)" if fields["is_modified"] else ""
        preview.text = filename + modified_note
    except Exception:
        pass


def _run_export(fields: dict, full_path: str):
    export_manager = fields["design"].exportManager
    fmt = fields["format"]
    if fmt == "STEP":
        options = export_manager.createSTEPExportOptions(full_path, fields["root"])
    elif fmt == "STL":
        options = export_manager.createSTLExportOptions(fields["root"], full_path)
    elif fmt == "3MF":
        create_3mf = getattr(export_manager, "create3MFExportOptions", None)
        if create_3mf is None:
            raise RuntimeError(
                "This version of Fusion's API does not expose 3MF export "
                "(ExportManager.create3MFExportOptions). Use STEP or STL instead."
            )
        options = create_3mf(fields["root"], full_path)
    else:
        raise ValueError(f"Unsupported format: {fmt}")
    export_manager.execute(options)


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            command = args.command
            _build_command_inputs(command)

            on_execute = CommandExecuteHandler()
            command.execute.add(on_execute)
            _handlers.append(on_execute)

            on_input_changed = InputChangedHandler()
            command.inputChanged.add(on_input_changed)
            _handlers.append(on_input_changed)

            on_validate = ValidateInputsHandler()
            command.validateInputs.add(on_validate)
            _handlers.append(on_validate)
        except Exception:
            _ui.messageBox(f"Failed to create command:\n{traceback.format_exc()}")


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            command = args.firingEvent.sender
            changed_input = args.input

            if changed_input.id == "browseFolderButton":
                folder_dialog = _ui.createFolderDialog()
                folder_dialog.title = "Select Output Folder"
                settings = cfg.load()
                if settings["last_folder"]:
                    folder_dialog.initialDirectory = settings["last_folder"]
                if folder_dialog.showDialog() == adsk.core.DialogResults.DialogOK:
                    command.commandInputs.itemById("folderInput").value = folder_dialog.folder
                changed_input.value = False

            _update_preview(command)
        except Exception:
            _ui.messageBox(f"Input change failed:\n{traceback.format_exc()}")


class ValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def notify(self, args):
        try:
            command = args.firingEvent.sender
            folder = command.commandInputs.itemById("folderInput").value
            args.areInputsValid = bool(folder) and os.path.isdir(folder)
        except Exception:
            args.areInputsValid = False


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            command = args.firingEvent.sender
            fields = _current_design_fields(command)
            folder = command.commandInputs.itemById("folderInput").value

            if fields["is_modified"]:
                result = _ui.messageBox(
                    "This document has unsaved changes newer than its last saved revision.\n"
                    "The stamped revision will not reflect what you're about to export.\n\n"
                    "Export anyway?",
                    "Unsaved Changes",
                    adsk.core.MessageBoxButtonTypes.YesNoButtonType,
                    adsk.core.MessageBoxIconTypes.WarningIconType,
                )
                if result == adsk.core.DialogResults.DialogNo:
                    return

            filename = _render_filename(fields)
            full_path = os.path.join(folder, filename)

            _run_export(fields, full_path)

            settings = cfg.load()
            log_path = os.path.join(folder, settings["log_filename"])
            handoff_log.append_entry(log_path, {
                "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                "part_name": fields["root"].name,
                "version_number": fields["version_number"],
                "revision": naming.revision_letter(fields["version_number"]),
                "format": fields["format"],
                "filename": filename,
                "vendor_note": fields["note"],
                "doc_had_unsaved_changes": fields["is_modified"],
            })

            settings["template"] = fields["template"]
            settings["last_folder"] = folder
            cfg.save(settings)

            _ui.messageBox(f"Exported:\n{full_path}\n\nLogged to:\n{log_path}")
        except Exception:
            _ui.messageBox(f"Export failed:\n{traceback.format_exc()}")


def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

        cmd_def = _ui.commandDefinitions.itemById(_CMD_ID)
        if cmd_def is None:
            cmd_def = _ui.commandDefinitions.addButtonDefinition(_CMD_ID, _CMD_NAME, _CMD_TOOLTIP)

        on_created = CommandCreatedHandler()
        cmd_def.commandCreated.add(on_created)
        _handlers.append(on_created)

        panel = _ui.allToolbarPanels.itemById(_PANEL_ID)
        if panel and panel.controls.itemById(_CMD_ID) is None:
            panel.controls.addCommand(cmd_def)
    except Exception:
        if _ui:
            _ui.messageBox(f"Failed to start add-in:\n{traceback.format_exc()}")


def stop(context):
    try:
        panel = _ui.allToolbarPanels.itemById(_PANEL_ID)
        if panel:
            control = panel.controls.itemById(_CMD_ID)
            if control:
                control.deleteMe()

        cmd_def = _ui.commandDefinitions.itemById(_CMD_ID)
        if cmd_def:
            cmd_def.deleteMe()
    except Exception:
        if _ui:
            _ui.messageBox(f"Failed to stop add-in:\n{traceback.format_exc()}")
