# Network Configuration Keyboard - Bug Report

**Date:** Generated Report  
**Component:** Network Configuration Dialog - TouchKeyboard Integration  
**File:** `src/gui/main_window.py`  
**Lines:** 1593-1633

---

## Executive Summary

The network configuration dialog has **critical bugs** in its keyboard implementation that prevent input fields from receiving focus when clicked. The implementation uses a problematic approach of directly overriding `mousePressEvent` handlers, which breaks Qt's focus management. This differs from the SIP settings dialog which uses proper event filters.

**Severity:** 🔴 **CRITICAL** - Input fields cannot receive focus, making the keyboard unusable

---

## Critical Issues

### 🔴 CRITICAL-001: Input Fields Cannot Receive Focus

**File:** `src/gui/main_window.py`  
**Lines:** 1630-1633  
**Severity:** Critical

**Issue:**
```python
# Connect input fields to show keyboard
ip_input.mousePressEvent = lambda event: show_keyboard_for_input(ip_input)
subnet_input.mousePressEvent = lambda event: show_keyboard_for_input(subnet_input)
gateway_input.mousePressEvent = lambda event: show_keyboard_for_input(gateway_input)
dns_input.mousePressEvent = lambda event: show_keyboard_for_input(dns_input)
```

**Problem:**
Directly overriding `mousePressEvent` with a lambda that doesn't call the original handler **breaks Qt's focus management**. When a user clicks on an input field:

1. ❌ The field does NOT receive focus
2. ❌ The cursor does NOT appear in the field
3. ❌ The field cannot be edited normally
4. ❌ Keyboard input won't work because the field isn't focused

**Root Cause:**
The lambda function replaces the entire `mousePressEvent` handler. Qt's default `mousePressEvent` for `QLineEdit` calls `setFocus()` internally - but this is bypassed entirely.

**Impact:**
- **User cannot click to focus input fields**
- Keyboard typing may not work (field not focused)
- Poor user experience - fields appear clickable but don't respond properly
- Inconsistent behavior compared to SIP settings dialog

**Current Code:**
```python
def show_keyboard_for_input(input_field):
    """Show keyboard when input field is clicked"""
    active_input[0] = input_field
    # Keyboard is always visible in gray area
    # ❌ MISSING: input_field.setFocus() is never called!
```

---

### 🔴 CRITICAL-002: Missing Focus Call in Keyboard Handler

**File:** `src/gui/main_window.py`  
**Lines:** 1596-1604  
**Severity:** Critical

**Issue:**
The `show_keyboard_for_input()` function doesn't call `setFocus()` on the input field, so even if the event handler worked, the field wouldn't receive focus.

**Current Code:**
```python
def show_keyboard_for_input(input_field):
    """Show keyboard when input field is clicked"""
    active_input[0] = input_field
    # Keyboard is always visible in gray area
    # ❌ Problem: input_field.setFocus() is never called
```

**Impact:**
- Field won't get focus even if mouse event is handled correctly
- Cursor won't appear
- Field won't be editable

---

## Medium Severity Issues

### 🟡 MEDIUM-001: Inconsistent Implementation Pattern

**File:** `src/gui/main_window.py`  
**Severity:** Medium

**Issue:**
The network configuration dialog uses a **different and problematic approach** compared to the SIP settings dialog:

- **SIP Settings** (correct): Uses `installEventFilter()` and `eventFilter()` method
- **Network Config** (incorrect): Directly overrides `mousePressEvent` with lambda

**Comparison:**

**SIP Settings (GOOD):**
```python
# In SIPSettingsDialog.__init__()
self.input_fields.append(self.server_input)
self.server_input.installEventFilter(self)

# Later in class:
def eventFilter(self, obj, event):
    if event.type() == QEvent.FocusIn:
        if isinstance(obj, QLineEdit):
            self.active_input = obj
            self._show_keyboard()
    # ... proper handling
    return super().eventFilter(obj, event)
```

**Network Config (BAD):**
```python
# Direct override - breaks focus handling
ip_input.mousePressEvent = lambda event: show_keyboard_for_input(ip_input)
```

**Impact:**
- Code inconsistency across dialogs
- Maintenance burden (two different patterns)
- Network config doesn't work properly while SIP config does

---

### 🟡 MEDIUM-002: Missing Visual Feedback for Active Field

**File:** `src/gui/main_window.py`  
**Lines:** 1481-1531  
**Severity:** Medium

**Issue:**
Unlike the SIP settings dialog which highlights the active input field with a border color change, the network configuration dialog doesn't provide visual feedback when a field is selected.

**SIP Settings (has visual feedback):**
```python
# Active field gets highlighted border
border: 2px solid #00d4ff;  # Cyan border when focused
```

**Network Config (no visual feedback):**
```python
# Static style - no focus indication
border: 2px solid #00d4ff;  # Always cyan, no change on focus
```

**Impact:**
- User can't tell which field is active
- Poor user experience
- Confusion about which field will receive keyboard input

---

### 🟡 MEDIUM-003: Backspace on Empty String (Edge Case)

**File:** `src/gui/main_window.py`  
**Line:** 1622  
**Severity:** Low (safely handled but not ideal)

**Issue:**
```python
elif key == '\b':
    # Backspace
    current_text = active_input[0].text()
    active_input[0].setText(current_text[:-1])  # Works but could be clearer
```

**Analysis:**
While `[:-1]` on an empty string returns an empty string (safe), it's not immediately clear this is intentional. Better to check for empty string explicitly.

