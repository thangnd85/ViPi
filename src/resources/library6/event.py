# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import json
import sys

from enum import IntEnum

try:
    import queue as queue
except ImportError:
    import Queue as queue


class EventType(IntEnum):
    """Event types."""

    ON_START_FINISHED = 0
    """The Assistant library has finished starting."""
    ON_CONVERSATION_TURN_STARTED = 1
    """Indicates a new turn has started.

    The Assistant is currently listening, waiting for a user
    query. This could be the result of hearing the hotword or
    :meth:`~google.assistant.library.Assistant.start_conversation`
    being called on the Assistant.
    """
    ON_CONVERSATION_TURN_TIMEOUT = 2
    """The Assistant timed out waiting for a discernable query.

    This could be caused by a mistrigger of the Hotword or the Assistant could
    not understand what the user said.
    """
    ON_END_OF_UTTERANCE = 3
    """The Assistant has stopped listening to a user query.

    The Assistant may not have finished figuring out what the user has said but
    it has stopped listening for more audio data.
    """
    ON_RECOGNIZING_SPEECH_FINISHED = 5
    """The Assistant has determined the final recognized speech.

    Args:
        text (str): The final text interpretation of a user's query.
    """
    ON_RESPONDING_STARTED = 6
    """The Assistant is starting to respond by voice.

    The Assistant will be responding until
    :data:`~google.assistant.library.event.EventType.ON_RESPONDING_FINISHED`
    is received.

    Args:
        is_error_response (bool): True means a local error TTS is being played,
            otherwise the Assistant responds with a server response.
    """
    ON_RESPONDING_FINISHED = 7
    """The Assistant has finished responding by voice."""
    ON_NO_RESPONSE = 8
    """The Assistant successfully completed its turn but has nothing to say."""
    ON_CONVERSATION_TURN_FINISHED = 9
    """The Assistant finished the current turn.

    This includes both processing a user's query and speaking the
    full response, if any.

    Args:
        with_follow_on_turn (bool): If True, the Assistant is expecting a
            follow up interaction from the user. The microphone will be
            re-opened to allow the user to answer a follow-up question.
    """
    ON_ALERT_STARTED = 10
    """Indicates that an alert has started sounding.

    This alert will continue until
    :data:`~google.assistant.library.event.EventType.ON_ALERT_FINISHED`
    with the same ``alert_type`` is received. Only one alert should be
    active at any given time.

    Args:
        alert_type (AlertType): The id of the Enum representing the currently
            sounding type of alert.
    """
    ON_ALERT_FINISHED = 11
    """Indicates the alert of ``alert_type`` has finished sounding.

    Args:
        alert_type (AlertType): The id of the Enum representing the type
            of alert which just finished.
    """
    ON_ASSISTANT_ERROR = 12
    """Indicates if the Assistant library has encountered an error.

    Args:
        is_fatal (bool): If True then the Assistant will be unable to recover
            and should be restarted.
    """
    ON_MUTED_CHANGED = 13
    """Indicates that the Assistant is currently listening or not.

    :meth:`~google.assistant.library.Assistant.start` will always
    generate an
    :data:`~google.assistant.library.event.EventType.ON_MUTED_CHANGED`
    to report the initial value.

    Args:
        is_muted (bool): If True then the Assistant is not currently listening
            for its hotword and will not respond to user queries.
    """
    ON_DEVICE_ACTION = 14
    """Indicates that a device action request was dispatched to the device.

    This is dispatched if any Device Grammar is triggered for the
    traits supported by the device. This event type has a special 'actions'
    property which will return an iterator or Device Action commands and
    the params associated with them (if applicable).

    TODO(jordanjtw): Include a link to public documentation for the Device
    Action JSON payload format and supported traits.

    Args:
        dict: The decoded JSON payload of a Device Action request.
    """
    ON_RENDER_RESPONSE = 15
    """Indicates that the Assistant has text output to render for a response.

    Args:
        type (RenderResponseType): The type of response to render.
        text (str): The string to render for RenderResponseType.TEXT.
    """
    ON_MEDIA_STATE_IDLE = 16
    """Indicates that there is nothing playing and nothing queued to play.

    This event is broadcast from the Google Assistant Library's built-in
    media player for news/podcast on start-up and whenever the player has
    gone idle because a user stopped the media or paused it and the stream
    has timed out."""
    ON_MEDIA_TRACK_LOAD = 17
    """Indicates a track is loading but has not started playing.

    This may be dispatched multiple times if new metadata is loaded
    asynchonously. This is typically followed by the event
    `~google.assistant.library.event.EventType.ON_MEDIA_TRACK_PLAY`

    Args:
        metadata(dict): Metadata for the loaded track. Not all fields will
            be filled by this time -- if a field is unknown it will not
            be included. Metadata fields include:
                album(str): The name of the album the track belongs to.
                album_art(str): A URL for the album art.
                artist(str): The artist who created this track.
                duration_ms(double): The length of this track in milliseconds.
                title(str): The title of the track.
        track_type(MediaTrackType): The type of track loaded."""
    ON_MEDIA_TRACK_PLAY = 18
    """Indicates that a track is currently outputting audio.

    This will only trigger when we transistion from one state to another, such
    as from `~google.assistant.library.event.EventType.ON_MEDIA_TRACK_LOAD`
    or `~google.assistant.library.event.EventType.ON_MEDIA_TRACK_STOP`

    Args:
        metadata(dict): Metadata for the playing track. If a field is unknown
            it will not be included. Metadata fields include:
                album(str): The name of the album the track belongs to.
                album_art(str): A URL for the album art.
                artist(str): The artist who created this track.
                duration_ms(double): The length of this track in milliseconds.
                title(str): The title of the track.
        position_ms(double): The current position in a playing track in
            milliseconds since the beginning. If "metadata.duration_ms" is
            unknown (set to 0) this field will not be set.
        track_type(MediaTrackType): The type of track playing."""
    ON_MEDIA_TRACK_STOP = 19
    """Indicates that a previously playing track is stopped.

    This is typically a result of the user pausing; the track can return to
    `~google.assistant.library.event.EventType.ON_MEDIA_TRACK_PLAY` if it is
    resumed by the user.

    Args:
        metadata(dict): Metadata for the stopped track. If a field is unknown
            it will not be included. Metadata fields include:
                album(str): The name of the album the track belongs to.
                album_art(str): A URL for the album art.
                artist(str): The artist who created this track.
                duration_ms(double): The length of this track in milliseconds.
                title(str): The title of the track.
        position_ms(double): The current position in a stopped track in
            milliseconds since the beginning. If "metadata.duration_ms" is
            unknown (set to 0) this field will not be set.
        track_type(MediaTrackType): The type of track stopped."""
    ON_MEDIA_STATE_ERROR = 20
    """Indicates that an error has occurred playing a track.

    The built-in media player will attempt to skip to the next track or
    return to `~google.assistant.library.event.EventType.ON_MEDIA_STATE_IDLE`
    if there is nothing left to play."""


