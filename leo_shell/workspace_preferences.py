"""Bounded, declarative workspace appearance; never loads executable theme code."""
import json
import re
from pathlib import Path
from .settings_store import _write_json_atomic


class WorkspacePreferences:
    def __init__(self, user):
        self.user = Path(user)
        self.path = self.user / 'workspace-appearance.json'

    @staticmethod
    def theme(value):
        if not isinstance(value, dict) or set(value) != {'name', 'colors'}:
            raise ValueError('THEME_INVALID')
        name, colors = value['name'], value['colors']
        keys = {'paper', 'surface', 'ink', 'accent', 'rail', 'rail_ink'}
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 60 or any(ord(c) < 32 for c in name):
            raise ValueError('THEME_INVALID')
        if not isinstance(colors, dict) or set(colors) != keys or any(not isinstance(c, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', c) for c in colors.values()):
            raise ValueError('THEME_INVALID')
        def luminance(color):
            rgb = [int(color[i:i+2],16)/255 for i in (1,3,5)]
            return sum(w*(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4) for w,c in zip((.2126,.7152,.0722),rgb))
        for foreground,background in [('ink','paper'),('ink','surface'),('rail_ink','rail')]:
            a,b=sorted((luminance(colors[foreground]),luminance(colors[background])))
            if (b+.05)/(a+.05)<4.5: raise ValueError('THEME_CONTRAST_LOW')
        return {'name':name.strip(),'colors':{k:v.upper() for k,v in colors.items()}}

    def request(self, payload):
        if not isinstance(payload, dict): raise ValueError('THEME_INVALID')
        for path in (self.user,self.path):
            if path.is_symlink() or getattr(path,'is_junction',lambda:False)(): raise ValueError('THEME_UNAVAILABLE')
        op=payload.get('operation')
        if op=='validate': return {'ok':True,'theme':self.theme(payload.get('theme'))}
        if op=='get':
            value={'mode':'system','theme':None}
            if self.path.exists():
                if self.path.stat().st_size>8192: raise ValueError('THEME_UNAVAILABLE')
                value=json.loads(self.path.read_text(encoding='utf-8'))
            if value.get('mode') not in ('light','dark','system'): raise ValueError('THEME_INVALID')
            if value.get('theme') is not None: value['theme']=self.theme(value['theme'])
            return {'ok':True,'preferences':value}
        if op!='save' or payload.get('mode') not in ('light','dark','system'): raise ValueError('THEME_INVALID')
        value={'mode':payload['mode'],'theme':self.theme(payload['theme']) if payload.get('theme') is not None else None}
        self.user.mkdir(parents=True,exist_ok=True)
        _write_json_atomic(self.path,value)
        return {'ok':True,'preferences':value}
