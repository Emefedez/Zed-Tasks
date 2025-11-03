# -*- coding: utf-8 -*-
# DecompileAndReport.py
# Exporta decompilacion consolidada + por funcion en subcarpeta + report

from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
from ghidra.program.model.listing import CodeUnit
import json, os, time, codecs

def _parse_kv(args):
    m = {}
    i = 0
    while i < len(args):
        k = args[i]
        v = args[i+1] if i+1 < len(args) else ""
        m[k] = v
        i += 2
    return m

def _safe_filename(s):
    bad = r'\/:*?"<>|'
    out = []
    for ch in str(s):
        out.append('_' if ch in bad else ch)
    return ''.join(out)

args = getScriptArgs()
kv = _parse_kv(args)

out_dir = kv.get("outDir", "")
project_path = kv.get("projectPath", "")
program_path = kv.get("programPath", "")

if not out_dir:
    out_dir = os.path.join(os.path.expanduser("~"), "Decompiled")

if not os.path.isdir(out_dir):
    os.makedirs(out_dir)

# Carpeta para funciones individuales
functions_dir = os.path.join(out_dir, "functions")
if not os.path.isdir(functions_dir):
    os.makedirs(functions_dir)

# Limpia archivos antiguos
try:
    for name in os.listdir(functions_dir):
        if name.endswith(".c"):
            try:
                os.remove(os.path.join(functions_dir, name))
            except:
                pass
except:
    pass

# Eliminar all_decompiled.c anterior si existe
all_decompiled_path = os.path.join(out_dir, "all_decompiled.c")
if os.path.isfile(all_decompiled_path):
    try:
        os.remove(all_decompiled_path)
    except:
        pass

ifc = DecompInterface()
ifc.openProgram(currentProgram)
monitor = ConsoleTaskMonitor()

fm = currentProgram.getFunctionManager()
func_iter = fm.getFunctions(True)

functions = []
listing = currentProgram.getListing()
all_code = []

def _collect_callers(func):
    callers = set()
    try:
        refs = getReferencesTo(func.getEntryPoint())
        for r in refs:
            try:
                if r.getReferenceType().isCall():
                    caller_f = getFunctionContaining(r.getFromAddress())
                    if caller_f:
                        callers.add(caller_f.getName())
            except:
                pass
    except:
        pass
    return sorted(list(callers))

def _collect_callees(func):
    callees = set()
    try:
        body = func.getBody()
        it = listing.getCodeUnits(body, True)
        while it.hasNext():
            cu = it.next()
            try:
                for rf in cu.getReferencesFrom():
                    try:
                        if rf.getReferenceType().isCall():
                            callee = getFunctionAt(rf.getToAddress())
                            if not callee:
                                callee = getFunctionContaining(rf.getToAddress())
                            if callee:
                                callees.add(callee.getName())
                    except:
                        pass
            except:
                pass
    except:
        pass
    return sorted(list(callees))

idx = 0
while func_iter.hasNext():
    f = func_iter.next()
    idx += 1

    # Decompilar funcion
    code_text = ""
    try:
        res = ifc.decompileFunction(f, 60, monitor)
        if res and res.getDecompiledFunction():
            code_text = res.getDecompiledFunction().getC()
    except:
        code_text = ""

    if not code_text:
        code_text = "/* no decompilation available */"

    # Agregar al archivo consolidado
    all_code.append("/* ============================================ */")
    all_code.append("/* Function: %s @ %s */" % (f.getName(), str(f.getEntryPoint())))
    all_code.append("/* Signature: %s */" % f.getSignature().getPrototypeString())
    all_code.append("/* ============================================ */")
    all_code.append(code_text)
    all_code.append("")

    # Guardar decompilacion individual en subcarpeta
    try:
        fn_name = _safe_filename(f.getName())
        entry = _safe_filename(str(f.getEntryPoint()))
        out_name = "%04d_%s_%s.c" % (idx, fn_name, entry)
        with codecs.open(os.path.join(functions_dir, out_name), "w", "utf-8") as w:
            w.write(code_text)
    except:
        pass

    info = {
        "name": f.getName(),
        "entry": str(f.getEntryPoint()),
        "calling_convention": f.getCallingConventionName(),
        "signature": f.getSignature().getPrototypeString(),
        "is_external": bool(f.isExternal()),
        "is_thunk": bool(f.isThunk()),
        "callers": _collect_callers(f),
        "callees": _collect_callees(f),
    }
    functions.append(info)

# Guardar archivo consolidado all_decompiled.c
with codecs.open(all_decompiled_path, "w", "utf-8") as w:
    w.write("/*\n")
    w.write(" * ALL DECOMPILED FUNCTIONS\n")
    w.write(" * Ghidra Project: %s\n" % project_path)
    w.write(" * Program: %s\n" % program_path)
    w.write(" * Generated: %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
    w.write(" * Total Functions: %d\n" % len(functions))
    w.write(" */\n\n")
    w.write("\n".join(all_code))

report = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "ghidra_project_path": project_path,
    "program_path": program_path,
    "output_dir": out_dir,
    "functions_count": len(functions),
    "functions": functions,
}

# Guardar JSON con UTF-8
with codecs.open(os.path.join(out_dir, "report.json"), "w", "utf-8") as w:
    w.write(json.dumps(report, indent=2, ensure_ascii=False))

# Guardar TXT resumen con UTF-8
with codecs.open(os.path.join(out_dir, "report.txt"), "w", "utf-8") as w:
    w.write(u"Ghidra Project: %s\n" % project_path)
    w.write(u"Program Path : %s\n" % program_path)
    w.write(u"Output Dir   : %s\n" % out_dir)
    w.write(u"Functions    : %d\n\n" % len(functions))
    for f in functions:
        w.write(u"- %s @ %s\n" % (f["name"], f["entry"]))
        w.write(u"  Signature: %s\n" % f["signature"])
        w.write(u"  Convention: %s\n" % f["calling_convention"])
        if f["is_external"]:
            w.write(u"  [EXTERNAL]\n")
        if f["is_thunk"]:
            w.write(u"  [THUNK]\n")
        if f["callers"]:
            w.write(u"  Called by: %s\n" % ", ".join(f["callers"]))
        if f["callees"]:
            w.write(u"  Calls: %s\n" % ", ".join(f["callees"]))
        w.write(u"\n")

print("Decompilation complete!")
print("Output directory: " + out_dir.encode('utf-8'))
print("Consolidated file: all_decompiled.c")
print("Individual functions: functions/ subdirectory")
print("Functions processed: %d" % len(functions))
