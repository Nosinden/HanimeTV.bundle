####################################################################################################
#                                                                                                  #
#                                     hanime.tv Plex Channel                                       #
#                                                                                                  #
####################################################################################################
# import modules
import messages
from common import load_search_url
import urllib2
from updater import Updater
from DumbTools import DumbKeyboard
from DumbTools import DumbPrefs

# set global variablesi
PREFIX = '/video/hanimetv'
TITLE = 'Hanime.tv'
BASE_URL = 'https://hanime.tv'
ICON = 'icon-default.png'
ART = 'art-default.jpg'

USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/46.0.2490.86 Safari/537.36'
    )

SEARCH_BASE_URL = load_search_url(BASE_URL, USER_AGENT)

MC = messages.NewMessageContainer(PREFIX, TITLE)

####################################################################################################
def Start():
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = TITLE

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)

    InputDirectoryObject.art = R(ART)
    VideoClipObject.art = R(ART)

    HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
@handler(PREFIX, TITLE, thumb=ICON, art=ART)
def MainMenu():
    """Create the Main Menu"""

    oc = ObjectContainer(title2=TITLE, no_cache=True)

    Updater(PREFIX + '/updater', oc)

    oc.add(DirectoryObject(
        key=Callback(ABCList, page=0, sort_by='name.raw', title='Alphabetical'),
        title='Alphabetical'))

    oc.add(DirectoryObject(
        key=Callback(BrandList, title='Brands'),
        title='Brands'))

    oc.add(DirectoryObject(
        key=Callback(DirectoryList, page=0, sort_by='views', title='Views'),
        title='Views'))

    oc.add(DirectoryObject(
        key=Callback(DirectoryList, page=0, sort_by='favorites_count', title='Favorites'),
        title='Favorites'))

    oc.add(DirectoryObject(
        key=Callback(DirectoryList, page=0, sort_by='created_at', title='Upload Date'),
        title='Upload Date'))

    oc.add(DirectoryObject(
        key=Callback(DirectoryList, page=0, sort_by='released_at', title='Release Date'),
        title='Release Date'))

    if Client.Product in DumbPrefs.clients:
        DumbPrefs(PREFIX, oc, title='Preferences', thumb=R('icon-prefs.png'))
    else:
        oc.add(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))

    if Client.Product in DumbKeyboard.clients:
        DumbKeyboard(PREFIX, oc, Search, dktitle='Search', dkthumb=R('icon-search.png'))
    else:
        oc.add(InputDirectoryObject(
            key=Callback(Search),
            title='Search', summary='Search Hanime.tv', prompt='Search for...'))

    return oc

####################################################################################################
@route(PREFIX + '/abc')
def ABCList(page, sort_by, title):
    """Setup ABC list"""

    oc = ObjectContainer(title2=title)

    abc_list = [('A-Z', 'asc'), ('Z-A', 'desc')]
    for (n, l) in abc_list:
        oc.add(DirectoryObject(
            key=Callback(DirectoryList, page=0, sort_by='name.raw', sort_by_ordering=l, title=n),
            title=n))

    return oc

####################################################################################################
@route(PREFIX + '/brandlist')
def BrandList(title):
    """Setup brand list"""

    oc = ObjectContainer(title2=title)

    html = HTML.ElementFromURL(BASE_URL + '/search')
    tup = []
    for b in html.xpath('//div[@class="htv-select-multiple inverse"]//span/text()'):
        nb = b.lower().replace('.', '').replace('-', '')
        if (b, nb) not in tup:
            tup.append((b, nb))

    for t, b in sorted(tup):
        oc.add(DirectoryObject(
            key=Callback(DirectoryList, page=0, sort_by='created_at', brand=b, title=t),
            title=t))

    return oc

####################################################################################################
@route(PREFIX + '/directorylist', page=int)
def DirectoryList(page, sort_by, title, brand='all', sort_by_ordering='desc', query=''):
    """Directory does the Heavy lifting"""


    page_size = 48  # currently this cannot change, the site dosen't allow it
    search_from = page_size * page if page > 0 else page
    query = String.Quote(query, usePlus=True) if query else ''

    if brand == 'all':
        req_data = (
            'q=%s&search_by=all&sort_by=%s&sort_by_ordering=%s&search_from=%i&page_size=%i'
            %(query, sort_by, sort_by_ordering, search_from, page_size)
            )
    else:
        req_data = (
            'q=%s&search_by=all&brands[]=%s&sort_by=%s&sort_by_ordering=%s&search_from=%i&page_size=%i'
            %(query, brand, sort_by, sort_by_ordering, search_from, page_size)
            )
        req_data = urllib2.quote(req_data, '&://?=')

    h = {
        'origin': BASE_URL, 'referer': BASE_URL + '/search', 'user-agent': USER_AGENT,
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }

    req = HTTP.Request(SEARCH_BASE_URL, data=req_data, headers=h)
    data = JSON.ObjectFromString(req.content)

    if data['hits']['total'] == 0:
        return MC.message_container('Warning', 'Page Empty')

    total = int(data['hits']['total'])
    p, r = divmod(total, page_size)
    last_page = p + 1 if r > 0 else p
    next_page = page + 1

    if total <= page_size:
        main_title = title
    else:
        main_title = '%s / Page %i of %i' %(title, page+1, last_page)

    oc = ObjectContainer(title2=main_title)

    for d in data['hits']['hits']:
        name = d['_source']['name']
        subs = d['_source']['is_hard_subtitled']
        ntitle = name + ' (Sub)' if subs else name
        slug = d['_source']['slug']
        views = d['_source']['views']
        fav = d['_source']['favorites_count']
        tagline = 'Favorites: %s | Views: %s' %(fav, views)
        released_at = d['_source']['released_at']
        description = String.StripTags(d['_source']['description'])
        tags = [x['text'] for x in d['_source']['hentai_tags']]
        nbrand = d['_source']['brand']
        duration = int(d['_source']['duration_in_ms'])
        cover_url = d['_source']['cover_url']
        video_url = BASE_URL + '/hentai-videos/' + slug

        oc.add(
            VideoClipObject(
                title=ntitle,
                summary=description,
                thumb=cover_url,
                url=video_url,
                tags=tags,
                duration=duration,
                source_title='hanime.tv',
                originally_available_at=Datetime.ParseDate(released_at),
                year=int(Datetime.ParseDate(released_at).year),
                studio=nbrand,
                directors=[nbrand],
                tagline=tagline,
                content_rating='X'
                )
            )

    if next_page < last_page:
        oc.add(NextPageObject(
            key=Callback(
                DirectoryList, page=next_page, sort_by=sort_by,
                title=title, query=query, brand=brand),
            title='Next Page>>'))

    if len(oc) > 0:
        return oc
    else:
        return MC.message_container('Warning', 'Page Empty')

####################################################################################################
@route(PREFIX + '/search')
def Search(query=''):
    """Setup search"""

    query = query.strip()
    Log.Info('search term = %s' %query)

    return DirectoryList(page=0, sort_by='created_at', query=query, brand='all', title='Search')
