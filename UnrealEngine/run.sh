#!/bin/bash

UE4_EDITOR_PATH="$HOME/dependencies/UnrealEngine/Engine/Binaries/Linux/UE4Editor"

export UE4_SLATE_APPLICATION_SCALE=2.0         
export GDK_BACKEND=x11                         
export QT_QPA_PLATFORM=xcb                     
export SDL_VIDEODRIVER=x11                     

"$UE4_EDITOR_PATH" "$@"
