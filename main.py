import re
import pandas
import folium
import requests

API_KEY = "AIzaSyAgddL1nFKDhUNuiEAPFNUD-kNktOratbU"


def correct_film_name_year(film_name, film_year, year):
    """(list[string], list[string], int) -> (bool)

    The function checks if film_name and
    film_year aren't empty and if the year
    of film is correct

    """
    if not film_name or not film_year or int(film_year[0]) != year:
        return False
    else:
        return True


def find_films_info(line, year):
    """(string, int) -> (tuple[string, int, string])

    The function parse the string with film's
    information and returns it in appropriate
    form (in tuple)

    """
    film_year = re.findall('.+\((\d{4})\)', line)
    film_name = re.findall('(.+)\(\d{4}\)', line)

    if not correct_film_name_year(film_name, film_year, year):
        return

    film_location = re.findall('\t+([^\(\)\n]+)', line)[0].strip()
    film_name = film_name[0].replace('\'', '')
    film_year = int(film_year[0])

    return film_name, film_year, film_location


def read_from_file(f_name, year, count=0):
    """(string, int, int) -> (list[tuple[string, int, string]])

    The function reads data from the file and
    returns it in the one list with tuples

    """
    with open(file=f_name, mode='r', errors='ignore', encoding='utf-8') as f:
        content = f.readlines()
        films = list()

        for line in content:
            if len(films) == count and count != 0:
                break
            info = find_films_info(line, year)
            if info:
                films.append(info)

    return films


def get_coordinates(address):
    """(string) -> (tuple[float, float])

    The functions finds actual coordinates of
    the place, which is given as a string and
    returns them in the tuple of floats

    """
    link = 'https://maps.googleapis.com/maps/api/geocode/'
    api_response = requests.get(
        link + 'json?address={0}&key={1}'.format(address, API_KEY)
    )
    api_response_dict = api_response.json()

    if api_response_dict['status'] == 'OK':
        lat = api_response_dict['results'][0]['geometry']['location']['lat']
        lon = api_response_dict['results'][0]['geometry']['location']['lng']
        return lat, lon
    else:
        return 0, 0


def print_info(info, coordinates):
    print(
        '"{0}" has coordinates: (latitude - {1}; longitude - {2})'.format(
            info[0],
            coordinates[0],
            coordinates[1]
        )
    )


def add_films_layer(my_map, films):
    """(folium.Map, list[tuple[string, int, string]]) -> (None)

    The function adds the layer with films to
    the map, which is given as an argument

    """
    fg = folium.FeatureGroup(name="Films")

    for film in films:
        coordinates = get_coordinates(film[2])
        if coordinates == (0, 0):
            continue
        print_info(film, coordinates)
        fg.add_child(
            folium.Marker(
                location=[coordinates[0], coordinates[1]],
                popup=str(film[0])
            )
        )

    my_map.add_child(fg)


def add_population_layer(my_map):
    """(folium.Map) -> (None)

    The function adds the layer with population
    to the map, which is given as an argument

    """
    fg = folium.FeatureGroup(name="Population")

    def choose_color(x):
        return {
            'fillColor': 'green'
            if x['properties']['POP2005'] < 10000000
            else 'orange'
            if (10000000 <= x['properties']['POP2005'] < 20000000)
            else 'red'
        }

    fg.add_child(
        folium.GeoJson(
            data=open(
                'world.json',
                'r',
                encoding='utf-8-sig'
            ).read(),
            style_function=choose_color
        )
    )
    my_map.add_child(fg)


def add_crimes_layer(my_map):
    """(folium.Map) -> (None)

    The function adds the layer with crimes
    to the map, which is given as an argument

    """
    data = pandas.read_csv('SacramentocrimeJanuary2006.csv')[0:100]

    latitude = data['latitude']
    longitude = data['longitude']
    time = data['datetime']
    crime_description = data['crimedescr']

    fg = folium.FeatureGroup(name='Crimes')

    for lat, lon, t, descrp in zip(latitude,
                                   longitude,
                                   time,
                                   crime_description):
        fg.add_child(
            folium.Marker(
                location=[lat, lon],
                popup=str(descrp)
            )
        )
    my_map.add_child(fg)


def request_year_and_count():
    """() -> (tuple[int, int])

    The function request the year and the count
    of films, which user is needed. If user
    haven't entered the count, function returns
    0 as a count

    """
    try:
        count = int(input("\n\nEnter the count of films you"
                          " wanted to be shown on the map"
                          " (or just press enter to skip): "))
    except ValueError:
        count = 0

    try:
        year = int(input("\nEnter the year: "))
    except ValueError:
        print("\nYou may entered a wrong data!\n")
        exit()

    return year, count


def create_map(films):
    """(list[tuple[string, int, string]]) -> (None)

    The function creates map with a few
    layers, which are needed.

    """
    _map = folium.Map()

    add_population_layer(_map)
    add_crimes_layer(_map)
    add_films_layer(_map, films)

    _map.add_child(folium.LayerControl())
    _map.save("Map.html")


def main():
    """The entry point of the program

    """
    year, count = request_year_and_count()
    films = read_from_file("locations.list", year, count)
    create_map(films)


if __name__ == "__main__":
    main()
