# The MIT License (MIT)
#
# Copyright (c) 2016 Scott Shawcroft for Adafruit Industries
# Copyright (c) 2017-2019 Kattni Rembor for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
`adafruit_circuitplayground.express`
====================================================

CircuitPython subclass for Circuit Playground Express.

**Hardware:**

* `Circuit Playground Express <https://www.adafruit.com/product/3333>`_

* Author(s): Kattni Rembor, Scott Shawcroft
"""

import array
import math
import time
import sys
import audioio
try:
    import audiocore
except ImportError:
    audiocore = audioio
import board
import digitalio
# pylint: disable=wrong-import-position
try:
    lib_index = sys.path.index("/lib")        # pylint: disable=invalid-name
    if lib_index < sys.path.index(".frozen"):
        # Prefer frozen modules over those in /lib.
        sys.path.insert(lib_index, ".frozen")
except ValueError:
    # Don't change sys.path if it doesn't contain "lib" or ".frozen".
    pass
from adafruit_circuitplayground.circuit_playground_base import CircuitPlaygroundBase


__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_CircuitPlayground.git"


class Express(CircuitPlaygroundBase):
    """Represents a single CircuitPlayground Express. Do not use more than one at
       a time."""

    # Touch pad A7 is labeled both A7/TX on Circuit Playground Express and only TX on
    # the Circuit Playground Bluefruit. It is therefore referred to as TX in the
    # CircuitPlaygroundBase class, but can be used as either for Express.
    touch_A7 = CircuitPlaygroundBase.touch_TX

    def __init__(self):
        # Only create the cpx module member when we aren't being imported by Sphinx
        if ("__module__" in dir(digitalio.DigitalInOut) and
                digitalio.DigitalInOut.__module__ == "sphinx.ext.autodoc"):
            return

        # Define audio:
        self._speaker_enable = digitalio.DigitalInOut(board.SPEAKER_ENABLE)
        self._speaker_enable.switch_to_output(value=False)
        self._sample = None
        self._sine_wave = None
        self._sine_wave_sample = None

        super().__init__()

    @staticmethod
    def _sine_sample(length):
        tone_volume = (2 ** 15) - 1
        shift = 2 ** 15
        for i in range(length):
            yield int(tone_volume * math.sin(2*math.pi*(i / length)) + shift)

    def _generate_sample(self, length=100):
        if self._sample is not None:
            return
        self._sine_wave = array.array("H", Express._sine_sample(length))
        self._sample = audioio.AudioOut(board.SPEAKER)
        self._sine_wave_sample = audiocore.RawSample(self._sine_wave)

    def play_tone(self, frequency, duration):
        """ Produce a tone using the speaker. Try changing frequency to change
        the pitch of the tone.

        :param int frequency: The frequency of the tone in Hz
        :param float duration: The duration of the tone in seconds

        .. image :: ../docs/_static/speaker.jpg
          :alt: Onboard speaker

        .. code-block:: python

            from adafruit_circuitplayground.express import cpx

            cpx.play_tone(440, 1)
        """
        # Play a tone of the specified frequency (hz).
        self.start_tone(frequency)
        time.sleep(duration)
        self.stop_tone()

    def start_tone(self, frequency):
        """ Produce a tone using the speaker. Try changing frequency to change
        the pitch of the tone.

        :param int frequency: The frequency of the tone in Hz

        .. image :: ../docs/_static/speaker.jpg
          :alt: Onboard speaker

        .. code-block:: python

             from adafruit_circuitplayground.express import cpx

             while True:
                 if cpx.button_a:
                     cpx.start_tone(262)
                 elif cpx.button_b:
                     cpx.start_tone(294)
                 else:
                     cpx.stop_tone()
        """
        self._speaker_enable.value = True
        length = 100
        if length * frequency > 350000:
            length = 350000 // frequency
        self._generate_sample(length)
        # Start playing a tone of the specified frequency (hz).
        self._sine_wave_sample.sample_rate = int(len(self._sine_wave) * frequency)
        if not self._sample.playing:
            self._sample.play(self._sine_wave_sample, loop=True)

    def stop_tone(self):
        """ Use with start_tone to stop the tone produced.

        .. image :: ../docs/_static/speaker.jpg
          :alt: Onboard speaker

        .. code-block:: python

             from adafruit_circuitplayground.express import cpx

             while True:
                 if cpx.button_a:
                     cpx.start_tone(262)
                 elif cpx.button_b:
                     cpx.start_tone(294)
                 else:
                     cpx.stop_tone()
        """
        # Stop playing any tones.
        if self._sample is not None and self._sample.playing:
            self._sample.stop()
            self._sample.deinit()
            self._sample = None
        self._speaker_enable.value = False

    def play_file(self, file_name):
        """ Play a .wav file using the onboard speaker.

        :param file_name: The name of your .wav file in quotation marks including .wav

        .. image :: ../docs/_static/speaker.jpg
          :alt: Onboard speaker

        .. code-block:: python

             from adafruit_circuitplayground.express import cpx

             while True:
                 if cpx.button_a:
                     cpx.play_file("laugh.wav")
                 elif cpx.button_b:
                     cpx.play_file("rimshot.wav")
        """
        # Play a specified file.
        self.stop_tone()
        self._speaker_enable.value = True
        with audioio.AudioOut(board.SPEAKER) as audio:
            wavefile = audiocore.WaveFile(open(file_name, "rb"))
            audio.play(wavefile)
            while audio.playing:
                pass
        self._speaker_enable.value = False


cpx = Express()  # pylint: disable=invalid-name
"""Object that is automatically created on import.

   To use, simply import it from the module:

   .. code-block:: python

     from adafruit_circuitplayground.express import cpx
"""
