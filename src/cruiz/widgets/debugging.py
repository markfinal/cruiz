#!/usr/bin/env python3

"""
Widget debugging
"""

from __future__ import annotations

import typing

from qtpy import QtCore, QtWidgets

if typing.TYPE_CHECKING:
    import logging


def _widget_window_flags_to_string(widget: QtWidgets.QWidget) -> str:
    flags = widget.windowFlags()
    text = ""
    # window type
    window_type = flags & QtCore.Qt.WindowType.WindowType_Mask
    if window_type == QtCore.Qt.WindowType.Window:
        text += "Window"
    if window_type == QtCore.Qt.WindowType.Dialog:
        text += "Dialog"
    if window_type == QtCore.Qt.WindowType.Sheet:
        text += "Sheet"
    if window_type == QtCore.Qt.WindowType.Drawer:
        text += "Drawer"
    if window_type == QtCore.Qt.WindowType.Popup:
        text += "Popup"
    if window_type == QtCore.Qt.WindowType.Tool:
        text += "Tool"
    if window_type == QtCore.Qt.WindowType.ToolTip:
        text += "ToolTip"
    if window_type == QtCore.Qt.WindowType.SplashScreen:
        text += "SplashScreen"
    if window_type == QtCore.Qt.WindowType.Desktop:
        text += "Desktop"
    if window_type == QtCore.Qt.WindowType.SubWindow:
        text += "SubWindow"
    if window_type == QtCore.Qt.WindowType.ForeignWindow:
        text += "ForeignWindow"
    if window_type == QtCore.Qt.WindowType.CoverWindow:
        text += "CoverWindow"
    # flags
    if flags & QtCore.Qt.WindowType.MSWindowsFixedSizeDialogHint:
        text += ":MSWindowsFixedSizeDialogHint"
    if flags & QtCore.Qt.WindowType.MSWindowsOwnDC:
        text += ":MSWindowsOwnDC"
    if flags & QtCore.Qt.WindowType.BypassWindowManagerHint:
        text += ":BypassWindowManagerHint"
    if flags & QtCore.Qt.WindowType.X11BypassWindowManagerHint:
        text += ":X11BypassWindowManagerHint"
    if flags & QtCore.Qt.WindowType.FramelessWindowHint:
        text += ":FramelessWindowHint"
    if flags & QtCore.Qt.WindowType.NoDropShadowWindowHint:
        text += ":NoDropShadowWindowHint"
    if flags & QtCore.Qt.WindowType.CustomizeWindowHint:
        text += ":CustomizeWindowHint"
    if flags & QtCore.Qt.WindowType.WindowTitleHint:
        text += ":WindowTitleHint"
    if flags & QtCore.Qt.WindowType.WindowSystemMenuHint:
        text += ":WindowSystemMenuHint"
    if flags & QtCore.Qt.WindowType.WindowMinimizeButtonHint:
        text += ":WindowMinimizeButtonHint"
    if flags & QtCore.Qt.WindowType.WindowMaximizeButtonHint:
        text += ":WindowMaximizeButtonHint"
    if flags & QtCore.Qt.WindowType.WindowMinMaxButtonsHint:
        text += ":WindowMinMaxButtonsHint"
    if flags & QtCore.Qt.WindowType.WindowCloseButtonHint:
        text += ":WindowCloseButtonHint"
    if flags & QtCore.Qt.WindowType.WindowContextHelpButtonHint:
        text += ":WindowContextHelpButtonHint"
    if flags & QtCore.Qt.WindowType.MacWindowToolBarButtonHint:
        text += ":MacWindowToolBarButtonHint"
    if flags & QtCore.Qt.WindowType.WindowFullscreenButtonHint:
        text += ":WindowFullscreenButtonHint"
    if flags & QtCore.Qt.WindowType.BypassGraphicsProxyWidget:
        text += ":BypassGraphicsProxyWidget"
    if flags & QtCore.Qt.WindowType.WindowShadeButtonHint:
        text += ":WindowShadeButtonHint"
    if flags & QtCore.Qt.WindowType.WindowStaysOnTopHint:
        text += ":WindowStaysOnTopHint"
    if flags & QtCore.Qt.WindowType.WindowStaysOnBottomHint:
        text += ":WindowStaysOnBottomHint"
    if flags & QtCore.Qt.WindowType.WindowTransparentForInput:
        text += ":WindowTransparentForInput"
    if flags & QtCore.Qt.WindowType.WindowOverridesSystemGestures:
        text += ":WindowOverridesSystemGestures"
    if flags & QtCore.Qt.WindowType.WindowDoesNotAcceptFocus:
        text += ":WindowDoesNotAcceptFocus"
    if flags & QtCore.Qt.WindowType.MaximizeUsingFullscreenGeometryHint:
        text += ":MaximizeUsingFullscreenGeometryHint"
    return text


