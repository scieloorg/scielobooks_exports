# -*- mode: python -*-

block_cipher = None


a = Analysis(['onix.py'],
             pathex=['C:\\Users\\[user.name]]\\Documents\\onix-master\\onix'],
             binaries=[],
             datas=[('C:\\Users\\[user.name]]\\Envs\\onix-env\\Lib\\site-packages\\iso639\\*.*', 'iso639')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='onix',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
