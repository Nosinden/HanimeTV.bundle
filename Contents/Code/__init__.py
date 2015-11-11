####################################################################################################
#                                                                                                  #
#                               hanime.tv Plex Channel -- v0.01                                    #
#                                                                                                  #
####################################################################################################
# import modules
import urllib, json

# set global variables
PREFIX = '/video/hanimetv'
TITLE = 'Hanime.tv'
BASE_URL = 'https://hanime.tv/'
ICON = 'icon-default.png'
ART = 'art-default.jpg'

####################################################################################################

def Start():
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = TITLE

    DirectoryObject.thumb = R(ICON)

    HTTP.CacheTime = 0
    HTTP.Headers['User-Agent'] = (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/46.0.2490.86 Safari/537.36'
        )
    HTTP.Headers['Referer'] = BASE_URL + '/browse'
    HTTP.Headers['Origin'] = BASE_URL

    Dict['Api Env'] = LoadEnvSettings()
    Log(Dict['Api Env'])
    Dict.Save()

    HTTP.Headers['host'] = Dict['Api Env']['app_id'] + '-dsn.algolia.net'

####################################################################################################
# Create the main menu

@handler(PREFIX, TITLE, ICON, ART)
def MainMenu():
    oc = ObjectContainer(title2=TITLE)

    oc.add(DirectoryObject(
        key=Callback(DirectoryList, url=BASE_URL, page=0, order='', title='Latest'),
        title='Latest'))
    oc.add(DirectoryObject(
        key=Callback(DirectoryList, url=BASE_URL, page=0, order='_views_desc', title='Views'),
        title='Views'))
    oc.add(DirectoryObject(
        key=Callback(DirectoryList, url=BASE_URL, page=0, order='_favorites_count_desc', title='Favorites'),
        title='Favorites'))
    oc.add(DirectoryObject(
        key=Callback(DirectoryList, url=BASE_URL, page=0, order='_released_at_desc', title='Realse Date'),
        title='Release Date'))
    oc.add(DirectoryObject(
        key=Callback(DirectoryList, url=BASE_URL, page=0, order='_alphabetical_desc', title='ABC'),
        title='Alphabetical'))
    oc.add(InputDirectoryObject(
        key=Callback(Search),
        title='Search', summary='Search Hanime.tv', prompt='Search for...'))

    return oc

####################################################################################################
# directory does the heavy lifting

@route(PREFIX + '/directorylist', page=int)
def DirectoryList(url, page, order, title, query=''):
    title2=title

    if not query:
        query = ''
    else:
        query = String.Quote(query, usePlus=False)

    hitsPerPage = 20

    form_data = {"params":
            urllib.urlencode({
                'query': query, 'hitsPerPage': hitsPerPage, 'page': page,
                'facets': 'brand', 'facetFilters': '[[]]'
                })
            }

    Log(form_data)

    algolia_api_data = urllib.urlencode({
        'x-algolia-api-key': Dict['Api Env']['api_key'],
        'x-algolia-application-id': Dict['Api Env']['app_id'],
        'x-algolia-agent': Dict['Api Env']['algolia_agent']
        })

    host_api_url = 'https://' + Dict['Api Env']['app_id'] + '-dsn.algolia.net'

    if order:
        url = host_api_url + '/1/indexes/HentaiVideo%s/query?' %order + algolia_api_data
    else:
        url = host_api_url + '/1/indexes/HentaiVideo/query?' + algolia_api_data

    r = HTTP.Request(url, data=json.dumps(form_data))
    data = JSON.ObjectFromString(r.content)

    if not data['nbHits'] > 0:
        return MessageContainer('Warning', 'Page Empty')
    else:
        pass

    if int(data['nbPages']) > 0 and int(data['nbPages']) > int(page):
        main_title = '%s | Page %i of %i' %(title2, int(page), int(data['nbPages']))
    else:
        main_title = '%s | Page %i | Last Page' %(title2, int(page))

    oc = ObjectContainer(title2=main_title)

    for node in data['hits']:
        name = node['name']
        subs = node['hard_subtitle_language']
        if subs == 'English':
            title = name + ' (Sub)'
        else:
            title = name

        slug = node['slug']
        views = node['views']
        fav = node['favorites_count']
        tagline = 'Favorites: %s | Views: %s' %(views, fav)
        #created_at = node['created_at']
        released_at = node['released_at']
        description = String.StripTags(node['description'])
        tags = node['_tags']
        studio = node['brand']
        cover_url = node['cover_url']
        video_url = Dict['Api Env']['url'] + '/api/v1/hentai_videos/' + slug + '/interest'
        Log('video interest url = %s' %video_url)

        oc.add(
            VideoClipObject(
                title=title,
                summary=description,
                thumb=cover_url,
                url=video_url,
                tags=tags,
                source_title='hanime.tv',
                originally_available_at=Datetime.ParseDate(released_at),
                year=int(Datetime.ParseDate(released_at).year),
                studio=studio,
                directors=[studio],
                tagline=tagline,
                content_rating='X'
                )
            )

    if int(data['nbPages']) > 0 and int(data['nbPages']) > int(page):
        oc.add(NextPageObject(
            key=Callback(
                DirectoryList, url=url, page=int(page) + 1, order=order,
                title=title2, query=query),
            title='Next Page>>'))

    if len(oc) > 0:
        return oc
    else:
        return MessageContainer(header='Warning', message='Page Empty')

####################################################################################################
# Search

@route(PREFIX + '/search')
def Search(query=''):
    Log.Info('search term = %s' %query)

    query = String.Quote(query, usePlus=False)
    hitsPerPage = 20
    page = 0

    form_data = {'params':
        urllib.urlencode({
            'query': query, 'hitsPerPage': hitsPerPage, 'page': page,
            'facets': 'brand', 'facetFilters': '[[]]'
            })
        }

    algolia_api_data = urllib.urlencode({
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
# load defaults

@route(PREFIX + '/loadenvsettings')
def LoadEnvSettings():
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

