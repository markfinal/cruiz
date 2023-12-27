#!/usr/bin/env python3

"""
Widget debugging
"""

import logging

from qtpy import QtCore, QtWidgets


def _widget_window_flags_to_string(widget: QtWidgets.QWidget) -> str:
    flags = widget.windowFlags()
    text = ""
    # window type
    window_type = flags & QtCore.Qt.WindowType_Mask
    if window_type == QtCore.Qt.Window:
        text += "Window"
    if window_type == QtCore.Qt.Dialog:
        text += "Dialog"
    if window_type == QtCore.Qt.Sheet:
        text += "Sheet"
    if window_type == QtCore.Qt.Drawer:
        text += "Drawer"
    if window_type == QtCore.Qt.Popup:
        text += "Popup"
    if window_type == QtCore.Qt.Tool:
        text += "Tool"
    if window_type == QtCore.Qt.ToolTip:
        text += "ToolTip"
    if window_type == QtCore.Qt.SplashScreen:
        text += "SplashScreen"
    if window_type == QtCore.Qt.Desktop:
        text += "Desktop"
    if window_type == QtCore.Qt.SubWindow:
        text += "SubWindow"
    if window_type == QtCore.Qt.ForeignWindow:
        text += "ForeignWindow"
    if window_type == QtCore.Qt.CoverWindow:
        text += "CoverWindow"
    # flags
    if flags & QtCore.Qt.MSWindowsFixedSizeDialogHint:
        text += ":MSWindowsFixedSizeDialogHint"
    if flags & QtCore.Qt.MSWindowsOwnDC:
        text += ":MSWindowsOwnDC"
    if flags & QtCore.Qt.BypassWindowManagerHint:
        text += ":BypassWindowManagerHint"
    if flags & QtCore.Qt.X11BypassWindowManagerHint:
        text += ":X11BypassWindowManagerHint"
    if flags & QtCore.Qt.FramelessWindowHint:
        text += ":FramelessWindowHint"
    if flags & QtCore.Qt.NoDropShadowWindowHint:
        text += ":NoDropShadowWindowHint"
    if flags & QtCore.Qt.CustomizeWindowHint:
        text += ":CustomizeWindowHint"
    if flags & QtCore.Qt.WindowTitleHint:
        text += ":WindowTitleHint"
    if flags & QtCore.Qt.WindowSystemMenuHint:
        text += ":WindowSystemMenuHint"
    if flags & QtCore.Qt.WindowMinimizeButtonHint:
        text += ":WindowMinimizeButtonHint"
    if flags & QtCore.Qt.WindowMaximizeButtonHint:
        text += ":WindowMaximizeButtonHint"
    if flags & QtCore.Qt.WindowMinMaxButtonsHint:
        text += ":WindowMinMaxButtonsHint"
    if flags & QtCore.Qt.WindowCloseButtonHint:
        text += ":WindowCloseButtonHint"
    if flags & QtCore.Qt.WindowContextHelpButtonHint:
        text += ":WindowContextHelpButtonHint"
    if flags & QtCore.Qt.MacWindowToolBarButtonHint:
        text += ":MacWindowToolBarButtonHint"
    if flags & QtCore.Qt.WindowFullscreenButtonHint:
        text += ":WindowFullscreenButtonHint"
    if flags & QtCore.Qt.BypassGraphicsProxyWidget:
        text += ":BypassGraphicsProxyWidget"
    if flags & QtCore.Qt.WindowShadeButtonHint:
        text += ":WindowShadeButtonHint"
    if flags & QtCore.Qt.WindowStaysOnTopHint:
        text += ":WindowStaysOnTopHint"
    if flags & QtCore.Qt.WindowStaysOnBottomHint:
        text += ":WindowStaysOnBottomHint"
    if flags & QtCore.Qt.WindowTransparentForInput:
        text += ":WindowTransparentForInput"
    if flags & QtCore.Qt.WindowOverridesSystemGestures:
        text += ":WindowOverridesSystemGestures"
    if flags & QtCore.Qt.WindowDoesNotAcceptFocus:
        text += ":WindowDoesNotAcceptFocus"
    if flags & QtCore.Qt.MaximizeUsingFullscreenGeometryHint:
        text += ":MaximizeUsingFullscreenGeometryHint"
    return text


