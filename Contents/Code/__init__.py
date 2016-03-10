####################################################################################################
#                                                                                                  #
#                                     hanime.tv Plex Channel                                       #
#                                                                                                  #
####################################################################################################
# import modules
import messages

# set global variablesi
PREFIX = '/video/hanimetv'
TITLE = 'Hanime.tv'
BASE_URL = 'https://hanime.tv'
SEARCH_BASE_URL = 'https://one-piece.hanime.tv'
ICON = 'icon-default.png'
ART = 'art-default.jpg'

USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/46.0.2490.86 Safari/537.36'
    )

MC = messages.NewMessageContainer(PREFIX, TITLE)

####################################################################################################
def Start():
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = TITLE

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)

    InputDirectoryObject.art = R(ART)
    VideoClipObject.art = R(ART)

    HTTP.CacheTime = 0

####################################################################################################
@handler(PREFIX, TITLE, thumb=ICON, art=ART)
def MainMenu():
    """Create the Main Menu"""

    oc = ObjectContainer(title2=TITLE)

    #q=&search_by=all&sort_by=name.raw&sort_by_ordering=desc&search_from=0&page_size=30
    oc.add(DirectoryObject(
        key=Callback(DirectoryList, page=0, sort_by='name.raw', title='ABC'),
        title='Alphabetical'))
    #q=&search_by=all&sort_by=created_at&sort_by_ordering=desc&search_from=0&page_size=48
    oc.add(DirectoryObject(
        key=Callback(DirectoryList, page=0, sort_by='created_at', title='Upload Date'),
        title='Upload Date'))
    #q=&search_by=all&sort_by=released_at&sort_by_ordering=desc&search_from=0&page_size=48
    oc.add(DirectoryObject(
        key=Callback(DirectoryList, page=0, sort_by='released_at', title='Release Date'),
        title='Release Date'))
    #q=&search_by=all&sort_by=views&sort_by_ordering=desc&search_from=0&page_size=48
    oc.add(DirectoryObject(
        key=Callback(DirectoryList, page=0, sort_by='views', title='Views'),
        title='Views'))
    #q=&search_by=all&sort_by=favorites_count&sort_by_ordering=desc&search_from=0&page_size=48
    oc.add(DirectoryObject(
        key=Callback(DirectoryList, page=0, sort_by='favorites_count', title='Favorites'),
        title='Favorites'))
    """
    oc.add(InputDirectoryObject(
        key=Callback(Search),
        title='Search', summary='Search Hanime.tv', prompt='Search for...'))
    """
    return oc

####################################################################################################
@route(PREFIX + '/directorylist', page=int)
def DirectoryList(page, sort_by, title, query=''):
    """Directory does the Heavy lifting"""


    page_size = 48  # currently this cannot change, the site dosen't allow it
    search_from = page_size * page if page > 0 else page
    query = String.Quote(query, usePlus=True) if query else ''

    req_data = (
        'q=%s&search_by=all&sort_by=%s&sort_by_ordering=desc&search_from=%i&page_size=%i'
        %(query, sort_by, search_from, page_size)
        )

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
    elif (total > page_size) and (page != last_page):
        main_title = '%s / Page %i of %i' %(title, page, last_page)
    else:
        main_title = '%s / Page %i / Last Page' %(title, page)

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
        brand = d['_source']['brand']
        cover_url = d['_source']['cover_url']
        video_url = BASE_URL + '/hentai-videos/' + slug

        oc.add(
            VideoClipObject(
                title=ntitle,
                summary=description,
                thumb=cover_url,
                url=video_url,
                tags=tags,
                source_title='hanime.tv',
                originally_available_at=Datetime.ParseDate(released_at),
                year=int(Datetime.ParseDate(released_at).year),
                studio=brand,
                directors=[brand],
                tagline=tagline,
                content_rating='X'
                )
            )

    if next_page < last_page:
        oc.add(NextPageObject(
            key=Callback(
                DirectoryList, page=next_page, sort_by=sort_by,
                title=title, query=query),
            title='Next Page>>'))

    if len(oc) > 0:
        return oc
    else:
        return MC.message_container('Warning', 'Page Empty')
