@echo off
:: Initialize conda for batch file usage
call "C:\Users\yshao\AppData\Local\anaconda3\Scripts\activate.bat"

:: Change to the TDMS viewer directory
cd /d "C:\CORE\Modules\yu-code\TDMS viewer"

:: Activate the Anaconda environment
call conda activate conda_lib_srn

:: Launch the Python script using the full path to Python in the conda environment
call "C:\Users\yshao\AppData\Local\anaconda3\envs\conda_lib_srn\python.exe" tdms_viewer.py

:: Keep the window open if there's an error
if errorlevel 1 pause

:: Deactivate the conda environment when done
call conda deactivate