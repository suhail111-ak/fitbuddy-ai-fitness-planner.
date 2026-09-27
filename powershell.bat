@echo off
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" (
    "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" %*
) else if exist "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" (
    "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" %*
) else if exist "%SystemRoot%\SysWOW64\WindowsPowerShell\v1.0\powershell.exe" (
    "%SystemRoot%\SysWOW64\WindowsPowerShell\v1.0\powershell.exe" %*
) else (
    echo PowerShell not found, executing via cmd /c
    cmd.exe /c %*
)