**Impact:**
- Low - code works correctly but could be more readable
- Minor performance impact (unnecessary operation on empty string)

**Recommendation:**
```python
elif key == '\b':
    # Backspace
    if active_input[0] and len(active_input[0].text()) > 0:
        current_text = active_input[0].text()
        active_input[0].setText(current_text[:-1])
```

---

## Recommended Fixes

### Fix 1: Use Event Filter Pattern (Like SIP Settings)

**Recommended Solution:**
Replace the direct `mousePressEvent` override with proper event filtering, matching the SIP settings implementation.

**Implementation:**

```python
def _show_network_settings(self, parent_dialog):
    """Show network configuration dialog"""
    # ... existing code ...
    
    # Create a custom event filter class
    class NetworkConfigEventFilter(QObject):
        def __init__(self, parent, active_input_ref, keyboard_widget):
            super().__init__(parent)
            self.active_input_ref = active_input_ref
            self.keyboard = keyboard_widget
            self.network_dialog = parent
        
        def eventFilter(self, obj, event):
            if event.type() == QEvent.FocusIn:
                if isinstance(obj, QLineEdit):
                    self.active_input_ref[0] = obj
                    # Highlight active field
                    obj.setStyleSheet("""
                        QLineEdit {
                            background-color: #2d2d2d;
                            color: white;
                            border: 3px solid #00d4ff;  /* Thicker, brighter border */
                            border-radius: 6px;
                            padding: 5px;
                            font-size: 14pt;
                        }
                    """)
                    # Keyboard is always visible
            elif event.type() == QEvent.FocusOut:
                if isinstance(obj, QLineEdit):
                    # Reset field style
                    obj.setStyleSheet("""
                        QLineEdit {
                            background-color: #2d2d2d;
                            color: white;
                            border: 2px solid #00d4ff;  /* Normal border */
                            border-radius: 6px;
                            padding: 5px;
                            font-size: 14pt;
                        }
                    """)
            return super().eventFilter(obj, event)
    
    # Create event filter instance
    event_filter = NetworkConfigEventFilter(network_dialog, active_input, keyboard)
    
    # Install event filter on input fields (NOT override mousePressEvent)
    ip_input.installEventFilter(event_filter)
    subnet_input.installEventFilter(event_filter)
    gateway_input.installEventFilter(event_filter)
    dns_input.installEventFilter(event_filter)
    
    # Remove the problematic lines:
    # ❌ DELETE: ip_input.mousePressEvent = lambda event: show_keyboard_for_input(ip_input)
    # ❌ DELETE: subnet_input.mousePressEvent = lambda event: show_keyboard_for_input(subnet_input)
    # ❌ DELETE: gateway_input.mousePressEvent = lambda event: show_keyboard_for_input(gateway_input)
    # ❌ DELETE: dns_input.mousePressEvent = lambda event: show_keyboard_for_input(dns_input)
```

---

### Fix 2: Add Focus Management to Keyboard Handler

**Additional Fix:**
Ensure the keyboard handler properly manages focus:

```python
def on_key_pressed(key):
    """Handle keyboard key press"""
    if active_input[0] is None:
        return
    
    # Ensure field has focus before typing
    if not active_input[0].hasFocus():
        active_input[0].setFocus()
    
    if key == 'DONE':
        active_input[0].clearFocus()  # Remove focus when done
        hide_keyboard()
    elif key == 'CANCEL':
        active_input[0].clear()  # Restore original value
        active_input[0].clearFocus()
        hide_keyboard()
    # ... rest of handler
```

---

### Fix 3: Improve Backspace Handling

**Code Improvement:**
```python
elif key == '\b':
    # Backspace
    if active_input[0] and len(active_input[0].text()) > 0:
        current_text = active_input[0].text()
        active_input[0].setText(current_text[:-1])
```

---

## Testing Checklist

After implementing fixes, test the following:

- [ ] Click on IP address field - field should receive focus and cursor appears
- [ ] Type on keyboard - characters should appear in focused field
- [ ] Click on different fields - focus should switch properly
- [ ] Backspace works on empty field (no crash)
- [ ] Backspace works on non-empty field (removes last character)
- [ ] Clear button clears the active field
- [ ] Cancel button clears field and removes focus
- [ ] Done button removes focus from field
- [ ] Visual feedback shows which field is active (border highlight)
- [ ] Switching between DHCP/Manual mode doesn't break keyboard

---

## Additional Notes

### Why Event Filters Are Better

1. **Preserves Qt's Default Behavior**: Event filters intercept events but still allow Qt to handle focus, selection, etc.
2. **Non-Destructive**: Doesn't replace the entire event handler
3. **More Flexible**: Can handle multiple event types (FocusIn, FocusOut, etc.)
4. **Consistent Pattern**: Matches SIP settings implementation

### Why Direct Override Fails

1. **Breaks Focus**: Qt's `QLineEdit.mousePressEvent()` calls `setFocus()` internally - overriding it removes this
2. **Breaks Selection**: Mouse click selection behavior is lost
3. **Hard to Maintain**: Lambda functions are harder to debug
4. **Inconsistent**: Different pattern than rest of codebase

---

## Priority

**Priority:** 🔴 **URGENT** - This is a critical user-facing bug that prevents the network configuration dialog from functioning properly.

**Recommendation:** Fix immediately before production deployment.

---

**Report Generated:** Manual Code Review  
**Files Analyzed:** `src/gui/main_window.py` (Network Configuration Dialog)  
**Comparison Reference:** `src/gui/main_window.py` (SIP Settings Dialog - Working Implementation)
