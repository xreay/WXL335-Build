# GameHub Chinese text input investigation — 2026-11-19

## Evidence and version gates
- User on Android: individually committing 输 then 入 works; one commit 输入 appears 入入 in WoW and in the container desktop. Container-internal Unicode copy/paste works; Android system clipboard to game does not.
- R5.2 Windows-side log: WM_CHAR already contains the wrong code point (U+5165). Do not deduplicate legitimate repeated characters.
- Library GameHub_6.3.2.apk SHA256 d73ac65e9f1aea16f416394d710f02719c0f9afdc1faf1609bec13058b29d297; six dex, no libxserver.so or libwinemu.so.
- Public *reference* pcengine 109-8 SHA256 725493a0f7f2cacc8acbb6d9d0b37378aa5aa5ad5c84c5537df236fc2a38514d. Actual device engine version/hash NOT established. Do not apply offsets to another build.

## Static analysis evidence
Actions runs 44469045243, 44470672034, 44470816601, 44470937656, 44471093787, 44471549554 succeeded.
Java UTF-8 byte array -> JNI sendTextEvent -> independent heap copy and queue -> native callback. Per character decoding, keysym conversion, press/release, two 30 ms sleeps. Native missing-symbol fallback searches unused keycodes and can recycle dynamic mappings; writes new symbol and issues mapping update. This supports a mapping lifetime race hypothesis, not proof of actual device event timing.

## Real X11 protocol experiment (Xvfb, separate sender and receiver, XTest)
Observed on 2026-11-19:
- spare keys 248 and 230; mapping width 7
- reused key, receiver processes each char immediately: 01008f93 01005165
- reused key, receiver processes after both events: 01005165 01005165
- separate keys, receiver processes after both events: 01008f93 01005165
- all three expected conditions passed.
This reproduces the symptom on X11, not the proprietary Android engine itself.

## Preferred remediation contract
1. Native engine should submit immutable whole UTF-8 text to the guest text channel or X11 selection/clipboard protocol, with one explicit paste transaction when an eligible input target is focused. Do not blindly paste or submit chat.
2. Alternative for key-event fallback: preserve mappings for the lifetime of outstanding events; avoid recycling during a batch; use nonblocking scheduling and actual guest-side acknowledgement, not time-only sleeps. Address finite key space, focus changes, cancellation, composing/commit replacement, modifiers, repeated characters and clipboard ownership.
3. Validate exact engine version and supported deployment path before patching. No verified stock-engine replacement path, no patched APK or SO produced. Do not remove signature/integrity checks.
4. Regression: distinct and repeated Han characters, mixed ASCII and Chinese, long phrases beyond spare key count, rapid consecutive commits, cancellation, focus changes, and container/game comparisons. The vendor must fix or supply a supported import/extension route for the native component.
