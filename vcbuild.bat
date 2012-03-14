@echo off

cd %~dp0

if /i "%1"=="help" goto help
if /i "%1"=="--help" goto help
if /i "%1"=="-help" goto help
if /i "%1"=="/help" goto help
if /i "%1"=="?" goto help
if /i "%1"=="-?" goto help
if /i "%1"=="--?" goto help
if /i "%1"=="/?" goto help

@rem Process arguments.
set config=Debug
set target=Build
set target_arch=ia32
set noprojgen=
set nobuild=

:next-arg
if "%1"=="" goto args-done
if /i "%1"=="debug"         set config=Debug&goto arg-ok
if /i "%1"=="release"       set config=Release&goto arg-ok
if /i "%1"=="clean"         set target=Clean&goto arg-ok
if /i "%1"=="ia32"          set target_arch=ia32&goto arg-ok
if /i "%1"=="x86"           set target_arch=ia32&goto arg-ok
if /i "%1"=="x64"           set target_arch=x64&goto arg-ok
if /i "%1"=="noprojgen"     set noprojgen=1&goto arg-ok
if /i "%1"=="nobuild"       set nobuild=1&goto arg-ok

echo Warning: ignoring invalid command line option `%1`.

:arg-ok
shift
goto next-arg
:args-done

:project-gen
@rem Skip project generation if requested.
if defined noprojgen goto msbuild

@rem Generate the VS project.
if exist build\gyp goto have_gyp
if not exist build mkdir build
echo git clone https://github.com/martine/gyp.git build/gyp
call git clone https://github.com/martine/gyp.git build/gyp
if errorlevel 1 goto gyp_install_failed
goto have_gyp

:gyp_install_failed
echo Failed to download gyp. Make sure you have git installed, or
echo manually install gyp into %~dp0build\gyp.
goto exit

:have_gyp
call build\gyp\gyp.bat smjs.gyp -f msvs -G msvs_version=2010 --depth=. -Dtarget_arch=%target_arch% -Dlibrary=static_library
if errorlevel 1 goto create-msvs-files-failed
if not exist smjs.sln goto create-msvs-files-failed
echo Project files generated.

:msbuild
@rem Skip project generation if requested.
if defined nobuild goto run

@rem Bail out early if not running in VS build env.
if defined VCINSTALLDIR goto msbuild-found
if not defined VS100COMNTOOLS goto msbuild-not-found
if not exist "%VS100COMNTOOLS%\..\..\vc\vcvarsall.bat" goto msbuild-not-found
call "%VS100COMNTOOLS%\..\..\vc\vcvarsall.bat"
if not defined VCINSTALLDIR goto msbuild-not-found
goto msbuild-found

:msbuild-not-found
echo Build skipped. To build, this file needs to run from VS cmd prompt.
goto run

:msbuild-found
@rem Build the sln with msbuild.
msbuild smjs.sln /m /t:%target% /p:Configuration=%config% /clp:NoSummary;NoItemAndPropertyList;Verbosity=minimal /nologo
if errorlevel 1 goto exit

:run
@rem Nothing to run yet
goto exit

:create-msvs-files-failed
echo Failed to create vc project files.
goto exit

:help
echo vcbuild.bat [debug/release] [clean] [noprojgen] [nobuild]
echo Examples:
echo   vcbuild.bat        : Build debug build.
echo   vcbuild.bat nobuild: Generate visual studio project, don't build.
echo   vcbuild.bat release: Build release build.
goto exit

:exit