class AlertType(IntEnum):
    """Alert types.

    Used with
    :data:`~google.assistant.library.event.EventType.ON_ALERT_STARTED`
    and
    :data:`~google.assistant.library.event.EventType.ON_ALERT_FINISHED`
    events.
    """

    ALARM = 0
    """An event set for an absolute time such as '3 A.M on Monday'"""
    TIMER = 1
    """An event set for a relative time such as '30 seconds from now'"""


class MediaTrackType(IntEnum):
    """Types of track for an ON_MEDIA_TRACK_X events.

    Used with
    :data:`~google.assistant.library.event.EventType.ON_MEDIA_TRACK_LOAD`,
    :data:`~google.assistant.library.event.EventType.ON_MEDIA_TRACK_PLAY`,
    & :data:`~google.assistant.library.event.EventType.ON_MEDIA_TRACK_STOP`
    """
    TTS = 1
    """A TTS introduction or interstitial track related to an item."""
    CONTENT = 2
    """The actual content for an item (news/podcast)."""


class RenderResponseType(IntEnum):
    """Types of content to render.

    Used with
    :data:`~google.assistant.library.event.EventType.ON_RENDER_RESPONSE`
    """
    TEXT = 0


class Event(object):
    """An event generated by the Assistant.

    Attributes:
        type (EventType): The type of event that was generated.
        args (dict): Argument key/value pairs associated with this event.
    """

    def __init__(self, event_type, args, **_):
        self._type = event_type
        self._args = args

    @staticmethod
    def New(event_type, args, **kwargs):
        """Create new event using a specialized Event class when needed.

        Args:
            event_type (int): A numeric id corresponding to an event in
                google.assistant.event.EventType.
            args (dict): Argument key/value pairs associated with this event.
            kwargs (dict): Optional argument key/value pairs specific to a
                specialization of the Event class for an EventType.
        """
        event_type = EventType(event_type)
        event_cls = _EVENT_BY_TYPE.get(event_type, Event)
        return event_cls(event_type, args, **kwargs)

    @property
    def type(self):
        return self._type

    @property
    def args(self):
        return self._args

    def __str__(self):
        out = self.type.name
        if self.args:
            out += ':\n'
            format_args = {
                'ensure_ascii': False,
                'sort_keys': True,
            }
            formatted_args = '  ' + json.dumps(self.args, **format_args)
            if len(formatted_args) >= 80:
                formatted_args = json.dumps(self.args, indent=2, **format_args)

            out += (formatted_args.encode('UTF-8')
                    if sys.version_info < (3, 0) else formatted_args)
        return out


