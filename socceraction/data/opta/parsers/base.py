# -*- coding: utf-8 -*-
"""Base class for all Opta(-derived) event stream parsers.

A parser reads a single data file and should extend the 'OptaParser' class to
extract data about competitions, games, players, teams and events that is
encoded in the file.

"""
import json  # type: ignore
from abc import ABC
from typing import Any, Dict, Optional

from lxml import objectify


class OptaParser(ABC):
    """Extract data from an Opta data stream.

    Parameters
    ----------
    path : str
        Path of the data file.
    """

    def extract_competitions(self) -> Dict[int, Dict[str, Any]]:
        """Return a dictionary with all available competitions.

        Returns
        -------
        dict
            A mapping between competion IDs and the information available about
            each competition in the data stream.
        """
        return {}

    def extract_games(self) -> Dict[int, Dict[str, Any]]:
        """Return a dictionary with all available games.

        Returns
        -------
        dict
            A mapping between game IDs and the information available about
            each game in the data stream.
        """
        return {}

    def extract_teams(self) -> Dict[int, Dict[str, Any]]:
        """Return a dictionary with all available teams.

        Returns
        -------
        dict
            A mapping between team IDs and the information available about
            each team in the data stream.
        """
        return {}

    def extract_players(self) -> Dict[int, Dict[str, Any]]:
        """Return a dictionary with all available players.

        Returns
        -------
        dict
            A mapping between player IDs and the information available about
            each player in the data stream.
        """
        return {}

    def extract_lineups(self) -> Dict[int, Dict[str, Any]]:
        """Return a dictionary with the lineup of each team.

        Returns
        -------
        dict
            A mapping between team IDs and the information available about
            each team's lineup in the data stream.
        """
        return {}

    def extract_events(self) -> Dict[int, Dict[str, Any]]:
        """Return a dictionary with all available events.

        Returns
        -------
        dict
            A mapping between event IDs and the information available about
            each event in the data stream.
        """
        return {}


class OptaJSONParser(OptaParser):
    """Extract data from an Opta JSON data stream.

    Parameters
    ----------
    path : str
        Path of the data file.
    """

    def __init__(self, path: str, **kwargs: Any):
        with open(path, 'rt', encoding='utf-8') as fh:
            self.root = json.load(fh)


class OptaXMLParser(OptaParser):
    """Extract data from an Opta XML data stream.

    Parameters
    ----------
    path : str
        Path of the data file.
    """

    def __init__(self, path: str, **kwargs: Any):
        with open(path, 'rb') as fh:
            self.root = objectify.fromstring(fh.read())


def assertget(dictionary: Dict[str, Any], key: str) -> Any:
    """Return the value of the item with the specified key.

    In contrast to the default `get` method, this version will raise an
    assertion error if the given key is not present in the dict.

    Parameters
    ----------
    dictionary : dict
        A Python dictionary.
    key : str
        A key in the dictionary.

    Returns
    -------
    value
        Returns the value for the specified key if the key is in the dictionary.

    Raises
    ------
    AssertionError
        If the given key could not be found in the dictionary.
    """
    value = dictionary.get(key)
    assert value is not None, 'KeyError: ' + key + ' not found in ' + str(dictionary)
    return value


def _get_end_x(qualifiers: Dict[int, Any]) -> Optional[float]:
    try:
        # pass
        if 140 in qualifiers:
            return float(qualifiers[140])
        # blocked shot
        if 146 in qualifiers:
            return float(qualifiers[146])
        # passed the goal line
        if 102 in qualifiers:
            return float(100)
        return None
    except ValueError:
        return None


def _get_end_y(qualifiers: Dict[int, Any]) -> Optional[float]:
    try:
        # pass
        if 141 in qualifiers:
            return float(qualifiers[141])
        # blocked shot
        if 147 in qualifiers:
            return float(qualifiers[147])
        # passed the goal line
        if 102 in qualifiers:
            return float(qualifiers[102])
        return None
    except ValueError:
        return None
