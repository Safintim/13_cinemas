import requests
import argparse
import termtables as tt
from bs4 import BeautifulSoup


def main():
    parser = create_parser()
    namespace = parser.parse_args()
    try:
        movies = get_movies_today_in_cinemas(namespace.city)
        output_movies_to_console(movies)
    except requests.RequestException as e:
        exit(e)


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('city')
    return parser


def get_movies_today_in_cinemas(city, count=10):
    url_afisha = 'https://www.afisha.ru/{}/schedule_cinema/'.format(city)
    afisha_page = fetch_afisha_page(url_afisha)
    movies = get_movies_from_afisha_page(afisha_page)
    for movie in movies[:count]:
        movie_obj = {
            'title': movie
        }
        kinopoisk_search_page = fetch_search_page_by_title(movie)
        movie_id = get_movie_id_from_search_page(kinopoisk_search_page)
        xml_rating = fetch_movie_info_xml(movie_id)
        rating_movie = get_rating_movie_from_xml(xml_rating)
        movie_obj.update(rating_movie)
        yield movie_obj


def fetch_afisha_page(url_afisha):
    response = requests.get(url_afisha)
    response.raise_for_status()
    return response.text


def get_movies_from_afisha_page(raw_html):
    soup = BeautifulSoup(raw_html, 'html.parser')
    return [movie.text for movie in soup.select('#widget-content ul li h3 a')]


def fetch_search_page_by_title(movie_title):
    url = 'http://www.kinopoisk.ru/index.php'
    params = {
        'kp_query': movie_title
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.text


def get_movie_id_from_search_page(raw_html):
    soup = BeautifulSoup(raw_html, 'html.parser')
    return soup.select_one('div.most_wanted p.name a').attrs['data-id']


def fetch_movie_info_xml(movie_id):
    url = 'https://rating.kinopoisk.ru/{}.xml'.format(movie_id)
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def get_rating_movie_from_xml(xml):
    soup = BeautifulSoup(xml, 'lxml')
    imdb_rating = soup.find('imdb_rating')
    rating_info = {
        'votes': 0,
        'rating': 0
    }
    if imdb_rating:
        rating_info['votes'] = int(imdb_rating.attrs['num_vote'])
        rating_info['rating'] = float(imdb_rating.get_text())

    return rating_info


def output_movies_to_console(movies):
    header = ['title', 'votes', 'rating']
    movies_for_table = []
    for movie in sorted(movies, key=lambda movie: movie['rating'], reverse=True):
        movies_for_table.append([movie['title'], movie['votes'], movie['rating']])

    string = tt.to_string(
        movies_for_table,
        header=header,
        style=tt.styles.thin_thick,
        alignment='c')
    print(string)


if __name__ == '__main__':
    main()
