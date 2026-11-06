# Template: a FreeCAD 1.1.4 GUI macro that runs in its own process and exits by itself.
#
# Flow: open a COPY of the input (or create a new empty document when no input is
# given) -> modify -> save -> close -> reopen -> verify (objects, visible objects,
# shapes) -> saveImage from the 3D view -> JSON log -> normal exit.
#
# Environment (all optional):
#   GUI_MACRO_INPUT    path of an FCStd to copy and open; empty -> new empty document
#   GUI_MACRO_OUT_DIR  output folder (copy, saved file, PNG, log); default: a new temp folder
#   GUI_MACRO_LOG_JSON path of the JSON log; default: <OUT_DIR>/result.json
#   GUI_MACRO_TIMEOUT  in-macro watchdog, seconds; default 100
#   GUI_MACRO_ALLOW_XLINKS  set to 1 to open an input that has external links anyway
#
# Launch it only as described in SKILL.md (copied profile, one GUI at a time, check
# the syntax first). Edit modify() and verify() for the real task; keep the rest.
import json
import os
import shutil
import re
import tempfile
import time
import zipfile
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtCore, QtWidgets

OUT_DIR = os.environ.get("GUI_MACRO_OUT_DIR") or tempfile.mkdtemp(prefix="gui_macro_")
LOG_JSON = os.environ.get("GUI_MACRO_LOG_JSON") or os.path.join(OUT_DIR, "result.json")
INPUT = os.environ.get("GUI_MACRO_INPUT", "")
TIMEOUT_S = float(os.environ.get("GUI_MACRO_TIMEOUT", "100"))
PROBE_NAME = "GuiMacroProbe"

LOG = {"ok": False, "steps": [], "error": None, "out_dir": OUT_DIR}
OWN_DOCS = []  # names of documents this macro opened or created
_state = {"finished": False, "logged": False}


def step(name, **data):
    entry = {"step": name, "t": round(time.time() - _state.get("t0", time.time()), 2)}
    entry.update(data)
    LOG["steps"].append(entry)


def write_log():
    os.makedirs(os.path.dirname(os.path.abspath(LOG_JSON)), exist_ok=True)
    with open(LOG_JSON, "w", encoding="utf-8") as fh:
        json.dump(LOG, fh, indent=2, default=str)
    _state["logged"] = True


def pump():
    """Let the GUI process pending events; call after every document change."""
    QtWidgets.QApplication.processEvents()


def activate(doc):
    """Make doc the active document through the MDI area and return its 3D view.

    The Gui module has no function that activates a document by name, so select
    the document's MDI sub-window by its title ("<name or label> : <n>[*]").
    """
    area = Gui.getMainWindow().findChild(QtWidgets.QMdiArea)
    if area is None:
        raise RuntimeError("no MDI area")
    wanted = (doc.Name + " : ", doc.Label + " : ")
    target = None
    for sub in area.subWindowList():
        title = sub.windowTitle()
        if title.startswith(wanted):
            target = sub
            break
    if target is None:
        titles = [sub.windowTitle() for sub in area.subWindowList()]
        raise RuntimeError("no MDI sub-window for %s among %s" % (doc.Name, titles))
    area.setActiveSubWindow(target)
    pump()
    active = Gui.ActiveDocument
    if active is None or active.Document.Name != doc.Name:
        raise RuntimeError("activation failed for " + doc.Name)
    view = active.ActiveView
    if view is None:
        views = active.mdiViewsOfType("Gui::View3DInventor")
        view = views[0] if views else None
    if view is None:
        raise RuntimeError("no 3D view for document " + doc.Name)
    return view


def modify(doc):
    """The change under test. Replace with the real edit.

    Adds one solid object. In a copy of an accepted assembly replace shapes
    without calling recompute(); recompute here only because the probe is new.
    """
    probe = doc.addObject("Part::Feature", PROBE_NAME)
    probe.Shape = Part.makeBox(10, 10, 10)
    probe.Visibility = True
    doc.recompute()
    pump()
    return probe


def shape_of(obj):
    """Shape of an object including App::Link (placement applied), or None."""
    try:
        shape = Part.getShape(obj, "", transform=True)
    except Exception:
        shape = getattr(obj, "Shape", None)
    if shape is None or shape.isNull():
        return None
    return shape


def snapshot(doc):
    """Objects, visible objects and shape facts of an open document."""
    objs = list(doc.Objects)
    visible = []
    shapes = {}
    for obj in objs:
        vo = getattr(obj, "ViewObject", None)  # None for objects without a view provider
        if vo is not None and getattr(vo, "Visibility", False):
            visible.append(obj.Name)
        shape = shape_of(obj)
        if shape is not None:
            shapes[obj.Name] = {
                "faces": len(shape.Faces),
                "solids": len(shape.Solids),
                "volume": shape.Volume,
            }
    return {"objects": len(objs), "visible": sorted(visible), "shapes": shapes}