def _widget_attributes_to_string(widget: QtWidgets.QWidget) -> str:
    text = "Attrs"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptDrops):
        text += ":WA_AcceptDrops"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_AlwaysShowToolTips):
        text += ":WA_AlwaysShowToolTips"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_CustomWhatsThis):
        text += ":WA_CustomWhatsThis"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose):
        text += ":WA_DeleteOnClose"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_Disabled):
        text += ":WA_Disabled"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_DontShowOnScreen):
        text += ":WA_DontShowOnScreen"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_ForceDisabled):
        text += ":WA_ForceDisabled"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_ForceUpdatesDisabled):
        text += ":WA_ForceUpdatesDisabled"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_Hover):
        text += ":WA_Hover"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_InputMethodEnabled):
        text += ":WA_InputMethodEnabled"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_KeyboardFocusChange):
        text += ":WA_KeyboardFocusChange"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_KeyCompression):
        text += ":WA_KeyCompression"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_LayoutOnEntireRect):
        text += ":WA_LayoutOnEntireRect"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_LayoutUsesWidgetRect):
        text += ":WA_LayoutUsesWidgetRect"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_MacOpaqueSizeGrip):
        text += ":WA_MacOpaqueSizeGrip"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_MacShowFocusRect):
        text += ":WA_MacShowFocusRect"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_MacNormalSize):
        text += ":WA_MacNormalSize"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_MacSmallSize):
        text += ":WA_MacSmallSize"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_MacMiniSize):
        text += ":WA_MacMiniSize"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_Mapped):
        text += ":WA_Mapped"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_MouseNoMask):
        text += ":WA_MouseNoMask"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_MouseTracking):
        text += ":WA_MouseTracking"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_Moved):
        text += ":WA_Moved"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_NoChildEventsForParent):
        text += ":WA_NoChildEventsForParent"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_NoChildEventsFromChildren):
        text += ":WA_NoChildEventsFromChildren"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_NoMouseReplay):
        text += ":WA_NoMouseReplay"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_NoMousePropagation):
        text += ":WA_NoMousePropagation"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents):
        text += ":WA_TransparentForMouseEvents"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground):
        text += ":WA_NoSystemBackground"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_OpaquePaintEvent):
        text += ":WA_OpaquePaintEvent"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_OutsideWSRange):
        text += ":WA_OutsideWSRange"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_PaintOnScreen):
        text += ":WA_PaintOnScreen"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_PaintUnclipped):
        text += ":WA_PaintUnclipped"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_PendingMoveEvent):
        text += ":WA_PendingMoveEvent"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_PendingResizeEvent):
        text += ":WA_PendingResizeEvent"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_QuitOnClose):
        text += ":WA_QuitOnClose"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_Resized):
        text += ":WA_Resized"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_RightToLeft):
        text += ":WA_RightToLeft"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_SetCursor):
        text += ":WA_SetCursor"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_SetFont):
        text += ":WA_SetFont"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_SetPalette):
        text += ":WA_SetPalette"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_SetStyle):
        text += ":WA_SetStyle"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_ShowModal):
        text += ":WA_ShowModal"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_StaticContents):
        text += ":WA_StaticContents"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_StyleSheet):
        text += ":WA_StyleSheet"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_StyleSheetTarget):
        text += ":WA_StyleSheetTarget"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_TabletTracking):
        text += ":WA_TabletTracking"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground):
        text += ":WA_TranslucentBackground"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_UnderMouse):
        text += ":WA_UnderMouse"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_UpdatesDisabled):
        text += ":WA_UpdatesDisabled"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_WindowModified):
        text += ":WA_WindowModified"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_WindowPropagation):
        text += ":WA_WindowPropagation"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow):
        text += ":WA_MacAlwaysShowToolWindow"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_SetLocale):
        text += ":WA_SetLocale"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground):
        text += ":WA_StyledBackground"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating):
        text += ":WA_ShowWithoutActivating"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_NativeWindow):
        text += ":WA_NativeWindow"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_DontCreateNativeAncestors):
        text += ":WA_DontCreateNativeAncestors"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypeDesktop):
        text += ":WA_X11NetWmWindowTypeDesktop"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypeDock):
        text += ":WA_X11NetWmWindowTypeDock"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypeToolBar):
        text += ":WA_X11NetWmWindowTypeToolBar"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypeMenu):
        text += ":WA_X11NetWmWindowTypeMenu"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypeUtility):
        text += ":WA_X11NetWmWindowTypeUtility"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypeSplash):
        text += ":WA_X11NetWmWindowTypeSplash"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypeDialog):
        text += ":WA_X11NetWmWindowTypeDialog"
    if widget.testAttribute(
        QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypeDropDownMenu
    ):
        text += ":WA_X11NetWmWindowTypeDropDownMenu"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypePopupMenu):
        text += ":WA_X11NetWmWindowTypePopupMenu"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypeToolTip):
        text += ":WA_X11NetWmWindowTypeToolTip"
    if widget.testAttribute(
        QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypeNotification
    ):
        text += ":WA_X11NetWmWindowTypeNotification"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypeCombo):
        text += ":WA_X11NetWmWindowTypeCombo"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypeDND):
        text += ":WA_X11NetWmWindowTypeDND"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents):
        text += ":WA_AcceptTouchEvents"
    if widget.testAttribute(
        QtCore.Qt.WidgetAttribute.WA_TouchPadAcceptSingleTouchEvents
    ):
        text += ":WA_TouchPadAcceptSingleTouchEvents"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_X11DoNotAcceptFocus):
        text += ":WA_X11DoNotAcceptFocus"
    if widget.testAttribute(QtCore.Qt.WidgetAttribute.WA_AlwaysStackOnTop):
        text += ":WA_AlwaysStackOnTop"
    if widget.testAttribute(
        QtCore.Qt.WidgetAttribute.WA_ContentsMarginsRespectsSafeArea
    ):
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
