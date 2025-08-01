@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%1" == "" (
	echo Please specify a build target.
	echo For example, run 'make html' to build the documentation.
	exit /b 1
)

set SPHINXBUILD=sphinx-build
set SOURCEDIR=source
set BUILDDIR=build

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

popd