def close_enough(a, b):
    """Relative tolerance 1e-6 with a small absolute floor (reloaded shapes differ in the last digits)."""
    return abs(a - b) <= max(1e-6 * max(abs(a), abs(b)), 1e-9)


def same_facts(a, b):
    return (a["faces"] == b["faces"] and a["solids"] == b["solids"]
            and close_enough(a["volume"], b["volume"]))


def verify(before, after):
    """Compare the state before saving with the state after reopening."""
    problems = []
    if after["objects"] != before["objects"]:
        problems.append("object count %s -> %s" % (before["objects"], after["objects"]))
    if after["visible"] != before["visible"]:
        problems.append("visible objects differ")
    if PROBE_NAME in before["shapes"]:
        got = after["shapes"].get(PROBE_NAME)
        if got is None:
            problems.append("probe shape missing")
        elif got["faces"] != 6 or not close_enough(got["volume"], 1000.0):
            problems.append("probe shape changed: %s" % got)
        if PROBE_NAME not in after["visible"]:
            problems.append("probe not visible after reopen")
    for name, facts in before["shapes"].items():
        got = after["shapes"].get(name)
        if got is None or not same_facts(got, facts):
            problems.append("shape differs: " + name)
    return problems


def check_no_external_links(path):
    """Fail clearly if the input links to other files: a lone copy would break them.

    If it does, copy the dependent files together into the same relative layout
    and set GUI_MACRO_ALLOW_XLINKS=1, or run on the whole folder copy.
    """
    if os.environ.get("GUI_MACRO_ALLOW_XLINKS") == "1":
        return
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("Document.xml").decode("utf-8", "replace")
    if re.search(r'<XLink[^>]*\sfile="[^"]+"', xml):
        raise RuntimeError("input has external links; copy the dependent files with it "
                           "(same relative layout) and set GUI_MACRO_ALLOW_XLINKS=1")


def run():
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        if INPUT:
            work = os.path.join(OUT_DIR, "work_copy.FCStd")
            check_no_external_links(INPUT)
            shutil.copy2(INPUT, work)  # never open the original
            doc = App.openDocument(work)
            step("opened_copy", file=work)
        else:
            doc = App.newDocument("GuiMacroDoc")
            step("new_document")
        name = doc.Name  # read names now: the wrapper is dead after closeDocument
        OWN_DOCS.append(name)
        pump()
        activate(doc)
        modify(doc)
        before = snapshot(doc)
        step("modified", state=before)

        saved = os.path.join(OUT_DIR, "saved.FCStd")
        doc.saveAs(saved)
        pump()
        step("saved", file=saved, bytes=os.path.getsize(saved))
        App.closeDocument(name)
        OWN_DOCS.remove(name)
        doc = None  # never touch the closed document again; use `before` and `saved`
        pump()

        doc2 = App.openDocument(saved)
        name2 = doc2.Name
        OWN_DOCS.append(name2)
        pump()
        view = activate(doc2)
        after = snapshot(doc2)
        problems = verify(before, after)
        step("reopened", state=after, problems=problems)

        png = os.path.join(OUT_DIR, "view.png")
        view.viewIsometric()
        view.fitAll()
        pump()
        view.saveImage(png, 800, 600, "Current")  # image comes from the 3D view
        if not (os.path.isfile(png) and os.path.getsize(png) > 0):
            problems.append("PNG not written")
        step("image", file=png, bytes=os.path.getsize(png) if os.path.isfile(png) else 0)

        LOG["ok"] = not problems
        if problems:
            LOG["error"] = "; ".join(problems)
    except Exception:
        LOG["ok"] = False
        LOG["error"] = traceback.format_exc()
    finally:
        finish()


def finish():
    """Write the log, close the documents this macro owns, then the main window."""
    if _state["finished"]:
        return
    _state["finished"] = True
    try:
        write_log()
    except Exception:
        pass
    for name in list(OWN_DOCS):
        try:
            App.closeDocument(name)
        except Exception:
            pass
    OWN_DOCS[:] = []
    pump()
    # Fallback only: if the window stays open, leave the event loop normally later.
    QtCore.QTimer.singleShot(5000, QtWidgets.QApplication.quit)
    Gui.getMainWindow().close()


def on_watchdog():
    # Fires only at event-loop points; a blocked loop needs the external watchdog.
    if _state["finished"]:
        return
    LOG["ok"] = False
    LOG["error"] = "in-macro watchdog: no result after %s s" % TIMEOUT_S
    finish()


def start():
    _state["t0"] = time.time()
    QtCore.QTimer.singleShot(int(TIMEOUT_S * 1000), on_watchdog)
    run()


# Start after the event loop is running, not at import time.
QtCore.QTimer.singleShot(1500, start)
