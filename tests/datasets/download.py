import os
import shutil
import ssl
import sys
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen, urlretrieve
from zipfile import ZipFile, is_zipfile

import pandas as pd
from tqdm import tqdm

import socceraction.spadl as spadl
import socceraction.spadl.statsbomb as statsbomb
import socceraction.spadl.wyscout as wyscout
from socceraction.data.statsbomb import StatsBombLoader
from socceraction.data.wyscout import PublicWyscoutLoader

# optional: if you get a SSL CERTIFICATE_VERIFY_FAILED exception
ssl._create_default_https_context = ssl._create_unverified_context

_data_dir = os.path.dirname(__file__)


def read_json_file(filename):
    with open(filename, 'rb') as json_file:
        return BytesIO(json_file.read()).getvalue().decode('unicode_escape')


def download_statsbomb_data():
    dataset_url = 'https://github.com/statsbomb/open-data/archive/master.zip'

    tmp_datafolder = os.path.join(_data_dir, 'statsbomb', 'tmp')
    raw_datafolder = os.path.join(_data_dir, 'statsbomb', 'raw')
    for datafolder in [tmp_datafolder, raw_datafolder]:
        if not os.path.exists(datafolder):
            os.makedirs(datafolder, exist_ok=True)
    statsbombzip = os.path.join(tmp_datafolder, 'statsbomb-open-data.zip')

    with urlopen(dataset_url) as dl_file:
        with open(statsbombzip, 'wb') as out_file:
            out_file.write(dl_file.read())

    with ZipFile(statsbombzip, 'r') as zipObj:
        zipObj.extractall(tmp_datafolder)

    shutil.rmtree(raw_datafolder)
    Path(f'{tmp_datafolder}/open-data-master/data').rename(raw_datafolder)
    shutil.rmtree(tmp_datafolder)


def convert_statsbomb_data():
    seasons = {
        3: '2018',
    }
    leagues = {
        'FIFA World Cup': 'WorldCup',
    }
    spadl_datafolder = os.path.join(_data_dir, 'statsbomb')

    free_open_data_remote = 'https://raw.githubusercontent.com/statsbomb/open-data/master/data/'

    SBL = StatsBombLoader(root=free_open_data_remote, getter='remote')

    # View all available competitions
    df_competitions = SBL.competitions()
    df_selected_competitions = df_competitions[
        df_competitions.competition_name.isin(leagues.keys())
    ]

    for competition in df_selected_competitions.itertuples():
        # Get games from all selected competition
        games = SBL.games(competition.competition_id, competition.season_id)

        games_verbose = tqdm(list(games.itertuples()), desc='Loading match data')
        teams, players = [], []

        competition_id = leagues[competition.competition_name]
        season_id = seasons[competition.season_id]
        spadl_h5 = os.path.join(spadl_datafolder, f'spadl-{competition_id}-{season_id}.h5')
        with pd.HDFStore(spadl_h5) as spadlstore:

            spadlstore.put('actiontypes', spadl.actiontypes_df(), format='table')
            spadlstore.put('results', spadl.results_df(), format='table')
            spadlstore.put('bodyparts', spadl.bodyparts_df(), format='table')

            for game in games_verbose:
                # load data
                teams.append(SBL.teams(game.game_id))
                players.append(SBL.players(game.game_id))
                events = SBL.events(game.game_id)

                # convert data
                spadlstore.put(
                    f'actions/game_{game.game_id}',
                    statsbomb.convert_to_actions(events, game.home_team_id),
                    format='table',
                )

            games.season_id = season_id
            games.competition_id = competition_id
            spadlstore.put('games', games)
            spadlstore.put(
                'teams',
                pd.concat(teams).drop_duplicates('team_id').reset_index(drop=True),
            )
            spadlstore.put(
                'players',
                pd.concat(players).drop_duplicates('player_id').reset_index(drop=True),
            )


def download_wyscout_data():
    # https://figshare.com/collections/Soccer_match_event_dataset/4415000/5
    dataset_urls = dict(
        competitions='https://ndownloader.figshare.com/files/15073685',
        teams='https://ndownloader.figshare.com/files/15073697',
        players='https://ndownloader.figshare.com/files/15073721',
        games='https://ndownloader.figshare.com/files/14464622',
        events='https://ndownloader.figshare.com/files/14464685',
    )

    raw_datafolder = os.path.join(_data_dir, 'wyscout_public', 'raw')
    if not os.path.exists(raw_datafolder):
        os.makedirs(raw_datafolder, exist_ok=True)

    # download and unzip Wyscout open data
    for url in tqdm(dataset_urls.values(), desc='Downloading data'):
        url_obj = urlopen(url).geturl()
        path = Path(urlparse(url_obj).path)
        file_name = os.path.join(raw_datafolder, path.name)
        file_local, _ = urlretrieve(url_obj, file_name)
        if is_zipfile(file_local):
            with ZipFile(file_local) as zip_file:
                zip_file.extractall(raw_datafolder)


def convert_wyscout_data():
    seasons = {
        10078: '2018',
    }
    leagues = {
        28: 'WorldCup',
    }

    raw_datafolder = os.path.join(_data_dir, 'wyscout_public', 'raw')
    spadl_datafolder = os.path.join(_data_dir, 'wyscout_public')

    WYL = PublicWyscoutLoader(root=raw_datafolder)

    # View all available competitions
    df_competitions = WYL.competitions()
    df_selected_competitions = df_competitions[
        df_competitions.competition_id.isin(leagues.keys())
    ]

    for competition in df_selected_competitions.itertuples():
        # Get games from all selected competition
        games = WYL.games(competition.competition_id, competition.season_id)

        games_verbose = tqdm(list(games.itertuples()), desc='Loading match data')
        teams, players = [], []

        competition_id = leagues[competition.competition_id]
        season_id = seasons[competition.season_id]
        spadl_h5 = os.path.join(spadl_datafolder, f'spadl-{competition_id}-{season_id}.h5')
        with pd.HDFStore(spadl_h5) as spadlstore:

            spadlstore.put('actiontypes', spadl.actiontypes_df(), format='table')
            spadlstore.put('results', spadl.results_df(), format='table')
            spadlstore.put('bodyparts', spadl.bodyparts_df(), format='table')

            for game in games_verbose:
                # load data
                teams.append(WYL.teams(game.game_id))
                players.append(WYL.players(game.game_id))
                events = WYL.events(game.game_id)

                # convert data
                spadlstore.put(
                    f'actions/game_{game.game_id}',
                    wyscout.convert_to_actions(events, game.home_team_id),
                    # format='table',
                )

            games.season_id = season_id
            games.competition_id = competition_id
            spadlstore.put('games', games)
            spadlstore.put(
                'teams',
                pd.concat(teams).drop_duplicates('team_id').reset_index(drop=True),
            )
            spadlstore.put(
                'players',
                pd.concat(players).drop_duplicates('player_id').reset_index(drop=True),
            )


if __name__ == '__main__':
    if len(sys.argv) == 1 or sys.argv[1] == 'statsbomb':
        download_statsbomb_data()
        convert_statsbomb_data()
    if len(sys.argv) == 1 or sys.argv[1] == 'wyscout':
        download_wyscout_data()
        convert_wyscout_data()
