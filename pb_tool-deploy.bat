:: This *.bat is used for correctly invoking the `pb_tool` command so to compile the *.ui files and copy the plugin to the target directory

:: Setting the path for the following bat(s)
SET base_path=C:\Program Files\QGIS 3.4\bin
call "%base_path%\o4w_env.bat"
call "%base_path%\py3_env.bat"
call "%base_path%\qt5_env.bat"

:: Setting the command
SET command=deploy
if not ["%~1"] == [""] (
    SET command=%~1
)

:: Setting the options
SET options=
if not ["%~2"] == [""] (
    SET options=%~2
)

:: Invoking the deployment
pb_tool %command% %options%