def _widget_attributes_to_string(widget: QtWidgets.QWidget) -> str:
    text = "Attrs"
    if widget.testAttribute(QtCore.Qt.WA_AcceptDrops):
        text += ":WA_AcceptDrops"
    if widget.testAttribute(QtCore.Qt.WA_AlwaysShowToolTips):
        text += ":WA_AlwaysShowToolTips"
    if widget.testAttribute(QtCore.Qt.WA_CustomWhatsThis):
        text += ":WA_CustomWhatsThis"
    if widget.testAttribute(QtCore.Qt.WA_DeleteOnClose):
        text += ":WA_DeleteOnClose"
    if widget.testAttribute(QtCore.Qt.WA_Disabled):
        text += ":WA_Disabled"
    if widget.testAttribute(QtCore.Qt.WA_DontShowOnScreen):
        text += ":WA_DontShowOnScreen"
    if widget.testAttribute(QtCore.Qt.WA_ForceDisabled):
        text += ":WA_ForceDisabled"
    if widget.testAttribute(QtCore.Qt.WA_ForceUpdatesDisabled):
        text += ":WA_ForceUpdatesDisabled"
    if widget.testAttribute(QtCore.Qt.WA_Hover):
        text += ":WA_Hover"
    if widget.testAttribute(QtCore.Qt.WA_InputMethodEnabled):
        text += ":WA_InputMethodEnabled"
    if widget.testAttribute(QtCore.Qt.WA_KeyboardFocusChange):
        text += ":WA_KeyboardFocusChange"
    if widget.testAttribute(QtCore.Qt.WA_KeyCompression):
        text += ":WA_KeyCompression"
    if widget.testAttribute(QtCore.Qt.WA_LayoutOnEntireRect):
        text += ":WA_LayoutOnEntireRect"
    if widget.testAttribute(QtCore.Qt.WA_LayoutUsesWidgetRect):
        text += ":WA_LayoutUsesWidgetRect"
    if widget.testAttribute(QtCore.Qt.WA_MacOpaqueSizeGrip):
        text += ":WA_MacOpaqueSizeGrip"
    if widget.testAttribute(QtCore.Qt.WA_MacShowFocusRect):
        text += ":WA_MacShowFocusRect"
    if widget.testAttribute(QtCore.Qt.WA_MacNormalSize):
        text += ":WA_MacNormalSize"
    if widget.testAttribute(QtCore.Qt.WA_MacSmallSize):
        text += ":WA_MacSmallSize"
    if widget.testAttribute(QtCore.Qt.WA_MacMiniSize):
        text += ":WA_MacMiniSize"
    if widget.testAttribute(QtCore.Qt.WA_Mapped):
        text += ":WA_Mapped"
    if widget.testAttribute(QtCore.Qt.WA_MouseNoMask):
        text += ":WA_MouseNoMask"
    if widget.testAttribute(QtCore.Qt.WA_MouseTracking):
        text += ":WA_MouseTracking"
    if widget.testAttribute(QtCore.Qt.WA_Moved):
        text += ":WA_Moved"
    if widget.testAttribute(QtCore.Qt.WA_NoChildEventsForParent):
        text += ":WA_NoChildEventsForParent"
    if widget.testAttribute(QtCore.Qt.WA_NoChildEventsFromChildren):
        text += ":WA_NoChildEventsFromChildren"
    if widget.testAttribute(QtCore.Qt.WA_NoMouseReplay):
        text += ":WA_NoMouseReplay"
    if widget.testAttribute(QtCore.Qt.WA_NoMousePropagation):
        text += ":WA_NoMousePropagation"
    if widget.testAttribute(QtCore.Qt.WA_TransparentForMouseEvents):
        text += ":WA_TransparentForMouseEvents"
    if widget.testAttribute(QtCore.Qt.WA_NoSystemBackground):
        text += ":WA_NoSystemBackground"
    if widget.testAttribute(QtCore.Qt.WA_OpaquePaintEvent):
        text += ":WA_OpaquePaintEvent"
    if widget.testAttribute(QtCore.Qt.WA_OutsideWSRange):
        text += ":WA_OutsideWSRange"
    if widget.testAttribute(QtCore.Qt.WA_PaintOnScreen):
        text += ":WA_PaintOnScreen"
    if widget.testAttribute(QtCore.Qt.WA_PaintUnclipped):
        text += ":WA_PaintUnclipped"
    if widget.testAttribute(QtCore.Qt.WA_PendingMoveEvent):
        text += ":WA_PendingMoveEvent"
    if widget.testAttribute(QtCore.Qt.WA_PendingResizeEvent):
        text += ":WA_PendingResizeEvent"
    if widget.testAttribute(QtCore.Qt.WA_QuitOnClose):
        text += ":WA_QuitOnClose"
    if widget.testAttribute(QtCore.Qt.WA_Resized):
        text += ":WA_Resized"
    if widget.testAttribute(QtCore.Qt.WA_RightToLeft):
        text += ":WA_RightToLeft"
    if widget.testAttribute(QtCore.Qt.WA_SetCursor):
        text += ":WA_SetCursor"
    if widget.testAttribute(QtCore.Qt.WA_SetFont):
        text += ":WA_SetFont"
    if widget.testAttribute(QtCore.Qt.WA_SetPalette):
        text += ":WA_SetPalette"
    if widget.testAttribute(QtCore.Qt.WA_SetStyle):
        text += ":WA_SetStyle"
    if widget.testAttribute(QtCore.Qt.WA_ShowModal):
        text += ":WA_ShowModal"
    if widget.testAttribute(QtCore.Qt.WA_StaticContents):
        text += ":WA_StaticContents"
    if widget.testAttribute(QtCore.Qt.WA_StyleSheet):
        text += ":WA_StyleSheet"
    if widget.testAttribute(QtCore.Qt.WA_StyleSheetTarget):
        text += ":WA_StyleSheetTarget"
    if widget.testAttribute(QtCore.Qt.WA_TabletTracking):
        text += ":WA_TabletTracking"
    if widget.testAttribute(QtCore.Qt.WA_TranslucentBackground):
        text += ":WA_TranslucentBackground"
    if widget.testAttribute(QtCore.Qt.WA_UnderMouse):
        text += ":WA_UnderMouse"
    if widget.testAttribute(QtCore.Qt.WA_UpdatesDisabled):
        text += ":WA_UpdatesDisabled"
    if widget.testAttribute(QtCore.Qt.WA_WindowModified):
        text += ":WA_WindowModified"
    if widget.testAttribute(QtCore.Qt.WA_WindowPropagation):
        text += ":WA_WindowPropagation"
    if widget.testAttribute(QtCore.Qt.WA_MacAlwaysShowToolWindow):
        text += ":WA_MacAlwaysShowToolWindow"
    if widget.testAttribute(QtCore.Qt.WA_SetLocale):
        text += ":WA_SetLocale"
    if widget.testAttribute(QtCore.Qt.WA_StyledBackground):
        text += ":WA_StyledBackground"
    if widget.testAttribute(QtCore.Qt.WA_ShowWithoutActivating):
        text += ":WA_ShowWithoutActivating"
    if widget.testAttribute(QtCore.Qt.WA_NativeWindow):
        text += ":WA_NativeWindow"
    if widget.testAttribute(QtCore.Qt.WA_DontCreateNativeAncestors):
        text += ":WA_DontCreateNativeAncestors"
    if widget.testAttribute(QtCore.Qt.WA_X11NetWmWindowTypeDesktop):
        text += ":WA_X11NetWmWindowTypeDesktop"
    if widget.testAttribute(QtCore.Qt.WA_X11NetWmWindowTypeDock):
        text += ":WA_X11NetWmWindowTypeDock"
    if widget.testAttribute(QtCore.Qt.WA_X11NetWmWindowTypeToolBar):
        text += ":WA_X11NetWmWindowTypeToolBar"
    if widget.testAttribute(QtCore.Qt.WA_X11NetWmWindowTypeMenu):
        text += ":WA_X11NetWmWindowTypeMenu"
    if widget.testAttribute(QtCore.Qt.WA_X11NetWmWindowTypeUtility):
        text += ":WA_X11NetWmWindowTypeUtility"
    if widget.testAttribute(QtCore.Qt.WA_X11NetWmWindowTypeSplash):
        text += ":WA_X11NetWmWindowTypeSplash"
    if widget.testAttribute(QtCore.Qt.WA_X11NetWmWindowTypeDialog):
        text += ":WA_X11NetWmWindowTypeDialog"
    if widget.testAttribute(QtCore.Qt.WA_X11NetWmWindowTypeDropDownMenu):
        text += ":WA_X11NetWmWindowTypeDropDownMenu"
    if widget.testAttribute(QtCore.Qt.WA_X11NetWmWindowTypePopupMenu):
        text += ":WA_X11NetWmWindowTypePopupMenu"
    if widget.testAttribute(QtCore.Qt.WA_X11NetWmWindowTypeToolTip):
        text += ":WA_X11NetWmWindowTypeToolTip"
    if widget.testAttribute(QtCore.Qt.WA_X11NetWmWindowTypeNotification):
        text += ":WA_X11NetWmWindowTypeNotification"
    if widget.testAttribute(QtCore.Qt.WA_X11NetWmWindowTypeCombo):
        text += ":WA_X11NetWmWindowTypeCombo"
    if widget.testAttribute(QtCore.Qt.WA_X11NetWmWindowTypeDND):
        text += ":WA_X11NetWmWindowTypeDND"
    if widget.testAttribute(QtCore.Qt.WA_AcceptTouchEvents):
        text += ":WA_AcceptTouchEvents"
    if widget.testAttribute(QtCore.Qt.WA_TouchPadAcceptSingleTouchEvents):
        text += ":WA_TouchPadAcceptSingleTouchEvents"
    if widget.testAttribute(QtCore.Qt.WA_X11DoNotAcceptFocus):
        text += ":WA_X11DoNotAcceptFocus"
    if widget.testAttribute(QtCore.Qt.WA_AlwaysStackOnTop):
        text += ":WA_AlwaysStackOnTop"
    if widget.testAttribute(QtCore.Qt.WA_ContentsMarginsRespectsSafeArea):
        text += ":WA_ContentsMarginsRespectsSafeArea"
    return text


def log_created_widget(widget: QtWidgets.QWidget, logger: logging.Logger) -> None:
    """
    Logging a created widget
    """
    logger.debug(
        "+=%d : (%s)(%s)",
        id(widget),
        _widget_window_flags_to_string(widget),
        _widget_attributes_to_string(widget),
    )