class AlertEvent(Event):
    """Extends Event to add parsing of 'alert_type'."""

    def __init__(self, event_type, args, **_):
        Event.__init__(self, event_type, args)
        self._args['alert_type'] = AlertType(args['alert_type'])


class DeviceActionEvent(Event):
    """Extends Event to add 'actions' property."""

    def __init__(self, event_type, args, **kwargs):
        Event.__init__(self, event_type, args)
        self._device_id = kwargs['device_id']

    @property
    def actions(self):
        """A generator of commands to execute for the current device."""
        if 'inputs' not in self._args:
            return

        for i in self._args['inputs']:
            if i['intent'] != 'action.devices.EXECUTE':
                pass

            for c in i['payload']['commands']:
                for device in c['devices']:
                    if device['id'] != self._device_id or 'execution' not in c:
                        pass

                    for e in c['execution']:
                        if 'params' in e:
                            yield e['command'], e['params']
                        else:
                            yield e['command'], None


class MediaStateChangeEvent(Event):
    """Extends Event to add parsing of 'state'."""

    def __init__(self, event_type, args, **_):
        Event.__init__(self, event_type, args)
        if 'track_type' in self._args:
            self._args['track_type'] = MediaTrackType(args['track_type'])


class RenderResponseEvent(Event):
    """Extends Event to add parsing of 'response_type'."""

    def __init__(self, event_type, args, **_):
        Event.__init__(self, event_type, args)
        self._args['type'] = RenderResponseType(args['type'])


class IterableEventQueue(queue.Queue):
    """Extends queue.Queue to add an ``__iter__`` interface."""

    def __init__(self, timeout=3600):
        """Initializes an iterable queue.Queue.

        Args:
            timeout(int): The number of seconds to sleep, waiting for an event
                when iterating. Lower numbers mean the event loop will be
                active more often (and consuming CPU cycles).
        """
        # pylint: disable=super-init-not-called
        queue.Queue.__init__(self, maxsize=32)
        self._timeout = timeout

    def offer(self, event):
        """Offer an event to put in the queue.

        If the queue is currently full the event will be logged but not added.

        Args:
            event (Event): The event to try to add to the queue.
        """
        try:
            self.put(event, block=False)
        except queue.Full:
            # TODO(jordanjtw): We should log or throw an exception with the
            # ignored event.
            pass

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        while True:
            try:
                return self.get(block=True, timeout=self._timeout)
            except KeyboardInterrupt:
                raise StopIteration()
            except queue.Empty:
                pass


_EVENT_BY_TYPE = {
    EventType.ON_ALERT_STARTED: AlertEvent,
    EventType.ON_ALERT_FINISHED: AlertEvent,
    EventType.ON_DEVICE_ACTION: DeviceActionEvent,
    EventType.ON_RENDER_RESPONSE: RenderResponseEvent,
    EventType.ON_MEDIA_TRACK_LOAD: MediaStateChangeEvent,
    EventType.ON_MEDIA_TRACK_PLAY: MediaStateChangeEvent,
    EventType.ON_MEDIA_TRACK_STOP: MediaStateChangeEvent,
}
