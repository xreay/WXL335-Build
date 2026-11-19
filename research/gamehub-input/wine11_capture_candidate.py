#!/usr/bin/env python3
"""Experimental source-only patch for Wine 11.0. Not for stock GameHub binary replacement.
Default disabled; WXL_X11_UNICODE_CAPTURE=1 enables BMP Han packet capture.
Cannot repair corruption before the first X11 lookup. No build/device validation.
"""
from pathlib import Path
import sys
root = Path(sys.argv[1])
replacements = [
  [
    "dlls/winex11.drv/keyboard.c",
    "#include <ctype.h>\n",
    "#include <ctype.h>\n#include <stdlib.h>\n"
  ],
  [
    "dlls/winex11.drv/keyboard.c",
    "    pthread_mutex_lock( &kbd_mutex );\n\n    /* If XKB extensions are used,",
    "    /* WXL: opt-in capture of a Han keysym before later ToUnicodeEx lookup.\n     * Experimental: cannot recover a symbol already corrupted by X11.\n     * Preserve XIM commits, shortcuts, ASCII and ordinary keyboard input.\n     */\n    {\n        const char *enabled = getenv(\"WXL_X11_UNICODE_CAPTURE\");\n        struct x11drv_thread_data *td = x11drv_thread_data();\n        unsigned int cp = keysym & 0xffffff;\n        if (enabled && !strcmp(enabled, \"1\") && td && hwnd && event->keycode < 256)\n        {\n            if (event->type == KeyRelease && td->wxl_unicode_down[event->keycode])\n            {\n                td->wxl_unicode_down[event->keycode] = FALSE;\n                if (buf != Str) free(Str);\n                return TRUE;\n            }\n            if (event->type == KeyPress)\n            {\n                td->wxl_unicode_down[event->keycode] = FALSE;\n                if ((keysym & 0xff000000) == 0x01000000 &&\n                    ((cp >= 0x3400 && cp <= 0x4dbf) ||\n                     (cp >= 0x4e00 && cp <= 0x9fff) ||\n                     (cp >= 0xf900 && cp <= 0xfaff)) &&\n                    !(event->state & (ControlMask | Mod1Mask | Mod4Mask | Mod5Mask)))\n                {\n                    td->wxl_unicode_down[event->keycode] = TRUE;\n                    X11DRV_send_keyboard_input(hwnd, 0, cp, KEYEVENTF_UNICODE, event_time);\n                    X11DRV_send_keyboard_input(hwnd, 0, cp, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, event_time);\n                    if (buf != Str) free(Str);\n                    return TRUE;\n                }\n            }\n        }\n    }\n\n    pthread_mutex_lock( &kbd_mutex );\n\n    /* If XKB extensions are used,"
  ],
  [
    "dlls/winex11.drv/x11drv.h",
    "    Display *display;\n    XEvent  *current_event;",
    "    BOOL wxl_unicode_down[256]; /* experimental Unicode packet release tracking */\n    Display *display;\n    XEvent  *current_event;"
  ]
]
files = {}
for name, old, new in replacements:
    p = root / name
    s = files.get(p)
    if s is None:
        s = p.read_text(encoding="utf-8")
    if s.count(old) != 1:
        raise SystemExit("Source mismatch or patch already applied: " + name)
    files[p] = s.replace(old,new,1)
for p,s in files.items():
    p.write_text(s, encoding="utf-8")
print("Applied experimental Wine 11.0 source patch; compile and test against matching tree.")
