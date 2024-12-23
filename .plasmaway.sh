#!/bin/bash

export XDG_SESSION_TYPE=wayland
export GDK_BACKEND=wayland

export QT_QPA_PLATFORM=wayland
export CLUTTER_BACKEND=wayland

exec dbus-run-session startplasma-wayland
