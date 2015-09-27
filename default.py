"""
    Link Tester XBMC Addon
    Copyright (C) 2015 tknorris

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import urlresolver
import xbmc
import xbmcgui
import xbmcplugin
import sys
import os.path
from local_lib.url_dispatcher import URL_Dispatcher
from local_lib import log_utils
from local_lib import kodi

def __enum(**enums):
    return type('Enum', (), enums)

LINK_PATH = os.path.join(xbmc.translatePath(kodi.get_profile()), 'links.txt')
MODES = __enum(
    MAIN='main', ADD_LINK='add_link', PLAY_LINK='play_link', DELETE_LINK='delete_link'
)

url_dispatcher = URL_Dispatcher()

@url_dispatcher.register(MODES.MAIN)
def main_menu():
    kodi.create_item({'mode': MODES.ADD_LINK}, 'Add Link')
    if os.path.exists(LINK_PATH):
        menu_items = []
        with open(LINK_PATH) as f:
            for i, line in enumerate(f):
                item = line.split('|')
                link = item[0].strip()
                if not link: continue
                try:
                    label = item[1]
                except:
                    label = item[0]
                queries = {'mode': MODES.DELETE_LINK, 'index': i}
                menu_items.append(('Delete Link', 'RunPlugin(%s)' % (kodi.get_plugin_url(queries))),)
                kodi.create_item({'mode': MODES.PLAY_LINK, 'link': link}, label, is_folder=False, is_playable=True, menu_items=menu_items)
    
    kodi.end_of_directory()

@url_dispatcher.register(MODES.ADD_LINK)
def add_link():
    keyboard = xbmc.Keyboard()
    keyboard.setHeading('Enter Link')
    keyboard.doModal()
    if keyboard.isConfirmed():
        link = keyboard.getText()
        if not link:
            return
        
        keyboard = xbmc.Keyboard()
        keyboard.setHeading('Enter Name')
        keyboard.doModal()
        if keyboard.isConfirmed():
            name = keyboard.getText()
            if not os.path.exists(os.path.dirname(LINK_PATH)):
                os.mkdir(os.path.dirname(os.path.dirname(LINK_PATH)))
                
            with open(LINK_PATH, 'a') as f:
                if name:
                    line = '%s|%s' % (link, name)
                else:
                    line = link
                if not line.endswith('\n'):
                    line += '\n'
                f.write(line)
    xbmc.executebuiltin("XBMC.Container.Refresh")

@url_dispatcher.register(MODES.DELETE_LINK, ['index'])
def delete_link(index):
    new_lines = []
    with open(LINK_PATH) as f:
        for i, line in enumerate(f):
            if i == int(index):
                continue
            new_lines.append(line)
            
    with open(LINK_PATH, 'w') as f:
        for line in new_lines:
            f.write(line)

    xbmc.executebuiltin("XBMC.Container.Refresh")

@url_dispatcher.register(MODES.PLAY_LINK, ['link'])
def play_link(link):
    log_utils.log('Playing Link: |%s|' % (link), log_utils.LOGDEBUG)
    hmf = urlresolver.HostedMediaFile(url=link)
    if not hmf:
        log_utils.log('Indirect hoster_url not supported by urlresolver: %s' % (link))
        return False
    log_utils.log('Link Supported: |%s|' % (link), log_utils.LOGDEBUG)

    stream_url = hmf.resolve()
    if not stream_url or not isinstance(stream_url, basestring):
        try: msg = stream_url.msg
        except: msg = link
        kodi.notify('Resolve Failed: %s' % (msg), duration=7500)
        return False
    log_utils.log('Link Resolved: |%s|%s|' % (link, stream_url), log_utils.LOGDEBUG)
        
    listitem = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)

def main(argv=None):
    if sys.argv: argv = sys.argv
    queries = kodi.parse_query(sys.argv[2])
    log_utils.log('Version: |%s| Queries: |%s|' % (kodi.get_version(), queries))
    log_utils.log('Args: |%s|' % (argv))

    # don't process params that don't match our url exactly. (e.g. plugin://plugin.video.1channel/extrafanart)
    plugin_url = 'plugin://%s/' % (kodi.get_id())
    if argv[0] != plugin_url:
        return

    mode = queries.get('mode', None)
    url_dispatcher.dispatch(mode, queries)

if __name__ == '__main__':
    sys.exit(main())
