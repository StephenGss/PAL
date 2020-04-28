@echo off
setlocal enableDelayedExpansion

:launchLoop
REM run Minecraft:
rem call gradlew setupDecompWorkspace
rem call gradlew build
call gradlew runClient
if "!-replaceable!"=="true" (
    goto :launchLoop
)
