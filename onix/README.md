# ONIX XML
Script to generate Onix XML format from SciELO Books metadata

Version: 3.0

http://www.editeur.org/12/About-Release-3.0/


# Requirements

- lxml==4.5.2
- iso-639==0.4.5
- requests==2.24.0
- PyInstaller==4.0


# Download onix.exe for Windows

|Link     | Windows | Type  |
| --------|---------|-------|
|[Download](https://github.com/scieloorg/scielobooks_exports/raw/master/onix/dist/onix.zip)  | 64-bit x64| .zip  |

For Windows platform the publishers.json file should be in UTF-8 Unicode and CRFL line terminators.

`$ file publishers.json`

`publishers.json: UTF-8 Unicode text, with CRLF line terminators`
