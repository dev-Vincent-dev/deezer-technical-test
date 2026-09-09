import pytest
from unittest.mock import Mock

from deezer_analytics.collect import DeezerCollector


def test_tracks_are_deduplicated():
    client = Mock()

    collector = DeezerCollector(
        client=client,
        target_size=2,
        target_size_per_query=2,
        queries=["pop"],
    )

    playlist = {
        "tracks": {
            "data": [
                {"id": 1, "title": "Track 1"},
                {"id": 2, "title": "Track 2"},
                {"id": 1, "title": "Track 1"},
            ]
        }
    }

    tracks_by_id = {}
    query_track_ids = set()

    collector._add_playlist_tracks(
        tracks_by_id,
        query_track_ids,
        playlist,
    )

    assert len(tracks_by_id) == 2
    assert query_track_ids == {1, 2}


def test_collection_stops_at_target_size_per_query():
    client = Mock()

    client.search_playlists.return_value = {
        "data": [
            {"id": 100},
            {"id": 101},
            {"id": 102},
        ]
    }

    client.get_playlist.side_effect = [
        {
            "tracks": {
                "data": [
                    {"id": 1},
                    {"id": 2},
                ]
            }
        },
        {
            "tracks": {
                "data": [
                    {"id": 3},
                    {"id": 4},
                ]
            }
        },
    ]

    collector = DeezerCollector(
        client=client,
        target_size=3,
        target_size_per_query=3,
        queries=["pop"],
        playlist_page_size=20,
    )

    tracks = collector._collect_tracks_from_playlists()

    assert len(tracks) == 3
    assert client.get_playlist.call_count == 2


def test_collect_albums_only_once_per_album():
    client = Mock()

    tracks = [
        {"album": {"id": 10}},
        {"album": {"id": 10}},
        {"album": {"id": 20}},
    ]

    client.get_album.side_effect = [
        {"id": 10, "title": "Album 10"},
        {"id": 20, "title": "Album 20"},
    ]

    collector = DeezerCollector(client=client)

    albums = collector._collect_albums(tracks)

    assert len(albums) == 2
    assert client.get_album.call_count == 2


def test_build_track():
    track = {
        "id": 1,
        "title": "Test",
        "duration": 180,
        "rank": 100,
    }

    album = {
        "id": 10,
        "title": "Album",
        "duration": 3600,
        "fans": 500,
    }

    artist = {
        "id": 20,
        "name": "Artist",
        "nb_album": 5,
        "nb_fan": 1000,
    }

    result = DeezerCollector._build_track(
        track,
        album,
        artist,
    )

    assert result.id == 1
    assert result.title == "Test"
    assert result.album_id == 10
    assert result.artist_id == 20


def test_collect_fails_if_target_size_not_reached():
    client = Mock()

    collector = DeezerCollector(
        client=client,
        target_size=3,
        target_size_per_query=2,
        queries=["pop"],
    )

    client.search_playlists.return_value = {"data": []}

    with pytest.raises(
        ValueError,
        match="Impossible de collecter 3 titres",
    ):
        collector.collect()