"""
####################################################################################################
@route(PREFIX + '/search')
def Search(query=''):
    Log.Info('search term = %s' %query)

    query = String.Quote(query, usePlus=False)
    hitsPerPage = 20
    page = 0

    form_data = {'params':
        urllib2.urlencode({
            'query': query, 'hitsPerPage': hitsPerPage, 'page': page,
            'facets': 'brand', 'facetFilters': '[[]]'
            })
        }

    algolia_api_data = urllib2.urlencode({
        'x-algolia-api-key': Dict['Api Env']['api_key'],
        'x-algolia-application-id': Dict['Api Env']['app_id'],
        'x-algolia-agent': Dict['Api Env']['algolia_agent']
        })

    host_api_url = 'https://' + Dict['Api Env']['app_id'] + '-dsn.algolia.net'
    url = host_api_url + '/1/indexes/HentaiVideo/query?' + algolia_api_data

    r = HTTP.Request(url, data=json.dumps(form_data))
    Log(r.headers)
    data = JSON.ObjectFromString(r.content)

    if not int(data['nbHits']) > 0:
        return MessageContainer(
            'Warning',
            'There are no search results for \"%s\". Try being less specific.' %query)
    else:
        pass

    oc = ObjectContainer(title2='Search')

    oc.add(DirectoryObject(
        key=Callback(
            DirectoryList, url=BASE_URL, page=0, order='',
            title='Latest', query=query),
        title='Sort by Latest'))
    oc.add(DirectoryObject(
        key=Callback(
            DirectoryList, url=BASE_URL, page=0, order='_views_desc',
            title='Views', query=query),
        title='Sort by Views'))
    oc.add(DirectoryObject(
        key=Callback(
            DirectoryList, url=BASE_URL, page=0, order='_favorites_count_desc',
            title='Favorites', query=query),
        title='Sort by Favorites'))
    oc.add(DirectoryObject(
        key=Callback(DirectoryList, url=BASE_URL, page=0, order='_released_at_desc',
            title='Realse Date', query=query),
        title='Sort by Release Date'))
    oc.add(DirectoryObject(
        key=Callback(DirectoryList, url=BASE_URL, page=0, order='_alphabetical_desc',
            title='ABC', query=query),
        title='Sort by Alphabetical'))

    return oc

####################################################################################################
@route(PREFIX + '/loadenvsettings')
def LoadEnvSettings():
    \"\"\"Load Defaults\"\"\"

    # find algolia api settings from env_settings.js
    page_text = HTTP.Request(BASE_URL).content
    env_settings_url = 'https:' + Regex('src=\"(.+env_settings.+?)\"').search(page_text).group(1)

    env_settings = HTTP.Request(env_settings_url).content
    api_base_url = Regex('api_base_url\:\ \'(.+)\'').search(env_settings).group(1)
    algolia_search_application_id = Regex('algolia_search_application_id\:\ \'(.+)\'').search(env_settings).group(1)
    algolia_search_search_only_api_key = Regex('algolia_search_search_only_api_key\:\ \'(.+)\'').search(env_settings).group(1)

    # find algolia agent name
    algolia_version_url = 'http:' + Regex('src=\"(.+algoliasearch.+?)\"').search(page_text).group(1)
    algolia_verison = HTTP.Request(algolia_version_url).content
    release_num = Regex('algoliasearch\ (\d+.+?)\ \|').search(algolia_verison).group(1)
    agent_name = Regex('n\.ua=\"(.+?)\"').search(algolia_verison).group(1)
    algolia_agent = agent_name + release_num

    api_settings = {
        'url': api_base_url,
        'app_id': algolia_search_application_id,
        'api_key': algolia_search_search_only_api_key,
        'algolia_agent': algolia_agent
        }

    return api_settings
"""
