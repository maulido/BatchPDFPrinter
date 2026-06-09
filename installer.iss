[Setup]
AppId={{8B841A11-E6BC-4B4B-B9CA-A5EACBE954F6}
AppName=Batch PDF Printer
AppVersion=1.0.0
AppPublisher=Egogohub
DefaultDirName={autopf}\Batch PDF Printer
DefaultGroupName=Batch PDF Printer
OutputDir=dist
OutputBaseFilename=BatchPDFPrinter-Setup
Compression=lzma2
SolidCompression=yes
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\BatchPDFPrinter.exe
DisableProgramGroupPage=yes
ArchitecturesInstallIn64BitMode=x64

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\BatchPDFPrinter-Portable.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Batch PDF Printer"; Filename: "{app}\BatchPDFPrinter-Portable.exe"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\Batch PDF Printer"; Filename: "{app}\BatchPDFPrinter-Portable.exe"; Tasks: desktopicon; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\BatchPDFPrinter-Portable.exe"; Description: "Launch Batch PDF Printer"; Flags: nowait postinstall skipifsilent
